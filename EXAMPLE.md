# Squirrel: Complete Process Walkthrough

Detailed example demonstrating the entire Squirrel data flow from user coding to personalized AI context.

## Core Concept

Squirrel watches AI tool logs, groups events into **Episodes** (4-hour time windows), and asks the Router Agent to analyze the entire session:

1. **Segment Tasks** - Identify distinct user goals within the episode
2. **Classify Outcomes** - SUCCESS | FAILURE | UNCERTAIN for each task
3. **Extract Memories** - SUCCESS→recipe/project_fact, FAILURE→pitfall, UNCERTAIN→skip

Episode = batch of events from same repo within 4-hour window (internal batching, not a product concept).

**The key insight:** Passive learning requires knowing WHAT succeeded before extracting patterns. We don't ask users to confirm - we infer from conversation flow.

---

## Scenario

Developer "Alice" working on `inventory-api` (FastAPI project).

Alice's coding preferences:
- Type hints everywhere
- pytest with fixtures
- Async/await patterns

---

## Phase 1: Setup

```bash
brew install sqrl
sqrl daemon start
cd ~/projects/inventory-api
sqrl init
```

File structure:
```
~/.sqrl/
├── config.toml           # API keys
├── squirrel.db           # Global SQLite (user_style memories)
└── projects.json         # Registered repos

~/projects/inventory-api/.sqrl/
└── squirrel.db           # Project SQLite (events, memories)
```

---

## Phase 2: Learning (Passive Collection)

### Step 2.1: Alice Codes (Two Tasks in One Session)

```
# Task 1: Add endpoint (SUCCESS)
Alice: "Add a new endpoint to get inventory items by category"
Claude Code: "I'll create a GET endpoint..."
Alice: "Use async def, add type hints, and write a pytest fixture"
Claude Code: [Revises code with async, types, fixture]
Alice: "Perfect, tests pass!"

# Task 2: Fix auth bug (FAILURE then SUCCESS)
Alice: "There's an auth loop bug when tokens expire"
Claude Code: "Let me check localStorage..."
[Error persists]
Alice: "Still broken"
Claude Code: "Let me try checking cookies..."
[Error persists]
Alice: "That didn't work either"
Claude Code: "I think the issue is in useEffect cleanup..."
[Implements fix]
Alice: "That fixed it, thanks!"
```

### Step 2.2: Rust Daemon Watches Logs

Daemon watches log files from all supported CLIs:
```
~/.claude/projects/**/*.jsonl      # Claude Code
~/.codex-cli/logs/**/*.jsonl       # Codex CLI
~/.gemini/logs/**/*.jsonl          # Gemini CLI
```

Parses into normalized Events:

```rust
let event = Event {
    id: "evt_001",
    repo: "/Users/alice/projects/inventory-api",
    kind: "user",           // user | assistant | tool | system
    content: "Use async def, add type hints...",
    file_paths: vec![],
    ts: "2025-11-25T10:01:00Z",
    processed: false,
};
storage.save_event(event)?;
```

**Note:** We don't track which CLI the event came from - all events are normalized to the same schema.

### Step 2.3: Episode Batching

Episodes are created by **4-hour time windows** OR **50 events max** (whichever comes first):

```rust
fn should_flush_episode(buffer: &EventBuffer) -> bool {
    let window_hours = 4;
    let max_events = 50;

    buffer.events.len() >= max_events ||
    buffer.oldest_event_age() >= Duration::hours(window_hours)
}

// Flush triggers IPC call to Python
fn flush_episode(repo: &str, events: Vec<Event>) {
    let episode = Episode {
        id: generate_uuid(),
        repo: repo.to_string(),
        start_ts: events.first().ts,
        end_ts: events.last().ts,
        events: events,
    };

    ipc_client.send(json!({
        "method": "router_agent",
        "params": {
            "mode": "ingest",
            "payload": { "episode": episode }
        },
        "id": 1
    }));
}
```

---

## Phase 3: Memory Extraction (Python Service)

### Step 3.1: Router Agent INGEST Mode (Success Detection)

The LLM analyzes the entire Episode in ONE call - segmenting tasks, classifying outcomes, and extracting memories:

```python
async def ingest_mode(payload: dict) -> dict:
    episode = payload["episode"]

    # Build context from events
    context = "\n".join([
        f"[{e['kind']}] {e['content']}"
        for e in episode["events"]
    ])

    # LLM analyzes: tasks, outcomes, and memories in ONE call
    response = await llm.call(INGEST_PROMPT.format(context=context))

    return {
        "tasks": [
            {
                "task": "Add category endpoint",
                "outcome": "SUCCESS",
                "evidence": "User said 'Perfect, tests pass!'",
                "memories": [
                    {
                        "type": "user_style",
                        "content": "Prefers async/await with type hints for all handlers",
                        "importance": "high",
                        "repo": "global",
                    }
                ]
            },
            {
                "task": "Fix auth loop bug",
                "outcome": "SUCCESS",  # Eventually succeeded after failures
                "evidence": "User said 'That fixed it, thanks!'",
                "memories": [
                    {
                        "type": "pitfall",
                        "content": "Auth token refresh loops are NOT caused by localStorage or cookies - check useEffect cleanup first",
                        "importance": "high",
                        "repo": "/Users/alice/projects/inventory-api",
                    },
                    {
                        "type": "recipe",
                        "content": "For auth redirect loops, fix useEffect cleanup to prevent re-triggering on token refresh",
                        "importance": "high",
                        "repo": "/Users/alice/projects/inventory-api",
                    }
                ]
            }
        ],
        "confidence": 0.9
    }
```

