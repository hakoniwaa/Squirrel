# Squirrel Architecture

High-level system boundaries and data flow.

## Design Principles

| Principle | Description |
|-----------|-------------|
| **CLI-Driven** | CLI AI decides what to remember, Squirrel just stores |
| **Local-First** | All data stored locally, no cloud required |
| **No AI in Squirrel** | Squirrel has zero LLM calls; all intelligence from CLI |
| **Minimal** | 2 MCP tools, git hooks, SQLite, simple web UI |
| **Doc Aware** | Pre-push hook shows changes for AI to review docs |
| **Global + Project** | Global config at `~/.sqrl/`, project config at `.sqrl/` |

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
| Git Hooks | Pre-push diff display for doc review |
| SQLite Storage | Memory storage |

**Owns:**
- SQLite read/write
- use_count tracking
- MCP protocol handling
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
- Updating docs when pre-push hook shows changes
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
| Global Config | `~/.sqrl/config.yaml` | Enabled tools, enabled MCPs |
| Global Preferences | `~/.sqrl/memory.db` | User preferences (apply everywhere) |
| MCP Config File | `~/.sqrl/mcp-config.json` | Uploaded MCP definitions |
| Project Memory DB | `<repo>/.sqrl/memory.db` | Project-specific memories |
| Project Config | `<repo>/.sqrl/config.yaml` | Project settings |
| Skill File | `<repo>/.claude/skills/squirrel-session/SKILL.md` | Session start instructions |

---

### ARCH-004: Web UI

Minimal black/white web UI for configuration. Runs locally on `localhost:3333`.

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Dashboard - view memories, config |
| `GET /api/config` | Get global config |
| `POST /api/config` | Update global config |
| `GET /api/mcps` | List MCP configs |
| `POST /api/mcps` | Upload MCP config |
| `DELETE /api/mcps/:name` | Remove MCP config |
| `GET /api/memories` | List project memories (requires project path) |
| `POST /api/memories` | Add memory |
| `PUT /api/memories/:id` | Update memory |
| `DELETE /api/memories/:id` | Delete memory |

**Technology:**
- Embedded static assets (rust-embed)
- axum for HTTP server
- HTMX for interactivity (no JS framework)

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

| Type | Storage | Description | Examples |
|------|---------|-------------|---------|
| `preference` | `~/.sqrl/memory.db` | Global user preferences | "No emojis", "Prefer async/await" |
| `project` | `.sqrl/memory.db` | Project-specific rules | "Use httpx not requests" |

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

### FLOW-004: Doc Review (Pre-Push)

```
1. User/AI pushes code
2. Git pre-push hook calls: sqrl _internal docguard-check
3. Squirrel prints:
   - Commits to push (count)
   - Files changed (diff stats)
   - Doc files in repo
4. AI reads output, decides if docs need updating
5. If yes: AI updates docs, commits, push continues
6. If no: push continues
```

Always informational, never blocks. AI makes the decision.

---

### FLOW-005: Git Hook Installation

```
1. sqrl init detects .git/ exists
2. Installs pre-push hook to .git/hooks/pre-push
3. Hook is self-contained (no daemon required)
```

---

## CLI Commands

| Command | Action |
|---------|--------|
| `sqrl` | Show help |
| `sqrl config` | Open web UI for global configuration |
| `sqrl init` | Initialize project + apply global MCP configs |
| `sqrl apply` | Apply global MCP configs to current project |
| `sqrl goaway` | Remove all Squirrel data (including MCP unregistration) |
| `sqrl status` | Show project status |
| `sqrl mcp-serve` | Start MCP server (called by CLI tool config) |

**Hidden internal commands** (called by hooks):
- `sqrl _internal docguard-check` - Show diff summary before push

---

## Files Created

### Global (`sqrl config` first run)

```
~/.sqrl/
├── config.yaml              # Enabled tools, settings
└── mcps/                    # MCP configs to apply
    └── squirrel.json        # Default Squirrel MCP
```

### Project (`sqrl init`)

```
<repo>/
├── .sqrl/
│   ├── config.yaml          # Project-specific overrides
│   └── memory.db            # SQLite (memories)
├── .claude/
│   ├── CLAUDE.md            # Memory Protocol triggers (appended)
│   └── skills/
│       └── squirrel-session/
│           └── SKILL.md     # Session start skill
└── .git/hooks/
    └── pre-push             # Diff summary for doc review
```

`sqrl init` also runs `sqrl apply` to register all MCPs from global config.

---

## Technology Stack

| Category | Technology | Notes |
|----------|------------|-------|
| Language | Rust | Single binary, no runtime deps |
| Storage | SQLite | Local-first, single file |
| MCP SDK | rmcp | Official Rust SDK |
| CLI | clap | Minimal commands |
| Web Server | axum | Lightweight, async |
| Web UI | HTMX + Tailwind | Minimal JS, black/white theme |
| Static Assets | rust-embed | Embedded in binary |
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
| Memory deduplication AI | Cloud version |
| Team sync | Cloud version |
| Embedding search | v2 if needed |
| More CLI tools (Cursor, Codex) | v1.1 |
