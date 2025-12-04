# Technology Research for Context Tool MVP

**Date:** 2025-10-09  
**Purpose:** Technical research for implementing the Context Tool MVP  
**Status:** Complete

---

## Table of Contents

1. [MCP SDK (@modelcontextprotocol/sdk)](#1-mcp-sdk-modelcontextprotocolsdk)
2. [ChromaDB with TypeScript/Bun](#2-chromadb-with-typescriptbun)
3. [bun:sqlite (Built-in SQLite)](#3-bunsqlite-built-in-sqlite)
4. [@babel/parser for TypeScript/JavaScript](#4-babelparser-for-typescriptjavascript)
5. [Background Services in Bun/Node.js](#5-background-services-in-bunnodejs)

---

## 1. MCP SDK (@modelcontextprotocol/sdk)

### Decision & Rationale

**Use:** `@modelcontextprotocol/sdk` version 1.19.1+ (latest)  
**Transport:** `StdioServerTransport` for stdio communication  
**Rationale:** Official TypeScript SDK with full MCP specification support, designed specifically for stdio servers, and provides robust lifecycle and error handling.

### Core Architecture

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

// Initialize server with metadata
const server = new McpServer({
  name: 'kioku-context-server',
  version: '1.0.0'
});

// Create stdio transport
const transport = new StdioServerTransport();

// Connect server to transport
await server.connect(transport);
```

### Best Practices

#### 1. Server Initialization
- Always provide clear name and version metadata
- Initialize server BEFORE creating transport
- Use descriptive server names for debugging

#### 2. Resource Registration

**Static Resources:**
```typescript
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [
    {
      uri: 'context://project',
      name: 'Project Context',
      description: 'Overall project context and architecture',
      mimeType: 'application/yaml'
    }
  ]
}));

server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  
  if (uri === 'context://project') {
    const content = await loadProjectContext();
    return {
      contents: [{
        uri,
        mimeType: 'application/yaml',
        text: content
      }]
    };
  }
  
  throw new Error(`Unknown resource: ${uri}`);
});
```

**Dynamic Resources with Templates:**
```typescript
import { ResourceTemplate } from '@modelcontextprotocol/sdk/types.js';

// Define template
const moduleTemplate = new ResourceTemplate('context://modules/{moduleName}', {
  list: undefined
});

