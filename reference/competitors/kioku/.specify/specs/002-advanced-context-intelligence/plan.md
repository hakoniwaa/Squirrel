# Implementation Plan: Advanced Context Intelligence (v2.0)

**Branch**: `002-advanced-context-intelligence` | **Date**: 2025-10-09 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/002-advanced-context-intelligence/spec.md`

---

## Summary

Kioku v2.0 transforms the MVP's foundation into a comprehensive context intelligence system by adding:
- **Historical Context** via Git integration (log, blame, diff tools)
- **Precision Search** via function/class-level chunking instead of file-level
- **Real-Time Freshness** via file watching for automatic context updates
- **AI-Enhanced Learning** via GPT-4/Claude refinement of discoveries
- **Intelligent Ranking** via context-aware result boosting (recency, module, frequency)
- **Multi-Project Support** via workspace linking and cross-project search
- **Visual Debugging** via web dashboard for context inspection
- **Streamlined Onboarding** via guided setup wizard and diagnostics

**Technical Approach**: Extends v1.0's MCP server with new tools (git_log, git_blame, git_diff), replaces file-level embeddings with AST-based chunk embeddings, adds Chokidar file watcher for real-time updates, integrates Anthropic API for discovery refinement, implements Prometheus metrics for observability, and provides React dashboard for visualization. All features follow Onion Architecture (Domain → Application → Infrastructure) with 90%+ test coverage and TDD workflow.

---

## Technical Context

**Language/Version**: TypeScript 5.0+, Bun v1.1.29+ (Node.js 18+ fallback)

**Primary Dependencies**:
- **Existing (v1.0)**: @modelcontextprotocol/sdk, better-sqlite3, chromadb, @babel/parser, @babel/traverse, yaml, openai
- **New (v2.0)**: simple-git v3.27+, chokidar v4+, prom-client v15+, fastify v4+, express v4+ (dashboard API)

**Storage**:
- SQLite (sessions, chunks, change_events, refined_discoveries, linked_projects, cross_references)
- ChromaDB (chunk-level embeddings, file-level embeddings as fallback)
- YAML (project.yaml for project context, workspace.yaml for multi-project links, config.yaml for configuration)

**Testing**: Vitest with 90%+ coverage requirement enforced, TDD mandatory (Red → Green → Refactor)

**Target Platform**: macOS, Linux, Windows (developer workstations)

**Project Type**: Single project (MCP server + CLI tool, NOT web app)

**Performance Goals**:
- Git tool responses: <2 seconds (p95)
- File change detection: <500ms from save to detection
- Metrics endpoint: <50ms (p99)
- AST parsing (5k files): <30 seconds first parse, <3 seconds cached
- Context search with ranking: <2 seconds (p99)

**Constraints**:
- Local-first (no cloud services except OpenAI/Anthropic APIs)
- Single user (no multi-user concurrency)
- TypeScript/JavaScript projects only (MVP scope)
- 90%+ test coverage (quality gate)
- Context window must stay under 80% capacity (smart pruning)

**Scale/Scope**:
- Typical project: 500-5,000 files
- Large project support: up to 10,000 files
- Multi-project: up to 10 linked projects
- Sessions: hundreds of sessions over months

---

## Constitution Check

### ✅ Passes All Gates

**1. Transparency First** ✓
- All context sources traceable (chunk metadata includes file path, line numbers, parent references)
- Ranking metadata exposed (semantic score, boosts applied, final score)
- Git tools show authorship, commit messages, file changes
- Dashboard provides visual inspection of context state
- Logs show all operations (DEBUG level) for troubleshooting

**2. Zero Manual Intervention** ✓
- File watcher auto-detects changes (no manual refresh)
- Sessions auto-tracked via MCP connection events (no manual start/stop)
- Context auto-enriched after sessions (no manual discovery extraction)
- Background services run without user interaction (scorer, pruner, embeddings)
- Only initialization (`kioku init`) and debugging (`kioku show`, `kioku status`, `kioku doctor`) require manual commands

**3. Progressive Intelligence** ✓
- AI discovery refinement improves extraction quality over time
- Chunk-level embeddings enable more precise search
- Ranking boosts surface recently accessed, frequently used code
- Git integration provides historical learning (who/when/why)
- All context archived, never lost (searchable even after pruning)

**4. Smart Resource Management** ✓
- Context window monitoring with 80% pruning threshold (maintained from v1.0)
- File watcher excludes node_modules/, .git/, dist/ (saves ~40MB RAM)
- Debouncing prevents re-embedding thrash (400ms stability threshold)
- Content-hash caching prevents redundant AST parsing
- Metrics track queue depth, memory usage, API costs

**5. Simplicity Over Features** ⚠️ *Justified Exception*
- **Complexity**: 10 new features across 4 priority levels
- **Justification**: Phased rollout mitigates risk (v2.0 = P1+P2, v2.1 = P3, v2.2 = P4)
- **Mitigation**: Each feature independently testable, can be disabled via config
- **Alternatives Rejected**: "Do nothing" leaves MVP feature-starved; "pick 3 features" leaves user stories incomplete

**Architecture Compliance** ✓
- Onion Architecture maintained (Domain → Application → Infrastructure)
- Domain layer 100% pure functions (no I/O)
- Functional programming patterns (immutability, copy-on-write)
- TDD workflow enforced (90%+ coverage)

**Security & Privacy** ✓
- All data local (no telemetry, no cloud storage)
- API keys via environment variables (never committed)
- Git command injection prevention (input validation regex)
- Sensitive data redaction before AI API calls (moderate security)
- User owns all data (.context/ directory)

---

## Project Structure

### Documentation (this feature)

```
specs/002-advanced-context-intelligence/
├── spec.md               # Requirements (69 FRs, 34 SCs)
├── plan.md               # This file (implementation plan)
├── research.md           # Technical decisions (4 major decisions)
├── data-model.md         # Database schemas, domain models
├── quickstart.md         # Developer onboarding guide
├── contracts/
│   ├── mcp-tools.md      # MCP tools API (git_log, git_blame, git_diff, context_search)
│   └── rest-api.md       # REST API (metrics, health, dashboard)
├── checklists/
│   └── requirements.md   # Quality checklist (21/21 passed)
└── tasks.md              # NOT YET CREATED (Phase 2: /speckit.tasks)
```

### Source Code (repository root)

**Structure**: Single project (existing v1.0 codebase extended)

```
src/
├── domain/                          # 🟢 Pure business logic (INNERMOST)
│   ├── models/
│   │   ├── CodeChunk.ts             # NEW: Chunk representation
│   │   ├── GitCommit.ts             # NEW: Git commit metadata
│   │   ├── GitBlame.ts              # NEW: Line-by-line authorship
│   │   ├── GitDiff.ts               # NEW: Change sets
│   │   ├── ChangeEvent.ts           # NEW: File watcher events
│   │   ├── RefinedDiscovery.ts      # NEW: AI-refined discoveries
│   │   ├── LinkedProject.ts         # NEW: Multi-project links
│   │   ├── SearchResult.ts          # EXTENDED: Add ranking metadata
│   │   └── [v1.0 models...]         # Existing: ProjectContext, Session, etc.
│   │
│   ├── calculations/                # Pure functions
│   │   ├── chunk-extractor.ts       # NEW: AST-based chunking
│   │   ├── chunk-differ.ts          # NEW: Compare old vs new chunks
│   │   ├── chunk-scorer.ts          # NEW: Score chunks for ranking
│   │   ├── ranking-calculator.ts    # NEW: Apply recency/module/frequency boosts
│   │   └── [v1.0 calculations...]   # Existing: context-scoring.ts, etc.
│   │
│   └── rules/                       # Business rules
│       ├── redaction-rules.ts       # NEW: Sensitive data patterns
│       ├── pruning-rules.ts         # Existing from v1.0
│       └── discovery-patterns.ts    # Existing from v1.0
│
├── application/                     # 🟡 Application logic (MIDDLE)
│   ├── use-cases/
│   │   ├── ExtractChunksUseCase.ts  # NEW: Chunk extraction workflow
│   │   ├── RefineDiscoveriesUseCase.ts  # NEW: AI discovery refinement
│   │   ├── RankSearchResultsUseCase.ts  # NEW: Apply ranking boosts
│   │   ├── LinkProjectUseCase.ts    # NEW: Link multi-project workspace
│   │   └── [v1.0 use-cases...]      # Existing: search, init, etc.
│   │
│   ├── services/
│   │   ├── ChunkingService.ts       # NEW: Orchestrate chunking
│   │   ├── GitService.ts            # NEW: Git operations orchestration
│   │   ├── FileWatcherOrchestrator.ts  # NEW: Coordinate file watching
│   │   ├── AIDiscoveryService.ts    # NEW: AI refinement workflow
│   │   ├── MultiProjectService.ts   # NEW: Cross-project coordination
│   │   └── [v1.0 services...]       # Existing: context, embeddings, etc.
│   │
│   └── ports/                       # Interfaces for infrastructure
│       ├── IChunkStorage.ts         # NEW: Chunk persistence interface
│       ├── IGitClient.ts            # NEW: Git operations interface
│       ├── IFileWatcher.ts          # NEW: File watching interface
│       ├── IAIClient.ts             # NEW: AI API interface
│       └── [v1.0 ports...]          # Existing: IStorage, IEmbeddings, etc.
│
├── infrastructure/                  # 🔴 External world (OUTERMOST)
│   ├── storage/
│   │   ├── migrations/
│   │   │   ├── migrate-v2.ts        # NEW: v1.0 → v2.0 migration
│   │   │   ├── 001-create-chunks-table.sql  # NEW
│   │   │   ├── 002-create-change-events-table.sql  # NEW
│   │   │   ├── 003-create-refined-discoveries-table.sql  # NEW
│   │   │   ├── 004-create-linked-projects-table.sql  # NEW
│   │   │   ├── 005-extend-sessions-table.sql  # NEW
│   │   │   └── [v1.0 migrations...]
│   │   ├── chunk-storage.ts         # NEW: SQLite chunk CRUD
│   │   ├── workspace-storage.ts     # NEW: workspace.yaml handler
│   │   └── [v1.0 storage...]        # Existing: sqlite, chroma, yaml
│   │
│   ├── mcp/
│   │   ├── server.ts                # EXTENDED: Register new tools
│   │   └── tools/
│   │       ├── GitLogTool.ts        # NEW: git_log MCP tool
│   │       ├── GitBlameTool.ts      # NEW: git_blame MCP tool
│   │       ├── GitDiffTool.ts       # NEW: git_diff MCP tool
│   │       ├── ContextSearchTool.ts # EXTENDED: Chunk-level + ranking
│   │       └── [v1.0 tools...]      # Existing: read_file, grep, etc.
│   │
│   ├── cli/
│   │   └── commands/
│   │       ├── link.ts              # NEW: kioku link command
│   │       ├── setup.ts             # NEW: kioku setup --interactive
│   │       ├── doctor.ts            # NEW: kioku doctor command
│   │       ├── dashboard.ts         # NEW: kioku dashboard command
│   │       └── [v1.0 commands...]   # Existing: init, serve, show, status
│   │
│   ├── background/
│   │   ├── context-scorer.ts        # Existing from v1.0
│   │   ├── context-pruner.ts        # Existing from v1.0
│   │   └── embedding-queue.ts       # EXTENDED: Chunk-level batching
│   │
│   ├── external/
│   │   ├── git-client.ts            # NEW: simple-git wrapper
│   │   ├── anthropic-client.ts      # NEW: Claude API for AI discovery
│   │   └── openai-client.ts         # Existing from v1.0
│   │
│   ├── file-watcher/
│   │   ├── FileWatcherService.ts    # NEW: Chokidar service
│   │   ├── config.ts                # NEW: Watcher configuration
│   │   └── event-handlers.ts        # NEW: Handle add/change/unlink
│   │
│   └── monitoring/
│       ├── metrics-registry.ts      # NEW: Prometheus registry
│       ├── custom-metrics.ts        # NEW: Metric definitions
│       ├── health-check.ts          # NEW: Health check logic
│       ├── metrics-server.ts        # NEW: Fastify HTTP server
│       └── api-endpoints.ts         # NEW: REST API for dashboard
│
├── shared/                          # ⚪ Utilities (shared across layers)
│   ├── types/
│   ├── utils/
│   ├── errors/
│   └── logger.ts
│
└── index.ts                         # Main entry point

