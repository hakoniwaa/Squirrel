# Feature Specification: Kioku v2.0 - Advanced Context Intelligence

**Feature Branch**: `002-advanced-context-intelligence`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "Advanced Context Intelligence - Git Integration, Smart Chunking, and File Watching"

---

## Overview

Kioku v2.0 transforms the MVP's foundation into a comprehensive context intelligence system by adding historical awareness (Git integration), precision search (smart chunking), real-time freshness (file watching), advanced discovery (AI-based), intelligent ranking (boost factors), multi-project support, visual insights (dashboard), and improved onboarding.

**Building on v1.0.0**: The MVP established automatic session tracking, basic semantic search, and context management. v2.0 enhances every aspect with deeper intelligence and broader capabilities.

**Core Value Additions**:
- **Historical Context**: Understand code evolution through git history
- **Precision Search**: Function/class-level granularity instead of file-level
- **Zero-Latency Updates**: Real-time context refresh on file changes
- **AI-Enhanced Learning**: GPT-4 refinement of discoveries
- **Intelligent Ranking**: Context-aware result boosting
- **Multi-Project Intelligence**: Cross-project context linking
- **Visual Debugging**: Web dashboard for context inspection
- **Streamlined Onboarding**: Guided setup and diagnostics

---

## Clarifications

### Session 2025-10-09

- Q: How comprehensive should the default sensitive data redaction be for AI discovery refinement? → A: Moderate (+ PII + secrets) - Redact API keys, OAuth tokens, email addresses, phone numbers, IP addresses, credit card numbers, social security numbers with configurable allow-list.
- Q: What level of observability should v2.0 provide for production monitoring? → A: Structured metrics + health endpoint - Expose Prometheus-compatible metrics, track embedding queue depth, API latency (p50/p95/p99), file watcher events/sec, error rates by type, plus health endpoint for load balancer checks.

---

## User Scenarios & Testing

### User Story 1 - Git Historical Context (Priority: P1)

**As a** developer debugging unfamiliar code  
**I want to** see who wrote a function, when, and why (via commit messages)  
**So that** I understand the historical context and rationale behind implementation decisions

**Why this priority**: Historical context is the most requested feature from MVP users. Understanding "why" code exists is as important as understanding "what" it does. This directly addresses the pain point of inheriting code without context.

**Independent Test**: Can be fully tested by calling git tools on any repository with commit history and verifying markdown-formatted results include author, date, commit message, and code context.

**Acceptance Scenarios**:

1. **Given** I'm viewing a file in my editor  
   **When** I ask AI "Who wrote the `authenticateUser` function?"  
   **Then** AI calls `git_blame` tool and returns author, date, and commit message for those lines

2. **Given** I'm debugging a bug introduced recently  
   **When** I ask AI "Show me recent changes to auth module"  
   **Then** AI calls `git_log` with file path filter and returns last 10 commits affecting auth files

3. **Given** I want to understand what changed between versions  
   **When** I ask AI "What changed in the last release?"  
   **Then** AI calls `git_diff` between tags and summarizes key changes

4. **Given** A file has no git history (new file or non-repo)  
   **When** I ask about git history  
   **Then** System gracefully reports "No git history available" without errors

5. **Given** I'm working in a monorepo with multiple submodules  
   **When** I ask about commit history  
   **Then** System correctly identifies and searches within the appropriate git repository

---

### User Story 2 - Precise Code Search (Priority: P1)

**As a** developer searching for specific functionality  
**I want** search results at function/class level instead of entire files  
**So that** I get precise, relevant code snippets without irrelevant context

**Why this priority**: MVP's file-level search often returns 500+ line files when only a 20-line function is relevant. Function-level precision reduces cognitive load and improves search quality by 40%+.

**Independent Test**: Can be fully tested by searching for a function name and verifying results include only that function's code block (not the entire file), with proper context (function signature, docstring, surrounding context).

**Acceptance Scenarios**:

1. **Given** I search for "authentication logic"  
   **When** Semantic search runs with smart chunking enabled  
   **Then** Results show specific functions like `authenticateUser()`, `validateToken()` instead of entire auth files

2. **Given** A large file with multiple classes  
   **When** I search for "user validation"  
   **Then** Results include only the relevant `UserValidator` class, not the entire file with 10 other classes

3. **Given** Search returns a function  
   **When** Viewing results  
   **Then** Results include function signature, docstring, and 3 lines of surrounding context for readability

4. **Given** Code has nested functions or closures  
   **When** Chunking algorithm processes the file  
   **Then** Each function is correctly identified as a separate chunk (handles nesting up to 3 levels deep)

5. **Given** A file written in an unsupported language (e.g., Python in MVP)  
   **When** Chunking attempts to parse it  
   **Then** System falls back to file-level chunking gracefully without errors

---

### User Story 3 - Real-Time Context Freshness (Priority: P2)

**As a** developer actively coding  
**I want** context to update automatically when I save files  
**So that** AI always has the latest code without manual refresh commands

**Why this priority**: Stale context causes AI to reference outdated code, leading to incorrect suggestions. Real-time updates eliminate the "refresh" mental overhead and ensure AI accuracy.

**Independent Test**: Can be fully tested by saving a file, waiting <2 seconds, then verifying the context search returns updated content and embeddings reflect the new code.

**Acceptance Scenarios**:

1. **Given** File watcher is running  
   **When** I save a TypeScript file  
   **Then** System detects change within 500ms and queues re-embedding

2. **Given** A file's embeddings are outdated  
   **When** Re-embedding completes  
   **Then** Vector database updated and search returns new content on next query (within 2 seconds of save)