// Register template handler
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const { uri } = request.params;
  
  // Extract parameters from URI
  const match = uri.match(/^context:\/\/modules\/(.+)$/);
  if (match) {
    const moduleName = match[1];
    const moduleContext = await loadModuleContext(moduleName);
    
    return {
      contents: [{
        uri,
        mimeType: 'application/yaml',
        text: moduleContext
      }]
    };
  }
});
```

#### 3. Tool Registration with Zod

```typescript
import { z } from 'zod';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'context_search',
      description: 'Search project context using semantic similarity',
      inputSchema: {
        type: 'object',
        properties: {
          query: {
            type: 'string',
            description: 'Search query'
          },
          limit: {
            type: 'number',
            description: 'Maximum results to return',
            default: 5
          }
        },
        required: ['query']
      }
    }
  ]
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  if (name === 'context_search') {
    const results = await searchContext(args.query, args.limit || 5);
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(results, null, 2)
        }
      ]
    };
  }
  
  throw new Error(`Unknown tool: ${name}`);
});
```

#### 4. Error Handling

```typescript
import { McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';

// Use McpError for protocol-level errors
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  try {
    const content = await loadResource(request.params.uri);
    return { contents: [content] };
  } catch (error) {
    if (error.code === 'ENOENT') {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Resource not found: ${request.params.uri}`
      );
    }
    throw new McpError(
      ErrorCode.InternalError,
      `Failed to load resource: ${error.message}`
    );
  }
});

// Transport-level error handling
transport.onerror = (error) => {
  logger.error('Transport error', { error });
};

transport.onclose = () => {
  logger.info('Transport closed');
  process.exit(0);
};
```

#### 5. Lifecycle Management

```typescript
import { AbortController } from 'node:abort-controller';

const abortController = new AbortController();

// Graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Shutting down gracefully...');
  abortController.abort();
  await transport.close();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.info('Shutting down gracefully...');
  abortController.abort();
  await transport.close();
  process.exit(0);
});

// Use AbortSignal for cancellable operations
async function longRunningOperation(signal: AbortSignal) {
  if (signal.aborted) {
    throw new Error('Operation aborted');
  }
  
  signal.addEventListener('abort', () => {
    // Cleanup logic
  });
  
  // ... operation logic
}
```

### Error Code Categories

**SDK-specific errors:** -32000 to -32099
- `ConnectionClosed`
- `RequestTimeout`
- `InvalidRequest`

**Standard JSON-RPC errors:** -32600 to -32699
- `ParseError`: -32700
- `InvalidRequest`: -32600
- `MethodNotFound`: -32601
- `InvalidParams`: -32602
- `InternalError`: -32603

### Implementation Recommendations

1. **Use Zod for input validation** - Type safety and runtime validation
2. **Provide comprehensive error messages** - Help LLM understand what went wrong
3. **Return both structured and human-readable content** - Text + JSON when appropriate
4. **Implement proper cleanup** - Use AbortController for cancellation
5. **Log all protocol interactions** - Essential for debugging MCP servers
6. **Use TypeScript strict mode** - Catch errors at compile time

### Gotchas & Considerations

- **Stdio transport is blocking**: Don't perform long-running sync operations
- **Each request should be quick**: Use async operations for I/O
- **Tool errors vs protocol errors**: Return tool errors in result, not as MCP errors
- **Resource URIs must be consistent**: Once defined, don't change URI patterns
- **Connection lifecycle**: Server must handle SIGINT/SIGTERM gracefully

---

## 2. ChromaDB with TypeScript/Bun

### Decision & Rationale

**Use:** `chromadb` npm package (v3.0.17+)  
**Mode:** Persistent client (local storage)  
**Rationale:** Mature vector database with TypeScript support, local-first architecture, supports metadata filtering, and offers batch operations for performance.

### Bun Compatibility

ChromaDB's npm package works with Bun through Node.js compatibility layer. No special configuration required.

```bash
bun add chromadb
```

### Core Setup

```typescript
import { ChromaClient } from 'chromadb';

// Initialize client (local persistent storage)
const client = new ChromaClient({
  path: '.context/chroma' // Local storage path
});

// Verify connection
const heartbeat = await client.heartbeat();
const version = await client.version();

logger.info('ChromaDB initialized', { version });
```

### Collection Management

```typescript
// Create collection with metadata
const collection = await client.createCollection({
  name: 'context-embeddings',
  metadata: {
    description: 'Project context embeddings',
    hnsw_batch_size: 100,      // Batch size for HNSW index
    hnsw_sync_threshold: 1000   // Sync threshold
  }
});

// Get existing collection
const collection = await client.getCollection({
  name: 'context-embeddings'
});

// Get or create (idempotent)
const collection = await client.getOrCreateCollection({
  name: 'context-embeddings',
  metadata: {
    description: 'Project context embeddings'
  }
});

// List all collections
const collections = await client.listCollections({
  limit: 10,
  offset: 0
});

// Delete collection
await client.deleteCollection({
  name: 'old-collection'
});

// Count collections
const count = await client.countCollections();
```

### Adding Data

```typescript
// Add documents with embeddings
await collection.add({
  ids: ['doc1', 'doc2', 'doc3'],
  embeddings: [
    [0.1, 0.2, 0.3, ...], // 1536 dimensions for text-embedding-3-small
    [0.4, 0.5, 0.6, ...],
    [0.7, 0.8, 0.9, ...]
  ],
  metadatas: [
    { source: 'module', moduleName: 'auth', type: 'pattern' },
    { source: 'module', moduleName: 'database', type: 'pattern' },
    { source: 'session', sessionId: 'sess-123', timestamp: 1696800000 }
  ],
  documents: [
    'Authentication uses JWT tokens with refresh mechanism',
    'Database uses PostgreSQL with connection pooling',
    'User reported bug in login flow'
  ]
});

// Add without embeddings (auto-generated if embedding function configured)
await collection.add({
  ids: ['doc4'],
  metadatas: [{ source: 'discovery' }],
  documents: ['Discovered new pattern in codebase']
});
```

### Batch Operations

```typescript
import { create_batches } from 'chromadb/utils/batch_utils';

// Check maximum batch size
const maxBatchSize = client.max_batch_size;
logger.info('Max batch size', { maxBatchSize });

// Prepare large dataset
const largeDataset: Array<[string, string, number[]]> = [];
for (let i = 0; i < 10000; i++) {
  largeDataset.push([
    `doc-${i}`,
    `Document content ${i}`,
    generateEmbedding() // 1536-dimensional array
  ]);
}

// Extract components
const ids = largeDataset.map(d => d[0]);
const documents = largeDataset.map(d => d[1]);
const embeddings = largeDataset.map(d => d[2]);

// Create batches
const batches = create_batches(
  client,
  ids,
  embeddings,
  metadatas,
  documents
);

// Insert batches
for (const batch of batches) {
  await collection.add({
    ids: batch[0],
    embeddings: batch[1],
    metadatas: batch[2],
    documents: batch[3]
  });
  
  logger.debug('Batch inserted', { count: batch[0].length });
}
```

### Querying Data

```typescript
// Query by embedding
const results = await collection.query({
  queryEmbeddings: [[0.1, 0.2, 0.3, ...]], // Your query embedding
  nResults: 5,
  include: ['embeddings', 'metadatas', 'documents', 'distances']
});

// Query by text (if embedding function configured)
const results = await collection.query({
  queryTexts: ['authentication bug'],
  nResults: 5,
  include: ['metadatas', 'documents', 'distances']
});

// Query with metadata filters
const results = await collection.query({
  queryEmbeddings: [[0.1, 0.2, 0.3, ...]],
  nResults: 10,
  where: {
    moduleName: 'auth',
    type: 'pattern'
  },
  include: ['metadatas', 'documents', 'distances']
});

// Complex filters with operators
const results = await collection.query({
  queryEmbeddings: [[0.1, 0.2, 0.3, ...]],
  nResults: 10,
  where: {
    $and: [
      { source: { $eq: 'session' } },
      { timestamp: { $gte: 1696800000 } }
    ]
  }
});
```

### Filter Operators

```typescript
// Equality
where: { field: 'value' }
where: { field: { $eq: 'value' } }

// Not equal
where: { field: { $ne: 'value' } }

// Greater than / Less than (numeric only)
where: { field: { $gt: 100 } }
where: { field: { $gte: 100 } }
where: { field: { $lt: 200 } }
where: { field: { $lte: 200 } }

// In / Not in
where: { field: { $in: ['value1', 'value2'] } }
where: { field: { $nin: ['value1', 'value2'] } }

// Logical operators
where: {
  $and: [
    { field1: 'value1' },
    { field2: { $gt: 100 } }
  ]
}

where: {
  $or: [
    { field1: 'value1' },
    { field2: 'value2' }
  ]
}

// Document content filtering
whereDocument: { $contains: 'search_string' }
```

### Getting Documents

```typescript
// Get all documents
const all = await collection.get();

// Get by IDs
const specific = await collection.get({
  ids: ['doc1', 'doc2']
});

// Get with filter
const filtered = await collection.get({
  where: { moduleName: 'auth' },
  limit: 10,
  offset: 0,
  include: ['metadatas', 'documents']
});

// Count documents
const count = await collection.count();
```

### Updating and Deleting

```typescript
// Upsert (update if exists, insert if not)
await collection.upsert({
  ids: ['doc1'],
  embeddings: [[0.1, 0.2, 0.3, ...]],
  metadatas: [{ updated: true, timestamp: Date.now() }],
  documents: ['Updated content']
});

// Update collection metadata
await collection.modify({
  name: 'new-name', // Optional
  metadata: { version: '2.0' } // Optional
});

// Delete by IDs
await collection.delete({
  ids: ['doc1', 'doc2']
});

// Delete by filter
await collection.delete({
  where: { 
    $and: [
      { source: 'session' },
      { timestamp: { $lt: Date.now() - 30 * 24 * 60 * 60 * 1000 } } // 30 days old
    ]
  }
});
```

### Performance Optimization

#### 1. Collection Configuration
```typescript
const collection = await client.createCollection({
  name: 'context-embeddings',
  metadata: {
    // Batch size for HNSW index (default: 100)
    // Higher values improve ingest performance
    hnsw_batch_size: 200,
    
    // Sync threshold (default: 1000)
    // Controls when index is synced to disk
    hnsw_sync_threshold: 2000
  }
});
```

#### 2. Batch Insertions
```typescript
// GOOD - Batch insert
await collection.add({
  ids: ['doc1', 'doc2', 'doc3', ...], // Multiple IDs
  embeddings: [...],
  documents: [...]
});

// BAD - Individual inserts
for (const doc of docs) {
  await collection.add({
    ids: [doc.id],
    embeddings: [doc.embedding],
    documents: [doc.content]
  });
}
```

#### 3. Query Optimization
```typescript
// Pre-filter with metadata BEFORE similarity search
const results = await collection.query({
  queryEmbeddings: [[...]],
  where: { moduleName: 'auth' }, // Metadata pre-filtering
  nResults: 5
});

// Only request needed fields
const results = await collection.query({
  queryEmbeddings: [[...]],
  nResults: 5,
  include: ['documents', 'metadatas'] // Don't include embeddings if not needed
});
```

### Best Practices

1. **Use persistent client for production** - In-memory only for testing
2. **Always provide metadata** - Enables powerful filtering
3. **Batch operations when possible** - 10-100x faster than individual ops
4. **Configure HNSW parameters** - Tune for your workload
5. **Use metadata pre-filtering** - Reduces search space
6. **Keep embedding dimensions consistent** - 1536 for text-embedding-3-small
7. **Handle connection errors gracefully** - ChromaDB may not be running

### Implementation Recommendations

```typescript
// Pure function for creating ChromaDB client (domain layer)
export interface ChromaConfig {
  path: string;
  collectionName: string;
  metadata?: Record<string, any>;
}

// Infrastructure layer - ChromaDB adapter
export class ChromaContextStore {
  private client: ChromaClient;
  private collection: Collection;
  
  constructor(private config: ChromaConfig) {}
  
  async initialize(): Promise<void> {
    this.client = new ChromaClient({ path: this.config.path });
    this.collection = await this.client.getOrCreateCollection({
      name: this.config.collectionName,
      metadata: this.config.metadata
    });
  }
  
  async addEmbeddings(items: ContextEmbedding[]): Promise<void> {
    const ids = items.map(i => i.id);
    const embeddings = items.map(i => i.embedding);
    const metadatas = items.map(i => i.metadata);
    const documents = items.map(i => i.content);
    
    await this.collection.add({
      ids,
      embeddings,
      metadatas,
      documents
    });
  }
  
  async searchSimilar(
    queryEmbedding: number[],
    limit: number = 5,
    filter?: Record<string, any>
  ): Promise<SearchResult[]> {
    const results = await this.collection.query({
      queryEmbeddings: [queryEmbedding],
      nResults: limit,
      where: filter,
      include: ['metadatas', 'documents', 'distances']
    });
    
    return results.ids[0].map((id, i) => ({
      id,
      content: results.documents[0][i],
      metadata: results.metadatas[0][i],
      distance: results.distances[0][i]
    }));
  }
  
  async close(): Promise<void> {
    // ChromaDB client doesn't require explicit close
    // But good practice for cleanup
  }
}
```

### Gotchas & Considerations

- **ChromaDB must be accessible**: Either embedded (default) or server mode
- **Batch size limits**: Check `client.max_batch_size` before batching
- **HNSW index updates**: Can be slow for very large batches, tune batch_size
- **Metadata types**: Only string, number, boolean supported
- **Document content search**: Less accurate than embedding search, use for filtering only
- **Collection names**: Must be unique, case-sensitive
- **No built-in pagination**: Implement manually with limit/offset

---

## 3. bun:sqlite (Built-in SQLite)

### Decision & Rationale

**Use:** Bun's built-in `bun:sqlite` (NOT better-sqlite3)  
**Mode:** Persistent database with WAL mode  
**Rationale:** Native to Bun, 3-6x faster than better-sqlite3, synchronous API (simpler code), zero npm dependencies, perfect for local-first architecture.

### Why Not better-sqlite3?

- **Compatibility issues**: better-sqlite3 requires recompilation for Bun
- **Performance**: bun:sqlite is 3-6x faster for reads, 2-3x faster for writes
- **Maintenance**: Built into Bun, no version conflicts
- **API similarity**: Inspired by better-sqlite3, easy migration

### Core Setup

```typescript
import { Database } from 'bun:sqlite';

// Create or open database
const db = new Database('.context/sessions.db');

// Enable WAL mode for better concurrency (CRITICAL!)
db.exec('PRAGMA journal_mode = WAL;');

// Other recommended pragmas
db.exec('PRAGMA synchronous = NORMAL;'); // Faster, still safe with WAL
db.exec('PRAGMA foreign_keys = ON;');    // Enforce foreign keys
db.exec('PRAGMA temp_store = MEMORY;');  // Temp tables in memory

// Create schema
db.exec(`
  CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    started_at INTEGER NOT NULL,
    ended_at INTEGER,
    message_count INTEGER DEFAULT 0,
    duration_ms INTEGER,
    metadata TEXT
  );
  
  CREATE TABLE IF NOT EXISTS discoveries (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
  );
  
  CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);
  CREATE INDEX IF NOT EXISTS idx_discoveries_session_id ON discoveries(session_id);
  CREATE INDEX IF NOT EXISTS idx_discoveries_type ON discoveries(type);
`);
```

### Prepared Statements

```typescript
// Prepare statements (cached automatically with query())
const insertSession = db.query(`
  INSERT INTO sessions (id, started_at, metadata)
  VALUES ($id, $startedAt, $metadata)
`);

const updateSession = db.query(`
  UPDATE sessions
  SET ended_at = $endedAt,
      message_count = $messageCount,
      duration_ms = $durationMs
  WHERE id = $id
`);

const getSession = db.query(`
  SELECT * FROM sessions WHERE id = $id
`);

const getAllSessions = db.query(`
  SELECT * FROM sessions
  ORDER BY started_at DESC
  LIMIT $limit OFFSET $offset
`);

// Execute with named parameters
insertSession.run({
  $id: 'sess-123',
  $startedAt: Date.now(),
  $metadata: JSON.stringify({ source: 'claude-desktop' })
});

// Get single result
const session = getSession.get({ $id: 'sess-123' });

// Get all results
const sessions = getAllSessions.all({ $limit: 10, $offset: 0 });
```

### Query Methods

```typescript
const query = db.query('SELECT * FROM sessions WHERE id = ?');

// .get() - First result or undefined
const session = query.get('sess-123');
// Returns: { id: 'sess-123', started_at: 1696800000, ... } | undefined

// .all() - Array of all results
const sessions = query.all();
// Returns: [{ id: '...', ... }, { id: '...', ... }]

// .run() - Execute without returning results (INSERT, UPDATE, DELETE)
const result = query.run('sess-123');
// Returns: { changes: 1, lastInsertRowid: 0 }

// .values() - Results as arrays (faster)
const values = query.values();
// Returns: [['sess-123', 1696800000, ...], ...]

// .iterate() - Lazy iteration (memory efficient)
for (const row of query.iterate()) {
  console.log(row);
}
```

### Transactions

```typescript
// Define transaction function
const insertMultiple = db.transaction((sessions: Session[]) => {
  const insert = db.query(`
    INSERT INTO sessions (id, started_at, metadata)
    VALUES ($id, $startedAt, $metadata)
  `);
  
  for (const session of sessions) {
    insert.run({
      $id: session.id,
      $startedAt: session.startedAt,
      $metadata: JSON.stringify(session.metadata)
    });
  }
});

// Execute transaction (atomic)
insertMultiple([
  { id: 'sess-1', startedAt: Date.now(), metadata: {} },
  { id: 'sess-2', startedAt: Date.now(), metadata: {} }
]);

// Transaction with return value
const countAndInsert = db.transaction((session: Session) => {
  const count = db.query('SELECT COUNT(*) as count FROM sessions').get();
  
  db.query(`
    INSERT INTO sessions (id, started_at, metadata)
    VALUES ($id, $startedAt, $metadata)
  `).run({
    $id: session.id,
    $startedAt: session.startedAt,
    $metadata: JSON.stringify(session.metadata)
  });
  
  return count.count + 1;
});

const newCount = countAndInsert(session);

// Transaction types
const deferred = db.transaction(() => { /* ... */ }); // Default
const immediate = db.transaction(() => { /* ... */ }, { immediate: true });
const exclusive = db.transaction(() => { /* ... */ }, { exclusive: true });
```

### Parameter Binding

```typescript
// Named parameters (recommended)
const query = db.query('SELECT * FROM sessions WHERE id = $id AND started_at > $startedAt');
query.all({ $id: 'sess-123', $startedAt: 1696800000 });

// Positional parameters
const query = db.query('SELECT * FROM sessions WHERE id = ?1 AND started_at > ?2');
query.all('sess-123', 1696800000);

// Mixed (not recommended)
const query = db.query('SELECT * FROM sessions WHERE id = ?1 AND started_at > $startedAt');
query.all('sess-123', { $startedAt: 1696800000 });
```

### Type Safety

```typescript
interface Session {
  id: string;
  started_at: number;
  ended_at: number | null;
  message_count: number;
  duration_ms: number | null;
  metadata: string; // JSON string
}

// Type-safe query results
const getSession = db.query<Session, { $id: string }>(`
  SELECT * FROM sessions WHERE id = $id
`);

const session: Session | undefined = getSession.get({ $id: 'sess-123' });

// Map to domain objects
interface SessionDomain {
  id: string;
  startedAt: Date;
  endedAt?: Date;
  messageCount: number;
  durationMs?: number;
  metadata: Record<string, any>;
}

function mapToSessionDomain(row: Session): SessionDomain {
  return {
    id: row.id,
    startedAt: new Date(row.started_at),
    endedAt: row.ended_at ? new Date(row.ended_at) : undefined,
    messageCount: row.message_count,
    durationMs: row.duration_ms ?? undefined,
    metadata: JSON.parse(row.metadata)
  };
}

const sessionDomain = getSession.get({ $id: 'sess-123' })?.then(mapToSessionDomain);
```

### Performance Optimization

#### 1. Enable WAL Mode (CRITICAL!)
```typescript
db.exec('PRAGMA journal_mode = WAL;');
// 10-100x faster for concurrent reads
// Allows readers while writing
```

#### 2. Use Transactions for Bulk Operations
```typescript
// GOOD - Transaction (100x faster)
const bulkInsert = db.transaction((items: Item[]) => {
  const insert = db.query('INSERT INTO items (id, data) VALUES ($id, $data)');
  for (const item of items) {
    insert.run({ $id: item.id, $data: item.data });
  }
});

bulkInsert(items);

// BAD - Individual inserts (slow)
const insert = db.query('INSERT INTO items (id, data) VALUES ($id, $data)');
for (const item of items) {
  insert.run({ $id: item.id, $data: item.data });
}
```

#### 3. Use Prepared Statements
```typescript
// GOOD - Prepared statement (cached)
const query = db.query('SELECT * FROM sessions WHERE id = ?');
for (const id of ids) {
  const result = query.get(id);
}

// BAD - Re-parsing query each time
for (const id of ids) {
  const result = db.query('SELECT * FROM sessions WHERE id = ?').get(id);
}
```

#### 4. Use Indexes
```typescript
// Create indexes for frequently queried columns
db.exec(`
  CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);
  CREATE INDEX IF NOT EXISTS idx_discoveries_session_id ON discoveries(session_id);
