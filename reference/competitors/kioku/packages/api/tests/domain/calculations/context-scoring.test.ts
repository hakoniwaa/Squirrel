import { describe, it, expect } from "vitest";
import {
  calculateContextScore,
  calculateRecencyFactor,
  normalizeAccessCount,
} from "../../../src/domain/calculations/context-scoring";

describe("calculateContextScore", () => {
  describe("when item was accessed recently", () => {
    it("should return high score for today", () => {
      const now = new Date("2025-10-09T12:00:00Z");
      const lastAccessed = new Date("2025-10-09T10:00:00Z");
      const score = calculateContextScore(lastAccessed, 10, now);

      // Score = 0.6 * ~1.0 (recency) + 0.4 * 0.1 (10/100 access) = ~0.64
      expect(score).toBeGreaterThan(0.6);
    });

    it("should return high score for yesterday", () => {
      const now = new Date("2025-10-09T12:00:00Z");
      const lastAccessed = new Date("2025-10-08T12:00:00Z");
      const score = calculateContextScore(lastAccessed, 10, now);

      // Score = 0.6 * ~0.967 (1 day ago) + 0.4 * 0.1 = ~0.62
      expect(score).toBeGreaterThan(0.6);
    });
  });

  describe("when item was not accessed recently", () => {
    it("should return low score for 30 days ago", () => {
      const now = new Date("2025-10-09T12:00:00Z");
      const lastAccessed = new Date("2025-09-09T12:00:00Z");
      const score = calculateContextScore(lastAccessed, 0, now);

      expect(score).toBeLessThan(0.3);
    });

    it("should return zero score for 60 days ago", () => {
      const now = new Date("2025-10-09T12:00:00Z");
      const lastAccessed = new Date("2025-08-10T12:00:00Z");
      const score = calculateContextScore(lastAccessed, 0, now);

      expect(score).toBe(0);
    });
  });

  describe("scoring weights", () => {
    it("should weigh recency at 60%", () => {
      const now = new Date("2025-10-09T12:00:00Z");
      const lastAccessed = new Date("2025-10-09T12:00:00Z");

      // Max recency (1.0), zero access
      const score = calculateContextScore(lastAccessed, 0, now);

      // Should be 0.6 * 1.0 + 0.4 * 0.0 = 0.6
      expect(score).toBeCloseTo(0.6, 2);
    });

    it("should weigh access count at 40%", () => {
      const now = new Date("2025-10-09T12:00:00Z");
      const lastAccessed = new Date("2025-08-10T12:00:00Z"); // 60 days ago = 0 recency

      // Zero recency, max access (100)
      const score = calculateContextScore(lastAccessed, 100, now);

      // Should be 0.6 * 0.0 + 0.4 * 1.0 = 0.4
      expect(score).toBeCloseTo(0.4, 2);
    });

    it("should combine both factors", () => {
      const now = new Date("2025-10-09T12:00:00Z");
      const lastAccessed = new Date("2025-10-09T12:00:00Z");

      // Max recency (1.0), max access (100)
      const score = calculateContextScore(lastAccessed, 100, now);

      // Should be 0.6 * 1.0 + 0.4 * 1.0 = 1.0
      expect(score).toBeCloseTo(1.0, 2);
    });
  });

  describe("edge cases", () => {
    it("should cap score at 1.0", () => {
      const now = new Date("2025-10-09T12:00:00Z");
      const lastAccessed = new Date("2025-10-09T12:00:00Z");

      const score = calculateContextScore(lastAccessed, 200, now);

      expect(score).toBeLessThanOrEqual(1.0);
    });

    it("should floor score at 0.0", () => {
      const now = new Date("2025-10-09T12:00:00Z");
      const lastAccessed = new Date("2020-01-01T12:00:00Z"); // Very old

      const score = calculateContextScore(lastAccessed, 0, now);

      expect(score).toBeGreaterThanOrEqual(0.0);
      expect(score).toBe(0);
    });
  });
});

describe("calculateRecencyFactor", () => {
  it("should return 1.0 for same day", () => {
    const now = new Date("2025-10-09T12:00:00Z");
    const lastAccessed = new Date("2025-10-09T10:00:00Z");

    const factor = calculateRecencyFactor(lastAccessed, now);

    expect(factor).toBeCloseTo(1.0, 2);
  });

  it("should return ~0.5 for 15 days ago", () => {
    const now = new Date("2025-10-09T12:00:00Z");
    const lastAccessed = new Date("2025-09-24T12:00:00Z");

    const factor = calculateRecencyFactor(lastAccessed, now);

    expect(factor).toBeCloseTo(0.5, 1);
  });

  it("should return 0.0 for 30+ days ago", () => {
    const now = new Date("2025-10-09T12:00:00Z");
    const lastAccessed = new Date("2025-09-09T12:00:00Z");

    const factor = calculateRecencyFactor(lastAccessed, now);

    expect(factor).toBeCloseTo(0.0, 2);
  });

  it("should never return negative values", () => {
    const now = new Date("2025-10-09T12:00:00Z");
    const lastAccessed = new Date("2020-01-01T12:00:00Z");

    const factor = calculateRecencyFactor(lastAccessed, now);

    expect(factor).toBeGreaterThanOrEqual(0);
  });
});

describe("normalizeAccessCount", () => {
  it("should return 0.0 for zero access", () => {
    const normalized = normalizeAccessCount(0);

    expect(normalized).toBe(0.0);
  });

  it("should return 0.5 for 50 accesses (default max 100)", () => {
    const normalized = normalizeAccessCount(50);

    expect(normalized).toBe(0.5);
  });

  it("should return 1.0 for 100 accesses (default max)", () => {
    const normalized = normalizeAccessCount(100);

    expect(normalized).toBe(1.0);
  });

  it("should cap at 1.0 for counts > max", () => {
    const normalized = normalizeAccessCount(200);

    expect(normalized).toBe(1.0);
  });

  it("should support custom max count", () => {
    const normalized = normalizeAccessCount(50, 50);

    expect(normalized).toBe(1.0);
  });
});