3. **Given** I save 10 files rapidly (e.g., auto-format on save)  
   **When** File watcher detects burst of changes  
   **Then** System debounces updates (waits 400ms of no activity) before re-embedding to avoid thrashing

4. **Given** I'm working in a large monorepo (10,000+ files)  
   **When** File watcher initializes  
   **Then** Only project files are watched (excludes `node_modules/`, `.git/`, `dist/`), keeping resource usage <50MB RAM

5. **Given** File watcher crashes or loses connection  
   **When** Service manager detects failure  
   **Then** Auto-restart within 5 seconds with error logged, no manual intervention required

---

### User Story 4 - AI-Enhanced Discovery Extraction (Priority: P2)

**As a** developer who just completed a coding session  
**I want** discoveries extracted and refined by AI  
**So that** patterns, rules, and insights are higher quality and more accurate than regex-based extraction

**Why this priority**: MVP's regex-based discovery extraction is limited—it misses nuanced patterns and produces false positives. GPT-4 refinement improves extraction quality by 60%+ through contextual understanding.

**Independent Test**: Can be fully tested by completing a mock session with conversation messages, verifying GPT-4 extracts discoveries with confidence scores, and comparing quality to regex-only baseline (fewer false positives, more nuanced patterns captured).

**Acceptance Scenarios**:

1. **Given** A coding session ends with 50 conversation messages  
   **When** Discovery extraction runs  
   **Then** System first applies regex patterns (fast, cheap), then sends high-confidence matches to GPT-4 for refinement

2. **Given** GPT-4 analyzes conversation context  
   **When** Refining a potential discovery  
   **Then** AI returns: discovery type, confidence score (0-1), refined description, and suggested module mapping

3. **Given** GPT-4 identifies a low-confidence discovery (score <0.6)  
   **When** Post-processing results  
   **Then** System excludes it from project.yaml enrichment but logs for future review

4. **Given** API rate limits or quota exceeded  
   **When** AI extraction fails  
   **Then** System falls back to regex-only extraction gracefully, logs warning, continues without blocking

5. **Given** A session contains sensitive information (API keys, passwords)  
   **When** Preparing messages for AI analysis  
   **Then** System redacts sensitive patterns before sending to external API (ANTHROPIC_API_KEY never sent)

---

### User Story 5 - Intelligent Result Ranking (Priority: P3)

**As a** developer searching for code  
**I want** results ranked by relevance (recency, module context, usage frequency)  
**So that** the most useful results appear first, not just semantic similarity

**Why this priority**: Pure semantic search can return old, unused code as top results. Ranking with boost factors surfaces recently touched, frequently accessed code—typically 2-3x more relevant to current work.

**Independent Test**: Can be fully tested by searching a term that appears in both recent and old code, then verifying recent files rank higher due to recency boost, and active module files rank higher due to module boost.

**Acceptance Scenarios**:

1. **Given** Search results with equal semantic similarity scores  
   **When** Ranking algorithm applies boosts  
   **Then** Files accessed in last 24 hours get 1.5x score boost, last week get 1.2x boost

2. **Given** I'm currently working in the "auth" module  
   **When** Searching for "validation"  
   **Then** Results from "auth" module boosted by 1.3x over other modules

3. **Given** A file has been accessed 20 times this week  
   **When** Ranking considers access patterns  
   **Then** File gets frequency boost: `1 + (access_count / 100)` capped at 1.5x

4. **Given** Multiple boost factors apply (recency + module + frequency)  
   **When** Calculating final scores  
   **Then** Boosts are multiplicative: `semantic_score * recency_boost * module_boost * freq_boost`

5. **Given** User preferences stored (e.g., prefers tests over implementation)  
   **When** Ranking results  
   **Then** System applies configurable preference boost (default: no preference, user can customize)

---

### User Story 6 - Multi-Project Context (Priority: P3)

**As a** developer working across multiple related projects  
**I want** Kioku to link context between projects  
**So that** I can search across codebases and understand cross-project dependencies

**Why this priority**: Modern development often spans microservices, libraries, and applications. Cross-project context enables "How does the API handle this?" queries that span repos—critical for full-stack or platform engineers.

**Independent Test**: Can be fully tested by initializing Kioku in 2 projects, linking them via configuration, then verifying search can return results from both projects and cross-references are tracked.

**Acceptance Scenarios**:

1. **Given** I have projects "frontend" and "backend" in a workspace  
   **When** I run `kioku link ../backend` from frontend  
   **Then** Configuration stores linked project paths in `.context/workspace.yaml`

2. **Given** Linked projects configured  
   **When** I search "authentication API"  
   **Then** Results include matches from both frontend (API client) and backend (API implementation), clearly labeled by project

3. **Given** Backend API changes an endpoint  
   **When** File watcher detects the change  
   **Then** System invalidates related embeddings in frontend project that reference that endpoint (cross-project invalidation)

4. **Given** I ask "How does the payment API work?"  
   **When** AI searches across linked projects  
   **Then** Results aggregate context from: backend implementation, frontend usage examples, shared types/interfaces

5. **Given** A linked project is moved or deleted  
   **When** System tries to access it  
   **Then** Graceful degradation: search excludes unavailable project, logs warning, continues with available projects only

---

### User Story 7 - Visual Context Dashboard (Priority: P4)

**As a** developer debugging context issues  
**I want** a web dashboard showing context state, sessions, and discovery graph  
**So that** I can visually inspect what Kioku knows and troubleshoot issues

**Why this priority**: While CLI commands work, visual inspection is faster for debugging. Dashboard provides at-a-glance insights into context health, session patterns, and knowledge graph—reducing troubleshooting time by 70%.

