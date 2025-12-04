import { describe, it, expect, beforeEach, vi } from "vitest";
import { AIDiscoveryService } from "../../../src/application/services/AIDiscoveryService";
import type { IAIClient } from "../../../src/application/ports/IAIClient";
import { DiscoveryType } from "../../../src/domain/models/RefinedDiscovery";

describe("AIDiscoveryService", () => {
  let service: AIDiscoveryService;
  let mockAIClient: IAIClient;

  beforeEach(() => {
    // Create mock AI client
    mockAIClient = {
      refineDiscovery: vi.fn(),
      refineDiscoveries: vi.fn(),
      checkHealth: vi.fn(),
      estimateCost: vi.fn(),
    };

    service = new AIDiscoveryService(mockAIClient);
  });

  describe("refineSessionDiscoveries", () => {
    const sessionContext = {
      sessionId: "test-session-123",
      conversationMessages: [
        "User: Let's use JWT for authentication",
        "AI: Good choice for stateless auth",
      ],
      filesAccessed: ["src/auth/auth-service.ts"],
    };

    it("should refine raw discoveries using AI client", async () => {
      // Arrange
      const rawDiscoveries = ["JWT authentication pattern", "Stateless auth"];

      (mockAIClient.refineDiscovery as any).mockResolvedValue({
        type: DiscoveryType.PATTERN,
        refinedContent: "Use JWT tokens for stateless authentication",
        confidence: 0.95,
        supportingEvidence: "User explicitly chose JWT",
        suggestedModule: "auth",
        tokensUsed: 150,
        processingTime: 120,
      });

      // Act
      const results = await service.refineSessionDiscoveries(
        rawDiscoveries,
        sessionContext,
      );

      // Assert
      expect(results).toHaveLength(2);
      expect(results[0].refinedContent).toBe(
        "Use JWT tokens for stateless authentication",
      );
      expect(results[0].confidence).toBe(0.95);
      expect(mockAIClient.refineDiscovery).toHaveBeenCalledTimes(2);
    });

    it("should filter out discoveries with confidence < 0.6", async () => {
      // Arrange
      const rawDiscoveries = ["Discovery 1", "Discovery 2", "Discovery 3"];

      (mockAIClient.refineDiscovery as any)
        .mockResolvedValueOnce({
          type: DiscoveryType.PATTERN,
          refinedContent: "High confidence discovery",
          confidence: 0.85,
          supportingEvidence: "Strong evidence",
          tokensUsed: 100,
          processingTime: 100,
        })
        .mockResolvedValueOnce({
          type: DiscoveryType.INSIGHT,
          refinedContent: "Low confidence discovery",
          confidence: 0.45, // Below threshold
          supportingEvidence: "Weak evidence",
          tokensUsed: 80,
          processingTime: 90,
        })
        .mockResolvedValueOnce({
          type: DiscoveryType.RULE,
          refinedContent: "Medium confidence discovery",
          confidence: 0.72,
          supportingEvidence: "Decent evidence",
          tokensUsed: 90,
          processingTime: 95,
        });

      // Act
      const results = await service.refineSessionDiscoveries(
        rawDiscoveries,
        sessionContext,
      );

      // Assert - Only 2 results (confidence >= 0.6)
      expect(results).toHaveLength(2);
      expect(results[0].confidence).toBe(0.85);
      expect(results[1].confidence).toBe(0.72);
      expect(results.every((r) => r.confidence >= 0.6)).toBe(true);
    });

    it("should redact sensitive data before sending to AI", async () => {
      // Arrange
      const rawDiscoveries = [
        "API key: sk-abc123def456ghi789jkl012mno345pqr678",
      ];

      (mockAIClient.refineDiscovery as any).mockResolvedValue({
        type: DiscoveryType.ISSUE,
        refinedContent: "API key exposed in code",
        confidence: 0.9,
        supportingEvidence: "Found in conversation",
        tokensUsed: 100,
        processingTime: 100,
      });

      // Act
      await service.refineSessionDiscoveries(rawDiscoveries, sessionContext);

      // Assert - Verify redaction occurred
      const callArg = (mockAIClient.refineDiscovery as any).mock.calls[0][0];
      expect(callArg.rawContent).toContain("[REDACTED:API_KEY]");
      expect(callArg.rawContent).not.toContain("sk-abc123");
    });

    it("should handle empty discoveries array", async () => {
      // Arrange
      const rawDiscoveries: string[] = [];

      // Act
      const results = await service.refineSessionDiscoveries(
        rawDiscoveries,
        sessionContext,
      );

      // Assert
      expect(results).toHaveLength(0);
      expect(mockAIClient.refineDiscovery).not.toHaveBeenCalled();
    });

    it("should handle AI client errors gracefully", async () => {
      // Arrange
      const rawDiscoveries = ["Test discovery"];

      (mockAIClient.refineDiscovery as any).mockRejectedValue(
        new Error("API rate limit exceeded"),
      );

      // Act & Assert - Should propagate error
      await expect(
        service.refineSessionDiscoveries(rawDiscoveries, sessionContext),
      ).rejects.toThrow("API rate limit exceeded");
    });

    it("should preserve session context in refinement requests", async () => {
      // Arrange
      const rawDiscoveries = ["Test discovery"];

      (mockAIClient.refineDiscovery as any).mockResolvedValue({
        type: DiscoveryType.PATTERN,
        refinedContent: "Refined",
        confidence: 0.8,
        supportingEvidence: "Evidence",
        tokensUsed: 100,
        processingTime: 100,
      });

      // Act
      await service.refineSessionDiscoveries(rawDiscoveries, sessionContext);

      // Assert
      const callArg = (mockAIClient.refineDiscovery as any).mock.calls[0][0];
      expect(callArg.sessionContext.sessionId).toBe("test-session-123");
      expect(callArg.sessionContext.conversationMessages).toEqual(
        sessionContext.conversationMessages,
      );
      expect(callArg.sessionContext.filesAccessed).toEqual(
        sessionContext.filesAccessed,
      );
    });
  });

  describe("checkAPIHealth", () => {
    it("should return health status from AI client", async () => {
      // Arrange
      (mockAIClient.checkHealth as any).mockResolvedValue({
        available: true,
      });

      // Act
      const health = await service.checkAPIHealth();

      // Assert
      expect(health.available).toBe(true);
      expect(mockAIClient.checkHealth).toHaveBeenCalled();
    });

    it("should return unavailable when AI client fails", async () => {
      // Arrange
      (mockAIClient.checkHealth as any).mockResolvedValue({
        available: false,
        error: "Authentication failed",
      });

      // Act
      const health = await service.checkAPIHealth();

      // Assert
      expect(health.available).toBe(false);
      expect(health.error).toBe("Authentication failed");
    });
  });

  describe("estimateRefinementCost", () => {
    it("should estimate cost for refinement batch", async () => {
      // Arrange
      const discoveryCount = 10;

      (mockAIClient.estimateCost as any).mockResolvedValue({
        estimatedTokens: 5000,
        estimatedCostUsd: 0.033,
      });

      // Act
      const estimate = await service.estimateRefinementCost(discoveryCount);

      // Assert
      expect(estimate.estimatedTokens).toBe(5000);
      expect(estimate.estimatedCostUsd).toBe(0.033);
      expect(mockAIClient.estimateCost).toHaveBeenCalledWith(discoveryCount);
    });
  });

  describe("redaction", () => {
    it("should redact multiple sensitive data types", async () => {
      // Arrange
      const rawDiscoveries = [
        "Email: user@example.com, API key: sk-test123456789012345678901234567890",
        "Phone: 555-123-4567, IP: 192.168.1.100",
      ];

      const sessionContext = {
        sessionId: "test",
        conversationMessages: [],
        filesAccessed: [],
      };

      (mockAIClient.refineDiscovery as any).mockResolvedValue({
        type: DiscoveryType.PATTERN,
        refinedContent: "Redacted discovery",
        confidence: 0.8,
        supportingEvidence: "Evidence",
        tokensUsed: 100,
        processingTime: 100,
      });

      // Act
      await service.refineSessionDiscoveries(rawDiscoveries, sessionContext);

      // Assert
      const firstCall = (mockAIClient.refineDiscovery as any).mock.calls[0][0];
      const secondCall = (mockAIClient.refineDiscovery as any).mock.calls[1][0];

      expect(firstCall.rawContent).toContain("[REDACTED:EMAIL]");
      expect(firstCall.rawContent).toContain("[REDACTED:API_KEY]");
      expect(secondCall.rawContent).toContain("[REDACTED:PHONE]");
      expect(secondCall.rawContent).toContain("[REDACTED:IP_ADDRESS]");
    });

    it("should respect allow-list for redaction", async () => {
      // Arrange
      const rawDiscoveries = ["Contact: support@kioku.dev"];
      const sessionContext = {
        sessionId: "test",
        conversationMessages: [],
        filesAccessed: [],
      };

      (mockAIClient.refineDiscovery as any).mockResolvedValue({
        type: DiscoveryType.PATTERN,
        refinedContent: "Contact info",
        confidence: 0.7,
        supportingEvidence: "Evidence",
        tokensUsed: 100,
        processingTime: 100,
      });

      // Act
      await service.refineSessionDiscoveries(rawDiscoveries, sessionContext, [
        "support@kioku.dev",
      ]);

      // Assert
      const callArg = (mockAIClient.refineDiscovery as any).mock.calls[0][0];
      expect(callArg.rawContent).toContain("support@kioku.dev");
      expect(callArg.rawContent).not.toContain("[REDACTED:EMAIL]");
    });
  });
});
