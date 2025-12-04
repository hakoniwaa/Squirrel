# Data Model: Context Tool MVP

**Date**: 2025-01-15  
**Purpose**: Define all data structures and persistence schemas  
**Status**: Complete

---

## Overview

This document defines all data models for the Context Tool MVP, organized by layer (Domain, Storage) following onion architecture principles. Domain models are pure TypeScript interfaces, while storage schemas define database structures.

---

## Domain Models (Pure TypeScript)

### ProjectContext

High-level project metadata and structure.

```typescript
interface ProjectContext {
  version: string;                    // Schema version (e.g., "1.0")
  project: {
    name: string;                     // Project name (from package.json or dir)
    type: 'web-app' | 'api' | 'cli' | 'library' | 'fullstack';
    path: string;                     // Absolute path to project root
  };
  tech: {
    stack: string[];                  // ["Next.js 14", "Express", "TypeScript"]
    runtime: string;                  // "Node.js 20", "Bun 1.0"
    packageManager: 'npm' | 'yarn' | 'pnpm' | 'bun';
  };
  architecture: {
    pattern: 'feature-based' | 'layered' | 'modular' | 'monorepo' | 'unknown';
    description: string;              // Human-readable description
  };
  modules: Record<string, ModuleContext>;
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    lastScanAt: Date;
  };
}
```

### ModuleContext

Domain/feature module within the project.

```typescript
interface ModuleContext {
  name: string;                       // "auth", "users", "payments"
  description: string;                // Human-readable description
  keyFiles: KeyFile[];                // Important files in this module
  patterns: string[];                 // ["Use JWT in httpOnly cookies"]
  businessRules: string[];            // ["Sessions expire after 7 days"]
  commonIssues: Issue[];              // Known issues and solutions
  dependencies: string[];             // Other modules this depends on
}

interface KeyFile {
  path: string;                       // Relative to project root
  role: 'entry' | 'config' | 'core' | 'test';
  description?: string;
}

interface Issue {
  description: string;                // "Token refresh race condition"
  solution: string;                   // "Use mutex lock in TokenManager"
  sessionId: string;                  // Reference to session where solved
  discoveredAt: Date;
}
```

### Session

Coding session with tracked activity.

```typescript
interface Session {
  id: string;                         // UUID
  projectId: string;                  // Reference to project
  startedAt: Date;
  endedAt?: Date;
  status: 'active' | 'completed' | 'archived';
  filesAccessed: FileAccess[];
  topics: string[];                   // ["auth bug fix", "token refresh"]
  metadata: {
    duration?: number;                // Milliseconds
    toolCallsCount: number;
    discoveryCount: number;
  };
}

interface FileAccess {
  path: string;                       // Relative to project root
  accessCount: number;
  firstAccessedAt: Date;
  lastAccessedAt: Date;
}
```

### Discovery

Learning extracted from a session.

```typescript
interface Discovery {
  id: string;                         // UUID
  sessionId: string;                  // Reference to session
  type: 'pattern' | 'rule' | 'decision' | 'issue';
  content: string;                    // The actual discovery text
  module?: string;                    // Associated module (if identified)
  context: {
    extractedFrom: string;            // "session conversation" | "code comment"
    confidence: number;               // 0.0 - 1.0 (regex match = 1.0)
  };
  embedding?: {
    id: string;                       // Reference to Chroma
    model: string;                    // "text-embedding-3-small"
    dimensions: number;               // 1536
  };
  createdAt: Date;
}
```

### ContextItem

Scored item in the context window.

```typescript
interface ContextItem {
  id: string;
  type: 'file' | 'module' | 'discovery' | 'session';
  content: string;                    // Actual text content
  metadata: {
    source: string;                   // File path or resource URI
    module?: string;
    sessionId?: string;
  };
  scoring: {
    score: number;                    // 0.0 - 1.0 (calculated)
    recencyFactor: number;            // 0.0 - 1.0
    accessFactor: number;             // 0.0 - 1.0
    lastAccessedAt: Date;
    accessCount: number;
  };
  tokens: number;                     // Estimated token count
  status: 'active' | 'archived';
}
```

### Config

Application configuration.

