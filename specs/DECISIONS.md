# Squirrel Decisions

Architecture Decision Records (ADR) for significant choices.

## ADR Format

Each decision follows:
- **ID**: ADR-NNN
- **Status**: proposed | accepted | deprecated | superseded
- **Date**: YYYY-MM-DD
- **Context**: Why this decision was needed
- **Decision**: What was decided
- **Consequences**: Trade-offs accepted

---

## ADR-001: Rust + Python Split Architecture

**Status:** accepted
**Date:** 2024-11-20

**Context:**
Need a system that watches files, serves MCP, and runs LLM operations. Single language options:
- Pure Rust: LLM libraries immature, PydanticAI not available
- Pure Python: File watching unreliable, MCP SDK less mature

**Decision:**
Split into Rust daemon (I/O, storage, MCP) and Python Memory Service (LLM operations). Communicate via JSON-RPC over Unix socket.

**Consequences:**
- (+) Best libraries for each domain
- (+) Clear separation of concerns
- (+) Daemon can run without Python for basic ops
- (-) IPC overhead (~1ms per call)
- (-) Two deployment artifacts
- (-) More complex build process

---

## ADR-002: SQLite with sqlite-vec

**Status:** accepted
**Date:** 2024-11-20

**Context:**
Need vector storage for embeddings. Options:
- PostgreSQL + pgvector: Requires server, overkill for local
- Pinecone/Weaviate: Cloud dependency, violates local-first
- SQLite + sqlite-vec: Local, single file, good enough performance
- ChromaDB: Python-only, can't use from Rust daemon

**Decision:**
Use SQLite with sqlite-vec extension for all storage including vectors.

**Consequences:**
- (+) Single file database, easy backup
- (+) No server process needed
- (+) Works from both Rust and Python
- (+) sqlite-vec handles cosine similarity efficiently
- (-) Limited to ~100k vectors before slowdown
- (-) No built-in sharding

---

## ADR-003: PydanticAI for Agent Framework

**Status:** accepted
**Date:** 2024-11-23

**Context:**
Need structured LLM outputs for memory extraction. Options:
- Raw API calls: No validation, manual JSON parsing
- LangChain: Heavy, over-engineered for our needs
- PydanticAI: Lightweight, Pydantic validation, good typing

**Decision:**
Use PydanticAI for all agent implementations.

**Consequences:**
- (+) Structured outputs with validation
- (+) Type safety
- (+) Clean agent patterns
- (+) Active development
- (-) Newer library, less ecosystem
- (-) Anthropic-focused (but supports OpenAI)

---

## ADR-004: 2-Tier Model Pipeline

**Status:** accepted
**Date:** 2024-11-23
**Updated:** 2025-01-20

**Context:**
Different operations have different accuracy/cost requirements:
- Log cleaning: Simple task, needs to be cheap
- Memory extraction: Core intelligence, needs quality

**Decision:**
Use two model tiers:
- `cheap_model`: Log Cleaner (default: Claude Haiku)
- `strong_model`: Memory Extractor (default: Claude Sonnet)

**Consequences:**
- (+) Cost optimization (cheap model for filtering)
- (+) Quality where it matters (strong model for extraction)
- (+) Provider flexibility via LiteLLM
- (-) Need to maintain two prompts
- (-) Configuration complexity

---

## ADR-006: Nix/devenv for Development Environment

**Status:** accepted
**Date:** 2024-11-23

**Context:**
Team uses Windows/WSL2/Mac. Need reproducible dev environment:
- Docker: Heavy, doesn't integrate well with IDEs
- Manual setup: Drift, "works on my machine"
- Nix/devenv: Declarative, reproducible, integrates with shells

**Decision:**
Use devenv.nix for development environment. All tools (Rust, Python, SQLite) managed by Nix.

**Consequences:**
- (+) Reproducible across all platforms (via WSL2 on Windows)
- (+) Single `devenv shell` command for setup
- (+) Declarative, matches spec-driven approach
- (+) No global installs needed
- (-) Nix learning curve
- (-) Windows requires WSL2

---

## ADR-007: Spec-Driven Development

**Status:** accepted
**Date:** 2024-11-23

**Context:**
Project is 98% AI-coded. Need to ensure consistency and quality:
- Ad-hoc development: AI generates inconsistent code
- Heavy process: Slows down iteration
- Spec-driven: Specs are source of truth, AI follows specs

**Decision:**
Adopt spec-driven development. All behavior defined in specs/ before implementation. Code is "compiled output" of specs.

**Consequences:**
- (+) AI has clear instructions
- (+) Consistent implementation
- (+) Documentation always current
- (+) Easy to review (review specs, not code)
- (-) More upfront work on specs
- (-) Need discipline to update specs first