INGEST Prompt:
```
Analyze this coding session (~4 hours of activity):

[user] Add a new endpoint to get inventory items by category
[assistant] I'll create a GET endpoint...
[user] Use async def, add type hints, and write a pytest fixture
[assistant] [Revises code with async, types, fixture]
[user] Perfect, tests pass!
[user] There's an auth loop bug when tokens expire
[assistant] Let me check localStorage...
[user] Still broken
[assistant] Let me try checking cookies...
[user] That didn't work either
[assistant] I think the issue is in useEffect cleanup...
[user] That fixed it, thanks!

Analyze this session:
1. Identify distinct Tasks (user goals like "add endpoint", "fix bug")
2. For each Task, determine:
   - outcome: SUCCESS | FAILURE | UNCERTAIN
   - evidence: why you classified it this way (quote user if possible)
3. For SUCCESS tasks: extract recipe (reusable pattern) or project_fact memories
4. For FAILURE tasks: extract pitfall memories (what NOT to do)
5. For tasks with failed attempts before success: extract BOTH pitfall AND recipe

Return only high-confidence memories. When in doubt, skip.
```

### Step 3.2: UUID→Integer Mapping for LLM

When showing existing memories to LLM for dedup, map UUIDs to simple integers to prevent hallucination:

```python
def prepare_memories_for_llm(memories: list[Memory]) -> tuple[list[dict], dict[str, str]]:
    """LLMs can hallucinate UUIDs. Use simple integers instead."""
    uuid_mapping = {}
    prepared = []
    for idx, memory in enumerate(memories):
        uuid_mapping[str(idx)] = memory.id  # "0" -> "uuid-xxx-xxx"
        prepared.append({"id": str(idx), "content": memory.content})
    return prepared, uuid_mapping

# After LLM response, map back to real UUIDs
def restore_memory_ids(llm_response, uuid_mapping):
    for item in llm_response:
        if item.get("id") in uuid_mapping:
            item["id"] = uuid_mapping[item["id"]]
    return llm_response
```

### Step 3.3: Near-Duplicate Check + Save Memory

If confidence >= 0.7 and action is ADD:

```python
# Before saving, check for near-duplicates
candidates = await retrieve_candidates(
    repo=memory.repo,
    task=memory.content,
    memory_types=[memory.memory_type],
    top_k=5
)
for candidate in candidates:
    if candidate.similarity >= 0.9:
        # Near-duplicate found - LLM decides merge or skip
        return await merge_or_skip(memory, candidate)
```

If no duplicate found:

```rust
let memory = Memory {
    id: generate_uuid(),
    content_hash: hash(&content),
    content: "Prefers async/await with type hints for all handlers",
    memory_type: "user_style",
    repo: "global",               // 'global' for user-level memories
    embedding: embed(&content),   // 384-dim ONNX
    confidence: 0.85,
    importance: "high",           // LLM-assigned importance
    state: "active",              // active | deleted (soft-delete)
    user_id: "local",
    assistant_id: "squirrel",
    created_at: now(),
    updated_at: now(),
    deleted_at: None,             // NULL unless state='deleted'
};
storage.save_memory(memory)?;

// Log to history table for audit trail
storage.log_history(HistoryEntry {
    memory_id: memory.id,
    old_content: None,            // NULL for ADD
    new_content: memory.content,
    event: "ADD",
    created_at: now(),
});
```

---

## Phase 4: Context Retrieval

### Step 4.1: MCP Tool Call

```json
{
  "tool": "squirrel_get_task_context",
  "arguments": {
    "project_root": "/Users/alice/projects/inventory-api",
    "task": "Add a delete endpoint for inventory items",
    "context_budget_tokens": 400
  }
}
```

### Step 4.2: Router Agent ROUTE Mode

