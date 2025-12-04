/**
 * Redact Sensitive Data Tests
 *
 * Tests for the pure redaction function
 */

import { describe, it, expect } from "vitest";
import {
  redactSensitiveData,
  redactWithCustomPatterns,
} from "../../../src/domain/calculations/redact-sensitive-data";
import {
  RedactionType,
  type RedactionPattern,
} from "../../../src/domain/rules/redaction-rules";

describe("redactSensitiveData", () => {
  describe("Basic redaction", () => {
    it("should redact API keys", () => {
      const text = "My OpenAI key is sk-1234567890abcdef1234567890abcdef";
      const result = redactSensitiveData(text);

      expect(result.hasRedactions).toBe(true);
      expect(result.redactedText).toContain("[REDACTED:API_KEY]");
      expect(result.redactedText).not.toContain("sk-1234567890abcdef");
      expect(result.redactionsApplied.length).toBe(1);
      expect(result.redactionsApplied[0].type).toBe(RedactionType.API_KEY);
      expect(result.redactionsApplied[0].count).toBe(1);
    });

    it("should redact email addresses", () => {
      const text = "Contact me at user@example.com for details";
      const result = redactSensitiveData(text);

      expect(result.hasRedactions).toBe(true);
      expect(result.redactedText).toBe(
        "Contact me at [REDACTED:EMAIL] for details",
      );
      expect(result.redactionsApplied[0].type).toBe(RedactionType.EMAIL);
    });

    it("should redact phone numbers", () => {
      const text = "Call 555-123-4567 for support";
      const result = redactSensitiveData(text);

      expect(result.hasRedactions).toBe(true);
      expect(result.redactedText).toContain("[REDACTED:PHONE]");
      expect(result.redactedText).not.toContain("555-123-4567");
    });

    it("should return original text if no sensitive data found", () => {
      const text = "This is a clean message with no sensitive data";
      const result = redactSensitiveData(text);

      expect(result.hasRedactions).toBe(false);
      expect(result.redactedText).toBe(text);
      expect(result.redactionsApplied.length).toBe(0);
    });
  });

  describe("Multiple redactions", () => {
    it("should redact multiple instances of same type", () => {
      const text = "First email: user1@example.com, second: user2@test.com";
      const result = redactSensitiveData(text);

      expect(result.hasRedactions).toBe(true);
      expect(result.redactionsApplied[0].count).toBe(2);
      expect(result.redactedText).not.toContain("@example.com");
      expect(result.redactedText).not.toContain("@test.com");
    });

    it("should redact multiple different sensitive types", () => {
      const text =
        "Email: user@example.com, Phone: 555-123-4567, IP: 192.168.1.1";
      const result = redactSensitiveData(text);

      expect(result.hasRedactions).toBe(true);
      expect(result.redactionsApplied.length).toBe(3);

      const types = result.redactionsApplied.map((r) => r.type);
      expect(types).toContain(RedactionType.EMAIL);
      expect(types).toContain(RedactionType.PHONE);
      expect(types).toContain(RedactionType.IP_ADDRESS);
    });

    it("should maintain text structure after multiple redactions", () => {
      const text =
        "Config: EMAIL=admin@company.com, PHONE=555-123-4567, IP=10.0.0.1";
      const result = redactSensitiveData(text);

      expect(result.redactedText).toContain("Config:");
      expect(result.redactedText).toContain("[REDACTED:");
      expect(result.redactedText).not.toContain("admin@company.com");
      expect(result.redactedText).not.toContain("555-123-4567");
    });
  });

  describe("Allow-list functionality", () => {
    it("should not redact items in allow-list", () => {
      const text = "Email: user@example.com and admin@test.com";
      const allowList = ["user@example.com"];
      const result = redactSensitiveData(text, allowList);

      expect(result.redactedText).toContain("user@example.com");
      expect(result.redactedText).not.toContain("admin@test.com");
      expect(result.redactionsApplied[0].count).toBe(1);
    });

    it("should be case-insensitive for allow-list matching", () => {
      const text = "API_KEY=TestKey123";
      const allowList = ["testkey123"];
      const result = redactSensitiveData(text, allowList);

      expect(result.redactedText).toContain("TestKey123");
      expect(result.hasRedactions).toBe(false);
    });

    it("should allow partial matches in allow-list", () => {
      const text = "Token: Bearer abc123def456ghi789";
      const allowList = ["abc123"];
      const result = redactSensitiveData(text, allowList);

      expect(result.redactedText).toContain("Bearer abc123def456ghi789");
      expect(result.hasRedactions).toBe(false);
    });
  });

  describe("Edge cases", () => {
    it("should handle empty string", () => {
      const result = redactSensitiveData("");

      expect(result.hasRedactions).toBe(false);
      expect(result.redactedText).toBe("");
      expect(result.redactionsApplied.length).toBe(0);
    });

    it("should handle text with only whitespace", () => {
      const result = redactSensitiveData("   \n\t  ");

      expect(result.hasRedactions).toBe(false);
      expect(result.redactedText).toBe("   \n\t  ");
    });

    it("should preserve newlines and formatting", () => {
      const text =
        "Line 1: user@example.com\nLine 2: 555-123-4567\nLine 3: normal text";
      const result = redactSensitiveData(text);

      expect(result.redactedText).toContain("\n");
      expect(result.redactedText.split("\n").length).toBe(3);
    });

    it("should track positions correctly for multiple redactions", () => {
      const text = "Email1: user@example.com, Email2: admin@test.com";
      const result = redactSensitiveData(text);

      expect(result.hasRedactions).toBe(true);
      expect(result.redactionsApplied[0].positions.length).toBe(2);
      expect(result.redactionsApplied[0].positions[0]).toBeLessThan(
        result.redactionsApplied[0].positions[1],
      );
    });
  });

  describe("Complex scenarios", () => {
    it("should redact private keys", () => {
      const text = `
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
-----END RSA PRIVATE KEY-----
      `;
      const result = redactSensitiveData(text);

      expect(result.hasRedactions).toBe(true);
      expect(result.redactedText).toContain("[REDACTED:PRIVATE_KEY]");
      expect(result.redactedText).not.toContain("BEGIN RSA PRIVATE KEY");
    });

    it("should handle mixed sensitive data in code snippets", () => {
      const text = `
const config = {
  apiKey: "sk-1234567890abcdef",
  email: "admin@company.com",
  serverIp: "203.0.113.42"
};
      `;
      const result = redactSensitiveData(text);

      expect(result.hasRedactions).toBe(true);
      expect(result.redactionsApplied.length).toBeGreaterThanOrEqual(2);
      expect(result.redactedText).toContain("[REDACTED:");
      expect(result.redactedText).not.toContain("sk-1234567890abcdef");
      expect(result.redactedText).not.toContain("admin@company.com");
    });
  });
});

