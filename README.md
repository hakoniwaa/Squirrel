# Squirrel

Local-first memory system for AI coding tools. Learns from your successes AND failures, providing personalized, task-aware context via MCP.

## What It Does

```
You code with Claude Code / Codex / Cursor / Gemini CLI
                    ↓
    Squirrel watches logs (100% passive, invisible)
                    ↓
    LLM segments session by type:
      EXECUTION_TASK → SUCCESS/FAILURE/UNCERTAIN
      PLANNING_DECISION → decisions, rationale
      RESEARCH_LEARNING → knowledge gained
      DISCUSSION → insights, preferences
                    ↓
    Extracts memories:
      lesson (what worked/failed)
      fact (project knowledge)
      profile (user preferences)
                    ↓
    AI tools call MCP → get personalized context
                    ↓
          Better code suggestions + avoid past mistakes
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        RUST DAEMON                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │Log Watch │  │ SQLite   │  │MCP Server│  │   CLI (thin)     ││
│  │(4 CLIs)  │  │sqlite-vec│  │          │  │ passes to agent  ││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────────────┘│
│       └─────────────┴─────────────┴─────────────────────────────│
│                            ↕ Unix socket IPC                    │
└─────────────────────────────────────────────────────────────────┘
                             ↕
┌─────────────────────────────────────────────────────────────────┐
│                      PYTHON AGENT                               │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Squirrel Agent (single LLM brain)            │ │
│  │                                                           │ │
│  │  Tools:                                                   │ │
│  │  ├── Memory: ingest, search, get_context, forget          │ │
│  │  ├── Filesystem: find_cli_configs, read/write_file        │ │
│  │  ├── Config: init_project, get/set_mcp_config             │ │
│  │  └── DB: query/add/update_memory, get_stats               │ │
│  │                                                           │ │
│  │  Entry points (all go through same agent):                │ │
│  │  ├── IPC: daemon sends Episode → agent ingests            │ │
│  │  ├── IPC: MCP tool call → agent retrieves                 │ │
│  │  └── IPC: CLI command → agent executes                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  Embeddings  │  │  Retrieval   │                            │
│  │  (API-based) │  │ (similarity) │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

| Component | Language | Role |
|-----------|----------|------|
| **Rust Daemon** | Rust | Log watcher, SQLite + sqlite-vec, MCP server, thin CLI |
| **Python Agent** | Python | Unified agent with tools, API embeddings, retrieval |

### Technology Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| **Storage** | SQLite + sqlite-vec | Local-first, vector search |
| **IPC** | JSON-RPC 2.0 over Unix socket | MCP-compatible protocol |
| **MCP SDK** | rmcp (official Rust SDK) | modelcontextprotocol/rust-sdk |
| **Agent Framework** | PydanticAI + LiteLLM | Multi-provider LLM support |
| **Embeddings** | OpenAI text-embedding-3-small | 1536-dim, API-based |
| **Build/Release** | dist (cargo-dist) | Generates Homebrew, MSI, installers |
| **Auto-update** | axoupdater | dist's official updater |

## Quick Start

```bash
# Install (detects OS automatically)
curl -sSL https://sqrl.dev/install.sh | sh

# First run: select which CLIs you use
sqrl config
# → Select: Claude Code, Codex CLI, Gemini CLI, Cursor

# Initialize a project
cd ~/my-project
sqrl init
# → Configures MCP for selected CLIs
# → Adds Squirrel instructions to CLAUDE.md, AGENTS.md, etc.
# → Ingests recent history

# Natural language - just talk to it
sqrl "what do you know about auth here"
sqrl "show my coding style"

# Or direct commands
sqrl search "database patterns"
sqrl status
```

## Installation

| Platform | Method |
|----------|--------|
| **Mac** | `brew install sqrl` (recommended) or install script |
| **Linux** | `brew install sqrl`, install script, AUR (Arch), nixpkg (NixOS) |
| **Windows** | MSI installer (recommended), `winget install sqrl`, or install script |

Universal install script (fallback):
```bash
# Mac/Linux
curl -sSL https://sqrl.dev/install.sh | sh

# Windows (PowerShell)
irm https://sqrl.dev/install.ps1 | iex
```

Auto-update:
```bash
sqrl update    # Updates both Rust daemon and Python agent
```

## How It Works

### Daemon Lifecycle

```
First sqrl command → daemon starts automatically
        ↓
Daemon watches logs, processes events
        ↓
2 hours no activity → daemon stops (saves resources)
        ↓
