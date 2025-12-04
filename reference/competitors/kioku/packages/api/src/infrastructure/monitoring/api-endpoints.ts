/**
 * Dashboard API Endpoints
 *
 * REST API endpoints for the Visual Context Dashboard
 *
 * Layer: Infrastructure (monitoring)
 * Purpose: Expose context data via HTTP for dashboard UI
 *
 * @module infrastructure/monitoring
 */

import type { FastifyInstance } from "fastify";
import { Database } from "bun:sqlite";
import { existsSync, statSync } from "fs";
import { logger } from "../cli/logger";
import { WorkspaceStorage } from "infrastructure/storage/workspace-storage";

interface ApiConfig {
  dbPath: string;
  vectorDbPath: string;
}

interface ProjectOverview {
  name: string;
  type: string;
  techStack: string[];
  moduleCount: number;
  fileCount: number;
  databaseSize: string;
  activeSession: boolean;
  lastSessionTime?: string;
}

interface Session {
  id: string;
  startTime: string;
  endTime?: string;
  duration: number;
  filesCount: number;
  discoveriesCount: number;
}

interface SessionDetails extends Session {
  files?: string[];
  topics?: string[];
  discoveries?: Discovery[];
}

interface Discovery {
  id: string;
  type: string;
  content: string;
  confidence: number;
  extractedAt: string;
}

interface ModuleNode {
  id: string;
  name: string;
  path: string;
  fileCount: number;
  lastAccessed?: string;
  activity: "active" | "recent" | "stale";
}

interface ModuleEdge {
  source: string;
  target: string;
  weight: number;
}

interface ModuleGraph {
  nodes: ModuleNode[];
  edges: ModuleEdge[];
}

interface EmbeddingsStats {
  totalCount: number;
  lastGenerated: string;
  queueSize: number;
  errorCount: number;
  diskUsage: string;
}

interface ContextWindowUsage {
  current: number;
  max: number;
  percentage: number;
  status: "healthy" | "warning" | "critical";
}

interface ServiceStatus {
  name: string;
  status: "running" | "stopped" | "error";
  details?: string;
}

interface HealthStatus {
  services: ServiceStatus[];
  uptime: number;
  timestamp: string;
}

interface LinkedProjectInfo {
  name: string;
  path: string;
  status: "available" | "unavailable";
  lastAccessed?: string;
  moduleCount?: number;
  fileCount?: number;
}

/**
 * Register all dashboard API routes
 */