**Independent Test**: Can be fully tested by starting dashboard server, navigating to localhost URL, and verifying UI displays: project overview, module list, session timeline, discovery graph, and embedding statistics.

**Acceptance Scenarios**:

1. **Given** Dashboard server started (`kioku dashboard`)  
   **When** I navigate to `http://localhost:3456`  
   **Then** Dashboard loads showing: project name, tech stack, module count, active session status

2. **Given** Viewing session timeline  
   **When** I click on a specific session  
   **Then** Detail view shows: files accessed (with heatmap), topics discussed, discoveries extracted, duration

3. **Given** Viewing module graph  
   **When** Rendering dependencies  
   **Then** Interactive graph shows modules as nodes, imports as edges, color-coded by activity (green=active, gray=stale)

4. **Given** Viewing context window usage  
   **When** Dashboard polls current state  
   **Then** Real-time gauge shows: current tokens (65,234), max (100,000), percentage (65%), with green/yellow/red zones

5. **Given** I want to debug why a search failed  
   **When** Viewing embeddings stats  
   **Then** Dashboard shows: total embeddings count, last generated timestamp, queue size, error log (if any)

---

### User Story 8 - Guided Onboarding (Priority: P4)

**As a** new Kioku user  
**I want** an interactive setup guide  
**So that** I can configure the tool correctly without reading docs

**Why this priority**: MVP requires reading documentation to configure MCP and API keys. Guided setup reduces time-to-first-success from 30 minutes to 5 minutes, improving adoption for new users.

**Independent Test**: Can be fully tested by running `kioku setup --interactive` in a fresh environment, following prompts, and verifying final configuration is valid and server starts successfully.

**Acceptance Scenarios**:

1. **Given** I run `kioku setup --interactive` for the first time  
   **When** Setup wizard starts  
   **Then** Prompts ask: (1) Project type? (2) OpenAI API key? (3) Editor (Zed/Claude Code)? (4) Test connection?

2. **Given** I provide an invalid OpenAI API key  
   **When** Setup tests the key  
   **Then** Error message explains issue ("Invalid key format" or "API returned 401"), prompts to re-enter

3. **Given** Setup completes successfully  
   **When** Wizard finishes  
   **Then** Creates: `.context/` directory, `project.yaml`, MCP config for selected editor, shows "✓ Ready! Run 'kioku serve'" message

4. **Given** User's editor is not Zed or Claude Code  
   **When** Setup asks for editor  
   **Then** Option "Other (manual setup)" provided, displays manual config instructions at end

5. **Given** I run setup in a project already initialized  
   **When** Setup detects existing `.context/`  
   **Then** Prompts: "Kioku already initialized. Reconfigure? (y/n)" and preserves existing data if "n"

---

### User Story 9 - Advanced Diagnostics (Priority: P4)

**As a** developer troubleshooting Kioku issues  
**I want** a `kioku doctor` command that auto-detects and fixes common problems  
**So that** I can resolve issues without manual debugging

**Why this priority**: Common issues (missing API keys, corrupted databases, stale embeddings) require technical knowledge to fix. Auto-diagnostics and repair reduce support burden and improve user experience.

**Independent Test**: Can be fully tested by intentionally breaking something (e.g., delete database), running `kioku doctor`, and verifying tool detects issue, suggests fix, and repairs automatically (with confirmation).

**Acceptance Scenarios**:

1. **Given** I run `kioku doctor`  
   **When** Diagnostics run  
   **Then** Checks: (1) API keys valid, (2) Databases accessible, (3) MCP config correct, (4) File permissions OK, (5) Embeddings up-to-date

2. **Given** OpenAI API key is missing or invalid  
   **When** Doctor detects this  
   **Then** Reports "❌ OpenAI API key invalid" and suggests: "Run 'kioku config set OPENAI_API_KEY=sk-...'"

3. **Given** SQLite database is corrupted  
   **When** Doctor detects corruption  
   **Then** Prompts: "Database corrupted. Rebuild from backups? (y/n)" and restores from `.context/backups/` if available

4. **Given** Embeddings are 30 days old (stale)  
   **When** Doctor checks embedding freshness  
   **Then** Reports "⚠ Embeddings outdated (30 days old)" and offers: "Re-index now? (y/n)" with estimated time

5. **Given** All checks pass  
   **When** Doctor completes  
   **Then** Shows "✓ All systems healthy" summary with: database size, embedding count, last session date, context window usage

---

### Edge Cases

#### Git Integration Edge Cases

- **Shallow clones**: Repository has `--depth=1` clone—git log limited. Handle gracefully, note in results.
- **Detached HEAD**: Not on a branch—git commands work but branch names unavailable. Show commit SHA instead.
- **Merge conflicts**: File has conflict markers—git blame may fail. Show warning, skip conflicted sections.
- **Binary files**: Git diff on images/binaries—skip or show "binary file changed" message.
- **Large commits**: Commit touches 500+ files—limit diff output to first 50 files + summary.
- **Non-existent commits**: User asks for diff with invalid SHA—validate and show clear error.

#### Smart Chunking Edge Cases

- **Minified code**: Single-line files can't be chunked meaningfully—fall back to file-level chunk.
- **Generated code**: Files with thousands of repetitive functions—chunk but flag as "generated" in metadata.
- **Syntax errors**: File doesn't parse—fall back to simple line-based chunking (every 50 lines).
- **Mixed languages**: File contains embedded languages (JSX, Vue)—parser handles outer language, treats embedded as text.
- **Macro-heavy code**: Preprocessor macros obscure structure—chunk based on visible code, note limitation.