---

## ADR-009: Unix Socket for IPC

**Status:** accepted
**Date:** 2024-11-20

**Context:**
Daemon and Memory Service need to communicate. Options:
- HTTP: Works but overhead for local
- gRPC: Complex setup for simple RPC
- Unix socket: Fast, secure, local-only

**Decision:**
Use Unix socket at `/tmp/sqrl.sock` with JSON-RPC 2.0 protocol. Windows uses named pipes.

**Consequences:**
- (+) No network exposure
- (+) Low latency (<1ms)
- (+) Simple protocol
- (-) Platform-specific paths
- (-) Need to handle socket cleanup

---

## ADR-012: Simplified Memory Architecture (v1 Redesign)

**Status:** accepted
**Date:** 2025-01-20

**Context:**
The original memory architecture was too complex:
- CR-Memory with opportunities, regret_hits, promotion/deprecation logic
- 5 memory kinds (preference, invariant, pattern, guard, note)
- 3 tiers (short_term, long_term, emergency)
- Guard interception for tool blocking
- Complex status lifecycle (provisional → active → deprecated)
- Declarative keys for conflict resolution

This complexity was premature. We needed to simplify for v1.

**Decision:**
Adopt simplified architecture with two memory types:

| Type | Storage | Access | Purpose |
|------|---------|--------|---------|
| User Style | `~/.sqrl/user_style.db` | Synced to agent.md files | Personal development preferences |
| Project Memory | `<repo>/.sqrl/memory.db` | MCP tool | Project-specific knowledge |

Key simplifications:

| Old | New |
|-----|-----|
| CR-Memory evaluation | Simple use_count ordering |
| 5 kinds, 3 tiers | No kinds/tiers, just text |
| Guard interception | Removed (v2 maybe) |
| Declarative keys | Removed |
| Complex status lifecycle | No status field |
| Context composition | Removed (return all memories) |

**Memory retrieval:**
- MCP tool returns ALL project memories grouped by category
- Ordered by use_count DESC within each category
- No semantic search, no filtering

**Model pipeline:**
1. Log Cleaner (cheap model) - compress, decide if worth processing
2. Memory Extractor (strong model) - extract user styles + project memories

**Consequences:**
- (+) Much simpler to implement and maintain
- (+) Easier to understand and debug
- (+) Less API cost (no complex evaluation)
- (+) Faster cold start (no bootstrapping period)
- (-) No intelligent context selection
- (-) May include irrelevant memories
- (-) No guard protection against dangerous actions

**Supersedes:**
- ADR-005: Declarative Keys (removed)
- ADR-008: Frustration Detection (removed)
- ADR-010: AI-Primary Memory Architecture (replaced by this simpler version)
- ADR-011: Historical Timeline (no longer needed without CR-Memory)

---

## ADR-013: B2B Focus with B2D Open Source

**Status:** accepted
**Date:** 2025-01-20

**Context:**
Need to determine business model and feature prioritization.

**Decision:**
B2B (Business to Business) is the main focus. B2D (Business to Developer) is the open source layer.

| Tier | Features | Monetization |
|------|----------|--------------|
| Free (B2D) | Local memory extraction, MCP access, Dashboard | Open source |
| Team (B2B) | Team style sync, shared project memory, analytics | Cloud subscription |

Team features require cloud service for sync and management.

**Consequences:**
- (+) Clear monetization path
- (+) Open source builds community
- (+) Team features justify cloud service
- (-) Need to build and maintain cloud infrastructure
- (-) Must ensure free tier is genuinely useful

---

## ADR-014: Minimal CLI Commands

**Status:** accepted
**Date:** 2025-01-20
**Updated:** 2025-02-01

**Context:**
Previous design had many CLI commands (search, forget, export, flush, policy). Most are unnecessary.

**Decision:**
Reduce CLI to essential commands:

| Command | Purpose |
|---------|---------|
| `sqrl` | Show help |
| `sqrl init` | Initialize project |
| `sqrl goaway [-f]` | Remove all Squirrel data |
| `sqrl status` | Show memories and doc debt |
| `sqrl mcp-serve` | Start MCP server (called by AI tool) |

Hidden internal commands for git hooks:
- `sqrl _internal docguard-record`
- `sqrl _internal docguard-check`

**Consequences:**
- (+) Simpler CLI, less code to maintain
- (+) Memory management via MCP (AI does it)
- (-) No quick command-line memory search

---

## ADR-015: Category-Based Project Memory Organization

**Status:** accepted
**Date:** 2025-01-20

