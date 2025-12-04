/**
 * Context Scoring Calculation (Domain Layer - Pure Functions)
 *
 * Calculates relevance scores for context items based on:
 * - Recency: When was it last accessed? (60% weight)
 * - Access frequency: How often is it used? (40% weight)
 *
 * All functions are pure (no I/O, no side effects) for easy testing.
 */

/**
 * Calculate overall context score for an item
 *
 * @param lastAccessedAt - Last time the item was accessed
 * @param accessCount - Total number of times accessed
 * @param now - Current time (defaults to Date.now(), injectable for testing)
 * @returns Score between 0.0 and 1.0
 */
export function calculateContextScore(
  lastAccessedAt: Date,
  accessCount: number,
  now: Date = new Date(),
): number {
  const recencyFactor = calculateRecencyFactor(lastAccessedAt, now);
  const accessFactor = normalizeAccessCount(accessCount);

  // Weighted combination: 60% recency, 40% access frequency
  const score = 0.6 * recencyFactor + 0.4 * accessFactor;

  // Ensure score is clamped to [0.0, 1.0]
  return Math.max(0.0, Math.min(1.0, score));
}

/**
 * Calculate recency factor (decays over 30 days)
 *
 * @param lastAccessed - Last access timestamp
 * @param now - Current time
 * @returns Factor between 0.0 and 1.0
 */
export function calculateRecencyFactor(lastAccessed: Date, now: Date): number {
  const millisPerDay = 1000 * 60 * 60 * 24;
  const daysSince = (now.getTime() - lastAccessed.getTime()) / millisPerDay;

  // Linear decay over 30 days: 1.0 at 0 days, 0.0 at 30 days
  const factor = 1.0 - daysSince / 30;

  // Clamp to [0.0, 1.0]
  return Math.max(0.0, Math.min(1.0, factor));
}

/**
 * Normalize access count to 0.0-1.0 range
 *
 * @param count - Number of times accessed
 * @param maxCount - Maximum count to normalize against (default 100)
 * @returns Normalized value between 0.0 and 1.0
 */
export function normalizeAccessCount(count: number, maxCount = 100): number {
  // Linear normalization, capped at 1.0
  return Math.min(count / maxCount, 1.0);
}
