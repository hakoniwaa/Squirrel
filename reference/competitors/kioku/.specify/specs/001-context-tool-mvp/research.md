# Research: Context Tool MVP Technologies

**Date**: 2025-01-15  
**Purpose**: Technical research for implementation planning  
**Status**: Complete

---

## Overview

This document contains research findings and best practices for the key technologies used in the Context Tool MVP. All decisions align with the project constitution's principles of simplicity, transparency, and functional programming.

---

## 1. MCP SDK (@modelcontextprotocol/sdk)

### Decision
Use official TypeScript SDK v1.19.1+ with `StdioServerTransport` for stdio-based MCP server.

### Rationale
- Official SDK from Anthropic with full TypeScript support
- StdioServerTransport is the standard for local MCP servers
- Integrates seamlessly with Claude Desktop
- Well-documented patterns for resources and tools

### Best Practices

#### Server Initialization
```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

const server = new Server(
  {
    name: 'context-tool',
    version: '1.0.0',
  },
  {
    capabilities: {
      resources: {},
      tools: {},
    },
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

#### Resource Registration
```typescript
// Static resource
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: 'context://project/overview',
        name: 'Project Overview',
        mimeType: 'text/markdown',
        description: 'High-level project context',
      },
    ],
  };
});

// Dynamic resource with URI template
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = new URL(request.params.uri);
  
  if (uri.pathname === '/project/overview') {
    const content = await loadProjectOverview();
    return {
      contents: [{
        uri: request.params.uri,
        mimeType: 'text/markdown',
        text: content,
      }],
    };
  }
  
  throw new Error(`Unknown resource: ${request.params.uri}`);
});
```

#### Tool Registration with Zod
```typescript
import { z } from 'zod';

