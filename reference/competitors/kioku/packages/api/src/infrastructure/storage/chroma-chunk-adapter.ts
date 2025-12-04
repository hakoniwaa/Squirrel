/**
 * ChromaChunkAdapter - ChromaDB adapter for code chunk embeddings
 *
 * Purpose: Store and query code chunk embeddings separately from discovery embeddings
 * Collection: "code_chunks" (separate from "context-embeddings")
 *
 * @module infrastructure/storage
 */

import type { Collection, EmbeddingFunction } from "chromadb";
import { ChromaClient } from "chromadb";
import type { EmbeddingMetadata } from "application/ports/IEmbeddingService";
import { StorageError } from "@kioku/shared";
import { logger } from "../cli/logger";

/**
 * Custom embedding function for pre-computed embeddings
 * ChromaDB requires an embedding function, but we provide embeddings directly
 */
class PrecomputedEmbeddingFunction implements EmbeddingFunction {
  async generate(texts: string[]): Promise<number[][]> {
    // Return dummy embeddings - actual embeddings provided via addEmbeddings
    return texts.map(() => new Array(1536).fill(0));
  }
}

/**
 * Query result from ChromaDB
 */
export interface ChunkQueryResult {
  id: string;
  document: string;
  metadata: EmbeddingMetadata;
  distance: number;
}

/**
 * ChromaDB adapter for code chunks
 *
 * Separate collection from discovery embeddings for:
 * - Different metadata schema (chunkId, chunkName, chunkType, filePath)
 * - Different search semantics (code-level vs concept-level)
 * - Independent scaling and optimization
 */
export class ChromaChunkAdapter {
  private client: ChromaClient;
  private collection: Collection | null = null;
  private collectionName = "code_chunks";

  constructor() {
    // ChromaDB in-memory mode (for development/testing)
    // For production, connect to separate ChromaDB server
    this.client = new ChromaClient();
  }

  /**
   * Initialize code_chunks collection
   */
  async initialize(): Promise<void> {
    try {
      this.collection = await this.client.getOrCreateCollection({
        name: this.collectionName,
        metadata: {
          description: "Code chunk embeddings for precise search",
          "hnsw:space": "cosine", // Cosine similarity
          "hnsw:construction_ef": 200, // Higher = better recall, slower build
          "hnsw:search_ef": 100, // Higher = better recall, slower search
          "hnsw:M": 16, // Number of bi-directional links per node
          "hnsw:batch_size": 100,
          "hnsw:sync_threshold": 1000,
        },
        embeddingFunction: new PrecomputedEmbeddingFunction(),
      });

      logger.info("ChromaDB code_chunks collection initialized", {
        collectionName: this.collectionName,
      });
    } catch (error) {
      throw new StorageError(
        "Failed to initialize ChromaDB code_chunks collection",
        error as Error
      );
    }
  }

  /**
   * Add embeddings in batch
   *
   * @param data - Batch of embeddings with metadata
   */
  async addEmbeddings(data: {
    ids: string[];
    embeddings: number[][];
    metadatas: EmbeddingMetadata[];
    documents: string[];
  }): Promise<void> {
    if (!this.collection) {
      await this.initialize();
    }

    const { ids, embeddings, metadatas, documents } = data;

    // Validate lengths match
    if (
      ids.length !== embeddings.length ||
      ids.length !== metadatas.length ||
      ids.length !== documents.length
    ) {
      throw new StorageError(
        "Mismatched lengths: ids, embeddings, metadatas, and documents must have same length"
      );
    }

    try {
      await this.collection!.add({
        ids,
        embeddings,
        metadatas: metadatas as any, // ChromaDB typing is loose
        documents,
      });

      logger.debug("Chunk embeddings added to ChromaDB", {
        count: ids.length,
        collectionName: this.collectionName,
      });
    } catch (error) {
      throw new StorageError(
        "Failed to add chunk embeddings to ChromaDB",
        error as Error
      );
    }
  }

