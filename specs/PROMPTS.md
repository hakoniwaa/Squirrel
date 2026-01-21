# Squirrel Prompts

All LLM prompts with stable IDs and model tier assignments.

## Model Configuration

Squirrel uses Gemini 3.0 Flash for both stages. Configured via LiteLLM.

| Stage | Default Model |
|-------|---------------|
| User Scanner | `gemini/gemini-3.0-flash` |
| Memory Extractor | `gemini/gemini-3.0-flash` |

**Configuration:** Users can override via `SQRL_CHEAP_MODEL` and `SQRL_STRONG_MODEL` environment variables.

**No embedding model** - v1 uses simple use_count ordering, no semantic search.

---

## PROMPT-001: User Scanner

**Model:** `gemini/gemini-3.0-flash` (configurable via `SQRL_CHEAP_MODEL`)

**ID:** PROMPT-001-USER-SCANNER

**Purpose:** Scan user messages only (no AI messages) to detect if any message indicates a correction or preference worth remembering.

**Core Insight:** Only process user messages first (minimal tokens). If correction detected, pull AI context later.

**Input Variables:**

| Variable | Type | Description |
|----------|------|-------------|
| user_messages | array | List of user messages only (no AI responses) |

**System Prompt:**
```
You scan user messages to detect corrections or preferences.

Look for signals like corrections, frustration, or preference statements.

Skip messages that are just acknowledgments ("ok", "sure", "continue", "looks good").

Output JSON only:
{"needs_context": true, "trigger_index": 1}
or
{"needs_context": false, "trigger_index": null}
```

**User Prompt Template:**
```
USER MESSAGES:
{user_messages}

Does any message indicate a correction or preference? Return JSON only.
```

---

## PROMPT-002: Memory Extractor

**Model:** `gemini/gemini-3.0-flash` (configurable via `SQRL_STRONG_MODEL`)

**ID:** PROMPT-002-MEMORY-EXTRACTOR

**Purpose:** Extract memories from user corrections. Distinguish between global preferences and project-specific AI mistakes.

**Core Insight:** All memories come from user corrections. The question is: is this a global preference or a project-specific issue?

**Input Variables:**

| Variable | Type | Description |
|----------|------|-------------|
| trigger_message | string | The user message that triggered (from User Scanner) |
| ai_context | string | The 3 AI turns before the trigger message |
| project_id | string | Project identifier |
| project_root | string | Absolute path to project |
| existing_user_styles | array | Current user style items |
| existing_project_memories | array | Current project memories by category |

**AI Turn Definition:** One AI turn = all content between two user messages (AI responses + tool calls + tool results).

**System Prompt:**
```
Extract memories from user corrections. Output JSON only.

User Style = global preference (all projects)
Project Memory = this project only

Example output:
{"user_styles": [{"op": "ADD", "text": "never use emoji"}], "project_memories": []}

Another example:
{"user_styles": [], "project_memories": [{"op": "ADD", "category": "backend", "text": "use httpx"}]}

Rules:
- Each item MUST be an object with "op" and "text" fields
- op: "ADD", "UPDATE", or "DELETE"
- category (project only): "frontend", "backend", "docs_test", "other"
- Return empty arrays if not worth remembering
```

**User Prompt Template:**
```
PROJECT: {project_id}

EXISTING USER STYLES: {existing_user_styles}
EXISTING PROJECT MEMORIES: {existing_project_memories}

AI CONTEXT:
{ai_context}

USER MESSAGE:
{trigger_message}
```

---

## Token Budgets

| Prompt ID | Max Input | Max Output |
|-----------|-----------|------------|
| PROMPT-001 (User Scanner) | 4000 | 200 |
| PROMPT-002 (Memory Extractor) | 8000 | 2000 |

---

## Error Handling

All prompts must handle:

| Error | Action |
|-------|--------|
| Rate limit | Exponential backoff, max 3 retries |
| Invalid JSON | Re-prompt with stricter format instruction |
| Timeout | Log, return empty result, don't block |
| Content filter | Log, skip memory, continue |

---

## Deprecated Prompts

| Old Prompt | Status |
|------------|--------|
| PROMPT-001-LOG-CLEANER | Replaced by PROMPT-001-USER-SCANNER |
| PROMPT-001-MEMORY-WRITER | Replaced by PROMPT-001 + PROMPT-002 pipeline |
| PROMPT-002-COMPOSE | Removed |
| PROMPT-003-CONFLICT | Removed |
| PROMPT-004-CLI | Removed |
| PROMPT-005-PREFERENCE | Removed |