const ContextSearchSchema = z.object({
  query: z.string().describe('Search query'),
  type: z.enum(['all', 'discovery', 'session', 'code']).optional(),
  limit: z.number().min(1).max(20).default(5),
});

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'context_search',
        description: 'Search project context semantically',
        inputSchema: zodToJsonSchema(ContextSearchSchema),
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'context_search') {
    const args = ContextSearchSchema.parse(request.params.arguments);
    const results = await searchContext(args.query, args.type, args.limit);
    
    return {
      content: [{ type: 'text', text: JSON.stringify(results, null, 2) }],
    };
  }
  
  throw new Error(`Unknown tool: ${request.params.name}`);
});
```

#### Error Handling
```typescript
import { McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';

// Protocol-level errors (connection issues, invalid requests)
throw new McpError(
  ErrorCode.InvalidRequest,
  'Resource URI must start with context://'
);

// Tool errors (return in result, not throw)
return {
  content: [{
    type: 'text',
    text: JSON.stringify({
      error: 'File not found',
      path: args.path,
    }),
  }],
  isError: true,
};
```

#### Lifecycle Management
```typescript
const abortController = new AbortController();

process.on('SIGINT', async () => {
  abortController.abort();
  await server.close();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  abortController.abort();
  await server.close();
  process.exit(0);
});
```

### Key Takeaways
- Use Zod for input validation (type-safe + JSON schema generation)
- Return tool errors in results, not as protocol errors
- Implement graceful shutdown with AbortController
- Log all MCP operations for transparency

---

## 2. ChromaDB with TypeScript/Bun

### Decision
Use `chromadb` npm package (v3.0.17+) in persistent mode with local file storage.

### Rationale
- Full TypeScript support, works perfectly with Bun
- Local-first architecture (no server needed)
- Powerful metadata filtering
- Excellent batch operations support

### Best Practices

#### Client Setup
```typescript
import { ChromaClient } from 'chromadb';

const client = new ChromaClient({
  path: '/path/to/.context/chroma',
});

// Get or create collection
const collection = await client.getOrCreateCollection({
  name: 'context-embeddings',
  metadata: { 
    description: 'Project context embeddings',
    'hnsw:space': 'cosine',  // cosine similarity
  },
});
```

#### Batch Embedding Insertion
```typescript
import { create_batches } from 'chromadb';

// Batch insertions (100-200 items optimal)
const discoveries = [...]; // Array of discoveries
const batches = create_batches(
  discoveries.map(d => d.id),
  discoveries.map(d => d.embedding),
  discoveries.map(d => ({
    type: d.type,
    module: d.module,
    session: d.sessionId,
    date: d.createdAt.toISOString(),
  })),
  discoveries.map(d => d.content),
);

for (const batch of batches) {
  await collection.add({
    ids: batch.ids,
    embeddings: batch.embeddings,
    metadatas: batch.metadatas,
    documents: batch.documents,
  });
}
```

#### Semantic Search with Metadata Filtering
```typescript
// Query with metadata filters
const results = await collection.query({
  queryEmbeddings: [queryEmbedding],
  nResults: 5,
  where: {
    $and: [
      { type: { $eq: 'discovery' } },
      { module: { $eq: 'auth' } },
    ],
  },
  include: ['documents', 'metadatas', 'distances'],
});

// Available operators: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $and, $or, $not
```

#### Collection Management
```typescript
// List all collections
const collections = await client.listCollections();

// Delete collection
await client.deleteCollection({ name: 'old-collection' });

// Modify collection metadata
await collection.modify({
  name: 'new-name',
  metadata: { updated: new Date().toISOString() },
});

// Count items
const count = await collection.count();
```

#### Performance Configuration
```typescript
// HNSW index parameters (set at collection creation)
const collection = await client.createCollection({
  name: 'embeddings',
  metadata: {
    'hnsw:space': 'cosine',        // cosine, l2, or ip
    'hnsw:construction_ef': 200,    // higher = better quality, slower build
    'hnsw:search_ef': 100,          // higher = better recall, slower search
    'hnsw:M': 16,                   // higher = better recall, more memory
    'hnsw:batch_size': 100,         // batch size for index updates
    'hnsw:sync_threshold': 1000,    // sync to disk every N operations
  },
});
```

### Key Takeaways
- Use batch operations (100-200 items) for performance
- Configure HNSW parameters for quality/speed tradeoff
- Metadata filtering before vector search (pre-filtering)
- Persistent local storage aligns with local-first principle
- Cosine similarity for text embeddings

---

## 3. Bun SQLite (bun:sqlite)

### Decision
Use Bun's built-in `bun:sqlite` module instead of better-sqlite3.

### Rationale
- **Native to Bun**: Zero npm dependencies
- **3-6x faster** than better-sqlite3
- **Perfect API compatibility** with better-sqlite3
- **Built-in optimizations**: WAL mode, prepared statements
- **Local-first**: File-based database aligns with constitution

### Critical Configuration

#### Database Initialization
```typescript
import { Database } from 'bun:sqlite';

const db = new Database('/path/to/.context/sessions.db', {
  create: true,
  readwrite: true,
});

// Enable WAL mode (10-100x faster concurrency)
db.run('PRAGMA journal_mode = WAL;');
db.run('PRAGMA synchronous = NORMAL;');
db.run('PRAGMA cache_size = -64000;');  // 64MB cache
db.run('PRAGMA temp_store = MEMORY;');
db.run('PRAGMA mmap_size = 30000000000;');
db.run('PRAGMA page_size = 4096;');
```

#### Schema Design
```typescript
// Sessions table
db.run(`
  CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    started_at INTEGER NOT NULL,
    ended_at INTEGER,
    status TEXT CHECK(status IN ('active', 'completed', 'archived')),
    files_accessed TEXT,  -- JSON array
    topics TEXT,          -- JSON array
    metadata TEXT,        -- JSON object
    created_at INTEGER DEFAULT (unixepoch()),
    updated_at INTEGER DEFAULT (unixepoch())
  )
`);

// Discoveries table
db.run(`
  CREATE TABLE IF NOT EXISTS discoveries (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    type TEXT CHECK(type IN ('pattern', 'rule', 'decision', 'issue')),
    content TEXT NOT NULL,
    module TEXT,
    embedding_id TEXT,
    created_at INTEGER DEFAULT (unixepoch()),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
  )
`);

// Indexes for common queries
db.run('CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id)');
db.run('CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)');
db.run('CREATE INDEX IF NOT EXISTS idx_discoveries_session ON discoveries(session_id)');
db.run('CREATE INDEX IF NOT EXISTS idx_discoveries_type ON discoveries(type)');
```

#### Transactions (100x faster for bulk operations)
```typescript
// Wrap bulk inserts in transaction
const insertDiscoveries = db.transaction((discoveries) => {
  const stmt = db.prepare(`
    INSERT INTO discoveries (id, session_id, type, content, module)
    VALUES (?, ?, ?, ?, ?)
  `);
  
  for (const d of discoveries) {
    stmt.run(d.id, d.sessionId, d.type, d.content, d.module);
  }
});

// Execute transaction
insertDiscoveries(discoveryArray);
```

#### Prepared Statements
```typescript
// Cache prepared statements
const stmtCache = new Map();

function getStmt(sql: string) {
  if (!stmtCache.has(sql)) {
    stmtCache.set(sql, db.prepare(sql));
  }
  return stmtCache.get(sql);
}

// Use named parameters
const stmt = getStmt(`
  SELECT * FROM sessions 
  WHERE project_id = $project 
    AND status = $status
  ORDER BY started_at DESC
  LIMIT $limit
`);

const sessions = stmt.all({
  $project: projectId,
  $status: 'active',
  $limit: 10,
});
```

#### JSON Handling
```typescript
// Store JSON as TEXT
db.run(`
  INSERT INTO sessions (id, files_accessed)
  VALUES (?, json(?))
`, sessionId, JSON.stringify(files));

// Query JSON with json_extract
const sessions = db.query(`
  SELECT id, json_extract(metadata, '$.duration') as duration
  FROM sessions
  WHERE json_extract(metadata, '$.user') = ?
`).all(userId);
```

### Key Takeaways
- **ALWAYS enable WAL mode** for performance
- Use transactions for bulk operations (100x faster)
- Prepared statements with caching
- Store JSON as TEXT, use json_extract for queries
- Named parameters ($param) for clarity
- Synchronous API is simpler (no async complexity)

---

## 4. @babel/parser for TypeScript/JavaScript

### Decision
Use `@babel/parser` with `@babel/traverse` for AST-based import extraction.

### Rationale
- Handles TypeScript, JSX, modern JavaScript
- Robust error recovery
- Extract imports, exports, dependencies
- Well-maintained by Babel team

### Best Practices

#### Parsing TypeScript/JavaScript
```typescript
import { parse } from '@babel/parser';
import traverse from '@babel/traverse';

function parseFile(code: string, filename: string) {
  try {
    return parse(code, {
      sourceType: 'module',
      plugins: [
        'typescript',
        'jsx',
        'decorators-legacy',
        'classProperties',
        'dynamicImport',
      ],
      errorRecovery: true,  // Continue parsing on errors
    });
  } catch (error) {
    logger.error('Parse error', { filename, error: error.message });
    return null;
  }
}
```

#### Extract Imports
```typescript
function extractImports(ast, filepath: string): string[] {
  const imports: string[] = [];
  
  traverse(ast, {
    ImportDeclaration(path) {
      const source = path.node.source.value;
      // Resolve relative imports
      if (source.startsWith('.')) {
        const resolved = resolveRelativePath(filepath, source);
        imports.push(resolved);
      } else {
        // npm package
        imports.push(source);
      }
    },
    
    CallExpression(path) {
      // require('module')
      if (
        path.node.callee.type === 'Identifier' &&
        path.node.callee.name === 'require' &&
        path.node.arguments[0]?.type === 'StringLiteral'
      ) {
        imports.push(path.node.arguments[0].value);
      }
      
      // import('module') - dynamic import
      if (path.node.callee.type === 'Import') {
        if (path.node.arguments[0]?.type === 'StringLiteral') {
          imports.push(path.node.arguments[0].value);
        }
      }
    },
  });
  
  return [...new Set(imports)];  // Deduplicate
}
```

#### Extract Exports
```typescript
function extractExports(ast): ExportInfo[] {
  const exports: ExportInfo[] = [];
  
  traverse(ast, {
    ExportNamedDeclaration(path) {
      if (path.node.declaration) {
        // export const x = ...
        if (path.node.declaration.type === 'VariableDeclaration') {
          for (const decl of path.node.declaration.declarations) {
            if (decl.id.type === 'Identifier') {
              exports.push({ name: decl.id.name, type: 'named' });
            }
          }
        }
        // export function foo() {}
        if (path.node.declaration.type === 'FunctionDeclaration') {
          exports.push({ 
            name: path.node.declaration.id.name, 
            type: 'named' 
          });
        }
      }
    },
    
    ExportDefaultDeclaration(path) {
      exports.push({ name: 'default', type: 'default' });
    },
    
    ExportAllDeclaration(path) {
      exports.push({ 
        name: '*', 
        type: 'all', 
        from: path.node.source.value 
      });
    },
  });
  
  return exports;
}
```

#### Dependency Tree Builder
```typescript
interface DependencyNode {
  path: string;
  imports: string[];
  exports: ExportInfo[];
  level: number;
}

function buildDependencyTree(
  entryPath: string, 
  maxDepth = 1
): Map<string, DependencyNode> {
  const tree = new Map<string, DependencyNode>();
  const queue: [string, number][] = [[entryPath, 0]];
  
  while (queue.length > 0) {
    const [filepath, level] = queue.shift()!;
    
    if (tree.has(filepath) || level > maxDepth) continue;
    
    const code = readFileSync(filepath, 'utf-8');
    const ast = parseFile(code, filepath);
    if (!ast) continue;
    
    const imports = extractImports(ast, filepath);
    const exports = extractExports(ast);
    
    tree.set(filepath, { path: filepath, imports, exports, level });
    
    // Queue dependencies for next level
    for (const imp of imports) {
      if (imp.startsWith('.')) {  // Local file only
        queue.push([imp, level + 1]);
      }
    }
  }
  
  return tree;
}
```

### Key Takeaways
- Enable `errorRecovery` for robustness
- Support TypeScript, JSX, modern syntax
- Extract both static and dynamic imports
- Resolve relative paths to absolute
- Build dependency tree with depth limit (MVP: level 1 only)
- Cache parsed ASTs for frequently accessed files

---

## 5. Background Services in Bun/Node.js

### Decision
Use `setInterval` with `AbortController` for background services.

### Rationale
- Simple, no external dependencies
- AbortController for clean cancellation
- Non-blocking execution
- Graceful shutdown support

### Best Practices

#### PeriodicTask Pattern
```typescript
interface PeriodicTaskOptions {
  name: string;
  intervalMs: number;
  task: () => Promise<void>;
  runImmediately?: boolean;
}

class PeriodicTask {
  private intervalId?: Timer;
  private abortController = new AbortController();
  
  constructor(private options: PeriodicTaskOptions) {}
  
  async start(): Promise<void> {
    if (this.options.runImmediately) {
      await this.runTask();
    }
    
    this.intervalId = setInterval(
      () => this.runTask(),
      this.options.intervalMs
    );
    
    logger.info(`Background task started: ${this.options.name}`);
  }
  
  async stop(): Promise<void> {
    this.abortController.abort();
    
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = undefined;
    }
    
    logger.info(`Background task stopped: ${this.options.name}`);
  }
  
  private async runTask(): Promise<void> {
    if (this.abortController.signal.aborted) return;
    
    try {
      await this.options.task();
    } catch (error) {
      logger.error(`Task failed: ${this.options.name}`, { error });
    }
  }
}
```

#### Background Service Manager
```typescript
class BackgroundServiceManager {
  private tasks: PeriodicTask[] = [];
  