tests/
├── unit/                            # Unit tests (90% of tests)
│   ├── domain/
│   │   ├── calculations/
│   │   │   ├── chunk-extractor.test.ts  # NEW
│   │   │   ├── ranking-calculator.test.ts  # NEW
│   │   │   └── [v1.0 tests...]
│   │   └── models/
│   ├── application/
│   │   ├── services/
│   │   │   ├── ChunkingService.test.ts  # NEW
│   │   │   ├── AIDiscoveryService.test.ts  # NEW
│   │   │   └── [v1.0 tests...]
│   │   └── use-cases/
│   └── infrastructure/
│       ├── storage/
│       │   ├── chunk-storage.test.ts  # NEW
│       │   └── [v1.0 tests...]
│       ├── mcp/tools/
│       │   ├── GitLogTool.test.ts   # NEW
│       │   ├── GitBlameTool.test.ts # NEW
│       │   ├── GitDiffTool.test.ts  # NEW
│       │   └── [v1.0 tests...]
│       └── file-watcher/
│           └── FileWatcherService.test.ts  # NEW
│
└── integration/                     # Integration tests (10% of tests)
    ├── full-workflow.test.ts        # Existing from v1.0
    ├── git-integration.test.ts      # NEW
    ├── file-watcher.test.ts         # NEW
    ├── chunking-pipeline.test.ts    # NEW
    └── multi-project.test.ts        # NEW

