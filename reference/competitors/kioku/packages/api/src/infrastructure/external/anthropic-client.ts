/**
 * AnthropicClient - Claude API wrapper for AI discovery refinement
 *
 * Purpose: Implement IAIClient interface for discovery refinement.
 * Used by: AIDiscoveryService
 *
 * @module infrastructure/external
 */

import Anthropic from "@anthropic-ai/sdk";
import type {
  IAIClient,
  DiscoveryRefinementRequest,
  DiscoveryRefinementResponse,
} from "application/ports/IAIClient";
import type { DiscoveryType } from "domain/models/RefinedDiscovery";
import { logger } from "../cli/logger";

export class AnthropicClient implements IAIClient {
  private readonly client: Anthropic;
  private readonly model: string;

  constructor(apiKey?: string, model = "claude-3-sonnet-20240229") {
    const key = apiKey || process.env.ANTHROPIC_API_KEY;

    if (!key) {
      throw new Error("ANTHROPIC_API_KEY environment variable is required");
    }

    this.client = new Anthropic({ apiKey: key });
    this.model = model;

    logger.info("AnthropicClient initialized", { model });
  }

  async refineDiscovery(
    request: DiscoveryRefinementRequest,
  ): Promise<DiscoveryRefinementResponse> {
    const startTime = Date.now();

    try {
      logger.debug("Discovery refinement requested", {
        sessionId: request.sessionContext.sessionId,
        model: this.model,
        rawContentLength: request.rawContent.length,
      });

      const { buildRefinementPrompt, REFINEMENT_SYSTEM_PROMPT } = await import(
        "./discovery-refinement-prompt"
      );

      const userPrompt = buildRefinementPrompt(request);

      // Call Claude API
      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 1024,
        system: REFINEMENT_SYSTEM_PROMPT,
        messages: [
          {
            role: "user",
            content: userPrompt,
          },
        ],
      });

      const processingTime = Date.now() - startTime;

      // Extract JSON from response
      const content = response.content[0];
      if (!content || content.type !== "text") {
        throw new Error("Unexpected response type from Claude");
      }

      const jsonText = (content as { type: "text"; text: string }).text.trim();
      const refinement = JSON.parse(jsonText);

      // Validate response structure
      if (
        !refinement.type ||
        !refinement.refinedContent ||
        typeof refinement.confidence !== "number"
      ) {
        throw new Error("Invalid refinement response structure");
      }

      logger.info("Discovery refined successfully", {
        sessionId: request.sessionContext.sessionId,
        type: refinement.type,
        confidence: refinement.confidence,
        tokensUsed: response.usage.input_tokens + response.usage.output_tokens,
        processingTime,
      });

      return {
        type: refinement.type as DiscoveryType,
        refinedContent: refinement.refinedContent,
        confidence: refinement.confidence,
        supportingEvidence: refinement.supportingEvidence || "",
        suggestedModule: refinement.suggestedModule,
        tokensUsed: response.usage.input_tokens + response.usage.output_tokens,
        processingTime,
      };
    } catch (error) {
      const processingTime = Date.now() - startTime;
      logger.error("Discovery refinement failed", {
        error: error instanceof Error ? error.message : String(error),
        sessionId: request.sessionContext.sessionId,
        processingTime,
      });
      throw error;
    }
  }

  async refineDiscoveries(
    requests: DiscoveryRefinementRequest[],
  ): Promise<DiscoveryRefinementResponse[]> {
    // TODO: Implement batch refinement
    return Promise.all(requests.map((req) => this.refineDiscovery(req)));
  }

  async checkHealth(): Promise<{
    available: boolean;
    quotaRemaining?: number;
    error?: string;
  }> {
    try {
      // Simple API call to verify connectivity and auth
      const response = await this.client.messages.create({
        model: this.model,
        max_tokens: 10,
        messages: [
          {
            role: "user",
            content: "ping",
          },
        ],
      });

      logger.debug("Anthropic API health check passed", {
        model: this.model,
        tokensUsed: response.usage.input_tokens + response.usage.output_tokens,
      });

      return {
        available: true,
        // Note: Anthropic doesn't provide quota info in response headers currently
      };
    } catch (error) {
      logger.warn("Anthropic API health check failed", {
        error: error instanceof Error ? error.message : String(error),
      });

      return {
        available: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  async estimateCost(
    messageCount: number,
  ): Promise<{ estimatedTokens: number; estimatedCostUsd: number }> {
    // Rough estimate: ~500 tokens per message
    const estimatedTokens = messageCount * 500;

    // Claude 3 Sonnet pricing (as of 2024): $3/MTok input, $15/MTok output
    // Assume 70% input, 30% output
    const inputCost = ((estimatedTokens * 0.7) / 1_000_000) * 3;
    const outputCost = ((estimatedTokens * 0.3) / 1_000_000) * 15;
    const estimatedCostUsd = inputCost + outputCost;

    return {
      estimatedTokens,
      estimatedCostUsd,
    };
  }
}
