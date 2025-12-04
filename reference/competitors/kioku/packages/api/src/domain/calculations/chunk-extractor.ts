/**
 * Chunk Extractor - AST-based code chunking
 *
 * Purpose: Extract functions, classes, methods, interfaces from TypeScript/JavaScript code
 * Layer: Domain (Pure calculation - no I/O)
 * Used by: ChunkingService (Application layer)
 *
 * Algorithm:
 * 1. Parse code with @babel/parser (TypeScript support)
 * 2. Traverse AST with @babel/traverse
 * 3. Extract chunks (functions, classes, methods, interfaces, types)
 * 4. Add context envelope (JSDoc + 3 lines before/after)
 * 5. Generate content hashes for change detection
 * 6. Fallback to file-level chunk on parse errors
 *
 * @module domain/calculations
 */

import { parse, type ParserPlugin } from "@babel/parser";
import traverse, { type NodePath } from "@babel/traverse";
import type {
  FunctionDeclaration,
  ClassDeclaration,
  ClassMethod,
  ArrowFunctionExpression,
  FunctionExpression,
  VariableDeclarator,
  TSInterfaceDeclaration,
  TSTypeAliasDeclaration,
  TSEnumDeclaration,
  Node,
} from "@babel/types";
import { createHash } from "crypto";
import { v4 as uuidv4 } from "uuid";
import { ChunkType, type CodeChunk } from "domain/models/CodeChunk";
import { basename } from "path";

const CONTEXT_LINES_BEFORE = 3;
const CONTEXT_LINES_AFTER = 3;
const MAX_NESTING_DEPTH = 3;

interface ChunkContext {
  filePath: string;
  sourceLines: string[];
  scopeStack: string[];
  parentChunkId?: string;
  nestingLevel: number;
}

/**
 * Extract code chunks from TypeScript/JavaScript source code
 *
 * @param code - Source code to parse
 * @param filePath - Absolute file path
 * @param options - Extraction options
 * @returns Array of code chunks
 */