dashboard/                           # Separate React app (P4)
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── ProjectOverview.tsx
│   │   ├── SessionTimeline.tsx
│   │   ├── ModuleGraph.tsx
│   │   └── EmbeddingsStats.tsx
│   └── services/
│       └── api-client.ts            # Calls REST API on :9090
├── package.json
└── tsconfig.json

.context/                            # Local data directory (existing + new)
├── sessions.db                      # EXTENDED: New tables added
├── chroma/                          # EXTENDED: code_chunks collection added
├── project.yaml                     # Existing from v1.0
├── workspace.yaml                   # NEW: Multi-project links
└── config.yaml                      # EXTENDED: New config sections

.specify/                            # Spec-Driven Development (existing)
├── memory/
│   └── constitution.md              # Project principles
├── specs/
│   ├── 001-context-tool-mvp/        # v1.0 spec (archived)
│   └── 002-advanced-context-intelligence/  # v2.0 spec (current)
└── templates/
```

**Structure Decision**: Single project structure maintained from v1.0. Onion Architecture strictly enforced:
- **Domain** (🟢): Pure functions, no I/O, easily testable
- **Application** (🟡): Orchestrates domain logic, depends only on domain
- **Infrastructure** (🔴): Handles I/O, depends on application + domain
- **Shared** (⚪): Utilities used across layers, minimal dependencies

Dashboard is separate React app in `dashboard/` directory to avoid polluting main MCP server codebase.

---

## Complexity Tracking

### Constitution Principle 5 Exception: "Simplicity Over Features"

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **10 new features (vs MVP's 4)** | User stories require comprehensive intelligence (git history, precision search, real-time updates, AI refinement, etc.). Each feature addresses distinct pain point from user research. | **Deliver only P1 features**: Leaves 60% of user stories incomplete, fails to achieve "Advanced Context Intelligence" vision. **Deliver only top 3 features**: Arbitrary cutoff breaks coherent feature set (e.g., AI discovery without ranking = incomplete, file watching without chunking = suboptimal). |
| **4 priority levels (P1-P4)** | Enables phased rollout to manage risk. P1 (High) in v2.0, P2 (Medium) in v2.1, P3/P4 (Low) in v2.2. | **Single release with all features**: Too risky (8-week timeline, high complexity). **Only P1 features**: Leaves observability, onboarding gaps that hurt adoption (user can't debug issues, setup too hard). |
| **5 new libraries** | Each library best-in-class for its domain: simple-git (git operations), chokidar (file watching), prom-client (metrics), fastify (HTTP), anthropic (AI). | **Use native APIs**: Would require 500+ lines wrapper code per library (reinventing wheel), higher maintenance burden, more bugs. **Pick fewer features**: See "10 new features" above. |

**Mitigation**:
- Phased rollout reduces risk (v2.0 = P1+P2, v2.1 = P3, v2.2 = P4)
- Each feature independently testable (90%+ coverage enforced)
- Each feature can be disabled via config (graceful degradation)
- TDD workflow prevents regressions
- Comprehensive research phase completed (all unknowns resolved)

**Approval**: Justified exception to Principle 5 for v2.0. Future versions (v3.0+) must return to strict simplicity.

---

## Implementation Phases

### Phase 0: Foundation (Week 1) - **Foundation Without Features**

**Goal**: Set up infrastructure, data models, and database schema without implementing features.

**Tasks**:
1. Install dependencies: `bun add simple-git chokidar prom-client fastify`
2. Create database migrations:
   - `001-create-chunks-table.sql`
   - `002-create-change-events-table.sql`
   - `003-create-refined-discoveries-table.sql`
   - `004-create-linked-projects-table.sql`
   - `005-extend-sessions-table.sql`
3. Create domain models (CodeChunk, GitCommit, GitBlame, GitDiff, ChangeEvent, RefinedDiscovery, LinkedProject)
4. Set up Git client wrapper (`infrastructure/external/git-client.ts`)
5. Set up File watcher service skeleton (`infrastructure/file-watcher/FileWatcherService.ts`)
6. Set up Metrics server skeleton (`infrastructure/monitoring/metrics-server.ts`)
7. Run migration script: `bun run src/infrastructure/storage/migrations/migrate-v2.ts`

**Acceptance Criteria**:
- All dependencies installed (`bun install` succeeds)
- Database schema migrated (all 5 new tables exist)
- Domain models defined with TypeScript types
- Services initialize without errors (but don't do anything yet)
- Tests pass (no features implemented, only structure tests)

**Duration**: 3-4 days

---

### Phase 1: Git Integration (Week 1-2) - **P1 Feature**

**Goal**: Users can query git history via MCP tools (git_log, git_blame, git_diff).

**Tasks**:
1. ✅ Write tests for `GitLogTool` (test various filters, edge cases)
2. Implement `GitLogTool` (TDD: make tests pass)
3. ✅ Write tests for `GitBlameTool`
4. Implement `GitBlameTool` (TDD)
5. ✅ Write tests for `GitDiffTool`
6. Implement `GitDiffTool` (TDD)
7. Register tools with MCP server (`infrastructure/mcp/server.ts`)
8. Add markdown formatting for tool responses
9. Integration test: Call tools from Claude Desktop
10. Handle edge cases: non-git repos, shallow clones, binary files, large diffs

**Acceptance Criteria** (FR-001 to FR-007):
- `git_log` returns commit history with filters (limit, since, until, author)
- `git_blame` returns line-by-line authorship with commit metadata
- `git_diff` compares two refs and returns unified diff format
- All tools handle non-git repos gracefully ("Not a git repository" message)
- Input sanitization prevents command injection (regex validation)
- Results formatted as markdown with syntax highlighting
- Session tracking records which git commands used (sessions.git_tools_used)
- All tests passing (90%+ coverage)

**Duration**: 5-7 days

---

### Phase 2: Smart Chunking (Week 2-3) - **P1 Feature**

**Goal**: Search returns function/class-level results instead of file-level.

**Tasks**:
1. ✅ Write tests for `chunk-extractor.ts` (AST parsing logic)
2. Implement `chunk-extractor.ts` (TDD: parse functions, classes, methods)
3. Handle nested functions (parent references, scope path)
4. Handle fallback cases (syntax errors, minified code, generated code)
5. Create `chunk-storage.ts` (SQLite CRUD for chunks table)
6. Update `EmbeddingService` to generate per-chunk embeddings (not per-file)
7. Update `context_search` tool to return chunk-level results
8. Add content-hash caching to avoid redundant parsing
9. Write migration script to convert v1.0 file embeddings → v2.0 chunk embeddings
10. Integration test: Search returns 20-150 line chunks, not 500+ line files

**Acceptance Criteria** (FR-008 to FR-014):
- AST parser identifies functions, classes, methods, interfaces as chunks
- Each chunk has metadata: type, name, start/end lines, parent reference
- Chunks include context envelope (JSDoc + 3 lines before/after)
- Nested functions up to 3 levels deep handled correctly
- Syntax errors fall back to file-level chunk gracefully
- Search results return chunks with surrounding context
- Chunk granularity stats tracked (avg chunks/file, size distribution, fallback rate)
- Migration preserves v1.0 data while upgrading to v2.0
- All tests passing (90%+ coverage)

**Duration**: 7-10 days

---

### Phase 3: File Watching (Week 3-4) - **P2 Feature**

**Goal**: Context updates automatically when files change (no manual refresh).

**Tasks**:
1. ✅ Write tests for `FileWatcherService` (add/change/unlink events)
2. Implement `FileWatcherService` with chokidar (TDD)
3. Configure debouncing (400ms stability threshold)
4. Configure exclude patterns (node_modules, .git, dist, build)
5. Connect watcher to `ChunkingService` (on change → re-chunk file)
6. Connect to `EmbeddingService` (on change → re-embed chunks)
7. Handle renames (delete old path, create new path)
8. Implement auto-restart with exponential backoff (1s, 2s, 4s, 8s, 16s delays)
9. Track file watcher events in database (change_events table)
10. Add metrics: `file_watcher_events_total` counter

**Acceptance Criteria** (FR-015 to FR-021):
- File changes detected within 500ms (400ms debounce + 100ms processing)
- Debouncing prevents thrash during rapid saves (waits for 1s of no activity)
- Excluded directories not watched (node_modules, .git, dist, build)
- Embeddings invalidated and regenerated within 2 seconds of change
- Renames handled correctly (old path embeddings deleted, new path created)
- Auto-restart on crash with exponential backoff (up to 5 retries)
- All watcher events logged at DEBUG level
- RAM overhead <50MB for 5,000 files
- All tests passing (90%+ coverage)

**Duration**: 5-7 days

---

### Phase 4: Observability (Week 4) - **P2 Feature**

**Goal**: Prometheus metrics and health checks for production monitoring.

**Tasks**:
1. Set up prom-client registry with default metrics
2. Define custom metrics:
   - `kioku_embedding_queue_depth` (gauge)
   - `kioku_api_latency_seconds` (histogram with p50/p95/p99)
   - `kioku_file_watcher_events_total` (counter)
   - `kioku_errors_total` (counter with type label)
   - `kioku_active_sessions` (gauge)
   - `kioku_context_window_usage_percent` (gauge)
3. Instrument code with timers, counters, gauges
4. Implement health check logic (`HealthChecker` class)
5. Create Fastify server for `/metrics` and `/health` endpoints
6. Add response caching (1s TTL) to hit <50ms p99 target
7. Integration test: Prometheus scrapes /metrics successfully

**Acceptance Criteria** (FR-065 to FR-069):
- `/metrics` endpoint returns Prometheus text format
- `/health` endpoint returns JSON with status (healthy/degraded/unhealthy)
- Status codes: 200 (healthy), 429 (degraded), 503 (unhealthy)
- Health checks cover: database, vectordb, file_watcher
- Metrics endpoint responds in <50ms (p99)
- All metrics collection errors logged at WARN level without blocking
- Metrics server runs on port 9090 (configurable)
- All tests passing (90%+ coverage)

**Duration**: 3-4 days

---

### Phase 5: AI Discovery (Week 5) - **P2 Feature**

**Goal**: AI refines discoveries from sessions using Claude API.

**Tasks**:
1. Set up Anthropic API client (`infrastructure/external/anthropic-client.ts`)
2. Implement redaction logic for sensitive data (API keys, tokens, PII)
3. ✅ Write tests for `AIDiscoveryService`
4. Implement `AIDiscoveryService` (TDD: send messages to Claude, parse response)
5. Update session end handler to trigger AI discovery
6. Store refined discoveries in database (refined_discoveries table)
7. Filter by confidence threshold (≥0.6)
8. Implement fallback to regex-only if API unavailable
9. Cache AI refinement results per session
10. Track costs: `ai_discovery_tokens_used`, `ai_discovery_cost_usd`

**Acceptance Criteria** (FR-022 to FR-028):
- Session messages sent to Anthropic Claude API after regex extraction
- AI returns: type, confidence (0-1), refined description, suggested module, evidence
- Discoveries with confidence ≥0.6 persisted to database
- Sensitive patterns redacted before API call (API keys, OAuth, email, phone, IP, credit cards, SSN)
- Configurable allow-list for false positive overrides (config.yaml)
- Fallback to regex-only on API error (rate limit, network, quota)
- Results cached per session to avoid re-processing
- All tests passing (90%+ coverage)

**Duration**: 5-7 days

---

### Phase 6: Re-ranking (Week 5) - **P2 Feature**

**Goal**: Search results ranked by recency, module, and frequency (not just semantic score).

**Tasks**:
1. ✅ Write tests for `ranking-calculator.ts` (pure function)
2. Implement boost calculations:
   - Recency: 1.5x (24h), 1.2x (7d), 1.0x (older)
   - Module: 1.3x (same module as current work)
   - Frequency: 1 + (access_count / 100), capped at 1.5x
3. Update `context_search` tool to apply boosts
4. Track file access statistics (last_accessed, access_count)
5. Expose ranking details in search results (debug metadata)
6. Add config options to customize boost weights (config.yaml)
7. Log ranking details at DEBUG level

**Acceptance Criteria** (FR-029 to FR-034):
- Recency boost applied based on last_accessed timestamp
- Module boost applied if result from same module as current work
- Frequency boost applied based on access_count
- Boosts combined multiplicatively: `final_score = semantic * recency * module * frequency`
- Ranking details logged at DEBUG level (original scores, boosts, final scores)
- Boost factors configurable in config.yaml
- All tests passing (90%+ coverage)

**Duration**: 3-4 days

---

### Phase 7: Multi-Project (Week 6) - **P3 Feature**

**Goal**: Link projects and search across multiple codebases.

**Tasks**:
1. Create `workspace.yaml` handler (`infrastructure/storage/workspace-storage.ts`)
2. Implement `kioku link <path>` command (`infrastructure/cli/commands/link.ts`)
3. Update `context_search` to search linked projects (projectScope parameter)
4. Implement cross-reference tracking (imports, API calls, type usage)
5. Implement circular link detection (visited set during graph traversal)
6. Handle unavailable projects (moved, deleted, permissions)
7. Session tracking records which projects accessed

**Acceptance Criteria** (FR-035 to FR-041):
- `kioku link <path>` stores linked project in workspace.yaml
- Global search returns results from all linked projects (labeled by project)
- Cross-project references tracked (frontend imports from backend)
- File watcher invalidates cross-project embeddings on related changes
- Unavailable projects excluded from search with warning logged
- Circular links detected and prevented (A → B → A)
- Session records projects accessed
- All tests passing (90%+ coverage)

**Duration**: 5-7 days

---

### Phase 8: Dashboard (Week 7) - **P4 Feature**

**Goal**: Web UI for visual context inspection and debugging.

**Tasks**:
1. Create React app with Create React App (`dashboard/`)
2. Implement REST API endpoints:
   - `GET /api/project` (project overview)
   - `GET /api/sessions` (session timeline)
   - `GET /api/sessions/:id` (session details)
   - `GET /api/modules` (dependency graph)
   - `GET /api/embeddings` (stats)
   - `GET /api/context` (window usage)
   - `GET /api/linked-projects` (multi-project)
3. Build UI components:
   - `ProjectOverview.tsx`
   - `SessionTimeline.tsx`
   - `ModuleGraph.tsx`
   - `EmbeddingsStats.tsx`
4. Implement polling (5-second interval) for real-time updates
5. Add `kioku dashboard` command to start server
6. Auto-open browser on start (unless `--no-browser` flag)

**Acceptance Criteria** (FR-042 to FR-049):
- `kioku dashboard` starts web server on port 3456
- Dashboard displays project overview (name, tech stack, stats)
- Session timeline shows past sessions with click-to-expand
- Module dependency graph interactive (color-coded by activity)
- Embeddings statistics displayed (count, queue, errors, disk usage)
- Dashboard polls /api/* every 5 seconds for updates
- Read-only (no mutations to prevent conflicts)
- Auto-opens browser on start
- All tests passing (90%+ coverage)

**Duration**: 5-7 days

---

### Phase 9: Onboarding & Diagnostics (Week 8) - **P4 Feature**

**Goal**: Guided setup and auto-repair for better UX.

**Tasks**:
1. Implement `kioku setup --interactive` wizard
2. Prompts: project type, OpenAI key, Anthropic key, editor choice
3. Validate API keys (test requests to OpenAI/Anthropic)
4. Generate MCP config for selected editor (Zed, Claude Code)
5. Run `kioku init` automatically after setup
6. Detect existing `.context/` and prompt for reconfigure
7. Implement `kioku doctor` command
8. Health checks: API keys, databases, MCP config, file permissions, embeddings freshness
9. Auto-repair: rebuild corrupted DB, re-index stale embeddings, fix permissions
10. Support `--fix` flag for automated repairs (no prompts)

**Acceptance Criteria** (FR-050 to FR-064):
- `kioku setup --interactive` launches step-by-step wizard
- Wizard prompts for: project type, API keys, editor
- API keys validated with test calls
- MCP config generated for selected editor
- `kioku init` runs automatically after setup
- Existing setup detected and offers reconfigure
- Success message displays: "✓ Setup complete! Run 'kioku serve'"
- `kioku doctor` runs comprehensive health checks
- Doctor reports: ✓ (healthy), ⚠ (warning), ❌ (error) with fixes
- Auto-repair offered for common issues (DB corruption, stale embeddings)
- `doctor --fix` applies repairs automatically
- All tests passing (90%+ coverage)

**Duration**: 5-7 days

---

## Testing Strategy

### Test Distribution (80-15-5 Rule)

```
Unit Tests (80%):
- Domain calculations (chunk-extractor, ranking-calculator) - 100% pure functions
- Application services (mocked infrastructure) - Use cases, orchestration
- Infrastructure adapters (mocked external APIs) - Storage, clients