`);
```

#### 5. Use .values() for Large Result Sets
```typescript
// Faster for large datasets (no object creation)
const values = db.query('SELECT id, started_at FROM sessions').values();
// Returns: [['sess-1', 1696800000], ['sess-2', 1696800001]]
```

### Error Handling

```typescript
try {
  const session = getSession.get({ $id: 'sess-123' });
  if (!session) {
    throw new Error('Session not found');
  }
} catch (error) {
  if (error.message.includes('SQLITE_CONSTRAINT')) {
    // Constraint violation (e.g., unique, foreign key)
  } else if (error.message.includes('SQLITE_BUSY')) {
    // Database is locked (rare with WAL mode)
  } else {
    // Other errors
  }
  
  logger.error('Database error', { error });
  throw error;
}
```

### Best Practices

1. **Always enable WAL mode** - Mandatory for good performance
2. **Use transactions for bulk operations** - 10-100x faster
3. **Prepare statements once** - Use `db.query()` which caches
4. **Use named parameters** - More readable and less error-prone
5. **Create indexes** - For columns in WHERE, ORDER BY, JOIN
6. **Use strict mode** - Catches parameter mismatches
7. **Store JSON as TEXT** - Use `JSON.stringify()` / `JSON.parse()`
8. **Handle BigInt properly** - Use `safeIntegers: true` option if needed

