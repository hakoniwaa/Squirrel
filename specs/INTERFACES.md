# Squirrel Interfaces

MCP and CLI contracts. No IPC (single binary, no Python service).

---

## MCP Tools

### MCP-001: squirrel_store_memory

Store a memory. Called by CLI when it decides something is worth remembering.

**Tool Definition:**
```json
{
  "name": "squirrel_store_memory",
  "description": "Store a memory in Squirrel. Use when user states a preference, you learn a project fact, make a decision, or solve a problem.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "The memory content"
      },
      "memory_type": {
        "type": "string",
        "enum": ["preference", "project", "decision", "solution"],
        "description": "Type of memory"
      },
      "tags": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Tags for organization (e.g., 'frontend', 'rust', 'testing')"
      }
    },
    "required": ["content", "memory_type"]
  }
}
```

**Response:**
```json
{
  "stored": true,
  "id": "mem-uuid",
  "deduplicated": false,
  "use_count": 1
}
```

**Deduplication:** If content matches an existing memory (exact or near-match), increments use_count instead of creating a new entry.

---

### MCP-002: squirrel_get_memory

Retrieve memories. Called by CLI when user needs project context or at session start via skill.

**Tool Definition:**
```json
{
  "name": "squirrel_get_memory",
  "description": "Get memories from Squirrel. Call when you need project context, user preferences, or past decisions.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "memory_type": {
        "type": "string",
        "enum": ["preference", "project", "decision", "solution"],
        "description": "Filter by type. Omit to get all."
      },
      "tags": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Filter by tags. Omit to get all."
      },
      "limit": {
        "type": "integer",
        "description": "Max memories to return. Default 50."
      }
    },
    "required": []
  }
}
```

**Response Format:**
```markdown
## preference (3)
- [used 5x] No emojis in code or commits
- [used 3x] Use Gemini 3 Pro, not Claude or older models
- [used 1x] Prefer async/await over callbacks

## project (2)
- [used 4x] Use httpx as HTTP client, not requests
- [used 1x] PostgreSQL 16 for main database

## decision (1)
- [used 2x] Chose SQLite over PostgreSQL for local storage

## solution (1)
- [used 1x] Fixed SSL error by switching from requests to httpx
```

Memories ordered by use_count DESC within each type.

---

## CLI Commands

### CLI-001: sqrl

Show help.

**Usage:** `sqrl`

**Action:** Displays available commands and usage information.

---

### CLI-002: sqrl init

Initialize project for Squirrel. Silent operation, no prompts.

**Usage:**
```bash
sqrl init
```

**Actions:**
1. Create `.sqrl/` directory
2. Create `.sqrl/memory.db` (empty SQLite)
3. Write `.sqrl/config.yaml` with defaults (including seeded doc mappings)
4. Add `.sqrl/` to `.gitignore`
5. If `.git/` exists: install git hooks
6. Create `.claude/skills/squirrel-session/SKILL.md`
7. Add Memory Protocol triggers to `.claude/CLAUDE.md`
8. Register MCP server with enabled AI tools (e.g., `claude mcp add`)

**Does NOT:**
- Ask questions
- Start a daemon
- Process historical logs

---

### CLI-003: sqrl goaway

Remove all Squirrel data from project.

**Usage:**
```bash
sqrl goaway          # Interactive confirmation
sqrl goaway --force  # Skip confirmation
sqrl goaway -f       # Skip confirmation (short form)
```

**Actions:**
1. Show what will be removed
2. Prompt for confirmation (unless --force)
3. Remove git hooks (post-commit, pre-push)
4. Unregister MCP server from enabled AI tools (e.g., `claude mcp remove`)
5. Remove `.claude/skills/squirrel-session/`
6. Remove Memory Protocol triggers from `.claude/CLAUDE.md`
7. Remove `.sqrl/` directory

**Does NOT remove:**
- `.claude/` directory itself
- User's other files
- Git history

---

### CLI-004: sqrl status

Show Squirrel status for current project.

**Usage:** `sqrl status`

**Output:**
```
Squirrel Status
  Project: /home/user/myproject
  Initialized: yes
  Memories: 12 total (5 preference, 4 project, 2 decision, 1 solution)
  Doc debt: 2 pending
  Last stored: 2 hours ago
```

