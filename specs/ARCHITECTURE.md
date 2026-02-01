# Squirrel Architecture

High-level system boundaries and data flow.

## Design Principles

| Principle | Description |
|-----------|-------------|
| **CLI-Driven** | CLI AI decides what to remember, Squirrel just stores |
| **Local-First** | All data stored locally, no cloud required |
| **No AI in Squirrel** | Squirrel has zero LLM calls; all intelligence from CLI |
| **Minimal** | 2 MCP tools, git hooks, SQLite. Nothing more. |
| **Doc Aware** | Git hooks track doc debt, CLI fixes docs |

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User's Machine                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Claude Code  │    │    Cursor    │    │  Codex CLI   │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                │
│         │  CLAUDE.md tells CLI when to store     │                │
│         │  Skill shows preferences at start      │                │
│         │                   │                   │                │
│         └─────────┬─────────┴─────────┬─────────┘                │
│                   │ MCP               │ MCP                      │
│                   ▼                   ▼                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    SQUIRREL (sqrl binary)                  │  │
│  │                                                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
│  │  │ MCP Server  │  │ CLI Handler │  │ Git Hooks   │        │  │
│  │  │ (rmcp)      │  │ (clap)      │  │ (docguard)  │        │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │  │
│  │         │                │                │               │  │
│  │         └────────────────┼────────────────┘               │  │
│  │                          ▼                                │  │
│  │                 ┌─────────────────┐                       │  │
│  │                 │     SQLite      │                       │  │
│  │                 │ (.sqrl/memory.db)│                       │  │
│  │                 └─────────────────┘                       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Boundaries

### ARCH-001: Squirrel Binary

Single Rust binary. No persistent daemon. Started on-demand by CLI tools (MCP) or git hooks.

| Module | Purpose |
|--------|---------|
| MCP Server | Serves `store_memory` + `get_memory` to CLI tools (rmcp) |
| CLI Handler | `sqrl init`, `sqrl goaway`, `sqrl status` (clap) |
| Git Hooks | Doc debt detection (post-commit, pre-push) |
| SQLite Storage | Memories + doc debt storage |

**Owns:**
- SQLite read/write
- use_count tracking
- MCP protocol handling
- Doc debt tracking
- Git hook installation

**Never Contains:**
- LLM API calls
- Log file watching
- History processing
- IPC to other services

---

### ARCH-002: CLI Integration

CLI tools (Claude Code, Cursor, etc.) are the intelligence layer.

| Integration | Mechanism | Purpose |
|-------------|-----------|---------|
| **CLAUDE.md** | Instructions in project/user config | Tells CLI when to store memories |
| **Skill** | `.claude/skills/squirrel-session/SKILL.md` | Shows user preferences at session start |
| **MCP** | `squirrel_store_memory`, `squirrel_get_memory` | Store and retrieve memories |

**CLI is responsible for:**
- Deciding what to remember
- Deciding when to store
- Updating docs when debt is reported
- Reviewing/applying user preferences

**Squirrel is NOT responsible for:**
- Memory extraction from conversations
- Deciding what's important
- Fixing documentation
- Any LLM operations

---

### ARCH-003: Storage Layer

| File | Location | Contains |
|------|----------|----------|
| Project Memory DB | `<repo>/.sqrl/memory.db` | All memories + doc debt |
| Project Config | `<repo>/.sqrl/config.yaml` | Doc patterns, hook settings |
| Skill File | `<repo>/.claude/skills/squirrel-session/SKILL.md` | Session start instructions |

---

## Memory Model

### How Memories Are Created

```
CLI AI decides "this is worth remembering"
    → CLI calls MCP: squirrel_store_memory
    → Squirrel stores to SQLite
    → Done
```

No extraction pipeline. No scanning. No filtering. CLI AI has full conversation context and makes the decision.

### How Memories Are Retrieved

```
CLI needs project context (user asks, or session start skill)
    → CLI calls MCP: squirrel_get_memory
    → Squirrel returns memories ordered by use_count
    → CLI uses them in context
```

### Memory Types

| Type | Description | Examples |
|------|-------------|---------|
| `preference` | User's coding style preferences | "No emojis", "Use Gemini 3 Pro" |
| `project` | Project-specific knowledge | "Use httpx not requests" |
| `decision` | Architecture decisions | "Chose PostgreSQL for transactions" |
| `solution` | Problem-solution pairs | "Fixed SSL by switching to httpx" |

---

## Data Flow

### FLOW-001: Memory Storage (CLI → Squirrel)

