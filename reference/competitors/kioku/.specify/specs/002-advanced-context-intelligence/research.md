# Research & Technical Decisions

**Feature**: Kioku v2.0 - Advanced Context Intelligence  
**Branch**: `002-advanced-context-intelligence`  
**Date**: 2025-10-09  
**Status**: Complete

---

## Overview

This document captures all technical research and decisions made during the planning phase for Kioku v2.0. Each decision includes rationale, alternatives considered, and implementation guidance.

---

## Decision 1: Git Integration Library

### Selected: simple-git v3.27.0+

**Rationale:**
- **Best Performance**: Lightweight wrapper around native git CLI executes at native speed (~100-500ms for typical repos)
- **Security Hardened**: All CVEs patched in v3.5.0+ (CVE-2022-24433, CVE-2022-24066)
- **Battle-Tested**: 5.8M weekly downloads, 10+ years production use
- **Bun Compatible**: Works seamlessly with Bun's child_process API
- **Simple API**: Clean promise-based interface maps directly to MCP tool requirements

**Alternatives Considered:**

| Library | Why Rejected |
|---------|--------------|
| **isomorphic-git** | Maintenance mode (2025), slower pure-JS implementation, no browser requirement for CLI tool |
| **nodegit** | Abandoned (5 years), native bindings incompatible with Bun, overkill for use case |
| **Direct child_process** | Reinventing wheel, no input sanitization, harder to test, more code to maintain |

**Implementation Notes:**

```typescript
// Security: ALWAYS validate user inputs
const SHA_REGEX = /^[a-f0-9]{7,40}$/;
const SAFE_PATH = /^[a-zA-Z0-9._/-]+$/;

if (!SHA_REGEX.test(commitSha)) {
  throw new Error('Invalid commit SHA');
}

// Use typed methods when possible (auto-sanitize)
await git.log({
  '--since': userInput,  // Library sanitizes
  '--author': email
});

// If using raw(), validate first
if (SAFE_PATH.test(filePath)) {
  await git.raw(['blame', filePath]);
}
```

**Edge Cases Handled:**
- Non-git repositories → Return "Not a git repository" message
- Shallow clones → Note limited history in results
- Detached HEAD → Show commit SHA instead of branch name
- Binary files → Skip or show "binary file changed"
- Large commits (500+ files) → Limit diff output to first 50 + summary

**Installation:**
```bash
bun add simple-git
```

**Files Created:**
- `src/infrastructure/external/git-client.ts` - Git client wrapper
- `src/infrastructure/mcp/tools/git-log.ts` - git_log MCP tool
- `src/infrastructure/mcp/tools/git-blame.ts` - git_blame MCP tool
- `src/infrastructure/mcp/tools/git-diff.ts` - git_diff MCP tool

---

## Decision 2: File Watching Library

### Selected: chokidar v4.0+

**Rationale:**
- **Battle-Tested**: 30M+ repositories, 10+ years production-proven
- **Cross-Platform Native**: Uses fsevents (macOS), inotify (Linux), ReadDirectoryChangesW (Windows)
- **Built-in Features**: Debouncing, ignore patterns, symlink handling, permission error recovery
- **v4 Improvements**: TypeScript native, 13→1 dependencies (Sept 2024 rewrite)
- **Proven Scalability**: Handles 50k+ files, ~30-50MB RAM for 5k files
- **Constitutional Alignment**: Reliability > performance (Kioku requires "Zero Intervention")

**Alternatives Considered:**

| Library | Why Rejected |
|---------|--------------|
| **Bun's fs.watch** | Compatibility issues (SIGABRT crashes reported Feb 2024), no built-in debouncing/ignoring, less mature |
| **Watchman** | Requires separate binary installation (violates "zero setup"), overkill for 500-10k files |
| **Native fs.watch** | Inconsistent cross-platform behavior, no debouncing, requires 200+ lines wrapper code |
| **node-watch** | Poor performance >1000 files, falls back to polling, smaller community |

