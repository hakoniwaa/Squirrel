/**
 * PruneContext Tests
 *
 * Tests for context window pruning use case.
 */

import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { PruneContext } from "../../../src/application/use-cases/PruneContext";
import { SQLiteAdapter } from "@kioku/api/infrastructure/storage/sqlite-adapter";
import type { ContextItem } from "../../../src/domain/models/ContextItem";
import { mkdtempSync, rmSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";

describe("PruneContext", () => {
  let testDir: string;
  let pruner: PruneContext;
  let sqliteAdapter: SQLiteAdapter;

  beforeEach(() => {
    testDir = mkdtempSync(join(tmpdir(), "prune-context-test-"));
    const dbPath = join(testDir, "test.db");
    sqliteAdapter = new SQLiteAdapter(dbPath);
    pruner = new PruneContext(sqliteAdapter);
  });

  afterEach(() => {
    sqliteAdapter.close();
    rmSync(testDir, { recursive: true, force: true });
  });

  describe("execute", () => {
    it("should calculate window usage", async () => {
      // Add some context items
      for (let i = 0; i < 10; i++) {
        const item: ContextItem = {
          id: `item-${i}`,
          type: "file",
          content: "x".repeat(1000), // 1000 chars = ~250 tokens
          metadata: { source: `src/file-${i}.ts` },
          scoring: {
            score: 0.5,
            recencyFactor: 0.5,
            accessFactor: 0.5,
            lastAccessedAt: new Date(),
            accessCount: 1,
          },
          tokens: 250,
          status: "active",
        };
        sqliteAdapter.saveContextItem(item);
      }

      const usage = await pruner.calculateUsage();

      // 10 items * 250 tokens = 2500 tokens
      // Max is 100000, so 2.5%
      expect(usage).toBeCloseTo(0.025, 3);
    });

    it("should not prune if below 80% threshold", async () => {
      // Add items totaling 50% usage (50k tokens)
      for (let i = 0; i < 50; i++) {
        const item: ContextItem = {
          id: `item-${i}`,
          type: "file",
          content: "x".repeat(4000), // 4000 chars = ~1000 tokens
          metadata: { source: `src/file-${i}.ts` },
          scoring: {
            score: 0.5,
            recencyFactor: 0.5,
            accessFactor: 0.5,
            lastAccessedAt: new Date(),
            accessCount: 1,
          },
          tokens: 1000,
          status: "active",
        };
        sqliteAdapter.saveContextItem(item);
      }

      const result = await pruner.execute();

      expect(result.pruned).toBe(false);
      expect(result.archivedCount).toBe(0);
    });

    it("should prune when above 80% threshold", async () => {
      // Add items totaling 85% usage (85k tokens)
      for (let i = 0; i < 85; i++) {
        const item: ContextItem = {
          id: `item-${i}`,
          type: "file",
          content: "x".repeat(4000), // 4000 chars = ~1000 tokens
          metadata: { source: `src/file-${i}.ts` },
          scoring: {
            score: i / 100, // Varying scores
            recencyFactor: 0.5,
            accessFactor: 0.5,
            lastAccessedAt: new Date(),
            accessCount: 1,
          },
          tokens: 1000,
          status: "active",
        };
        sqliteAdapter.saveContextItem(item);
      }

      const result = await pruner.execute();

      expect(result.pruned).toBe(true);
      expect(result.archivedCount).toBeGreaterThan(0);
    });

    it("should archive bottom 20% of items", async () => {
      // Add 100 items with varying scores
      for (let i = 0; i < 100; i++) {
        const item: ContextItem = {
          id: `item-${i}`,
          type: "file",
          content: "x".repeat(4000), // 4000 chars = ~1000 tokens
          metadata: { source: `src/file-${i}.ts` },
          scoring: {
            score: i / 100, // Scores from 0.00 to 0.99
            recencyFactor: 0.5,
            accessFactor: 0.5,
            lastAccessedAt: new Date(),
            accessCount: 1,
          },
          tokens: 1000,
          status: "active",
        };
        sqliteAdapter.saveContextItem(item);
      }

      const result = await pruner.execute();

      expect(result.pruned).toBe(true);
      // Should archive 20 items (20%)
      expect(result.archivedCount).toBe(20);

      // Verify archived items are lowest scoring
      const archivedItems = sqliteAdapter.getContextItemsByStatus("archived");
      expect(archivedItems.length).toBe(20);

      // All archived items should have score < 0.20
      for (const item of archivedItems) {
        expect(item.scoring.score).toBeLessThan(0.2);
      }
    });

    it("should preserve high-score items", async () => {
      // Add items with varying scores
      for (let i = 0; i < 100; i++) {
        const item: ContextItem = {
          id: `item-${i}`,
          type: "file",
          content: "x".repeat(4000),
          metadata: { source: `src/file-${i}.ts` },
          scoring: {
            score: i / 100,
            recencyFactor: 0.5,
            accessFactor: 0.5,
            lastAccessedAt: new Date(),
            accessCount: 1,
          },
          tokens: 1000,
          status: "active",
        };
        sqliteAdapter.saveContextItem(item);
      }

      await pruner.execute();

      // Check that high-score items are still active
      const activeItems = sqliteAdapter.getContextItemsByStatus("active");

      // All active items should have score >= 0.20
      for (const item of activeItems) {
        expect(item.scoring.score).toBeGreaterThanOrEqual(0.2);
      }
    });

    it("should log pruning decisions", async () => {
      // Add items above threshold (85k tokens)
      for (let i = 0; i < 85; i++) {
        const item: ContextItem = {
          id: `item-${i}`,
          type: "file",
          content: "x".repeat(4000),
          metadata: { source: `src/file-${i}.ts` },
          scoring: {
            score: i / 100,
            recencyFactor: 0.5,
            accessFactor: 0.5,
            lastAccessedAt: new Date(),
            accessCount: 1,
          },
          tokens: 1000,
          status: "active",
        };
        sqliteAdapter.saveContextItem(item);
      }

      const result = await pruner.execute();

      // Should return detailed result
      expect(result).toHaveProperty("usageBefore");
      expect(result).toHaveProperty("usageAfter");
      expect(result).toHaveProperty("archivedCount");
      expect(result.usageBefore).toBeGreaterThan(result.usageAfter);
    });

    it("should handle empty context gracefully", async () => {
      const result = await pruner.execute();

      expect(result.pruned).toBe(false);
      expect(result.archivedCount).toBe(0);
      expect(result.usageBefore).toBe(0);
    });
  });
});