```python
async def route_mode(payload: dict) -> dict:
    task = payload["task"]
    candidates = payload["candidates"]
    budget = payload["context_budget_tokens"]

    # v1: Heuristic scoring (no LLM call)
    # score = w_sim * similarity + w_imp * importance_weight + w_rec * recency
    # importance_weight: critical=1.0, high=0.75, medium=0.5, low=0.25
    scored = score_candidates(candidates, task)
    selected = select_within_budget(scored, budget)

    # Log access for debugging retrieval behavior
    for memory in selected:
        await log_memory_access(
            memory_id=memory.id,
            access_type="get_context",
            query=task,
            score=memory.score,
            metadata={"budget": budget, "selected_count": len(selected)}
        )

    return {
        "memories": [
            {
                "type": "user_style",
                "content": "Prefers async/await with type hints",
                "importance": "high",
                "why": "Relevant because you're adding an HTTP endpoint"
            }
        ],
        "tokens_used": 120
    }
```

### Step 4.3: Response

```json
{
  "task": "Add a delete endpoint for inventory items",
  "memories": [
    {
      "type": "user_style",
      "content": "Prefers async/await with type hints for all handlers",
      "importance": "high",
      "why": "Relevant because you're adding an HTTP endpoint"
    },
    {
      "type": "project_fact",
      "content": "Uses FastAPI with Pydantic models",
      "importance": "medium",
      "why": "Relevant because delete endpoint needs proper response model"
    }
  ],
  "tokens_used": 156
}
```

---

## Data Schema

### Event (normalized from all CLIs)

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    repo TEXT NOT NULL,
    kind TEXT NOT NULL,        -- user | assistant | tool | system
    content TEXT NOT NULL,
    file_paths TEXT,           -- JSON array
    ts TEXT NOT NULL,
    processed INTEGER DEFAULT 0
);
```

### Memory

```sql
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,        -- user_style | project_fact | pitfall | recipe
    repo TEXT NOT NULL,               -- repo path OR 'global' for user-level memories
    embedding BLOB,                   -- 384-dim float32
    confidence REAL NOT NULL,
    importance TEXT NOT NULL DEFAULT 'medium',  -- critical | high | medium | low
    state TEXT NOT NULL DEFAULT 'active',       -- active | deleted (soft-delete)
    user_id TEXT NOT NULL DEFAULT 'local',
    assistant_id TEXT NOT NULL DEFAULT 'squirrel',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT                             -- NULL unless state='deleted'
);
```

### Memory History (audit trail)

```sql
CREATE TABLE memory_history (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    old_content TEXT,          -- Previous content (NULL for ADD)
    new_content TEXT NOT NULL, -- New content
    event TEXT NOT NULL,       -- ADD | UPDATE | DELETE
    created_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);
```

### Memory Access Log (debugging retrieval)

```sql
CREATE TABLE memory_access_log (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    access_type TEXT NOT NULL,  -- search | get_context | list
    query TEXT,                 -- The query that triggered access
    score REAL,                 -- Similarity score at access time
    metadata TEXT,              -- JSON: additional debug info
    accessed_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);
```

---

## Summary

| Phase | What Happens |
|-------|--------------|
| Setup | `sqrl init` registers project |
| Learning | Daemon watches CLI logs, parses to Events |
| Batching | Groups events into Episodes (4-hour window OR 50 events) |
| **Success Detection** | LLM segments Tasks, classifies SUCCESS/FAILURE/UNCERTAIN |
| Extraction | SUCCESS→recipe/project_fact, FAILURE→pitfall, UNCERTAIN→skip |
| Dedup | Near-duplicate check (0.9 similarity) before ADD |
| Retrieval | MCP tool → ROUTE mode scores by similarity+importance+recency → select within token budget |

### Why Success Detection Matters

Without success detection, we'd blindly store patterns without knowing if they worked:
- User tries 5 approaches, only #5 works
- Old approach: Store all 5 as "patterns" (4 are wrong!)
- With success detection: Store #1-4 as pitfalls, #5 as recipe

This is the core insight from analyzing claude-cache: passive learning REQUIRES outcome classification.

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Episode trigger | 4-hour window OR 50 events | Balance context vs LLM cost |
| **Success detection** | LLM classifies outcomes | Core insight for passive learning |
| **Task segmentation** | LLM decides, no rules engine | Simple, semantic understanding |
| **Memory extraction** | Outcome-based (SUCCESS→recipe, FAILURE→pitfall) | Learn from both success and failure |
| Session tracking | None | Simpler, CLI-agnostic |
| Event schema | Normalized (no CLI field) | All CLIs treated equally |
| Episode storage | Not stored | Just internal batching |
| User-level memories | repo='global' | Simpler than separate flag |
| Importance levels | critical/high/medium/low | Prioritize memories in retrieval |
| Near-duplicate threshold | 0.9 similarity | Avoid redundant memories |
| ROUTE mode (v1) | Heuristic scoring | Fast, no LLM call needed |
| UUID→integer mapping | Map before LLM, restore after | Prevents LLM hallucinating UUIDs |
| Memory deletion | Soft-delete (state column) | Recoverable, audit trail |
| History tracking | old/new content per change | Debug, rollback capability |
| Access logging | Log every retrieval | Debug why memories surface |
| **100% passive** | No user prompts or confirmations | Invisible during use |
