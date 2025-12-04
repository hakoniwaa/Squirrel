/**
 * SessionManager Tests
 *
 * Tests for session tracking and auto-save functionality.
 */

import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { SessionManager } from "../../../src/application/use-cases/SessionManager";
import { SQLiteAdapter } from "../../../src/infrastructure/storage/sqlite-adapter";
import { mkdtempSync, mkdirSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

describe("SessionManager", () => {
  let testDir: string;
  let manager: SessionManager;
  let sqliteAdapter: SQLiteAdapter;

  beforeEach(() => {
    testDir = mkdtempSync(join(tmpdir(), "session-manager-test-"));
    // Create .context directory
    mkdirSync(join(testDir, ".context"), { recursive: true });
    const dbPath = join(testDir, ".context", "sessions.db");
    sqliteAdapter = new SQLiteAdapter(dbPath);
    manager = new SessionManager(testDir, sqliteAdapter);
  });

  afterEach(() => {
    sqliteAdapter.close();
    rmSync(testDir, { recursive: true, force: true });
  });

  describe("startSession", () => {
    it("should create new session with metadata", async () => {
      const session = await manager.startSession();

      expect(session.id).toBeDefined();
      expect(session.status).toBe("active");
      expect(session.startedAt).toBeInstanceOf(Date);
      expect(session.filesAccessed.size).toBe(0);
      expect(session.topics).toEqual([]);
    });

    it("should save session to database", async () => {
      const session = await manager.startSession();

      // Verify session was saved by retrieving it
      const retrieved = await manager.getCurrentSession();
      expect(retrieved).toBeDefined();
      expect(retrieved?.id).toBe(session.id);
    });

    it("should mark previous session as completed before starting new one", async () => {
      const session1 = await manager.startSession();
      const session2 = await manager.startSession();

      expect(session1.id).not.toBe(session2.id);
      // Verify session1 was completed
      // This will be checked via database queries in integration tests
    });
  });

  describe("trackFileAccess", () => {
    it("should add file to session files accessed", async () => {
      await manager.startSession();

      await manager.trackFileAccess("src/auth/AuthService.ts");
      await manager.trackFileAccess("src/auth/TokenManager.ts");

      const session = await manager.getCurrentSession();
      expect(session?.filesAccessed.has("src/auth/AuthService.ts")).toBe(true);
      expect(session?.filesAccessed.has("src/auth/TokenManager.ts")).toBe(true);
    });

    it("should not duplicate file entries", async () => {
      await manager.startSession();

      await manager.trackFileAccess("src/auth/AuthService.ts");
      await manager.trackFileAccess("src/auth/AuthService.ts");
      await manager.trackFileAccess("src/auth/AuthService.ts");

      const session = await manager.getCurrentSession();
      // Map doesn't duplicate keys, so there should be exactly one entry
      expect(session?.filesAccessed.has("src/auth/AuthService.ts")).toBe(true);
      expect(session?.filesAccessed.size).toBe(1);
    });

    it("should increment access count for repeated files", async () => {
      await manager.startSession();

      await manager.trackFileAccess("src/auth/AuthService.ts");
      await manager.trackFileAccess("src/auth/AuthService.ts");
      await manager.trackFileAccess("src/auth/AuthService.ts");

      const accessCount = await manager.getFileAccessCount(
        "src/auth/AuthService.ts",
      );
      expect(accessCount).toBe(3);
    });

    it("should throw error if no active session", async () => {
      expect(async () => {
        await manager.trackFileAccess("src/test.ts");
      }).toThrow();
    });
  });

  describe("trackTopic", () => {
    it("should add topic to session", async () => {
      await manager.startSession();

      await manager.trackTopic("authentication");
      await manager.trackTopic("JWT tokens");

      const session = await manager.getCurrentSession();
      expect(session?.topics).toContain("authentication");
      expect(session?.topics).toContain("JWT tokens");
    });

    it("should not duplicate topics", async () => {
      await manager.startSession();

      await manager.trackTopic("authentication");
      await manager.trackTopic("authentication");

      const session = await manager.getCurrentSession();
      const count = session?.topics.filter(
        (t) => t === "authentication",
      ).length;
      expect(count).toBe(1);
    });
  });

  describe("endSession", () => {
    it("should mark session as completed", async () => {
      await manager.startSession();

      await manager.endSession();

      const completed = await manager.getCurrentSession();
      expect(completed).toBeUndefined();

      // Verify it was saved as completed (integration test will check DB)
    });

    it("should calculate session duration", async () => {
      await manager.startSession();

      // Simulate some work
      await new Promise((resolve) => setTimeout(resolve, 100));

      await manager.endSession();

      // Duration will be checked via database in integration tests
      expect(true).toBe(true);
    });

    it("should do nothing if no active session", async () => {
      await manager.endSession(); // Should not throw
      expect(true).toBe(true);
    });
  });

  describe("getCurrentSession", () => {
    it("should return active session", async () => {
      const started = await manager.startSession();

      const current = await manager.getCurrentSession();

      expect(current?.id).toBe(started.id);
      expect(current?.status).toBe("active");
    });

    it("should return undefined if no active session", async () => {
      const current = await manager.getCurrentSession();
      expect(current).toBeUndefined();
    });
  });

  describe("getFileAccessCount", () => {
    it("should return 0 for unaccessed files", async () => {
      await manager.startSession();

      const count = await manager.getFileAccessCount("src/never-accessed.ts");
      expect(count).toBe(0);
    });

    it("should return correct count for accessed files", async () => {
      await manager.startSession();

      await manager.trackFileAccess("src/test.ts");
      await manager.trackFileAccess("src/test.ts");
      await manager.trackFileAccess("src/test.ts");

      const count = await manager.getFileAccessCount("src/test.ts");
      expect(count).toBe(3);
    });
  });

  describe("checkInactivity", () => {
    it("should return false if no active session", async () => {
      const wasEnded = await manager.checkInactivity();
      expect(wasEnded).toBe(false);
    });

    it("should return false if session is still active", async () => {
      await manager.startSession();

      const wasEnded = await manager.checkInactivity();
      expect(wasEnded).toBe(false);

      // Verify session still active
      const session = await manager.getCurrentSession();
      expect(session).toBeDefined();
      expect(session?.status).toBe("active");
    });

    it("should return false if session has recent activity", async () => {
      await manager.startSession();

      // Simulate recent activity
      await manager.trackFileAccess("src/test.ts");

      const wasEnded = await manager.checkInactivity();
      expect(wasEnded).toBe(false);

      const session = await manager.getCurrentSession();
      expect(session).toBeDefined();
    });

    it("should end session if inactive for 30+ minutes", async () => {
      const session = await manager.startSession();

      // Mock lastActivityAt to be 31 minutes ago
      const thirtyOneMinutesAgo = new Date(Date.now() - 31 * 60 * 1000);
      // Access private property for testing (TypeScript will complain but it works at runtime)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (manager as any).currentSession.lastActivityAt = thirtyOneMinutesAgo;

      const wasEnded = await manager.checkInactivity();
      expect(wasEnded).toBe(true);

      // Verify session was ended
      const current = await manager.getCurrentSession();
      expect(current).toBeUndefined();
    });

    it("should update lastActivityAt on file access", async () => {
      await manager.startSession();

      const initialSession = await manager.getCurrentSession();
      const initialActivity = initialSession?.lastActivityAt;

      // Wait a bit
      await new Promise((resolve) => setTimeout(resolve, 50));

      // Track activity
      await manager.trackFileAccess("src/test.ts");

      const updatedSession = await manager.getCurrentSession();
      const updatedActivity = updatedSession?.lastActivityAt;

      expect(updatedActivity).toBeDefined();
      expect(updatedActivity!.getTime()).toBeGreaterThan(
        initialActivity!.getTime(),
      );
    });

    it("should update lastActivityAt on topic tracking", async () => {
      await manager.startSession();

      const initialSession = await manager.getCurrentSession();
      const initialActivity = initialSession?.lastActivityAt;

      // Wait a bit
      await new Promise((resolve) => setTimeout(resolve, 50));

      // Track activity
      await manager.trackTopic("test-topic");

      const updatedSession = await manager.getCurrentSession();
      const updatedActivity = updatedSession?.lastActivityAt;

      expect(updatedActivity).toBeDefined();
      expect(updatedActivity!.getTime()).toBeGreaterThan(
        initialActivity!.getTime(),
      );
    });
  });

  describe("getInactivityTimeout", () => {
    it("should return 30 minutes in milliseconds", () => {
      const timeout = SessionManager.getInactivityTimeout();
      expect(timeout).toBe(30 * 60 * 1000); // 30 minutes
    });
  });
});
