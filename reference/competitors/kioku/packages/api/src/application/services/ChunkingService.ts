/**
 * ChunkingService - Orchestrates code chunking workflow
 *
 * Purpose: Coordinate extraction, diffing, storage, and embedding generation
 * Layer: Application (Orchestration)
 * Dependencies: Domain (chunk-extractor, chunk-differ), Infrastructure (storage, embeddings)
 *
 * Workflow:
 * 1. Extract chunks from source code (using chunk-extractor)
 * 2. Load existing chunks from storage
 * 3. Detect changes (using chunk-differ)
 * 4. Update storage (add/modify/delete chunks)
 * 5. Queue embeddings for changed chunks
 *
 * @module application/services
 */

import { extractChunks } from "domain/calculations/chunk-extractor";
import { detectChunkChanges } from "domain/calculations/chunk-differ";
import type { CodeChunk } from "domain/models/CodeChunk";
import type { IChunkStorage } from "application/ports/IChunkStorage";
import type { IEmbeddingService } from "application/ports/IEmbeddingService";
import { logger } from "infrastructure/cli/logger";

/**
 * Result of processing a file
 */
export interface ChunkingResult {
  chunksExtracted: number;
  chunksAdded: number;
  chunksModified: number;
  chunksDeleted: number;
  chunksUnchanged: number;
  needsReembedding: boolean;
  processingTimeMs: number;
}

/**
 * ChunkingService - Orchestrates chunking workflow
 */
export class ChunkingService {
  constructor(
    private chunkStorage: IChunkStorage,
    private embeddingService: IEmbeddingService,
  ) {}

