# Kioku v2.0 Developer Quickstart

**Target Audience**: Developers implementing Kioku v2.0 features  
**Estimated Read Time**: 10 minutes  
**Prerequisites**: Familiarity with v1.0 codebase, Onion Architecture, TDD

---

## Overview

This guide gets you from reading the spec to writing your first v2.0 code in 10 minutes.

**v2.0 adds 10 major features** across 4 priority levels:
- **P1 (High)**: Git Integration, Smart Chunking
- **P2 (Medium)**: File Watching, AI Discovery, Re-ranking, Observability
- **P3 (Medium)**: Multi-Project Support
- **P4 (Low)**: Dashboard, Onboarding, Diagnostics

**Implementation order**: P1 → P2 → P3 → P4 (phased rollout to v2.0, v2.1, v2.2)

---

## Architecture at a Glance

### Onion Layers (Dependency Flow)

```
🔴 Infrastructure (Outermost - I/O)
    ├── storage/ (SQLite, ChromaDB, YAML)
    ├── mcp/ (MCP server, tools)
    ├── cli/ (Commands)
    ├── external/ (OpenAI, Anthropic, Git)
    ├── file-watcher/ (Chokidar service)
    └── monitoring/ (Prometheus metrics)
         ↓ depends on
🟡 Application (Middle - Orchestration)
    ├── use-cases/ (Feature workflows)
    ├── services/ (Application services)
    └── ports/ (Interfaces for infrastructure)
         ↓ depends on
🟢 Domain (Innermost - Pure Logic)
    ├── models/ (Data types, interfaces)
    ├── calculations/ (Pure functions)
    └── rules/ (Business rules)
```

**Golden Rule**: Dependencies only point INWARD (🔴 → 🟡 → 🟢)

### Key Patterns

**Functional Programming** (from Grokking Simplicity):
- **Domain = 100% pure functions** (no I/O, no side effects)
- **Prefer immutability** (copy-on-write, map/filter/reduce)
- **Push side effects to edges** (infrastructure layer)

**Test-Driven Development**:
- Write tests BEFORE code (Red → Green → Refactor)
- 90%+ coverage required (enforced)
- Pure functions = easy to test

---

## Quick Reference: Key Technologies

| Feature | Library/Tech | Why | Files |
|---------|-------------|-----|-------|
| **Git Integration** | simple-git v3.27+ | Native CLI speed, security hardened | `infrastructure/external/git-client.ts` |
| **Smart Chunking** | @babel/parser (existing) | AST parsing, already in project | `domain/calculations/chunk-extractor.ts` |
| **File Watching** | chokidar v4+ | Battle-tested, cross-platform | `infrastructure/file-watcher/` |
| **AI Discovery** | Anthropic API | Claude 3 Sonnet for refinement | `infrastructure/external/anthropic-client.ts` |
| **Metrics** | prom-client v15+ | Prometheus standard | `infrastructure/monitoring/` |
| **HTTP Server** | Fastify v4+ | Lightweight, fast | `infrastructure/monitoring/metrics-server.ts` |

---

## 10-Minute Setup

### Step 1: Install New Dependencies (2 min)

```bash
cd /Users/sovanaryththorng/sanzoku_labs/kioku

# Install v2.0 dependencies
bun add simple-git chokidar prom-client fastify

# Install dev dependencies
bun add -d @types/chokidar

# Verify installation
bun install
```

### Step 2: Create Directory Structure (1 min)

```bash
# Domain layer (pure logic)
mkdir -p src/domain/models
mkdir -p src/domain/calculations
mkdir -p src/domain/rules

# Application layer (use cases)
mkdir -p src/application/use-cases
mkdir -p src/application/services
mkdir -p src/application/ports

# Infrastructure layer (I/O)
mkdir -p src/infrastructure/external
mkdir -p src/infrastructure/file-watcher
mkdir -p src/infrastructure/monitoring
mkdir -p src/infrastructure/storage/migrations

# Tests
mkdir -p tests/unit/domain/calculations
mkdir -p tests/unit/application/services
mkdir -p tests/integration
```

