# Squirrel

Memory layer for AI coding agents. Fully automatic.

## Why Squirrel

| Problem | Squirrel Solution |
|---------|-------------------|
| AI forgets your coding style every session | **Vibe coding works.** The more you code, the more AI learns your preferences. |
| AI repeats the same project mistakes | **Mistakes remembered.** Past errors become future prevention. |
| Docs get stale after code changes | **Docs stay fresh.** Automatic detection when docs need updates. |
| Team knowledge lives in people's heads | **Team memory persists.** Project knowledge survives member changes. |

## How It Works

```
You code with AI (corrections, preferences, decisions)
        ↓
Squirrel watches silently (zero manual work)
        ↓
Memory extracted automatically
        ↓
Three outputs:
  1. User Style    → synced to CLAUDE.md, .cursorrules
  2. Project Memory → exposed via MCP
  3. Doc Awareness  → detects stale docs
```

## Memory Architecture

### User Style (Global)

Personal preferences synced to agent config files. Applies across all projects.

```markdown
<!-- START Squirrel User Style -->
- Prefer async/await over callbacks
- Never use emoji in code
- Keep commits concise
<!-- END Squirrel User Style -->
```

**Storage:** `~/.sqrl/user_style.db`

**Sync targets:** `~/.claude/CLAUDE.md`, `~/.cursor/rules/`, `~/.codex/instructions.md`

### Project Memory (Per-Project)

Project-specific knowledge accessed via MCP.

```
squirrel_get_memory → returns:

## frontend
- Uses shadcn/ui components
- State management with Zustand

## backend
- FastAPI with Pydantic models
- Use httpx for HTTP client
```

**Storage:** `<repo>/.sqrl/memory.db`

**Access:** MCP tool `squirrel_get_memory`

### Doc Awareness

Indexes project docs, detects when code changes but docs don't.

| Feature | Description |
|---------|-------------|
| Doc Tree | Summarized doc structure via MCP |
| Doc Debt | Detects stale docs after commits |
| Auto Hooks | Git hooks remind to update docs |

## Supported Tools

Claude Code, Cursor, Codex CLI (others coming)

## Quick Start

> **v1 releasing in one week.**

```bash
# Configure API key and select your tools
sqrl config

# Initialize in any project (new or existing)
cd ~/my-project
sqrl init
```

## CLI

| Command | Description |
|---------|-------------|
| `sqrl init` | Initialize project |
| `sqrl on` | Enable watcher |
| `sqrl off` | Disable watcher |
| `sqrl config` | Open Dashboard |
| `sqrl status` | Show status |

## For Teams (Cloud)

Squirrel Cloud: shared memory across your engineering team.

| Why Teams Need This |
|---------------------|
| New members get project context instantly via AI |
| Corrections from any member benefit everyone |
| Project knowledge survives when people leave |
| Consistent coding standards across the team |

### Cloud Features

| Feature | Free | Team |
|---------|------|------|
| User style sync | ✓ | ✓ |
| Project memory | ✓ | ✓ |
| Doc awareness | ✓ | ✓ |
| **Shared team memory** | - | ✓ |
| **Cross-machine sync** | - | ✓ |
| **Team management** | - | ✓ |
| **Analytics dashboard** | - | ✓ |

**Interested in Squirrel for your team?** Contact us: [team@squirrel.dev](mailto:team@squirrel.dev)

## Architecture

```
Rust Daemon          Python Memory Service
(I/O, storage, MCP)  (LLM operations)
       │                    │
       └──── IPC ───────────┘
```

| Component | Responsibility |
|-----------|----------------|
| Rust Daemon | Log watching, SQLite, MCP server, CLI, Dashboard |
| Python Service | Log cleaning, memory extraction, style sync |

## Development

```bash
git clone https://github.com/anthropics/squirrel.git
cd squirrel
devenv shell

test-all     # Run tests
dev-daemon   # Start dev daemon
```

## License

AGPL-3.0
