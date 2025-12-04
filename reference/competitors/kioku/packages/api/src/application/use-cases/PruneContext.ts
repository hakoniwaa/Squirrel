/**
 * Prune Context Use Case
 *
 * Manages context window by archiving low-score items when usage exceeds threshold.
 */

 
import type { SQLiteAdapter } from "infrastructure/storage/sqlite-adapter";

export interface PruneResult {
  pruned: boolean;
  usageBefore: number;
  usageAfter: number;
  archivedCount: number;
  threshold: number;
}

export class PruneContext {
  private sqliteAdapter: SQLiteAdapter;
  private readonly maxTokens = 100000; // 100k token context window
  private readonly threshold = 0.8; // 80% threshold
  private readonly prunePercentage = 0.2; // Archive bottom 20%

  constructor(sqliteAdapter: SQLiteAdapter) {
    this.sqliteAdapter = sqliteAdapter;
  }

  /**
   * Calculate current context window usage (0.0 to 1.0)
   */
  async calculateUsage(): Promise<number> {
    const items = this.sqliteAdapter.getContextItemsByStatus("active");

    if (items.length === 0) {
      return 0;
    }

    // Sum up tokens from all active items
    const totalTokens = items.reduce((sum, item) => sum + item.tokens, 0);

    return totalTokens / this.maxTokens;
  }

  /**
   * Execute pruning if threshold exceeded
   */
  async execute(): Promise<PruneResult> {
    const usageBefore = await this.calculateUsage();

    // If below threshold, no pruning needed
    if (usageBefore < this.threshold) {
      return {
        pruned: false,
        usageBefore,
        usageAfter: usageBefore,
        archivedCount: 0,
        threshold: this.threshold,
      };
    }

    // Load all active items
    const activeItems = this.sqliteAdapter.getContextItemsByStatus("active");

    if (activeItems.length === 0) {
      return {
        pruned: false,
        usageBefore: 0,
        usageAfter: 0,
        archivedCount: 0,
        threshold: this.threshold,
      };
    }

    // Sort by score (ascending) - lowest scores first
    const sortedItems = [...activeItems].sort(
      (a, b) => a.scoring.score - b.scoring.score,
    );

    // Calculate how many to archive (bottom 20%)
    const archiveCount = Math.ceil(sortedItems.length * this.prunePercentage);
    const itemsToArchive = sortedItems.slice(0, archiveCount);

    // Archive items by updating their status
    for (const item of itemsToArchive) {
      this.sqliteAdapter.saveContextItem({
        ...item,
        status: "archived",
      });
    }

    const usageAfter = await this.calculateUsage();

    return {
      pruned: true,
      usageBefore,
      usageAfter,
      archivedCount: itemsToArchive.length,
      threshold: this.threshold,
    };
  }
}