**Implementation Notes:**

```typescript
const watcher = chokidar.watch(projectRoot, {
  // Wait for file stability (avoid incomplete writes)
  awaitWriteFinish: {
    stabilityThreshold: 400,  // 400ms of no changes
    pollInterval: 100         // Check every 100ms
  },
  
  // Critical exclusions (saves ~40MB RAM)
  ignored: [
    /(^|[\/\\])\../,          // Dotfiles (.git, .DS_Store)
    /node_modules/,
    /dist/,
    /build/,
    /coverage/,
  ],
  
  persistent: true,           // Keep watcher running
  ignoreInitial: true,        // Don't emit 'add' for existing files
  followSymlinks: false,      // Security: don't follow symlinks
  usePolling: false,          // Use native OS events (faster)
});
```

**Auto-Restart with Exponential Backoff:**

```typescript
let restartAttempts = 0;
const MAX_RETRIES = 5;
const BASE_DELAY = 1000; // 1 second

watcher.on('error', async (error) => {
  logger.error('File watcher crashed', { error, restartAttempts });
  
  if (restartAttempts >= MAX_RETRIES) {
    logger.fatal('File watcher failed after 5 retries');
    return;
  }
  
  // Exponential backoff: 1s, 2s, 4s, 8s, 16s
  const delay = BASE_DELAY * Math.pow(2, restartAttempts++);
  await new Promise(resolve => setTimeout(resolve, delay));
  startWatcher();
});
```

**Performance Expectations:**
- File changes detected within 500ms (400ms debounce + 100ms processing)
- RAM usage: 30-50MB for 5,000 files
- CPU: <1% idle, <5% during burst saves
- Crash recovery: Exponential backoff up to 5 retries

**Installation:**
```bash
bun add chokidar
bun add -d @types/chokidar
```

**Files Created:**
- `src/infrastructure/file-watcher/FileWatcherService.ts` - Main service
- `src/infrastructure/file-watcher/config.ts` - Configuration
- `tests/integration/file-watcher.test.ts` - Integration tests

---

## Decision 3: Prometheus Metrics Implementation

### Selected: prom-client v15+ with Fastify for HTTP endpoints

**Rationale:**
- **Industry Standard**: 15M+ weekly downloads, proven at scale
- **Performance**: <50ms p99 response time achievable with caching
- **TypeScript Native**: Excellent type definitions bundled
- **Minimal Overhead**: Fastify for lightweight HTTP server (2 endpoints only)
- **MCP Compatible**: Separate HTTP server doesn't interfere with stdio MCP protocol

**Metrics Architecture:**

| Metric Name | Type | Purpose | Labels |
|-------------|------|---------|--------|
| `kioku_embedding_queue_depth` | Gauge | Files waiting for embedding | - |
| `kioku_api_latency_seconds` | Histogram | API call latency (p50/p95/p99) | `provider`, `operation` |
| `kioku_file_watcher_events_total` | Counter | File system events detected | `event_type` |
| `kioku_errors_total` | Counter | Total errors by type | `error_type` |
| `kioku_active_sessions` | Gauge | Currently active MCP sessions | - |
| `kioku_context_window_usage_percent` | Gauge | Context window utilization (0-100) | - |

**Histogram Buckets for Latency:**
```typescript
buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
// Covers: 5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s

// Query percentiles in Prometheus:
histogram_quantile(0.50, rate(kioku_api_latency_seconds_bucket[5m]))  # p50
histogram_quantile(0.95, rate(kioku_api_latency_seconds_bucket[5m]))  # p95
histogram_quantile(0.99, rate(kioku_api_latency_seconds_bucket[5m]))  # p99
```

**Health Check Endpoint:**

```typescript
interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: {
    database: boolean;
    vectordb: boolean;
    file_watcher: boolean;
  };
  uptime_seconds: number;
  timestamp: string;
}

// Status codes:
// 200 - healthy (all systems operational)
// 429 - degraded (non-critical services down, core functional)
// 503 - unhealthy (critical services down)
```

