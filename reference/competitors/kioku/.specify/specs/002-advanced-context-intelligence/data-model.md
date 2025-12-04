# Data Models & Schema Design

**Feature**: Kioku v2.0 - Advanced Context Intelligence  
**Branch**: `002-advanced-context-intelligence`  
**Date**: 2025-10-09  
**Status**: Complete

---

## Overview

This document defines all data structures, database schemas, and domain models for Kioku v2.0. Models follow the Onion Architecture principle: domain models are pure (no I/O), with infrastructure adapters handling persistence.

---

## Domain Models (Pure TypeScript)

### 1. CodeChunk

**Purpose**: Represents a discrete unit of code (function, class, method) for function-level search.

**Location**: `src/domain/models/CodeChunk.ts`

```typescript
export enum ChunkType {
  FUNCTION_DECLARATION = 'function',
  FUNCTION_EXPRESSION = 'function_expr',
  ARROW_FUNCTION = 'arrow_function',
  CLASS_DECLARATION = 'class',
  CLASS_METHOD = 'method',
  OBJECT_METHOD = 'object_method',
  INTERFACE = 'interface',
  TYPE_ALIAS = 'type',
  EXPORTED_DECLARATION = 'export',
}

export interface CodeChunk {
  // Identity
  id: string;                      // UUID v4
  filePath: string;                // Absolute path
  
  // Chunk boundaries
  type: ChunkType;
  name: string;                    // Function/class name or <anonymous>
  startLine: number;               // Start line (with context)
  endLine: number;                 // End line (with context)
  contentStartLine: number;        // Actual code start (without context)
  contentEndLine: number;          // Actual code end (without context)
  
  // Content
  code: string;                    // Source code with context envelope
  
  // Hierarchy
  parentChunkId?: string;          // For nested functions/methods
  nestingLevel: number;            // 0 = top-level, 1+ = nested
  scopePath: string[];             // ['ClassName', 'methodName', 'closureFn']
  
  // Metadata
  metadata: {
    signature?: string;            // Function signature
    jsDoc?: string;                // JSDoc comment
    isExported: boolean;           // Is this exported?
    isAsync: boolean;              // Async function?
    parameters?: string[];         // Parameter names
    returnType?: string;           // TypeScript return type
    complexity?: number;           // Cyclomatic complexity (optional)
  };
  
  // Embeddings reference
  embeddingId?: string;            // Reference to Chroma embedding
  
  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}
```

---

### 2. GitCommit

**Purpose**: Represents a git commit with metadata for historical context.

**Location**: `src/domain/models/GitCommit.ts`

```typescript
export interface GitCommit {
  sha: string;                     // Full commit SHA (40 chars)
  shortSha: string;                // Short SHA (7 chars)
  author: {
    name: string;
    email: string;
  };
  date: Date;
  message: string;                 // Full commit message
  messageShort: string;            // First line of message
  filesChanged: string[];          // Array of file paths
  parentSha?: string;              // Parent commit SHA
}
```

---

### 3. GitBlame

**Purpose**: Line-by-line authorship information for a file.

**Location**: `src/domain/models/GitBlame.ts`

```typescript
export interface GitBlameLine {
  lineNumber: number;
  content: string;                 // Code content
  commit: {
    sha: string;
    shortSha: string;
    author: string;
    authorEmail: string;
    date: Date;
    message: string;               // Commit message excerpt
  };
}

export interface GitBlame {
  filePath: string;
  lines: GitBlameLine[];
  totalLines: number;
}
```

---

### 4. GitDiff

**Purpose**: Represents changes between two git references.

**Location**: `src/domain/models/GitDiff.ts`

```typescript
export enum ChangeType {
  ADDED = 'added',
  MODIFIED = 'modified',
  DELETED = 'deleted',
  RENAMED = 'renamed',
}

export interface FileDiff {
  filePath: string;
  oldPath?: string;                // For renames
  changeType: ChangeType;
  additions: number;               // Lines added
  deletions: number;               // Lines deleted
  diff: string;                    // Unified diff format
  isBinary: boolean;               // Is binary file?
}

export interface GitDiff {
  ref1: string;                    // First reference (commit/branch/tag)
  ref2?: string;                   // Second reference (if comparing two)
  files: FileDiff[];
  summary: {
    filesChanged: number;
    insertions: number;
    deletions: number;
  };
}
```

---

### 5. ChangeEvent

**Purpose**: Represents a file system change detected by file watcher.