### Implementation Recommendations

```typescript
// Pure interface (domain layer)
export interface SessionRepository {
  save(session: Session): void;
  findById(id: string): Session | undefined;
  findAll(limit: number, offset: number): Session[];
  update(session: Session): void;
  delete(id: string): void;
}

// SQLite implementation (infrastructure layer)
export class SqliteSessionRepository implements SessionRepository {
  private db: Database;
  
  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.db.exec('PRAGMA journal_mode = WAL;');
    this.db.exec('PRAGMA foreign_keys = ON;');
    this.initSchema();
  }
  
  private initSchema(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        started_at INTEGER NOT NULL,
        ended_at INTEGER,
        message_count INTEGER DEFAULT 0,
        duration_ms INTEGER,
        metadata TEXT
      );
      
      CREATE INDEX IF NOT EXISTS idx_sessions_started_at ON sessions(started_at);
    `);
  }
  
  save(session: Session): void {
    const insert = this.db.query(`
      INSERT INTO sessions (id, started_at, metadata)
      VALUES ($id, $startedAt, $metadata)
    `);
    
    insert.run({
      $id: session.id,
      $startedAt: session.startedAt.getTime(),
      $metadata: JSON.stringify(session.metadata)
    });
  }
  
  findById(id: string): Session | undefined {
    const query = this.db.query<SessionRow, { $id: string }>(`
      SELECT * FROM sessions WHERE id = $id
    `);
    
    const row = query.get({ $id: id });
    return row ? this.mapToDomain(row) : undefined;
  }
  
  findAll(limit: number, offset: number): Session[] {
    const query = this.db.query<SessionRow, { $limit: number; $offset: number }>(`
      SELECT * FROM sessions
      ORDER BY started_at DESC
      LIMIT $limit OFFSET $offset
    `);
    
    return query.all({ $limit: limit, $offset: offset }).map(this.mapToDomain);
  }
  
  private mapToDomain(row: SessionRow): Session {
    return {
      id: row.id,
      startedAt: new Date(row.started_at),
      endedAt: row.ended_at ? new Date(row.ended_at) : undefined,
      messageCount: row.message_count,
      durationMs: row.duration_ms ?? undefined,
      metadata: JSON.parse(row.metadata)
    };
  }
  
  close(): void {
    this.db.close();
  }
}
```

### Gotchas & Considerations

- **Synchronous API**: bun:sqlite is synchronous (blocking), use in I/O layer only
- **No connection pooling**: Single connection per Database instance
- **BigInt handling**: Use `safeIntegers: true` for numbers > 2^53
- **JSON storage**: Store as TEXT, parse/stringify manually
- **Case sensitivity**: Column names are case-insensitive, but values are case-sensitive
- **Foreign keys disabled by default**: Enable with `PRAGMA foreign_keys = ON;`
- **WAL files**: Creates `-wal` and `-shm` files, normal behavior
- **Close database**: Call `db.close()` on shutdown to flush WAL

---

## 4. @babel/parser for TypeScript/JavaScript

### Decision & Rationale

**Use:** `@babel/parser` + `@babel/traverse`  
**Purpose:** Parse TypeScript/JavaScript files to extract import statements and dependencies  
**Rationale:** Mature, battle-tested, supports full TypeScript syntax, provides visitor pattern for easy AST traversal, zero-config for basic usage.

### Installation

```bash
bun add @babel/parser @babel/traverse @babel/types
```

### Core Setup

```typescript
import * as parser from '@babel/parser';
import traverse from '@babel/traverse';
import * as t from '@babel/types';

