# Squirrel Key Conventions

Non-binding suggestions for declarative keys. Memory Writer may use these or define new ones.

## Purpose

Keys enable fast deterministic lookup and conflict resolution:
- Same key + different value → UPDATE operation (Memory Writer decides)
- Fast path retrieval without embedding search

**Note:** This is a convention registry, not a rule engine. Memory Writer is free to use any keys it deems appropriate.

## Key Format

```
<scope>.<category>.<property>
```

- **scope**: `project` or `user`
- **category**: domain grouping (db, api, http, pref, etc.)
- **property**: specific attribute

---

## Recommended Invariant Keys (project.*)

For kind='invariant' memories. Stored with project_id set.

| Key | Description | Example Values |
|-----|-------------|----------------|
| `project.db.engine` | Database engine | PostgreSQL, MySQL, SQLite, MongoDB |
| `project.db.version` | Database version | 15, 8.0, 3.x |
| `project.db.orm` | ORM/query builder | Prisma, SQLAlchemy, TypeORM, Diesel |
| `project.api.framework` | API framework | FastAPI, Express, Rails, Actix |
| `project.ui.framework` | UI framework | React, Vue, Svelte, None |
| `project.language.main` | Primary language | Python, TypeScript, Rust, Go |
| `project.language.version` | Language version | 3.12, 5.0, 1.75 |
| `project.test.framework` | Test framework | pytest, jest, cargo test |
| `project.test.command` | Test run command | `pytest`, `npm test`, `cargo test` |
| `project.build.command` | Build command | `npm run build`, `cargo build` |
| `project.auth.method` | Auth mechanism | JWT, session, OAuth, API key |
| `project.package_manager` | Package manager | npm, pnpm, yarn, pip, uv, cargo |
| `project.deploy.platform` | Deploy target | Vercel, AWS, Railway, self-hosted |
| `project.ci.platform` | CI system | GitHub Actions, GitLab CI, CircleCI |
| `project.http.client` | HTTP client library | httpx, requests, axios, reqwest |

---

## Recommended Preference Keys (user.*)

For kind='preference' memories. Stored with project_id=NULL in global db.

| Key | Description | Example Values |
|-----|-------------|----------------|
| `user.pref.async_style` | Async pattern preference | async_await, callbacks, sync |
| `user.pref.language` | Favorite language | Python, TypeScript, Rust |
| `user.pref.null_handling` | Null handling style | strict, permissive |
| `user.pref.comment_style` | Comment preference | minimal, detailed, jsdoc |
| `user.pref.error_handling` | Error pattern | exceptions, result_types, errors |
| `user.pref.test_style` | Testing approach | tdd, after_impl, minimal |
| `user.pref.naming_convention` | Naming style | snake_case, camelCase |
| `user.pref.explanation_style` | Explanation verbosity | concise, detailed, step_by_step |
| `user.pref.ask_when_uncertain` | Confirmation preference | always, sometimes, never |

---

## Key Uniqueness Convention

For any `(project_id, owner_type, owner_id, key)` tuple:
- At most one active invariant/preference is expected at a time
- When Memory Writer decides to change a keyed memory, it should output an UPDATE op
- Commit layer marks previous memories with same key as status='deprecated'

**Example:**
```
Existing: project.http.client = "requests"
New info: httpx works better

Memory Writer outputs:
{
  "op": "UPDATE",
  "target_memory_id": "mem-old-123",
  "key": "project.http.client",
  "text": "The standard HTTP client is httpx.",
  ...
}

Commit layer:
1. Mark mem-old-123 as status='deprecated'
2. Insert new memory with key="project.http.client"
```

---

## Fast Path Retrieval

Keyed memories support direct lookup without embedding search:

```sql
SELECT * FROM memories
WHERE key = 'project.http.client'
  AND project_id = ?
  AND owner_type = ?
  AND owner_id = ?
  AND status IN ('provisional', 'active')
ORDER BY created_at DESC
LIMIT 1
```

Use this for environment queries before falling back to vector search.

---

## Deprecated Sections

The following sections from the old KEYS.md are no longer applicable:

| Old Section | Status |
|-------------|--------|
| Promotion Rules | Removed - CR-Memory handles promotion via memory_policy.toml |
| Conflict Resolution Rules | Removed - Memory Writer handles conflicts |
| KEY-P-* / KEY-U-* IDs | Removed - Keys are suggestions, not enforced registry |

---

## Adding New Keys

Memory Writer is free to create new keys. Recommended conventions:

| Pattern | Use For |
|---------|---------|
| `project.<domain>.<property>` | Project-scoped invariants |
| `user.pref.<property>` | User preferences |
| `user.style.<property>` | Coding style preferences |

When creating new keys:
- Use lowercase with underscores for multi-word properties
- Be specific enough to avoid collisions
- Be general enough to be reusable
