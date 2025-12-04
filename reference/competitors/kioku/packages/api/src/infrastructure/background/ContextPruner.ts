/**
 * Context Pruner Background Service
 *
 * Periodically checks context window usage and prunes if threshold exceeded.
 */

import type { SQLiteAdapter } from "infrastructure/storage/sqlite-adapter";
import { PruneContext } from "application/use-cases/PruneContext";
import { logger } from "infrastructure/cli/logger";

export class ContextPruner {
  private pruneContext: PruneContext;
  private intervalId: Timer | null = null;
  private readonly intervalMs: number;

  constructor(sqliteAdapter: SQLiteAdapter, intervalMs = 600000) {
    // Default: 10 minutes (600000ms)
    this.pruneContext = new PruneContext(sqliteAdapter);
    this.intervalMs = intervalMs;
  }

  /**
   * Start the background pruner
   */
  start(): void {
    if (this.intervalId) {
      logger.warn("Context pruner already running");
      return;
    }

    logger.info("Starting context pruner", {
      intervalMs: this.intervalMs,
      intervalMinutes: this.intervalMs / 60000,
    });

    // Run immediately on start
    this.prune().catch((error) => {
      logger.error("Failed to prune context on startup", { error });
    });

    // Then run periodically
    this.intervalId = setInterval(() => {
      this.prune().catch((error) => {
        logger.error("Failed to prune context", { error });
      });
    }, this.intervalMs);
  }

  /**
   * Stop the background pruner
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      logger.info("Context pruner stopped");
    }
  }

  /**
   * Execute pruning if needed
   */
  private async prune(): Promise<void> {
    try {
      const result = await this.pruneContext.execute();

      if (result.pruned) {
        logger.info("Context pruned by background service", {
          archivedCount: result.archivedCount,
          usageBefore: `${(result.usageBefore * 100).toFixed(1)}%`,
          usageAfter: `${(result.usageAfter * 100).toFixed(1)}%`,
        });
      } else {
        logger.debug("Pruning not needed", {
          usage: `${(result.usageBefore * 100).toFixed(1)}%`,
        });
      }
    } catch (error) {
      logger.error("Pruning failed", { error });
      throw error;
    }
  }
}