```
1. User says something memorable (e.g., "never use emoji")
2. CLI reads CLAUDE.md trigger rules
3. CLI calls MCP: squirrel_store_memory({type, content, tags})
4. Squirrel checks for duplicates:
   - Exact match: increment use_count
   - No match: insert new memory
5. Squirrel returns success
```

---

### FLOW-002: Memory Retrieval (Squirrel → CLI)

```
1. CLI calls MCP: squirrel_get_memory({type?, tags?})
2. Squirrel queries SQLite
3. Returns memories ordered by use_count DESC
4. CLI uses in context
```

---

### FLOW-003: Session Start (Skill)

```
1. New CLI session begins
2. Skill auto-triggers (user-invocable: false)
3. Skill instructs CLI to call squirrel_get_memory(type: "preference")
4. CLI displays preferences in context
5. User's preferences guide the session
```

---

### FLOW-004: Doc Debt Detection

```
1. User commits code
2. Git post-commit hook calls: sqrl _internal docguard-record
3. Auto-resolve: if docs were updated in this commit, resolve matching old debt
4. Squirrel analyzes commit diff:
   a. Config mappings (.sqrl/config.yaml doc_rules.mappings)
   b. Reference patterns (code contains SCHEMA-001 → SCHEMAS.md)
5. If code changed but related docs didn't:
   - Record doc debt entry in SQLite
6. CLI sees debt via CLAUDE.md instructions or sqrl status
```

---

### FLOW-005: Git Hook Installation

```
1. sqrl init detects .git/ exists
2. Installs hooks to .git/hooks/:
   - post-commit: sqrl _internal docguard-record
   - pre-push: sqrl _internal docguard-check
3. Hooks are self-contained (no daemon required)
```

---

## CLI Commands

| Command | Action |
|---------|--------|
| `sqrl` | Show help |
| `sqrl init` | Initialize project (.sqrl/, hooks, skill, MCP registration) |
| `sqrl goaway` | Remove all Squirrel data (including MCP unregistration) |
| `sqrl status` | Show project status including doc debt |
| `sqrl mcp-serve` | Start MCP server (called by CLI tool config) |

**Hidden internal commands** (called by hooks):
- `sqrl _internal docguard-record` - Record doc debt after commit
- `sqrl _internal docguard-check` - Check doc debt before push

---

## Files Created by `sqrl init`

```
<repo>/
├── .sqrl/
│   ├── config.yaml          # Tools, doc mappings, hook settings
│   └── memory.db            # SQLite (memories + doc debt)
├── .claude/
│   ├── CLAUDE.md            # Memory Protocol triggers (appended)
│   └── skills/
│       └── squirrel-session/
│           └── SKILL.md     # Session start skill
└── .git/hooks/
    ├── post-commit          # Doc debt recording
    └── pre-push             # Doc debt check (optional block)
```

Also registers MCP server with enabled AI tools (e.g., `claude mcp add squirrel`).

---

## Technology Stack

| Category | Technology | Notes |
|----------|------------|-------|
| Language | Rust | Single binary, no runtime deps |
| Storage | SQLite | Local-first, single file |
| MCP SDK | rmcp | Official Rust SDK |
| CLI | clap | Minimal commands |
| Build | cargo-dist | Single binary distribution |

---

## What Was Removed (ADR-021)

| Removed | Why |
|---------|-----|
| Python Memory Service | CLI handles memory decisions |
| Daemon log watching | No longer needed |
| History processing | Not needed |
| IPC (Unix socket) | No Python service to talk to |
| LLM calls (Gemini) | CLI AI handles all intelligence |
| systemd/launchd service | No persistent daemon needed |
| Dashboard | Future feature, not v1 |
| sqlite-vec | No embedding search needed |

---

## Platform Support

| Platform | MCP Config | Hooks |
|----------|------------|-------|
| macOS | `claude mcp add squirrel -- sqrl mcp-serve` | `.git/hooks/` |
| Linux/WSL | `claude mcp add squirrel -- sqrl mcp-serve` | `.git/hooks/` |
| Windows | `claude mcp add squirrel -- sqrl.exe mcp-serve` | `.git/hooks/` |

---

## Security

| Boundary | Enforcement |
|----------|-------------|
| No network in Squirrel | Rust binary has no HTTP client |
| No LLM keys | Squirrel makes zero API calls |
| Project isolation | Separate DB per project |
| No secrets in memories | CLI responsibility (via CLAUDE.md) |

---

## Future (Not v1)

| Feature | When |
|---------|------|
| Dashboard (web UI) | v2 |
| Memory deduplication AI | Cloud version |
| Team sync | Cloud version |
| Embedding search | v2 if needed |
