# Squirrel Project

Local-first memory system for AI coding tools.

## Architecture

Single Rust binary (`sqrl`). No daemon, no Python, no LLM calls.

```
CLI AI (Claude Code, Cursor, etc.)
    │ MCP
    ▼
sqrl binary (Rust)
    │
    ▼
SQLite (.sqrl/memory.db)
```

| Component | Responsibility | Never Does |
|-----------|----------------|------------|
| sqrl binary | MCP server, CLI, git hooks, SQLite | LLM calls, file watching, daemon |
| CLI AI | Decides what to store, fixes doc debt | Direct DB access |

## Spec-Driven Development

Specs are source of truth. Code is compiled output.

| Spec File | Purpose |
|-----------|---------|
| specs/CONSTITUTION.md | Project governance, core principles |
| specs/ARCHITECTURE.md | System boundaries, data flow |
| specs/SCHEMAS.md | Database schemas (SCHEMA-*) |
| specs/INTERFACES.md | MCP, CLI contracts (MCP-*, CLI-*) |
| specs/DECISIONS.md | Architecture decision records (ADR-*) |

**Rules:**
1. Read specs before implementing
2. Never implement behavior not defined in specs
3. Update specs before or with code, never after
4. Reference spec IDs in commits

## AI Workflow

| Phase | Action | Output |
|-------|--------|--------|
| 1. Specify | Define WHAT and WHY | `specs/*.md` updated |
| 2. Clarify | Ask questions, resolve ambiguities | Ambiguities resolved |
| 3. Plan | Define HOW | Implementation plan |
| 4. Tasks | Break into ordered steps | Task list |
| 5. Implement | Execute one task at a time | Working code |

## Stop and Discuss

Do NOT decide these on your own:
- Model selection (which LLM to use)
- Numeric values (thresholds, limits, timeouts)
- Prompts (system prompts, extraction prompts)
- Any non-trivial design decisions

## Development Environment

Uses Nix via devenv (ADR-006):

```bash
devenv shell
```

## Team Standards

- English only in code, comments, commits
- No emojis in documentation
- Brief, direct language
- Tables over paragraphs
- Branch: `yourname/type-description`
- Commit: `type(scope): brief description`
- Keep files under 200 lines
- Only change what's necessary (DR5)
- Write tests for new features (DR4)

## Doc Review

When you push, Squirrel's pre-push hook shows you what files changed and lists doc files in the repo. Review the changes and decide if any docs need updating. Update them before the push completes.

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
