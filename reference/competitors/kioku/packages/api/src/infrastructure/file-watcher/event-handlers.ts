/**
 * File Watcher Event Handlers
 *
 * Handler functions for file system events (add, change, unlink)
 * These orchestrate the chunking service to keep context up-to-date
 */

import type { ChangeEvent } from "domain/models/ChangeEvent";
import type { ChunkingService } from "application/services/ChunkingService";
import { logger } from "infrastructure/cli/logger";
import * as fs from "fs/promises";

/**
 * Create event handlers for file watcher
 */
export function createFileWatcherHandlers(chunkingService: ChunkingService): {
  handleFileAdded: (event: ChangeEvent) => Promise<void>;
  handleFileChanged: (event: ChangeEvent) => Promise<void>;
  handleFileDeleted: (event: ChangeEvent) => Promise<void>;
} {
  /**
   * Handle file addition
   * Reads the file and processes it to extract chunks
   */
  const handleFileAdded = async (event: ChangeEvent): Promise<void> => {
    logger.debug("File added event", { filePath: event.filePath });

    try {
      // Only process TypeScript/JavaScript files
      if (!isCodeFile(event.filePath)) {
        logger.debug("Skipping non-code file", { filePath: event.filePath });
        return;
      }

      // Read file content
      const code = await fs.readFile(event.filePath, "utf-8");

      // Process file to extract chunks and generate embeddings
      const result = await chunkingService.processFile(event.filePath, code);

      logger.info("File added and processed", {
        filePath: event.filePath,
        chunksAdded: result.chunksAdded,
        chunksExtracted: result.chunksExtracted,
        processingTimeMs: result.processingTimeMs,
      });
    } catch (error) {
      logger.error("Error handling file addition", {
        filePath: event.filePath,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  };

  /**
   * Handle file modification
   * Re-processes the file and updates chunks
   */
  const handleFileChanged = async (event: ChangeEvent): Promise<void> => {
    logger.debug("File changed event", { filePath: event.filePath });

    try {
      // Only process TypeScript/JavaScript files
      if (!isCodeFile(event.filePath)) {
        logger.debug("Skipping non-code file", { filePath: event.filePath });
        return;
      }

      // Read updated file content
      const code = await fs.readFile(event.filePath, "utf-8");

      // Update file chunks (detects changes and applies them)
      const result = await chunkingService.processFile(event.filePath, code);

      logger.info("File updated", {
        filePath: event.filePath,
        chunksAdded: result.chunksAdded,
        chunksModified: result.chunksModified,
        chunksDeleted: result.chunksDeleted,
        processingTimeMs: result.processingTimeMs,
      });
    } catch (error) {
      logger.error("Error handling file change", {
        filePath: event.filePath,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  };

  /**
   * Handle file deletion
   * Removes all chunks for the deleted file
   */
  const handleFileDeleted = async (event: ChangeEvent): Promise<void> => {
    logger.debug("File deleted event", { filePath: event.filePath });

    try {
      // Only process TypeScript/JavaScript files
      if (!isCodeFile(event.filePath)) {
        logger.debug("Skipping non-code file", { filePath: event.filePath });
        return;
      }

      // Delete all chunks for the file
      await chunkingService.deleteChunksForFile(event.filePath);

      logger.info("File deleted and chunks removed", {
        filePath: event.filePath,
      });
    } catch (error) {
      logger.error("Error handling file deletion", {
        filePath: event.filePath,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  };

  return {
    handleFileAdded,
    handleFileChanged,
    handleFileDeleted,
  };
}

/**
 * Check if file is a code file that should be processed
 */
function isCodeFile(filePath: string): boolean {
  const codeExtensions = [
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mts",
    ".mjs",
    ".cts",
    ".cjs",
  ];

  return codeExtensions.some((ext) => filePath.endsWith(ext));
}
