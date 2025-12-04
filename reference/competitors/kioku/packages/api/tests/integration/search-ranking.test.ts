/**
 * Search Ranking Integration Tests
 *
 * Tests that search results are intelligently ranked by recency, module context,
 * and frequency - not just semantic similarity.
 *
 * Validates User Story 5: Intelligent Result Ranking
 */

import { describe, it, expect, beforeEach } from "vitest";
import { RankSearchResultsUseCase } from "../../../src/application/use-cases/RankSearchResultsUseCase";
import type { SearchResult } from "../../../src/domain/models/SearchResult";

describe("Search Ranking Integration", () => {
  let rankSearchResults: RankSearchResultsUseCase;

  beforeEach(() => {
    rankSearchResults = new RankSearchResultsUseCase();
  });

  describe("T112: Full ranking workflow with realistic data", () => {
    it("should rank recent files higher than old files with same semantic score", async () => {
      const now = new Date();
      const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

      const results: SearchResult[] = [
        {
          id: "old-chunk",
          type: "chunk",
          filePath: "/project/src/auth/old-handler.ts",
          content: "function authenticate() { /* old code */ }",
          chunkName: "authenticate",
          startLine: 10,
          endLine: 20,
          score: 0.85, // Same semantic score
          lastAccessed: thirtyDaysAgo,
          accessCount: 5,
          metadata: {},
        },
        {
          id: "recent-chunk",
          type: "chunk",
          filePath: "/project/src/auth/new-handler.ts",
          content: "function authenticate() { /* new code */ }",
          chunkName: "authenticate",
          startLine: 15,
          endLine: 25,
          score: 0.85, // Same semantic score
          lastAccessed: oneDayAgo,
          accessCount: 5,
          metadata: {},
        },
      ];

      const ranked = rankSearchResults.execute(results, {
        currentModule: undefined,
        now,
      });

      // Recent file should rank higher
      expect(ranked[0].id).toBe("recent-chunk");
      expect(ranked[1].id).toBe("old-chunk");

      // Recent file should have recency boost applied
      expect(ranked[0].recencyBoost).toBe(1.5); // <24h
      expect(ranked[1].recencyBoost).toBe(1.0); // >7d

      // Final scores should reflect boost
      expect(ranked[0].finalScore).toBeGreaterThan(ranked[1].finalScore!);
    });

    it("should rank same-module files higher than different-module files", async () => {
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      const results: SearchResult[] = [
        {
          id: "different-module-chunk",
          type: "chunk",
          filePath: "/project/src/payment/handler.ts",
          content: "function processPayment() {}",
          chunkName: "processPayment",
          startLine: 10,
          endLine: 20,
          score: 0.85,
          module: "payment",
          lastAccessed: yesterday,
          accessCount: 10,
          metadata: {},
        },
        {
          id: "same-module-chunk",
          type: "chunk",
          filePath: "/project/src/auth/handler.ts",
          content: "function validateToken() {}",
          chunkName: "validateToken",
          startLine: 30,
          endLine: 40,
          score: 0.85,
          module: "auth",
          lastAccessed: yesterday,
          accessCount: 10,
          metadata: {},
        },
      ];

      const ranked = rankSearchResults.execute(results, {
        currentModule: "auth", // Currently working in auth module
        now,
      });

      // Same-module file should rank higher
      expect(ranked[0].id).toBe("same-module-chunk");
      expect(ranked[1].id).toBe("different-module-chunk");

      // Same-module should have module boost
      expect(ranked[0].moduleBoost).toBe(1.3);
      expect(ranked[1].moduleBoost).toBe(1.0);
    });

    it("should rank frequently accessed files higher", async () => {
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      const results: SearchResult[] = [
        {
          id: "rare-chunk",
          type: "chunk",
          filePath: "/project/src/util/rare.ts",
          content: "function rarelyUsed() {}",
          chunkName: "rarelyUsed",
          startLine: 10,
          endLine: 20,
          score: 0.85,
          lastAccessed: yesterday,
          accessCount: 1, // Rarely accessed
          metadata: {},
        },
        {
          id: "frequent-chunk",
          type: "chunk",
          filePath: "/project/src/util/common.ts",
          content: "function commonlyUsed() {}",
          chunkName: "commonlyUsed",
          startLine: 30,
          endLine: 40,
          score: 0.85,
          lastAccessed: yesterday,
          accessCount: 50, // Frequently accessed
          metadata: {},
        },
      ];

      const ranked = rankSearchResults.execute(results, {
        currentModule: undefined,
        now,
      });

      // Frequently accessed file should rank higher
      expect(ranked[0].id).toBe("frequent-chunk");
      expect(ranked[1].id).toBe("rare-chunk");

      // Frequency boosts should differ
      expect(ranked[0].frequencyBoost).toBe(1.5); // 50 accesses = 1.5x
      expect(ranked[1].frequencyBoost).toBe(1.01); // 1 access = 1.01x
    });

    it("should combine all boosts multiplicatively for best-case scenario", async () => {
      const now = new Date();
      const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      const results: SearchResult[] = [
        {
          id: "perfect-match",
          type: "chunk",
          filePath: "/project/src/auth/validator.ts",
          content: "function validate() {}",
          chunkName: "validate",
          startLine: 10,
          endLine: 20,
          score: 0.9, // High semantic score
          module: "auth",
          lastAccessed: oneDayAgo, // Recent
          accessCount: 50, // Frequently accessed
          metadata: {},
        },
        {
          id: "poor-match",
          type: "chunk",
          filePath: "/project/src/legacy/old.ts",
          content: "function old() {}",
          chunkName: "old",
          startLine: 30,
          endLine: 40,
          score: 0.5, // Lower semantic score
          module: "legacy",
          lastAccessed: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000), // Old
          accessCount: 0, // Never accessed
          metadata: {},
        },
      ];

      const ranked = rankSearchResults.execute(results, {
        currentModule: "auth",
        now,
      });

      // Perfect match should rank much higher
      expect(ranked[0].id).toBe("perfect-match");
      expect(ranked[1].id).toBe("poor-match");

      // All boosts should be applied
      expect(ranked[0].recencyBoost).toBe(1.5);
      expect(ranked[0].moduleBoost).toBe(1.3);
      expect(ranked[0].frequencyBoost).toBe(1.5);

      // Final score should be multiplicative: 0.9 * 1.5 * 1.3 * 1.5 = 2.6325
      expect(ranked[0].finalScore).toBeCloseTo(2.6325, 2);

      // Poor match has minimal boosts: 0.5 * 1.0 * 1.0 * 1.0 = 0.5
      expect(ranked[1].finalScore).toBeCloseTo(0.5, 2);

      // Quality gap should be significant
      expect(ranked[0].finalScore! / ranked[1].finalScore!).toBeGreaterThan(5);
    });

    it("should handle edge cases gracefully", async () => {
      const now = new Date();

      const results: SearchResult[] = [
        {
          id: "no-metadata",
          type: "chunk",
          filePath: "/project/src/unknown.ts",
          content: "function test() {}",
          score: 0.75,
          lastAccessed: now, // No proper timestamp handling
          accessCount: 0,
          metadata: {},
        },
      ];

      const ranked = rankSearchResults.execute(results, {
        currentModule: undefined,
        now,
      });

      // Should not crash
      expect(ranked.length).toBe(1);
      expect(ranked[0].finalScore).toBeDefined();
      expect(ranked[0].recencyBoost).toBeDefined();
      expect(ranked[0].moduleBoost).toBeDefined();
      expect(ranked[0].frequencyBoost).toBeDefined();
    });

    it("should preserve ranking metadata in results", async () => {
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      const results: SearchResult[] = [
        {
          id: "test-chunk",
          type: "chunk",
          filePath: "/project/src/test.ts",
          content: "function test() {}",
          chunkName: "test",
          startLine: 10,
          endLine: 20,
          score: 0.8,
          module: "test",
          lastAccessed: yesterday,
          accessCount: 25,
          metadata: {},
        },
      ];

      const ranked = rankSearchResults.execute(results, {
        currentModule: "test",
        now,
      });

      const result = ranked[0];

      // All ranking metadata should be present
      expect(result.score).toBe(0.8); // Original score preserved
      expect(result.recencyBoost).toBeDefined();
      expect(result.moduleBoost).toBeDefined();
      expect(result.frequencyBoost).toBeDefined();
      expect(result.finalScore).toBeDefined();

      // Verify boost values are reasonable
      expect(result.recencyBoost).toBeGreaterThanOrEqual(1.0);
      expect(result.recencyBoost).toBeLessThanOrEqual(1.5);
      expect(result.moduleBoost).toBeGreaterThanOrEqual(1.0);
      expect(result.moduleBoost).toBeLessThanOrEqual(1.3);
      expect(result.frequencyBoost).toBeGreaterThanOrEqual(1.0);
      expect(result.frequencyBoost).toBeLessThanOrEqual(1.5);
    });

    it("should handle empty results array", async () => {
      const ranked = rankSearchResults.execute([], {
        currentModule: undefined,
        now: new Date(),
      });

      expect(ranked).toEqual([]);
    });

    it("should rank results by finalScore in descending order", async () => {
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      const results: SearchResult[] = [
        {
          id: "low-score",
          type: "chunk",
          filePath: "/project/src/a.ts",
          content: "function a() {}",
          score: 0.6,
          lastAccessed: yesterday,
          accessCount: 0,
          metadata: {},
        },
        {
          id: "high-score",
          type: "chunk",
          filePath: "/project/src/b.ts",
          content: "function b() {}",
          score: 0.95,
          lastAccessed: yesterday,
          accessCount: 50,
          metadata: {},
        },
        {
          id: "medium-score",
          type: "chunk",
          filePath: "/project/src/c.ts",
          content: "function c() {}",
          score: 0.8,
          lastAccessed: yesterday,
          accessCount: 25,
          metadata: {},
        },
      ];

      const ranked = rankSearchResults.execute(results, {
        currentModule: undefined,
        now,
      });

      // Should be sorted by final score descending
      expect(ranked[0].id).toBe("high-score");
      expect(ranked[1].id).toBe("medium-score");
      expect(ranked[2].id).toBe("low-score");

      // Verify scores are in descending order
      expect(ranked[0].finalScore).toBeGreaterThan(ranked[1].finalScore!);
      expect(ranked[1].finalScore).toBeGreaterThan(ranked[2].finalScore!);
    });
  });
});
