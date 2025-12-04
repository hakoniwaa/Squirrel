/**
 * IAIClient - Interface for AI API operations
 *
 * Purpose: Define contract for AI-powered discovery refinement.
 * Implementation: AnthropicClient will implement this.
 * Used by: AIDiscoveryService
 *
 * @module application/ports
 */

import type { DiscoveryType } from "domain/models/RefinedDiscovery";

export interface DiscoveryRefinementRequest {
  rawContent: string;
  sessionContext: {
    sessionId: string;
    conversationMessages: string[];
    filesAccessed: string[];
  };
}

export interface DiscoveryRefinementResponse {
  type: DiscoveryType;
  refinedContent: string;
  confidence: number; // 0-1
  supportingEvidence: string;
  suggestedModule?: string;
  tokensUsed: number;
  processingTime: number; // Milliseconds
}

export interface IAIClient {
  /**
   * Refine a discovery using AI
   */
  refineDiscovery(
    request: DiscoveryRefinementRequest,
  ): Promise<DiscoveryRefinementResponse>;

  /**
   * Batch refine multiple discoveries
   */
  refineDiscoveries(
    requests: DiscoveryRefinementRequest[],
  ): Promise<DiscoveryRefinementResponse[]>;

  /**
   * Check if API is available (for health checks)
   */
  checkHealth(): Promise<{
    available: boolean;
    quotaRemaining?: number;
    error?: string;
  }>;

  /**
   * Get estimated cost for a refinement request
   */
  estimateCost(messageCount: number): Promise<{
    estimatedTokens: number;
    estimatedCostUsd: number;
  }>;
}