Integration Tests (15%):
- Full workflows: git tool → MCP → Claude
- File watcher → chunking → embedding pipeline
- Multi-project search across linked projects
- Dashboard → REST API → MCP server data flow

E2E Tests (5%):
- Manual testing with real Claude Desktop
- Real git repository operations
- Real file watching on developer machine
- Real API calls to OpenAI/Anthropic (optional, cost consideration)
```

### TDD Workflow (Mandatory)

```
For each task:
1. 🔴 RED: Write failing test first
2. 🟢 GREEN: Write minimum code to pass
3. 🔵 REFACTOR: Improve code quality (keep tests passing)

Example:
# Test first
describe('extractChunks', () => {
  it('should extract function from code', () => {
    const chunks = extractChunks('function foo() {}', 'test.ts');
    expect(chunks[0].name).toBe('foo');
  });
});

# Run: bun test (FAILS - good!)
# Implement: extractChunks function
# Run: bun test (PASSES - good!)
# Refactor: Clean up code
# Run: bun test (STILL PASSES - good!)
```

### Coverage Requirements

- **Minimum**: 90% (statements, branches, functions, lines)
- **Domain layer**: 100% (pure functions, easy to test)
- **Application layer**: 95% (orchestration, use cases)
- **Infrastructure layer**: 80% (adapters, mock external deps)

### Quality Gate (Before Commit)

```bash
# Run full quality gate
bun run quality-gate