**Location**: `src/domain/models/ChangeEvent.ts`

```typescript
export enum FileEventType {
  ADD = 'add',
  CHANGE = 'change',
  UNLINK = 'unlink',
  RENAME = 'rename',
}

export interface ChangeEvent {
  id: string;                      // UUID v4
  eventType: FileEventType;
  filePath: string;                // Absolute path
  oldPath?: string;                // For renames
  timestamp: Date;
  processed: boolean;              // Has this been handled?
  error?: string;                  // Error message if processing failed
}
```

---

### 6. RefinedDiscovery

**Purpose**: AI-enhanced discovery from session conversations.

**Location**: `src/domain/models/RefinedDiscovery.ts`

```typescript
export enum DiscoveryType {
  PATTERN = 'pattern',
  RULE = 'rule',
  DECISION = 'decision',
  ISSUE = 'issue',
  INSIGHT = 'insight',
}

export interface RefinedDiscovery {
  id: string;                      // UUID v4
  sessionId: string;               // Reference to session
  
  // Content
  rawContent: string;              // Original regex-extracted content
  refinedContent: string;          // AI-refined description
  type: DiscoveryType;
  
  // AI metadata
  confidence: number;              // 0-1 (only persist if >= 0.6)
  supportingEvidence: string;      // Message excerpt from conversation
  suggestedModule?: string;        // Module where this applies
  
  // Processing metadata
  aiModel: string;                 // e.g., "claude-3-sonnet-20240229"
  tokensUsed: number;
  processingTime: number;          // Milliseconds
  
  // Status
  accepted: boolean;               // User accepted/rejected
  appliedAt?: Date;                // When applied to project.yaml
  
  // Timestamps
  createdAt: Date;
  updatedAt: Date;
}
```

---

### 7. LinkedProject

**Purpose**: Represents a linked project in multi-project workspace.

**Location**: `src/domain/models/LinkedProject.ts`

```typescript
export enum LinkType {
  WORKSPACE = 'workspace',         // Part of same workspace (monorepo)
  DEPENDENCY = 'dependency',       // External dependency
}

export enum ProjectStatus {
  AVAILABLE = 'available',
  UNAVAILABLE = 'unavailable',     // Moved, deleted, permission denied
  INITIALIZING = 'initializing',   // Kioku init in progress
}

export interface LinkedProject {
  name: string;                    // User-friendly name
  path: string;                    // Absolute path to project root
  linkType: LinkType;
  status: ProjectStatus;
  lastAccessed: Date;
  
  // Metadata
  techStack?: string[];            // ['TypeScript', 'React', 'Node.js']
  moduleCount?: number;
  fileCount?: number;
}

export interface CrossReference {
  id: string;                      // UUID v4
  sourceProject: string;           // Source project name
  sourceFile: string;              // Source file path
  targetProject: string;           // Target project name
  targetFile: string;              // Target file path
  referenceType: 'import' | 'api_call' | 'type_usage';
  confidence: number;              // 0-1
  
  createdAt: Date;
}
```

---

### 8. SearchResult (Enhanced)

**Purpose**: Enhanced search result with ranking metadata.

**Location**: `src/domain/models/SearchResult.ts`

```typescript
export interface SearchResult {
  // Identity
  id: string;                      // Chunk ID or file ID
  type: 'chunk' | 'file';
  
  // Content
  filePath: string;
  content: string;                 // Chunk content or file excerpt
  
  // Location (for chunks)
  chunkName?: string;              // Function/class name
  startLine?: number;
  endLine?: number;
  
  // Scoring
  semanticScore: number;           // Base similarity score (0-1)
  recencyBoost: number;            // 1.0, 1.2, or 1.5
  moduleBoost: number;             // 1.0 or 1.3
  frequencyBoost: number;          // 1.0 to 1.5
  finalScore: number;              // Combined score
  
  // Metadata
  projectName?: string;            // For multi-project search
  lastAccessed?: Date;
  accessCount: number;
  
  // Context
  surroundingContext?: string;     // 3 lines before/after
}
```

---

## Database Schemas

### SQLite Database Schema

**Location**: `src/infrastructure/storage/migrations/`

#### Table: `chunks`

Stores code chunk metadata (embeddings stored in Chroma).