```typescript
interface Config {
  storage: {
    contextDir: string;               // Default: ".context"
    dbPath: string;                   // Default: ".context/sessions.db"
    chromaPath: string;               // Default: ".context/chroma"
  };
  embeddings: {
    provider: 'openai';
    model: string;                    // "text-embedding-3-small"
    apiKey: string;                   // From env var
    batchSize: number;                // Default: 100
  };
  services: {
    scorerInterval: number;           // Default: 300000 (5 min)
    prunerThreshold: number;          // Default: 0.8 (80%)
    sessionTimeout: number;           // Default: 1800000 (30 min)
    embeddingsInterval: number;       // Default: 900000 (15 min)
  };
  contextWindow: {
    maxTokens: number;                // Default: 100000
    pruneTarget: number;              // Default: 0.64 (64% after prune)
  };
  logging: {
    level: 'debug' | 'info' | 'warn' | 'error';
    file?: string;
  };
}
```

---

## Storage Schemas

### SQLite Database (`sessions.db`)

#### Sessions Table

```sql
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  started_at INTEGER NOT NULL,                    -- Unix timestamp (ms)
  ended_at INTEGER,                               -- Unix timestamp (ms)
  status TEXT NOT NULL CHECK(status IN ('active', 'completed', 'archived')),
  files_accessed TEXT NOT NULL DEFAULT '[]',      -- JSON array of FileAccess
  topics TEXT NOT NULL DEFAULT '[]',              -- JSON array of strings
  metadata TEXT NOT NULL DEFAULT '{}',            -- JSON object
  created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
);

CREATE INDEX idx_sessions_project ON sessions(project_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_started ON sessions(started_at DESC);
```

**Validation Rules:**
- `id`: UUID v4 format
- `status`: One of 'active', 'completed', 'archived'
- `files_accessed`: Valid JSON array
- `topics`: Valid JSON array
- `metadata`: Valid JSON object

#### Discoveries Table

```sql
CREATE TABLE IF NOT EXISTS discoveries (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('pattern', 'rule', 'decision', 'issue')),
  content TEXT NOT NULL,
  module TEXT,
  context_json TEXT NOT NULL DEFAULT '{}',        -- JSON object
  embedding_id TEXT,                              -- Reference to Chroma
  embedding_model TEXT,
  created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
  
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_discoveries_session ON discoveries(session_id);
CREATE INDEX idx_discoveries_type ON discoveries(type);
CREATE INDEX idx_discoveries_module ON discoveries(module);
CREATE INDEX idx_discoveries_created ON discoveries(created_at DESC);
```

**Validation Rules:**
- `id`: UUID v4 format
- `session_id`: Must exist in sessions table
- `type`: One of 'pattern', 'rule', 'decision', 'issue'
- `content`: Non-empty string
- `context_json`: Valid JSON object

#### Context Items Table

```sql
CREATE TABLE IF NOT EXISTS context_items (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK(type IN ('file', 'module', 'discovery', 'session')),
  content TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',       -- JSON object
  score REAL NOT NULL DEFAULT 0.0,
  recency_factor REAL NOT NULL DEFAULT 0.0,
  access_factor REAL NOT NULL DEFAULT 0.0,
  last_accessed_at INTEGER NOT NULL,
  access_count INTEGER NOT NULL DEFAULT 0,
  tokens INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK(status IN ('active', 'archived')),
  created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
);

CREATE INDEX idx_context_items_type ON context_items(type);
CREATE INDEX idx_context_items_status ON context_items(status);
CREATE INDEX idx_context_items_score ON context_items(score DESC);
CREATE INDEX idx_context_items_last_accessed ON context_items(last_accessed_at DESC);
```

**Validation Rules:**
- `id`: UUID v4 format
- `type`: One of 'file', 'module', 'discovery', 'session'
- `score`: 0.0 to 1.0
- `recency_factor`: 0.0 to 1.0
- `access_factor`: 0.0 to 1.0
- `status`: One of 'active', 'archived'

---

### Chroma Vector Database

#### Collection: `context-embeddings`

```typescript
// Collection metadata
{
  name: 'context-embeddings',
  metadata: {
    description: 'Project context embeddings',
    'hnsw:space': 'cosine',           // Cosine similarity
    'hnsw:construction_ef': 200,
    'hnsw:search_ef': 100,
    'hnsw:M': 16,
    'hnsw:batch_size': 100,
    'hnsw:sync_threshold': 1000,
  }
}

// Document structure
{
  ids: string[],                      // Discovery IDs
  embeddings: number[][],             // 1536-dimensional vectors
  metadatas: Array<{
    type: 'pattern' | 'rule' | 'decision' | 'issue',
    module?: string,
    session: string,
    project: string,
    date: string,                     // ISO 8601
  }>,
  documents: string[],                // Original discovery content
}
```

