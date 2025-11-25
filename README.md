# Squirrel

Local-first memory system for AI coding tools. Learns your coding patterns and provides personalized, task-aware context to AI assistants via MCP.

## What It Does

Squirrel passively watches your development activity, extracts coding patterns and project knowledge, and feeds that context back to AI tools so they generate code matching your style.

```
You code with Claude Code
        ↓
Squirrel watches and learns
        ↓
AI tools get personalized context
        ↓
Better code suggestions
```

The more you code, the better Squirrel understands your preferences.

## Key Features

- **Task-Aware Context**: Given a specific task, returns only relevant memory with explanations
- **User Style Memory**: Learns your coding preferences (async/await, type hints, testing patterns)
- **Project Knowledge**: Remembers project facts (framework, database, key endpoints)
- **Token-Efficient**: Budget-bounded outputs that fit any context window
- **Local-First**: All data stays on your machine

## Quick Start

```bash
# Install
brew install sqrl

# Start daemon (one per machine)
sqrl daemon start

# Initialize a project
cd ~/my-project
sqrl init

# Done - Squirrel now watches and learns
```

## Architecture

Two modules working together:

| Module | Language | Role |
|--------|----------|------|
| **Rust Agent** | Rust | Daemon, file watchers, SQLite storage, MCP server, CLI |
| **Memory Service** | Python | LLM-based pattern extraction, memory updates, view generation |

```
~/.sqrl/                     # Global config and user memory
<repo>/.ctx/                 # Per-project events, episodes, memory, views
```

## MCP Tools

Squirrel exposes 5 MCP tools for AI assistants:

| Tool | Purpose |
|------|---------|
| `get_task_context` | Task-aware memory with relevance explanations (primary) |
| `get_user_style_view` | User coding preferences summary |
| `get_project_brief_view` | Project overview and key facts |
| `get_pitfalls_view` | Known pitfalls for specific scope |
| `search_project_memory` | Semantic memory search with explanations |

All tools accept `context_budget_tokens` to adapt to any model's context size.

## How It Works

### Input (Passive Learning)

```
Claude Code logs → Rust watcher → Events → Batch to Python
                                              ↓
                              Episodes → LLM extraction → Memory items
```

1. Squirrel watches `~/.claude/projects/**/*.jsonl`
2. Parses logs into normalized Event structs
3. Batches events (20 events or 30 seconds)
4. Python groups events into Episodes (coding sessions)
5. LLM extracts structured memory (user_style, project_fact, pitfalls)
6. Mem0-style update logic keeps memory clean (ADD/UPDATE/NOOP/DELETE)

### Output (On-Demand Context)

```
AI tool calls MCP → Rust daemon → Python views → Structured JSON
```

1. AI tool calls `get_task_context` with task description
2. Python retrieves relevant memory candidates
3. LLM selects and explains relevant memories
4. Returns budget-bounded markdown + structured data

## Example Output

```json
{
  "type": "task_context",
  "task_description": "Add a delete endpoint",
  "has_relevant_memory": true,
  "selected_memories": [
    {
      "key": "async_preference",
      "content": "Prefers async/await for I/O handlers",
      "reason": "This is an HTTP endpoint; user prefers async."
    },
    {
      "key": "testing_framework",
      "content": "Uses pytest with fixtures",
      "reason": "Task will need tests; user uses pytest fixtures."
    }
  ],
  "markdown": "## Relevant memory\n\n- Use async/await\n- Add pytest fixtures"
}
```

## CLI Commands

```bash
sqrl init              # Initialize project, create .ctx/
sqrl config            # Set user_id, API keys
sqrl daemon start      # Start global daemon
sqrl daemon stop       # Stop daemon
sqrl status            # Show project memory state
sqrl mcp               # Run MCP server (called by AI tools)
```

## Data Model

| Table | Purpose |
|-------|---------|
| `events` | Raw activity from AI tools |
| `episodes` | Grouped coding sessions with summaries |
| `memory_items` | Long-term facts and preferences |
| `view_meta` | Cache staleness tracking |

Memory types:
- `user_style`: Coding preferences (async, type hints, naming)
- `project_fact`: Project knowledge (framework, DB, services)
- `pitfall`: Known issues and gotchas
- `recipe`: Common patterns and solutions

## Configuration

```toml
# ~/.sqrl/config.toml
[user]
id = "alice"

[llm]
openai_api_key = "sk-..."
anthropic_api_key = "sk-ant-..."
default_model = "gpt-4"

[daemon]
port = 9468
```

## Documentation

- [Architecture Spec](docs/ARCHITECTURE.md) - Full technical design
- [Development Plan](docs/DEVELOPMENT_PLAN.md) - Implementation roadmap
- [Process Example](docs/EXAMPLE.md) - Detailed walkthrough
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Directory layout

## MVP Scope (4 weeks)

**In:**
- Single event source: Claude Code JSONL
- 5 MCP tools with task-aware context
- Two memory types: user_style, project_fact
- Basic CLI: init, config, daemon, status
- Budget-bounded, explainable outputs

**Future:**
- Multi-tool ingestion: Cursor, Codex CLI, Gemini CLI, Git
- Advanced memory: pitfalls, recipes
- Cloud sync, team memory sharing
- Web dashboard

## License

AGPL-3.0
