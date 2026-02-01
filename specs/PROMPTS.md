# Squirrel Prompts

**Status: Deprecated (ADR-021)**

Squirrel no longer makes LLM calls. All intelligence comes from the CLI AI.

All prompts in this file are historical. They were used when Squirrel had a Python Memory Service with Gemini models.

---

## Current Architecture

CLI AI (Claude, Cursor, etc.) decides what to remember. Squirrel just stores and retrieves.

| Component | LLM? | Role |
|-----------|-------|------|
| Squirrel | No | Storage + git hooks |
| CLI AI | Yes | Memory decisions, doc updates |

---

## Deprecated Prompts

All prompts below were removed in ADR-021.

| Prompt ID | Was Used For | Status |
|-----------|-------------|--------|
| PROMPT-001 (User Scanner) | Scan user messages for patterns | Removed |
| PROMPT-002 (Memory Extractor) | Extract memories from flagged messages | Removed |
| PROMPT-003 (Project Summarizer) | Summarize project README | Removed |
| PROMPT-004 (Doc Summarizer) | Summarize doc files | Removed |

---

## CLI-Side Prompts

These are not Squirrel prompts. They are instructions embedded in CLAUDE.md and Skill files that tell the CLI AI how to interact with Squirrel.

See INTERFACES.md:
- **TRIGGER-001**: CLAUDE.md memory storage instructions
- **SKILL-001**: Session start skill file
