/**
 * SearchCodeChunks Use Case
 *
 * Semantic search over code chunks using embeddings.
 * Returns function/class-level results instead of file-level.
 *
 * @module application/use-cases
 */

import { logger } from "infrastructure/cli/logger";
import type { CodeChunk } from "domain/models/CodeChunk";

/**
 * OpenAI client interface for generating query embeddings
 */
export interface IOpenAIClient {
  generateEmbedding(text: string): Promise<number[]>;
}

/**
 * ChromaDB adapter interface for querying chunk embeddings
 */
export interface IChromaChunkAdapter {
  queryEmbeddings(
    queryEmbedding: number[],
    limit: number,
    filter?: { filePath?: string; chunkType?: string; chunkName?: string },
  ): Promise<
    {
      id: string;
      document: string;
      metadata: {
        chunkId: string;
        filePath: string;
        chunkName: string;
        chunkType: string;
      };
      distance: number;
    }[]
  >;
}

/**
 * Chunk storage interface for retrieving full chunk details
 */
export interface IChunkStorage {
  getChunkById(chunkId: string): Promise<CodeChunk | null>;
}

/**
 * Search result with chunk details
 */
export interface CodeChunkSearchResult {
  chunk: CodeChunk;
  relevanceScore: number; // 1.0 = perfect match, 0.0 = no match
  snippet: string; // Code snippet with context
}

/**
 * Search options
 */
export interface SearchCodeChunksOptions {
  query: string;
  limit?: number;
  filePath?: string; // Filter by file
  chunkType?: "function" | "class" | "method" | "interface" | "type" | "enum"; // Filter by type
}

/**
 * SearchCodeChunks use case
 *
 * Performs semantic search over code chunks using vector embeddings.
 */
export class SearchCodeChunks {
  constructor(
    private openAIClient: IOpenAIClient,
    private chromaAdapter: IChromaChunkAdapter,
    private chunkStorage: IChunkStorage,
  ) {}

  /**
   * Execute semantic search over code chunks
   *
   * @param options - Search options
   * @returns Array of matching chunks with relevance scores
   */
  async execute(
    options: SearchCodeChunksOptions,
  ): Promise<CodeChunkSearchResult[]> {
    const { query, limit = 5, filePath, chunkType } = options;

    logger.info("Searching code chunks", {
      query,
      limit,
      filePath,
      chunkType,
    });

    try {
      // Step 1: Generate query embedding
      const queryEmbedding = await this.openAIClient.generateEmbedding(query);

      logger.debug("Query embedding generated", {
        dimensions: queryEmbedding.length,
      });

      // Step 2: Query ChromaDB for similar chunks
      const filter: { filePath?: string; chunkType?: string } = {};
      if (filePath) filter.filePath = filePath;
      if (chunkType) filter.chunkType = chunkType;

      const chromaResults = await this.chromaAdapter.queryEmbeddings(
        queryEmbedding,
        limit,
        filter,
      );

      logger.debug("ChromaDB query completed", {
        resultsCount: chromaResults.length,
      });

      // Step 3: Retrieve full chunk details from storage
      const results: CodeChunkSearchResult[] = [];

      for (const chromaResult of chromaResults) {
        const chunk = await this.chunkStorage.getChunkById(
          chromaResult.metadata.chunkId,
        );

        if (!chunk) {
          logger.warn("Chunk not found in storage", {
            chunkId: chromaResult.metadata.chunkId,
          });
          continue;
        }

        // Convert distance to relevance score (lower distance = higher relevance)
        // Assuming cosine distance: 0 = identical, 2 = opposite
        const relevanceScore = Math.max(0, 1 - chromaResult.distance / 2);

        // Create snippet with limited lines
        const snippet = this.createSnippet(chunk.code, 10);

        results.push({
          chunk,
          relevanceScore,
          snippet,
        });
      }

      logger.info("Code chunk search completed", {
        query,
        resultsCount: results.length,
      });

      return results;
    } catch (error) {
      logger.error("Code chunk search failed", {
        query,
        error: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
  }

  /**
   * Create a code snippet with limited lines
   *
   * @param code - Full code
   * @param maxLines - Maximum lines to include
   * @returns Truncated snippet
   */
  private createSnippet(code: string, maxLines: number): string {
    const lines = code.split("\n");

    if (lines.length <= maxLines) {
      return code;
    }

    const snippet = lines.slice(0, maxLines).join("\n");
    return `${snippet}\n... (${lines.length - maxLines} more lines)`;
  }
}