**Metadata Query Operators:**
- `$eq`, `$ne`: Equality/inequality
- `$gt`, `$gte`, `$lt`, `$lte`: Comparisons
- `$in`, `$nin`: Set membership
- `$and`, `$or`, `$not`: Logical operators

**Example Query:**
```typescript
await collection.query({
  queryEmbeddings: [queryEmbedding],
  nResults: 5,
  where: {
    $and: [
      { type: { $eq: 'pattern' } },
      { module: { $eq: 'auth' } },
    ],
  },
  include: ['documents', 'metadatas', 'distances'],
});
```

---

### YAML Files

#### `project.yaml`

```yaml
version: "1.0"

project:
  name: "My SaaS App"
  type: "fullstack"
  path: "/Users/dev/projects/my-saas"

tech:
  stack:
    - "Next.js 14"
    - "Express 4"
    - "TypeScript 5"
  runtime: "Node.js 20"
  packageManager: "pnpm"

architecture:
  pattern: "feature-based"
  description: "Feature modules with shared infrastructure"

modules:
  auth:
    name: "auth"
    description: "Authentication and authorization"
    keyFiles:
      - path: "src/server/auth/AuthService.ts"
        role: "core"
      - path: "src/server/auth/TokenManager.ts"
        role: "core"
    patterns:
      - "Use JWT tokens in httpOnly cookies"
      - "Implement token refresh with mutex locks"
    businessRules:
      - "Sessions expire after 7 days"
      - "Require 2FA for admin users"
    commonIssues:
      - description: "Token refresh race condition"
        solution: "Use mutex lock in TokenManager"
        sessionId: "session-123"
        discoveredAt: "2025-01-15T10:30:00Z"
    dependencies:
      - "users"

  users:
    name: "users"
    description: "User management and profiles"
    keyFiles:
      - path: "src/server/users/UserRepository.ts"
        role: "core"
    patterns:
      - "Use repository pattern for data access"
    businessRules:
      - "Email must be unique"
    commonIssues: []
    dependencies: []

metadata:
  createdAt: "2025-01-15T08:00:00Z"
  updatedAt: "2025-01-15T18:00:00Z"
  lastScanAt: "2025-01-15T08:00:00Z"
```

**Validation Schema (Zod):**
```typescript
const ProjectContextSchema = z.object({
  version: z.string(),
  project: z.object({
    name: z.string().min(1),
    type: z.enum(['web-app', 'api', 'cli', 'library', 'fullstack']),
    path: z.string().min(1),
  }),
  tech: z.object({
    stack: z.array(z.string()),
    runtime: z.string(),
    packageManager: z.enum(['npm', 'yarn', 'pnpm', 'bun']),
  }),
  architecture: z.object({
    pattern: z.enum(['feature-based', 'layered', 'modular', 'monorepo', 'unknown']),
    description: z.string(),
  }),
  modules: z.record(z.object({
    name: z.string(),
    description: z.string(),
    keyFiles: z.array(z.object({
      path: z.string(),
      role: z.enum(['entry', 'config', 'core', 'test']),
      description: z.string().optional(),
    })),
    patterns: z.array(z.string()),
    businessRules: z.array(z.string()),
    commonIssues: z.array(z.object({
      description: z.string(),
      solution: z.string(),
      sessionId: z.string(),
      discoveredAt: z.string().datetime(),
    })),
    dependencies: z.array(z.string()),
  })),
  metadata: z.object({
    createdAt: z.string().datetime(),
    updatedAt: z.string().datetime(),
    lastScanAt: z.string().datetime(),
  }),
});
```

---

## Data Relationships

### Entity Relationship Diagram

```
Project (YAML)
    │
    ├─── 1:N ──> Session (SQLite)
    │                │
    │                └─── 1:N ──> Discovery (SQLite)
    │                                  │
    │                                  └─── 1:1 ──> Embedding (Chroma)
    │
    └─── 1:N ──> Module (YAML)
                     │
                     └─── 1:N ──> Issue (YAML)

ContextItem (SQLite) references:
  - File (filesystem path)
  - Module (YAML key)
  - Discovery (SQLite ID)
  - Session (SQLite ID)
```

### Data Flow

1. **Initialization:**
   - Scan project → Generate `ProjectContext` → Save to `project.yaml`

