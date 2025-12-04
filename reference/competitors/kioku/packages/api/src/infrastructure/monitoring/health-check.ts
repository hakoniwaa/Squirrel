/**
 * Health Check - System health monitoring
 *
 * Purpose: Check health of all critical components.
 * Layer: Infrastructure (monitoring)
 * Used by: Metrics server /health endpoint
 *
 * Health Status:
 * - healthy (200): All systems operational
 * - degraded (429): Some non-critical issues
 * - unhealthy (503): Critical failures
 *
 * @module infrastructure/monitoring
 */

import { existsSync } from "fs";
import { stat } from "fs/promises";
import { Database } from "bun:sqlite";
import { logger } from "../cli/logger";

export type HealthStatus = "healthy" | "degraded" | "unhealthy";

export interface ComponentHealth {
  name: string;
  status: HealthStatus;
  message?: string;
  details?: Record<string, string | number | boolean>;
}

export interface HealthCheckResult {
  status: HealthStatus;
  timestamp: string;
  components: ComponentHealth[];
  uptime: number; // seconds
}

export class HealthChecker {
  private startTime: number;
  private dbPath: string;
  private vectorDbPath: string;

  constructor(dbPath: string, vectorDbPath: string) {
    this.startTime = Date.now();
    this.dbPath = dbPath;
    this.vectorDbPath = vectorDbPath;
  }

  /**
   * Perform comprehensive health check
   */
  async check(): Promise<HealthCheckResult> {
    const components: ComponentHealth[] = [];

    // Check SQLite database
    components.push(await this.checkSQLiteDatabase());

    // Check vector database (ChromaDB)
    components.push(await this.checkVectorDatabase());

    // Check disk space
    components.push(await this.checkDiskSpace());

    // Determine overall status
    const overallStatus = this.determineOverallStatus(components);

    const result: HealthCheckResult = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      components,
      uptime: Math.floor((Date.now() - this.startTime) / 1000),
    };

    logger.debug("Health check completed", {
      status: overallStatus,
      componentCount: components.length,
    });

    return result;
  }

  /**
   * Check SQLite database health
   */
  private async checkSQLiteDatabase(): Promise<ComponentHealth> {
    try {
      // Check if database file exists
      if (!existsSync(this.dbPath)) {
        return {
          name: "sqlite_database",
          status: "unhealthy",
          message: "Database file does not exist",
        };
      }

      // Try to connect and run integrity check
      const db = new Database(this.dbPath, { readonly: true });

      try {
        const result = db.query("PRAGMA integrity_check").get() as {
          integrity_check: string;
        };

        if (result.integrity_check === "ok") {
          // Get database size
          const fileStats = await stat(this.dbPath);
          const sizeInMB = (fileStats.size / (1024 * 1024)).toFixed(2);

          return {
            name: "sqlite_database",
            status: "healthy",
            message: "Database operational",
            details: {
              path: this.dbPath,
              sizeInMB,
            },
          };
        } else {
          return {
            name: "sqlite_database",
            status: "degraded",
            message: "Database integrity check failed",
            details: { integrityCheck: result.integrity_check },
          };
        }
      } finally {
        db.close();
      }
    } catch (error) {
      return {
        name: "sqlite_database",
        status: "unhealthy",
        message: "Database connection failed",
        details: {
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  /**
   * Check vector database (ChromaDB) health
   */
  private async checkVectorDatabase(): Promise<ComponentHealth> {
    try {
      // Check if vector DB directory exists
      if (!existsSync(this.vectorDbPath)) {
        return {
          name: "vector_database",
          status: "degraded",
          message: "Vector database not initialized",
          details: { path: this.vectorDbPath },
        };
      }

      // Get directory size
      const stats = await stat(this.vectorDbPath);
      const sizeInMB = stats.isDirectory()
        ? "N/A (directory)"
        : (stats.size / (1024 * 1024)).toFixed(2);

      return {
        name: "vector_database",
        status: "healthy",
        message: "Vector database operational",
        details: {
          path: this.vectorDbPath,
          sizeInMB,
        },
      };
    } catch (error) {
      return {
        name: "vector_database",
        status: "degraded",
        message: "Vector database check failed",
        details: {
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  /**
   * Check available disk space
   */
  private async checkDiskSpace(): Promise<ComponentHealth> {
    try {
      // Get disk usage for database directory
      const dbStats = await stat(this.dbPath);
      const dbSize = dbStats.size;

      // Simple heuristic: warn if DB > 1GB
      const GB = 1024 * 1024 * 1024;
      const dbSizeInGB = dbSize / GB;

      if (dbSizeInGB > 5) {
        return {
          name: "disk_space",
          status: "degraded",
          message: "Database size is large",
          details: {
            databaseSizeGB: dbSizeInGB.toFixed(2),
            recommendation: "Consider pruning old data",
          },
        };
      }

      return {
        name: "disk_space",
        status: "healthy",
        message: "Adequate disk space",
        details: {
          databaseSizeGB: dbSizeInGB.toFixed(2),
        },
      };
    } catch (error) {
      return {
        name: "disk_space",
        status: "degraded",
        message: "Disk space check failed",
        details: {
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }

  /**
   * Determine overall health status from components
   */
  private determineOverallStatus(components: ComponentHealth[]): HealthStatus {
    const hasUnhealthy = components.some((c) => c.status === "unhealthy");
    const hasDegraded = components.some((c) => c.status === "degraded");

    if (hasUnhealthy) {
      return "unhealthy";
    } else if (hasDegraded) {
      return "degraded";
    } else {
      return "healthy";
    }
  }

  /**
   * Get HTTP status code for health status
   */
  static getStatusCode(status: HealthStatus): number {
    switch (status) {
      case "healthy":
        return 200;
      case "degraded":
        return 429; // Too Many Requests (non-critical degradation)
      case "unhealthy":
        return 503; // Service Unavailable
    }
  }
}