**Performance Optimization (Sub-50ms Target):**

```typescript
// Cache metrics response (1s TTL)
private metricsCache: { value: string; timestamp: number } | null = null;
private CACHE_TTL = 1000;

async getMetrics(): Promise<string> {
  const now = Date.now();
  
  if (this.metricsCache && now - this.metricsCache.timestamp < this.CACHE_TTL) {
    return this.metricsCache.value; // Return cached
  }
  
  const metrics = await register.metrics();
  this.metricsCache = { value: metrics, timestamp: now };
  return metrics;
}
```

**Critical Gotchas:**

1. **Label Cardinality Explosion**: Keep unique label combinations <100 per metric
   ```typescript
   // ❌ BAD: user_id × session_id × file_path = millions of time series
   // ✅ GOOD: provider × operation = 4 time series only
   ```

2. **Timer Memory Leaks**: Always use try-finally
   ```typescript
   const end = apiLatency.startTimer({ provider: 'openai' });
   try {
     await operation();
   } finally {
     end(); // Always called, even on error
   }
   ```

3. **Gauge vs Counter**: Gauge = fluctuates, Counter = only increases
   ```typescript
   // ✅ Queue depth (goes up/down) = Gauge
   // ✅ Total errors (only increases) = Counter
   ```

**Installation:**
```bash
bun add prom-client fastify
```

**Files Created:**
- `src/infrastructure/monitoring/metrics-registry.ts` - Registry + default metrics
- `src/infrastructure/monitoring/custom-metrics.ts` - Custom metric definitions
- `src/infrastructure/monitoring/health-check.ts` - Health check logic
- `src/infrastructure/monitoring/metrics-server.ts` - Fastify HTTP server

---

## Decision 4: AST Chunking Strategy

### Selected: Hierarchical Function/Class-Level Chunking with Context Envelopes

**Rationale:**
- **Precision**: Function-level (20-150 lines) vs file-level (500+ lines) improves search precision by 40%+
- **Embedding Model Sweet Spot**: 400-800 lines fits within 512-1000 token optimal range (research-backed)
- **Existing Tools**: Babel parser already in project (`@babel/parser`, `@babel/traverse`)
- **Context Preservation**: Include JSDoc + 3 lines before/after for semantic coherence
- **Research-Backed**: Anthropic's contextual retrieval shows 30%+ improvement with surrounding context

**Chunk Types:**
```typescript
enum ChunkType {
  FUNCTION_DECLARATION = 'function',      // function foo() {}
  ARROW_FUNCTION = 'arrow_function',      // const foo = () => {}
  CLASS_DECLARATION = 'class',            // class Foo {}
  CLASS_METHOD = 'method',                // methodName() {} inside class
  INTERFACE = 'interface',                // interface Foo {}
  TYPE_ALIAS = 'type',                    // type Foo = {}
}
```

**Context Envelope (What to Include):**
```
[JSDoc comment if present]
[3 lines before for context]
[Function signature with full type annotations]
[Function body]
[3 lines after for context]
```

**Chunk Size Constraints:**
- **MIN_LINES**: 5 (below = merge with parent)
- **IDEAL_LINES**: 20-150 (target range)
- **MAX_LINES**: 300 (above = split into sub-chunks)
- **CONTEXT_LINES**: 3 (surrounding lines)
- **MAX_NESTING_DEPTH**: 3 (deeper = include in parent)

**AST Traversal Pattern:**

```typescript
import { parse } from '@babel/parser';
import traverse from '@babel/traverse';

const ast = parse(content, {
  sourceType: 'module',
  plugins: ['typescript', 'jsx', 'decorators-legacy'],
  errorRecovery: true,  // CRITICAL: Don't fail on syntax errors
});

traverse(ast, {
  FunctionDeclaration(path) {
    chunks.push(extractFunctionChunk(path, lines, filePath));
  },
  ClassDeclaration(path) {
    chunks.push(extractClassChunk(path, lines, filePath));
    // Extract methods as sub-chunks
    path.node.body.body.forEach((member) => {
      if (t.isClassMethod(member)) {
        chunks.push(extractMethodChunk(member, lines, filePath));
      }
    });
  },
});
```

