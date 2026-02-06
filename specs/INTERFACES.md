# Squirrel Interfaces

MCP and CLI contracts. No IPC (single binary, no Python service).

---

## MCP Tools

### MCP-001: squirrel_store_memory

Store a behavioral correction. Called by CLI AI when the user corrects it, it learns a project rule, a decision constrains future work, or it finds an error fix.

**Tool Definition:**
```json
{
  "name": "squirrel_store_memory",
  "description": "Store a behavioral correction. Use when the user corrects you, you learn a project rule, a decision constrains future work, or you find a fix for an error.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "An actionable instruction: 'Do X', 'Don't do Y', or 'When Z, do W' (1-2 sentences)"
      },
      "memory_type": {
        "type": "string",
        "enum": ["preference", "project", "decision", "solution"],
        "description": "Type: preference (user correction), project (project rule), decision (constrains future work), solution (error fix)"
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

Retrieve behavioral corrections. Called at session start (via skill) or before making choices the user may have corrected before.

**Tool Definition:**
```json
{
  "name": "squirrel_get_memory",
  "description": "Get behavioral corrections from Squirrel. Call at session start or before making choices the user may have corrected before.",
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
- [used 5x] Don't use emojis in code or commits
- [used 3x] Use Gemini 3 Pro, don't suggest Claude or older models
- [used 1x] Prefer async/await over callbacks

## project (2)
- [used 4x] Use httpx not requests in this project
- [used 1x] PostgreSQL 16 for main database

## decision (1)
- [used 2x] We chose SQLite for local storage, don't suggest Postgres

## solution (1)
- [used 1x] SSL error with requests? Switch to httpx
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
3. Write `.sqrl/config.yaml` with defaults
4. Add `.sqrl/` to `.gitignore`
5. If `.git/` exists: install pre-push hook
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
3. Remove git hooks (pre-push)
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
  Last activity: 2 hours ago
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

### CLI-006: sqrl _internal docguard-check

Hidden. Called by pre-push git hook.

**Usage:** `sqrl _internal docguard-check`

**Action:** Prints diff summary and doc file list so AI can decide if docs need updating.

**Output example:**
```
═══════════════════════════════════════════════════════════════
 Squirrel: Review changes before push
═══════════════════════════════════════════════════════════════

 Commits to push: 3

 Files changed:
   daemon/src/mcp/mod.rs     | 45 ++++---
   daemon/src/storage/mod.rs | 23 ++--

 Doc files in repo:
   specs/ARCHITECTURE.md
   specs/INTERFACES.md
   README.md

 → Review if any docs need updating based on these changes.
═══════════════════════════════════════════════════════════════
```

Always exits 0 (informational only, never blocks).

---

## Skill File

### SKILL-001: squirrel-session

Auto-triggers at session start. Loads behavioral corrections.

**File:** `.claude/skills/squirrel-session/SKILL.md`

```markdown
---
name: squirrel-session
description: Load behavioral corrections from Squirrel memory at session start. Use when starting a new coding session.
user-invocable: false
---

At the start of this session, load corrections from Squirrel:

1. Call `squirrel_get_memory` to get all behavioral corrections.
2. Apply these corrections throughout the session.
```

---

## CLAUDE.md Memory Triggers

### TRIGGER-001: Memory Storage Instructions

Added to project CLAUDE.md by `sqrl init`.

```markdown
<!-- START Squirrel Memory Protocol -->
## Squirrel Memory Protocol

You have access to Squirrel memory tools via MCP. Memories are **behavioral corrections** — things that change how you act next time.

### When to store (squirrel_store_memory):
- User corrects your behavior → type: "preference" (e.g., "Don't use emojis in commits")
- You learn a project-specific rule → type: "project" (e.g., "Use httpx not requests here")
- A choice is made that constrains future work → type: "decision" (e.g., "We chose SQLite, don't suggest Postgres")
- You hit an error and find the fix → type: "solution" (e.g., "SSL error with requests? Switch to httpx")

### When NOT to store:
- Research in progress (no decision made yet)
- General knowledge (not project-specific)
- Conversation context (already in chat history)
- Anything that doesn't change your future behavior

### When to retrieve (squirrel_get_memory):
- At session start (via squirrel-session skill)
- Before making choices the user may have corrected before

### Rules:
- Store corrections proactively when the user corrects you. Don't ask permission.
- Every memory should be an actionable instruction: "Do X" or "Don't do Y" or "When Z, do W".
- Keep content concise (1-2 sentences).
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

# Documentation file settings
docs:
  extensions: [md, mdc, txt, rst]
  include_paths: [specs/, docs/, .claude/, .cursor/]
  exclude_paths: [node_modules/, target/, .git/, vendor/, dist/]

# Git hooks behavior
hooks:
  auto_install: true
```

---

## Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32001 | Project not initialized | No .sqrl/ directory |
| -32004 | Invalid project root | Path doesn't exist |
| -32005 | No memories found | Project has no memories |
| -32006 | Store failed | SQLite write error |