describe("redactWithCustomPatterns", () => {
  it("should apply custom patterns before standard patterns", () => {
    const text = "Custom secret: CUSTOM123";
    const customPattern: RedactionPattern = {
      type: "CUSTOM" as any,
      pattern: /CUSTOM\d+/g,
      replacement: "[REDACTED:CUSTOM]",
      description: "Custom pattern",
    };

    const result = redactWithCustomPatterns(text, [customPattern]);

    expect(result.hasRedactions).toBe(true);
    expect(result.redactedText).toContain("[REDACTED:CUSTOM]");
    expect(result.redactedText).not.toContain("CUSTOM123");
  });

  it("should combine custom and standard pattern redactions", () => {
    const text = "Custom: CUSTOM123, Email: user@example.com";
    const customPattern: RedactionPattern = {
      type: "CUSTOM" as any,
      pattern: /CUSTOM\d+/g,
      replacement: "[REDACTED:CUSTOM]",
      description: "Custom pattern",
    };

    const result = redactWithCustomPatterns(text, [customPattern]);

    expect(result.hasRedactions).toBe(true);
    expect(result.redactionsApplied.length).toBe(2);
    expect(result.redactedText).toContain("[REDACTED:CUSTOM]");
    expect(result.redactedText).toContain("[REDACTED:EMAIL]");
  });

  it("should respect allow-list for custom patterns", () => {
    const text = "Custom: CUSTOM123";
    const customPattern: RedactionPattern = {
      type: "CUSTOM" as any,
      pattern: /CUSTOM\d+/g,
      replacement: "[REDACTED:CUSTOM]",
      description: "Custom pattern",
    };
    const allowList = ["CUSTOM123"];

    const result = redactWithCustomPatterns(text, [customPattern], allowList);

    expect(result.hasRedactions).toBe(false);
    expect(result.redactedText).toContain("CUSTOM123");
  });
});
