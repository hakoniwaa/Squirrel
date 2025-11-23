# Project Structure

Complete directory layout and file responsibilities for Squirrel.

## Root Layout

```
Squirrel/
├── agent/                  # Rust module
├── memory_service/         # Python module
├── docs/                   # Documentation
├── .claude/                # Claude Code config
├── .cursorrules            # Cursor config
├── AGENTS.md               # Codex CLI config
├── GEMINI.md               # Gemini CLI config
├── CONTRIBUTING.md         # Contributor guide
├── LICENSE                 # AGPL-3.0
└── README.md               # Main documentation
```

## Rust Agent Module (`agent/`)

```
agent/
├── Cargo.toml              # Rust dependencies
├── Cargo.lock
├── src/
│   ├── main.rs             # Entry point: routes to daemon/mcp/cli
│   ├── lib.rs              # Shared library code
│   │
│   ├── daemon.rs           # Global daemon process
│   │   ├── DaemonServer    # TCP server for IPC
│   │   ├── spawn_python()  # Launch Python subprocess
│   │   ├── watch_repos()   # Monitor registered repos
│   │   └── health_check()  # Keep Python alive
│   │
│   ├── watcher.rs          # File system monitoring
│   │   ├── ClaudeWatcher   # Watch ~/.claude/projects/**/*.jsonl
│   │   ├── parse_jsonl()   # JSONL → Event
│   │   └── handle_change() # Notify daemon on new events
│   │
│   ├── events.rs           # Event data model
│   │   ├── Event struct    # Core event type
│   │   ├── SourceTool enum # claude_code, cursor, git, ...
│   │   ├── EventType enum  # chat, code_change, commit, ...
│   │   ├── compute_hash()  # Deduplication hash
│   │   ├── EventStore      # SQLite operations
│   │   └── batch_unsent()  # Get events to send to Python
│   │
│   ├── storage.rs          # SQLite database layer
│   │   ├── init_user_db()  # ~/.sqrl/user.db schema
│   │   ├── init_project_db() # <repo>/.ctx/data.db schema
│   │   ├── get_connection() # Connection pooling
│   │   └── migrations/      # Schema versioning
│   │
│   ├── mcp.rs              # MCP stdio server
│   │   ├── McpServer       # MCP protocol handler
│   │   ├── handle_tool_call() # Route to tool handlers
│   │   ├── get_user_style_view_tool()
│   │   ├── get_project_brief_view_tool()
│   │   └── connect_daemon() # TCP to daemon for data
│   │
│   ├── python_client.rs    # HTTP client to Python service
│   │   ├── PythonClient    # HTTP client wrapper
│   │   ├── process_events() # POST /process_events
│   │   ├── get_user_style_view() # GET /views/user_style
│   │   ├── get_project_brief_view() # GET /views/project_brief
│   │   └── retry_logic()   # Exponential backoff
│   │
│   ├── views.rs            # View caching
│   │   ├── ViewCache       # Manage <repo>/.ctx/views/
│   │   ├── is_stale()      # Check .meta.json
│   │   ├── read_cache()    # Read cached view
│   │   ├── write_cache()   # Update cache + meta
│   │   └── ViewMeta struct # Staleness metadata
│   │
│   ├── cli.rs              # CLI commands
│   │   ├── cmd_init()      # sqrl init
│   │   ├── cmd_config()    # sqrl config
│   │   ├── cmd_status()    # sqrl status
│   │   ├── cmd_daemon_start() # sqrl daemon start
│   │   ├── cmd_daemon_stop()  # sqrl daemon stop
│   │   └── auto_config_mcp()  # Patch MCP configs
│   │
│   ├── config.rs           # Configuration management
│   │   ├── Config struct   # ~/.sqrl/config.toml
│   │   ├── load_config()
│   │   ├── save_config()
│   │   └── get_api_key()   # Read user's LLM API keys
│   │
│   └── utils.rs            # Shared utilities
│       ├── get_sqrl_dir()  # ~/.sqrl/
│       ├── get_ctx_dir()   # <repo>/.ctx/
│       ├── find_repo_root() # Walk up to .git/
│       └── ensure_dir()    # Create dir if missing
│
└── tests/
    ├── integration/
    │   ├── daemon_test.rs
    │   ├── watcher_test.rs
    │   └── mcp_test.rs
    └── unit/
        ├── events_test.rs
        └── storage_test.rs
```