  register(options: PeriodicTaskOptions): void {
    this.tasks.push(new PeriodicTask(options));
  }
  
  async startAll(): Promise<void> {
    await Promise.all(this.tasks.map(task => task.start()));
  }
  
  async stopAll(): Promise<void> {
    // Use allSettled to ensure all tasks stop even if some fail
    await Promise.allSettled(this.tasks.map(task => task.stop()));
  }
}
```

#### Service Definitions
```typescript
const serviceManager = new BackgroundServiceManager();

// Context scorer (every 5 minutes)
serviceManager.register({
  name: 'context-scorer',
  intervalMs: 5 * 60 * 1000,  // 5 minutes
  task: async () => {
    const items = await loadContextItems();
    const scored = items.map(item => ({
      ...item,
      score: calculateContextScore(item.lastAccessed, item.accessCount),
    }));
    await saveContextScores(scored);
  },
});

// Context pruner (every 10 minutes)
serviceManager.register({
  name: 'context-pruner',
  intervalMs: 10 * 60 * 1000,  // 10 minutes
  task: async () => {
    const usage = await getContextWindowUsage();
    if (usage > 0.8) {  // 80% threshold
      await pruneContext();
    }
  },
});

// Session archiver (every hour)
serviceManager.register({
  name: 'session-archiver',
  intervalMs: 60 * 60 * 1000,  // 1 hour
  task: async () => {
    const oldSessions = await findInactiveSessions(30);  // 30 min
    await archiveSessions(oldSessions);
  },
});