  /**
   * Process a file: extract chunks, detect changes, update storage
   *
   * @param filePath - Absolute path to file
   * @param code - Source code content
   * @returns Chunking result with metrics
   */
  async processFile(filePath: string, code: string): Promise<ChunkingResult> {
    const startTime = Date.now();

    logger.debug("Processing file for chunking", { filePath });

    try {
      // Step 1: Extract chunks from source code
      const newChunks = extractChunks(code, filePath);
      logger.debug("Chunks extracted", {
        filePath,
        count: newChunks.length,
      });

      // Step 2: Load existing chunks from storage
      const oldChunks = await this.chunkStorage.getChunksByFilePath(filePath);
      logger.debug("Existing chunks loaded", {
        filePath,
        count: oldChunks.length,
      });

      // Step 3: Detect changes
      const changes = detectChunkChanges(oldChunks, newChunks);
      logger.debug("Changes detected", {
        filePath,
        changes: {
          added: changes.filter((c) => c.type === "added").length,
          modified: changes.filter((c) => c.type === "modified").length,
          deleted: changes.filter((c) => c.type === "deleted").length,
          unchanged: changes.filter((c) => c.type === "unchanged").length,
        },
      });

      // Step 4: Update storage
      await this.applyChanges(changes);

      // Step 5: Queue embeddings for changed chunks
      const needsReembedding = changes.some((c) => c.needsReembedding);
      if (needsReembedding) {
        await this.queueEmbeddingsForChanges(changes);
      }

      // Calculate metrics
      const result: ChunkingResult = {
        chunksExtracted: newChunks.length,
        chunksAdded: changes.filter((c) => c.type === "added").length,
        chunksModified: changes.filter((c) => c.type === "modified").length,
        chunksDeleted: changes.filter((c) => c.type === "deleted").length,
        chunksUnchanged: changes.filter((c) => c.type === "unchanged").length,
        needsReembedding,
        processingTimeMs: Date.now() - startTime,
      };

      logger.info("File processing complete", {
        filePath,
        ...result,
      });

      return result;
    } catch (error) {
      logger.error("Error processing file", {
        filePath,
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  }

  /**
   * Apply chunk changes to storage
   */
  private async applyChanges(
    changes: {
      type: "added" | "modified" | "deleted" | "unchanged";
      oldChunk?: CodeChunk;
      newChunk?: CodeChunk;
      needsReembedding: boolean;
    }[],
  ): Promise<void> {
    // Collect chunks to save (new only), update (modified), and delete
    const chunksToAdd: CodeChunk[] = [];
    const chunksToUpdate: CodeChunk[] = [];
    const chunkIdsToDelete: string[] = [];

    for (const change of changes) {
      switch (change.type) {
        case "added":
          if (change.newChunk) {
            chunksToAdd.push(change.newChunk);
          }
          break;

        case "modified":
          if (change.newChunk) {
            // For modified chunks, preserve the old chunk ID
            // This maintains embedding references
            if (change.oldChunk) {
              change.newChunk.id = change.oldChunk.id;
              change.newChunk.createdAt = change.oldChunk.createdAt;
            }
            chunksToUpdate.push(change.newChunk);
          }
          break;

        case "deleted":
          if (change.oldChunk) {
            chunkIdsToDelete.push(change.oldChunk.id);
          }
          break;

        case "unchanged":
          // No action needed
          break;
      }
    }

    // Batch save new chunks
    if (chunksToAdd.length > 0) {
      await this.chunkStorage.saveChunks(chunksToAdd);
      logger.debug("New chunks saved to storage", {
        count: chunksToAdd.length,
      });
    }

    // Update modified chunks
    for (const chunk of chunksToUpdate) {
      await this.chunkStorage.updateChunk(chunk);
    }

    if (chunksToUpdate.length > 0) {
      logger.debug("Modified chunks updated in storage", {
        count: chunksToUpdate.length,
      });
    }

    // Delete removed chunks
    for (const chunkId of chunkIdsToDelete) {
      await this.chunkStorage.deleteChunk(chunkId);
    }

    if (chunkIdsToDelete.length > 0) {
      logger.debug("Chunks deleted from storage", {
        count: chunkIdsToDelete.length,
      });
    }
  }

  /**
   * Queue embeddings for changed chunks
   */
  private async queueEmbeddingsForChanges(
    changes: {
      type: "added" | "modified" | "deleted" | "unchanged";
      oldChunk?: CodeChunk;
      newChunk?: CodeChunk;
      needsReembedding: boolean;
    }[],
  ): Promise<void> {
    const chunksNeedingEmbedding = changes
      .filter((c) => c.needsReembedding && c.newChunk)
      .map((c) => c.newChunk as CodeChunk);

    if (chunksNeedingEmbedding.length === 0) {
      return;
    }

    logger.debug("Queueing embeddings for changed chunks", {
      count: chunksNeedingEmbedding.length,
    });

    // Generate embeddings and update chunks with embeddingIds
    for (const chunk of chunksNeedingEmbedding) {
      try {
        // Generate embedding and get the embeddingId
        const embeddingId = await this.embeddingService.generateEmbedding(
          chunk.code,
          {
            chunkId: chunk.id,
            filePath: chunk.filePath,
            chunkName: chunk.name,
            chunkType: chunk.type,
          },
        );

        // Update chunk with embeddingId
        chunk.embeddingId = embeddingId;
        await this.chunkStorage.updateChunk(chunk);

        logger.debug("Embedding generated and chunk updated", {
          chunkId: chunk.id,
          embeddingId,
        });
      } catch (error) {
        // Log error but don't fail the entire operation
        logger.warn("Failed to generate embedding for chunk", {
          chunkId: chunk.id,
          chunkName: chunk.name,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }
  }

  /**
   * Get all chunks for a file
   *
   * @param filePath - Absolute path to file
   * @returns Array of chunks
   */
  async getChunksForFile(filePath: string): Promise<CodeChunk[]> {
    return this.chunkStorage.getChunksByFilePath(filePath);
  }

  /**
   * Delete all chunks for a file
   *
   * @param filePath - Absolute path to file
   */
  async deleteChunksForFile(filePath: string): Promise<void> {
    logger.debug("Deleting all chunks for file", { filePath });

    await this.chunkStorage.deleteChunksByFilePath(filePath);

    logger.info("Chunks deleted for file", { filePath });
  }

  /**
   * Get a single chunk by ID
   *
   * @param chunkId - Chunk UUID
   * @returns Chunk or null if not found
   */
  async getChunkById(chunkId: string): Promise<CodeChunk | null> {
    return this.chunkStorage.getChunkById(chunkId);
  }

  /**
   * Get all chunks across all files
   *
   * @returns Array of all chunks
   */
  async getAllChunks(): Promise<CodeChunk[]> {
    return this.chunkStorage.getAllChunks();
  }

  /**
   * Process multiple files in batch
   *
   * @param files - Array of file paths and code content
   * @returns Array of chunking results
   */
  async processFiles(
    files: { path: string; code: string }[],
  ): Promise<ChunkingResult[]> {
    logger.debug("Processing multiple files", { count: files.length });

    const results: ChunkingResult[] = [];

    for (const file of files) {
      try {
        const result = await this.processFile(file.path, file.code);
        results.push(result);
      } catch (error) {
        logger.error("Failed to process file in batch", {
          filePath: file.path,
          error: error instanceof Error ? error.message : String(error),
        });
        // Continue processing other files even if one fails
      }
    }

    logger.info("Batch processing complete", {
      total: files.length,
      successful: results.length,
      failed: files.length - results.length,
    });

    return results;
  }
}
