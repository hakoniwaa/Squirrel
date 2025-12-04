/**
 * IEmbeddingService - Port for embedding generation
 * Defines the interface for generating and managing embeddings
 */

/**
 * Metadata for embedding generation
 */
export interface EmbeddingMetadata {
  chunkId: string;
  filePath: string;
  chunkName: string;
  chunkType: string;
  [key: string]: string;
}

/**
 * Interface for embedding service operations
 */
export interface IEmbeddingService {
  /**
   * Generate embedding for text content
   *
   * @param content - Text content to embed
   * @param metadata - Metadata for the embedding
   * @returns Embedding ID
   */
  generateEmbedding(
    content: string,
    metadata: EmbeddingMetadata,
  ): Promise<string>;

  /**
   * Generate embeddings for multiple content items (batch)
   *
   * @param items - Array of content and metadata pairs
   * @returns Array of embedding IDs
   */
  generateEmbeddings(
    items: { content: string; metadata: EmbeddingMetadata }[],
  ): Promise<string[]>;

  /**
   * Queue an embedding for async generation
   *
   * @param content - Text content to embed
   * @param metadata - Metadata for the embedding
   */
  queueEmbedding(content: string, metadata: EmbeddingMetadata): Promise<void>;

  /**
   * Delete an embedding by ID
   *
   * @param embeddingId - ID of embedding to delete
   */
  deleteEmbedding(embeddingId: string): Promise<void>;
}