**Nested Functions (Hierarchical References):**
```typescript
interface CodeChunk {
  id: string;
  parentChunkId?: string;        // Reference to parent chunk
  nestingLevel: number;          // 0 = top-level, 1+ = nested
  scopePath: string[];           // ['ClassName', 'methodName', 'closureFn']
}

// Rule: If nested > 3 levels deep OR < 10 lines, include in parent
function shouldCreateSeparateChunk(nestingLevel: number, linesOfCode: number): boolean {
  if (nestingLevel === 0) return true;
  if (nestingLevel > 3) return false;
  if (linesOfCode < 10) return false;
  return true;
}
```

**Fallback Strategy (Graceful Degradation):**
1. **Syntax Errors**: Use Babel's `errorRecovery: true` → partial AST still usable
2. **Parsing Fails**: Catch error → return single file-level chunk with warning
3. **Minified Code**: Detect (avg line length >200 chars) → file-level chunk
4. **Generated Code**: Detect markers (`@generated`, `DO NOT EDIT`) → file-level chunk

**Performance Optimization:**

```typescript
// 1. Content-Hash Caching
private cache = new Map<string, { hash: string; chunks: CodeChunk[] }>();

async extractWithCache(filePath: string, content: string): Promise<CodeChunk[]> {
  const hash = Bun.hash(content).toString();
  const cached = this.cache.get(filePath);
  
  if (cached && cached.hash === hash) {
    return cached.chunks; // Cache hit
  }
  
  const chunks = extractChunks(content, filePath);
  this.cache.set(filePath, { hash, chunks });
  return chunks;
}

// 2. Incremental Re-chunking (with File Watching)
async onFileChanged(filePath: string, newContent: string): Promise<void> {
  const newChunks = await this.extractWithCache(filePath, newContent);
  const oldChunks = await this.getStoredChunks(filePath);
  const changedChunks = this.diffChunks(oldChunks, newChunks);
  
  // Re-embed only changed chunks (not entire file)
  await this.reembedChunks(changedChunks);
}

// 3. Parallel Processing (Batched)
const BATCH_SIZE = 100;
for (let i = 0; i < files.length; i += BATCH_SIZE) {
  const batch = files.slice(i, i + BATCH_SIZE);
  await Promise.all(batch.map(file => extractor.extractWithCache(file, content)));
}
```

**Expected Performance:**
- 500 files: ~5 seconds first parse, ~0.5 seconds cached
- 5,000 files: ~30 seconds first parse, ~3 seconds cached
- 10,000 files: ~60 seconds first parse, ~6 seconds cached
- Memory: ~100MB (500 files), ~500MB (5k files), ~1GB (10k files)

**Edge Cases Handled:**
- Multi-line template literals → Babel identifies as string literals (no action needed)
- Dynamic property names → Use `<computed>` as chunk name
- Anonymous functions → Use `<anonymous>` or `<default export>` as name
- JSX/TSX → Babel's `jsx` plugin handles automatically

**Installation:**
No new dependencies (Babel already in project)

**Files Created:**
- `src/domain/models/CodeChunk.ts` - CodeChunk interface
- `src/domain/calculations/chunk-extractor.ts` - Pure AST logic
- `src/domain/calculations/chunk-differ.ts` - Compare old vs new chunks
- `src/application/services/ChunkingService.ts` - Orchestration
- `src/infrastructure/storage/chunk-storage.ts` - Store/retrieve chunks

---

## Decision 5: Multi-Project Architecture

### Selected: Explicit Link Declarations with Directed Graph Traversal

**Rationale:**
- **Transparency**: User explicitly links projects via `kioku link <path>` command
- **Circular Detection**: Maintain visited set during graph traversal to prevent infinite loops
- **Cross-Project Invalidation**: When backend API changes, invalidate frontend embeddings
- **Graceful Degradation**: Continue with available projects if one unavailable (moved/deleted)