#### File Watcher Edge Cases

- **Symlinks**: Watched directory contains symlinks—resolve and watch targets (detect cycles, avoid infinite loops).
- **Permission denied**: Can't read file due to permissions—log warning, skip file, continue watching others.
- **Rapid saves**: Auto-save every 1 second—debounce to avoid re-embedding thrash (wait 400ms stability threshold).
- **Renamed files**: File renamed—invalidate old path's embeddings, create new for new path.
- **Deleted files**: Watched file deleted—remove from embeddings, log event, don't re-trigger on restore from trash.
- **Editor temp files**: `.swp`, `.tmp`, `~` files created—ignore based on configurable pattern list.

#### AI Discovery Edge Cases

- **API quota exceeded**: Anthropic rate limit hit—queue for retry, fall back to regex-only in meantime.
- **Malformed responses**: GPT-4 returns invalid JSON—catch parsing error, log raw response, skip that discovery.
- **Hallucinations**: AI invents patterns not in code—validate against source before accepting (confidence threshold).
- **Long messages**: Session has 200+ messages exceeding API limit—chunk into batches of 50, process separately.
- **Sensitive data**: Code contains API keys in strings—redact before sending to API (regex pattern list).

#### Multi-Project Edge Cases

- **Circular links**: Project A links to B, B links to A—detect cycles, break with warning, use directed graph.
- **Version mismatches**: Linked projects have different Kioku versions—check compatibility, warn if schema differs.
- **Path conflicts**: Two projects have files with same relative path—disambiguate with project prefix in results.
- **Network drives**: Linked project on slow network mount—timeout after 5s, mark unavailable, continue without it.
- **Git submodules**: Project contains submodules—treat as separate linked projects if initialized with Kioku.

#### Dashboard Edge Cases

- **Port already in use**: 3456 occupied—try 3457, 3458, ..., up to 3465, then fail with clear message.
- **No browser available**: Headless server environment—show URL, suggest SSH tunnel or remote access.
- **Large graphs**: 100+ modules overwhelm visualization—paginate or zoom-to-fit with collapse/expand nodes.
- **Concurrent access**: Two users open dashboard—read-only mode, no mutations, show warning if data changes underneath.
- **Stale data**: Dashboard open while server restarts—detect disconnect, show "Reconnecting..." overlay, auto-refresh.

---

## Requirements

### Functional Requirements

#### Git Integration (High Priority)

- **FR-001**: System MUST provide `git_log` MCP tool that returns commit history for specified file paths with filters: limit (default 10), since (date/tag), until (date/tag), author (email/name)
- **FR-002**: System MUST provide `git_blame` MCP tool that returns line-by-line authorship for files with: line ranges (optional), commit SHA, author name/email, date, commit message excerpt
- **FR-003**: System MUST provide `git_diff` MCP tool that compares two commits/branches/tags and returns: added/removed/modified files, line-level diffs, summary statistics (files changed, insertions, deletions)
- **FR-004**: Git tools MUST handle repositories without `.git` gracefully by returning clear message "Not a git repository" without crashing server
- **FR-005**: Git tools MUST sanitize user inputs (file paths, commit SHAs) to prevent command injection attacks
- **FR-006**: Git tool results MUST be formatted as markdown with syntax highlighting for code diffs
- **FR-007**: System MUST track git tool usage in session context (which commits/files queried) for future correlation with discoveries

#### Smart Chunking (High Priority)

- **FR-008**: System MUST parse TypeScript/JavaScript files using AST (Abstract Syntax Tree) to identify functions, classes, methods, and interfaces as discrete chunks
- **FR-009**: System MUST generate embeddings at chunk level (function/class) instead of file level, with metadata: chunk type (function/class/interface), start line, end line, parent scope
- **FR-010**: System MUST include surrounding context in chunk embeddings: function signature, JSDoc comments, 3 lines before/after for readability
- **FR-011**: System MUST handle nested functions by creating hierarchical chunks: parent function as one chunk, nested functions as separate chunks with parent reference
- **FR-012**: System MUST fall back to file-level chunking when AST parsing fails (syntax errors, unsupported constructs) without blocking embeddings
- **FR-013**: Search results MUST return chunk-level matches with: chunk content, file path, line range, surrounding context, confidence score
- **FR-014**: System MUST track chunk granularity statistics: avg chunks per file, chunk size distribution, fallback rate for monitoring quality

#### File Watcher (Medium Priority)

- **FR-015**: System MUST monitor project directory for file changes (create, modify, delete, rename) using native OS file system events (fsevents/inotify/ReadDirectoryChangesW)
- **FR-016**: System MUST debounce file change events by 400ms (wait for no activity) before triggering re-embedding to avoid thrash during rapid saves
- **FR-017**: System MUST exclude directories from watching: `node_modules/`, `.git/`, `dist/`, `build/`, `.next/`, configurable via `.context/config.yaml`
- **FR-018**: System MUST invalidate embeddings for modified files and re-generate within 2 seconds of change detection
- **FR-019**: File watcher MUST handle renames by: deleting old path's embeddings, creating new path's embeddings, preserving access statistics
- **FR-020**: File watcher MUST auto-restart if crashed, with exponential backoff: 1s, 2s, 4s, 8s, 16s delays between retries, max 5 retry attempts (6 total attempts including initial) before giving up
- **FR-021**: System MUST log all file watcher events (files changed, embeddings invalidated, errors) at DEBUG level for troubleshooting

#### AI-Based Discovery (Medium Priority)

