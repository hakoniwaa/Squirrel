/**
 * Chunk Differ - Delta detection for code chunks
 *
 * Purpose: Compare old and new chunks to detect changes (added, modified, deleted, unchanged)
 * Layer: Domain (Pure calculation - no I/O)
 * Used by: ChunkingService (Application layer)
 *
 * Algorithm:
 * 1. Create unique keys for chunks (filePath + type + scopePath)
 * 2. Match chunks by key
 * 3. Compare content hashes to detect modifications
 * 4. Identify added, modified, deleted, and unchanged chunks
 * 5. Mark which chunks need re-embedding
 *
 * @module domain/calculations
 */

import type { CodeChunk } from "domain/models/CodeChunk";

/**
 * Type of chunk change
 */
export type ChunkChangeType = "added" | "modified" | "deleted" | "unchanged";

/**
 * Represents a detected change in a chunk
 */
export interface ChunkChange {
  type: ChunkChangeType;
  oldChunk?: CodeChunk;
  newChunk?: CodeChunk;
  needsReembedding: boolean;
}

/**
 * Detect changes between old and new chunk arrays
 *
 * Strategy:
 * - Match chunks by unique key (name + scopePath + type)
 * - Compare content hashes to detect modifications
 * - Track which chunks need re-embedding
 *
 * @param oldChunks - Previous chunks
 * @param newChunks - Current chunks
 * @returns Array of detected changes
 */
export function detectChunkChanges(
  oldChunks: CodeChunk[],
  newChunks: CodeChunk[],
): ChunkChange[] {
  const changes: ChunkChange[] = [];

  // Create maps for efficient lookup by unique key
  const oldChunkMap = new Map<string, CodeChunk>();
  const newChunkMap = new Map<string, CodeChunk>();
  const processedKeys = new Set<string>();

  // Build old chunks map
  for (const chunk of oldChunks) {
    const key = createChunkKey(chunk);
    oldChunkMap.set(key, chunk);
  }

  // Build new chunks map
  for (const chunk of newChunks) {
    const key = createChunkKey(chunk);
    newChunkMap.set(key, chunk);
  }

  // Process all old chunks (detect deleted and modified)
  for (const [key, oldChunk] of oldChunkMap.entries()) {
    const newChunk = newChunkMap.get(key);

    if (!newChunk) {
      // Chunk was deleted
      changes.push({
        type: "deleted",
        oldChunk,
        needsReembedding: false, // Deleted chunks don't need re-embedding
      });
    } else {
      // Chunk exists in both - check if modified
      if (isChunkModified(oldChunk, newChunk)) {
        changes.push({
          type: "modified",
          oldChunk,
          newChunk,
          needsReembedding: true, // Modified chunks need re-embedding
        });
      } else {
        changes.push({
          type: "unchanged",
          oldChunk,
          newChunk,
          needsReembedding: false, // Unchanged chunks don't need re-embedding
        });
      }
    }

    processedKeys.add(key);
  }

  // Process new chunks not in old chunks (detect added)
  for (const [key, newChunk] of newChunkMap.entries()) {
    if (!processedKeys.has(key)) {
      // Chunk was added
      changes.push({
        type: "added",
        newChunk,
        needsReembedding: true, // Added chunks need re-embedding
      });
    }
  }

  return changes;
}

/**
 * Create unique key for chunk identification
 *
 * Key combines:
 * - File path (to distinguish same-named chunks in different files)
 * - Chunk type (to distinguish class User vs interface User)
 * - Chunk name (primary identifier)
 * - Scope path (to distinguish nested chunks with same name)
 *
 * Note: We include the chunk name explicitly because scopePath might not
 * always contain it (e.g., for top-level functions, scopePath is just [name])
 *
 * @param chunk - Code chunk
 * @returns Unique key string
 */
function createChunkKey(chunk: CodeChunk): string {
  // Use filePath + type + name + full scopePath for uniqueness
  // This handles cases where multiple functions have same name in same file
  // but different scope paths (e.g., nested in different classes)
  return `${chunk.filePath}::${chunk.type}::${chunk.name}::${chunk.scopePath.join("::")}`;
}

/**
 * Check if chunk was modified
 *
 * Uses content hash for fast comparison.
 * Content hash includes:
 * - Function/class code
 * - JSDoc comments
 * - Context envelope
 *
 * @param oldChunk - Previous version of chunk
 * @param newChunk - Current version of chunk
 * @returns True if chunk was modified
 */
function isChunkModified(oldChunk: CodeChunk, newChunk: CodeChunk): boolean {
  // Fast path: Compare content hashes
  // If hashes match, content is identical
  return oldChunk.contentHash !== newChunk.contentHash;
}