## Python Memory Service Module (`memory_service/`)

```
memory_service/
├── pyproject.toml          # Python dependencies (uv/pip)
├── README.md               # Python module docs
├── squirrel_memory/
│   ├── __init__.py         # Package init
│   │
│   ├── server.py           # FastAPI application
│   │   ├── app = FastAPI()
│   │   ├── POST /process_events
│   │   ├── GET /views/user_style
│   │   ├── GET /views/project_brief
│   │   └── startup/shutdown hooks
│   │
│   ├── models.py           # Pydantic data models
│   │   ├── Event           # Input from Rust
│   │   ├── Episode         # Grouped events
│   │   ├── MemoryItem      # Extracted memory
│   │   ├── UserStyleView   # Output view
│   │   └── ProjectBriefView # Output view
│   │
│   ├── extractor.py        # Event → Memory extraction
│   │   ├── Extractor class
│   │   ├── group_episodes() # Time/session-based grouping
│   │   ├── extract_user_style() # LLM call
│   │   ├── extract_project_facts() # LLM call
│   │   └── assign_importance() # Score 0.0-1.0
│   │
│   ├── updater.py          # Memory update logic
│   │   ├── MemoryUpdater class
│   │   ├── find_similar() # Key-based or semantic search
│   │   ├── decide_action() # LLM: ADD/UPDATE/NOOP/DELETE
│   │   ├── merge_items()  # Combine memory items
│   │   └── apply_updates() # Write to DB
│   │
│   ├── views.py            # View generation
│   │   ├── ViewGenerator class
│   │   ├── build_user_style_view() # Summarize user memory
│   │   ├── build_project_brief_view() # Summarize project
│   │   ├── select_memories() # Filter by importance/recency
│   │   └── format_view()  # Compact token-efficient format
│   │
│   ├── storage.py          # Database operations
│   │   ├── get_db_connection() # SQLite connection
│   │   ├── save_episodes()
│   │   ├── save_memory_items()
│   │   ├── query_memories() # Fetch for views
│   │   └── init_schema()   # Create tables if missing
│   │
│   ├── llm.py              # LLM client wrapper
│   │   ├── LLMClient class
│   │   ├── call_openai()   # GPT-4 / GPT-4o
│   │   ├── call_anthropic() # Claude 3.5
│   │   ├── call_gemini()   # Gemini 2.0 Pro
│   │   └── retry_with_backoff()
│   │
│   └── prompts.py          # LLM prompt templates
│       ├── EXTRACT_USER_STYLE_PROMPT
│       ├── EXTRACT_PROJECT_FACTS_PROMPT
│       ├── UPDATE_DECISION_PROMPT
│       └── VIEW_GENERATION_PROMPT
│
└── tests/
    ├── test_extractor.py
    ├── test_updater.py
    ├── test_views.py
    └── fixtures/
        └── sample_events.json
```

## Documentation (`docs/`)

```
docs/
├── ARCHITECTURE.md         # System design, component interaction
├── PROJECT_STRUCTURE.md    # This file
├── API.md                  # Python HTTP API specification
├── MCP_TOOLS.md            # MCP tool documentation
├── DATA_MODEL.md           # Event/Episode/Memory/View schemas
├── DEVELOPMENT.md          # Setup, build, test instructions
└── DEPLOYMENT.md           # Installation, distribution (future)
```

## Configuration Files

```
.claude/
├── CLAUDE.md               # Team standards (read by Claude Code)
└── settings.local.json     # Local settings (gitignored)

.cursorrules                # Cursor configuration
AGENTS.md                   # Codex CLI configuration
GEMINI.md                   # Gemini CLI configuration
```

## Runtime Directories (Created by sqrl)