**Link Storage:**

```yaml
# .context/workspace.yaml
workspace:
  projects:
    - name: "frontend"
      path: "/Users/user/projects/my-app/frontend"
      type: "workspace"  # or "dependency"
      status: "available"
      lastAccessed: "2025-10-09T12:00:00Z"
    
    - name: "backend"
      path: "/Users/user/projects/my-app/backend"
      type: "workspace"
      status: "available"
      lastAccessed: "2025-10-09T12:00:00Z"
```

**Cross-Project Search:**
```typescript
class MultiProjectSearchService {
  async search(query: string, globalSearch: boolean = true): Promise<SearchResult[]> {
    const projects = globalSearch 
      ? await this.getAllLinkedProjects()
      : [this.currentProject];
    
    const results: SearchResult[] = [];
    
    for (const project of projects) {
      if (project.status !== 'available') {
        logger.warn('Project unavailable, skipping', { project: project.name });
        continue;
      }
      
      const projectResults = await this.searchProject(project, query);
      results.push(...projectResults.map(r => ({
        ...r,
        projectName: project.name,  // Label by project
      })));
    }
    
    return this.rankResults(results);
  }
}
```

**Circular Link Detection:**
```typescript
function detectCircularLinks(startProject: string, links: ProjectLink[]): boolean {
  const visited = new Set<string>();
  const stack = [startProject];
  
  while (stack.length > 0) {
    const current = stack.pop()!;
    
    if (visited.has(current)) {
      logger.error('Circular link detected', { path: Array.from(visited) });
      return true;
    }
    
    visited.add(current);
    const linkedProjects = links.filter(l => l.source === current);
    stack.push(...linkedProjects.map(l => l.target));
  }
  
  return false;
}
```

**Files Created:**
- `src/domain/models/LinkedProject.ts` - LinkedProject interface
- `src/application/services/MultiProjectService.ts` - Multi-project orchestration
- `src/infrastructure/cli/commands/link.ts` - `kioku link` command
- `src/infrastructure/storage/workspace-storage.ts` - workspace.yaml handler

---

## Decision 6: Dashboard Technology Stack

### Selected: Express + React (Create React App) for Simplicity

**Rationale:**
- **Simplicity**: Dashboard is P4 (low priority), use battle-tested boring technology
- **Fast Development**: CRA provides instant setup with TypeScript support
- **Separation**: Dashboard is separate process from MCP server (no interference)
- **Constitutional Alignment**: "Simplicity Over Features" - avoid cutting-edge frameworks

**Architecture:**
```
┌─────────────────────┐
│  MCP Server (stdio) │ ← AI assistant connects here
└──────────┬──────────┘
           │ shares data via
           ↓
┌─────────────────────┐
│  Metrics Server     │ ← Dashboard polls this
│  (HTTP :9090)       │    /metrics, /health, /api/*
└──────────┬──────────┘
           │ REST API
           ↓
┌─────────────────────┐
│  Dashboard          │ ← User opens browser
│  (React :3456)      │    localhost:3456
└─────────────────────┘
```

**REST API Endpoints for Dashboard:**
- `GET /api/project` - Project overview (name, tech stack, module count)
- `GET /api/sessions` - Session timeline (last 50 sessions)
- `GET /api/modules` - Module dependency graph
- `GET /api/embeddings` - Embedding statistics
- `GET /api/context` - Current context window usage

**Polling Strategy:**
```typescript
// Dashboard polls every 5 seconds for real-time updates
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await fetch('http://localhost:9090/api/project').then(r => r.json());
    setProjectData(data);
  }, 5000);
  
  return () => clearInterval(interval);
}, []);
```

**Files Created:**
- `dashboard/` - Separate directory (not in src/)
- `dashboard/src/App.tsx` - Main React app
- `dashboard/src/components/` - React components
- `src/infrastructure/monitoring/api-endpoints.ts` - REST API for dashboard data

