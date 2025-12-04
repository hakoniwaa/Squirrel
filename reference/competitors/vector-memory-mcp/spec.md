# vector-memory-mcp — MVP Specification

## Overview

A simple, zero-configuration RAG memory server for MCP clients (like Claude Code). It gives AI the ability to recall previous information without having to hold all of that information in context.

## Design Philosophy

**Config Optional**: Sensible defaults, everything works out of the box. Configuration is available for those who want it, but never required.

## Deployment

- **Single command startup**: `bunx vector-memory-mcp`
- **No repo clone required** — published as an NPM package
- **Local LanceDB file** — default location works automatically, configurable via environment variable if desired

## Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | TypeScript | Type safety, modern ecosystem |
| Runtime | Bun | Fast startup, great DX |
| MCP SDK | `@modelcontextprotocol/sdk` | Official TypeScript SDK |
| Embeddings | @huggingface/transformers | Runs locally in JS/TS, no Python dependency needed |
| Vector Storage | LanceDB | Fast, local, efficient vector search |

## Data Model

### Memory
```typescript
interface Memory {
  id: string;                     // Unique identifier (UUID)
  content: string;                // The text content of the memory
  embedding: number[];            // Vector embedding (384 dimensions for MiniLM-v6)
  metadata: Record<string, any>;  // Flexible key-value metadata
  created_at: Date;               // When the memory was created
  updated_at: Date;               // When the memory was last modified
}
```

## MCP Tools

Four tools total:

### 1. `store_memory`

Create a new memory.

**Parameters:**
- `content` (string, required): The text content to store
- `metadata` (object, optional): Key-value pairs for metadata

**Returns:**
- `id`: The ID of the created memory

---

### 2. `delete_memory`

Delete a memory.

**Parameters:**
- `id` (string, required): The ID of the memory to delete

**Returns:**
- `success`: boolean

---

### 3. `search_memories`

Semantic search for relevant memories.

**Parameters:**
- `query` (string, required): The search query
- `limit` (integer, optional, default 10): Maximum number of results to return

**Returns:**
- Array of memories, ranked by semantic similarity

---

### 4. `get_memory`

Retrieve a specific memory by ID.

**Parameters:**
- `id` (string, required): The ID of the memory to retrieve

**Returns:**
- The memory object, or null if not found

---

## Project Structure
```
vector-memory-mcp/
├── package.json            # Package config, dependencies
├── README.md               # User-facing documentation
├── src/
│   ├── index.ts            # Entry point
│   ├── config/             # Configuration management
│   ├── db/                 # LanceDB storage layer
│   ├── services/
│   │   ├── embeddings.service.ts  # Embeddings via @huggingface/transformers
│   │   └── memory.service.ts      # Core memory operations
│   └── mcp/
│       ├── server.ts       # MCP server setup
│       ├── tools.ts        # MCP tool definitions
│       └── handlers.ts     # Tool request handlers
└── tests/
    └── ...
```

## Configuration

All configuration via environment variables, all optional:

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_MEMORY_DB_PATH` | `~/.local/share/vector-memory-mcp/memories.db` | Path to LanceDB database |
| `VECTOR_MEMORY_MODEL` | `Xenova/all-MiniLM-L6-v2` | Embedding model |

## Dependencies
```json
{
  "dependencies": {
    "@lancedb/lancedb": "^0.4.0",
    "@modelcontextprotocol/sdk": "^0.6.0",
    "@huggingface/transformers": "^3.8.0",
    "apache-arrow": "^14.0.0"
  }
}
```

## Success Criteria

MVP is complete when:

1. `bunx vector-memory-mcp` starts the server with zero configuration
2. All four MCP tools work correctly
3. Semantic search returns relevant results