export function extractChunks(
  code: string,
  filePath: string,
  options: { fallbackToFile?: boolean; maxDepth?: number } = {},
): CodeChunk[] {
  const { fallbackToFile = true, maxDepth = MAX_NESTING_DEPTH } = options;

  // Handle empty files
  if (!code || code.trim().length === 0) {
    return [createFileChunk(code, filePath)];
  }

  try {
    const sourceLines = code.split("\n");
    const ast = parseCode(code);

    const chunks: CodeChunk[] = [];
    const chunkMap = new Map<string, CodeChunk>(); // For parent lookups
    const context: ChunkContext = {
      filePath,
      sourceLines,
      scopeStack: [],
      nestingLevel: 0,
    };

    // Traverse AST and extract chunks
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    traverse(ast as any, {
      // Function declarations
      FunctionDeclaration: {
        enter(path) {
          if (context.nestingLevel <= maxDepth) {
            const chunk = extractFunctionChunk(path, context);
            if (chunk) {
              chunks.push(chunk);
              chunkMap.set(chunk.id, chunk);
              // Update context for nested functions
              context.scopeStack.push(chunk.name);
              context.parentChunkId = chunk.id;
              context.nestingLevel++;
            }
          }
        },
        exit() {
          if (context.nestingLevel > 0) {
            context.scopeStack.pop();
            context.nestingLevel--;
            // Restore parent
            if (context.scopeStack.length > 0) {
              const parentName =
                context.scopeStack[context.scopeStack.length - 1];
              const parentChunk = Array.from(chunkMap.values()).find(
                (c) => c.name === parentName,
              );
              if (parentChunk) {
                context.parentChunkId = parentChunk.id;
              } else {
                delete context.parentChunkId;
              }
            } else {
              delete context.parentChunkId;
            }
          }
        },
      },

      // Arrow functions assigned to variables
      VariableDeclarator(path) {
        const init = path.node.init;
        if (
          init &&
          (init.type === "ArrowFunctionExpression" ||
            init.type === "FunctionExpression")
        ) {
          if (context.nestingLevel <= maxDepth) {
            const chunk = extractArrowFunctionChunk(path, context);
            if (chunk) {
              chunks.push(chunk);
              chunkMap.set(chunk.id, chunk);
            }
          }
        }
      },

      // Class declarations
      ClassDeclaration: {
        enter(path) {
          if (context.nestingLevel <= maxDepth) {
            const chunk = extractClassChunk(path, context);
            if (chunk) {
              chunks.push(chunk);
              chunkMap.set(chunk.id, chunk);
              // Update context for methods
              context.scopeStack.push(chunk.name);
              context.parentChunkId = chunk.id;
              context.nestingLevel++;
            }
          }
        },
        exit() {
          if (context.nestingLevel > 0) {
            context.scopeStack.pop();
            context.nestingLevel--;
            delete context.parentChunkId;
          }
        },
      },

      // Class methods (handled separately from class)
      ClassMethod: {
        enter(path) {
          if (context.nestingLevel <= maxDepth) {
            const chunk = extractClassMethodChunk(path, context);
            if (chunk) {
              chunks.push(chunk);
              chunkMap.set(chunk.id, chunk);
              // Update context for nested functions inside methods
              context.scopeStack.push(chunk.name);
              context.parentChunkId = chunk.id;
              context.nestingLevel++;
            }
          }
        },
        exit() {
          if (context.nestingLevel > 0) {
            context.scopeStack.pop();
            context.nestingLevel--;
            // Restore parent (the class)
            if (context.scopeStack.length > 0) {
              const parentName =
                context.scopeStack[context.scopeStack.length - 1];
              const parentChunk = Array.from(chunkMap.values()).find(
                (c) => c.name === parentName,
              );
              if (parentChunk) {
                context.parentChunkId = parentChunk.id;
              } else {
                delete context.parentChunkId;
              }
            } else {
              delete context.parentChunkId;
            }
          }
        },
      },

      // TypeScript interfaces
      TSInterfaceDeclaration(path) {
        const chunk = extractInterfaceChunk(path, context);
        if (chunk) chunks.push(chunk);
      },

      // TypeScript type aliases
      TSTypeAliasDeclaration(path) {
        const chunk = extractTypeAliasChunk(path, context);
        if (chunk) chunks.push(chunk);
      },

      // TypeScript enums
      TSEnumDeclaration(path) {
        const chunk = extractEnumChunk(path, context);
        if (chunk) chunks.push(chunk);
      },
    });

    // If no chunks extracted and only comments, return file-level chunk
    if (chunks.length === 0) {
      return [createFileChunk(code, filePath)];
    }

    return chunks;
  } catch (error) {
    // Fallback to file-level chunk on parse errors
    if (fallbackToFile) {
      return [
        createFileChunk(code, filePath, {
          warning: `Parse error: ${error instanceof Error ? error.message : String(error)}`,
        }),
      ];
    }
    throw error;
  }
}

/**
 * Parse TypeScript/JavaScript code into AST
 */
function parseCode(code: string): File {
  const plugins: ParserPlugin[] = [
    "typescript",
    "jsx",
    "decorators-legacy",
    "classProperties",
    "classPrivateProperties",
    "classPrivateMethods",
    "exportDefaultFrom",
    "exportNamespaceFrom",
    "dynamicImport",
    "nullishCoalescingOperator",
    "optionalChaining",
    "objectRestSpread",
  ];

   
  return parse(code, {
    sourceType: "module",
    plugins,
    errorRecovery: true,
  }) as any;
}

/**
 * Extract function declaration chunk
 */
