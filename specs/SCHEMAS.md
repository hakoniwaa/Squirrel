# Squirrel Schemas

Database schema for project memories and doc debt. Single database per project.

---

## Database File

| Database | Location | Purpose |
|----------|----------|---------|
| Project DB | `<repo>/.sqrl/memory.db` | Memories + doc debt |

---

## SCHEMA-001: memories

All memories stored in a single table with type field.

```sql
CREATE TABLE memories (
  id           TEXT PRIMARY KEY,          -- UUID
  memory_type  TEXT NOT NULL,             -- 'preference' | 'project' | 'decision' | 'solution'
  content      TEXT NOT NULL,             -- Memory content (1-2 sentences)
  tags         TEXT DEFAULT '[]',         -- JSON array of tags
  use_count    INTEGER DEFAULT 1,         -- Times stored/reinforced
  created_at   TEXT NOT NULL,             -- ISO 8601
  updated_at   TEXT NOT NULL              -- ISO 8601
);

CREATE INDEX idx_memories_type ON memories(memory_type);
CREATE INDEX idx_memories_use_count ON memories(use_count DESC);
```

### Memory Types

| Type | Description | Examples |
|------|-------------|---------|
| `preference` | User's coding style | "No emojis", "Use Gemini 3 Pro" |
| `project` | Project-specific knowledge | "Use httpx not requests" |
| `decision` | Architecture decisions | "Chose PostgreSQL for transactions" |
| `solution` | Problem-solution pairs | "Fixed SSL by switching to httpx" |

### Examples

| memory_type | content | tags | use_count |
|-------------|---------|------|-----------|
| preference | No emojis in code or commits | ["style"] | 5 |
| preference | Use Gemini 3 Pro, not Claude or older models | ["tooling", "llm"] | 3 |
| project | Use httpx as HTTP client, not requests | ["backend", "http"] | 4 |
| decision | Chose SQLite over PostgreSQL for local storage | ["database", "architecture"] | 2 |
| solution | Fixed SSL error by switching from requests to httpx | ["backend", "ssl", "fix"] | 1 |

---

## SCHEMA-002: doc_debt

Tracked documentation debt per commit.

```sql
CREATE TABLE doc_debt (
  id              TEXT PRIMARY KEY,         -- UUID
  commit_sha      TEXT NOT NULL,            -- Git commit SHA
  commit_message  TEXT,                     -- First line of commit message
  code_files      TEXT NOT NULL,            -- JSON array of changed code files
  expected_docs   TEXT NOT NULL,            -- JSON array of docs that should update
  detection_rule  TEXT NOT NULL,            -- 'config' | 'reference' | 'pattern'
  resolved        INTEGER DEFAULT 0,        -- 1 if debt resolved
  resolved_at     TEXT,                     -- ISO 8601 when resolved
  created_at      TEXT NOT NULL             -- ISO 8601
);

CREATE INDEX idx_doc_debt_commit ON doc_debt(commit_sha);
CREATE INDEX idx_doc_debt_resolved ON doc_debt(resolved);
```

### Detection Rules

| Rule | Priority | Description |
|------|----------|-------------|
| config | 1 | User-defined mapping in .sqrl/config.yaml |
| reference | 2 | Code contains spec ID (e.g., SCHEMA-001) |
| pattern | 3 | File pattern match (e.g., *.rs → ARCHITECTURE.md) |

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
| Team schemas | Deferred | Future cloud version |

---

## Migration Notes

### From Old Schema

If migrating from the previous multi-table schema:

| Old Table | Action |
|-----------|--------|
| `user_styles` | Move to `memories` with type "preference" |
| `project_memories` | Move to `memories` with type "project" |
| `categories` | Convert category to tags |
| `extraction_log` | Drop |
| `docs_index` | Drop |