Next sqrl command → daemon starts again
```

No manual daemon management. No system services. Just works.

### CLI Selection (Global)

First run (or `sqrl config`) lets you select which CLIs you use:

```bash
sqrl config
# Interactive: select Claude Code, Codex CLI, Gemini CLI, Cursor
```

```toml
# ~/.sqrl/config.toml
[agents]
claude_code = true
codex_cli = true
gemini_cli = false
cursor = true
```

Only selected CLIs get configured during `sqrl init`.

### Project Initialization

```bash
cd ~/my-project
sqrl init
```

This:
1. Creates `.sqrl/squirrel.db` for project memories
2. Scans CLI log folders for logs mentioning this project
3. Ingests recent history (token-limited)
4. For each enabled CLI:
   - Configures MCP (adds Squirrel server to CLI's MCP config)
   - Adds instruction text to agent file (CLAUDE.md, AGENTS.md, GEMINI.md, .cursor/rules/)

Skip history ingestion:
```bash
sqrl init --skip-history
```

### Syncing New CLIs

If you enable a new CLI after initializing projects:

```bash
# Enable Cursor globally
sqrl config  # select Cursor

# Update all existing projects
sqrl sync
# → Adds MCP config + instructions for Cursor to all registered projects
```

### Passive Learning (Write Path)

```
User codes with Claude Code normally
        ↓
Claude Code writes to ~/.claude/projects/**/*.jsonl
        ↓
Rust Daemon tails JSONL files → normalized Events
        ↓
Buffers events, flushes as Episode (4hr window OR 50 events)
        ↓
Python Agent analyzes Episode (segment-first approach):
  1. Segments by kind:
     - EXECUTION_TASK (coding, fixing)
     - PLANNING_DECISION (architecture, design)
     - RESEARCH_LEARNING (learning, exploring)
     - DISCUSSION (brainstorming, chat)
  2. For EXECUTION_TASK only: SUCCESS | FAILURE | UNCERTAIN
  3. Extracts memories based on segment kind
  4. Checks for fact contradictions → invalidates old facts
        ↓
Near-duplicate check (0.9 threshold) → store or merge
```

### Context Retrieval (Read Path)

```
Claude Code calls MCP: squirrel_get_task_context
        ↓
Vector search retrieves candidate memories (top 20)
        ↓
LLM reranks candidates + composes context prompt:
  - Selects relevant memories
  - Resolves conflicts between memories
  - Merges related memories
  - Generates structured prompt with memory IDs
        ↓
Returns ready-to-inject context prompt
        ↓
Claude Code uses context for better response
```

For trivial queries ("fix typo"), agent returns empty fast (<20ms).

## Natural Language CLI

The CLI understands natural language. Same agent that handles memory handles your commands:

```bash
sqrl "init this project but skip old logs"
sqrl "what went wrong with the postgres migration"
sqrl "forget the memory about deprecated API"
sqrl "configure gemini cli to use squirrel"
sqrl "show my profile"
sqrl "I prefer functional programming style"
```

Direct commands still work:
```bash
sqrl init --skip-history
sqrl search "postgres"
sqrl forget <memory-id>
sqrl config set llm.model claude-sonnet
sqrl sync                               # Update all projects with new CLI configs
```

### Export/Import

```bash
# Export/Import memories (for backup or sharing)
sqrl export lesson                  # Export all lessons as JSON
sqrl export fact --project          # Export project facts
sqrl import memories.json           # Import memories
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `squirrel_get_task_context` | Task-aware memory with "why" explanations |
| `squirrel_search_memory` | Semantic search across all memory |

## Memory Types

3 memory types, each with scope (global/project):

| Type | Fields | Description | Example |
|------|--------|-------------|---------|
| `lesson` | outcome (success/failure), scope | What worked or failed | "async/await preferred", "API 500 on null user_id" |
| `fact` | fact_type (knowledge/process), scope | Project knowledge or what happened | "Uses PostgreSQL 15", "Tried X, then Y worked" |
| `profile` | scope | User info | "Backend dev, 5yr Python" |

### Scope

| Scope | DB Location | Description |
|-------|-------------|-------------|
| Global | `~/.sqrl/squirrel.db` | User preferences, profile (applies to all projects) |
| Project | `<repo>/.sqrl/squirrel.db` | Project-specific lessons and facts |

### Examples by Type

**lesson (outcome=success):** coding preferences, patterns that worked
- "Prefers async/await over callbacks"
- "Use repository pattern for DB access"

**lesson (outcome=failure):** issues encountered, things to avoid
- "API returns 500 on null user_id"
- "Never use ORM for bulk inserts"

**fact (fact_type=knowledge):** project facts, tech stack info
- "Uses PostgreSQL 15"
- "Auth via JWT tokens"

**fact (fact_type=process):** what happened, decision history
- "Tried Redis, failed due to memory, switched to PostgreSQL"
- "Sprint 12: migrated to Redis"

**profile:** user info
- "Backend dev, 5yr Python experience"
- "Prefers detailed code comments"

### Memory Lifecycle

Memories have status and validity tracking:

| Status | Description | Retrieval |
|--------|-------------|-----------|
| `active` | Normal memory | Included |
| `inactive` | Soft deleted via `sqrl forget` | Hidden (recoverable) |
| `invalidated` | Superseded by newer fact | Hidden (keeps history) |

**Fact contradiction handling:**
- When new fact contradicts old (e.g., "uses PostgreSQL" vs "uses MySQL")
- Old fact marked `invalidated`, `valid_to` set, `superseded_by` points to new
- History preserved for debugging