**Context:**
Project memories need organization. Options:
- Flat list: Simple but hard to navigate
- By role (engineering, product, design): Overlapping concerns
- By project composition (frontend, backend, etc.): Natural fit

**Decision:**
Organize project memories by 4 default categories:

| Category | Description |
|----------|-------------|
| frontend | UI framework, components, styling |
| backend | API, database, services |
| docs_test | Documentation, testing |
| other | Everything else |

Users can add custom subcategories via Dashboard.

**Consequences:**
- (+) Natural organization for most projects
- (+) Simple to understand and use
- (+) MCP can return all grouped by category
- (-) May not fit all project types
- (-) Need subcategories for complex projects

---

## ADR-016: System Service for Daemon

**Status:** accepted
**Date:** 2025-01-25

**Context:**
The watcher daemon needs to run persistently in the background. Options:
- Foreground process: User must keep terminal open
- PID file management: Manual start/stop, doesn't survive reboot
- System service: Managed by OS, survives reboot, auto-restart

**Decision:**
Use platform-native system services:

| Platform | Service |
|----------|---------|
| Linux | systemd user service (`~/.config/systemd/user/dev.sqrl.daemon.service`) |
| macOS | launchd agent (`~/Library/LaunchAgents/dev.sqrl.daemon.plist`) |
| Windows | Task Scheduler (runs at logon) |

Hidden command `sqrl watch-daemon` runs the actual watcher loop. System service calls this command.

**Consequences:**
- (+) Survives reboots and terminal closures
- (+) Auto-restart on failure
- (+) Platform-native management (systemctl, launchctl)
- (+) No manual daemon management for users
- (-) Platform-specific code paths
- (-) Requires service installation on first init

---

## ADR-017: Doc Awareness Feature

**Status:** accepted
**Date:** 2025-01-26
**Updated:** 2025-02-01

**Context:**
AI tools often forget to update documentation when code changes. Projects have many docs (specs, README, etc.) that drift from reality. Need a way to detect when docs are stale and remind AI to update.

**Decision:**
Add doc debt tracking to Squirrel via git hooks:

| Component | Purpose |
|-----------|---------|
| Post-commit hook | Record doc debt when code changes but related docs don't |
| Pre-push hook | Warn (or block) if unresolved doc debt exists |
| Config mappings | User-defined code→doc relationships |
| Auto-resolve | Debt resolved when expected docs updated in later commit |

Detection rules (priority order):
1. User config mappings (seeded by `sqrl init`, editable in `.sqrl/config.yaml`)
2. Reference-based (code contains SCHEMA-001 → SCHEMAS.md)
3. Fallback (none by default)

**Consequences:**
- (+) Doc staleness is tracked and visible
- (+) Deterministic detection (no LLM)
- (+) User can configure mappings to reduce false positives
- (+) Auto-resolves when docs are updated
- (-) No doc tree or doc summaries (CLI AI reads docs directly)

---

## ADR-018: Silent Init

**Status:** accepted
**Date:** 2025-01-26
**Updated:** 2025-02-01

**Context:**
Previous design had `sqrl init` ask questions about which tools to use. This adds friction and confusion.

**Decision:**
Make `sqrl init` completely silent:
- Creates `.sqrl/` with default config (including seeded doc mappings)
- No prompts, no questions
- Auto-registers MCP server with enabled AI tools
- User can edit `.sqrl/config.yaml` directly for customization

**Consequences:**
- (+) Zero friction init
- (+) Works for any project (even blank)
- (+) Doc debt detection works out of the box
- (-) User must edit config.yaml manually for custom mappings

---

## ADR-019: Auto Git Hook Installation

**Status:** accepted
**Date:** 2025-01-26
**Updated:** 2025-02-01

**Context:**
Git hooks are needed for doc debt detection, but manual hook installation is friction.

**Decision:**
`sqrl init` auto-installs hooks when `.git/` exists:

```
sqrl init
    ↓ detects .git/
Install hooks to .git/hooks/
    ↓
post-commit: sqrl _internal docguard-record
pre-push: sqrl _internal docguard-check (optional block)
```

