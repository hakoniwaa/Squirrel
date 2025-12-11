# Squirrel Constitution

Project governance and principles for AI agents working on this codebase.

## Project Identity

- **Name**: Squirrel
- **Purpose**: Local-first memory system for AI coding tools
- **License**: AGPL-3.0

---

## Core Principles

### P1: Future-Impact

**Memory value = regret reduction in future episodes.**

A memory is valuable only if it measurably helps in future sessions - reducing repeated bugs, repeated confusion, or wasted tokens. Not because it came from frustration. Not because the outcome was success/failure. Because it actually helped later.

This is our unique advantage: we have full Claude Code session logs with the complete timeline of what happens AFTER a memory is created. We can measure real future impact. Generic memory systems (mem0, langmem) cannot.

| Old Approach | New Approach |
|--------------|--------------|
| frustration → importance | future usage → value |
| outcome (success/failure) → store | opportunities/regret_hits → promote/deprecate |
| support_count | use_count + opportunities |

### P2: AI-Primary

**The model is the decision-maker, not a form-filler.**

We don't design 20-field schemas for the LLM to fill. We don't write rules like "frustration=severe → importance=critical". We give the model episodes and existing memories, and it decides what to extract, how to phrase it, what operations to perform.

| Our Job | Not Our Job |
|---------|-------------|
| Build minimal framework | Write rules for AI to follow |
| Define schema structure | Decide what to extract |
| Set constraints | Choose phrasing |
| Declare objectives | Assign importance levels |

### P3: Declarative

**We declare objectives and constraints. The model + evaluation loop discover the policy.**

We declare:
- **Objectives:** minimize repeated debugging, minimize re-explaining preferences, avoid re-discovering invariants
- **Constraints:** no secrets, no raw stack traces, favor stable over transient
- **Policy parameters:** promotion/deprecation thresholds in `memory_policy.toml`

We don't declare:
- What to extract from each episode
- How to phrase memories
- When to UPDATE vs ADD
- What kind/tier to assign

---

## System Constraints

| Constraint | Rationale |
|------------|-----------|
| **Local-first** | All user data on their machine by default. No cloud dependency for core functionality. Privacy is non-negotiable. |
| **Passive** | 100% invisible during coding sessions. No prompts, no confirmations, no interruptions. Watch logs silently, learn passively. |
| **Cross-platform** | Support Mac, Linux, Windows. No OS-specific hacks in core code. |
| **No secrets** | Never store API keys, tokens, passwords, or credentials as memories. |
| **No raw logs** | Don't store raw stack traces or full tool outputs. Compress and summarize. |
| **Immediate usability** | New memories must be usable in the next task (no delay for batch processing). |

---

## Architecture Boundaries

| Component | Language | Responsibility | Boundary |
|-----------|----------|----------------|----------|
| Rust Daemon | Rust | Log watching, storage, MCP server, CLI, guard interception | Never contains LLM logic |
| Python Agent | Python | Memory Writer, embeddings, context composition | Never does file watching |
| IPC | JSON-RPC 2.0 | Communication between daemon and agent | Unix socket / named pipe |

---

## Technology Constraints

| Category | Choice | Locked? |
|----------|--------|---------|
| Storage | SQLite + sqlite-vec | Yes (v1) |
| MCP SDK | rmcp (Rust) | Yes (v1) |
| Agent Framework | PydanticAI | Yes (v1) |
| Embeddings | API-based (OpenAI default) | Provider swappable |
| LLM | Strong model for Memory Writer | Provider swappable |

---

## Development Rules

### DR1: Spec IDs Required
Every schema, interface, prompt, and policy must have a stable ID (e.g., `SCHEMA-001`, `POLICY-001`). PRs must reference spec IDs.

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
| `AGENTS.md` | Canonical source (Codex native) |
| `.claude/CLAUDE.md` | Symlink → AGENTS.md |
| `.cursor/rules/*.mdc` | Cursor project rules |

GEMINI.md and .cursorrules are deprecated. Configure Gemini CLI to read AGENTS.md via `contextFileName` setting.