// Parse TypeScript file
const code = await Bun.file('src/module.ts').text();

const ast = parser.parse(code, {
  sourceType: 'module',      // or 'script'
  plugins: [
    'typescript',            // TypeScript syntax
    'jsx',                   // JSX syntax (for React)
    'decorators-legacy'      // Decorators
  ]
});

// Traverse AST with visitor pattern
traverse(ast, {
  ImportDeclaration(path) {
    // Handle import statements
    console.log('Import source:', path.node.source.value);
  }
});
```

### Extracting Import Statements

```typescript
interface ImportInfo {
  source: string;           // Module path ('react', './utils')
  type: 'default' | 'namespace' | 'named';
  importedName?: string;    // What's imported
  localName: string;        // Local binding name
}

function extractImports(code: string): ImportInfo[] {
  const imports: ImportInfo[] = [];
  
  const ast = parser.parse(code, {
    sourceType: 'module',
    plugins: ['typescript', 'jsx']
  });
  
  traverse(ast, {
    ImportDeclaration(path) {
      const source = path.node.source.value;
      
      path.node.specifiers.forEach(spec => {
        if (t.isImportDefaultSpecifier(spec)) {
          // import React from 'react'
          imports.push({
            source,
            type: 'default',
            localName: spec.local.name
          });
        } else if (t.isImportNamespaceSpecifier(spec)) {
          // import * as utils from './utils'
          imports.push({
            source,
            type: 'namespace',
            localName: spec.local.name
          });
        } else if (t.isImportSpecifier(spec)) {
          // import { useState } from 'react'
          // import { useState as state } from 'react'
          const importedName = t.isIdentifier(spec.imported) 
            ? spec.imported.name 
            : spec.imported.value;
            
          imports.push({
            source,
            type: 'named',
            importedName,
            localName: spec.local.name
          });
        }
      });
    }
  });
  
  return imports;
}
```

### Extracting Require Statements

```typescript
function extractRequires(code: string): Array<{ source: string; localName?: string }> {
  const requires: Array<{ source: string; localName?: string }> = [];
  
  const ast = parser.parse(code, {
    sourceType: 'module',
    plugins: ['typescript', 'jsx']
  });
  
  traverse(ast, {
    CallExpression(path) {
      // Check if it's require()
      if (
        t.isIdentifier(path.node.callee) &&
        path.node.callee.name === 'require' &&
        path.node.arguments.length === 1 &&
        t.isStringLiteral(path.node.arguments[0])
      ) {
        const source = path.node.arguments[0].value;
        
        // Check if assigned to variable
        // const utils = require('./utils')
        const parent = path.parent;
        if (t.isVariableDeclarator(parent) && t.isIdentifier(parent.id)) {
          requires.push({
            source,
            localName: parent.id.name
          });
        } else {
          requires.push({ source });
        }
      }
    }
  });
  
  return requires;
}
```

### Extracting Dynamic Imports

```typescript
function extractDynamicImports(code: string): string[] {
  const dynamicImports: string[] = [];
  
  const ast = parser.parse(code, {
    sourceType: 'module',
    plugins: ['typescript', 'jsx', 'dynamicImport']
  });
  
  traverse(ast, {
    Import(path) {
      // import('module')
      const parent = path.parent;
      if (
        t.isCallExpression(parent) &&
        parent.arguments.length === 1 &&
        t.isStringLiteral(parent.arguments[0])
      ) {
        dynamicImports.push(parent.arguments[0].value);
      }
    }
  });
  
  return dynamicImports;
}
```

### Extracting Export Statements

```typescript
interface ExportInfo {
  type: 'default' | 'named' | 'all';
  exportedName?: string;
  localName?: string;
  source?: string;
}

function extractExports(code: string): ExportInfo[] {
  const exports: ExportInfo[] = [];
  
  const ast = parser.parse(code, {
    sourceType: 'module',
    plugins: ['typescript', 'jsx']
  });
  
  traverse(ast, {
    ExportDefaultDeclaration(path) {
      // export default Component
      exports.push({ type: 'default' });
    },
    
    ExportNamedDeclaration(path) {
      if (path.node.source) {
        // export { something } from './module'
        path.node.specifiers.forEach(spec => {
          if (t.isExportSpecifier(spec)) {
            const exportedName = t.isIdentifier(spec.exported)
              ? spec.exported.name
              : spec.exported.value;
            const localName = spec.local.name;
            
            exports.push({
              type: 'named',
              exportedName,
              localName,
              source: path.node.source?.value
            });
          }
        });
      } else {
        // export { something }
        path.node.specifiers.forEach(spec => {
          if (t.isExportSpecifier(spec)) {
            const exportedName = t.isIdentifier(spec.exported)
              ? spec.exported.name
              : spec.exported.value;
            const localName = spec.local.name;
            
            exports.push({
              type: 'named',
              exportedName,
              localName
            });
          }
        });
      }
    },
    
    ExportAllDeclaration(path) {
      // export * from './module'
      exports.push({
        type: 'all',
        source: path.node.source.value
      });
    }
  });
  
  return exports;
}
```

### Error Handling

```typescript
function safeExtractImports(code: string, filepath: string): ImportInfo[] {
  try {
    const ast = parser.parse(code, {
      sourceType: 'module',
      plugins: ['typescript', 'jsx'],
      errorRecovery: true // Try to recover from errors
    });
    
    return extractImports(code);
  } catch (error) {
    if (error instanceof SyntaxError) {
      logger.warn('Syntax error in file', { 
        filepath, 
        error: error.message,
        line: error.loc?.line,
        column: error.loc?.column
      });
      return [];
    }
    
    logger.error('Failed to parse file', { filepath, error });
    return [];
  }
}
```

### Performance Considerations

```typescript
// Cache parsed ASTs for files that don't change
const astCache = new Map<string, any>();