```sql
CREATE TABLE chunks (
  id TEXT PRIMARY KEY,             -- UUID v4
  file_path TEXT NOT NULL,
  type TEXT NOT NULL,              -- ChunkType enum value
  name TEXT NOT NULL,
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  content_start_line INTEGER NOT NULL,
  content_end_line INTEGER NOT NULL,
  code TEXT NOT NULL,
  parent_chunk_id TEXT,            -- Foreign key to chunks.id
  nesting_level INTEGER NOT NULL DEFAULT 0,
  scope_path TEXT,                 -- JSON array as string
  signature TEXT,
  js_doc TEXT,
  is_exported BOOLEAN NOT NULL DEFAULT 0,
  is_async BOOLEAN NOT NULL DEFAULT 0,
  parameters TEXT,                 -- JSON array as string
  return_type TEXT,
  complexity INTEGER,
  embedding_id TEXT,               -- Reference to Chroma
  created_at INTEGER NOT NULL,     -- Unix timestamp
  updated_at INTEGER NOT NULL,     -- Unix timestamp
  
  FOREIGN KEY (parent_chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);

CREATE INDEX idx_chunks_file_path ON chunks(file_path);
CREATE INDEX idx_chunks_type ON chunks(type);
CREATE INDEX idx_chunks_name ON chunks(name);
CREATE INDEX idx_chunks_parent ON chunks(parent_chunk_id);
CREATE INDEX idx_chunks_updated ON chunks(updated_at);
```

#### Table: `sessions` (Extended from v1.0)

Add new columns to existing sessions table.

```sql
-- v1.0 schema (existing)
-- id, started_at, ended_at, duration, context_window_tokens, status

-- v2.0 additions
ALTER TABLE sessions ADD COLUMN git_tools_used INTEGER DEFAULT 0;
ALTER TABLE sessions ADD COLUMN git_commits_queried TEXT;  -- JSON array
ALTER TABLE sessions ADD COLUMN ai_discoveries_count INTEGER DEFAULT 0;
ALTER TABLE sessions ADD COLUMN files_watched_changed INTEGER DEFAULT 0;
```

#### Table: `change_events`

Stores file watcher events for audit trail.

```sql
CREATE TABLE change_events (
  id TEXT PRIMARY KEY,             -- UUID v4
  event_type TEXT NOT NULL,        -- FileEventType enum
  file_path TEXT NOT NULL,
  old_path TEXT,                   -- For renames
  timestamp INTEGER NOT NULL,      -- Unix timestamp
  processed BOOLEAN NOT NULL DEFAULT 0,
  error TEXT,
  created_at INTEGER NOT NULL
);

CREATE INDEX idx_change_events_timestamp ON change_events(timestamp);
CREATE INDEX idx_change_events_processed ON change_events(processed);
CREATE INDEX idx_change_events_file_path ON change_events(file_path);
```

#### Table: `refined_discoveries`

Stores AI-refined discoveries.

```sql
CREATE TABLE refined_discoveries (
  id TEXT PRIMARY KEY,             -- UUID v4
  session_id TEXT NOT NULL,
  raw_content TEXT NOT NULL,
  refined_content TEXT NOT NULL,
  type TEXT NOT NULL,              -- DiscoveryType enum
  confidence REAL NOT NULL,        -- 0.0 to 1.0
  supporting_evidence TEXT NOT NULL,
  suggested_module TEXT,
  ai_model TEXT NOT NULL,
  tokens_used INTEGER NOT NULL,
  processing_time INTEGER NOT NULL,  -- Milliseconds
  accepted BOOLEAN NOT NULL DEFAULT 0,
  applied_at INTEGER,              -- Unix timestamp
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  
  FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_refined_discoveries_session ON refined_discoveries(session_id);
CREATE INDEX idx_refined_discoveries_confidence ON refined_discoveries(confidence);
CREATE INDEX idx_refined_discoveries_accepted ON refined_discoveries(accepted);
CREATE INDEX idx_refined_discoveries_created ON refined_discoveries(created_at);
```

#### Table: `linked_projects`

Stores multi-project workspace links.

```sql
CREATE TABLE linked_projects (
  name TEXT PRIMARY KEY,
  path TEXT NOT NULL UNIQUE,
  link_type TEXT NOT NULL,         -- LinkType enum
  status TEXT NOT NULL,            -- ProjectStatus enum
  last_accessed INTEGER NOT NULL,  -- Unix timestamp
  tech_stack TEXT,                 -- JSON array as string
  module_count INTEGER,
  file_count INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE INDEX idx_linked_projects_status ON linked_projects(status);
CREATE INDEX idx_linked_projects_last_accessed ON linked_projects(last_accessed);
```

