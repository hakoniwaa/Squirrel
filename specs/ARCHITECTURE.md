# Squirrel Architecture

High-level system boundaries and data flow.

## Design Principles

| Principle | Description |
|-----------|-------------|
| **Passive** | Daemon watches logs, never intercepts tool calls |
| **Distributed-first** | All extraction happens locally, no central server required |
| **LLM Autonomy** | LLM decides what to extract, not hardcoded rules |
| **Simple** | No complex evaluation loops, just use_count based ordering |

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
│         └─────────┬─────────┴─────────┬─────────┘                │
│                   │                   │                          │
│                   ▼                   ▼                          │
│         ┌─────────────────┐  ┌─────────────────┐                 │
│         │   Log Files     │  │   MCP Client    │                 │
│         │ (watched)       │  │   (manual)      │                 │
│         └────────┬────────┘  └────────┬────────┘                 │
│                  │                    │                          │
│                  ▼                    ▼                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    RUST DAEMON                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
│  │  │ Log Watcher │  │ MCP Server  │  │ CLI Handler │        │  │
│  │  │   (notify)  │  │   (rmcp)    │  │  (clap)     │        │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │  │
│  │         │                │                │               │  │
│  │         └────────────────┼────────────────┘               │  │
│  │                          ▼                                │  │
│  │                 ┌─────────────────┐                       │  │
│  │                 │     SQLite      │                       │  │
│  │                 │  + sqlite-vec   │                       │  │
│  │                 └─────────────────┘                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              │ Unix Socket (JSON-RPC 2.0)        │
│                              ▼                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               PYTHON MEMORY SERVICE                        │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                  Log Cleaner                         │  │  │
│  │  │  - Cheap model (Haiku/GPT-4o-mini)                  │  │  │
│  │  │  - Removes noise, compresses tokens                  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                  Memory Extractor                    │  │  │
│  │  │  - Strong model (Sonnet/GPT-4o)                     │  │  │
│  │  │  - Extracts user style + project memory             │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                  Style Syncer                        │  │  │
│  │  │  - Writes user style to agent.md files              │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │ HTTPS
                               ▼
                    ┌─────────────────────┐
                    │    LLM Providers    │
                    │ (Anthropic/OpenAI)  │
                    └─────────────────────┘
```

## Component Boundaries

### ARCH-001: Rust Daemon

**Responsibility:** Local I/O, storage, MCP server, CLI.

| Module | Purpose |
|--------|---------|
| Log Watcher | File system events for CLI logs (notify) |
| MCP Server | Serves project memory to AI tools (rmcp) |
| CLI Handler | `sqrl`, `sqrl init`, `sqrl status` (clap) |
| SQLite Storage | User style + project memory storage |

**Owns:**
- SQLite read/write
- sqlite-vec vector queries
- use_count tracking
- MCP protocol handling

**Never Contains:**
- LLM API calls
- Embedding generation
- Tool interception

---

### ARCH-002: Python Memory Service

**Responsibility:** All LLM operations.

| Module | Purpose | Model |
|--------|---------|-------|
| Log Cleaner | Remove noise, compress tokens | cheap (Haiku) |
| Memory Extractor | Extract user style + project memory | strong (Sonnet) |
| Style Syncer | Write user style to agent.md | N/A |
| Embeddings | Generate vectors for semantic search | embedding model |

**Owns:**
- All LLM API calls
- Log cleaning/compression
- Memory extraction logic
- agent.md file writes

**Never Contains:**
- File watching
- Direct database access (via IPC only)
- MCP protocol

---

### ARCH-003: Storage Layer

| Database | Location | Contains |
|----------|----------|----------|
| User Style DB | `~/.sqrl/user_style.db` | Personal development style |
| Project Memory DB | `<repo>/.sqrl/memory.db` | Project-specific memories |

---

## Memory Types

### User Style (Personal)

Extracted from coding sessions, synced to agent.md files.

| Example |
|---------|
| "Commits should use minimal English" |
| "AI should maintain critical, calm attitude" |
| "Never use emoji in code or comments" |
| "Prefer async/await over callbacks" |

**Storage:** Database + synced to `~/.sqrl/personal-style.md` and agent config files.

**Team (B2B):** Team admin can promote personal styles to team-level via Dashboard.

---

### Project Memory

Project-specific knowledge, organized by category.

| Category | Description |
|----------|-------------|
| `frontend` | Frontend architecture, components, styling |
| `backend` | Backend architecture, APIs, database |
| `docs_test` | Documentation, testing conventions |
| `other` | Everything else |

**Subcategories:** Default is `main`. Users can add custom subcategories via Dashboard.

**Storage:** `<repo>/.sqrl/memory.db`

**Access:** Via MCP tool, returns all categories grouped.

---

## Data Flow

### FLOW-001: Memory Extraction (Input)

```
1. User codes with AI CLI
2. CLI writes to log file
3. Daemon detects file change (notify)
4. Daemon buffers events until episode boundary:
   - Time gap (>30 min idle)
   - Explicit flush (sqrl flush)