```
~/.sqrl/                    # User-scope data
├── config.toml             # User settings
│   ├── [user]
│   │   └── id = "uuid"
│   ├── [llm]
│   │   ├── openai_api_key = "sk-..."
│   │   ├── anthropic_api_key = "sk-ant-..."
│   │   └── default_model = "gpt-4"
│   └── [daemon]
│       └── port = 9468
│
├── user.db                 # SQLite: user-level memory
│   └── Tables:
│       ├── user_style_items
│       └── sync_state
│
├── projects.json           # Registered repos
│   └── {"projects": ["/path/to/repo1", "/path/to/repo2"]}
│
├── daemon.json             # Daemon connection info
│   └── {"pid": 12345, "host": "127.0.0.1", "port": 9468}
│
└── memory-service.json     # Python service info
    └── {"pid": 23456, "host": "127.0.0.1", "port": 8734}

<repo>/.ctx/                # Project-scope data
├── data.db                 # SQLite: events, episodes, memory
│   └── Tables:
│       ├── events
│       ├── episodes
│       ├── memory_items
│       └── sync_state
│
└── views/                  # Cached views
    ├── user_style.json
    ├── project_brief.json
    └── .meta.json          # Staleness metadata
        └── {
              "user_style": {
                "last_generated": "2025-11-23T10:30:00Z",
                "events_count_at_generation": 1234,
                "ttl_minutes": 10
              }
            }
```

## File Responsibilities Summary

### Rust Agent

| File | Responsibility | Key Functions |
|------|---------------|---------------|
| `daemon.rs` | Global process lifecycle | spawn_python, watch_repos, TCP server |
| `watcher.rs` | File monitoring | parse JSONL, detect changes |
| `events.rs` | Event data model | Event struct, hash, storage ops |
| `storage.rs` | SQLite operations | init schemas, connections |
| `mcp.rs` | MCP protocol | stdio server, tool handlers |
| `python_client.rs` | HTTP to Python | POST/GET requests, retry |
| `views.rs` | View caching | staleness check, read/write cache |
| `cli.rs` | User commands | init, config, status, daemon |
| `config.rs` | Settings management | load/save TOML, API keys |
| `utils.rs` | Shared helpers | paths, dirs, repo detection |

### Python Memory Service

| File | Responsibility | Key Functions |
|------|---------------|---------------|
| `server.py` | HTTP endpoints | FastAPI routes |
| `models.py` | Data schemas | Pydantic models |
| `extractor.py` | Pattern extraction | group episodes, LLM extraction |
| `updater.py` | Memory updates | find similar, ADD/UPDATE/NOOP |
| `views.py` | View generation | build compact summaries |
| `storage.py` | Database ops | save/query memory items |
| `llm.py` | LLM client | call OpenAI/Anthropic/Gemini |
| `prompts.py` | Prompt templates | extraction/update/view prompts |

## Development Workflow

```
1. Clone repo
   git clone https://github.com/kaminoguo/Squirrel.git
   cd Squirrel

2. Build Rust module
   cd agent
   cargo build

3. Install Python module
   cd ../memory_service
   pip install -e .

4. Run daemon (development mode)
   cd ../agent
   cargo run --bin sqrl daemon start

5. Initialize a project
   cd ~/my-project
   sqrl init

6. Configure MCP for Claude Code
   # sqrl init auto-patches ~/.claude/mcp.json

7. Start coding with Claude Code
   # Daemon watches, sends to Python, caches views
```

## Build Artifacts

```
agent/target/
├── debug/
│   └── sqrl                # Development binary
└── release/
    └── sqrl                # Production binary

memory_service/dist/
└── squirrel_memory-0.1.0-py3-none-any.whl
```

## Distribution (Future)

```
Planned package structure:

macOS:
  brew install sqrl
  → /usr/local/bin/sqrl

Linux:
  curl -fsSL https://get.sqrl.dev | sh
  → ~/.local/bin/sqrl

Windows:
  scoop install sqrl
  → C:\Users\<user>\scoop\apps\sqrl\current\sqrl.exe
```

## Notes for AI Assistants

When modifying code:
- Rust changes: navigate to `agent/src/<file>.rs`
- Python changes: navigate to `memory_service/squirrel_memory/<file>.py`
- Docs updates: navigate to `docs/<file>.md`
- Config changes: update appropriate `.md` file in root

SQLite schemas defined in:
- Rust: `agent/src/storage.rs`
- Python: `memory_service/squirrel_memory/storage.py`

HTTP API contract: See `docs/API.md`
MCP protocol: See `docs/MCP_TOOLS.md`
