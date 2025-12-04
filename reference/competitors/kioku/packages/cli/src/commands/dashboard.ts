/**
 * Dashboard Command
 *
 * Starts the Kioku dashboard web server with REST API
 *
 * Usage: kioku dashboard [options]
 *
 * Options:
 *   --port <number>     Port for dashboard (default: 3456)
 *   --api-port <number> Port for API (default: 9090)
 *   --no-browser        Don't auto-open browser
 *
 * Layer: Infrastructure (CLI)
 */

import Fastify from "fastify";
import type { FastifyInstance } from "fastify";
import { join } from "path";
import { existsSync, readFileSync, statSync } from "fs";
import { logger } from "../logger";
import { registerApiRoutes } from "@kioku/api";

interface DashboardOptions {
  port?: number;
  apiPort?: number;
  noBrowser?: boolean;
}

/**
 * Start dashboard server
 */
export async function dashboardCommand(
  options: DashboardOptions = {},
): Promise<void> {
  const port = options.port || 3456;
  const apiPort = options.apiPort || 9090;
  const shouldOpenBrowser = !options.noBrowser;

  logger.info("Starting Kioku dashboard", { port, apiPort, shouldOpenBrowser });

  try {
    // Get workspace context directory
    const workspaceRoot = process.cwd();
    const contextDir = join(workspaceRoot, ".context");

    // Get database paths (sessions.db is created by init command)
    const dbPath = join(contextDir, "sessions.db");
    const vectorDbPath = join(contextDir, "chroma");

    // Verify database exists
    if (!existsSync(dbPath)) {
      logger.error("Database not found. Run 'kioku init' first", { dbPath });
      console.error("❌ Database not found. Please run 'kioku init' first.");
      process.exit(1);
    }

    // Create API server
    const apiServer = await createApiServer(apiPort, dbPath, vectorDbPath);

    // Create dashboard server with API port for proxying
    const dashboardServer = await createDashboardServer(port, apiPort);

    // Graceful shutdown
    const shutdown = async (signal: string): Promise<void> => {
      logger.info(`Received ${signal}, shutting down gracefully`);
      await apiServer.close();
      await dashboardServer.close();
      process.exit(0);
    };

    process.on("SIGINT", () => shutdown("SIGINT"));
    process.on("SIGTERM", () => shutdown("SIGTERM"));

    // Log success
    const dashboardUrl = `http://localhost:${port}`;
    const apiUrl = `http://localhost:${apiPort}`;

    console.log("\n✅ Kioku Dashboard started successfully!\n");
    console.log(`📊 Dashboard: ${dashboardUrl}`);
    console.log(`🔌 API:       ${apiUrl}/api`);
    console.log("\nPress Ctrl+C to stop\n");

    // Auto-open browser
    if (shouldOpenBrowser) {
      await openBrowser(dashboardUrl);
    }

    // Keep process alive
    await new Promise(() => {}); // Never resolves
  } catch (error) {
    logger.error("Failed to start dashboard", { error });
    console.error("❌ Failed to start dashboard:", error);
    process.exit(1);
  }
}

/**
 * Create API server (REST endpoints)
 */
async function createApiServer(
  port: number,
  dbPath: string,
  vectorDbPath: string,
): Promise<FastifyInstance> {
  const server = Fastify({
    logger: false, // Use our custom logger
  });

  // Register API routes
  await registerApiRoutes(server, { dbPath, vectorDbPath });

  // Start server
  await server.listen({ port, host: "0.0.0.0" });

  logger.info("API server started", { port, url: `http://localhost:${port}` });

  return server;
}

/**
 * Create dashboard server (static files)
 */
async function createDashboardServer(
  port: number,
  apiPort: number,
): Promise<FastifyInstance> {
  const server = Fastify({
    logger: false,
  });

  // Get dashboard build directory (monorepo: packages/ui/dist)
  // Use process.cwd() instead of __dirname for Bun compatibility
  const workspaceRoot = process.cwd();
  const dashboardDir = join(workspaceRoot, "packages/ui/dist");

  // Check if dashboard is built
  if (!existsSync(dashboardDir)) {
    logger.error(
      "Dashboard not built. Run 'bun run build:ui' first",
      {
        dashboardDir,
        workspaceRoot,
      },
    );
    console.error("\n❌ Dashboard not built.");
    console.error("Please build the dashboard first:");
    console.error("  bun run build:ui");
    console.error("\nOr build all packages:");
    console.error("  bun run build\n");
    process.exit(1);
  }

  logger.info("Serving dashboard from", { dashboardDir });

  // Proxy API requests to the API server
  server.all("/api/*", async (request, reply) => {
    const apiUrl = `http://localhost:${apiPort}${request.url}`;
    try {
      const response = await fetch(apiUrl, {
        method: request.method,
        headers: request.headers as Record<string, string>,
        body:
          request.method !== "GET" && request.method !== "HEAD"
            ? JSON.stringify(request.body)
            : undefined,
      });

      const contentType = response.headers.get("content-type");
      const data = contentType?.includes("application/json")
        ? await response.json()
        : await response.text();

      reply
        .code(response.status)
        .header("content-type", contentType || "application/json")
        .send(data);
    } catch (error) {
      logger.error("Proxy error", { error, apiUrl });
      reply.code(502).send({ error: "Failed to proxy request to API server" });
    }
  });

  // Workaround for Bun + @fastify/static compatibility issue
  // Use manual file serving instead of fastifyStatic plugin
  server.get("/*", async (request, reply) => {
    const { url } = request;

    // Try to serve the requested file
    const filePath = join(dashboardDir, url === "/" ? "index.html" : url);

    if (existsSync(filePath) && statSync(filePath).isFile()) {
      const content = readFileSync(filePath);
      const ext = filePath.split(".").pop() || "";

      const mimeTypes: Record<string, string> = {
        html: "text/html",
        js: "application/javascript",
        css: "text/css",
        json: "application/json",
        png: "image/png",
        jpg: "image/jpeg",
        svg: "image/svg+xml",
      };

      // Bun + Fastify compatibility: convert Buffer to appropriate type
      const contentType = mimeTypes[ext] || "application/octet-stream";
      reply.type(contentType);

      // For text files, convert Buffer to string; for binary, keep as Buffer
      const textTypes = ["text/html", "application/javascript", "text/css", "application/json"];
      const payload = textTypes.includes(contentType)
        ? content.toString("utf-8")
        : content;

      return reply.send(payload);
    }

    // SPA fallback - serve index.html for unknown routes
    const indexPath = join(dashboardDir, "index.html");
    const indexContent = readFileSync(indexPath);
    reply.type("text/html");
    return reply.send(indexContent);
  });

  // Start server
  await server.listen({ port, host: "0.0.0.0" });

  logger.info("Dashboard server started", {
    port,
    url: `http://localhost:${port}`,
  });

  return server;
}

/**
 * Open browser (cross-platform)
 */
async function openBrowser(url: string): Promise<void> {
  const platform = process.platform;
  let command: string;

  if (platform === "darwin") {
    command = `open "${url}"`;
  } else if (platform === "win32") {
    command = `start "${url}"`;
  } else {
    command = `xdg-open "${url}"`;
  }

  try {
    const { spawn } = await import("child_process");
    const child = spawn(command, {
      shell: true,
      detached: true,
      stdio: "ignore",
    });
    child.unref();

    logger.info("Opened browser", { url, platform });
  } catch (error) {
    logger.warn("Failed to open browser automatically", { error, url });
    console.log(`\n💡 Please open ${url} in your browser manually\n`);
  }
}
