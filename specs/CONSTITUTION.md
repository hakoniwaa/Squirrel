# Squirrel Constitution

Project governance and principles for AI agents working on this codebase.

## Project Identity

- **Name**: Squirrel
- **Purpose**: Local-first memory system for AI coding tools
- **License**: AGPL-3.0

---

## Core Principles

### P1: Simple

**Simple use_count based ordering. No complex evaluation loops.**

Memories are ranked by how often they've been extracted or reinforced. Higher use_count = more important. No regret calculation, no opportunity tracking, no complex promotion/deprecation logic.

| Aspect | Our Approach |
|--------|--------------|
| Ranking | use_count DESC |
| New memory | use_count = 1 |
| Reinforced | use_count++ |
| Garbage collection | use_count = 0 AND age > threshold |

### P2: CLI-Driven

**CLI AI decides what to remember. Squirrel just stores.**

Squirrel has no AI. The CLI (Claude Code, Cursor, etc.) has full conversation context and decides what's worth storing. Squirrel provides MCP tools for storage and retrieval.

| Squirrel's Job | CLI's Job |
|----------------|-----------|
| Store memories | Decide what to store |
| Return memories | Decide when to retrieve |
| Track doc debt | Fix doc debt |
| Install git hooks | Follow CLAUDE.md instructions |

### P3: Invisible

**Zero runtime overhead during coding sessions.**

No daemon, no log watching, no background processing. Squirrel only runs when called (MCP request, CLI command, git hook).

### P4: Distributed-First

**All extraction happens locally. No central server required for core functionality.**

Each developer's machine is the source of truth. Cloud features (team sync) are optional B2B add-ons.

### P5: Doc Aware

**Squirrel tracks project documentation, making it discoverable to AI tools.**

AI tools often forget project docs exist or which docs to update. Squirrel:
- Indexes docs with summaries
- Exposes doc tree via MCP
- Tracks doc debt (stale docs)
- Uses deterministic detection (config > references > patterns)

---

## System Constraints

| Constraint | Rationale |
|------------|-----------|
| **Local-first** | All user data on their machine by default. No cloud dependency for core functionality. Privacy is non-negotiable. |
| **No AI in Squirrel** | Squirrel makes zero LLM calls. All intelligence comes from CLI AI. |
| **Cross-platform** | Support Mac, Linux, Windows. No OS-specific hacks in core code. |
| **No secrets** | Never store API keys, tokens, passwords, or credentials as memories. |
| **No daemon** | No persistent background process. Only runs when called. |

---

## Architecture Boundaries

| Component | Language | Responsibility | Boundary |
|-----------|----------|----------------|----------|
| Squirrel (`sqrl`) | Rust | MCP server, CLI, git hooks, SQLite storage | No LLM, no daemon, no network |

---

## Technology Constraints

| Category | Choice | Locked? |
|----------|--------|---------|
| Language | Rust | Yes (v1) |
| Storage | SQLite | Yes (v1) |
| MCP SDK | rmcp (Rust) | Yes (v1) |
| CLI | clap | Yes (v1) |
| Build | cargo-dist | Yes (v1) |

---

## Development Rules

### DR1: Spec IDs Required
Every schema, interface, prompt, and policy must have a stable ID (e.g., `SCHEMA-001`, `IPC-001`). PRs must reference spec IDs.

### DR2: No Implicit Behavior
If behavior isn't in specs, it doesn't exist. No "obvious" defaults. Document everything.

### DR3: Environment via devenv
All tools managed by devenv.nix. No global installs. `devenv shell` is the only setup command.

### DR4: Test Before Merge
All code changes require passing tests. No exceptions.

### DR5: Minimal Changes
Only change what's necessary. No drive-by refactoring. No "while I'm here" improvements.

### DR6: Spec-Driven Development
Specs are source of truth. Code is generated output. Never introduce behavior not defined in specs. Update specs before or with code, never after.

### DR7: Docs Always Current
Keep all documentation up-to-date at every moment. When code changes, update related docs in the same commit. Never leave docs stale.

### DR8: Clean Up Test Artifacts
Promptly clean up test files after use. Remove temporary test data, mock files, and debug outputs.

### DR9: Small Commits, Concise English
Use small, atomic commits. Each commit should do one thing. Commit messages must be concise English. Format: `type(scope): brief description`.

---

## Decision Authority

| Decision Type | Authority |
|---------------|-----------|
| Spec changes | Team consensus (PR approval) |
| Architecture changes | Documented in DECISIONS.md first |
| Dependency additions | Must justify in PR |
| Breaking changes | Major version bump required |

---

## Communication Style

- English only in code, comments, commits, specs
- No emojis in documentation
- Brief, direct language
- Tables over paragraphs

---

## Agent Instruction Files

Single source of truth for AI tool instructions:

| File | Purpose |
|------|---------|
| `.claude/CLAUDE.md` | Claude Code project rules |
| `.cursor/rules/*.mdc` | Cursor project rules |

Squirrel manages a block in these files for user style (see INTERFACES.md for format).
