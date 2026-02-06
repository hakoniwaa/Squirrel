# Squirrel Interfaces

MCP and CLI contracts. No IPC (single binary, no Python service).

---

## MCP Tools

### MCP-001: squirrel_store_memory

Store a behavioral correction.

**Tool Definition:**
```json
{
  "name": "squirrel_store_memory",
  "description": "Store a behavioral correction. Use when the user corrects you or you learn a project rule.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "content": {
        "type": "string",
        "description": "An actionable instruction: 'Do X', 'Don't do Y', or 'When Z, do W' (1-2 sentences)"
      },
      "memory_type": {
        "type": "string",
        "enum": ["preference", "project"],
        "description": "Type: preference (global user preference), project (project-specific rule)"
      },
      "tags": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Tags for organization"
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

**Storage:**
- `preference` → stored in `~/.sqrl/memory.db` (global)
- `project` → stored in `.sqrl/memory.db` (project)

---

### MCP-002: squirrel_get_memory

Retrieve behavioral corrections from both global and project databases.

**Tool Definition:**
```json
{
  "name": "squirrel_get_memory",
  "description": "Get behavioral corrections from Squirrel. Call at session start or before making choices.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "memory_type": {
        "type": "string",
        "enum": ["preference", "project"],
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
## preference (global)
- [used 5x] Don't use emojis in code or commits
- [used 3x] Prefer async/await over callbacks

## project
- [used 4x] Use httpx not requests in this project
- [used 1x] PostgreSQL 16 for database
```

---

## CLI Commands

### CLI-001: sqrl

Show help.

**Usage:** `sqrl`

---

### CLI-002: sqrl config

Open web UI for global configuration.

**Usage:**
```bash
sqrl config              # Open browser to localhost:3333
sqrl config --no-open    # Start server without opening browser
```

**Web UI Features:**
- Select enabled CLI tools (Claude Code, Git)
- Upload MCP config file, select which MCPs to enable
- View/edit global preferences and project memories
- Black/white minimal theme

---

### CLI-003: sqrl init

Initialize project for Squirrel.

**Usage:** `sqrl init`

**Actions:**
1. Create `.sqrl/` directory
2. Create `.sqrl/memory.db` (project memories)
3. Write `.sqrl/config.yaml`
4. Add `.sqrl/` to `.gitignore`
5. If `.git/` exists: install pre-push hook
6. Create `.claude/skills/squirrel-session/SKILL.md`
7. Add Memory Protocol triggers to `.claude/CLAUDE.md`
8. Run `sqrl apply` to register enabled MCPs

---

### CLI-004: sqrl apply

Apply enabled MCP configs to current project.

**Usage:** `sqrl apply`

**Actions:**
1. Read `~/.sqrl/config.yaml` for enabled tools and MCPs
2. For each enabled tool, register enabled MCPs
3. Print summary

---

### CLI-005: sqrl goaway

Remove all Squirrel data from project.

**Usage:**
```bash
sqrl goaway          # Interactive confirmation
sqrl goaway --force  # Skip confirmation
```

**Does NOT remove:** Global config (`~/.sqrl/`)

---

### CLI-006: sqrl status

Show Squirrel status.

**Usage:** `sqrl status`

**Output:**
```
Squirrel Status
  Project: /home/user/myproject
  Initialized: yes
  Project memories: 5
  Last activity: 2 hours ago

Global Config: ~/.sqrl/
  Preferences: 3
  Enabled tools: Claude Code, Git
  Enabled MCPs: 2
```

---

### CLI-007: sqrl mcp-serve

Start MCP server (called by CLI tools, not user).

**Usage:** `sqrl mcp-serve`

---

### CLI-008: sqrl _internal docguard-check

Hidden. Called by pre-push git hook.

---

## Skill File

### SKILL-001: squirrel-session

**File:** `.claude/skills/squirrel-session/SKILL.md`

```markdown
---
name: squirrel-session
description: Load behavioral corrections from Squirrel at session start.
user-invocable: false
---

At session start, call `squirrel_get_memory` to get all corrections and apply them.
```

---

## CLAUDE.md Memory Triggers

### TRIGGER-001: Memory Storage Instructions

```markdown
<!-- START Squirrel Memory Protocol -->
## Squirrel Memory Protocol

You have access to Squirrel memory tools via MCP.

### When to store (squirrel_store_memory):
- User corrects your behavior → type: "preference" (global, applies everywhere)
- You learn a project-specific rule → type: "project" (only this project)

### When NOT to store:
- Research in progress
- General knowledge
- Conversation context

### Rules:
- Store corrections proactively. Don't ask permission.
- Every memory: "Do X" or "Don't do Y" or "When Z, do W"
- Keep concise (1-2 sentences)
<!-- END Squirrel Memory Protocol -->
```

---

## Config Schemas

### CONFIG-001: ~/.sqrl/config.yaml (Global)

```yaml
# Squirrel global configuration

tools:
  claude_code: true
  git: true

# MCPs enabled (from uploaded config file)
mcps:
  - squirrel
  - other-mcp

ui:
  port: 3333
```

### CONFIG-002: .sqrl/config.yaml (Project)

```yaml
# Squirrel project configuration

hooks:
  auto_install: true
```

---

## MCP Config Upload

User uploads a file (e.g., `.mcp.json` or `mcp-config.json`) containing MCP definitions:

```json
{
  "mcpServers": {
    "squirrel": {
      "command": "sqrl",
      "args": ["mcp-serve"]
    },
    "other-mcp": {
      "command": "/path/to/mcp",
      "args": ["serve"],
      "env": { "API_KEY": "xxx" }
    }
  }
}
```

Squirrel parses this file, shows MCPs in the UI, user selects which to enable.
`sqrl apply` registers enabled MCPs with all enabled CLI tools.

---

## Web API

### API-001: Config Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/config` | Get global config |
| POST | `/api/config` | Update global config |

### API-002: MCP Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/mcps` | List parsed MCPs |
| POST | `/api/mcps/upload` | Upload MCP config file |
| POST | `/api/mcps/enable` | Enable/disable MCPs |

### API-003: Memory Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/preferences` | List global preferences |
| POST | `/api/preferences` | Add preference |
| DELETE | `/api/preferences/:id` | Delete preference |
| GET | `/api/memories?project=<path>` | List project memories |
| POST | `/api/memories?project=<path>` | Add project memory |
| DELETE | `/api/memories/:id?project=<path>` | Delete project memory |

---

## Error Codes

| Code | Message |
|------|---------|
| -32001 | Project not initialized |
| -32005 | No memories found |
| -32006 | Store failed |
