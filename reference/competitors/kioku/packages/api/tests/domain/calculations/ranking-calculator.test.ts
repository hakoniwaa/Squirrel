import { describe, it, expect } from "vitest";
import {
  calculateRecencyBoost,
  calculateModuleBoost,
  calculateFrequencyBoost,
  calculateFinalScore,
} from "../../../src/domain/calculations/ranking-calculator";

describe("Ranking Calculator", () => {
  const now = new Date("2025-10-10T12:00:00Z");

  describe("calculateRecencyBoost", () => {
    it("should return 1.5x boost for files accessed <24 hours ago", () => {
      // 12 hours ago
      const lastAccessed = new Date("2025-10-10T00:00:00Z");
      const boost = calculateRecencyBoost(lastAccessed, now);

      expect(boost).toBe(1.5);
    });

    it("should return 1.5x boost for files accessed exactly 24 hours ago", () => {
      // Exactly 24 hours ago
      const lastAccessed = new Date("2025-10-09T12:00:00Z");
      const boost = calculateRecencyBoost(lastAccessed, now);

      expect(boost).toBe(1.5);
    });

    it("should return 1.2x boost for files accessed <7 days ago", () => {
      // 3 days ago
      const lastAccessed = new Date("2025-10-07T12:00:00Z");
      const boost = calculateRecencyBoost(lastAccessed, now);

      expect(boost).toBe(1.2);
    });

    it("should return 1.2x boost for files accessed exactly 7 days ago", () => {
      // Exactly 7 days ago
      const lastAccessed = new Date("2025-10-03T12:00:00Z");
      const boost = calculateRecencyBoost(lastAccessed, now);

      expect(boost).toBe(1.2);
    });

    it("should return 1.0x boost for files accessed >7 days ago", () => {
      // 14 days ago
      const lastAccessed = new Date("2025-09-26T12:00:00Z");
      const boost = calculateRecencyBoost(lastAccessed, now);

      expect(boost).toBe(1.0);
    });

    it("should return 1.0x boost for files accessed 30 days ago", () => {
      // 30 days ago
      const lastAccessed = new Date("2025-09-10T12:00:00Z");
      const boost = calculateRecencyBoost(lastAccessed, now);

      expect(boost).toBe(1.0);
    });

    it("should handle very recent access (1 minute ago)", () => {
      // 1 minute ago
      const lastAccessed = new Date("2025-10-10T11:59:00Z");
      const boost = calculateRecencyBoost(lastAccessed, now);

      expect(boost).toBe(1.5);
    });

    it("should handle edge case of future date gracefully", () => {
      // 1 day in the future (shouldn't happen, but test robustness)
      const lastAccessed = new Date("2025-10-11T12:00:00Z");
      const boost = calculateRecencyBoost(lastAccessed, now);

      // Should treat as very recent
      expect(boost).toBe(1.5);
    });
  });

  describe("calculateModuleBoost", () => {
    it("should return 1.3x boost when result is from current module", () => {
      const currentModule = "auth";
      const resultModule = "auth";

      const boost = calculateModuleBoost(currentModule, resultModule);

      expect(boost).toBe(1.3);
    });

    it("should return 1.0x boost when result is from different module", () => {
      const currentModule = "auth";
      const resultModule = "payment";

      const boost = calculateModuleBoost(currentModule, resultModule);

      expect(boost).toBe(1.0);
    });

    it("should handle undefined current module", () => {
      const currentModule = undefined;
      const resultModule = "auth";

      const boost = calculateModuleBoost(currentModule, resultModule);

      expect(boost).toBe(1.0);
    });

    it("should handle undefined result module", () => {
      const currentModule = "auth";
      const resultModule = undefined;

      const boost = calculateModuleBoost(currentModule, resultModule);

      expect(boost).toBe(1.0);
    });

    it("should handle both modules undefined", () => {
      const currentModule = undefined;
      const resultModule = undefined;

      const boost = calculateModuleBoost(currentModule, resultModule);

      expect(boost).toBe(1.0);
    });

    it("should be case-sensitive for module names", () => {
      const currentModule = "Auth";
      const resultModule = "auth";

      const boost = calculateModuleBoost(currentModule, resultModule);

      expect(boost).toBe(1.0); // Different case = different modules
    });

    it("should handle empty string modules", () => {
      const currentModule = "";
      const resultModule = "";

      const boost = calculateModuleBoost(currentModule, resultModule);

      // Empty strings match, but arguably not a meaningful module
      // Could be 1.3x or 1.0x depending on business logic
      expect(boost).toBe(1.0); // Treat empty as "no module"
    });
  });

  describe("calculateFrequencyBoost", () => {
    it("should return 1.0x for files never accessed", () => {
      const accessCount = 0;
      const boost = calculateFrequencyBoost(accessCount);

      expect(boost).toBe(1.0);
    });

    it("should return 1.01x for files accessed once", () => {
      const accessCount = 1;
      const boost = calculateFrequencyBoost(accessCount);

      expect(boost).toBe(1.01);
    });

    it("should return 1.1x for files accessed 10 times", () => {
      const accessCount = 10;
      const boost = calculateFrequencyBoost(accessCount);

      expect(boost).toBe(1.1);
    });

    it("should return 1.5x for files accessed 50 times", () => {
      const accessCount = 50;
      const boost = calculateFrequencyBoost(accessCount);

      expect(boost).toBe(1.5);
    });

    it("should cap at 1.5x for files accessed 100 times", () => {
      const accessCount = 100;
      const boost = calculateFrequencyBoost(accessCount);

      expect(boost).toBe(1.5);
    });

    it("should cap at 1.5x for files accessed 500 times", () => {
      const accessCount = 500;
      const boost = calculateFrequencyBoost(accessCount);

      expect(boost).toBe(1.5);
    });

    it("should handle negative access count gracefully", () => {
      const accessCount = -5;
      const boost = calculateFrequencyBoost(accessCount);

      // Should treat as 0
      expect(boost).toBe(1.0);
    });

    it("should return correct boost for 25 accesses", () => {
      const accessCount = 25;
      const boost = calculateFrequencyBoost(accessCount);

      expect(boost).toBe(1.25);
    });
  });

  describe("calculateFinalScore", () => {
    it("should multiply semantic score by all boosts", () => {
      const semanticScore = 0.8;
      const recencyBoost = 1.5;
      const moduleBoost = 1.3;
      const frequencyBoost = 1.2;

      const finalScore = calculateFinalScore(
        semanticScore,
        recencyBoost,
        moduleBoost,
        frequencyBoost,
      );

      // 0.8 * 1.5 * 1.3 * 1.2 = 1.872
      expect(finalScore).toBeCloseTo(1.872, 3);
    });

    it("should handle all boosts at 1.0x (no boost)", () => {
      const semanticScore = 0.7;
      const recencyBoost = 1.0;
      const moduleBoost = 1.0;
      const frequencyBoost = 1.0;

      const finalScore = calculateFinalScore(
        semanticScore,
        recencyBoost,
        moduleBoost,
        frequencyBoost,
      );

      expect(finalScore).toBe(0.7);
    });

    it("should handle maximum boosts scenario", () => {
      const semanticScore = 1.0;
      const recencyBoost = 1.5; // <24h
      const moduleBoost = 1.3; // same module
      const frequencyBoost = 1.5; // 100+ accesses

      const finalScore = calculateFinalScore(
        semanticScore,
        recencyBoost,
        moduleBoost,
        frequencyBoost,
      );

      // 1.0 * 1.5 * 1.3 * 1.5 = 2.925
      expect(finalScore).toBeCloseTo(2.925, 3);
    });

    it("should handle low semantic score with high boosts", () => {
      const semanticScore = 0.3;
      const recencyBoost = 1.5;
      const moduleBoost = 1.3;
      const frequencyBoost = 1.5;

      const finalScore = calculateFinalScore(
        semanticScore,
        recencyBoost,
        moduleBoost,
        frequencyBoost,
      );

      // 0.3 * 1.5 * 1.3 * 1.5 = 0.8775
      expect(finalScore).toBeCloseTo(0.8775, 3);
    });

    it("should handle zero semantic score", () => {
      const semanticScore = 0.0;
      const recencyBoost = 1.5;
      const moduleBoost = 1.3;
      const frequencyBoost = 1.5;

      const finalScore = calculateFinalScore(
        semanticScore,
        recencyBoost,
        moduleBoost,
        frequencyBoost,
      );

      expect(finalScore).toBe(0.0);
    });

    it("should produce higher score for recent + same module + frequent file", () => {
      const baseScore = 0.6;

      // Scenario 1: Old, different module, rarely accessed
      const score1 = calculateFinalScore(baseScore, 1.0, 1.0, 1.0);

      // Scenario 2: Recent, same module, frequently accessed
      const score2 = calculateFinalScore(baseScore, 1.5, 1.3, 1.5);

      expect(score2).toBeGreaterThan(score1);
      expect(score2 / score1).toBeCloseTo(2.925, 2); // ~3x boost
    });

    it("should handle fractional boosts correctly", () => {
      const semanticScore = 0.75;
      const recencyBoost = 1.2;
      const moduleBoost = 1.0;
      const frequencyBoost = 1.25;

      const finalScore = calculateFinalScore(
        semanticScore,
        recencyBoost,
        moduleBoost,
        frequencyBoost,
      );

      // 0.75 * 1.2 * 1.0 * 1.25 = 1.125
      expect(finalScore).toBeCloseTo(1.125, 3);
    });
  });

  describe("Edge Cases and Integration", () => {
    it("should rank recent file higher than old file with same semantic score", () => {
      const semanticScore = 0.8;

      // Recent file: <24h, no other boosts
      const recentBoost = calculateRecencyBoost(
        new Date("2025-10-10T00:00:00Z"),
        now,
      );
      const recentScore = calculateFinalScore(
        semanticScore,
        recentBoost,
        1.0,
        1.0,
      );

      // Old file: >7 days, no other boosts
      const oldBoost = calculateRecencyBoost(
        new Date("2025-09-01T00:00:00Z"),
        now,
      );
      const oldScore = calculateFinalScore(semanticScore, oldBoost, 1.0, 1.0);

      expect(recentScore).toBeGreaterThan(oldScore);
      expect(recentScore).toBe(0.8 * 1.5); // 1.2
      expect(oldScore).toBe(0.8 * 1.0); // 0.8
    });

    it("should rank same-module file higher than different-module file", () => {
      const semanticScore = 0.7;

      // Same module
      const sameModuleBoost = calculateModuleBoost("auth", "auth");
      const sameModuleScore = calculateFinalScore(
        semanticScore,
        1.0,
        sameModuleBoost,
        1.0,
      );

      // Different module
      const diffModuleBoost = calculateModuleBoost("auth", "payment");
      const diffModuleScore = calculateFinalScore(
        semanticScore,
        1.0,
        diffModuleBoost,
        1.0,
      );

      expect(sameModuleScore).toBeGreaterThan(diffModuleScore);
      expect(sameModuleScore).toBe(0.7 * 1.3); // 0.91
      expect(diffModuleScore).toBe(0.7 * 1.0); // 0.7
    });

    it("should rank frequently accessed file higher than rarely accessed file", () => {
      const semanticScore = 0.6;

      // Frequently accessed
      const frequentBoost = calculateFrequencyBoost(50);
      const frequentScore = calculateFinalScore(
        semanticScore,
        1.0,
        1.0,
        frequentBoost,
      );

      // Rarely accessed
      const rareBoost = calculateFrequencyBoost(2);
      const rareScore = calculateFinalScore(semanticScore, 1.0, 1.0, rareBoost);

      expect(frequentScore).toBeGreaterThan(rareScore);
      expect(frequentScore).toBe(0.6 * 1.5); // 0.9
      expect(rareScore).toBe(0.6 * 1.02); // 0.612
    });

    it("should combine all boosts multiplicatively for best-case scenario", () => {
      const semanticScore = 0.85;

      // Best case: recent + same module + frequent
      const recencyBoost = calculateRecencyBoost(
        new Date("2025-10-10T06:00:00Z"),
        now,
      ); // 6h ago = 1.5x
      const moduleBoost = calculateModuleBoost("auth", "auth"); // 1.3x
      const frequencyBoost = calculateFrequencyBoost(100); // 1.5x

      const bestScore = calculateFinalScore(
        semanticScore,
        recencyBoost,
        moduleBoost,
        frequencyBoost,
      );

      // 0.85 * 1.5 * 1.3 * 1.5 = 2.48625
      expect(bestScore).toBeCloseTo(2.48625, 3);

      // Worst case: old + different module + never accessed
      const worstScore = calculateFinalScore(
        semanticScore,
        1.0,
        1.0,
        1.0,
      );

      expect(worstScore).toBe(0.85);
      expect(bestScore / worstScore).toBeCloseTo(2.925, 2); // ~3x improvement
    });
  });
});
