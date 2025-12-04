/**
 * Chunk domain model
 * Represents a semantic code chunk extracted from source files
 */

/**
 * Type of code chunk
 */
export enum ChunkType {
  FUNCTION = "function",
  CLASS = "class",
  METHOD = "method",
  FILE = "file", // Fallback for unparseable files
}

/**
 * Code chunk with metadata and boundaries
 */
export interface CodeChunk {
  // Identity
  id: string; // UUID v4
  filePath: string; // Absolute path

  // Chunk boundaries
  type: ChunkType;
  name: string; // Function/class name or <anonymous>
  startLine: number; // Start line (with context)
  endLine: number; // End line (with context)
  contentStartLine: number; // Actual code start (without context)
  contentEndLine: number; // Actual code end (without context)

  // Content
  code: string; // Source code with context envelope

  // Hierarchy
  parentChunkId?: string; // For nested functions/methods
  nestingLevel: number; // 0 = top-level, 1+ = nested
  scopePath: string[]; // ['ClassName', 'methodName', 'closureFn']

  // Metadata
  metadata: {
    signature?: string; // Function signature
    jsDoc?: string; // JSDoc comment
    isExported: boolean; // Is this exported?
    isAsync: boolean; // Async function?
    parameters?: string[]; // Parameter names
    returnType?: string; // TypeScript return type
    complexity?: number; // Cyclomatic complexity (optional)
  };

  // Embeddings reference
  embeddingId?: string; // Reference to Chroma embedding

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}