- **FR-022**: System MUST send session messages to Anthropic Claude API (GPT-4 alternative) for discovery refinement after regex extraction completes
- **FR-023**: AI refinement MUST receive: regex-extracted discoveries (with confidence), full message context (last 50 messages max), current project.yaml for module mapping
- **FR-024**: AI MUST return for each discovery: type (pattern/rule/decision/issue), confidence score (0-1), refined description, suggested module, supporting evidence (message excerpt)
- **FR-025**: System MUST only persist discoveries with confidence >= 0.6 to project.yaml; low-confidence discoveries logged for review
- **FR-026**: System MUST redact sensitive patterns before sending to API using moderate security approach: API keys (sk-, pk-, Bearer patterns), OAuth tokens, email addresses (RFC 5322), phone numbers (E.164 format), IP addresses (IPv4/IPv6), credit card numbers (Luhn validation), social security numbers (XXX-XX-XXXX). System MUST maintain configurable allow-list in `config.yaml` for false positive overrides. Redaction replaces sensitive data with `[REDACTED:<type>]` placeholder.
- **FR-027**: System MUST fall back to regex-only extraction if AI API unavailable (rate limit, network error, quota exceeded) and log warning
- **FR-028**: System MUST cache AI refinement results per session to avoid re-processing same messages on retry

#### Re-ranking & Boost (Medium Priority)

- **FR-029**: Search results MUST apply recency boost: files accessed in last 24h get 1.5x score, last 7 days get 1.2x, older get 1.0x
- **FR-030**: Search results MUST apply module boost: if user is in specific module (detected from file path), results from that module get 1.3x boost
- **FR-031**: Search results MUST apply frequency boost: `1 + (access_count / 100)` capped at 1.5x based on session access statistics
- **FR-032**: System MUST combine boosts multiplicatively: `final_score = semantic_score * recency_boost * module_boost * frequency_boost`
- **FR-033**: System MUST log ranking details at DEBUG level: original scores, applied boosts, final scores for debugging ranking issues
- **FR-034**: System MUST provide configuration option to disable/customize boost factors in `config.yaml`: `ranking.recency_weight`, `ranking.module_weight`, `ranking.frequency_weight`

#### Multi-Repo Support (Medium Priority)

- **FR-035**: System MUST support linking multiple projects via `kioku link <path>` command which stores linked project paths in `.context/workspace.yaml`
- **FR-036**: System MUST search across all linked projects when global search enabled (default), with results clearly labeled by project name
- **FR-037**: System MUST track cross-project references: if frontend file imports from backend, metadata stores this relationship
- **FR-038**: File watcher MUST invalidate cross-project embeddings when related files change (e.g., API schema change invalidates client-side types)
- **FR-039**: System MUST handle linked projects being unavailable (moved, deleted, permissions) by: logging warning, excluding from search, continuing with available projects
- **FR-040**: System MUST detect circular links (A → B → A) and prevent infinite loops by maintaining visited set during graph traversal
- **FR-041**: Session tracking MUST record which projects were accessed to provide cross-project activity insights

#### Dashboard UI (Low Priority)

- **FR-042**: System MUST provide `kioku dashboard` command that starts web server on port 3456 (or next available port 3457-3465)
- **FR-043**: Dashboard MUST display project overview page: name, tech stack, module count, total files, active session status, context window usage gauge
- **FR-044**: Dashboard MUST display session timeline: list of past sessions with date, duration, files accessed, discoveries count, click to expand details
- **FR-045**: Dashboard MUST display module dependency graph: interactive visualization with modules as nodes, imports as edges, color-coded by recent activity
- **FR-046**: Dashboard MUST display embeddings statistics: total count, last generated timestamp, queue size, error log, disk usage
- **FR-047**: Dashboard MUST poll MCP server every 5 seconds for real-time updates (context window usage, active session, background services status)
- **FR-048**: Dashboard MUST be read-only (no mutations) to prevent conflicts with MCP server operations
- **FR-049**: Dashboard MUST be accessible at `http://localhost:<port>` with auto-open browser on start (unless `--no-browser` flag)

#### Guided Onboarding (Low Priority)

- **FR-050**: System MUST provide `kioku setup --interactive` command that launches step-by-step wizard
- **FR-051**: Setup wizard MUST prompt for: project type (web-app/api/cli/library/fullstack), OpenAI API key, Anthropic API key (optional), editor choice (Zed/Claude Code/Other)
- **FR-052**: Setup wizard MUST validate API keys by making test requests: OpenAI embeddings API test call, Anthropic API test call (if provided)
- **FR-053**: Setup wizard MUST generate MCP configuration file for selected editor: `~/.config/zed/mcp.json` for Zed, `~/.claude/claude_desktop_config.json` for Claude Code
- **FR-054**: Setup wizard MUST run `kioku init` automatically after configuration completes to initialize project context
- **FR-055**: Setup wizard MUST detect if `.context/` already exists and prompt: "Reconfigure? (y/n)" to avoid overwriting existing setup
- **FR-056**: Setup wizard MUST display success message with next steps: "✓ Setup complete! Run 'kioku serve' or restart your editor"

#### Observability & Monitoring (Medium Priority)

