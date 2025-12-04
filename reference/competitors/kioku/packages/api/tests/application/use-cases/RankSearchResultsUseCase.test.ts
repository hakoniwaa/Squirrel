import { describe, it, expect, beforeEach } from "vitest";
import { RankSearchResultsUseCase } from "../../../src/application/use-cases/RankSearchResultsUseCase";
import type { SearchResult } from "../../../src/domain/models/SearchResult";

describe("RankSearchResultsUseCase", () => {
  let useCase: RankSearchResultsUseCase;

  beforeEach(() => {
    useCase = new RankSearchResultsUseCase();
  });

  describe("execute", () => {
    const now = new Date("2025-10-10T12:00:00Z");

    it("should apply recency boost to search results", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "chunk-1",
          type: "chunk",
          filePath: "src/auth/login.ts",
          content: "function login() { }",
          score: 0.8,
          module: "auth",
          lastAccessed: new Date("2025-10-10T06:00:00Z"), // 6 hours ago
          accessCount: 0,
          metadata: {},
        },
        {
          id: "chunk-2",
          type: "chunk",
          filePath: "src/auth/logout.ts",
          content: "function logout() { }",
          score: 0.8,
          module: "auth",
          lastAccessed: new Date("2025-09-01T12:00:00Z"), // 39 days ago
          accessCount: 0,
          metadata: {},
        },
      ];

      // Act
      const ranked = useCase.execute(results, { currentModule: undefined, now });

      // Assert
      expect(ranked[0].id).toBe("chunk-1"); // Recent file ranks first
      expect(ranked[1].id).toBe("chunk-2");
      expect(ranked[0].finalScore).toBeGreaterThan(ranked[1].finalScore);
      expect(ranked[0].recencyBoost).toBe(1.5);
      expect(ranked[1].recencyBoost).toBe(1.0);
    });

    it("should apply module boost to search results", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "chunk-1",
          type: "chunk",
          filePath: "src/payment/charge.ts",
          content: "function charge() { }",
          score: 0.7,
          module: "payment",
          lastAccessed: new Date("2025-10-01T12:00:00Z"),
          accessCount: 0,
          metadata: {},
        },
        {
          id: "chunk-2",
          type: "chunk",
          filePath: "src/auth/verify.ts",
          content: "function verify() { }",
          score: 0.7,
          module: "auth",
          lastAccessed: new Date("2025-10-01T12:00:00Z"),
          accessCount: 0,
          metadata: {},
        },
      ];

      // Act - Current module is "auth"
      const ranked = useCase.execute(results, {
        currentModule: "auth",
        now,
      });

      // Assert
      expect(ranked[0].id).toBe("chunk-2"); // Same module ranks first
      expect(ranked[1].id).toBe("chunk-1");
      expect(ranked[0].finalScore).toBeGreaterThan(ranked[1].finalScore);
      expect(ranked[0].moduleBoost).toBe(1.3);
      expect(ranked[1].moduleBoost).toBe(1.0);
    });

    it("should apply frequency boost to search results", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "chunk-1",
          type: "chunk",
          filePath: "src/common/utils.ts",
          content: "export function formatDate() { }",
          score: 0.6,
          module: "common",
          lastAccessed: new Date("2025-10-01T12:00:00Z"),
          accessCount: 50, // Frequently accessed
          metadata: {},
        },
        {
          id: "chunk-2",
          type: "chunk",
          filePath: "src/rare/helper.ts",
          content: "export function rareHelper() { }",
          score: 0.6,
          module: "rare",
          lastAccessed: new Date("2025-10-01T12:00:00Z"),
          accessCount: 1, // Rarely accessed
          metadata: {},
        },
      ];

      // Act
      const ranked = useCase.execute(results, { currentModule: undefined, now });

      // Assert
      expect(ranked[0].id).toBe("chunk-1"); // Frequent file ranks first
      expect(ranked[1].id).toBe("chunk-2");
      expect(ranked[0].finalScore).toBeGreaterThan(ranked[1].finalScore);
      expect(ranked[0].frequencyBoost).toBe(1.5);
      expect(ranked[1].frequencyBoost).toBe(1.01);
    });

    it("should combine all boosts multiplicatively", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "best",
          type: "chunk",
          filePath: "src/auth/login.ts",
          content: "function login() { }",
          score: 0.8,
          module: "auth",
          lastAccessed: new Date("2025-10-10T06:00:00Z"), // 6h ago = 1.5x
          accessCount: 100, // 1.5x
          metadata: {},
        },
        {
          id: "worst",
          type: "chunk",
          filePath: "src/payment/old.ts",
          content: "function old() { }",
          score: 0.8,
          module: "payment",
          lastAccessed: new Date("2025-09-01T12:00:00Z"), // 39d ago = 1.0x
          accessCount: 0, // 1.0x
          metadata: {},
        },
      ];

      // Act - Current module is "auth"
      const ranked = useCase.execute(results, {
        currentModule: "auth",
        now,
      });

      // Assert
      expect(ranked[0].id).toBe("best");
      expect(ranked[1].id).toBe("worst");

      // Best: 0.8 * 1.5 (recency) * 1.3 (module) * 1.5 (frequency) = 2.34
      expect(ranked[0].finalScore).toBeCloseTo(2.34, 2);

      // Worst: 0.8 * 1.0 * 1.0 * 1.0 = 0.8
      expect(ranked[1].finalScore).toBe(0.8);

      // ~2.9x improvement
      expect(ranked[0].finalScore / ranked[1].finalScore).toBeCloseTo(2.925, 2);
    });

    it("should preserve original order when all scores are equal", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "chunk-1",
          type: "chunk",
          filePath: "src/a.ts",
          content: "a",
          score: 0.5,
          module: "test",
          lastAccessed: new Date("2025-10-01T12:00:00Z"),
          accessCount: 5,
          metadata: {},
        },
        {
          id: "chunk-2",
          type: "chunk",
          filePath: "src/b.ts",
          content: "b",
          score: 0.5,
          module: "test",
          lastAccessed: new Date("2025-10-01T12:00:00Z"),
          accessCount: 5,
          metadata: {},
        },
        {
          id: "chunk-3",
          type: "chunk",
          filePath: "src/c.ts",
          content: "c",
          score: 0.5,
          module: "test",
          lastAccessed: new Date("2025-10-01T12:00:00Z"),
          accessCount: 5,
          metadata: {},
        },
      ];

      // Act
      const ranked = useCase.execute(results, { currentModule: undefined, now });

      // Assert - Order preserved when final scores are equal
      expect(ranked[0].id).toBe("chunk-1");
      expect(ranked[1].id).toBe("chunk-2");
      expect(ranked[2].id).toBe("chunk-3");
      expect(ranked[0].finalScore).toBe(ranked[1].finalScore);
      expect(ranked[1].finalScore).toBe(ranked[2].finalScore);
    });

    it("should handle empty results array", () => {
      // Arrange
      const results: SearchResult[] = [];

      // Act
      const ranked = useCase.execute(results, { currentModule: undefined, now });

      // Assert
      expect(ranked).toEqual([]);
    });

    it("should handle single result", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "only",
          type: "chunk",
          filePath: "src/only.ts",
          content: "only",
          score: 0.9,
          module: "test",
          lastAccessed: new Date("2025-10-10T00:00:00Z"),
          accessCount: 10,
          metadata: {},
        },
      ];

      // Act
      const ranked = useCase.execute(results, { currentModule: "test", now });

      // Assert
      expect(ranked).toHaveLength(1);
      expect(ranked[0].id).toBe("only");
      expect(ranked[0].recencyBoost).toBe(1.5);
      expect(ranked[0].moduleBoost).toBe(1.3);
      expect(ranked[0].frequencyBoost).toBe(1.1);
      expect(ranked[0].finalScore).toBeCloseTo(0.9 * 1.5 * 1.3 * 1.1, 2);
    });

    it("should add ranking metadata to results", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "chunk-1",
          type: "chunk",
          filePath: "src/test.ts",
          content: "test",
          score: 0.75,
          module: "auth",
          lastAccessed: new Date("2025-10-10T00:00:00Z"),
          accessCount: 25,
          metadata: {},
        },
      ];

      // Act
      const ranked = useCase.execute(results, {
        currentModule: "auth",
        now,
      });

      // Assert
      expect(ranked[0]).toHaveProperty("recencyBoost");
      expect(ranked[0]).toHaveProperty("moduleBoost");
      expect(ranked[0]).toHaveProperty("frequencyBoost");
      expect(ranked[0]).toHaveProperty("finalScore");
      expect(ranked[0].recencyBoost).toBe(1.5);
      expect(ranked[0].moduleBoost).toBe(1.3);
      expect(ranked[0].frequencyBoost).toBe(1.25);
    });

    it("should handle results without lastAccessed timestamp", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "chunk-1",
          type: "chunk",
          filePath: "src/test.ts",
          content: "test",
          score: 0.7,
          module: "test",
          lastAccessed: new Date(0), // Epoch time (very old)
          accessCount: 0,
          metadata: {},
        },
      ];

      // Act
      const ranked = useCase.execute(results, { currentModule: undefined, now });

      // Assert
      expect(ranked[0].recencyBoost).toBe(1.0); // Old file = no boost
      expect(ranked[0].finalScore).toBe(0.7);
    });

    it("should handle results without module", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "chunk-1",
          type: "chunk",
          filePath: "src/test.ts",
          content: "test",
          score: 0.6,
          module: undefined,
          lastAccessed: new Date("2025-10-01T12:00:00Z"),
          accessCount: 0,
          metadata: {},
        },
      ];

      // Act
      const ranked = useCase.execute(results, {
        currentModule: "auth",
        now,
      });

      // Assert
      expect(ranked[0].moduleBoost).toBe(1.0); // No module = no boost
    });

    it("should sort results by finalScore in descending order", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "low",
          type: "chunk",
          filePath: "src/low.ts",
          content: "low",
          score: 0.3,
          module: "test",
          lastAccessed: new Date("2025-09-01T12:00:00Z"),
          accessCount: 0,
          metadata: {},
        },
        {
          id: "high",
          type: "chunk",
          filePath: "src/high.ts",
          content: "high",
          score: 0.9,
          module: "test",
          lastAccessed: new Date("2025-10-10T00:00:00Z"),
          accessCount: 50,
          metadata: {},
        },
        {
          id: "medium",
          type: "chunk",
          filePath: "src/medium.ts",
          content: "medium",
          score: 0.6,
          module: "test",
          lastAccessed: new Date("2025-10-05T12:00:00Z"),
          accessCount: 10,
          metadata: {},
        },
      ];

      // Act
      const ranked = useCase.execute(results, { currentModule: undefined, now });

      // Assert
      expect(ranked[0].id).toBe("high");
      expect(ranked[1].id).toBe("medium");
      expect(ranked[2].id).toBe("low");
      expect(ranked[0].finalScore).toBeGreaterThan(ranked[1].finalScore);
      expect(ranked[1].finalScore).toBeGreaterThan(ranked[2].finalScore);
    });

    it("should use current time by default if not provided", () => {
      // Arrange
      const results: SearchResult[] = [
        {
          id: "chunk-1",
          type: "chunk",
          filePath: "src/test.ts",
          content: "test",
          score: 0.8,
          module: "test",
          lastAccessed: new Date(Date.now() - 1000 * 60 * 60), // 1 hour ago
          accessCount: 5,
          metadata: {},
        },
      ];

      // Act - No 'now' provided
      const ranked = useCase.execute(results, { currentModule: undefined });

      // Assert
      expect(ranked[0].recencyBoost).toBe(1.5); // Should use current time
    });
  });
});
