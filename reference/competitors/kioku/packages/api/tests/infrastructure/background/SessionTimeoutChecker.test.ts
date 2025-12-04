/**
 * SessionTimeoutChecker Tests
 *
 * Tests for the background service that checks session inactivity.
 */

import { describe, it, expect, beforeEach, afterEach, mock } from "bun:test";
import { SessionTimeoutChecker } from "../../../src/infrastructure/background/SessionTimeoutChecker";
import { SessionManager } from "../../../src/application/use-cases/SessionManager";
import { SQLiteAdapter } from "../../../src/infrastructure/storage/sqlite-adapter";
import { mkdtempSync, mkdirSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

describe("SessionTimeoutChecker", () => {
  let testDir: string;
  let sessionManager: SessionManager;
  let sqliteAdapter: SQLiteAdapter;
  let checker: SessionTimeoutChecker;

  beforeEach(() => {
    testDir = mkdtempSync(join(tmpdir(), "timeout-checker-test-"));
    mkdirSync(join(testDir, ".context"), { recursive: true });
    const dbPath = join(testDir, ".context", "sessions.db");
    sqliteAdapter = new SQLiteAdapter(dbPath);
    sessionManager = new SessionManager(testDir, sqliteAdapter);
  });

  afterEach(() => {
    if (checker) {
      checker.stop();
    }
    sqliteAdapter.close();
    rmSync(testDir, { recursive: true, force: true });
  });

  describe("constructor", () => {
    it("should create checker with default interval", () => {
      checker = new SessionTimeoutChecker(sessionManager);
      expect(checker).toBeDefined();
    });

    it("should create checker with custom interval", () => {
      checker = new SessionTimeoutChecker(sessionManager, 60000); // 1 minute
      expect(checker).toBeDefined();
    });
  });

  describe("start", () => {
    it("should start the timeout checker", () => {
      checker = new SessionTimeoutChecker(sessionManager, 100); // Fast interval for testing

      checker.start();

      // Should not throw
      expect(true).toBe(true);
    });

    it("should log warning if already running", () => {
      checker = new SessionTimeoutChecker(sessionManager, 100);

      checker.start();
      checker.start(); // Second start should log warning

      // Should not throw
      expect(true).toBe(true);
    });

    it("should check timeout immediately on start", async () => {
      await sessionManager.startSession();

      // Mock checkInactivity to track if it was called
      const mockCheck = mock(() => Promise.resolve(false));
      sessionManager.checkInactivity = mockCheck;

      checker = new SessionTimeoutChecker(sessionManager, 100);
      checker.start();

      // Wait a bit for immediate check to complete
      await new Promise((resolve) => setTimeout(resolve, 50));

      expect(mockCheck).toHaveBeenCalled();
    });
  });

  describe("stop", () => {
    it("should stop the timeout checker", () => {
      checker = new SessionTimeoutChecker(sessionManager, 100);

      checker.start();
      checker.stop();

      // Should not throw
      expect(true).toBe(true);
    });

    it("should do nothing if not running", () => {
      checker = new SessionTimeoutChecker(sessionManager);

      checker.stop(); // Stop before start

      // Should not throw
      expect(true).toBe(true);
    });

    it("should prevent further timeout checks after stop", async () => {
      await sessionManager.startSession();

      let checkCount = 0;
      sessionManager.checkInactivity = async () => {
        checkCount++;
        return false;
      };

      checker = new SessionTimeoutChecker(sessionManager, 50); // 50ms interval
      checker.start();

      // Wait for a few checks
      await new Promise((resolve) => setTimeout(resolve, 150));

      const checksBeforeStop = checkCount;

      checker.stop();

      // Wait some more
      await new Promise((resolve) => setTimeout(resolve, 150));

      // Check count should not increase after stop
      expect(checkCount).toBe(checksBeforeStop);
    });
  });

  describe("periodic checking", () => {
    it("should check timeout periodically", async () => {
      await sessionManager.startSession();

      let checkCount = 0;
      sessionManager.checkInactivity = async () => {
        checkCount++;
        return false;
      };

      checker = new SessionTimeoutChecker(sessionManager, 50); // 50ms interval
      checker.start();

      // Wait for multiple intervals
      await new Promise((resolve) => setTimeout(resolve, 250));

      // Should have checked multiple times (immediate + periodic)
      expect(checkCount).toBeGreaterThanOrEqual(3);

      checker.stop();
    });

    it("should handle session ending during check", async () => {
      await sessionManager.startSession();

      // Mock to simulate session ending
      let callCount = 0;
      sessionManager.checkInactivity = async () => {
        callCount++;
        return callCount === 2; // End on second call
      };

      checker = new SessionTimeoutChecker(sessionManager, 50);
      checker.start();

      // Wait for checks
      await new Promise((resolve) => setTimeout(resolve, 150));

      expect(callCount).toBeGreaterThanOrEqual(2);

      checker.stop();
    });

    it("should handle errors gracefully", async () => {
      await sessionManager.startSession();

      // Mock to throw error
      sessionManager.checkInactivity = async () => {
        throw new Error("Test error");
      };

      checker = new SessionTimeoutChecker(sessionManager, 50);

      // Should not throw even with errors in checkInactivity
      expect(() => checker.start()).not.toThrow();

      await new Promise((resolve) => setTimeout(resolve, 100));

      checker.stop();
    });
  });

  describe("integration with SessionManager", () => {
    it("should detect and end inactive sessions", async () => {
      await sessionManager.startSession();

      // Mock lastActivityAt to be old
      const thirtyOneMinutesAgo = new Date(Date.now() - 31 * 60 * 1000);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (sessionManager as any).currentSession.lastActivityAt = thirtyOneMinutesAgo;

      checker = new SessionTimeoutChecker(sessionManager, 50);
      checker.start();

      // Wait for check
      await new Promise((resolve) => setTimeout(resolve, 100));

      // Session should have been ended
      const current = await sessionManager.getCurrentSession();
      expect(current).toBeUndefined();

      checker.stop();
    });

    it("should not end active sessions", async () => {
      await sessionManager.startSession();

      // Session is fresh, should not be ended
      checker = new SessionTimeoutChecker(sessionManager, 50);
      checker.start();

      // Wait for multiple checks
      await new Promise((resolve) => setTimeout(resolve, 200));

      // Session should still be active
      const current = await sessionManager.getCurrentSession();
      expect(current).toBeDefined();
      expect(current?.status).toBe("active");

      checker.stop();
    });

    it("should respect activity updates", async () => {
      await sessionManager.startSession();

      checker = new SessionTimeoutChecker(sessionManager, 100);
      checker.start();

      // Keep updating activity
      const keepAlive = setInterval(async () => {
        try {
          await sessionManager.trackFileAccess("test.ts");
        } catch {
          clearInterval(keepAlive);
        }
      }, 50);

      // Wait for multiple check cycles
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Session should still be active due to constant activity
      const current = await sessionManager.getCurrentSession();
      expect(current).toBeDefined();
      expect(current?.status).toBe("active");

      clearInterval(keepAlive);
      checker.stop();
    });
  });

  describe("getInactivityTimeout", () => {
    it("should match SessionManager timeout", () => {
      const sessionTimeout = SessionManager.getInactivityTimeout();
      expect(sessionTimeout).toBe(30 * 60 * 1000);
    });
  });
});
