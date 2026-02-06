# Squirrel

Memory layer for AI coding agents. Local-first, no AI in Squirrel itself.

## Why Squirrel

- **AI stops repeating mistakes.** Corrections persist across sessions.
- **Your AI, your rules.** Tell it once, it remembers forever.
- **Docs stay fresh.** Git hooks detect when docs need updates.
- **Zero overhead.** No daemon, no background process. Runs only when called.

## How It Works

```
AI makes a mistake → User corrects it → AI stores the correction
        ↓
AI calls MCP: squirrel_store_memory
        ↓
Squirrel stores to local SQLite
        ↓
Next session: AI calls squirrel_get_memory → corrections loaded
```

Squirrel has **no AI**. Your CLI tool (Claude Code, Cursor, etc.) has full conversation context and decides what to store. Squirrel is just storage + git hooks.

## Memory Types

Memories are behavioral corrections — things that change how the AI acts next time.

| Type | When to store | Example |
|------|---------------|---------|
| `preference` | User corrects the AI's style | "Don't use emojis in code or commits" |
| `project` | AI learns a project rule | "Use httpx not requests in this project" |
| `decision` | A choice is made that constrains future behavior | "We chose SQLite, don't suggest Postgres" |
| `solution` | AI hits an error and finds the fix | "SSL error with requests? Switch to httpx" |

**Don't store:** research in progress, general knowledge, conversation context, anything that doesn't change AI behavior.

## Doc Review

Pre-push hook shows what changed so AI can review docs.

```
You push → pre-push hook shows diff summary + doc file list
    → AI reads output, decides if docs need updating
    → AI updates docs if needed, then push succeeds
```

No static mappings. No complex rules. The AI understands the code and makes the call.

## Quick Start

```bash
# Initialize in any project
cd ~/my-project
sqrl init
```

`sqrl init` automatically:
- Creates `.sqrl/` with config and database
- Installs git hooks for doc debt tracking
- Registers MCP server with your AI tool
- Adds memory triggers to CLAUDE.md

## CLI

| Command | Description |
|---------|-------------|
| `sqrl init` | Initialize project |
| `sqrl status` | Show memories and doc debt |
| `sqrl goaway` | Remove all Squirrel data |
| `sqrl mcp-serve` | Start MCP server (called by AI tool) |

## Supported Tools

Claude Code (others coming)

## Architecture

```
CLI AI (Claude Code, Cursor, etc.)
    │ MCP
    ▼
sqrl binary (Rust)
    │
    ▼
SQLite (.sqrl/memory.db)
```

Single Rust binary. No daemon, no Python, no LLM calls, no network.

| Component | Responsibility |
|-----------|----------------|
| sqrl binary | MCP server, CLI, git hooks, SQLite storage |
| CLI AI | Decides what to remember, fixes doc debt |

## Development

```bash
git clone https://github.com/anthropics/squirrel.git
cd squirrel
devenv shell

cargo test    # Run tests
cargo build   # Build binary
```

## License

AGPL-3.0