function getCachedAST(filepath: string, code: string): any {
  const cacheKey = `${filepath}:${hashCode(code)}`;
  
  if (astCache.has(cacheKey)) {
    return astCache.get(cacheKey);
  }
  
  const ast = parser.parse(code, {
    sourceType: 'module',
    plugins: ['typescript', 'jsx']
  });
  
  astCache.set(cacheKey, ast);
  return ast;
}

function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return hash;
}
```

### Best Practices

1. **Use error recovery** - `errorRecovery: true` to handle partial files
2. **Specify correct plugins** - TypeScript, JSX, decorators as needed
3. **Handle syntax errors gracefully** - Don't crash on malformed code
4. **Cache ASTs** - Parsing is expensive, cache when possible
5. **Use type guards** - `t.isImportDeclaration()` etc. for type safety
6. **Consider source type** - 'module' for ES6, 'script' for CommonJS
7. **Don't traverse entire AST** - Stop early when possible

### Implementation Recommendations

```typescript
// Pure function (domain layer)
export interface DependencyInfo {
  imports: string[];      // Module paths
  exports: string[];      // Exported names
  dependencies: string[]; // All dependencies (imports + requires)
}

export function analyzeDependencies(code: string): DependencyInfo {
  const imports = extractImports(code);
  const requires = extractRequires(code);
  const dynamicImports = extractDynamicImports(code);
  const exports = extractExports(code);
  
  return {
    imports: imports.map(i => i.source),
    exports: exports.map(e => e.exportedName).filter(Boolean) as string[],
    dependencies: [
      ...new Set([
        ...imports.map(i => i.source),
        ...requires.map(r => r.source),
        ...dynamicImports
      ])
    ]
  };
}

// Infrastructure layer - File dependency analyzer
export class FileDependencyAnalyzer {
  async analyzeFile(filepath: string): Promise<DependencyInfo> {
    const code = await Bun.file(filepath).text();
    return analyzeDependencies(code);
  }
  
  async analyzeDirectory(dirpath: string): Promise<Map<string, DependencyInfo>> {
    const glob = new Glob('**/*.{ts,tsx,js,jsx}');
    const files = await Array.fromAsync(glob.scan(dirpath));
    
    const results = new Map<string, DependencyInfo>();
    
    for (const file of files) {
      const filepath = `${dirpath}/${file}`;
      const info = await this.analyzeFile(filepath);
      results.set(filepath, info);
    }
    
    return results;
  }
}
```

### Gotchas & Considerations

- **Parsing is slow**: Cache ASTs when possible
- **Memory usage**: ASTs are large, clear cache periodically
- **Syntax errors**: Always handle gracefully, don't crash
- **Plugin selection**: Missing plugins = parse errors
- **Type imports**: TypeScript type-only imports may be removed at runtime
- **Barrel exports**: `export * from './module'` creates indirect dependencies
- **Circular dependencies**: Need separate detection logic

---

## 5. Background Services in Bun/Node.js

### Decision & Rationale

**Use:** `setInterval` with AbortController for graceful shutdown  
**Alternative:** node-cron for complex scheduling (if needed post-MVP)  
**Rationale:** Built-in, simple, no dependencies, works with Bun's promise-based timers, integrates with AbortController for clean shutdown.

### Basic Periodic Task Pattern

```typescript
import { setTimeout, setInterval } from 'timers/promises';

class PeriodicTask {
  private controller: AbortController;
  private intervalId: NodeJS.Timeout | null = null;
  private isRunning = false;
  
  constructor(
    private name: string,
    private intervalMs: number,
    private task: () => Promise<void>
  ) {
    this.controller = new AbortController();
  }
  
  async start(): Promise<void> {
    if (this.isRunning) {
      logger.warn('Task already running', { name: this.name });
      return;
    }
    
    this.isRunning = true;
    logger.info('Starting periodic task', { 
      name: this.name, 
      intervalMs: this.intervalMs 
    });
    
    // Run immediately
    await this.runTask();
    
    // Schedule periodic execution
    this.intervalId = setInterval(
      () => this.runTask(),
      this.intervalMs
    );
  }
  
  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }
    
    logger.info('Stopping periodic task', { name: this.name });
    
    this.isRunning = false;
    this.controller.abort();
    
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
  
  private async runTask(): Promise<void> {
    if (this.controller.signal.aborted) {
      return;
    }
    
    try {
      logger.debug('Running task', { name: this.name });
      await this.task();
      logger.debug('Task completed', { name: this.name });
    } catch (error) {
      logger.error('Task failed', { 
        name: this.name, 
        error: error.message 
      });
    }
  }
}

// Usage
const contextScorer = new PeriodicTask(
  'context-scorer',
  5 * 60 * 1000, // 5 minutes
  async () => {
    await scoreContextItems();
  }
);

await contextScorer.start();
```

### Graceful Shutdown Pattern

```typescript
class BackgroundServiceManager {
  private tasks: PeriodicTask[] = [];
  private shutdownPromise: Promise<void> | null = null;
  
  register(task: PeriodicTask): void {
    this.tasks.push(task);
  }
  
  async startAll(): Promise<void> {
    logger.info('Starting all background services', { 
      count: this.tasks.length 
    });
    
    for (const task of this.tasks) {
      await task.start();
    }
    
    this.setupShutdownHandlers();
  }
  
  private setupShutdownHandlers(): void {
    const shutdown = async (signal: string) => {
      if (this.shutdownPromise) {
        // Shutdown already in progress
        await this.shutdownPromise;
        return;
      }
      
      logger.info('Received shutdown signal', { signal });
      
      this.shutdownPromise = this.stopAll();
      await this.shutdownPromise;
      
      logger.info('Graceful shutdown complete');
      process.exit(0);
    };
    
    process.on('SIGINT', () => shutdown('SIGINT'));
    process.on('SIGTERM', () => shutdown('SIGTERM'));
  }
  