**Forget command:**
```bash
sqrl forget <memory-id>              # Soft delete by ID
sqrl forget "deprecated API"         # Search + confirm + soft delete
```

## Storage Layout

```
~/.sqrl/
├── config.toml                 # User settings, API keys
├── squirrel.db                 # Global memories (lesson, fact, profile with scope=global)
└── logs/                       # Daemon logs

<repo>/.sqrl/
├── squirrel.db                 # Project memories (lesson, fact with scope=project)
└── config.toml                 # Project overrides (optional)
```

### 2-Layer Database Architecture

| Layer | DB File | Contents |
|-------|---------|----------|
| **Global** | `~/.sqrl/squirrel.db` | lesson, fact, profile (scope=global) |
| **Project** | `<repo>/.sqrl/squirrel.db` | lesson, fact (scope=project) |

## Configuration

```toml
# ~/.sqrl/config.toml

[agents]
claude_code = true                # Enable Claude Code integration
codex_cli = true                  # Enable Codex CLI integration
gemini_cli = false                # Enable Gemini CLI integration
cursor = true                     # Enable Cursor integration

[llm]
provider = "gemini"               # gemini | openai | anthropic | ollama | ...
api_key = "..."
base_url = ""                     # Optional, for local models (Ollama, LMStudio)

# 2-tier model design
strong_model = "gemini-2.5-pro"   # Complex reasoning (episode ingestion)
fast_model = "gemini-3-flash"     # Fast tasks (context compose, CLI, dedup)

[embedding]
provider = "openai"               # openai | gemini | cohere | ...
model = "text-embedding-3-small"  # 1536-dim, $0.10/M tokens

[daemon]
idle_timeout_hours = 2            # Stop after N hours inactive
```

### LLM Usage

| Task | Model | Why |
|------|-------|-----|
| Episode Ingestion | strong_model | Multi-step reasoning over ~10K tokens |
| Context Compose | fast_model | Rerank + generate structured prompt |
| CLI Interpretation | fast_model | Parse natural language commands |
| Near-duplicate Check | fast_model | Simple comparison |

## Project Structure

```
Squirrel/
├── agent/                      # Rust daemon + CLI + MCP
│   └── src/
│       ├── daemon.rs           # Lazy start, idle shutdown
│       ├── watcher.rs          # Multi-CLI log watching
│       ├── storage.rs          # SQLite + sqlite-vec
│       ├── ipc.rs              # Unix socket client
│       ├── mcp.rs              # MCP server
│       └── cli.rs              # Thin CLI, passes to agent
│
├── memory_service/             # Python Agent
│   └── squirrel_memory/
│       ├── server.py           # Unix socket IPC server
│       ├── agent.py            # Unified agent with tools
│       ├── tools/              # Tool implementations
│       ├── embeddings.py       # API embeddings (OpenAI, etc.)
│       └── retrieval.py        # Similarity search
│
└── docs/
    ├── DEVELOPMENT_PLAN.md
    └── EXAMPLE.md
```

## Development Setup

### Prerequisites

```bash
# Rust 1.83+
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Python via uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Build

```bash
git clone https://github.com/kaminoguo/Squirrel.git
cd Squirrel

# Rust
cd agent && cargo build && cargo test

# Python
cd ../memory_service
uv venv && uv pip install -e ".[dev]"
source .venv/bin/activate && pytest
```

## v1 Scope

- Passive log watching (4 CLIs)
- Episode segmentation (EXECUTION_TASK / PLANNING_DECISION / RESEARCH_LEARNING / DISCUSSION)
- Success detection for EXECUTION_TASK only (with evidence requirement)
- Memory lifecycle: status (active/inactive/invalidated) + validity tracking
- Fact contradiction detection + auto-invalidation
- Soft delete (`sqrl forget`) - recoverable
- Unified Python agent with tools
- Natural language CLI
- MCP integration (2 tools)
- Lazy daemon (start on demand, stop after 2hr idle)
- Retroactive log ingestion on init (token-limited)
- 3 memory types (lesson, fact, profile) with scope flag
- Near-duplicate deduplication (0.9 threshold)
- Cross-platform (Mac, Linux, Windows)
- Export/import memories (JSON)
- Auto-update (`sqrl update`)
- CLI selection + MCP wiring + agent instruction injection
- `sqrl sync` for updating existing projects with new CLIs

**v1 limitations:**
- No TTL/auto-expiration
- No hard delete (soft delete only)

**v2:** Team/cloud sync, deep CLI integrations, TTL/temporary memory, hard purge, memory linking

## Contributing

1. Fork and clone
2. Create branch: `git checkout -b yourname/feat-description`
3. Make changes, run tests
4. Commit: `feat(scope): description`
5. Push and create PR

### Code Style

```bash
# Rust
cargo fmt && cargo clippy

# Python
ruff check --fix . && ruff format .
```

## License

AGPL-3.0