### Step 3: Set Up Environment Variables (1 min)

```bash
# .env (add to existing or create)
cat >> .env << 'EOF'

# v2.0 additions
ANTHROPIC_API_KEY=sk-ant-...  # Optional: for AI discovery
KIOKU_METRICS_PORT=9090       # Prometheus metrics port
KIOKU_DASHBOARD_PORT=3456     # Dashboard port (optional)
EOF
```

### Step 4: Read Core Documents (5 min)

**Must-read order**:
1. ✅ `specs/002-advanced-context-intelligence/spec.md` - Requirements (69 FRs)
2. ✅ `specs/002-advanced-context-intelligence/research.md` - Technical decisions
3. ✅ `specs/002-advanced-context-intelligence/data-model.md` - Data structures
4. ✅ `specs/002-advanced-context-intelligence/contracts/` - API contracts

### Step 5: Write Your First Test (1 min)

```typescript
// tests/unit/domain/calculations/chunk-extractor.test.ts
import { describe, it, expect } from 'vitest';
import { extractChunks } from '@/domain/calculations/chunk-extractor';

describe('extractChunks', () => {
  it('should extract function chunks from TypeScript code', () => {
    const code = `
      function add(a: number, b: number): number {
        return a + b;
      }
    `;
    
    const chunks = extractChunks(code, 'test.ts');
    
    expect(chunks).toHaveLength(1);
    expect(chunks[0].name).toBe('add');
    expect(chunks[0].type).toBe('function');
  });
});
```

