/**
 * Metrics Server - Prometheus metrics and health check HTTP server
 *
 * Purpose: Expose /metrics and /health endpoints for monitoring.
 * Layer: Infrastructure (monitoring)
 * Used by: Prometheus, monitoring tools, DevOps
 *
 * Endpoints:
 * - GET /metrics - Prometheus text format metrics
 * - GET /health - JSON health check status
 *
 * @module infrastructure/monitoring
 */

import type { FastifyInstance } from "fastify";
import Fastify from "fastify";
import { register } from "prom-client";
import { getMetricsText } from "./custom-metrics";
import { HealthChecker, type HealthCheckResult } from "./health-check";
import { logger } from "../cli/logger";

export class MetricsServer {
  private server: FastifyInstance;
  private healthChecker: HealthChecker;
  private port: number;
  private metricsCache: { text: string; timestamp: number } | null = null;
  private readonly CACHE_TTL_MS = 1000; // 1 second cache TTL

  constructor(port: number, dbPath: string, vectorDbPath: string) {
    this.port = port;
    this.healthChecker = new HealthChecker(dbPath, vectorDbPath);
    this.server = Fastify({
      logger: false, // Use our own logger
      requestTimeout: 5000, // 5 second timeout
    });

    this.setupRoutes();
  }

  /**
   * Setup HTTP routes
   */
  private setupRoutes(): void {
    // GET /metrics - Prometheus metrics endpoint
    this.server.get("/metrics", async (_request, reply) => {
      try {
        const metrics = await this.getMetricsWithCache();

        reply
          .code(200)
          .header("Content-Type", register.contentType)
          .send(metrics);

        logger.debug("Metrics endpoint accessed", {
          cacheHit: !!this.metricsCache,
        });
      } catch (error) {
        logger.error("Failed to generate metrics", { error });
        reply.code(500).send({
          error: "Internal Server Error",
          message: "Failed to generate metrics",
        });
      }
    });

    // GET /health - Health check endpoint
    this.server.get("/health", async (_request, reply) => {
      try {
        const health: HealthCheckResult = await this.healthChecker.check();
        const statusCode = HealthChecker.getStatusCode(health.status);

        reply.code(statusCode).send(health);

        logger.debug("Health check endpoint accessed", {
          status: health.status,
          statusCode,
        });
      } catch (error) {
        logger.error("Health check failed", { error });
        reply.code(503).send({
          status: "unhealthy",
          timestamp: new Date().toISOString(),
          error: error instanceof Error ? error.message : String(error),
        });
      }
    });

    // GET / - Root endpoint (redirect to /health)
    this.server.get("/", async (_request, reply) => {
      reply.redirect("/health", 302);
    });
  }

  /**
   * Get metrics with 1-second cache to achieve <50ms p99 target
   */
  private async getMetricsWithCache(): Promise<string> {
    const now = Date.now();

    // Check cache validity
    if (
      this.metricsCache &&
      now - this.metricsCache.timestamp < this.CACHE_TTL_MS
    ) {
      return this.metricsCache.text;
    }

    // Combine default Prometheus metrics with custom metrics
    const defaultMetrics = await register.metrics();
    const customMetrics = await getMetricsText();

    const combinedMetrics = `${defaultMetrics}\n${customMetrics}`;

    // Update cache
    this.metricsCache = {
      text: combinedMetrics,
      timestamp: now,
    };

    return combinedMetrics;
  }

  /**
   * Start the metrics server
   */
  async start(): Promise<void> {
    try {
      await this.server.listen({ port: this.port, host: "0.0.0.0" });

      logger.info("Metrics server started", {
        port: this.port,
        endpoints: [
          `http://localhost:${this.port}/metrics`,
          `http://localhost:${this.port}/health`,
        ],
      });
    } catch (error) {
      logger.error("Failed to start metrics server", {
        error,
        port: this.port,
      });
      throw error;
    }
  }

  /**
   * Stop the metrics server
   */
  async stop(): Promise<void> {
    try {
      await this.server.close();
      logger.info("Metrics server stopped");
    } catch (error) {
      logger.error("Failed to stop metrics server", { error });
      throw error;
    }
  }

  /**
   * Get server instance (for testing)
   */
  getServer(): FastifyInstance {
    return this.server;
  }
}