---

## Open Questions / Deferred to Implementation

### 1. Re-ranking Boost Factor Tuning
**Question**: What are optimal boost factors for recency/module/frequency?

**Initial Values** (from spec):
- Recency: 1.5x (24h), 1.2x (7d), 1.0x (older)
- Module: 1.3x (same module)
- Frequency: 1 + (access_count / 100), capped at 1.5x

**Decision**: Start with spec values, instrument with metrics, tune based on user feedback in v2.1.

---

### 2. AI Discovery Prompting Strategy
**Question**: What prompt format yields best discovery extraction from Claude API?

**Decision**: Deferred to implementation. Start with simple prompt:
```
Extract patterns, rules, and architectural decisions from this conversation.
Return JSON array with: type, description, confidence (0-1), evidence.
```

Iterate based on quality metrics (user acceptance rate).

---

### 3. Dashboard Visualization Library
**Question**: Use D3.js, Recharts, or Vis.js for module dependency graph?

**Decision**: **Recharts** for simplicity (React-friendly, TypeScript support, good docs). If graph visualization inadequate, upgrade to Vis.js in v2.1.

---

## Dependencies Summary

### New Dependencies Added for v2.0

```json
{
  "dependencies": {
    "simple-git": "^3.27.0",      // Git integration
    "chokidar": "^4.0.0",          // File watching
    "prom-client": "^15.1.0",      // Prometheus metrics
    "fastify": "^4.28.0",          // Metrics HTTP server
    "express": "^4.19.0"           // Dashboard API (alternative to Fastify)
  },
  "devDependencies": {
    "@types/chokidar": "^2.1.3",
    "@types/express": "^4.17.21"
  }
}
```

### Existing Dependencies (Already in v1.0)
- `@babel/parser` - AST parsing (smart chunking)
- `@babel/traverse` - AST traversal
- `@modelcontextprotocol/sdk` - MCP protocol
- `better-sqlite3` - SQLite database
- `chromadb` - Vector embeddings
- `yaml` - YAML parsing

---

## Performance Targets Summary

| Metric | Target | Decision Enabling Target |
|--------|--------|--------------------------|
| Git tool response time | <2 seconds | simple-git (native CLI speed) |
| File change detection | <500ms | chokidar (native OS events) |
| Metrics endpoint latency | <50ms p99 | prom-client + 1s response caching |
| Health check response | <100ms | In-memory checks, 3 retries with timeout |
| AST parsing (5k files) | <30 seconds | Babel + content-hash caching |
| Chunk re-embedding (on change) | <2 seconds | Incremental chunking + diff algorithm |
| File watcher RAM overhead | <50MB | chokidar + aggressive exclude patterns |
| Multi-project search | <3 seconds | Parallel search across projects |

---

## Risk Mitigation Summary

### High-Risk Areas & Mitigations

1. **AST Parsing Performance**
   - **Risk**: 10k files × 30s = 5 min initialization
   - **Mitigation**: Content-hash caching, incremental parsing, background processing

2. **File Watcher Resource Usage**
   - **Risk**: 10k files × 50KB RAM = 500MB overhead
   - **Mitigation**: Exclude node_modules, debounce aggressively, allow disabling in config

3. **API Cost Explosion**
   - **Risk**: AI refinement × 100 sessions/month = $50-100 cost
   - **Mitigation**: Display cost estimates in setup, rate limit (10/day default), allow disabling

4. **Multi-Project Complexity**
   - **Risk**: Circular links, cascading re-embeddings
   - **Mitigation**: Explicit link declarations, circular detection, 1-level depth limit

---

## Next Steps

With research complete, proceed to:

1. ✅ **Phase 0 Complete**: research.md generated
2. **Phase 1**: Generate data models, API contracts, quickstart guide
3. **Phase 2**: Fill complete plan.md with architecture details
4. **Phase 3**: Validate against constitution check

---

**END OF RESEARCH DOCUMENT**
