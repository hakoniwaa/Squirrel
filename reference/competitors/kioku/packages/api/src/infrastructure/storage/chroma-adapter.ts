import type { Collection, EmbeddingFunction } from "chromadb";
import { ChromaClient } from "chromadb";
import type { Discovery } from "domain/models/Discovery";
import { StorageError } from "@kioku/shared";
import { logger } from "../cli/logger";

// Custom embedding function that accepts pre-computed embeddings
class CustomEmbeddingFunction implements EmbeddingFunction {
  async generate(texts: string[]): Promise<number[][]> {
    // Return dummy embeddings - actual embeddings will be provided via addEmbeddings
    return texts.map(() => new Array(1536).fill(0));
  }
}

export interface SearchResult {
  id: string;
  content: string;
  metadata: {
    type: string;
    module?: string;
    session: string;
    project: string;
    date: string;
  };
  distance: number;
}

export class ChromaAdapter {
  private client: ChromaClient;
  private collection: Collection | null = null;
  private collectionName = "context-embeddings";

  constructor(_chromaPath?: string) {
    // ChromaClient in memory mode by default (no path parameter needed)
    // For persistent storage, would need to run chroma server separately
    this.client = new ChromaClient();
  }

  /**
   * Initialize or get existing collection
   */
  async initializeCollection(): Promise<void> {
    try {
      this.collection = await this.client.getOrCreateCollection({
        name: this.collectionName,
        metadata: {
          description: "Project context embeddings",
          "hnsw:space": "cosine",
          "hnsw:construction_ef": 200,
          "hnsw:search_ef": 100,
          "hnsw:M": 16,
          "hnsw:batch_size": 100,
          "hnsw:sync_threshold": 1000,
        },
        // Use custom embeddings (OpenAI), not default
        embeddingFunction: new CustomEmbeddingFunction(),
      });

      logger.info("Chroma collection initialized", {
        collectionName: this.collectionName,
      });
    } catch (error) {
      throw new StorageError(
        "Failed to initialize Chroma collection",
        error as Error,
      );
    }
  }

  /**
   * Add embeddings in batch
   */
  async addEmbeddings(
    discoveries: Discovery[],
    embeddings: number[][],
    projectName: string,
  ): Promise<void> {
    if (!this.collection) {
      await this.initializeCollection();
    }

    if (discoveries.length !== embeddings.length) {
      throw new StorageError("Discoveries and embeddings length mismatch");
    }

    try {
      const ids = discoveries.map((d) => d.embedding?.id || d.id);
      const documents = discoveries.map((d) => d.content);
      const metadatas = discoveries.map((d) => ({
        type: d.type,
        module: d.module || "",
        session: d.sessionId,
        project: projectName,
        date: d.createdAt.toISOString(),
      }));

      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      await this.collection!.add({
        ids,
        embeddings,
        documents,
        metadatas,
      });

      logger.debug("Embeddings added to Chroma", { count: discoveries.length });
    } catch (error) {
      throw new StorageError("Failed to add embeddings", error as Error);
    }
  }

  /**
   * Search with metadata filtering
   */
  async search(
    queryEmbedding: number[],
    options: {
      nResults?: number;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      where?: Record<string, any>;
    } = {},
  ): Promise<SearchResult[]> {
    if (!this.collection) {
      await this.initializeCollection();
    }

    try {
      const queryOptions: {
        queryEmbeddings: number[][];
        nResults: number;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        where?: Record<string, any>;
        include: ("documents" | "metadatas" | "distances")[];
      } = {
        queryEmbeddings: [queryEmbedding],
        nResults: options.nResults || 5,
        include: ["documents", "metadatas", "distances"],
      };

      if (options.where) {
        queryOptions.where = options.where;
      }

      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const results = await this.collection!.query(queryOptions);

      // Transform results
      const searchResults: SearchResult[] = [];

      if (results.ids && results.ids[0]) {
        for (let i = 0; i < results.ids[0].length; i++) {
          searchResults.push({
            id: results.ids[0][i] as string,
            content: (results.documents?.[0]?.[i] as string) || "",
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            metadata: (results.metadatas?.[0]?.[i] as any) || {},
            distance: (results.distances?.[0]?.[i] as number) || 0,
          });
        }
      }

      logger.debug("Chroma search completed", {
        resultsCount: searchResults.length,
        filters: options.where,
      });

      return searchResults;
    } catch (error) {
      throw new StorageError("Failed to search Chroma", error as Error);
    }
  }

  /**
   * Get collection count
   */
  async count(): Promise<number> {
    if (!this.collection) {
      await this.initializeCollection();
    }

    try {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const count = await this.collection!.count();
      return count;
    } catch (error) {
      throw new StorageError("Failed to get collection count", error as Error);
    }
  }

  /**
   * Delete collection (for testing)
   */
  async deleteCollection(): Promise<void> {
    try {
      await this.client.deleteCollection({ name: this.collectionName });
      this.collection = null;
      logger.debug("Chroma collection deleted", {
        collectionName: this.collectionName,
      });
    } catch (error) {
      // Ignore errors if collection doesn't exist
      logger.debug("Collection deletion failed (may not exist)", { error });
    }
  }
}