- **FR-065**: System MUST expose Prometheus-compatible metrics endpoint at `/metrics` when MCP server running
- **FR-066**: System MUST track and expose these metrics: `embedding_queue_depth` (gauge), `api_latency_seconds` (histogram with p50/p95/p99), `file_watcher_events_per_second` (counter), `errors_total` (counter with type label), `active_sessions` (gauge), `context_window_usage_percent` (gauge)
- **FR-067**: System MUST provide health check endpoint at `/health` returning JSON: `{status: "healthy"|"degraded"|"unhealthy", checks: {database: bool, vectordb: bool, file_watcher: bool}, uptime_seconds: number}`
- **FR-068**: Health endpoint MUST return HTTP 200 for "healthy", 503 for "unhealthy", 429 for "degraded" (some services down but core functional)
- **FR-069**: System MUST log all metrics collection errors at WARN level without blocking normal operations

#### Advanced Diagnostics (Low Priority)

- **FR-057**: System MUST provide `kioku doctor` command that runs comprehensive health checks on all components
- **FR-058**: Doctor MUST check API keys validity: test OpenAI embeddings call, test Anthropic API call (if configured), report status and quotas
- **FR-059**: Doctor MUST check database integrity: SQLite pragma integrity_check, ChromaDB collection health, file permissions on `.context/` directory
- **FR-060**: Doctor MUST check MCP configuration: parse config files, validate schema, check for common mistakes (wrong paths, syntax errors)
- **FR-061**: Doctor MUST check embeddings freshness: report oldest embedding timestamp, suggest re-index if >30 days old
- **FR-062**: Doctor MUST offer auto-repair for common issues: rebuild corrupted database from backups, re-generate stale embeddings, fix file permissions
- **FR-063**: Doctor MUST display health report with color-coded status: ✓ (green) healthy, ⚠ (yellow) warning, ❌ (red) error, with suggested fixes for warnings/errors
- **FR-064**: Doctor MUST support `--fix` flag to automatically apply repairs without prompts (for CI/CD or scripted maintenance)

### Key Entities

#### Git Context Entities

- **GitCommit**: Represents a single commit with: SHA (string), author name/email, date, message, files changed (array), parent SHA
- **GitBlame**: Line-by-line attribution with: line number, commit SHA, author, date, code content
- **GitDiff**: Change set between two commits with: file path, change type (added/modified/deleted), line diffs (additions/deletions), statistics

#### Chunking Entities

- **CodeChunk**: Discrete code unit with: chunk ID (UUID), file path, chunk type (function/class/interface/file), content (string), start line, end line, parent chunk ID (for nested), embedding vector ID reference, metadata (signature, JSDoc, complexity score)
- **ChunkIndex**: Mapping table linking: file path → chunk IDs for efficient lookup, chunk ID → embedding ID for search

#### File Watcher Entities

- **WatchedFile**: File being monitored with: absolute path, last modified timestamp, last embedded timestamp, change event history (array of timestamps and event types)
- **ChangeEvent**: File system event with: event type (create/modify/delete/rename), file path, old path (for renames), timestamp, processed flag (boolean)

#### AI Discovery Entities

- **RefinedDiscovery**: Enhanced discovery from AI with: discovery ID, raw content (from regex), refined content (from AI), confidence score (0-1), type (pattern/rule/decision/issue), supporting evidence (message excerpt), suggested module, metadata (API model used, tokens consumed)
- **AISession**: Tracking AI API usage with: session ID, messages sent count, tokens used, cost estimate, errors encountered, fallback activations

#### Multi-Project Entities

- **LinkedProject**: Related project with: name, absolute path, link type (workspace/dependency), status (available/unavailable), last accessed timestamp
- **CrossReference**: Inter-project dependency with: source project + file, target project + file, reference type (import/API call/type usage), confidence score

#### Dashboard Entities

- **DashboardState**: Snapshot of system state for UI with: context window usage (tokens), active session ID, background services status (array of service name + status), recent activity (last 10 events)
- **ModuleNode**: Graph visualization node with: module name, file count, recent access count (activity level), incoming edges count, outgoing edges count

---

## Success Criteria

### Measurable Outcomes

#### Git Integration Success Metrics

- **SC-001**: Users can answer "Who wrote this function?" in <5 seconds using git_blame tool
- **SC-002**: Git tools return results for 95% of queries (5% failure rate acceptable for edge cases like binary files)
- **SC-003**: Users report 70% reduction in time spent manually investigating code history (baseline: 10 min/day, target: 3 min/day)

#### Smart Chunking Success Metrics

- **SC-004**: Search result precision improves by 40% measured by: relevant results in top 5 / total top 5 results (baseline: 60%, target: 85%)
- **SC-005**: Average chunk size is 20-150 lines (function/class level granularity), not 500+ lines (file level)
- **SC-006**: 90% of searches return at least one chunk-level result (not falling back to file-level search)

#### File Watcher Success Metrics

- **SC-007**: Context freshness <2 seconds measured from file save to embedding updated in vector DB
- **SC-008**: Zero manual refresh commands needed during coding sessions (telemetry tracks refresh command usage drops to 0)
- **SC-009**: File watcher uptime >99.9% (restarts automatically on crash, no manual intervention)

#### AI Discovery Success Metrics

- **SC-010**: Discovery quality improves by 60% measured by: user-accepted discoveries / total discoveries (baseline: 50%, target: 80%)
- **SC-011**: False positive rate decreases by 50% measured by: rejected discoveries / total discoveries (baseline: 30%, target: 15%)
- **SC-012**: 90% of sessions have at least one AI-refined discovery accepted into project.yaml

#### Re-ranking Success Metrics

- **SC-013**: Users find relevant results in top 3 search results 85% of the time (up from 60% with pure semantic search)
- **SC-014**: Recent files (accessed <24h ago) appear in top 5 results when relevant 95% of the time

#### Multi-Project Success Metrics