export async function registerApiRoutes(
  server: FastifyInstance,
  config: ApiConfig,
): Promise<void> {
  const { dbPath, vectorDbPath } = config;

  logger.info("Registering dashboard API routes", { dbPath, vectorDbPath });

  // Configure CORS for dashboard (localhost:3456)
  server.addHook("onRequest", async (request, reply) => {
    // Allow requests from dashboard
    const origin = request.headers.origin;
    if (
      origin &&
      (origin === "http://localhost:3456" ||
        origin.startsWith("http://localhost:"))
    ) {
      reply.header("Access-Control-Allow-Origin", origin);
      reply.header(
        "Access-Control-Allow-Methods",
        "GET, POST, PUT, DELETE, OPTIONS",
      );
      reply.header(
        "Access-Control-Allow-Headers",
        "Content-Type, Authorization",
      );
      reply.header("Access-Control-Allow-Credentials", "true");
    }

    // Handle preflight requests
    if (request.method === "OPTIONS") {
      reply.code(204).send();
    }
  });

  // GET /api/project - Project overview
  server.get("/api/project", async (_request, reply) => {
    try {
      const overview = await getProjectOverview(dbPath);
      reply.code(200).send(overview);
    } catch (error) {
      logger.error("Failed to get project overview", { error });
      reply.code(500).send({
        error: "Internal Server Error",
        message: "Failed to get project overview",
      });
    }
  });

  // GET /api/sessions - List sessions
  server.get<{ Querystring: { limit?: string } }>(
    "/api/sessions",
    async (request, reply) => {
      try {
        const limit = request.query.limit
          ? parseInt(request.query.limit, 10)
          : undefined;
        const sessions = await getSessions(dbPath, limit);
        reply.code(200).send(sessions);
      } catch (error) {
        logger.error("Failed to get sessions", { error });
        reply.code(500).send({
          error: "Internal Server Error",
          message: "Failed to get sessions",
        });
      }
    },
  );

  // GET /api/sessions/:id - Session details
  server.get<{ Params: { id: string } }>(
    "/api/sessions/:id",
    async (request, reply) => {
      try {
        const session = await getSessionDetails(dbPath, request.params.id);
        if (!session) {
          reply.code(404).send({
            error: "Not Found",
            message: `Session ${request.params.id} not found`,
          });
          return;
        }
        reply.code(200).send(session);
      } catch (error) {
        logger.error("Failed to get session details", { error });
        reply.code(500).send({
          error: "Internal Server Error",
          message: "Failed to get session details",
        });
      }
    },
  );

  // GET /api/modules - Module dependency graph
  server.get("/api/modules", async (_request, reply) => {
    try {
      const graph = await getModuleGraph(dbPath);
      reply.code(200).send(graph);
    } catch (error) {
      logger.error("Failed to get module graph", { error });
      reply.code(500).send({
        error: "Internal Server Error",
        message: "Failed to get module graph",
      });
    }
  });

  // GET /api/embeddings - Embeddings statistics
  server.get("/api/embeddings", async (_request, reply) => {
    try {
      const stats = await getEmbeddingsStats(dbPath, vectorDbPath);
      reply.code(200).send(stats);
    } catch (error) {
      logger.error("Failed to get embeddings stats", { error });
      reply.code(500).send({
        error: "Internal Server Error",
        message: "Failed to get embeddings stats",
      });
    }
  });

  // GET /api/context - Context window usage
  server.get("/api/context", async (_request, reply) => {
    try {
      const usage = await getContextWindowUsage(dbPath);
      reply.code(200).send(usage);
    } catch (error) {
      logger.error("Failed to get context window usage", { error });
      reply.code(500).send({
        error: "Internal Server Error",
        message: "Failed to get context window usage",
      });
    }
  });

  // GET /api/health - Service health status
  server.get("/api/health", async (_request, reply) => {
    try {
      const health = await getHealthStatus(dbPath, vectorDbPath);
      reply.code(200).send(health);
    } catch (error) {
      logger.error("Failed to get health status", { error });
      reply.code(500).send({
        error: "Internal Server Error",
        message: "Failed to get health status",
      });
    }
  });

  // GET /api/linked-projects - Linked projects info
  server.get("/api/linked-projects", async (_request, reply) => {
    try {
      const projects = await getLinkedProjects(dbPath);
      reply.code(200).send(projects);
    } catch (error) {
      logger.error("Failed to get linked projects", { error });
      reply.code(500).send({
        error: "Internal Server Error",
        message: "Failed to get linked projects",
      });
    }
  });

  logger.info("Dashboard API routes registered successfully");
}

/**
 * Get project overview
 */
async function getProjectOverview(dbPath: string): Promise<ProjectOverview> {
  const db = new Database(dbPath);

  try {
    let moduleCount = 0;
    let fileCount = 0;
    let activeSession = false;
    let lastSessionTime: string | undefined;
    let projectName = "kioku";
    let techStack: string[] = ["TypeScript"];

    // Count unique modules (handle missing table)
    try {
      const moduleCountResult = db
        .query<
          { count: number },
          []
        >("SELECT COUNT(DISTINCT module_path) as count FROM chunks")
        .get();
      moduleCount = moduleCountResult?.count || 0;
    } catch {
      // Table doesn't exist, use default
      moduleCount = 0;
    }

    // Count unique files (handle missing table)
    try {
      const fileCountResult = db
        .query<
          { count: number },
          []
        >("SELECT COUNT(DISTINCT file_path) as count FROM chunks")
        .get();
      fileCount = fileCountResult?.count || 0;
    } catch {
      // Table doesn't exist, use default
      fileCount = 0;
    }

    // Get database size
    const databaseSize = formatFileSize(getFileSize(dbPath));

    // Check for active session (session without end_time)
    try {
      const activeSessionResult = db
        .query<
          { id: string; start_time: string },
          []
        >("SELECT id, start_time FROM sessions WHERE end_time IS NULL ORDER BY start_time DESC LIMIT 1")
        .get();

      activeSession = !!activeSessionResult;
    } catch {
      // Table doesn't exist, use default
      activeSession = false;
    }

    // Get last session time
    try {
      const lastSessionResult = db
        .query<
          { start_time: string },
          []
        >("SELECT start_time FROM sessions ORDER BY start_time DESC LIMIT 1")
        .get();

      lastSessionTime = lastSessionResult?.start_time;
    } catch {
      // Table doesn't exist, use default
      lastSessionTime = undefined;
    }

    // Infer project name from first chunk (or default)
    try {
      const firstChunkResult = db
        .query<
          { file_path: string },
          []
        >("SELECT file_path FROM chunks LIMIT 1")
        .get();

      projectName = firstChunkResult?.file_path?.split("/")[0] || "kioku";
    } catch {
      // Table doesn't exist, use default
      projectName = "kioku";
    }

    // Infer tech stack from file extensions
    try {
      techStack = inferTechStack(db);
    } catch {
      // Table doesn't exist, use default
      techStack = ["TypeScript"];
    }

    const result: ProjectOverview = {
      name: projectName,
      type: "TypeScript Project",
      techStack,
      moduleCount,
      fileCount,
      databaseSize,
      activeSession,
    };

    if (lastSessionTime) {
      result.lastSessionTime = lastSessionTime;
    }

    return result;
  } finally {
    db.close();
  }
}

