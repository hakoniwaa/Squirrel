/**
 * EmbeddingService - Chunk-level embedding generation and management
 *
 * Orchestrates:
 * - OpenAI embeddings generation
 * - ChromaDB vector storage
 * - Async queue processing
 */

import type {
  IEmbeddingService,
  EmbeddingMetadata,
} from "application/ports/IEmbeddingService";
import { logger } from "../cli/logger";

/**
 * Queue item for async embedding processing
 */
interface EmbeddingQueueItem {
  content: string;
  metadata: EmbeddingMetadata;
}

/**
 * OpenAI client interface
 */
interface IOpenAIClient {
  generateEmbedding(text: string): Promise<number[]>;
  generateEmbeddings(texts: string[]): Promise<number[][]>;
}

/**
 * ChromaDB adapter interface
 */
interface IChromaAdapter {
  addEmbeddings(data: {
    ids: string[];
    embeddings: number[][];
    metadatas: EmbeddingMetadata[];
    documents: string[];
  }): Promise<void>;
  deleteEmbedding(id: string): Promise<void>;
  queryEmbeddings(
    query: number[],
    limit: number,
    filter?: Record<string, string>
  ): Promise<{ id: string; distance: number; metadata: EmbeddingMetadata }[]>;
}

/**
 * EmbeddingService configuration
 */
interface EmbeddingServiceConfig {
  batchSize?: number;
  autoProcessThreshold?: number;
}

/**
 * EmbeddingService implementation
 *
 * Implements IEmbeddingService port for chunk-level embeddings.
 */
export class EmbeddingService implements IEmbeddingService {
  private openAIClient: IOpenAIClient;
  private chromaAdapter: IChromaAdapter;
  private queue: EmbeddingQueueItem[] = [];
  private batchSize: number;
  private autoProcessThreshold: number;
  private isProcessing = false;

  constructor(
    openAIClient: IOpenAIClient,
    chromaAdapter: IChromaAdapter,
    config: EmbeddingServiceConfig = {}
  ) {
    this.openAIClient = openAIClient;
    this.chromaAdapter = chromaAdapter;
    this.batchSize = config.batchSize ?? 100;
    this.autoProcessThreshold = config.autoProcessThreshold ?? this.batchSize;

    logger.debug("EmbeddingService initialized", {
      batchSize: this.batchSize,
      autoProcessThreshold: this.autoProcessThreshold,
    });
  }

  /**
   * Generate embedding for single chunk
   */
  async generateEmbedding(
    content: string,
    metadata: EmbeddingMetadata
  ): Promise<string> {
    if (!content || content.trim().length === 0) {
      throw new Error("Content cannot be empty");
    }

    logger.debug("Generating single embedding", {
      chunkId: metadata.chunkId,
      chunkName: metadata.chunkName,
      contentLength: content.length,
    });

    try {
      // Generate embedding vector
      const vector = await this.openAIClient.generateEmbedding(content);

      // Store in vector DB
      await this.chromaAdapter.addEmbeddings({
        ids: [metadata.chunkId],
        embeddings: [vector],
        metadatas: [metadata],
        documents: [content],
      });

      logger.info("Embedding generated and stored", {
        chunkId: metadata.chunkId,
        chunkName: metadata.chunkName,
        vectorDimensions: vector.length,
      });

      return metadata.chunkId;
    } catch (error) {
      logger.error("Failed to generate embedding", {
        chunkId: metadata.chunkId,
        error: error instanceof Error ? error.message : "Unknown error",
      });
      throw error;
    }
  }

  /**
   * Generate embeddings for multiple chunks (batch)
   */
  async generateEmbeddings(
    items: { content: string; metadata: EmbeddingMetadata }[]
  ): Promise<string[]> {
    if (items.length === 0) {
      return [];
    }

    logger.debug("Generating batch embeddings", { count: items.length });

    try {
      // Extract content and metadata
      const contents = items.map((item) => item.content);
      const metadatas = items.map((item) => item.metadata);
      const ids = metadatas.map((m) => m.chunkId);

      // Generate all embeddings in batch
      const vectors = await this.openAIClient.generateEmbeddings(contents);

      // Store all in vector DB
      await this.chromaAdapter.addEmbeddings({
        ids,
        embeddings: vectors,
        metadatas,
        documents: contents,
      });

      logger.info("Batch embeddings generated and stored", {
        count: items.length,
        chunkIds: ids,
      });

      return ids;
    } catch (error) {
      logger.error("Failed to generate batch embeddings", {
        count: items.length,
        error: error instanceof Error ? error.message : "Unknown error",
      });
      throw error;
    }
  }

  /**
   * Queue embedding for async processing
   */
  async queueEmbedding(
    content: string,
    metadata: EmbeddingMetadata
  ): Promise<void> {
    this.queue.push({ content, metadata });

    logger.debug("Embedding queued", {
      chunkId: metadata.chunkId,
      queueSize: this.queue.length,
    });

    // Auto-process if threshold reached
    if (this.queue.length >= this.autoProcessThreshold && !this.isProcessing) {
      // Process in background without blocking
      this.processQueue().catch((error) => {
        logger.error("Auto-process queue failed", {
          error: error instanceof Error ? error.message : "Unknown error",
        });
      });
    }
  }

  /**
   * Process all queued embeddings
   */
  async processQueue(): Promise<void> {
    if (this.isProcessing) {
      logger.warn("Queue processing already in progress");
      return;
    }

    if (this.queue.length === 0) {
      logger.debug("Queue is empty, nothing to process");
      return;
    }

    this.isProcessing = true;

    try {
      const itemsToProcess = [...this.queue];
      this.queue = []; // Clear queue

      logger.info("Processing embedding queue", {
        count: itemsToProcess.length,
      });

      // Process in batches
      for (let i = 0; i < itemsToProcess.length; i += this.batchSize) {
        const batch = itemsToProcess.slice(i, i + this.batchSize);
        await this.generateEmbeddings(batch);
      }

      logger.info("Queue processing complete", {
        processed: itemsToProcess.length,
      });
    } catch (error) {
      logger.error("Queue processing failed", {
        error: error instanceof Error ? error.message : "Unknown error",
      });
      throw error;
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Delete embedding by ID
   */
  async deleteEmbedding(embeddingId: string): Promise<void> {
    logger.debug("Deleting embedding", { embeddingId });

    try {
      await this.chromaAdapter.deleteEmbedding(embeddingId);

      logger.info("Embedding deleted", { embeddingId });
    } catch (error) {
      logger.error("Failed to delete embedding", {
        embeddingId,
        error: error instanceof Error ? error.message : "Unknown error",
      });
      throw error;
    }
  }

  /**
   * Get current queue size (for testing/monitoring)
   */
  getQueueSize(): number {
    return this.queue.length;
  }
}