#### Table: `cross_references`

Stores cross-project dependency references.

```sql
CREATE TABLE cross_references (
  id TEXT PRIMARY KEY,             -- UUID v4
  source_project TEXT NOT NULL,
  source_file TEXT NOT NULL,
  target_project TEXT NOT NULL,
  target_file TEXT NOT NULL,
  reference_type TEXT NOT NULL,    -- 'import' | 'api_call' | 'type_usage'
  confidence REAL NOT NULL,        -- 0.0 to 1.0
  created_at INTEGER NOT NULL,
  
  FOREIGN KEY (source_project) REFERENCES linked_projects(name) ON DELETE CASCADE,
  FOREIGN KEY (target_project) REFERENCES linked_projects(name) ON DELETE CASCADE
);

CREATE INDEX idx_cross_refs_source ON cross_references(source_project, source_file);
CREATE INDEX idx_cross_refs_target ON cross_references(target_project, target_file);
```

---

### ChromaDB Collections

#### Collection: `code_chunks`

Stores chunk-level embeddings (replaces file-level embeddings from v1.0).

```typescript
// Collection metadata
{
  name: 'code_chunks',
  metadata: {
    description: 'Function/class-level code embeddings for semantic search',
    model: 'text-embedding-3-small',
    dimensions: 1536,
  }
}

// Document structure
{
  id: 'chunk-uuid-v4',           // Matches chunks.id in SQLite
  embedding: number[],           // 1536-dimensional vector
  document: string,              // Chunk code with context
  metadata: {
    file_path: string,
    chunk_type: string,          // ChunkType
    chunk_name: string,
    start_line: number,
    end_line: number,
    project_name?: string,       // For multi-project
    last_accessed: number,       // Unix timestamp
    access_count: number,
  }
}
```

#### Collection: `file_embeddings` (Retained from v1.0)

Keep file-level embeddings as fallback when chunking fails.

```typescript
// Same structure as v1.0, no changes
```

---

### YAML Configuration Extensions

#### `.context/workspace.yaml` (New)

Stores multi-project workspace configuration.

```yaml
workspace:
  name: "My Full-Stack App"
  version: "2.0.0"
  
  projects:
    - name: "frontend"
      path: "/Users/user/projects/my-app/frontend"
      link_type: "workspace"
      status: "available"
      last_accessed: "2025-10-09T12:00:00Z"
    
    - name: "backend"
      path: "/Users/user/projects/my-app/backend"
      link_type: "workspace"
      status: "available"
      last_accessed: "2025-10-09T12:00:00Z"
  
  cross_references:
    - source: "frontend:/src/api/client.ts"
      target: "backend:/src/routes/api.ts"
      type: "api_call"
```

#### `.context/config.yaml` (Extended from v1.0)

Add v2.0 configuration sections.

```yaml
# v1.0 sections (existing)
embeddings:
  provider: "openai"
  model: "text-embedding-3-small"
  batchSize: 100

storage:
  contextDir: ".context"
  dbPath: ".context/sessions.db"

# v2.0 additions
chunking:
  enabled: true
  minLines: 5
  maxLines: 300
  contextLines: 3
  maxNestingDepth: 3
  fallbackToFile: true

file_watcher:
  enabled: true
  debounceMs: 400
  pollIntervalMs: 100
  ignored:
    - "node_modules"
    - ".git"
    - "dist"
    - "build"
    - "coverage"

git:
  enabled: true
  maxCommitsPerLog: 100
  diffMaxFiles: 50

ai_discovery:
  enabled: false                  # Requires ANTHROPIC_API_KEY
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  confidenceThreshold: 0.6
  maxMessagesPerSession: 50
  costLimitPerDay: 10.0           # USD

ranking:
  recencyWeight: 1.5              # 24h boost
  recencyWeekWeight: 1.2          # 7d boost
  moduleWeight: 1.3               # Same module boost
  frequencyDivisor: 100           # access_count / 100
  frequencyCap: 1.5

multi_project:
  enabled: false
  maxLinkedProjects: 10
  searchDepth: 1                  # Levels of transitive links

monitoring:
  metricsEnabled: true
  metricsPort: 9090
  healthCheckEnabled: true
  cacheMetricsTTL: 1000           # Milliseconds

dashboard:
  enabled: false
  port: 3456
  autoOpenBrowser: true
  pollInterval: 5000              # Milliseconds
```

---

## Migration Strategy (v1.0 → v2.0)

