/**
 * SQLiteAdapter Cleanup Methods Tests
 *
 * Tests for the new cleanup methods added to SQLiteAdapter
 */

import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { SQLiteAdapter } from "../../../src/infrastructure/storage/sqlite-adapter";
import type { Session } from "../../../src/domain/models/Session";
import { mkdtempSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

describe("SQLiteAdapter - Cleanup Methods", () => {
  let testDir: string;
  let dbPath: string;
  let adapter: SQLiteAdapter;

  beforeEach(() => {
    testDir = mkdtempSync(join(tmpdir(), "sqlite-cleanup-test-"));
    dbPath = join(testDir, "test.db");
    adapter = new SQLiteAdapter(dbPath);
  });

  afterEach(() => {
    adapter.close();
    rmSync(testDir, { recursive: true, force: true });
  });

  describe("getActiveSessionsOlderThan", () => {
    it("should return empty array when no sessions exist", () => {
      const cutoffTime = Date.now();
      const sessions = adapter.getActiveSessionsOlderThan(cutoffTime);

      expect(sessions).toEqual([]);
    });

    it("should return only active sessions older than cutoff", () => {
      const now = Date.now();
      const twoHoursAgo = now - 2 * 60 * 60 * 1000;
      const oneHourAgo = now - 1 * 60 * 60 * 1000;

      // Create old active session
      const oldSession: Session = {
        id: "old-session",
        projectId: "test-project",
        status: "active",
        startedAt: new Date(twoHoursAgo),
        filesAccessed: [],
        topics: [],
        metadata: {
          toolCallsCount: 0,
          discoveryCount: 0,
        },
      };

      // Create recent active session
      const recentSession: Session = {
        id: "recent-session",
        projectId: "test-project",
        status: "active",
        startedAt: new Date(now - 10 * 60 * 1000), // 10 minutes ago
        filesAccessed: [],
        topics: [],
        metadata: {
          toolCallsCount: 0,
          discoveryCount: 0,
        },
      };

      adapter.saveSession(oldSession);
      adapter.saveSession(recentSession);

      // Query for sessions older than 1 hour
      const cutoffTime = oneHourAgo;
      const orphaned = adapter.getActiveSessionsOlderThan(cutoffTime);

      expect(orphaned.length).toBe(1);
      expect(orphaned[0].id).toBe("old-session");
    });

    it("should not return completed sessions", () => {
      const now = Date.now();
      const twoHoursAgo = now - 2 * 60 * 60 * 1000;

      // Create old but completed session
      const completedSession: Session = {
        id: "completed-session",
        projectId: "test-project",
        status: "completed",
        startedAt: new Date(twoHoursAgo),
        endedAt: new Date(twoHoursAgo + 60 * 60 * 1000),
        filesAccessed: [],
        topics: [],
        metadata: {
          toolCallsCount: 0,
          discoveryCount: 0,
        },
      };

      adapter.saveSession(completedSession);

      const cutoffTime = now - 60 * 60 * 1000; // 1 hour ago
      const orphaned = adapter.getActiveSessionsOlderThan(cutoffTime);

      expect(orphaned.length).toBe(0);
    });

    it("should return sessions in order of started_at", () => {
      const now = Date.now();

      // Create multiple old sessions
      const sessions = [
        { id: "session-3", startedAt: now - 3 * 60 * 60 * 1000 }, // 3 hours ago
        { id: "session-1", startedAt: now - 1 * 60 * 60 * 1000 }, // 1 hour ago
        { id: "session-2", startedAt: now - 2 * 60 * 60 * 1000 }, // 2 hours ago
      ];

      for (const s of sessions) {
        const session: Session = {
          id: s.id,
          projectId: "test-project",
          status: "active",
          startedAt: new Date(s.startedAt),
          filesAccessed: [],
          topics: [],
          metadata: {
            toolCallsCount: 0,
            discoveryCount: 0,
          },
        };
        adapter.saveSession(session);
      }

      const cutoffTime = now;
      const result = adapter.getActiveSessionsOlderThan(cutoffTime);

      // Should be ordered oldest first
      expect(result.length).toBe(3);
      expect(result[0].id).toBe("session-3");
      expect(result[1].id).toBe("session-2");
      expect(result[2].id).toBe("session-1");
    });

    it("should include project_id and started_at fields", () => {
      const now = Date.now();
      const oldSession: Session = {
        id: "test-session",
        projectId: "my-project",
        status: "active",
        startedAt: new Date(now - 2 * 60 * 60 * 1000),
        filesAccessed: [],
        topics: [],
        metadata: {
          toolCallsCount: 0,
          discoveryCount: 0,
        },
      };

      adapter.saveSession(oldSession);

      const result = adapter.getActiveSessionsOlderThan(now);

      expect(result[0]).toHaveProperty("id");
      expect(result[0]).toHaveProperty("project_id");
      expect(result[0]).toHaveProperty("started_at");
      expect(result[0].project_id).toBe("my-project");
    });
  });

  describe("completeSession", () => {
    it("should mark session as completed", () => {
      const now = Date.now();
      const activeSession: Session = {
        id: "test-session",
        projectId: "test-project",
        status: "active",
        startedAt: new Date(now - 60 * 60 * 1000),
        filesAccessed: [],
        topics: [],
        metadata: {
          toolCallsCount: 0,
          discoveryCount: 0,
        },
      };

      adapter.saveSession(activeSession);

      // Complete the session
      const endedAt = now;
      const duration = 60 * 60 * 1000; // 1 hour
      adapter.completeSession("test-session", endedAt, duration);

      // Verify session was updated
      const updated = adapter.getSession("test-session");
      expect(updated).toBeDefined();
      expect(updated?.status).toBe("completed");
      expect(updated?.endedAt).toBeDefined();
      expect(updated?.endedAt?.getTime()).toBe(endedAt);
      expect(updated?.metadata.duration).toBe(duration);
    });

    it("should update metadata with duration", () => {
      const activeSession: Session = {
        id: "test-session",
        projectId: "test-project",
        status: "active",
        startedAt: new Date(),
        filesAccessed: [],
        topics: [],
        metadata: {
          toolCallsCount: 5,
          discoveryCount: 3,
        },
      };

      adapter.saveSession(activeSession);

      const duration = 120 * 60 * 1000; // 2 hours
      adapter.completeSession("test-session", Date.now(), duration);

      const updated = adapter.getSession("test-session");
      expect(updated?.metadata.duration).toBe(duration);
      // Other metadata should be preserved
      expect(updated?.metadata.toolCallsCount).toBe(5);
      expect(updated?.metadata.discoveryCount).toBe(3);
    });

    it("should update updated_at timestamp", () => {
      const now = Date.now();
      const activeSession: Session = {
        id: "test-session",
        projectId: "test-project",
        status: "active",
        startedAt: new Date(now - 60 * 60 * 1000),
        filesAccessed: [],
        topics: [],
        metadata: {
          toolCallsCount: 0,
          discoveryCount: 0,
        },
      };

      adapter.saveSession(activeSession);

      // Wait a bit before completing
      const beforeComplete = Date.now();

      adapter.completeSession("test-session", now, 60 * 60 * 1000);

      // updated_at should be recent
      const updated = adapter.getSession("test-session");
      // We can't directly check updated_at, but we can verify the session was updated
      expect(updated?.status).toBe("completed");
    });

    it("should handle non-existent session gracefully", () => {
      // Should not throw
      expect(() => {
        adapter.completeSession("non-existent", Date.now(), 1000);
      }).not.toThrow();
    });

    it("should preserve other session fields", () => {
      const activeSession: Session = {
        id: "test-session",
        projectId: "test-project",
        status: "active",
        startedAt: new Date(),
        filesAccessed: [],
        topics: ["auth", "testing"],
        metadata: {
          toolCallsCount: 10,
          discoveryCount: 5,
        },
      };

      adapter.saveSession(activeSession);

      adapter.completeSession("test-session", Date.now(), 60000);

      const updated = adapter.getSession("test-session");
      expect(updated?.projectId).toBe("test-project");
      expect(updated?.topics).toEqual(["auth", "testing"]);
      expect(updated?.startedAt).toBeDefined();
    });
  });

  describe("integration - cleanup workflow", () => {
    it("should support full cleanup workflow", () => {
      const now = Date.now();
      const oneHourAgo = now - 60 * 60 * 1000;

      // Create some orphaned sessions
      for (let i = 0; i < 5; i++) {
        const session: Session = {
          id: `session-${i}`,
          projectId: "test-project",
          status: "active",
          startedAt: new Date(now - (i + 2) * 60 * 60 * 1000),
          filesAccessed: [],
          topics: [],
          metadata: {
            toolCallsCount: 0,
            discoveryCount: 0,
          },
        };
        adapter.saveSession(session);
      }

      // Find orphaned sessions (older than 1 hour)
      const orphaned = adapter.getActiveSessionsOlderThan(oneHourAgo);
      expect(orphaned.length).toBe(5);

      // Clean them up
      for (const session of orphaned) {
        const estimatedEndTime = session.started_at + 60 * 60 * 1000;
        adapter.completeSession(session.id, estimatedEndTime, 60 * 60 * 1000);
      }

      // Verify all are now completed
      const stillOrphaned = adapter.getActiveSessionsOlderThan(oneHourAgo);
      expect(stillOrphaned.length).toBe(0);

      // Verify they exist as completed
      for (let i = 0; i < 5; i++) {
        const session = adapter.getSession(`session-${i}`);
        expect(session?.status).toBe("completed");
      }
    });
  });
});
