# Squirrel

Local-first memory system for AI coding tools. Learns from your coding sessions, syncs your style to agent config files, and provides project context via MCP.

## What It Does

```
You code with Claude Code / Cursor / Codex CLI / Gemini CLI
                    ↓
    Squirrel watches logs (100% passive, invisible)
                    ↓
    Memory pipeline:
      1. Log Cleaner (cheap model) - compress, filter noise
      2. Memory Extractor (strong model) - extract memories
                    ↓
    Two types of memories:
      User Style → synced to agent.md files
      Project Memory → accessed via MCP
                    ↓
    AI tools understand you and your project
```

## What Squirrel Enables

| Capability | Description |
|------------|-------------|
| **Personal coding style** | Vibe coding gradually learns your preferences. AI adapts to you, not the other way around. |
| **Cross-CLI memory** | Switch between Claude Code, Cursor, Codex CLI, Gemini CLI - memories follow you. |
| **Project awareness** | AI understands project history, architecture decisions, and current progress. |
| **Team onboarding** | New members instantly benefit from accumulated project knowledge via AI. |
| **Mistake prevention** | AI remembers past failures and avoids repeating them. |
| **No repeated explanations** | Stop telling AI the same project conventions every session. |
| **Knowledge retention** | Team members leave, project memory stays. |

## Memory Types

### User Style

Personal development preferences that apply across ALL projects:

| Example |
|---------|
| "Prefer async/await over callbacks" |
| "Never use emoji in code or comments" |
| "Commits should use minimal English" |
| "AI should maintain critical, calm attitude" |

**Storage:** `~/.sqrl/user_style.db`

**Access:** Synced to agent.md files (CLAUDE.md, .cursorrules, etc.)

### Project Memory

Project-specific knowledge organized by category:

| Category | Description |
|----------|-------------|
| `frontend` | UI framework, components, styling |
| `backend` | API, database, services |
| `docs_test` | Documentation, testing |
| `other` | Everything else |

**Storage:** `<repo>/.sqrl/memory.db`

**Access:** Via MCP tool `squirrel_get_memory`

## Architecture

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

| Component | Language | Role |
|-----------|----------|------|
| **Rust Daemon** | Rust | Log watcher, SQLite + sqlite-vec, MCP server, CLI |
| **Python Memory Service** | Python | Log Cleaner, Memory Extractor, Style Syncer |

## Quick Start

```bash
# Initialize a project
cd ~/my-project
sqrl init

# Initialize with historical log processing
sqrl init --history 30    # Process last 30 days
sqrl init --history all   # Process all history

# Check status
sqrl status

# Open Dashboard
sqrl
```

## CLI Commands

| Command | Purpose |
|---------|---------|
| `sqrl` | Open Dashboard in browser |
| `sqrl init` | Initialize project (watch future logs only) |
| `sqrl init --history <days\|all>` | Initialize + process historical logs |
| `sqrl status` | Show daemon status and stats |

All other operations (edit, delete, search) happen in Dashboard.

## MCP Tool

```json
{
  "name": "squirrel_get_memory",
  "description": "Get project memories from Squirrel"
}
```

Returns all project memories grouped by category:

```markdown
## frontend
- Component library uses shadcn/ui
- State management with Zustand

## backend
- Use httpx as HTTP client
- API uses FastAPI with Pydantic models

## docs_test
- Tests use pytest with fixtures in conftest.py

## other
- Deploy via GitHub Actions to Vercel
```

## Agent File Integration

Squirrel manages a block in agent config files:

```markdown
<!-- START Squirrel User Style -->
## Development Style (managed by Squirrel)

- Prefer async/await over callbacks
- Never use emoji in code or comments
- Commits should use minimal English
- AI should maintain critical, calm attitude

<!-- END Squirrel User Style -->
```

Supported files:

| Tool | File |
|------|------|
| Claude Code | `~/.claude/CLAUDE.md`, `<repo>/CLAUDE.md` |
| Cursor | `~/.cursor/rules/*.mdc`, `<repo>/.cursorrules` |
| Codex CLI | `~/.codex/instructions.md` |
| Gemini CLI | `~/.gemini/instructions.md` |

## Storage

```
~/.sqrl/
├── user_style.db              # Personal development style

<repo>/.sqrl/
├── memory.db                  # Project-specific memories
```

## Dashboard

Web UI for managing memories:

| Feature | Free | Team (B2B) |
|---------|------|------------|
| View/edit personal style | ✓ | ✓ |
| View/edit project memory | ✓ | ✓ |
| Memory categories management | ✓ | ✓ |
| Team style management | - | ✓ |
| Team member management | - | ✓ |
| Cloud sync | - | ✓ |
| Activity analytics | - | ✓ |

## Development Setup

### Option 1: Nix/devenv (Recommended)

```bash
git clone https://github.com/kaminoguo/Squirrel.git
cd Squirrel
devenv shell

# Available commands:
test-all    # Run all tests
dev-daemon  # Start daemon in dev mode
fmt         # Format all code
lint        # Lint all code
```

### Option 2: Manual Setup

```bash
# Rust 1.83+
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Python via uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Design Principles

| Principle | Description |
|-----------|-------------|
| **Simple** | use_count based ordering. No complex evaluation loops. |
| **AI-Primary** | LLM decides what to extract, not hardcoded rules. |
| **Passive** | Daemon watches logs, never intercepts. |
| **Distributed-first** | All extraction happens locally. |

## v1 Scope

- Passive log watching (Claude Code, Cursor, Codex CLI, Gemini CLI)
- 2-stage model pipeline (Log Cleaner + Memory Extractor)
- User style synced to agent.md files
- Project memory via MCP
- 4 default categories (frontend, backend, docs_test, other)
- Dashboard for management
- Cross-platform (Mac, Linux, Windows)

**v2:** Team/cloud sync, shared memories, analytics

## Contributing

1. Fork and clone
2. Create branch: `git checkout -b yourname/feat-description`
3. Make changes, run tests
4. Commit: `feat(scope): description`
5. Push and create PR

## License

AGPL-3.0