- **SC-015**: Users can answer cross-project questions (e.g., "How does frontend call this API?") in <10 seconds
- **SC-016**: Cross-project search returns results from all linked projects <3 seconds (performance target)
- **SC-017**: 80% of full-stack developers link at least 2 projects within first week of v2 adoption

#### Dashboard Success Metrics

- **SC-018**: Users identify context issues via dashboard 70% faster than CLI (baseline: 5 min, target: 1.5 min)
- **SC-019**: Dashboard loads and renders project overview in <1 second on typical hardware (500 file project)
- **SC-020**: 50% of users access dashboard at least once per week for context inspection

#### Onboarding Success Metrics

- **SC-021**: Time to first successful MCP connection reduces from 30 min to <5 min with guided setup
- **SC-022**: 90% of users complete setup wizard without errors on first attempt
- **SC-023**: Support inquiries about initial setup decrease by 80% after guided onboarding release

#### Observability Success Metrics

- **SC-027**: Metrics endpoint responds in <50ms (p99) without impacting server performance
- **SC-028**: Health checks accurately detect 95% of service degradation within 10 seconds
- **SC-029**: Teams using Prometheus/Grafana can set up monitoring dashboards in <15 minutes

#### Diagnostics Success Metrics

- **SC-024**: Users self-resolve 70% of common issues using `kioku doctor` without external support
- **SC-025**: Doctor command identifies and suggests fixes for 90% of detectable issues (API key problems, database corruption, stale embeddings)
- **SC-026**: Auto-repair via `doctor --fix` successfully resolves 80% of fixable issues without manual intervention

### Overall v2.0 Success Criteria

- **SC-030**: Context intelligence score (composite of search precision, freshness, discovery quality) improves by 50% over v1.0 baseline
- **SC-031**: User satisfaction (measured by survey) increases from 75% to 90% "very satisfied" rating
- **SC-032**: Daily active usage increases by 100% (users find tool more valuable, use it daily instead of occasionally)
- **SC-033**: Zero context window saturation issues reported (v1.0 goal maintained)
- **SC-034**: v2.0 adoption reaches 60% of v1.0 users within 3 months of release

---

## Out of Scope for v2.0

The following features are valuable but deferred to future releases (v2.1+, v3.0):

### Deferred Features

- **Multi-language support**: Python, Go, Rust, Java parsing and chunking (v2.0 = TypeScript/JavaScript only)
- **Team collaboration**: Shared context, multi-user sessions, context sync (v2.0 = single developer)
- **Cloud sync**: Remote context backup, sync across machines (v2.0 = local only)
- **Plugin system**: Third-party extensions, custom tools (v2.0 = built-in tools only)
- **Advanced analytics**: Detailed usage reports, context growth trends (v2.0 = basic stats only)
- **IDE-native UI**: VSCode/Zed extensions with inline context views (v2.0 = web dashboard separate)
- **Git hosting integration**: GitHub/GitLab API integration for PR context, issues (v2.0 = local git only)
- **Enterprise features**: SSO, RBAC, audit logs, compliance (v2.0 = personal use)

### Explicitly Excluded