**Exit codes:**
| Code | Meaning |
|------|---------|
| 0 | Project initialized |
| 1 | Project not initialized |

---

### CLI-005: sqrl mcp-serve

Start MCP server. Called by CLI tool configuration, not by user directly.

**Usage:**
```bash
sqrl mcp-serve
```

**Action:** Starts stdio-based MCP server exposing `squirrel_store_memory` and `squirrel_get_memory`.

**CLI tool config example:**
```bash
claude mcp add squirrel -- sqrl mcp-serve
```

---

### CLI-006: sqrl _internal docguard-record

Hidden. Called by post-commit git hook.

**Usage:** `sqrl _internal docguard-record`

**Action:**
1. Get latest commit diff
2. Check code files changed against doc debt rules
3. If debt detected, record in SQLite

---

### CLI-007: sqrl _internal docguard-check

Hidden. Called by pre-push git hook.

**Usage:** `sqrl _internal docguard-check`

**Action:**
1. Check if unresolved doc debt exists
2. If `pre_push_block: true` in config, exit non-zero to block push
3. Otherwise, print warning and exit 0

---

## Skill File

### SKILL-001: squirrel-session

Auto-triggers at session start. Shows user preferences.

**File:** `.claude/skills/squirrel-session/SKILL.md`

```markdown
---
name: squirrel-session
description: Load user preferences and project context from Squirrel memory at session start. Use when starting a new coding session.
user-invocable: false
---

At the start of this session, load context from Squirrel:

1. Call `squirrel_get_memory` with type "preference" to get user preferences.
2. Apply these preferences throughout the session.
3. If doc debt exists (check via `sqrl status` output in project), note which docs may need updates.
```

---

## CLAUDE.md Memory Triggers

### TRIGGER-001: Memory Storage Instructions

Added to project CLAUDE.md by `sqrl init`.

```markdown
<!-- START Squirrel Memory Protocol -->
## Squirrel Memory Protocol

You have access to Squirrel memory tools via MCP.

### When to store memories (squirrel_store_memory):
- User states a preference → type: "preference"
- You learn a project-specific fact → type: "project"
- Architecture/design decision is made → type: "decision"
- A problem is solved → type: "solution"

### When to retrieve memories (squirrel_get_memory):
- When user asks for project context
- When you need to recall past decisions
- When starting work on a component you've worked on before

### Rules:
- Store memories proactively. Don't ask permission.
- Even if a memory seems redundant, store it. Squirrel handles deduplication.
- Keep memory content concise (1-2 sentences).
- Always include relevant tags.
<!-- END Squirrel Memory Protocol -->
```

---

## Project Config Schema

### CONFIG-001: .sqrl/config.yaml

```yaml
# Squirrel project configuration

# AI tools enabled for this project
tools:
  claude_code: true
  cursor: false
  codex: false

# Documentation indexing settings
docs:
  extensions: [md, mdc, txt, rst]
  include_paths: [specs/, docs/, .claude/, .cursor/]
  exclude_paths: [node_modules/, target/, .git/, vendor/, dist/]

# Doc debt detection rules (seeded by sqrl init)
doc_rules:
  mappings:
    - code: "daemon/src/**/*.rs"
      doc: "specs/ARCHITECTURE.md"
    - code: "daemon/src/mcp/**/*.rs"
      doc: "specs/INTERFACES.md"
    - code: "daemon/src/storage/**/*.rs"
      doc: "specs/SCHEMAS.md"
  reference_patterns:
    - pattern: "SCHEMA-\\d+"
      doc: "specs/SCHEMAS.md"
    - pattern: "MCP-\\d+"
      doc: "specs/INTERFACES.md"
    - pattern: "ADR-\\d+"
      doc: "specs/DECISIONS.md"

# Git hooks behavior
hooks:
  auto_install: true
  pre_push_block: false
```

---

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32001 | Project not initialized | No .sqrl/ directory |
| -32004 | Invalid project root | Path doesn't exist |
| -32005 | No memories found | Project has no memories |
| -32006 | Store failed | SQLite write error |