/**
 * Get sessions list
 */
async function getSessions(dbPath: string, limit?: number): Promise<Session[]> {
  const db = new Database(dbPath);

  try {
    const limitClause = limit ? `LIMIT ${limit}` : "";

    let sessions: {
      id: string;
      start_time: string;
      end_time: string | null;
      created_at: string;
    }[] = [];

    // Handle missing sessions table
    try {
      sessions = db
        .query<
          {
            id: string;
            start_time: string;
            end_time: string | null;
            created_at: string;
          },
          []
        >(
          `SELECT id, start_time, end_time, created_at
           FROM sessions
           ORDER BY start_time DESC
           ${limitClause}`,
        )
        .all();
    } catch {
      // Table doesn't exist, return empty array
      return [];
    }

    return sessions.map((session) => {
      // Calculate duration
      const startTime = new Date(session.start_time);
      const endTime = session.end_time
        ? new Date(session.end_time)
        : new Date();
      const durationMs = endTime.getTime() - startTime.getTime();
      const durationMinutes = Math.floor(durationMs / (1000 * 60));

      // Count files for this session
      let filesCount = 0;
      try {
        const filesCountResult = db
          .query<
            { count: number },
            [string]
          >("SELECT COUNT(*) as count FROM session_files WHERE session_id = ?")
          .get(session.id);
        filesCount = filesCountResult?.count || 0;
      } catch {
        // Table doesn't exist, use default
        filesCount = 0;
      }

      // Count discoveries for this session
      let discoveriesCount = 0;
      try {
        const discoveriesCountResult = db
          .query<
            { count: number },
            [string]
          >("SELECT COUNT(*) as count FROM refined_discoveries WHERE session_id = ?")
          .get(session.id);
        discoveriesCount = discoveriesCountResult?.count || 0;
      } catch {
        // Table doesn't exist, use default
        discoveriesCount = 0;
      }

      const result: Session = {
        id: session.id,
        startTime: session.start_time,
        duration: durationMinutes,
        filesCount,
        discoveriesCount,
      };

      if (session.end_time) {
        result.endTime = session.end_time;
      }

      return result;
    });
  } finally {
    db.close();
  }
}

/**
 * Get session details
 */
async function getSessionDetails(
  dbPath: string,
  sessionId: string,
): Promise<SessionDetails | null> {
  const db = new Database(dbPath);

  try {
    // Get session (handle missing table)
    let sessionResult;
    try {
      sessionResult = db
        .query<
          {
            id: string;
            start_time: string;
            end_time: string | null;
            created_at: string;
          },
          [string]
        >(
          "SELECT id, start_time, end_time, created_at FROM sessions WHERE id = ?",
        )
        .get(sessionId);
    } catch {
      // Table doesn't exist
      return null;
    }

    if (!sessionResult) {
      return null;
    }

    // Calculate duration
    const startTime = new Date(sessionResult.start_time);
    const endTime = sessionResult.end_time
      ? new Date(sessionResult.end_time)
      : new Date();
    const durationMs = endTime.getTime() - startTime.getTime();
    const durationMinutes = Math.floor(durationMs / (1000 * 60));

    // Get files (handle missing table)
    let files: string[] = [];
    try {
      const filesResult = db
        .query<
          { file_path: string; access_count: number },
          [string]
        >("SELECT file_path, access_count FROM session_files WHERE session_id = ? ORDER BY access_count DESC")
        .all(sessionId);
      files = filesResult.map((f) => f.file_path);
    } catch {
      // Table doesn't exist, use empty array
      files = [];
    }

    // Get discoveries (handle missing table)
    let discoveries: Discovery[] = [];
    try {
      const discoveriesResult = db
        .query<
          {
            id: string;
            type: string;
            content: string;
            confidence: number;
            created_at: string;
          },
          [string]
        >(
          "SELECT id, type, content, confidence, created_at FROM refined_discoveries WHERE session_id = ?",
        )
        .all(sessionId);
      discoveries = discoveriesResult.map((d) => ({
        id: d.id,
        type: d.type,
        content: d.content,
        confidence: d.confidence,
        extractedAt: d.created_at,
      }));
    } catch {
      // Table doesn't exist, use empty array
      discoveries = [];
    }

    // Extract topics from discoveries
    const topics = [...new Set(discoveries.map((d) => d.type))];

    const result: SessionDetails = {
      id: sessionResult.id,
      startTime: sessionResult.start_time,
      duration: durationMinutes,
      filesCount: files.length,
      discoveriesCount: discoveries.length,
      files,
      topics,
      discoveries,
    };

    if (sessionResult.end_time) {
      result.endTime = sessionResult.end_time;
    }

    return result;
  } finally {
    db.close();
  }
}