2. **Active Session:**
   - MCP connection → Create `Session` → Save to SQLite
   - File access → Update `FileAccess` → Calculate scores → Update `ContextItem`

3. **Session End:**
   - MCP disconnect → Update `Session.endedAt` and `status`
   - Extract discoveries → Save to `discoveries` table
   - Generate embeddings → Save to Chroma → Link to discoveries

4. **Context Enrichment:**
   - Load `project.yaml` → Map discoveries to modules → Update module sections → Save `project.yaml`

5. **Context Pruning:**
   - Load all `ContextItem` where `status = 'active'`
   - Calculate scores → Sort → Archive bottom 20% → Update `status = 'archived'`

---

## State Transitions

### Session States

```
[MCP Connect] → active
active → [MCP Disconnect OR 30min inactivity] → completed
completed → [Enrichment done] → completed
completed → [After 7 days] → archived
```

### Context Item States

```
[Created] → active
active → [Score < threshold AND window > 80%] → archived
archived → [Never deleted, searchable via RAG]
```

### Discovery Lifecycle

```
[Session End] → Extract regex patterns → Create Discovery
Discovery → [Background service] → Generate embedding → Link to Chroma
Discovery → [Enrichment] → Add to Module in project.yaml
```

---

## Storage Estimates

### Typical Project (500 files)

**project.yaml:**
- Size: ~50-100 KB
- Modules: 10-20
- Patterns: 50-100
- Rules: 20-50
- Issues: 10-30

**sessions.db:**
- Sessions: ~100-200 (over 2 weeks)
- Discoveries: ~300-600 (3-5 per session)
- Context items: ~200-500
- Total size: <10 MB

**Chroma:**
- Embeddings: ~300-600 vectors
- Dimensions: 1536 per vector
- Size: ~5-10 MB

**Total: ~15-20 MB per project**

---

## Performance Considerations

### Indexing Strategy

**SQLite Indexes:**
- `sessions(project_id)` - Filter by project
- `sessions(status)` - Filter active/archived
- `sessions(started_at DESC)` - Recent first
- `discoveries(session_id)` - Join with sessions
- `discoveries(type)` - Filter by type
- `discoveries(module)` - Filter by module
- `context_items(score DESC)` - Pruning queries
- `context_items(status)` - Active/archived filter

**Chroma Metadata:**
- Index on `type` for filtering
- Index on `module` for filtering
- Index on `session` for traceability
- Index on `date` for recency

### Query Patterns

**Hot Paths (optimize):**
- Load active context items by score DESC
- Search embeddings with metadata filters
- Update context item scores (batch)
- Insert discoveries (batch with transaction)

**Cold Paths (acceptable slower):**
- Archive old sessions
- Full project scan
- Generate embeddings (async background)

---

## Validation Rules

### Domain Constraints

**Project:**
- Name: 1-100 characters
- Type: Must be one of enum values
- Path: Must be valid absolute path

**Session:**
- ID: UUID v4 format
- Status: Must progress through states (no backward)
- Duration: >= 0 milliseconds

**Discovery:**
- Content: 10-1000 characters
- Type: Must be one of enum values
- Confidence: 0.0 to 1.0

**ContextItem:**
- Score: 0.0 to 1.0
- Tokens: >= 0
- Access count: >= 0

### Storage Constraints

**SQLite:**
- Foreign keys enforced (CASCADE delete)
- CHECK constraints on enum fields
- NOT NULL on required fields
- DEFAULT values for timestamps

**Chroma:**
- Embedding dimensions: Must be 1536
- IDs: Must be unique
- Metadata: Must be valid JSON

**YAML:**
- Must pass Zod schema validation
- Dates: Must be ISO 8601 format
- Arrays: No duplicates in patterns/rules

---

## Migration Strategy

### Schema Versioning

**Version in project.yaml:**
```yaml
version: "1.0"
```

**Version in SQLite:**
```sql
CREATE TABLE IF NOT EXISTS schema_version (
  version TEXT PRIMARY KEY,
  applied_at INTEGER NOT NULL
);

INSERT INTO schema_version (version, applied_at) 
VALUES ('1.0', unixepoch() * 1000);
```

**Migration Path:**
- 1.0 → 1.1: Add new fields with defaults
- 1.1 → 2.0: Breaking changes (rare, requires full re-init)

### Backward Compatibility

**Rules:**
- Never remove fields (deprecate instead)
- Always provide defaults for new fields
- Validate on load, migrate on save
- Keep old data readable

---

**END OF DATA MODEL**
