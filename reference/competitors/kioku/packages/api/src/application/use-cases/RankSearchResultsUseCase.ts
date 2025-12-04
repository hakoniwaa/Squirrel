/**
 * RankSearchResultsUseCase - Apply intelligent ranking to search results
 *
 * Purpose: Re-rank search results using recency, module context, and frequency boosts.
 * Layer: Application (use case)
 * Used by: ContextSearchTool
 *
 * Strategy:
 * 1. Calculate recency boost for each result (based on lastAccessed)
 * 2. Calculate module boost (1.3x if same module as current work)
 * 3. Calculate frequency boost (based on accessCount)
 * 4. Combine: finalScore = semanticScore × recency × module × frequency
 * 5. Sort by finalScore descending
 *
 * @module application/use-cases
 */

import type { SearchResult } from "domain/models/SearchResult";
import {
  calculateRecencyBoost,
  calculateModuleBoost,
  calculateFrequencyBoost,
  calculateFinalScore,
} from "domain/calculations/ranking-calculator";
import { logger } from "infrastructure/cli/logger";

export interface RankingContext {
  currentModule?: string;
  now?: Date; // For testing
}

export interface RankedSearchResult extends SearchResult {
  recencyBoost: number;
  moduleBoost: number;
  frequencyBoost: number;
  finalScore: number;
}

export class RankSearchResultsUseCase {
  /**
   * Apply intelligent ranking to search results
   *
   * @param results - Raw search results from vector search
   * @param context - Ranking context (current module, time)
   * @returns Ranked and sorted results
   */
  execute(
    results: SearchResult[],
    context: RankingContext,
  ): RankedSearchResult[] {
    if (results.length === 0) {
      logger.debug("No results to rank");
      return [];
    }

    const now = context.now || new Date();
    const currentModule = context.currentModule;

    logger.debug("Ranking search results", {
      resultCount: results.length,
      currentModule,
    });

    // Calculate boosts for each result
    const rankedResults: RankedSearchResult[] = results.map((result) => {
      const recencyBoost = calculateRecencyBoost(result.lastAccessed, now);
      const moduleBoost = calculateModuleBoost(currentModule, result.module);
      const frequencyBoost = calculateFrequencyBoost(result.accessCount);

      const finalScore = calculateFinalScore(
        result.score,
        recencyBoost,
        moduleBoost,
        frequencyBoost,
      );

      return {
        ...result,
        recencyBoost,
        moduleBoost,
        frequencyBoost,
        finalScore,
      };
    });

    // Sort by finalScore descending
    rankedResults.sort((a, b) => b.finalScore - a.finalScore);

    logger.debug("Ranking complete", {
      topResultScore: rankedResults[0]?.finalScore,
      topResultBoosts: {
        recency: rankedResults[0]?.recencyBoost,
        module: rankedResults[0]?.moduleBoost,
        frequency: rankedResults[0]?.frequencyBoost,
      },
    });

    return rankedResults;
  }
}
