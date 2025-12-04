/**
 * IChunkStorage - Port for chunk persistence
 * Defines the interface for storing and retrieving code chunks
 */

import type { CodeChunk } from "domain/models/CodeChunk";

/**
 * Interface for chunk storage operations
 */
export interface IChunkStorage {
  /**
   * Save a single chunk
   */
  saveChunk(chunk: CodeChunk): Promise<void>;

  /**
   * Save multiple chunks
   */
  saveChunks(chunks: CodeChunk[]): Promise<void>;

  /**
   * Get all chunks for a specific file
   */
  getChunksByFilePath(filePath: string): Promise<CodeChunk[]>;

  /**
   * Get a chunk by ID
   */
  getChunkById(chunkId: string): Promise<CodeChunk | null>;

  /**
   * Delete a chunk by ID
   */
  deleteChunk(chunkId: string): Promise<void>;

  /**
   * Delete all chunks for a specific file
   */
  deleteChunksByFilePath(filePath: string): Promise<void>;

  /**
   * Update an existing chunk
   */
  updateChunk(chunk: CodeChunk): Promise<void>;

  /**
   * Get all chunks
   */
  getAllChunks(): Promise<CodeChunk[]>;
}