5. Daemon sends raw events to Memory Service
6. Log Cleaner (cheap model):
   - Removes noise, redundant code blocks
   - Compresses to reduce tokens
   - Decides if worth extracting (skip if trivial)
7. Memory Extractor (strong model):
   - Extracts user style items
   - Extracts project memories with categories
   - Compares with existing memories:
     - Duplicate: increment use_count
     - Similar: merge/update
     - New: add
8. Style Syncer:
   - Updates user style in database
   - Syncs to agent.md files
9. Daemon stores project memories in SQLite
```

---

### FLOW-002: Memory Retrieval (Output)

```
1. User says "use Squirrel" or triggers MCP
2. AI CLI calls MCP tool: squirrel_get_memory
3. Daemon queries project memory database
4. Returns all memories grouped by category:

   ## frontend
   - memory 1
   - memory 2

   ## backend
   - memory 3

   ## docs_test
   (none)

   ## other
   - memory 4

5. Memories ordered by use_count (most used first)
```

---

### FLOW-003: Garbage Collection

```
Periodic cleanup (configurable interval):

1. Find memories with use_count = 0 AND age > threshold
2. Mark as candidates for deletion
3. On next extraction, if similar memory extracted:
   - Cancel deletion, merge instead
4. Otherwise, delete after grace period
```

---

## CLI Commands

| Command | Action |
|---------|--------|
| `sqrl` | Open Dashboard in browser |
| `sqrl init` | Initialize project |
| `sqrl init --history <days\|all>` | Initialize + process historical logs |
| `sqrl status` | Show daemon status and stats |

All other operations via Dashboard.

---

## Dashboard (Web UI)

| Feature | Free | Team (B2B) |
|---------|------|------------|
| View/edit personal style | ✅ | ✅ |
| View/edit project memory | ✅ | ✅ |
| Memory categories management | ✅ | ✅ |
| Team style management | ❌ | ✅ |
| Team member management | ❌ | ✅ |
| Cloud sync | ❌ | ✅ |
| Activity analytics | ❌ | ✅ |

---

## Team Features (B2B)

### Data Hierarchy

```
Personal Style (local, not synced)
      ↓ override
Team Style (cloud synced, read-only for members)
      ↓ merged with
Project Memory (cloud synced, team shared)
```

### Sync Flow

```
Local daemon extract → Push to cloud → Cloud deduplicates/merges → Sync to team
```

### Roles

| Role | Permissions |
|------|-------------|
| Owner | All + billing |
| Admin | Edit team style, manage members |
| Member | Contribute project memory, view all |

---

## Technology Stack

| Category | Technology | Notes |
|----------|------------|-------|
| **Rust Daemon** | | |
| Storage | SQLite + sqlite-vec | Local-first, vector search |
| IPC | JSON-RPC 2.0 | Over Unix socket |
| MCP SDK | rmcp | Official Rust SDK |
| CLI | clap | Minimal commands |
| File Watching | notify | Cross-platform |
| **Python Service** | | |
| LLM Client | LiteLLM | Multi-provider |
| Agent Framework | PydanticAI | Structured outputs |
| **Build** | | |
| Rust | cargo-dist | Single binary |
| Python | PyInstaller | Bundled |

---

## Platform Support

| Platform | Log Locations | Socket |
|----------|---------------|--------|
| macOS | `~/Library/Application Support/*/` | `/tmp/sqrl.sock` |
| Linux | `~/.config/*/` | `/tmp/sqrl.sock` |
| Windows | `%APPDATA%\*\` | `\\.\pipe\sqrl` |

---

## Security

| Boundary | Enforcement |
|----------|-------------|
| Daemon has no network | Rust compile-time |
| LLM keys in Python only | Environment variables |
| Project isolation | Separate DB per project |
| No secrets in memories | Extractor constraint |
