/**
 * AIDiscoveryService - Orchestrate AI-enhanced discovery refinement
 *
 * Purpose: Coordinate regex extraction → redaction → AI refinement → filtering.
 * Layer: Application (orchestration)
 * Used by: Background services, MCP tools
 *
 * Flow:
 * 1. Receive raw discoveries from regex extraction
 * 2. Redact sensitive data (API keys, emails, etc.)
 * 3. Send to AI client for refinement
 * 4. Filter by confidence threshold (>= 0.6)
 * 5. Return refined discoveries
 *
 * @module application/services
 */

import type {
  IAIClient,
  DiscoveryRefinementRequest,
  DiscoveryRefinementResponse,
} from "application/ports/IAIClient";
import { redactSensitiveData } from "domain/calculations/redact-sensitive-data";
import { logger } from "infrastructure/cli/logger";

export interface SessionContext {
  sessionId: string;
  conversationMessages: string[];
  filesAccessed: string[];
}

export class AIDiscoveryService {
  private readonly CONFIDENCE_THRESHOLD = 0.6;

  constructor(private readonly aiClient: IAIClient) {
    logger.info("AIDiscoveryService initialized");
  }

  /**
   * Refine raw discoveries from a session using AI
   *
   * @param rawDiscoveries - Raw regex-extracted discoveries
   * @param sessionContext - Session metadata (messages, files)
   * @param allowList - Whitelist for redaction (optional)
   * @returns Refined discoveries with confidence >= 0.6
   */
  async refineSessionDiscoveries(
    rawDiscoveries: string[],
    sessionContext: SessionContext,
    allowList: string[] = [],
  ): Promise<DiscoveryRefinementResponse[]> {
    if (rawDiscoveries.length === 0) {
      logger.debug("No discoveries to refine", {
        sessionId: sessionContext.sessionId,
      });
      return [];
    }

    logger.info("Refining session discoveries", {
      sessionId: sessionContext.sessionId,
      discoveryCount: rawDiscoveries.length,
    });

    const refinedDiscoveries: DiscoveryRefinementResponse[] = [];

    for (const rawContent of rawDiscoveries) {
      try {
        // Step 1: Redact sensitive data before sending to AI
        const redactionResult = redactSensitiveData(rawContent, allowList);

        if (redactionResult.hasRedactions) {
          logger.debug("Redacted sensitive data from discovery", {
            sessionId: sessionContext.sessionId,
            redactionCount: redactionResult.redactionsApplied.length,
            types: redactionResult.redactionsApplied.map((r) => r.type),
          });
        }

        // Step 2: Build refinement request
        const request: DiscoveryRefinementRequest = {
          rawContent: redactionResult.redactedText,
          sessionContext: {
            sessionId: sessionContext.sessionId,
            conversationMessages: sessionContext.conversationMessages,
            filesAccessed: sessionContext.filesAccessed,
          },
        };

        // Step 3: Call AI for refinement
        const refinedDiscovery = await this.aiClient.refineDiscovery(request);

        // Step 4: Filter by confidence threshold
        if (refinedDiscovery.confidence >= this.CONFIDENCE_THRESHOLD) {
          refinedDiscoveries.push(refinedDiscovery);

          logger.debug("Discovery refined and accepted", {
            sessionId: sessionContext.sessionId,
            type: refinedDiscovery.type,
            confidence: refinedDiscovery.confidence,
            tokensUsed: refinedDiscovery.tokensUsed,
          });
        } else {
          logger.debug("Discovery rejected due to low confidence", {
            sessionId: sessionContext.sessionId,
            confidence: refinedDiscovery.confidence,
            threshold: this.CONFIDENCE_THRESHOLD,
          });
        }
      } catch (error) {
        logger.error("Failed to refine discovery", {
          sessionId: sessionContext.sessionId,
          error: error instanceof Error ? error.message : String(error),
          rawContent: rawContent.substring(0, 100), // Log first 100 chars
        });
        throw error;
      }
    }

    logger.info("Session discoveries refined", {
      sessionId: sessionContext.sessionId,
      totalDiscoveries: rawDiscoveries.length,
      acceptedDiscoveries: refinedDiscoveries.length,
      rejectedCount: rawDiscoveries.length - refinedDiscoveries.length,
    });

    return refinedDiscoveries;
  }

  /**
   * Check AI API health
   */
  async checkAPIHealth(): Promise<{
    available: boolean;
    quotaRemaining?: number;
    error?: string;
  }> {
    return this.aiClient.checkHealth();
  }

  /**
   * Estimate cost for refining discoveries
   *
   * @param discoveryCount - Number of discoveries to refine
   * @returns Estimated tokens and cost
   */
  async estimateRefinementCost(discoveryCount: number): Promise<{
    estimatedTokens: number;
    estimatedCostUsd: number;
  }> {
    return this.aiClient.estimateCost(discoveryCount);
  }
}
