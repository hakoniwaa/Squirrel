/**
 * EmbeddingService - Manages embeddings for code chunks
 * Application layer service that interfaces with ChromaDB
 */

import type {
  IEmbeddingService,
  EmbeddingMetadata,
} from "application/ports/IEmbeddingService";
import { logger } from "infrastructure/cli/logger";
import { v4 as uuidv4 } from "uuid";

/**
 * Mock implementation for testing
 * TODO: Replace with real ChromaDB integration in production
 */
export class EmbeddingService implements IEmbeddingService {
  private embeddings: Map<
    string,
    { content: string; metadata: EmbeddingMetadata }
  >;

  constructor() {
    this.embeddings = new Map();
  }

  /**
   * Generate embedding for content
   */
  async generateEmbedding(
    content: string,
    metadata: EmbeddingMetadata,
  ): Promise<string> {
    logger.debug("EmbeddingService.generateEmbedding", {
      chunkId: metadata.chunkId,
      contentLength: content.length,
    });

    try {
      // Generate unique embedding ID
      const embeddingId = uuidv4();

      // Store embedding (mock implementation)
      this.embeddings.set(embeddingId, { content, metadata });

      logger.debug("Embedding generated", {
        embeddingId,
        chunkId: metadata.chunkId,
      });

      return embeddingId;
    } catch (error) {
      logger.error("Failed to generate embedding", {
        error: error instanceof Error ? error.message : String(error),
        chunkId: metadata.chunkId,
      });
      throw error;
    }
  }

  /**
   * Generate embeddings for multiple content items (batch)
   */
  async generateEmbeddings(
    items: { content: string; metadata: EmbeddingMetadata }[],
  ): Promise<string[]> {
    logger.debug("EmbeddingService.generateEmbeddings", {
      count: items.length,
    });

    try {
      const embeddingIds: string[] = [];

      for (const item of items) {
        const embeddingId = await this.generateEmbedding(
          item.content,
          item.metadata,
        );
        embeddingIds.push(embeddingId);
      }

      logger.debug("Batch embeddings generated", {
        count: embeddingIds.length,
      });

      return embeddingIds;
    } catch (error) {
      logger.error("Failed to generate batch embeddings", {
        error: error instanceof Error ? error.message : String(error),
        count: items.length,
      });
      throw error;
    }
  }

  /**
   * Queue an embedding for async generation
   */
  async queueEmbedding(
    content: string,
    metadata: EmbeddingMetadata,
  ): Promise<void> {
    logger.debug("EmbeddingService.queueEmbedding", {
      chunkId: metadata.chunkId,
      contentLength: content.length,
    });

    try {
      // For mock implementation, generate immediately
      // In production, this would add to a queue
      await this.generateEmbedding(content, metadata);

      logger.debug("Embedding queued", {
        chunkId: metadata.chunkId,
      });
    } catch (error) {
      logger.error("Failed to queue embedding", {
        error: error instanceof Error ? error.message : String(error),
        chunkId: metadata.chunkId,
      });
      throw error;
    }
  }

  /**
   * Delete an embedding
   */
  async deleteEmbedding(embeddingId: string): Promise<void> {
    logger.debug("EmbeddingService.deleteEmbedding", { embeddingId });

    try {
      this.embeddings.delete(embeddingId);

      logger.debug("Embedding deleted", { embeddingId });
    } catch (error) {
      logger.error("Failed to delete embedding", {
        error: error instanceof Error ? error.message : String(error),
        embeddingId,
      });
      throw error;
    }
  }

  /**
   * Get embedding by ID (for testing)
   */
  getEmbedding(
    embeddingId: string,
  ): { content: string; metadata: EmbeddingMetadata } | undefined {
    return this.embeddings.get(embeddingId);
  }

  /**
   * Clear all embeddings (for testing)
   */
  clear(): void {
    this.embeddings.clear();
  }
}
