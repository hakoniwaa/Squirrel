/**
 * Dashboard API Integration Tests
 *
 * Tests the full dashboard API workflow with real database and services
 *
 * Validates Phase 10: User Story 7 - Visual Context Dashboard
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import type { FastifyInstance } from "fastify";
import Fastify from "fastify";
import { registerApiRoutes } from "infrastructure/monitoring/api-endpoints";
import * as fs from "fs/promises";
import * as path from "path";
import * as os from "os";
import { Database } from "bun:sqlite";

describe("Dashboard API Integration", () => {
  let server: FastifyInstance;
  let testDir: string;
  let dbPath: string;
  let vectorDbPath: string;

  beforeEach(async () => {
    // Create temporary test directory
    testDir = await fs.mkdtemp(path.join(os.tmpdir(), "kioku-dashboard-test-"));
    dbPath = path.join(testDir, "test.db");
    vectorDbPath = path.join(testDir, "chroma");

    // Create test database with schema matching actual implementation
    const db = new Database(dbPath);
    db.exec(`
      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        started_at INTEGER NOT NULL,
        ended_at INTEGER,
        status TEXT NOT NULL CHECK(status IN ('active', 'completed', 'archived')),
        files_accessed TEXT NOT NULL DEFAULT '[]',
        topics TEXT NOT NULL DEFAULT '[]',
        metadata TEXT NOT NULL DEFAULT '{}',
        created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        updated_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      );

      CREATE TABLE IF NOT EXISTS discoveries (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('pattern', 'rule', 'decision', 'issue')),
        content TEXT NOT NULL,
        module TEXT,
        context_json TEXT NOT NULL DEFAULT '{}',
        embedding_id TEXT,
        embedding_model TEXT,
        created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
      );

      CREATE TABLE IF NOT EXISTS context_items (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL CHECK(type IN ('file', 'module', 'discovery', 'session')),
        content TEXT NOT NULL,
        metadata_json TEXT NOT NULL DEFAULT '{}',
        score REAL NOT NULL DEFAULT 0.0,
        recency_factor REAL NOT NULL DEFAULT 0.0,
        access_factor REAL NOT NULL DEFAULT 0.0,
        last_accessed_at INTEGER NOT NULL,
        access_count INTEGER NOT NULL DEFAULT 0,
        tokens INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL CHECK(status IN ('active', 'archived')),
        created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        updated_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      );
    `);

    // Insert test data
    const nowMs = Date.now();
    const oneHourAgoMs = nowMs - (60 * 60 * 1000);

    // Insert test sessions with files_accessed as JSON
    const session1Files = JSON.stringify([
      {
        path: "src/domain/models/User.ts",
        accessCount: 5,
        firstAccessedAt: new Date(oneHourAgoMs).toISOString(),
        lastAccessedAt: new Date(nowMs).toISOString(),
      },
      {
        path: "src/application/services/UserService.ts",
        accessCount: 3,
        firstAccessedAt: new Date(oneHourAgoMs).toISOString(),
        lastAccessedAt: new Date(nowMs).toISOString(),
      },
    ]);

    db.run(
      `INSERT INTO sessions (id, project_id, started_at, ended_at, status, files_accessed, topics, metadata)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        "session-1",
        "test-project",
        oneHourAgoMs,
        nowMs,
        "completed",
        session1Files,
        JSON.stringify([]),
        JSON.stringify({ duration: 60 * 60 * 1000 }),
      ]
    );

    db.run(
      `INSERT INTO sessions (id, project_id, started_at, status, files_accessed, topics, metadata)
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [
        "session-2",
        "test-project",
        nowMs,
        "active",
        JSON.stringify([]),
        JSON.stringify([]),
        JSON.stringify({}),
      ]
    );

    // Insert discoveries
    db.run(
      `INSERT INTO discoveries (id, session_id, type, content, module, context_json)
       VALUES (?, ?, ?, ?, ?, ?)`,
      [
        "disc-1",
        "session-1",
        "pattern",
        "Always validate user input",
        "src/domain",
        JSON.stringify({}),
      ]
    );

    // Insert context items
    db.run(
      `INSERT INTO context_items (id, type, content, metadata_json, score, recency_factor, access_factor, last_accessed_at, access_count, tokens, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        "item-1",
        "file",
        "src/domain/models/User.ts",
        JSON.stringify({ source: "file_access", module: "src/domain", sessionId: "session-1" }),
        0.85,
        0.9,
        0.75,
        nowMs,
        5,
        100,
        "active",
      ]
    );

    db.close();

    // Create vector DB directory
    await fs.mkdir(vectorDbPath, { recursive: true });

    // Create Fastify instance with API routes
    server = Fastify({ logger: false });
    await registerApiRoutes(server, { dbPath, vectorDbPath });
    await server.listen({ port: 0 }); // Random available port
  });

  afterEach(async () => {
    await server.close();

    // Clean up test directory
    try {
      await fs.rm(testDir, { recursive: true, force: true });
    } catch {
      // Ignore cleanup errors
    }
  });

  describe("T152: Full Dashboard API Workflow", () => {
    it("should serve all API endpoints successfully", async () => {
      const endpoints = [
        "/api/project",
        "/api/sessions",
        "/api/modules",
        "/api/embeddings",
        "/api/context",
        "/api/health",
        "/api/linked-projects",
      ];

      for (const endpoint of endpoints) {
        const response = await server.inject({
          method: "GET",
          url: endpoint,
        });

        expect(response.statusCode).toBe(200);
        expect(response.headers["content-type"]).toContain("application/json");

        const data = JSON.parse(response.payload);
        expect(data).toBeDefined();
      }
    });

    it("should return project overview with test data stats", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/project",
      });

      const data = JSON.parse(response.payload);

      // Should count chunks and modules from test data
      expect(data.moduleCount).toBeGreaterThan(0);
      expect(data.fileCount).toBeGreaterThan(0);
    });

    it("should return sessions from test database", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/sessions",
      });

      const sessions = JSON.parse(response.payload);

      // Should have our 2 test sessions
      expect(sessions.length).toBeGreaterThanOrEqual(2);

      // Sessions should be sorted by start time (newest first)
      const sessionIds = sessions.map((s: { id: string }) => s.id);
      expect(sessionIds).toContain("session-1");
      expect(sessionIds).toContain("session-2");
    });

    it("should return session details with files and discoveries", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/sessions/session-1",
      });

      expect(response.statusCode).toBe(200);

      const session = JSON.parse(response.payload);

      expect(session.id).toBe("session-1");
      expect(session.files).toBeDefined();
      expect(session.discoveries).toBeDefined();

      // Should have 2 files
      expect(session.files.length).toBe(2);

      // Should have 1 discovery
      expect(session.discoveries.length).toBe(1);
      expect(session.discoveries[0].content).toBe("Always validate user input");
    });

    it("should return module graph from chunks", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/modules",
      });

      const data = JSON.parse(response.payload);

      expect(data.nodes).toBeDefined();
      expect(data.edges).toBeDefined();

      // Should have nodes for our modules (extracted from file paths)
      const moduleNames = data.nodes.map((n: { name: string }) => n.name);
      // Module names are extracted from the immediate parent directory
      expect(moduleNames).toContain("models");
      expect(moduleNames).toContain("services");
    });

    it("should handle CORS for dashboard frontend", async () => {
      const response = await server.inject({
        method: "OPTIONS",
        url: "/api/project",
        headers: {
          origin: "http://localhost:3456",
          "access-control-request-method": "GET",
        },
      });

      // Should allow CORS
      expect([200, 204]).toContain(response.statusCode);
    });

    it("should return embeddings statistics", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/embeddings",
      });

      const data = JSON.parse(response.payload);

      expect(data.totalCount).toBeDefined();
      expect(data.queueSize).toBeDefined();
      expect(data.errorCount).toBeDefined();
    });

    it("should return context window usage", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/context",
      });

      const data = JSON.parse(response.payload);

      expect(data.current).toBeGreaterThanOrEqual(0);
      expect(data.max).toBeGreaterThan(0);
      expect(data.percentage).toBeGreaterThanOrEqual(0);
      expect(data.percentage).toBeLessThanOrEqual(100);
    });

    it("should return health status with services", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/health",
      });

      const data = JSON.parse(response.payload);

      expect(Array.isArray(data.services)).toBe(true);
      expect(data.services.length).toBeGreaterThan(0);

      // Each service should have name and status
      data.services.forEach((service: { name: string; status: string }) => {
        expect(service.name).toBeDefined();
        expect(["running", "stopped", "error"]).toContain(service.status);
      });
    });

    it("should return linked projects list", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/linked-projects",
      });

      const data = JSON.parse(response.payload);

      expect(Array.isArray(data)).toBe(true);
      // May be empty if no projects linked
    });

    it("should handle pagination on sessions endpoint", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/sessions?limit=1",
      });

      const sessions = JSON.parse(response.payload);

      expect(sessions.length).toBeLessThanOrEqual(1);
    });

    it("should return 404 for non-existent session", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/sessions/non-existent-session-id",
      });

      expect(response.statusCode).toBe(404);
    });

    it("should calculate session duration correctly", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/sessions",
      });

      const sessions = JSON.parse(response.payload);

      const completedSession = sessions.find(
        (s: { id: string; endTime?: string }) =>
          s.id === "session-1" && s.endTime
      );

      if (completedSession) {
        expect(completedSession.duration).toBeGreaterThan(0);
        // Duration should be approximately 60 minutes (1 hour)
        expect(completedSession.duration).toBeCloseTo(60, 0);
      }
    });

    it("should count files and discoveries per session", async () => {
      const response = await server.inject({
        method: "GET",
        url: "/api/sessions",
      });

      const sessions = JSON.parse(response.payload);

      const session1 = sessions.find((s: { id: string }) => s.id === "session-1");

      expect(session1.filesCount).toBe(2);
      expect(session1.discoveriesCount).toBe(1);
    });
  });

  describe("API Performance", () => {
    it("should respond to /api/project in under 100ms", async () => {
      const start = Date.now();

      await server.inject({
        method: "GET",
        url: "/api/project",
      });

      const duration = Date.now() - start;
      expect(duration).toBeLessThan(100);
    });

    it("should handle concurrent requests", async () => {
      const requests = Array.from({ length: 10 }, () =>
        server.inject({
          method: "GET",
          url: "/api/project",
        })
      );

      const responses = await Promise.all(requests);

      responses.forEach((response) => {
        expect(response.statusCode).toBe(200);
      });
    });
  });
});