### Automatic Migration Script

**Location**: `src/infrastructure/storage/migrations/migrate-v2.ts`

```typescript
export async function migrateToV2(db: Database): Promise<void> {
  logger.info('Starting migration from v1.0 to v2.0');
  
  // 1. Create new tables
  await db.exec(/* chunks table SQL */);
  await db.exec(/* change_events table SQL */);
  await db.exec(/* refined_discoveries table SQL */);
  await db.exec(/* linked_projects table SQL */);
  await db.exec(/* cross_references table SQL */);
  
  // 2. Extend existing tables
  await db.exec('ALTER TABLE sessions ADD COLUMN git_tools_used INTEGER DEFAULT 0');
  await db.exec('ALTER TABLE sessions ADD COLUMN git_commits_queried TEXT');
  await db.exec('ALTER TABLE sessions ADD COLUMN ai_discoveries_count INTEGER DEFAULT 0');
  await db.exec('ALTER TABLE sessions ADD COLUMN files_watched_changed INTEGER DEFAULT 0');
  
  // 3. Update schema version
  await db.exec('UPDATE metadata SET value = "2.0.0" WHERE key = "schema_version"');
  
  logger.info('Migration to v2.0 complete');
}
```

### Data Preservation

- **Sessions**: Preserved with default values for new columns
- **File embeddings**: Preserved as-is (will be replaced incrementally with chunk embeddings)
- **Project.yaml**: Preserved with new sections added
- **Config.yaml**: Merged with v2.0 defaults, user customizations preserved

---

## Data Flow Diagrams

### Chunk Extraction & Embedding Flow

```
┌──────────────┐
│  File Saved  │ (via file watcher)
└──────┬───────┘
       ↓
┌──────────────────────┐
│  Extract Chunks      │ (AST parsing)
│  - Parse with Babel  │
│  - Identify functions│
│  - Create chunks     │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│  Store in SQLite     │
│  INSERT INTO chunks  │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│  Generate Embeddings │ (OpenAI API)
│  - Batch 100 chunks  │
│  - text-embedding-3  │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│  Store in ChromaDB   │
│  code_chunks coll.   │
└──────────────────────┘
```

### Search with Ranking Flow

```
┌──────────────┐
│  User Query  │ "authentication logic"
└──────┬───────┘
       ↓
┌──────────────────────┐
│  Generate Embedding  │ (OpenAI)
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│  Search ChromaDB     │ (semantic similarity)
│  - Top 50 results    │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│  Apply Boosts        │
│  - Recency: 1.5x     │
│  - Module: 1.3x      │
│  - Frequency: 1.2x   │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│  Re-rank Results     │
│  - Sort by final_score│
│  - Return top 5      │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│  Format Response     │ (Markdown)
└──────────────────────┘
```

---

## Validation & Constraints

### Domain Model Validation

```typescript
// src/domain/models/validators/chunk-validator.ts
import { z } from 'zod';

export const CodeChunkSchema = z.object({
  id: z.string().uuid(),
  filePath: z.string().min(1),
  type: z.nativeEnum(ChunkType),
  name: z.string().min(1),
  startLine: z.number().int().min(1),
  endLine: z.number().int().min(1),
  contentStartLine: z.number().int().min(1),
  contentEndLine: z.number().int().min(1),
  code: z.string().min(1),
  parentChunkId: z.string().uuid().optional(),
  nestingLevel: z.number().int().min(0).max(10),
  scopePath: z.array(z.string()),
  metadata: z.object({
    signature: z.string().optional(),
    jsDoc: z.string().optional(),
    isExported: z.boolean(),
    isAsync: z.boolean(),
    parameters: z.array(z.string()).optional(),
    returnType: z.string().optional(),
    complexity: z.number().int().optional(),
  }),
  embeddingId: z.string().optional(),
  createdAt: z.date(),
  updatedAt: z.date(),
}).refine(
  (data) => data.endLine >= data.startLine,
  'endLine must be >= startLine'
).refine(
  (data) => data.contentEndLine >= data.contentStartLine,
  'contentEndLine must be >= contentStartLine'
);
```

### Database Constraints

- **Foreign Keys**: Enforce referential integrity (cascading deletes)
- **Unique Constraints**: Project paths, chunk IDs must be unique
- **Check Constraints**: Confidence scores between 0.0 and 1.0
- **Not Null**: Critical fields must have values

---

**END OF DATA MODEL DOCUMENT**