// Embeddings generator (every 15 minutes)
serviceManager.register({
  name: 'embeddings-generator',
  intervalMs: 15 * 60 * 1000,  // 15 minutes
  task: async () => {
    const discoveries = await findDiscoveriesWithoutEmbeddings();
    if (discoveries.length > 0) {
      await generateEmbeddings(discoveries);
    }
  },
});
```

#### Graceful Shutdown
```typescript
// Main server startup
const serviceManager = new BackgroundServiceManager();
// ... register services

await serviceManager.startAll();

// Graceful shutdown handlers
process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully...');
  await serviceManager.stopAll();
  await mcpServer.close();
  await db.close();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  await serviceManager.stopAll();
  await mcpServer.close();
  await db.close();
  process.exit(0);
});

process.on('uncaughtException', async (error) => {
  logger.error('Uncaught exception', { error });
  await serviceManager.stopAll();
  process.exit(1);
});
```

### Key Takeaways
- Use AbortController for clean cancellation
- Wrap task execution in try-catch (don't crash service)
- Log all service lifecycle events
- Use Promise.allSettled for shutdown (don't fail on one error)
- Handle SIGINT/SIGTERM for graceful shutdown
- Services should be non-blocking (use async)

---

## 6. OpenAI Embeddings API

### Decision
Use OpenAI `text-embedding-3-small` model (1536 dimensions).

### Rationale
- Cost-effective ($0.02 per 1M tokens)
- Good performance for semantic search
- 1536 dimensions balance quality/storage
- Official SDK with TypeScript support

### Best Practices

#### Client Setup
```typescript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// Batch embedding generation
async function generateEmbeddings(
  texts: string[]
): Promise<number[][]> {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: texts,  // Can send up to 2048 texts
    encoding_format: 'float',
  });
  
  return response.data.map(item => item.embedding);
}
```

#### Error Handling & Retry
```typescript
async function generateEmbeddingsWithRetry(
  texts: string[],
  maxRetries = 3
): Promise<number[][]> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await generateEmbeddings(texts);
    } catch (error) {
      if (error.status === 429) {  // Rate limit
        const delay = Math.pow(2, attempt) * 1000;  // Exponential backoff
        logger.warn(`Rate limited, retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else if (attempt === maxRetries) {
        throw error;
      }
    }
  }
  
  throw new Error('Failed after max retries');
}
```

#### Batch Processing
```typescript
function chunkArray<T>(array: T[], size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunks.push(array.slice(i, i + size));
  }
  return chunks;
}

async function batchGenerateEmbeddings(
  discoveries: Discovery[]
): Promise<void> {
  const BATCH_SIZE = 100;
  const chunks = chunkArray(discoveries, BATCH_SIZE);
  
  for (const chunk of chunks) {
    const texts = chunk.map(d => d.content);
    const embeddings = await generateEmbeddingsWithRetry(texts);
    
    // Store in Chroma
    await collection.add({
      ids: chunk.map(d => d.id),
      embeddings: embeddings,
      metadatas: chunk.map(d => ({
        type: d.type,
        module: d.module,
        session: d.sessionId,
      })),
      documents: texts,
    });
  }
}
```

### Key Takeaways
- Batch up to 2048 texts per API call (optimal: 100-200)
- Implement exponential backoff for rate limits
- Handle 429 errors gracefully
- text-embedding-3-small is cost-effective for MVP
- 1536 dimensions work well with ChromaDB

---

## Architecture Integration

### Onion Architecture Application

**Domain Layer (Pure):**
- Context scoring calculations (recency + access)
- Discovery pattern matching (regex)
- Token counting (estimation)
- Pruning rules (threshold logic)

**Application Layer (Orchestration):**
- Use cases: InitializeProject, TrackSession, SearchContext, ExtractDiscoveries, EnrichContext, PruneContext
- Services: SessionManager, ContextManager, FileAccessTracker
- Ports: IStorage, IVectorDB, IEmbedding (abstractions)

**Infrastructure Layer (I/O):**
- Storage: yaml-handler, sqlite-adapter, chroma-adapter
- MCP: server.ts, resources/, tools/
- CLI: commands (init, serve, show, status)
- Background: ContextScorer, ContextPruner, EmbeddingsGenerator
- External: OpenAIClient

### Data Flow

```
User Query (Claude Desktop)
    ↓
MCP Server (Infrastructure)
    ↓
SearchContext Use Case (Application)
    ↓
ContextScorer Calculation (Domain)
    ↓
ChromaAdapter Query (Infrastructure)
    ↓
Results → MCP Response
```

---

## Implementation Checklist

### Foundation
- [x] Research MCP SDK patterns
- [x] Research ChromaDB with TypeScript
- [x] Research Bun SQLite
- [x] Research Babel parser for AST
- [x] Research background service patterns
- [x] Research OpenAI embeddings

### Next Steps (Phase 1: Data Models)
- [ ] Define domain models (ProjectContext, Session, Discovery, ContextItem)
- [ ] Define storage schemas (SQLite tables, Chroma collections)
- [ ] Define MCP contracts (resources, tools with schemas)
- [ ] Create data-model.md
- [ ] Create contracts/

### Future Phases
- [ ] Implement domain layer (pure functions)
- [ ] Implement application layer (use cases)
- [ ] Implement infrastructure layer (adapters)
- [ ] Write tests (90%+ coverage)
- [ ] Integration testing
- [ ] Documentation

---

## Key Decisions Summary

| Technology | Decision | Rationale |
|------------|----------|-----------|
| **MCP Server** | @modelcontextprotocol/sdk with StdioServerTransport | Official SDK, TypeScript support, stdio for local |
| **Vector DB** | chromadb (npm, persistent) | Local-first, batch ops, metadata filtering |
| **Relational DB** | bun:sqlite with WAL mode | 3-6x faster, native to Bun, zero dependencies |
| **AST Parser** | @babel/parser + @babel/traverse | TypeScript support, robust, maintained |
| **Background** | setInterval + AbortController | Simple, no deps, graceful shutdown |
| **Embeddings** | OpenAI text-embedding-3-small | Cost-effective, 1536 dims, good quality |

---

## Alternatives Considered

### Vector DB Alternatives
- **Rejected: Pinecone** - Cloud-based (violates local-first)
- **Rejected: Weaviate** - Too heavy, server required
- **Rejected: Milvus** - Complex setup, overkill for MVP
- **Chosen: ChromaDB** - Local, simple, perfect for MVP

### SQLite Alternatives
- **Rejected: better-sqlite3** - Slower than bun:sqlite (3-6x)
- **Rejected: PostgreSQL** - Server required, overkill
- **Rejected: MongoDB** - Document DB not needed
- **Chosen: bun:sqlite** - Fastest, native, simple

### Parser Alternatives
- **Rejected: TypeScript Compiler API** - Heavy, slow
- **Rejected: regex parsing** - Fragile, unreliable
- **Rejected: acorn** - No TypeScript support
- **Chosen: @babel/parser** - Battle-tested, full syntax support

---

## Performance Optimizations

### SQLite
1. Enable WAL mode (10-100x concurrency improvement)
2. Use transactions for bulk operations (100x faster)
3. Prepared statements with caching
4. Indexes on query columns

### ChromaDB
1. Batch insertions (100-200 items)
2. Configure HNSW parameters (construction_ef, search_ef)
3. Metadata pre-filtering before vector search
4. Persistent mode (no server startup overhead)

### OpenAI API
1. Batch requests (up to 2048 texts)
2. Exponential backoff for rate limits
3. Cache embeddings (never regenerate)
4. Async generation (non-blocking)

### Background Services
1. Non-blocking execution (async)
2. AbortController for clean cancellation
3. Interval-based (not polling loops)
4. Graceful shutdown (no zombie processes)

---

## Critical Gotchas

### MCP SDK
- Tool errors should return in results (not throw McpError)
- Use Zod for input validation AND JSON schema generation
- Implement graceful shutdown (AbortController + signal handlers)

### ChromaDB
- Always use batches for insertions (single adds are slow)
- Metadata filtering happens BEFORE vector search (pre-filter)
- Collection names must be alphanumeric + underscores

### Bun SQLite
- MUST enable WAL mode for performance (default is DELETE mode)
- Synchronous API (no await needed)
- JSON stored as TEXT, use json_extract for queries

### Babel Parser
- Enable errorRecovery to continue on syntax errors
- Resolve relative imports to absolute paths
- Cache parsed ASTs (parsing is expensive)

### Background Services
- Always wrap task execution in try-catch (don't crash)
- Use Promise.allSettled for shutdown (don't fail on one error)
- Handle SIGINT/SIGTERM for graceful shutdown

---

**END OF RESEARCH**