  /**
   * Query embeddings with optional metadata filtering
   *
   * @param queryEmbedding - Query vector
   * @param limit - Maximum results to return
   * @param filter - Metadata filters (filePath, chunkType, etc.)
   * @returns Array of matching chunks sorted by similarity
   */
  async queryEmbeddings(
    queryEmbedding: number[],
    limit: number,
    filter?: Partial<EmbeddingMetadata>
  ): Promise<ChunkQueryResult[]> {
    if (!this.collection) {
      await this.initialize();
    }

    try {
      const queryOptions: {
        queryEmbeddings: number[][];
        nResults: number;
        where?: Record<string, any>;
        include: ("documents" | "metadatas" | "distances")[];
      } = {
        queryEmbeddings: [queryEmbedding],
        nResults: limit,
        include: ["documents", "metadatas", "distances"],
      };

      // Build where clause from filter
      if (filter) {
        const where: Record<string, any> = {};
        if (filter.filePath) where.filePath = filter.filePath;
        if (filter.chunkType) where.chunkType = filter.chunkType;
        if (filter.chunkName) where.chunkName = filter.chunkName;

        if (Object.keys(where).length > 0) {
          queryOptions.where = where;
        }
      }

      const results = await this.collection!.query(queryOptions);

      // Transform results
      const queryResults: ChunkQueryResult[] = [];

      if (results.ids && results.ids[0]) {
        for (let i = 0; i < results.ids[0].length; i++) {
          queryResults.push({
            id: results.ids[0][i] as string,
            document: (results.documents?.[0]?.[i] as string) || "",
            metadata: (results.metadatas?.[0]?.[i] as any) || {},
            distance: (results.distances?.[0]?.[i] as number) || 0,
          });
        }
      }

      logger.debug("ChromaDB chunk query completed", {
        resultsCount: queryResults.length,
        filters: filter,
        collectionName: this.collectionName,
      });

      return queryResults;
    } catch (error) {
      throw new StorageError(
        "Failed to query ChromaDB code_chunks",
        error as Error
      );
    }
  }

  /**
   * Delete embedding by ID
   *
   * @param embeddingId - Chunk ID to delete
   */
  async deleteEmbedding(embeddingId: string): Promise<void> {
    if (!this.collection) {
      await this.initialize();
    }

    try {
      await this.collection!.delete({
        ids: [embeddingId],
      });

      logger.debug("Chunk embedding deleted from ChromaDB", {
        embeddingId,
        collectionName: this.collectionName,
      });
    } catch (error) {
      // Don't throw on not found - idempotent delete
      logger.debug("Delete embedding failed (may not exist)", {
        embeddingId,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  /**
   * Delete all embeddings for a file
   *
   * @param filePath - File path to delete chunks for
   */
  async deleteEmbeddingsByFilePath(filePath: string): Promise<void> {
    if (!this.collection) {
      await this.initialize();
    }

    try {
      await this.collection!.delete({
        where: { filePath },
      });

      logger.debug("File chunk embeddings deleted from ChromaDB", {
        filePath,
        collectionName: this.collectionName,
      });
    } catch (error) {
      // Don't throw on not found - idempotent delete
      logger.debug("Delete file embeddings failed (may not exist)", {
        filePath,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  /**
   * Get collection count
   *
   * @returns Number of embeddings in collection
   */
  async count(): Promise<number> {
    if (!this.collection) {
      await this.initialize();
    }

    try {
      const count = await this.collection!.count();
      return count;
    } catch (error) {
      throw new StorageError(
        "Failed to get ChromaDB collection count",
        error as Error
      );
    }
  }

  /**
   * Delete collection (for testing/cleanup)
   */
  async deleteCollection(): Promise<void> {
    try {
      await this.client.deleteCollection({ name: this.collectionName });
      this.collection = null;

      logger.debug("ChromaDB code_chunks collection deleted", {
        collectionName: this.collectionName,
      });
    } catch (error) {
      // Ignore errors if collection doesn't exist
      logger.debug("Collection deletion failed (may not exist)", {
        collectionName: this.collectionName,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }
}
