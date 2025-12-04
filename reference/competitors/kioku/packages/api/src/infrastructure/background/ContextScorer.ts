/**
 * Context Scorer Background Service
 *
 * Periodically recalculates scores for all context items based on recency and access patterns.
 */

import type { SQLiteAdapter } from 'infrastructure/storage/sqlite-adapter';
import { calculateContextScore } from 'domain/calculations/context-scoring';
import { logger } from '../cli/logger';

export class ContextScorer {
  private sqliteAdapter: SQLiteAdapter;
  private intervalId: Timer | null = null;
  private readonly intervalMs: number;

  constructor(sqliteAdapter: SQLiteAdapter, intervalMs = 300000) {
    // Default: 5 minutes (300000ms)
    this.sqliteAdapter = sqliteAdapter;
    this.intervalMs = intervalMs;
  }

  /**
   * Start the background scorer
   */
  start(): void {
    if (this.intervalId) {
      logger.warn('Context scorer already running');
      return;
    }

    logger.info('Starting context scorer', {
      intervalMs: this.intervalMs,
      intervalMinutes: this.intervalMs / 60000,
    });

    // Run immediately on start
    this.scoreAll().catch((error) => {
      logger.error('Failed to score context items on startup', { error });
    });

    // Then run periodically
    this.intervalId = setInterval(() => {
      this.scoreAll().catch((error) => {
        logger.error('Failed to score context items', { error });
      });
    }, this.intervalMs);
  }

  /**
   * Stop the background scorer
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      logger.info('Context scorer stopped');
    }
  }

  /**
   * Score all active context items
   */
  private async scoreAll(): Promise<void> {
    logger.debug('Scoring all context items');

    const items = this.sqliteAdapter.getContextItemsByStatus('active');

    if (items.length === 0) {
      logger.debug('No active items to score');
      return;
    }

    const now = new Date();
    let updated = 0;

    for (const item of items) {
      const { lastAccessedAt, accessCount } = item.scoring;

      // Calculate new score
      const newScore = calculateContextScore(lastAccessedAt, accessCount, now);

      // Only update if score changed significantly (> 1%)
      if (Math.abs(newScore - item.scoring.score) > 0.01) {
        this.sqliteAdapter.saveContextItem({
          ...item,
          scoring: {
            ...item.scoring,
            score: newScore,
          },
        });
        updated++;
      }
    }

    logger.info('Context items scored', {
      total: items.length,
      updated,
      unchanged: items.length - updated,
    });
  }
}