function extractFunctionChunk(
  path: NodePath<FunctionDeclaration>,
  context: ChunkContext,
): CodeChunk | null {
  const node = path.node;
  const name = node.id?.name || "<anonymous>";

  const { startLine, endLine, contentStartLine, contentEndLine } =
    calculateLineNumbers(node, context.sourceLines);

  const code = extractCodeWithContext(
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    context.sourceLines,
  );

  const jsDoc = extractJSDoc(node, context.sourceLines);
  const isExported = isNodeExported(path);
  const isAsync = node.async || false;

  const chunk: CodeChunk = {
    id: uuidv4(),
    filePath: context.filePath,
    type: ChunkType.FUNCTION_DECLARATION,
    name,
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    code,
    contentHash: generateHash(code),
    nestingLevel: context.nestingLevel,
    scopePath: [...context.scopeStack, name],
    metadata: buildMetadata({
      signature: extractFunctionSignature(node),
      jsDoc,
      isExported,
      isAsync,
      parameters: node.params.map((p) =>
        p.type === "Identifier" ? p.name : "...",
      ),
      returnType: extractReturnType(node),
    }),
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  if (context.parentChunkId !== undefined) {
    chunk.parentChunkId = context.parentChunkId;
  }

  return chunk;
}

/**
 * Extract arrow function chunk (from variable declaration)
 */
function extractArrowFunctionChunk(
  path: NodePath<VariableDeclarator>,
  context: ChunkContext,
): CodeChunk | null {
  const node = path.node;
  const name = node.id.type === "Identifier" ? node.id.name : "<anonymous>";
  const init = node.init as ArrowFunctionExpression | FunctionExpression;

  const { startLine, endLine, contentStartLine, contentEndLine } =
    calculateLineNumbers(node, context.sourceLines);

  const code = extractCodeWithContext(
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    context.sourceLines,
  );

  const jsDoc = extractJSDoc(node, context.sourceLines);
  const isExported = isNodeExported(path);
  const isAsync = init.async || false;

  const chunk: CodeChunk = {
    id: uuidv4(),
    filePath: context.filePath,
    type: ChunkType.ARROW_FUNCTION,
    name,
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    code,
    contentHash: generateHash(code),
    nestingLevel: context.nestingLevel,
    scopePath: [...context.scopeStack, name],
    metadata: buildMetadata({
      signature: `const ${name} = (${init.params.map((p) => (p.type === "Identifier" ? p.name : "...")).join(", ")}) => ...`,
      jsDoc,
      isExported,
      isAsync,
      parameters: init.params.map((p) =>
        p.type === "Identifier" ? p.name : "...",
      ),
    }),
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  if (context.parentChunkId !== undefined) {
    chunk.parentChunkId = context.parentChunkId;
  }

  return chunk;
}

/**
 * Extract class declaration chunk
 */
function extractClassChunk(
  path: NodePath<ClassDeclaration>,
  context: ChunkContext,
): CodeChunk | null {
  const node = path.node;
  const name = node.id?.name || "<anonymous>";

  const { startLine, endLine, contentStartLine, contentEndLine } =
    calculateLineNumbers(node, context.sourceLines);

  const code = extractCodeWithContext(
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    context.sourceLines,
  );

  const jsDoc = extractJSDoc(node, context.sourceLines);
  const isExported = isNodeExported(path);

  const chunk: CodeChunk = {
    id: uuidv4(),
    filePath: context.filePath,
    type: ChunkType.CLASS_DECLARATION,
    name,
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    code,
    contentHash: generateHash(code),
    nestingLevel: context.nestingLevel,
    scopePath: [...context.scopeStack, name],
    metadata: buildMetadata({
      signature: `class ${name}`,
      jsDoc,
      isExported,
      isAsync: false,
    }),
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  if (context.parentChunkId !== undefined) {
    chunk.parentChunkId = context.parentChunkId;
  }

  return chunk;
}

/**
 * Extract class method chunk
 */
function extractClassMethodChunk(
  path: NodePath<ClassMethod>,
  context: ChunkContext,
): CodeChunk | null {
  const node = path.node;
  const key = node.key;
  const name = key.type === "Identifier" ? key.name : "<computed>";

  // Find parent class name
  const classPath = path.findParent((p) => p.isClassDeclaration());
  const className =
    classPath && classPath.isClassDeclaration() && classPath.node.id
      ? classPath.node.id.name
      : "UnknownClass";

  const { startLine, endLine, contentStartLine, contentEndLine } =
    calculateLineNumbers(node, context.sourceLines);

  const code = extractCodeWithContext(
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    context.sourceLines,
  );

  const jsDoc = extractJSDoc(node, context.sourceLines);
  const isAsync = node.async || false;

  const chunk: CodeChunk = {
    id: uuidv4(),
    filePath: context.filePath,
    type: ChunkType.CLASS_METHOD,
    name,
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    code,
    contentHash: generateHash(code),
    nestingLevel: context.nestingLevel + 1,
    scopePath: [...context.scopeStack, className, name],
    metadata: buildMetadata({
      signature: `${node.static ? "static " : ""}${name}(${node.params.map((p) => (p.type === "Identifier" ? p.name : "...")).join(", ")})`,
      jsDoc,
      isExported: false,
      isAsync,
      parameters: node.params.map((p) =>
        p.type === "Identifier" ? p.name : "...",
      ),
    }),
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  if (context.parentChunkId !== undefined) {
    chunk.parentChunkId = context.parentChunkId;
  }

  return chunk;
}

/**
 * Extract TypeScript interface chunk
 */
function extractInterfaceChunk(
  path: NodePath<TSInterfaceDeclaration>,
  context: ChunkContext,
): CodeChunk | null {
  const node = path.node;
  const name = node.id.name;

  const { startLine, endLine, contentStartLine, contentEndLine } =
    calculateLineNumbers(node, context.sourceLines);

  const code = extractCodeWithContext(
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    context.sourceLines,
  );

  const jsDoc = extractJSDoc(node, context.sourceLines);
  const isExported = isNodeExported(path);

  const chunk: CodeChunk = {
    id: uuidv4(),
    filePath: context.filePath,
    type: ChunkType.INTERFACE,
    name,
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    code,
    contentHash: generateHash(code),
    nestingLevel: context.nestingLevel,
    scopePath: [...context.scopeStack, name],
    metadata: buildMetadata({
      signature: `interface ${name}`,
      jsDoc,
      isExported,
      isAsync: false,
    }),
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  if (context.parentChunkId !== undefined) {
    chunk.parentChunkId = context.parentChunkId;
  }

  return chunk;
}

/**
 * Extract TypeScript type alias chunk
 */
function extractTypeAliasChunk(
  path: NodePath<TSTypeAliasDeclaration>,
  context: ChunkContext,
): CodeChunk | null {
  const node = path.node;
  const name = node.id.name;

  const { startLine, endLine, contentStartLine, contentEndLine } =
    calculateLineNumbers(node, context.sourceLines);

  const code = extractCodeWithContext(
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    context.sourceLines,
  );

  const jsDoc = extractJSDoc(node, context.sourceLines);
  const isExported = isNodeExported(path);

  const chunk: CodeChunk = {
    id: uuidv4(),
    filePath: context.filePath,
    type: ChunkType.TYPE_ALIAS,
    name,
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    code,
    contentHash: generateHash(code),
    nestingLevel: context.nestingLevel,
    scopePath: [...context.scopeStack, name],
    metadata: buildMetadata({
      signature: `type ${name}`,
      jsDoc,
      isExported,
      isAsync: false,
    }),
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  if (context.parentChunkId !== undefined) {
    chunk.parentChunkId = context.parentChunkId;
  }

  return chunk;
}

/**
 * Extract TypeScript enum chunk
 */
function extractEnumChunk(
  path: NodePath<TSEnumDeclaration>,
  context: ChunkContext,
): CodeChunk | null {
  const node = path.node;
  const name = node.id.name;

  const { startLine, endLine, contentStartLine, contentEndLine } =
    calculateLineNumbers(node, context.sourceLines);

  const code = extractCodeWithContext(
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    context.sourceLines,
  );

  const jsDoc = extractJSDoc(node, context.sourceLines);
  const isExported = isNodeExported(path);

  const chunk: CodeChunk = {
    id: uuidv4(),
    filePath: context.filePath,
    type: ChunkType.TYPE_ALIAS, // Enums treated as type aliases
    name,
    startLine,
    endLine,
    contentStartLine,
    contentEndLine,
    code,
    contentHash: generateHash(code),
    nestingLevel: context.nestingLevel,
    scopePath: [...context.scopeStack, name],
    metadata: buildMetadata({
      signature: `enum ${name}`,
      jsDoc,
      isExported,
      isAsync: false,
    }),
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  if (context.parentChunkId !== undefined) {
    chunk.parentChunkId = context.parentChunkId;
  }

  return chunk;
}

/**
 * Calculate line numbers with context envelope
 */
function calculateLineNumbers(
  node: Node,
  sourceLines: string[],
): {
  startLine: number;
  endLine: number;
  contentStartLine: number;
  contentEndLine: number;
} {
  const contentStartLine = node.loc?.start.line || 1;
  const contentEndLine = node.loc?.end.line || sourceLines.length;

  const startLine = Math.max(1, contentStartLine - CONTEXT_LINES_BEFORE);
  const endLine = Math.min(
    sourceLines.length,
    contentEndLine + CONTEXT_LINES_AFTER,
  );

  return { startLine, endLine, contentStartLine, contentEndLine };
}

/**
 * Extract code with context envelope (includes JSDoc if present)
 */
function extractCodeWithContext(
  startLine: number,
  endLine: number,
  contentStartLine: number,
  _contentEndLine: number,
  sourceLines: string[],
): string {
  // Look for JSDoc comment before the content
  let actualStartLine = startLine;
  for (let i = Math.max(0, contentStartLine - 10); i < contentStartLine; i++) {
    const line = sourceLines[i]?.trim();
    if (line && line.startsWith("/**")) {
      actualStartLine = i + 1; // i is 0-indexed, line numbers are 1-indexed
      break;
    }
  }

  return sourceLines.slice(actualStartLine - 1, endLine).join("\n");
}

/**
 * Extract JSDoc comment
 */
function extractJSDoc(node: Node, sourceLines: string[]): string | undefined {
  if (!node.loc) return undefined;

  const startLine = node.loc.start.line;
  const docLines: string[] = [];

  // Look backwards for JSDoc comment
  for (let i = startLine - 2; i >= 0; i--) {
    const line = sourceLines[i]?.trim();
    if (!line) continue;

    if (line.startsWith("/**")) {
      // Found start of JSDoc
      for (let j = i; j < startLine - 1; j++) {
        docLines.push(sourceLines[j] || "");
      }
      return docLines.join("\n");
    }

    if (!line.startsWith("*") && !line.startsWith("*/")) {
      // Not part of JSDoc comment
      break;
    }
  }

  return undefined;
}

/**
 * Check if node is exported
 */
function isNodeExported(path: NodePath): boolean {
  const parent = path.parent;
  if (!parent) return false;

  return (
    parent.type === "ExportNamedDeclaration" ||
    parent.type === "ExportDefaultDeclaration"
  );
}

/**
 * Extract function signature
 */
function extractFunctionSignature(node: FunctionDeclaration): string {
  const name = node.id?.name || "<anonymous>";
  const params = node.params
    .map((p) => (p.type === "Identifier" ? p.name : "..."))
    .join(", ");
  const asyncPrefix = node.async ? "async " : "";
  const generatorPrefix = node.generator ? "*" : "";

  return `${asyncPrefix}function${generatorPrefix} ${name}(${params})`;
}

/**
 * Extract return type from TypeScript annotation
 */
function extractReturnType(_node: FunctionDeclaration): string | undefined {
  // TypeScript return type annotation would be in node.returnType
  // This is a simplified version
  return undefined;
}

/**
 * Generate SHA-256 hash of content
 */
function generateHash(content: string): string {
  return createHash("sha256").update(content).digest("hex");
}

/**
 * Build metadata object with only defined properties
 * This avoids TypeScript exactOptionalPropertyTypes issues
 */
function buildMetadata(data: {
  signature?: string | undefined;
  jsDoc?: string | undefined;
  isExported: boolean;
  isAsync: boolean;
  parameters?: string[] | undefined;
  returnType?: string | undefined;
}): CodeChunk["metadata"] {
  const metadata: CodeChunk["metadata"] = {
    isExported: data.isExported,
    isAsync: data.isAsync,
  };

  if (data.signature !== undefined) metadata.signature = data.signature;
  if (data.jsDoc !== undefined) metadata.jsDoc = data.jsDoc;
  if (data.parameters !== undefined && data.parameters.length > 0)
    metadata.parameters = data.parameters;
  if (data.returnType !== undefined) metadata.returnType = data.returnType;

  return metadata;
}

/**
 * Create file-level fallback chunk
 */
function createFileChunk(
  code: string,
  filePath: string,
  extraMetadata: Record<string, string | number | boolean> = {},
): CodeChunk {
  const fileName = basename(filePath);
  const lines = code.split("\n");

  return {
    id: uuidv4(),
    filePath,
    type: ChunkType.EXPORTED_DECLARATION, // File-level treated as export
    name: fileName,
    startLine: 1,
    endLine: lines.length,
    contentStartLine: 1,
    contentEndLine: lines.length,
    code,
    contentHash: generateHash(code),
    nestingLevel: 0,
    scopePath: [fileName],
    metadata: {
      ...extraMetadata,
      isExported: false,
      isAsync: false,
    },
    createdAt: new Date(),
    updatedAt: new Date(),
  };
}