/**
 * Get module dependency graph
 */
async function getModuleGraph(dbPath: string): Promise<ModuleGraph> {
  const db = new Database(dbPath);

  try {
    // Get unique modules (handle missing table)
    let modulesResult: { module_path: string; count: number }[] = [];
    try {
      modulesResult = db
        .query<
          { module_path: string; count: number },
          []
        >("SELECT module_path, COUNT(*) as count FROM chunks GROUP BY module_path")
        .all();
    } catch {
      // Table doesn't exist, return empty graph
      return { nodes: [], edges: [] };
    }

    // Create nodes
    const nodes: ModuleNode[] = modulesResult.map((m) => {
      const moduleName = m.module_path.split("/").pop() || m.module_path;

      return {
        id: m.module_path,
        name: moduleName,
        path: m.module_path,
        fileCount: m.count,
        activity: "stale" as const, // TODO: Implement activity tracking
      };
    });

    // For now, create edges based on module hierarchy
    // (e.g., src/application depends on src/domain)
    const edges: ModuleEdge[] = [];

    // Simple heuristic: if module A is a parent of module B, create edge
    for (const moduleA of modulesResult) {
      for (const moduleB of modulesResult) {
        if (
          moduleA.module_path !== moduleB.module_path &&
          moduleB.module_path.startsWith(moduleA.module_path + "/")
        ) {
          edges.push({
            source: moduleA.module_path,
            target: moduleB.module_path,
            weight: 1,
          });
        }
      }
    }

    return { nodes, edges };
  } finally {
    db.close();
  }
}

/**
 * Get embeddings statistics
 */
async function getEmbeddingsStats(
  dbPath: string,
  vectorDbPath: string,
): Promise<EmbeddingsStats> {
  const db = new Database(dbPath);

  try {
    let totalCount = 0;
    let lastGenerated = new Date().toISOString();

    // Count total chunks (proxy for embeddings) - handle missing table
    try {
      const countResult = db
        .query<{ count: number }, []>("SELECT COUNT(*) as count FROM chunks")
        .get();
      totalCount = countResult?.count || 0;
    } catch {
      // Table doesn't exist, use default
      totalCount = 0;
    }

    // Get last updated chunk time - handle missing table
    try {
      const lastUpdatedResult = db
        .query<
          { updated_at: string },
          []
        >("SELECT updated_at FROM chunks ORDER BY updated_at DESC LIMIT 1")
        .get();
      lastGenerated = lastUpdatedResult?.updated_at || new Date().toISOString();
    } catch {
      // Table doesn't exist, use current time
      lastGenerated = new Date().toISOString();
    }

    // Queue size (mock for now - would need separate queue table)
    const queueSize = 0;

    // Error count (mock for now - would need error log table)
    const errorCount = 0;

    // Get vector DB disk usage
    const diskUsage = existsSync(vectorDbPath)
      ? formatFileSize(getDirectorySize(vectorDbPath))
      : "0 B";

    return {
      totalCount,
      lastGenerated,
      queueSize,
      errorCount,
      diskUsage,
    };
  } finally {
    db.close();
  }
}

/**
 * Get context window usage
 */
