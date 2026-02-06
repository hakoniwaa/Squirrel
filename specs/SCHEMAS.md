# Squirrel Schemas

Database schema for project memories. Single database per project.

---

## Database File

| Database | Location | Purpose |
|----------|----------|---------|
| Project DB | `<repo>/.sqrl/memory.db` | Memories (behavioral corrections) |

---

## SCHEMA-001: memories

All memories stored in a single table with type field.

```sql
CREATE TABLE memories (
  id           TEXT PRIMARY KEY,          -- UUID
  memory_type  TEXT NOT NULL,             -- 'preference' | 'project' | 'decision' | 'solution'
  content      TEXT NOT NULL,             -- Actionable instruction (1-2 sentences)
  tags         TEXT DEFAULT '[]',         -- JSON array of tags
  use_count    INTEGER DEFAULT 1,         -- Times stored/reinforced
  created_at   TEXT NOT NULL,             -- ISO 8601
  updated_at   TEXT NOT NULL              -- ISO 8601
);

CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_use_count ON memories(use_count DESC);
```

### Memory Types

Memories are behavioral corrections — things that change how the AI acts next time. Every memory should be an actionable instruction.

| Type | When to store | Example |
|------|---------------|---------|
| `preference` | User corrects AI behavior | "Don't use emojis in code or commits" |
| `project` | AI learns a project-specific rule | "Use httpx not requests in this project" |
| `decision` | A choice constrains future behavior | "We chose SQLite, don't suggest Postgres" |
| `solution` | AI hits an error and finds the fix | "SSL error with requests? Switch to httpx" |

**Don't store:** research in progress, general knowledge, conversation context, anything that doesn't change AI behavior.

### Examples

| memory_type | content | tags | use_count |
|-------------|---------|------|-----------|
| preference | Don't use emojis in code or commits | ["style"] | 5 |
| preference | Use Gemini 3 Pro, don't suggest Claude or older models | ["tooling", "llm"] | 3 |
| project | Use httpx not requests in this project | ["backend", "http"] | 4 |
| decision | We chose SQLite for local storage, don't suggest Postgres | ["database", "architecture"] | 2 |
| solution | SSL error with requests? Switch to httpx | ["backend", "ssl", "fix"] | 1 |

---

## use_count Semantics

The `use_count` field tracks how many times a memory has been stored or reinforced.

| Event | Action |
|-------|--------|
| CLI stores new memory | use_count = 1 |
| CLI stores duplicate/similar memory | use_count++ on existing |
| MCP get_memory returns memory | No change (read-only) |

**Ordering:** Memories with higher use_count appear first in MCP responses.

---

## What Was Removed (ADR-021)

| Old Schema | Status | Reason |
|------------|--------|--------|
| SCHEMA-001: user_styles | Merged | Now `memories` with type "preference" |
| SCHEMA-002: project_memories | Merged | Now `memories` with type "project" |
| SCHEMA-003: categories | Removed | Tags replace categories |
| SCHEMA-004: extraction_log | Removed | No extraction pipeline |
| SCHEMA-005: docs_index | Removed | No LLM doc summaries |
| SCHEMA-002: doc_debt | Removed | AI decides doc updates, no tracking needed |
| Team schemas | Deferred | Future cloud version |