  async stopAll(): Promise<void> {
    logger.info('Stopping all background services');
    
    // Stop all tasks in parallel
    await Promise.all(
      this.tasks.map(task => task.stop())
    );
    
    logger.info('All background services stopped');
  }
}

// Usage
const manager = new BackgroundServiceManager();

manager.register(new PeriodicTask('context-scorer', 5 * 60 * 1000, scoreContext));
manager.register(new PeriodicTask('context-pruner', 10 * 60 * 1000, pruneContext));
manager.register(new PeriodicTask('session-archiver', 60 * 60 * 1000, archiveSessions));

await manager.startAll();
```

### AbortController Integration

```typescript
class AbortableTask {
  private controller: AbortController;
  
  constructor(
    private name: string,
    private intervalMs: number,
    private task: (signal: AbortSignal) => Promise<void>
  ) {
    this.controller = new AbortController();
  }
  
  async start(): Promise<void> {
    while (!this.controller.signal.aborted) {
      try {
        // Run task with abort signal
        await this.task(this.controller.signal);
        
        // Wait for interval (abortable)
        await setTimeout(this.intervalMs, undefined, {
          signal: this.controller.signal
        });
      } catch (error) {
        if (error.name === 'AbortError') {
          logger.info('Task aborted', { name: this.name });
          break;
        }
        
        logger.error('Task error', { name: this.name, error });
        
        // Wait before retry (abortable)
        try {
          await setTimeout(this.intervalMs, undefined, {
            signal: this.controller.signal
          });
        } catch {
          break;
        }
      }
    }
  }
  
  stop(): void {
    this.controller.abort();
  }
}

// Task implementation with AbortSignal
async function scoreContext(signal: AbortSignal): Promise<void> {
  // Check if aborted before starting
  if (signal.aborted) {
    throw new Error('Task aborted');
  }
  
  // Set up abort listener for cleanup
  const cleanup = () => {
    logger.info('Cleaning up context scorer');
    // Release resources
  };
  
  signal.addEventListener('abort', cleanup);
  
  try {
    const items = await loadContextItems();
    
    for (const item of items) {
      // Check abort signal periodically
      if (signal.aborted) {
        throw new Error('Task aborted during processing');
      }
      
      await scoreItem(item);
    }
  } finally {
    signal.removeEventListener('abort', cleanup);
  }
}
```

### Resource Cleanup Pattern

```typescript
class ResourceManager {
  private resources: Array<{ name: string; cleanup: () => Promise<void> }> = [];
  
  register(name: string, cleanup: () => Promise<void>): void {
    this.resources.push({ name, cleanup });
  }
  
  async cleanupAll(): Promise<void> {
    logger.info('Cleaning up resources', { count: this.resources.length });
    
    const results = await Promise.allSettled(
      this.resources.map(async ({ name, cleanup }) => {
        try {
          logger.debug('Cleaning up resource', { name });
          await cleanup();
          logger.debug('Resource cleaned up', { name });
        } catch (error) {
          logger.error('Resource cleanup failed', { name, error });
          throw error;
        }
      })
    );
    
    const failed = results.filter(r => r.status === 'rejected');
    if (failed.length > 0) {
      logger.warn('Some resources failed to clean up', { 
        failed: failed.length,
        total: this.resources.length
      });
    }
  }
}

// Usage
const resourceManager = new ResourceManager();

// Register database
const db = new Database('.context/sessions.db');
resourceManager.register('database', async () => {
  db.close();
});

// Register chroma client
const chroma = new ChromaClient();
resourceManager.register('chroma', async () => {
  // Chroma doesn't require explicit close, but good practice
  await chroma.reset(); // Optional
});

// Register file watchers, etc.
// ...

// On shutdown
await resourceManager.cleanupAll();
```

### Non-Blocking Background Jobs

```typescript
class BackgroundJobQueue {
  private queue: Array<() => Promise<void>> = [];
  private isProcessing = false;
  private controller: AbortController;
  
  constructor(private concurrency: number = 1) {
    this.controller = new AbortController();
  }
  
  enqueue(job: () => Promise<void>): void {
    this.queue.push(job);
    
    if (!this.isProcessing) {
      this.process();
    }
  }
  
  private async process(): Promise<void> {
    this.isProcessing = true;
    
    while (this.queue.length > 0 && !this.controller.signal.aborted) {
      const batch = this.queue.splice(0, this.concurrency);
      
      await Promise.all(
        batch.map(async (job) => {
          try {
            await job();
          } catch (error) {
            logger.error('Background job failed', { error });
          }
        })
      );
    }
    
    this.isProcessing = false;
  }
  
  stop(): void {
    this.controller.abort();
    this.queue = [];
  }
}

// Usage
const jobQueue = new BackgroundJobQueue(3); // 3 concurrent jobs

// Enqueue jobs without blocking
jobQueue.enqueue(async () => {
  await generateEmbeddings(documents);
});

jobQueue.enqueue(async () => {
  await extractDiscoveries(session);
});

// Jobs run in background
```

### Context Scorer Example

```typescript
class ContextScorer extends PeriodicTask {
  constructor(
    private contextStore: ContextStore,
    intervalMs: number = 5 * 60 * 1000 // 5 minutes
  ) {
    super(
      'context-scorer',
      intervalMs,
      () => this.scoreAllItems()
    );
  }
  
  private async scoreAllItems(): Promise<void> {
    const items = await this.contextStore.getAllItems();
    
    logger.info('Scoring context items', { count: items.length });
    
    const now = new Date();
    const updatedItems = items.map(item => ({
      ...item,
      score: calculateContextScore(item.lastAccessedAt, item.accessCount, now)
    }));
    
    await this.contextStore.updateScores(updatedItems);
    
    logger.info('Context scoring complete', { 
      count: updatedItems.length,
      avgScore: average(updatedItems.map(i => i.score))
    });
  }
}

// Start scorer
const scorer = new ContextScorer(contextStore);
await scorer.start();
```

### Context Pruner Example

```typescript
class ContextPruner extends PeriodicTask {
  constructor(
    private contextStore: ContextStore,
    private threshold: number = 0.8, // 80%
    intervalMs: number = 10 * 60 * 1000 // 10 minutes
  ) {
    super(
      'context-pruner',
      intervalMs,
      () => this.pruneIfNeeded()
    );
  }
  
