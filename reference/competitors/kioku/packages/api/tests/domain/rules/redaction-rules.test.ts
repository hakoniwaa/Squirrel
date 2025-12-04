/**
 * Redaction Rules Unit Tests
 *
 * Tests for sensitive data detection patterns used to redact
 * information before sending to AI APIs
 */

import { describe, it, expect } from "vitest";
import {
  REDACTION_PATTERNS,
  RedactionType,
  type RedactionPattern as _RedactionPattern,
} from "../../../src/domain/rules/redaction-rules";

describe("Redaction Rules", () => {
  describe("API Keys", () => {
    it("should detect OpenAI API keys", () => {
      const text = "My key is sk-1234567890abcdef1234567890abcdef";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.API_KEY,
      );

      expect(pattern).toBeDefined();
      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("sk-1234567890abcdef1234567890abcdef");
    });

    it("should detect Anthropic API keys", () => {
      const text = "ANTHROPIC_API_KEY=sk-ant-api03-abcdef123456";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.API_KEY,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toContain("sk-ant-");
    });

    it("should detect generic API keys with KEY= pattern", () => {
      const text = "API_KEY=1234567890abcdef";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.API_KEY,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
    });

    it("should detect AWS access keys", () => {
      const text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.API_KEY,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toContain("AKIA");
    });
  });

  describe("OAuth Tokens", () => {
    it("should detect Bearer tokens", () => {
      const text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.OAUTH_TOKEN,
      );

      expect(pattern).toBeDefined();
      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toContain("Bearer");
    });

    it("should detect GitHub tokens", () => {
      const text = "GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.OAUTH_TOKEN,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toContain("ghp_");
    });

    it("should detect access_token in URLs", () => {
      const text = "https://api.example.com?access_token=abc123def456";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.OAUTH_TOKEN,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
    });
  });

  describe("Email Addresses", () => {
    it("should detect standard email addresses", () => {
      const text = "Contact me at user@example.com for details";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.EMAIL,
      );

      expect(pattern).toBeDefined();
      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("user@example.com");
    });

    it("should detect emails with subdomains", () => {
      const text = "Email: admin@mail.company.co.uk";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.EMAIL,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("admin@mail.company.co.uk");
    });

    it("should detect emails with plus addressing", () => {
      const text = "user+tag@example.com";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.EMAIL,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("user+tag@example.com");
    });
  });

  describe("Phone Numbers", () => {
    it("should detect US phone numbers with dashes", () => {
      const text = "Call 123-456-7890 for support";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.PHONE,
      );

      expect(pattern).toBeDefined();
      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("123-456-7890");
    });

    it("should detect phone numbers with parentheses", () => {
      const text = "Contact: (555) 123-4567";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.PHONE,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toContain("555");
    });

    it("should detect international format", () => {
      const text = "Phone: +1-555-123-4567";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.PHONE,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
    });
  });

  describe("IP Addresses", () => {
    it("should detect IPv4 addresses", () => {
      const text = "Server IP: 192.168.1.100";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.IP_ADDRESS,
      );

      expect(pattern).toBeDefined();
      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("192.168.1.100");
    });

    it("should detect public IPs", () => {
      const text = "External IP is 203.0.113.42";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.IP_ADDRESS,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("203.0.113.42");
    });

    it("should detect localhost", () => {
      const text = "Connect to 127.0.0.1:3000";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.IP_ADDRESS,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("127.0.0.1");
    });
  });

  describe("Credit Card Numbers", () => {
    it("should detect Visa card numbers", () => {
      const text = "Card: 4532-1234-5678-9010";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.CREDIT_CARD,
      );

      expect(pattern).toBeDefined();
      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toContain("4532");
    });

    it("should detect Mastercard numbers", () => {
      const text = "MC: 5425233430109903";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.CREDIT_CARD,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("5425233430109903");
    });

    it("should detect Amex numbers", () => {
      const text = "AMEX 378282246310005";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.CREDIT_CARD,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
    });
  });

  describe("Social Security Numbers", () => {
    it("should detect SSN with dashes", () => {
      const text = "SSN: 123-45-6789";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.SSN,
      );

      expect(pattern).toBeDefined();
      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("123-45-6789");
    });

    it("should detect SSN without dashes", () => {
      const text = "Social Security: 123456789";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.SSN,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("123456789");
    });
  });

  describe("Private Keys", () => {
    it("should detect SSH private key headers", () => {
      const text =
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.PRIVATE_KEY,
      );

      expect(pattern).toBeDefined();
      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toContain("BEGIN RSA PRIVATE KEY");
    });

    it("should detect OpenSSH private keys", () => {
      const text =
        "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAA...\n-----END OPENSSH PRIVATE KEY-----";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.PRIVATE_KEY,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
    });
  });

  describe("Pattern Priority", () => {
    it("should have all redaction types defined", () => {
      const types = Object.values(RedactionType);

      types.forEach((type) => {
        const pattern = REDACTION_PATTERNS.find((p) => p.type === type);
        expect(pattern).toBeDefined();
        expect(pattern!.pattern).toBeInstanceOf(RegExp);
        expect(pattern!.replacement).toBeDefined();
      });
    });

    it("should have descriptive replacement strings", () => {
      REDACTION_PATTERNS.forEach((pattern) => {
        expect(pattern.replacement).toContain("[REDACTED:");
        expect(pattern.replacement).toContain("]");
      });
    });

    it("should use global flag for multiple matches", () => {
      REDACTION_PATTERNS.forEach((pattern) => {
        expect(pattern.pattern.flags).toContain("g");
      });
    });

    it("should be case-insensitive where appropriate", () => {
      const apiKeyPattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.API_KEY,
      );
      expect(apiKeyPattern!.pattern.flags).toContain("i");
    });
  });

  describe("Edge Cases", () => {
    it("should not match partial email addresses", () => {
      const text = "This is not@email";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.EMAIL,
      );

      const match = text.match(pattern!.pattern);
      expect(match).toBeNull();
    });

    it("should handle edge case IPs conservatively", () => {
      const text = "Valid IP: 192.168.1.1";
      const pattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.IP_ADDRESS,
      );

      // Pattern should match valid IPs
      const match = text.match(pattern!.pattern);
      expect(match).toBeTruthy();
      expect(match![0]).toBe("192.168.1.1");
    });

    it("should handle multiple sensitive items in one string", () => {
      const text =
        "Email: user@example.com, Phone: 555-123-4567, IP: 192.168.1.1";

      const emailPattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.EMAIL,
      );
      const phonePattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.PHONE,
      );
      const ipPattern = REDACTION_PATTERNS.find(
        (p) => p.type === RedactionType.IP_ADDRESS,
      );

      expect(text.match(emailPattern!.pattern)).toBeTruthy();
      expect(text.match(phonePattern!.pattern)).toBeTruthy();
      expect(text.match(ipPattern!.pattern)).toBeTruthy();
    });
  });
});
