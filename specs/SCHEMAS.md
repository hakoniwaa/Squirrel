# Squirrel Schemas

Database schemas for memories. Two databases: global and project.

---

## Database Files

| Database | Location | Purpose |
|----------|----------|---------|
| Global DB | `~/.sqrl/memory.db` | User preferences (apply to all projects) |
| Project DB | `<repo>/.sqrl/memory.db` | Project-specific memories |

---

## SCHEMA-001: memories

Same schema for both global and project databases.

```sql
CREATE TABLE memories (
  id           TEXT PRIMARY KEY,          -- UUID
  content      TEXT NOT NULL,             -- Actionable instruction (1-2 sentences)
  tags         TEXT DEFAULT '[]',         -- JSON array of tags
  use_count    INTEGER DEFAULT 1,         -- Times stored/reinforced
  created_at   TEXT NOT NULL,             -- ISO 8601
  updated_at   TEXT NOT NULL              -- ISO 8601
);

CREATE INDEX idx_memories_use_count ON memories(use_count DESC);
```

---

## Memory Types

| Type | Storage | When to store | Example |
|------|---------|---------------|---------|
| `preference` | `~/.sqrl/memory.db` | User corrects AI behavior (applies everywhere) | "Don't use emojis in code or commits" |
| `project` | `.sqrl/memory.db` | Project-specific rule | "Use httpx not requests in this project" |

**Don't store:** research in progress, general knowledge, conversation context.

### Examples

**Global preferences (~/.sqrl/memory.db):**
| content | tags | use_count |
|---------|------|-----------|
| Don't use emojis in code or commits | ["style"] | 5 |
| Prefer async/await over callbacks | ["style", "js"] | 3 |

**Project memories (.sqrl/memory.db):**
| content | tags | use_count |
|---------|------|-----------|
| Use httpx not requests in this project | ["backend", "http"] | 4 |
| PostgreSQL 16 for database | ["database"] | 2 |

---

## use_count Semantics

| Event | Action |
|-------|--------|
| CLI stores new memory | use_count = 1 |
| CLI stores duplicate/similar memory | use_count++ on existing |
| MCP get_memory returns memory | No change (read-only) |

**Ordering:** Memories with higher use_count appear first in MCP responses.
