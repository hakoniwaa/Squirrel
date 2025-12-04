/**
 * Ranking Calculator - Pure functions for search result ranking
 *
 * Purpose: Calculate boost factors for search results based on recency, module context, and frequency.
 * Layer: Domain (pure calculations)
 * Used by: RankSearchResultsUseCase
 *
 * Boost Strategy:
 * - Recency: 1.5x (<24h), 1.2x (<7d), 1.0x (older)
 * - Module: 1.3x (same module as current work), 1.0x (different)
 * - Frequency: 1 + (access_count / 100), capped at 1.5x
 * - Final: semantic_score × recency × module × frequency
 *
 * @module domain/calculations
 */

const MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000;
const RECENCY_BOOST_24H = 1.5;
const RECENCY_BOOST_7D = 1.2;
const RECENCY_BOOST_DEFAULT = 1.0;

const MODULE_BOOST_SAME = 1.3;
const MODULE_BOOST_DIFFERENT = 1.0;

const FREQUENCY_BOOST_CAP = 1.5;
const FREQUENCY_BOOST_DIVISOR = 100;

/**
 * Calculate recency boost based on last access time
 *
 * @param lastAccessed - When the file was last accessed
 * @param now - Current time (for testing)
 * @returns Boost multiplier (1.5x, 1.2x, or 1.0x)
 */
export function calculateRecencyBoost(
  lastAccessed: Date,
  now: Date = new Date(),
): number {
  const ageInMs = now.getTime() - lastAccessed.getTime();
  const ageInDays = ageInMs / MILLISECONDS_PER_DAY;

  if (ageInDays <= 1) {
    // Less than or equal to 24 hours
    return RECENCY_BOOST_24H;
  } else if (ageInDays <= 7) {
    // Less than or equal to 7 days
    return RECENCY_BOOST_7D;
  } else {
    // Older than 7 days
    return RECENCY_BOOST_DEFAULT;
  }
}

/**
 * Calculate module boost based on current module context
 *
 * @param currentModule - Module the developer is currently working in
 * @param resultModule - Module the search result belongs to
 * @returns Boost multiplier (1.3x same, 1.0x different)
 */
export function calculateModuleBoost(
  currentModule: string | undefined,
  resultModule: string | undefined,
): number {
  // Handle undefined, null, or empty modules
  if (!currentModule || !resultModule || currentModule === "" || resultModule === "") {
    return MODULE_BOOST_DIFFERENT;
  }

  // Exact match (case-sensitive)
  if (currentModule === resultModule) {
    return MODULE_BOOST_SAME;
  }

  return MODULE_BOOST_DIFFERENT;
}

/**
 * Calculate frequency boost based on access count
 *
 * Formula: 1 + (access_count / 100), capped at 1.5x
 *
 * @param accessCount - Number of times the file has been accessed
 * @returns Boost multiplier (1.0x to 1.5x)
 */
export function calculateFrequencyBoost(accessCount: number): number {
  // Handle negative counts
  if (accessCount < 0) {
    return 1.0;
  }

  const boost = 1 + accessCount / FREQUENCY_BOOST_DIVISOR;

  // Cap at 1.5x
  return Math.min(boost, FREQUENCY_BOOST_CAP);
}

/**
 * Calculate final score by multiplying semantic score with all boosts
 *
 * @param semanticScore - Base similarity score from vector search (0-1)
 * @param recencyBoost - Recency multiplier
 * @param moduleBoost - Module context multiplier
 * @param frequencyBoost - Access frequency multiplier
 * @returns Final ranked score
 */
export function calculateFinalScore(
  semanticScore: number,
  recencyBoost: number,
  moduleBoost: number,
  frequencyBoost: number,
): number {
  return semanticScore * recencyBoost * moduleBoost * frequencyBoost;
}
