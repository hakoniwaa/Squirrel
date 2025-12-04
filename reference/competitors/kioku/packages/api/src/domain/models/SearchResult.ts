/**
 * SearchResult - Enhanced search result with ranking metadata
 *
 * Purpose: Represent search results with intelligent ranking boosts.
 * Used by: Search and Ranking features (User Stories 2, 5)
 *
 * @module domain/models
 */

export interface SearchResult {
  // Identity
  id: string; // Chunk ID or file ID
  type: "chunk" | "file";

  // Content
  filePath: string;
  content: string; // Chunk content or file excerpt

  // Location (for chunks)
  chunkName?: string; // Function/class name
  startLine?: number;
  endLine?: number;

  // Scoring
  score: number; // Base semantic similarity score (0-1)
  recencyBoost?: number; // 1.0, 1.2, or 1.5 (added by ranking)
  moduleBoost?: number; // 1.0 or 1.3 (added by ranking)
  frequencyBoost?: number; // 1.0 to 1.5 (added by ranking)
  finalScore?: number; // Combined score (added by ranking)

  // Metadata
  module?: string; // Module name (e.g., "auth", "payment")
  projectName?: string; // For multi-project search
  lastAccessed: Date; // Last access timestamp
  accessCount: number; // Number of times accessed
  metadata: Record<string, string | number | boolean>; // Additional metadata

  // Context
  surroundingContext?: string; // 3 lines before/after
}
