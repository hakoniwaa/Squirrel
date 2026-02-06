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

Squirrel has **no AI**. Your CLI tool (Claude Code, Cursor, etc.) decides what to store. Squirrel is just storage + git hooks.

## Memory Types

| Type | Storage | When to store | Example |
|------|---------|---------------|---------|
| `preference` | Global (~/.sqrl/) | User corrects AI behavior | "Don't use emojis in commits" |
| `project` | Project (.sqrl/) | Project-specific rule | "Use httpx not requests here" |

**Don't store:** research in progress, general knowledge, conversation context.

## Quick Start

```bash
# Configure Squirrel globally
sqrl config

# Initialize in any project
cd ~/my-project
sqrl init
```

## CLI

| Command | Description |
|---------|-------------|
| `sqrl config` | Open web UI for global configuration |
| `sqrl init` | Initialize project |
| `sqrl apply` | Apply global MCP configs to project |
| `sqrl status` | Show status |
| `sqrl goaway` | Remove Squirrel from project |

## Architecture

```
~/.sqrl/                     # Global
├── config.yaml              # Tools, enabled MCPs
├── memory.db                # User preferences
└── mcp-config.json          # Uploaded MCP definitions

<project>/.sqrl/             # Project
├── config.yaml              # Project settings
└── memory.db                # Project memories
```

Single Rust binary. No daemon, no Python, no LLM calls.

## Development

```bash
git clone https://github.com/anthropics/squirrel.git
cd squirrel
devenv shell

cargo test
cargo build
```

## License

AGPL-3.0
