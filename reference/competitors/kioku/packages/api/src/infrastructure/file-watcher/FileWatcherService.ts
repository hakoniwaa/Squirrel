/**
 * FileWatcherService - File system monitoring using chokidar
 *
 * Purpose: Implement IFileWatcher interface for real-time file change detection.
 * Used by: MCP server, context update orchestration
 *
 * @module infrastructure/file-watcher
 */

import type { FSWatcher } from "chokidar";
import chokidar from "chokidar";
import { minimatch } from "minimatch";
import type {
  IFileWatcher,
  FileChangeHandler,
  FileWatcherOptions,
} from "application/ports/IFileWatcher";
import { FileEventType } from "domain/models/ChangeEvent";
import type { ChangeEvent } from "domain/models/ChangeEvent";
import { logger } from "../cli/logger";
import { randomUUID } from "crypto";

export class FileWatcherService implements IFileWatcher {
  private watcher: FSWatcher | null = null;
  private handlers = new Map<FileEventType | "all", Set<FileChangeHandler>>();
  private watchedDirectory: string | null = null;
  private ignoredPatterns: string[] = [];
  private eventsProcessed = 0;
  private errors = 0;
  private lastError?: string;

  async start(directory: string, options?: FileWatcherOptions): Promise<void> {
    if (this.watcher) {
      logger.warn("FileWatcher already running, stopping first");
      await this.stop();
    }

    logger.info("Starting FileWatcher", { directory, options });

    const ignored = options?.ignored || [
      "**/node_modules/**",
      "**/.git/**",
      "**/dist/**",
      "**/build/**",
    ];

    // Store patterns for later filtering
    this.ignoredPatterns = ignored;

    this.watcher = chokidar.watch(directory, {
      ignored,
      persistent: true,
      ignoreInitial: true,
      ignorePermissionErrors: true,
      depth: 99,
      awaitWriteFinish: {
        stabilityThreshold: options?.debounceMs || 400,
        pollInterval: options?.pollIntervalMs || 100,
      },
    });

    this.watchedDirectory = directory;

    // Register event listeners
    this.watcher
      .on("add", (path) => this.handleEvent(FileEventType.ADD, path))
      .on("change", (path) => this.handleEvent(FileEventType.CHANGE, path))
      .on("unlink", (path) => this.handleEvent(FileEventType.UNLINK, path))
      .on("addDir", () => {
        // Ignore directory events - we only care about files
      })
      .on("unlinkDir", () => {
        // Ignore directory events - we only care about files
      })
      .on("error", (error: unknown) => {
        this.errors++;
        this.lastError = error instanceof Error ? error.message : String(error);
        logger.error("FileWatcher error", { error });
      });

    // Wait for watcher to be ready (important for tests and reliability)
    await new Promise<void>((resolve) => {
      this.watcher!.on("ready", () => {
        logger.info("FileWatcher started successfully");
        resolve();
      });
    });
  }

  async stop(): Promise<void> {
    if (this.watcher) {
      await this.watcher.close();
      this.watcher = null;
      this.watchedDirectory = null;
      logger.info("FileWatcher stopped");
    }
  }

  on(eventType: FileEventType | "all", handler: FileChangeHandler): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);
  }

  off(eventType: FileEventType | "all", handler: FileChangeHandler): void {
    this.handlers.get(eventType)?.delete(handler);
  }

  isWatching(): boolean {
    return this.watcher !== null;
  }

  getStatus(): {
    isWatching: boolean;
    watchedDirectory: string | null;
    eventsProcessed: number;
    errors: number;
    lastError?: string;
  } {
    return {
      isWatching: this.isWatching(),
      watchedDirectory: this.watchedDirectory,
      eventsProcessed: this.eventsProcessed,
      errors: this.errors,
      ...(this.lastError ? { lastError: this.lastError } : {}),
    };
  }

  private async handleEvent(
    eventType: FileEventType,
    filePath: string,
  ): Promise<void> {
    // Double-check ignored patterns (belt and suspenders approach)
    // Chokidar should already filter, but we verify here for safety
    const shouldIgnore = this.shouldIgnorePath(filePath);
    if (shouldIgnore) {
      logger.debug("Ignoring event for filtered path", { eventType, filePath });
      return;
    }

    const event: ChangeEvent = {
      id: randomUUID(),
      eventType,
      filePath,
      timestamp: new Date(),
      processed: false,
    };

    logger.debug("File event detected", { eventType, filePath });

    this.eventsProcessed++;

    // Call specific handlers
    const specificHandlers = this.handlers.get(eventType);
    if (specificHandlers) {
      for (const handler of specificHandlers) {
        try {
          await handler(event);
        } catch (error) {
          logger.error("Handler error", { error, eventType, filePath });
        }
      }
    }

    // Call 'all' handlers
    const allHandlers = this.handlers.get("all");
    if (allHandlers) {
      for (const handler of allHandlers) {
        try {
          await handler(event);
        } catch (error) {
          logger.error("Handler error", { error, eventType, filePath });
        }
      }
    }
  }

  private shouldIgnorePath(filePath: string): boolean {
    // Use minimatch for proper glob pattern matching
    return this.ignoredPatterns.some((pattern) => {
      return minimatch(filePath, pattern, { dot: true });
    });
  }
}