  private async pruneIfNeeded(): Promise<void> {
    const stats = await this.contextStore.getStats();
    const utilizationPct = stats.currentSize / stats.maxSize;
    
    logger.debug('Context window utilization', { 
      utilizationPct: utilizationPct * 100,
      threshold: this.threshold * 100
    });
    
    if (utilizationPct >= this.threshold) {
      logger.info('Context window above threshold, pruning', {
        currentSize: stats.currentSize,
        maxSize: stats.maxSize,
        utilizationPct: utilizationPct * 100
      });
      
      const pruned = await this.contextStore.pruneLowestScored(0.3); // Prune 30%
      
      logger.info('Context pruning complete', { 
        prunedCount: pruned.length,
        newSize: stats.currentSize - pruned.reduce((sum, p) => sum + p.size, 0)
      });
    }
  }
}

// Start pruner
const pruner = new ContextPruner(contextStore);
await pruner.start();
```

### Best Practices

1. **Use AbortController** - Standard pattern for cancellation
2. **Handle errors gracefully** - Don't crash entire service on task error
3. **Log comprehensively** - Every task start, completion, error
4. **Implement graceful shutdown** - Wait for tasks to complete
5. **Clean up resources** - Close DB connections, file handles, etc.
6. **Use Promise.allSettled** - Don't fail all cleanups if one fails
7. **Avoid blocking operations** - Use async/await throughout
8. **Set up SIGINT/SIGTERM handlers** - Essential for Docker, systemd
9. **Use queue for non-critical jobs** - Prevents blocking critical tasks
10. **Monitor task duration** - Log how long tasks take

### Implementation Recommendations

```typescript
// Infrastructure layer - Background service registry
export class BackgroundServices {
  private services: Map<string, PeriodicTask> = [];
  private manager: BackgroundServiceManager;
  
  constructor(
    private contextStore: ContextStore,
    private sessionStore: SessionStore,
    private embeddingService: EmbeddingService
  ) {
    this.manager = new BackgroundServiceManager();
  }
  
  async initialize(): Promise<void> {
    // Context scorer - every 5 minutes
    this.manager.register(
      new ContextScorer(this.contextStore, 5 * 60 * 1000)
    );
    
    // Context pruner - every 10 minutes
    this.manager.register(
      new ContextPruner(this.contextStore, 0.8, 10 * 60 * 1000)
    );
    
    // Session archiver - every hour
    this.manager.register(
      new PeriodicTask(
        'session-archiver',
        60 * 60 * 1000,
        async () => {
          await this.sessionStore.archiveOldSessions(30); // 30 days
        }
      )
    );
    
    // Embeddings generator - every 15 minutes
    this.manager.register(
      new PeriodicTask(
        'embeddings-generator',
        15 * 60 * 1000,
        async () => {
          const pending = await this.contextStore.getPendingEmbeddings();
          if (pending.length > 0) {
            await this.embeddingService.generateBatch(pending);
          }
        }
      )
    );
    
    await this.manager.startAll();
    
    logger.info('Background services initialized');
  }
  
  async shutdown(): Promise<void> {
    await this.manager.stopAll();
  }
}
```

### Gotchas & Considerations

- **setInterval drift**: Tasks run at intervals, not at exact times
- **Overlapping tasks**: If task takes longer than interval, use semaphore
- **Memory leaks**: Clear references in cleanup handlers
- **Error recovery**: Decide if task should retry on error
- **Testing**: Use dependency injection for easier testing
- **Monitoring**: Log task durations, errors, success rates
- **Process managers**: PM2, systemd handle restarts, don't duplicate logic

---

## Summary & Recommendations

### Technology Stack Overview

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **MCP Server** | @modelcontextprotocol/sdk | Official SDK, stdio transport, robust lifecycle |
| **Vector DB** | ChromaDB (npm) | Local-first, metadata filtering, batch operations |
| **Relational DB** | bun:sqlite | Native to Bun, 3-6x faster, zero dependencies |
| **AST Parser** | @babel/parser + @babel/traverse | Mature, full TS support, visitor pattern |
| **Background Services** | setInterval + AbortController | Built-in, simple, clean shutdown |
| **Embeddings** | OpenAI text-embedding-3-small | Cost-effective, 1536 dims, batch support |

### Key Architectural Patterns

#### 1. Onion Architecture Mapping

```
Infrastructure Layer (I/O, External):
├── MCP Server (stdio transport)
├── ChromaDB adapter
├── SQLite adapter
├── File system scanner
├── OpenAI embeddings client
└── Background services

Application Layer (Orchestration):
├── Context search use case
├── Discovery extraction service
├── Session management service
└── Context enrichment service

Domain Layer (Pure Logic):
├── Context scoring calculations
├── Dependency analysis
├── Discovery pattern matching
└── Data models
```

#### 2. Functional Programming

- **Pure functions in domain**: All scoring, filtering, calculation logic
- **Actions in infrastructure**: All I/O, database, API calls
- **Immutability**: Use spread operators, map/filter/reduce
- **Copy-on-write**: Never mutate inputs

#### 3. Error Handling

- **MCP errors**: Use McpError with appropriate error codes
- **Tool errors**: Return in tool result, not as protocol errors
- **Database errors**: Catch and log, provide meaningful messages
- **Graceful degradation**: Continue serving even if background service fails

#### 4. Performance

- **SQLite**: WAL mode, transactions, prepared statements, indexes
- **ChromaDB**: Batch insertions, metadata pre-filtering, tune HNSW params
- **Embeddings**: Batch API, proper chunking (1000 tokens), cache when possible
- **Background**: Non-blocking async, AbortController for cancellation

### Critical Configuration Checklist

```typescript
// ✅ Enable WAL mode for SQLite
db.exec('PRAGMA journal_mode = WAL;');

// ✅ Configure ChromaDB collection
const collection = await client.createCollection({
  name: 'context-embeddings',
  metadata: {
    hnsw_batch_size: 100,
    hnsw_sync_threshold: 1000
  }
});

// ✅ Set up graceful shutdown
process.on('SIGINT', async () => {
  await shutdown();
});

process.on('SIGTERM', async () => {
  await shutdown();
});

// ✅ Use AbortController for cancellation
const controller = new AbortController();
await longTask(controller.signal);

// ✅ Batch embeddings generation
const batches = create_batches(client, ids, embeddings, metadatas, documents);
```

### Testing Strategy

1. **Domain layer (100% coverage)**: Pure functions, easy to test
2. **Application layer (95% coverage)**: Use cases with mocked adapters
3. **Infrastructure layer (80% coverage)**: Mock external dependencies

### Next Steps for Implementation

1. ✅ **Read constitution.md** - Understand principles
2. ✅ **Read spec.md** - Understand requirements
3. ⏭️ **Use /plan** - Create technical implementation plan
4. ⏭️ **Use /tasks** - Break into actionable tasks
5. ⏭️ **Use /analyze** - Validate consistency
6. ⏭️ **Use /implement** - Build with TDD

---

**END OF RESEARCH DOCUMENT**
