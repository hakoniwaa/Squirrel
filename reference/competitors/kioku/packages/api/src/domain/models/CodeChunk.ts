/**
 * CodeChunk - Represents a discrete unit of code (function, class, method)
 *
 * Purpose: Enable function/class-level search instead of file-level search.
 * Used by: Smart Chunking feature (User Story 2)
 *
 * @module domain/models
 */

export enum ChunkType {
  FUNCTION_DECLARATION = "function",
  FUNCTION_EXPRESSION = "function_expr",
  ARROW_FUNCTION = "arrow_function",
  CLASS_DECLARATION = "class",
  CLASS_METHOD = "method",
  OBJECT_METHOD = "object_method",
  INTERFACE = "interface",
  TYPE_ALIAS = "type",
  EXPORTED_DECLARATION = "export",
}

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
  contentHash: string; // SHA-256 hash of code (for change detection)

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