**Run test** (it will fail - that's Red in TDD):
```bash
bun test tests/unit/domain/calculations/chunk-extractor.test.ts
```

---

## Implementation Workflow

### Phase 0: Foundation (Week 1)

**Goal**: Set up infrastructure without features.

**Tasks**:
1. Create database schema (SQLite tables for chunks, change_events, etc.)
2. Set up Git client wrapper (simple-git)
3. Set up File watcher service (chokidar)
4. Set up Metrics server (prom-client + Fastify)
5. Create domain models (CodeChunk, GitCommit, etc.)

**Acceptance**: All services start without errors, no features implemented yet.

### Phase 1: Git Integration (Week 1-2)

**Goal**: Users can query git history via MCP tools.

**Tasks**:
1. ✅ Write tests for git_log tool
2. Implement git_log tool (TDD)
3. ✅ Write tests for git_blame tool
4. Implement git_blame tool (TDD)
5. ✅ Write tests for git_diff tool
6. Implement git_diff tool (TDD)
7. Register tools with MCP server
8. Integration test: Call tools from Claude

**Acceptance**: All 3 git tools return markdown-formatted results, handle edge cases gracefully.

### Phase 2: Smart Chunking (Week 2-3)

**Goal**: Search returns function-level results, not file-level.

**Tasks**:
1. ✅ Write tests for chunk extractor (AST parsing)
2. Implement chunk extractor (TDD)
3. Create chunk storage (SQLite table + CRUD)
4. Update embedding generation (per-chunk instead of per-file)
5. Update context_search tool (return chunks)
6. Migration script (v1.0 embeddings → v2.0 chunks)

**Acceptance**: context_search returns 20-150 line chunks, not 500+ line files.

### Phase 3: File Watching (Week 3-4)

**Goal**: Context updates automatically on file saves.

**Tasks**:
1. ✅ Write tests for file watcher service
2. Implement file watcher with chokidar (TDD)
3. Connect watcher to chunk extractor (on change → re-chunk)
4. Connect to embedding generator (on change → re-embed)
5. Add debouncing logic (400ms stability threshold)
6. Add auto-restart with exponential backoff

**Acceptance**: Save file → embeddings update within 2 seconds, watcher auto-restarts on crash.

### Phase 4: Observability (Week 4)

**Goal**: Metrics and health checks for monitoring.

**Tasks**:
1. Set up prom-client registry + default metrics
2. Define custom metrics (queue depth, latency, errors)
3. Instrument code (add timers, counters, gauges)
4. Implement health check logic
5. Create Fastify server for /metrics and /health
6. Test with Prometheus scraping

**Acceptance**: /metrics returns Prometheus format, /health returns 200/429/503 correctly.

### Phase 5: AI Discovery (Week 5)

**Goal**: AI refines discoveries from sessions.

**Tasks**:
1. Set up Anthropic API client
2. Implement redaction logic (sensitive data patterns)
3. ✅ Write tests for AI discovery service
4. Implement AI discovery service (TDD)
5. Update session end handler (trigger AI discovery)
6. Store refined discoveries in SQLite
7. Apply discoveries to project.yaml

**Acceptance**: Session ends → AI extracts discoveries with confidence ≥0.6, applies to project.yaml.

### Phase 6: Re-ranking (Week 5)

**Goal**: Search results ranked by relevance, not just semantic score.

**Tasks**:
1. ✅ Write tests for ranking algorithm
2. Implement boost calculations (recency, module, frequency)
3. Update context_search to apply boosts
4. Track file access statistics
5. Expose ranking details in results (debug mode)

**Acceptance**: Recent files appear higher in results, same-module files boosted.

### Phase 7: Multi-Project (Week 6)

**Goal**: Link projects, search across codebases.

**Tasks**:
1. Create workspace.yaml handler
2. Implement `kioku link` command
3. Update context_search to search linked projects
4. Implement cross-reference tracking
5. Add circular link detection
6. Handle unavailable projects gracefully

**Acceptance**: Link 2 projects → search returns results from both, labeled by project.

### Phase 8: Dashboard (Week 7)

**Goal**: Web UI for visual debugging.

**Tasks**:
1. Create React app with Create React App
2. Implement REST API endpoints (/api/project, /api/sessions, etc.)
3. Build dashboard UI components
4. Implement polling for real-time updates
5. Add module dependency graph visualization

**Acceptance**: Open localhost:3456 → see project overview, session timeline, module graph.

### Phase 9: Onboarding & Diagnostics (Week 8)

**Goal**: Guided setup and auto-repair.

**Tasks**:
1. Implement `kioku setup --interactive` wizard
2. Implement `kioku doctor` command
3. Add API key validation
4. Add database integrity checks
5. Add auto-repair logic

**Acceptance**: Fresh setup works in <5 min, doctor auto-fixes common issues.

---

## Code Examples (Copy-Paste Ready)

### Example 1: Pure Domain Function (Chunk Extraction)

```typescript
// src/domain/calculations/chunk-extractor.ts
import { parse } from '@babel/parser';
import traverse from '@babel/traverse';
import type { CodeChunk, ChunkType } from '@/domain/models/CodeChunk';

/**
 * Extract code chunks from source code using AST parsing
 * PURE FUNCTION: No I/O, no side effects, testable
 */
export function extractChunks(
  content: string,
  filePath: string
): CodeChunk[] {
  const chunks: CodeChunk[] = [];
  const lines = content.split('\n');
  
  try {
    const ast = parse(content, {
      sourceType: 'module',
      plugins: ['typescript', 'jsx', 'decorators-legacy'],
      errorRecovery: true,
    });
    
    traverse(ast, {
      FunctionDeclaration(path) {
        const chunk = createChunkFromNode(path.node, lines, filePath);
        chunks.push(chunk);
      },
    });
  } catch (error) {
    // Fallback: return file-level chunk
    return [createFileChunk(content, filePath)];
  }
  
  return chunks;
}
```

### Example 2: Application Service (Orchestration)

```typescript
// src/application/services/ChunkingService.ts
import { extractChunks } from '@/domain/calculations/chunk-extractor';
import type { IChunkStorage } from '@/application/ports/IChunkStorage';
import type { IEmbeddingGenerator } from '@/application/ports/IEmbeddingGenerator';

export class ChunkingService {
  constructor(
    private storage: IChunkStorage,
    private embeddings: IEmbeddingGenerator
  ) {}
  
  async processFile(filePath: string, content: string): Promise<void> {
    // 1. Extract chunks (pure domain logic)
    const chunks = extractChunks(content, filePath);
    
    // 2. Store chunks (infrastructure via port)
    await this.storage.saveChunks(chunks);
    
    // 3. Generate embeddings (infrastructure via port)
    await this.embeddings.generateForChunks(chunks);
    
    logger.info('File processed', { filePath, chunkCount: chunks.length });
  }
}
```

### Example 3: Infrastructure Adapter (I/O)

```typescript
// src/infrastructure/storage/SQLiteChunkStorage.ts
import type { IChunkStorage } from '@/application/ports/IChunkStorage';
import type { CodeChunk } from '@/domain/models/CodeChunk';
import type { Database } from 'better-sqlite3';

export class SQLiteChunkStorage implements IChunkStorage {
  constructor(private db: Database) {}
  
  async saveChunks(chunks: CodeChunk[]): Promise<void> {
    const stmt = this.db.prepare(`
      INSERT INTO chunks (id, file_path, type, name, code, ...)
      VALUES (?, ?, ?, ?, ?, ...)
      ON CONFLICT(id) DO UPDATE SET updated_at = ?
    `);
    
    const transaction = this.db.transaction((chunks) => {
      for (const chunk of chunks) {
        stmt.run(
          chunk.id,
          chunk.filePath,
          chunk.type,
          chunk.name,
          chunk.code,
          // ...
          Date.now()
        );
      }
    });
    
    transaction(chunks);
  }
}
```

### Example 4: Prometheus Metrics Instrumentation

```typescript
// src/infrastructure/monitoring/custom-metrics.ts
import { Histogram, Gauge } from 'prom-client';
import { register } from './metrics-registry';

export const apiLatency = new Histogram({
  name: 'kioku_api_latency_seconds',
  help: 'API call latency',
  labelNames: ['provider', 'operation'],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
  registers: [register],
});

// Usage in code
async function generateEmbedding(text: string): Promise<number[]> {
  const end = apiLatency.startTimer({ provider: 'openai', operation: 'embed' });
  
  try {
    const response = await client.embeddings.create({ input: text });
    return response.data[0].embedding;
  } finally {
    end(); // Records duration automatically
  }
}
```

---

## Common Gotchas

### Gotcha 1: Forgetting Try-Finally in Metrics

```typescript
// ❌ BAD: Timer leaks on error
const end = apiLatency.startTimer();
await riskyOperation(); // Throws
end(); // NEVER CALLED

// ✅ GOOD: Always use try-finally
const end = apiLatency.startTimer();
try {
  await riskyOperation();
} finally {
  end(); // Always called
}
```

### Gotcha 2: Violating Onion Architecture

```typescript
// ❌ BAD: Domain importing from Infrastructure
// File: src/domain/calculations/chunk-extractor.ts
import { logger } from '@infrastructure/cli/logger';

// ✅ GOOD: Domain is pure, no imports from outer layers
// If logging needed, return errors and let caller log
```

### Gotcha 3: Mutation Instead of Copy-on-Write

```typescript
// ❌ BAD: Mutates input
function enrichChunk(chunk: CodeChunk, metadata: Metadata): void {
  chunk.metadata = { ...chunk.metadata, ...metadata }; // Mutation!
}

// ✅ GOOD: Returns new object
function enrichChunk(chunk: CodeChunk, metadata: Metadata): CodeChunk {
  return {
    ...chunk,
    metadata: { ...chunk.metadata, ...metadata }
  };
}
```

### Gotcha 4: High Cardinality Labels in Metrics

```typescript
// ❌ BAD: Unbounded label values
const requestLatency = new Histogram({
  labelNames: ['user_id', 'file_path'] // Millions of combinations!
});

// ✅ GOOD: Low cardinality labels
const requestLatency = new Histogram({
  labelNames: ['provider', 'operation'] // 4 combinations total
});
```

---

## Testing Strategy

### Test Pyramid

```
           /\
          /  \     E2E (5%)
         /____\    Manual: Full workflow with Claude
        /      \   
       / Integ  \  Integration (15%)
      /__________\ Tests: Services + Real DB/API
     /            \
    /   Unit Tests \ Unit (80%)
   /________________\ Tests: Pure functions, mocked I/O
```

### Testing Pure Functions (Easy!)

```typescript
// Domain functions = 100% pure = Easy to test
describe('extractChunks', () => {
  it('should extract function chunks', () => {
    const code = 'function foo() { return 42; }';
    const chunks = extractChunks(code, 'test.ts');
    
    expect(chunks).toHaveLength(1);
    expect(chunks[0].name).toBe('foo');
    // No mocks needed!
  });
});
```

### Testing With Mocks (Infrastructure)

```typescript
// Infrastructure needs mocks for I/O
describe('ChunkingService', () => {
  it('should store chunks after extraction', async () => {
    const mockStorage = {
      saveChunks: vi.fn().mockResolvedValue(undefined)
    };
    
    const service = new ChunkingService(mockStorage, mockEmbeddings);
    await service.processFile('test.ts', 'function foo() {}');
    
    expect(mockStorage.saveChunks).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ name: 'foo' })
      ])
    );
  });
});
```

---

## Performance Checklist

Before marking a feature complete, verify:

- [ ] AST parsing cached by content hash (no re-parse if unchanged)
- [ ] File watcher excludes node_modules/ (saves ~40MB RAM)
- [ ] Metrics endpoint response cached (1s TTL for <50ms target)
- [ ] Git commands timeout after 10 seconds (prevent hangs)
- [ ] Embeddings generated in batches of 100 (not one-by-one)
- [ ] Database queries use indexes (check with EXPLAIN QUERY PLAN)
- [ ] Health checks retry 3 times before failing (avoid false negatives)
- [ ] Dashboard polls every 5 seconds (not every 100ms)

---

## Quality Gate (MUST PASS)

Before committing any code:

```bash
# Run full quality gate
bun run quality-gate

# This runs:
# 1. TypeScript type check (bun run type-check)
# 2. ESLint with architecture rules (bun run lint)
# 3. Tests with coverage (bun test:coverage)

# All must pass:
# ✓ No TypeScript errors
# ✓ No ESLint errors (architecture boundaries enforced)
# ✓ All tests passing
# ✓ Coverage ≥ 90%
```

---

## Next Steps

1. **Read remaining docs**:
   - `spec.md` - Full requirements (69 FRs, 34 success criteria)
   - `research.md` - Technical decisions with rationale
   - `data-model.md` - Database schemas, domain models
   - `contracts/` - MCP tools API, REST API

2. **Start with Phase 0** (Foundation):
   - Set up database schema
   - Create domain models
   - Install dependencies

3. **Follow TDD strictly**:
   - Red: Write failing test
   - Green: Make it pass
   - Refactor: Improve code quality

4. **Ask for help**:
   - Unclear requirements? → Check spec.md or ask user
   - Architecture question? → Review constitution.md
   - Technical decision? → Check research.md

---

## Resources

**Project Docs**:
- Constitution: `.specify/memory/constitution.md`
- v1.0 README: `README.md`
- v2.0 Spec: `specs/002-advanced-context-intelligence/spec.md`

**External Docs**:
- simple-git: https://github.com/steveukx/git-js
- chokidar: https://github.com/paulmillr/chokidar
- prom-client: https://github.com/siimon/prom-client
- Babel Parser: https://babeljs.io/docs/babel-parser

**Code Examples**:
- v1.0 codebase: `src/` (reference for patterns)
- Tests: `tests/` (reference for test structure)

---

**You're ready to build! Start with Phase 0 and TDD your way to v2.0. 🚀**

**END OF QUICKSTART**