async function getContextWindowUsage(
  dbPath: string,
): Promise<ContextWindowUsage> {
  const db = new Database(dbPath);

  try {
    let totalLength = 0;

    // Estimate tokens from chunks (rough estimate: ~4 chars per token) - handle missing table
    try {
      const totalLengthResult = db
        .query<
          { total_length: number },
          []
        >("SELECT SUM(LENGTH(code)) as total_length FROM chunks")
        .get();
      totalLength = totalLengthResult?.total_length || 0;
    } catch {
      // Table doesn't exist, use default
      totalLength = 0;
    }

    const current = Math.floor(totalLength / 4); // Rough token estimate

    const max = 100000; // Default context window size
    const percentage = Math.floor((current / max) * 100);

    let status: "healthy" | "warning" | "critical";
    if (percentage < 70) {
      status = "healthy";
    } else if (percentage < 90) {
      status = "warning";
    } else {
      status = "critical";
    }

    return {
      current,
      max,
      percentage,
      status,
    };
  } finally {
    db.close();
  }
}

/**
 * Get health status
 */
async function getHealthStatus(
  dbPath: string,
  vectorDbPath: string,
): Promise<HealthStatus> {
  const services: ServiceStatus[] = [];

  // Check SQLite database
  try {
    const db = new Database(dbPath);
    db.query("SELECT 1").get();
    db.close();
    services.push({
      name: "SQLite Database",
      status: "running",
      details: "Connected",
    });
  } catch (error) {
    services.push({
      name: "SQLite Database",
      status: "error",
      details: error instanceof Error ? error.message : String(error),
    });
  }

  // Check vector database
  if (existsSync(vectorDbPath)) {
    services.push({
      name: "Vector Database",
      status: "running",
      details: "Directory exists",
    });
  } else {
    services.push({
      name: "Vector Database",
      status: "stopped",
      details: "Directory not found",
    });
  }

  // Mock other services (would need actual service checks)
  services.push({
    name: "File Watcher",
    status: "running",
    details: "Active",
  });

  services.push({
    name: "Embeddings Queue",
    status: "running",
    details: "Idle",
  });

  return {
    services,
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  };
}

/**
 * Get linked projects
 */
async function getLinkedProjects(dbPath: string): Promise<LinkedProjectInfo[]> {
  try {
    // Try to find workspace.yaml in context directory
    const contextDir = dbPath.replace(/\/[^/]+$/, ""); // Get directory
    const workspaceStorage = new WorkspaceStorage(contextDir);

    if (!workspaceStorage.exists()) {
      return [];
    }

    const linkedProjects = workspaceStorage.getLinkedProjects();

    return linkedProjects.map((project) => {
      const result: LinkedProjectInfo = {
        name: project.name,
        path: project.path,
        status: project.status as "available" | "unavailable",
      };

      if (project.lastAccessed) {
        result.lastAccessed = project.lastAccessed.toISOString();
      }

      if (project.moduleCount !== undefined) {
        result.moduleCount = project.moduleCount;
      }

      if (project.fileCount !== undefined) {
        result.fileCount = project.fileCount;
      }

      return result;
    });
  } catch (error) {
    logger.warn("Failed to get linked projects", { error });
    return [];
  }
}

/**
 * Helper: Get file size in bytes
 */
function getFileSize(filePath: string): number {
  try {
    if (!existsSync(filePath)) {
      return 0;
    }
    return statSync(filePath).size;
  } catch {
    return 0;
  }
}

/**
 * Helper: Get directory size in bytes
 */
function getDirectorySize(dirPath: string): number {
  try {
    if (!existsSync(dirPath)) {
      return 0;
    }
    // Simplified: just return 0 for now (would need recursive dir walk)
    return 0;
  } catch {
    return 0;
  }
}

/**
 * Helper: Format file size
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

/**
 * Helper: Infer tech stack from file paths
 */
function inferTechStack(db: Database): string[] {
  const techStack = new Set<string>();

  // Check for common file extensions
  const extensionsResult = db
    .query<
      { file_path: string },
      []
    >("SELECT DISTINCT file_path FROM chunks LIMIT 100")
    .all();

  extensionsResult.forEach((row) => {
    const ext = row.file_path.split(".").pop()?.toLowerCase();

    if (ext === "ts" || ext === "tsx") {
      techStack.add("TypeScript");
    }
    if (ext === "js" || ext === "jsx") {
      techStack.add("JavaScript");
    }
    if (ext === "py") {
      techStack.add("Python");
    }
    if (ext === "rs") {
      techStack.add("Rust");
    }
    if (ext === "go") {
      techStack.add("Go");
    }
  });

  // Check for framework indicators
  const filesResult = db
    .query<
      { file_path: string },
      []
    >("SELECT file_path FROM chunks WHERE file_path LIKE '%package.json%' OR file_path LIKE '%tsconfig%'")
    .all();

  if (filesResult.length > 0) {
    techStack.add("Node.js");
  }

  return Array.from(techStack);
}
