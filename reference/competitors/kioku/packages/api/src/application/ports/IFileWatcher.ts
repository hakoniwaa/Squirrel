/**
 * IFileWatcher - Interface for file system watching
 *
 * Purpose: Define contract for monitoring file changes.
 * Implementation: FileWatcherService (chokidar wrapper) will implement this.
 * Used by: MCP server startup, context update orchestration
 *
 * @module application/ports
 */

import type { ChangeEvent, FileEventType } from 'domain/models/ChangeEvent';

export type FileChangeHandler = (event: ChangeEvent) => Promise<void>;

export interface FileWatcherOptions {
  ignored?: string[];      // Patterns to ignore (node_modules, .git, etc.)
  debounceMs?: number;     // Debounce delay in milliseconds
  pollIntervalMs?: number; // Polling interval for fallback
}

export interface IFileWatcher {
  /**
   * Start watching directory for changes
   */
  start(directory: string, options?: FileWatcherOptions): Promise<void>;

  /**
   * Stop watching
   */
  stop(): Promise<void>;

  /**
   * Register event handler
   */
  on(eventType: FileEventType | 'all', handler: FileChangeHandler): void;

  /**
   * Remove event handler
   */
  off(eventType: FileEventType | 'all', handler: FileChangeHandler): void;

  /**
   * Check if watcher is currently running
   */
  isWatching(): boolean;

  /**
   * Get watcher status (for health checks)
   */
  getStatus(): {
    isWatching: boolean;
    watchedDirectory: string | null;
    eventsProcessed: number;
    errors: number;
    lastError?: string;
  };
}
