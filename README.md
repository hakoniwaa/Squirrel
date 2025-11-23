# Squirrel

Local-first memory system for AI coding tools. Automatically learns your coding patterns and provides personalized context to AI assistants via MCP.

## What Is This

Squirrel watches your development activity (Claude Code, Codex CLI, Gemini CLI, Cursor, Git), extracts coding patterns and project knowledge, and feeds that context back to AI tools so they generate code matching your style.

The more you code with AI tools, the better Squirrel understands your preferences.

## Architecture

Two modules:

**1. Rust Agent** (`agent/`)
- Local daemon process
- Watches AI tool logs and Git activity
- Normalizes events into SQLite
- Serves MCP server for AI tools
- Provides CLI commands

**2. Python Memory Service** (`memory_service/`)
- HTTP service (runs locally)
- Processes events with LLMs
- Extracts coding patterns
- Generates compact memory views
- Managed by Rust daemon

## How Modules Work

### Rust Agent Module

**What it does:**
- Runs one global daemon per machine
- Monitors `~/.claude/projects/**/*.jsonl` for new conversations
- Normalizes logs into `Event` structs
- Stores events in `<repo>/.ctx/data.db` (SQLite)
- Batches events and sends to Python service via HTTP
- Caches views from Python in `<repo>/.ctx/views/`
- Exposes MCP server that AI tools call

**Key components:**
- `daemon.rs` - Long-running process, manages watchers and Python service
- `watcher.rs` - File system monitoring (notify crate)
- `events.rs` - Event models, SQLite storage, deduplication
- `mcp.rs` - MCP stdio server (spawned per AI tool request)
- `python_client.rs` - HTTP client to memory service
- `cli.rs` - User commands: `sqrl init`, `sqrl status`, `sqrl config`

**Process model:**
```
sqrl daemon (global, one per machine)
    ├─> watches all registered repos
    ├─> spawns Python subprocess
    └─> listens on localhost TCP

sqrl mcp (short-lived, spawned by AI tools)
    └─> connects to daemon via TCP
    └─> forwards MCP requests
```

**Storage:**
```
~/.sqrl/
  ├── config.toml          # API keys, user settings
  ├── user.db              # User-level coding style (global)
  ├── projects.json        # List of registered repos
  ├── daemon.json          # {pid, host, port}
  └── memory-service.json  # Python service connection info

<repo>/.ctx/
  ├── data.db              # Events, episodes, memory_items
  └── views/
      ├── user_style.json
      ├── project_brief.json
      └── .meta.json       # Staleness tracking
```

**Event batching:**
- Triggers: 20 events accumulated OR 30 seconds elapsed
- Failed sends: queued in SQLite, retry with backoff
- Deduplication: content-based hash prevents duplicate events

### Python Memory Service Module

**What it does:**
- Runs as HTTP service on random localhost port
- Receives batches of events from Rust
- Groups events into episodes (coding sessions)
- Uses LLMs to extract structured memory
- Applies Mem0-style update logic (ADD/UPDATE/NOOP)
- Generates compact views for AI tools

**Key components:**
- `server.py` - FastAPI app with 3 endpoints
- `models.py` - Pydantic schemas (Event, Episode, MemoryItem, View)
- `extractor.py` - Groups events → episodes, extracts memory items
- `updater.py` - Deduplicates memory, handles conflicts
- `views.py` - Builds user_style_view and project_brief_view

**HTTP API:**
```python
POST /process_events
{
  "project_id": "repo://github.com/user/project",
  "events": [
    {"id": "evt_1", "timestamp": "...", "source_tool": "claude_code", ...}
  ]
}
→ {"episodes": [...], "memory_items": [...]}

GET /views/user_style?project_id=repo://...
→ {"view": "User prefers TypeScript...", "metadata": {...}}

GET /views/project_brief?project_id=repo://...
→ {"view": "FastAPI backend with PostgreSQL...", "metadata": {...}}
```

**Episode grouping:**
- Time-based: gaps > 20 minutes = new episode
- Session-based: different Claude Code session_id = new episode
- Context-based: different directory/module = new episode

**Memory extraction:**
- Sends episode context to LLM (GPT-4 / Claude)
- Extracts structured patterns:
  - user_style: "Prefers async/await over callbacks"
  - project_fact: "Uses PostgreSQL for main DB"
- Tags each memory item (e.g., ["naming", "typescript", "testing"])
- Assigns importance score (0.0-1.0)

**Update logic:**
- For new memory item, finds similar existing items (key-based or semantic)
- LLM decides:
  - ADD: new unique information
  - UPDATE: refine existing item
  - NOOP: already known
  - DELETE: contradictory, remove old
- Keeps memory deduplicated and consistent

**View generation:**
- On-demand when Rust requests
- Builds compact summary (few hundred tokens)
- Designed to fit in AI tool context window
- Cached by Rust until stale

## Data Flow

```
1. User codes with Claude Code
   ↓
2. Claude writes ~/.claude/projects/xxx/session.jsonl
   ↓
3. Rust watcher detects new lines
   ↓
4. Parse JSONL → Event struct
   ↓
5. Store in <repo>/.ctx/data.db
   ↓
6. Batch events (20 or 30s)
   ↓
7. HTTP POST to Python /process_events
   ↓
8. Python groups into episodes
   ↓
9. Python extracts memory items via LLM
   ↓
10. Python applies ADD/UPDATE/NOOP logic
    ↓
11. Python stores in data.db
    ↓
12. Claude Code calls MCP tool: get_user_style_view
    ↓
13. Rust checks view cache staleness
    ↓
14. If stale: GET /views/user_style from Python
    ↓
15. Python generates view from memory items
    ↓
16. Rust caches view, returns to Claude Code
    ↓
17. Claude Code uses context to generate better code
```

## MVP Scope

**In (4 weeks):**
- Single event source: Claude Code JSONL only
- Local Python service: spawned by Rust daemon
- Two memory types: user_style, project_fact
- Two MCP tools: get_user_style_view, get_project_brief_view
- Basic CLI: init, status, config, daemon start/stop
- Auto-configure Claude Code MCP settings

**Out (future):**
- Multi-tool ingestion: Cursor, Codex, Gemini CLI, Git
- Advanced memory: pitfalls, macro recipes
- Cloud sync, team memory sharing
- Web dashboard
- Offline local LLM support

## License

AGPL-3.0
