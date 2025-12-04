/**
 * ExtractDiscoveries Tests
 *
 * Tests for extracting discoveries from session conversations.
 */

import { describe, it, expect } from "bun:test";
import { ExtractDiscoveries } from "../../../src/application/use-cases/ExtractDiscoveries";

describe("ExtractDiscoveries", () => {
  const extractor = new ExtractDiscoveries();

  describe("execute", () => {
    it("should extract pattern discoveries", () => {
      const messages = [
        "We use JWT tokens for authentication",
        "The system stores tokens in httpOnly cookies",
      ];

      const discoveries = extractor.execute("session-123", messages);

      const patterns = discoveries.filter((d) => d.type === "pattern");
      expect(patterns.length).toBeGreaterThan(0);
      expect(patterns[0]?.content).toContain("JWT");
    });

    it("should extract business rule discoveries", () => {
      const messages = [
        "Sessions must always expire after 7 days",
        "Users must verify email before accessing premium features",
      ];

      const discoveries = extractor.execute("session-123", messages);

      const rules = discoveries.filter((d) => d.type === "rule");
      expect(rules.length).toBeGreaterThan(0);
      expect(rules[0]?.content).toContain("must");
    });

    it("should extract decision discoveries", () => {
      const messages = [
        "We decided to use PostgreSQL instead of MongoDB",
        "Decided to switch from REST to GraphQL for the API",
      ];

      const discoveries = extractor.execute("session-123", messages);

      const decisions = discoveries.filter((d) => d.type === "decision");
      expect(decisions.length).toBeGreaterThan(0);
      expect(decisions[0]?.content).toContain("decided");
    });

    it("should extract issue discoveries", () => {
      const messages = [
        "Fixed the token refresh race condition by adding a mutex lock",
        "Bug with database connection pooling, resolved by increasing max connections",
      ];

      const discoveries = extractor.execute("session-123", messages);

      const issues = discoveries.filter((d) => d.type === "issue");
      expect(issues.length).toBeGreaterThan(0);
      const content = issues[0]?.content.toLowerCase() || "";
      expect(content.includes("fixed") || content.includes("resolved")).toBe(
        true,
      );
    });

    it("should limit discoveries to reasonable number", () => {
      const messages = Array(100).fill("We use pattern X for feature Y");

      const discoveries = extractor.execute("session-123", messages);

      expect(discoveries.length).toBeLessThanOrEqual(10);
    });

    it("should deduplicate similar discoveries", () => {
      const messages = [
        "We use JWT tokens for authentication",
        "We use JWT tokens for auth",
        "JWT tokens are used for authentication",
      ];

      const discoveries = extractor.execute("session-123", messages);

      expect(discoveries.length).toBe(1);
    });

    it("should include session metadata", () => {
      const messages = ["We use Redis for caching"];

      const discoveries = extractor.execute("session-456", messages);

      expect(discoveries[0]?.sessionId).toBe("session-456");
      expect(discoveries[0]?.createdAt).toBeInstanceOf(Date);
    });

    it("should return empty array for no discoveries", () => {
      const messages = ["Hello", "How are you?", "Thanks"];

      const discoveries = extractor.execute("session-123", messages);

      expect(discoveries).toEqual([]);
    });

    it("should handle empty messages array", () => {
      const discoveries = extractor.execute("session-123", []);

      expect(discoveries).toEqual([]);
    });
  });

  describe("pattern matching", () => {
    it('should match "we use X for Y" pattern', () => {
      const messages = ["We use React for the frontend"];

      const discoveries = extractor.execute("session-123", messages);

      expect(discoveries.length).toBeGreaterThan(0);
      expect(discoveries[0]?.type).toBe("pattern");
    });

    it('should match "X stores Y in Z" pattern', () => {
      const messages = ["The system stores user sessions in Redis"];

      const discoveries = extractor.execute("session-123", messages);

      expect(discoveries.length).toBeGreaterThan(0);
      expect(discoveries[0]?.type).toBe("pattern");
    });

    it('should match "must always/never" rules', () => {
      const messages = ["API keys must never be committed to git"];

      const discoveries = extractor.execute("session-123", messages);

      const rules = discoveries.filter((d) => d.type === "rule");
      expect(rules.length).toBeGreaterThan(0);
    });

    it('should match "decided to" decisions', () => {
      const messages = ["We decided to migrate to TypeScript"];

      const discoveries = extractor.execute("session-123", messages);

      const decisions = discoveries.filter((d) => d.type === "decision");
      expect(decisions.length).toBeGreaterThan(0);
    });

    it('should match "fixed/resolved" issues', () => {
      const messages = ["Fixed the memory leak in the websocket handler"];

      const discoveries = extractor.execute("session-123", messages);

      const issues = discoveries.filter((d) => d.type === "issue");
      expect(issues.length).toBeGreaterThan(0);
    });
  });

  describe("module detection", () => {
    it("should detect module from file paths", () => {
      const messages = [
        "Updated src/auth/AuthService.ts - we use JWT tokens for authentication",
      ];

      const discoveries = extractor.execute("session-123", messages);

      expect(discoveries.length).toBeGreaterThan(0);
      expect(discoveries[0]?.module).toBe("auth");
    });

    it("should detect module from explicit mentions", () => {
      const messages = [
        "In the authentication module, we use bcrypt for hashing",
      ];

      const discoveries = extractor.execute("session-123", messages);

      expect(discoveries[0]?.module).toBe("authentication");
    });

    it("should handle no module detection", () => {
      const messages = ["We use Redis for caching"];

      const discoveries = extractor.execute("session-123", messages);

      expect(discoveries[0]?.module).toBeUndefined();
    });
  });
});