Hooks preserve existing user hooks (append, don't overwrite). `sqrl goaway` cleanly removes them.

**Consequences:**
- (+) Zero friction hook setup
- (+) No manual hook management
- (+) Preserves existing hooks
- (-) Hooks can still be bypassed (--no-verify)

---

## ADR-020: Poll-Based File Watching for WSL Compatibility

**Status:** accepted
**Date:** 2025-01-27

**Context:**
The file watcher using `notify` crate's `RecommendedWatcher` (inotify on Linux) fails silently on WSL2 when watching `~/.claude/projects/`. This directory resides on Windows filesystem mounted via 9p (`/mnt/c`), where inotify events are not propagated.

**Decision:**
Use `PollWatcher` instead of `RecommendedWatcher` with a 2-second polling interval. This works across all filesystem types including 9p/drvfs mounts.

```rust
let config = Config::default()
    .with_poll_interval(Duration::from_secs(2));
let watcher = PollWatcher::new(callback, config)?;
```

**Consequences:**
- (+) Works on WSL2 with Windows-mounted directories
- (+) Works consistently across all platforms
- (+) No silent failures on unsupported filesystems
- (-) 2-second latency before detecting changes (vs immediate with inotify)
- (-) Higher CPU usage due to polling
- (-) Scales worse with many watched files

---

## ADR-021: CLI-Driven Memory Architecture

**Status:** accepted
**Date:** 2025-02-01

**Context:**
The original architecture had a Rust daemon watching log files and a Python Memory Service running Gemini to extract memories. Problems:
- Daemon-extracted memories were often wrong (low accuracy)
- Python service added complexity (IPC, deployment, LLM costs)
- History processing was slow and error-prone
- The CLI AI already has full conversation context and better judgment

Reference systems (Letta/MemGPT, memory-graph) both use the CLI/agent itself to decide what to store, not an external daemon.

**Decision:**
Remove all AI from Squirrel. CLI AI decides what to remember and calls MCP tools directly.

| Removed | Replacement |
|---------|-------------|
| Python Memory Service | CLI AI stores via MCP |
| Daemon log watching | Not needed |
| History processing in init | Not needed |
| Gemini LLM calls | CLI AI handles decisions |
| IPC (Unix socket) | Not needed (single binary) |
| systemd/launchd service | Not needed (no daemon) |
| sqlite-vec embeddings | Not needed |
| Dashboard | Deferred to v2 |

New architecture:
- Single Rust binary (`sqrl`)
- 2 MCP tools: `store_memory`, `get_memory`
- Git hooks for doc debt
- Skill file for session start preferences
- CLAUDE.md triggers for memory storage

**Consequences:**
- (+) Much simpler (single binary, no Python, no daemon)
- (+) Higher accuracy (CLI AI has full context)
- (+) Zero LLM cost for Squirrel
- (+) No deployment complexity
- (+) Faster init (no history processing)
- (-) Depends on CLI AI following CLAUDE.md instructions
- (-) No memory extraction from non-MCP-aware tools
- (-) Dedup is basic (exact match only, no semantic)

**Supersedes:**
- ADR-001: Rust + Python Split (now single Rust binary)
- ADR-003: PydanticAI (no Python service)
- ADR-004: 2-Tier Model Pipeline (no LLM in Squirrel)
- ADR-009: Unix Socket IPC (no IPC needed)
- ADR-012: Simplified Memory Architecture (further simplified)
- ADR-016: System Service (no daemon)
- ADR-020: Poll-Based Watching (no file watching)

---

## Deprecated ADRs

| ADR | Status | Reason |
|-----|--------|--------|
| ADR-001 | superseded | Single binary, no Python split (ADR-021) |
| ADR-003 | superseded | No Python service (ADR-021) |
| ADR-004 | superseded | No LLM in Squirrel (ADR-021) |
| ADR-005 | superseded | Declarative keys removed in ADR-012 |
| ADR-008 | superseded | Frustration detection removed in ADR-012 |
| ADR-009 | superseded | No IPC needed (ADR-021) |
| ADR-010 | superseded | Replaced by simpler ADR-012 |
| ADR-011 | superseded | No longer needed without CR-Memory |
| ADR-012 | superseded | Further simplified by ADR-021 |
| ADR-016 | superseded | No daemon needed (ADR-021) |
| ADR-020 | superseded | No file watching (ADR-021) |

---

## Active ADRs

| ADR | Summary |
|-----|---------|
| ADR-002 | SQLite storage (still used, without sqlite-vec) |
| ADR-006 | Nix/devenv for development |
| ADR-007 | Spec-driven development |
| ADR-013 | B2B focus with B2D open source |
| ADR-014 | Minimal CLI commands |
| ADR-015 | Category-based organization (now tag-based, spirit preserved) |
| ADR-017 | Doc awareness (git hooks, doc debt) |
| ADR-018 | Silent init |
| ADR-019 | Auto git hook installation |
| ADR-021 | CLI-driven memory architecture |

---

## Pending Decisions

| Topic | Options | Blocking |
|-------|---------|----------|
| Team sync backend | Supabase / Custom / None | v2 |
| Dashboard hosting | Local / Cloud / Hybrid | v2 |
| Memory dedup strategy | Exact match / Semantic / AI | Cloud version |