- **Code generation**: Kioku provides context, AI assistant generates code (not in Kioku's scope)
- **Version control**: Kioku uses git but doesn't replace git (read-only git operations)
- **Testing framework**: Kioku doesn't run tests (can provide test context though)
- **Deployment**: No CI/CD integration (context is development-time only)

---

## Assumptions

### Technical Assumptions

1. **Git availability**: Assume git CLI installed and accessible in PATH for git integration features
2. **File system access**: Assume read/write permissions on project directory and `.context/` directory
3. **Network access**: Assume internet connectivity for OpenAI and Anthropic API calls (with graceful degradation)
4. **Single project root**: Assume one `.context/` directory per project (multi-project via links, not multiple roots in one tree)
5. **TypeScript/JavaScript focus**: AST parsing assumes TS/JS syntax (other languages fall back to simple chunking)

### Environment Assumptions

1. **Development machine**: Kioku runs on developer's local machine with sufficient resources (4GB RAM, modern CPU)
2. **Modern editors**: MCP support available (Zed, Claude Code, or compatible editors)
3. **OS support**: Kioku works on macOS, Linux, Windows (file watcher uses native APIs)
4. **Node.js/Bun runtime**: Bun v1.1.29+ available (or Node.js 18+ for compatibility fallback)

### User Assumptions

1. **API keys**: Users provide their own OpenAI API keys (and optionally Anthropic keys)
2. **Git knowledge**: Users understand basic git concepts (commits, branches, diffs)
3. **Single developer**: v2.0 assumes one developer per project (no concurrent multi-user access)
4. **English language**: Code comments, commit messages, discoveries assumed in English (internationalization in future)

### Data Assumptions

1. **Reasonable project sizes**: Projects under 10,000 files perform optimally (larger projects work but may be slower)
2. **Text-based code**: Binary files, images, videos excluded from context (code only)
3. **UTF-8 encoding**: Source files assumed UTF-8 encoded (other encodings may cause parsing issues)
4. **Stable file paths**: Frequent mass file renames/moves may degrade context quality temporarily

### API Assumptions

1. **OpenAI API stability**: text-embedding-3-small model remains available and compatible
2. **Anthropic API stability**: Claude 3 Sonnet (or newer) available for discovery refinement
3. **API rate limits**: Users have sufficient quota for their usage patterns (graceful degradation on limits)
4. **API costs**: Users accept API costs associated with embeddings and AI refinement (documented in setup)

### Default Behaviors

1. **Auto-save enabled**: Sessions auto-save by default (no manual save required)
2. **File watcher on**: Automatically enabled when MCP server starts (can be disabled via config)
3. **AI refinement opt-in**: AI discovery refinement requires Anthropic API key (falls back to regex if not configured)
4. **Dashboard opt-in**: Dashboard not started by default (explicit `kioku dashboard` command required)

---

## Dependencies

### External Dependencies

- **Git**: Required for git integration features (version 2.30+)
- **OpenAI API**: Required for embeddings (text-embedding-3-small model)
- **Anthropic API**: Optional for AI-based discovery refinement (Claude 3 Sonnet)
- **Bun runtime**: Primary runtime (v1.1.29+), Node.js 18+ as fallback
- **MCP-compatible editor**: Zed or Claude Code for MCP protocol support

### Internal Dependencies (v1.0 Foundation)

- **MCP Server**: v2.0 extends existing MCP server with new tools
- **SQLite Database**: Existing sessions table extended with new columns for git/AI data
- **ChromaDB**: Existing vector database used for chunk-level embeddings
- **YAML Handler**: Existing project.yaml extended with new metadata sections
- **Session Manager**: Extended to track git tool usage and AI refinement events

### New Libraries/Tools (v2.0)

- **simple-git**: Node.js git wrapper for git CLI operations (git_log, git_blame, git_diff)
- **@babel/parser** + **@babel/traverse**: Already in v1.0, enhanced usage for AST-based chunking
- **chokidar**: Cross-platform file watcher library (fsevents on macOS, inotify on Linux)
- **prom-client**: Prometheus metrics client for Node.js (metrics endpoint, histograms, gauges, counters)
- **express** or **fastify**: Web server for dashboard UI and metrics/health endpoints (lightweight, minimal dependencies)
- **React** (optional): Dashboard frontend (or vanilla JS if React adds too much complexity)

---

## Risks & Mitigation

### Technical Risks

#### Risk 1: AST Parsing Performance
- **Description**: Parsing 10,000 files with AST could take 5+ minutes on initialization
- **Impact**: High (slow startup degrades UX)
- **Mitigation**: Incremental parsing (parse changed files only), parallelize parsing across CPU cores, cache parse results
- **Fallback**: Progress indicator + background processing (server starts before parsing completes)

#### Risk 2: File Watcher Resource Usage
- **Description**: Watching 10,000 files could consume 200+ MB RAM, high CPU on rapid changes
- **Impact**: Medium (performance degradation on large projects)
- **Mitigation**: Exclude large directories (node_modules), debounce aggressively, use native OS APIs (more efficient)
- **Fallback**: Allow disabling file watcher via config for very large projects

#### Risk 3: API Cost Explosion
- **Description**: AI refinement on every session could cost $5-10/month for heavy users
- **Impact**: Medium (user complaints about unexpected costs)
- **Mitigation**: Display cost estimates in setup, provide usage dashboard, allow disabling AI refinement
- **Fallback**: Rate limit AI calls (max 10/day default), warn users when approaching limits

#### Risk 4: Multi-Project Complexity
- **Description**: Cross-project invalidation logic could cause cascading re-embeddings (project A change triggers project B re-embed)
- **Impact**: High (performance, correctness issues)
- **Mitigation**: Limit cross-project depth (1 level only), use explicit link declarations (not auto-detect)
- **Fallback**: Allow disabling cross-project features per project basis

### User Experience Risks

#### Risk 5: Overwhelming Feature Set
- **Description**: 10 new features might confuse users, feature discovery low
- **Impact**: Medium (low adoption of advanced features)
- **Mitigation**: Phased rollout (P1 features in v2.0, P2-P4 in v2.1/v2.2), in-app feature tours
- **Fallback**: Comprehensive documentation, video tutorials

#### Risk 6: Breaking Changes from v1.0
- **Description**: Schema changes might break existing v1.0 installations
- **Impact**: High (user frustration, data loss risk)
- **Mitigation**: Automatic migration script (detect v1.0, backup, migrate to v2.0), clear upgrade guide
- **Fallback**: Dual support (v2.0 reads v1.0 format but writes v2.0)

---

## Migration from v1.0 to v2.0

### Breaking Changes

- **Database schema**: New columns in sessions table, new tables for chunks and git data
- **Configuration format**: `.context/config.yaml` gains new sections (watcher, ranking, ai, workspace)
- **Embedding structure**: Chunk-level embeddings alongside file-level (migration re-embeds)

### Migration Process

1. **Backup**: Automatic backup of `.context/` directory before migration
2. **Schema upgrade**: SQLite ALTER TABLE statements to add new columns
3. **Config merge**: Preserve user customizations, add new default settings
4. **Re-embedding**: Background re-embed with progress indicator (can take 10-30 min for large projects)
5. **Validation**: Post-migration health check, rollback if errors detected

### Upgrade Command

```bash
kioku upgrade --from v1.0.0 --to v2.0.0
```

Handles all migration automatically with user confirmation prompts.

---

## Notes

### Development Priorities

v2.0 development follows these priorities:
1. **P1 features first**: Git Integration, Smart Chunking (foundation for other features)
2. **P2 features second**: File Watcher, AI Discovery, Re-ranking (enhance core experience)
3. **P3 features third**: Multi-Project (advanced users)
4. **P4 features last**: Dashboard, Onboarding, Diagnostics (polish, usability)

### Phased Rollout Recommendation

- **v2.0.0**: P1 + P2 features (core intelligence enhancements)
- **v2.1.0**: P3 features (multi-project)
- **v2.2.0**: P4 features (dashboard, onboarding, diagnostics)

Allows faster release of high-value features, reduces v2.0 scope risk.

---

**END OF SPECIFICATION**