# Checks:
✓ TypeScript type check (bun run type-check)
✓ ESLint with architecture rules (bun run lint)
✓ Tests with coverage (bun test:coverage)

# Must pass:
✓ No TypeScript errors
✓ No ESLint errors (architecture boundaries enforced)
✓ All tests passing
✓ Coverage ≥ 90%
```

---

## Risk Mitigation

### High-Risk Areas

**1. AST Parsing Performance**
- **Risk**: 10,000 files × 30s = 5 min initialization
- **Mitigation**: Content-hash caching, incremental parsing, background processing, progress indicator
- **Fallback**: File-level chunking if parsing takes >60s

**2. File Watcher Resource Usage**
- **Risk**: 10,000 files × 50KB RAM = 500MB overhead
- **Mitigation**: Exclude node_modules (saves 40MB), debounce aggressively, allow disabling via config
- **Monitoring**: Track RAM usage with metrics, warn if >100MB

**3. API Cost Explosion**
- **Risk**: AI refinement × 100 sessions/month = $50-100/month
- **Mitigation**: Display cost estimates in setup, rate limit (10/day default), allow disabling
- **Monitoring**: Track tokens_used, cost_usd in database

**4. Multi-Project Complexity**
- **Risk**: Circular links, cascading re-embeddings
- **Mitigation**: Explicit link declarations, circular detection, 1-level depth limit
- **Fallback**: Disable cross-project features per project

**5. Breaking Changes from v1.0**
- **Risk**: v2.0 schema breaks existing installations
- **Mitigation**: Automatic migration script, backup `.context/` before migration, rollback on error
- **Testing**: Integration tests with v1.0 data

---

## Success Metrics

### Functional Success (Must Achieve)

- [ ] All 69 functional requirements implemented (FR-001 to FR-069)
- [ ] All 34 success criteria met (SC-001 to SC-034)
- [ ] 90%+ test coverage achieved (enforced by quality gate)
- [ ] All quality gates passing (type check, lint, tests)
- [ ] Zero critical bugs in production

### Performance Success (Measured)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Git tool latency | <2s (p95) | `kioku_api_latency_seconds{provider="git"}` |
| File change detection | <500ms | `kioku_file_watcher_events_total` timing |
| Metrics endpoint | <50ms (p99) | Prometheus scrape timing |
| Context search | <2s (p99) | `kioku_api_latency_seconds{operation="search"}` |
| AST parsing (5k files) | <30s first, <3s cached | Initialization logs |

### User Success (Validated)

- [ ] Users answer "Who wrote this?" in <5 seconds (SC-001)
- [ ] Search precision improves by 40% (SC-004: 85% relevant in top 5)
- [ ] Context freshness <2 seconds (SC-007)
- [ ] Discovery quality improves by 60% (SC-010: 80% acceptance rate)
- [ ] Setup time reduces from 30 min to <5 min (SC-021)

---

## Rollout Plan

### v2.0.0 Release (P1 + P2 Features)

**Target Date**: 8 weeks from start  
**Features**: Git Integration, Smart Chunking, File Watching, AI Discovery, Re-ranking, Observability  
**Validation**: 2-week dogfooding period on real projects

### v2.1.0 Release (P3 Features)

**Target Date**: +4 weeks after v2.0  
**Features**: Multi-Project Support  
**Validation**: Test with monorepo and multi-project workspaces

### v2.2.0 Release (P4 Features)

**Target Date**: +4 weeks after v2.1  
**Features**: Dashboard, Onboarding, Diagnostics  
**Validation**: User onboarding success rate >90%

---

## Dependencies Summary

### External Dependencies (New in v2.0)

```json
{
  "dependencies": {
    "simple-git": "^3.27.0",
    "chokidar": "^4.0.0",
    "prom-client": "^15.1.0",
    "fastify": "^4.28.0",
    "express": "^4.19.0"
  },
  "devDependencies": {
    "@types/chokidar": "^2.1.3",
    "@types/express": "^4.17.21"
  }
}
```

### Internal Dependencies (Existing from v1.0)

- @modelcontextprotocol/sdk (MCP protocol)
- better-sqlite3 (SQLite database)
- chromadb (Vector embeddings)
- @babel/parser, @babel/traverse (AST parsing)
- yaml (YAML parsing)
- openai (OpenAI API client)

---

## Next Steps

### Immediate (After Plan Approval)

1. **Run `/speckit.tasks`**: Break plan into actionable tasks with dependencies
2. **Run `/speckit.analyze`**: Validate spec ↔ plan ↔ tasks consistency
3. **Start Phase 0**: Foundation (install deps, create schemas, domain models)

### During Implementation

- **Daily**: Run quality gate (`bun run quality-gate`)
- **Per Phase**: Update progress, mark tasks complete
- **Per Feature**: Integration test with Claude Desktop
- **Weekly**: Review metrics, adjust timelines if needed

### Before Release

- **Dogfood v2.0**: Use on real project (this project) for 2 weeks
- **User testing**: Get feedback from 3-5 early adopters
- **Performance profiling**: Verify all targets met
- **Documentation**: Update README, CHANGELOG, migration guide

---

**END OF IMPLEMENTATION PLAN**
