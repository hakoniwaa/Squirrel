# Squirrel: Complete Process Walkthrough

Detailed example demonstrating the entire Squirrel data flow from user coding to personalized AI context.

## Core Concept

Squirrel watches AI tool logs, groups events into **Episodes** (4-hour time windows), and asks the Router Agent: "What stable patterns can we learn?"

Episode = batch of events from same repo within 4-hour window (internal batching, not a product concept).

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

### Step 2.1: Alice Codes

```
Alice: "Add a new endpoint to get inventory items by category"
Claude Code: "I'll create a GET endpoint..."
Alice: "Use async def, add type hints, and write a pytest fixture"
Claude Code: [Revises code with async, types, fixture]
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

### Step 3.1: Router Agent INGEST Mode

```python
async def ingest_mode(payload: dict) -> dict:
    episode = payload["episode"]

    # Build context from events
    context = "\n".join([
        f"[{e['kind']}] {e['content']}"
        for e in episode["events"]
    ])

    # LLM decides: is there a memorable pattern?
    response = await llm.call(INGEST_PROMPT.format(context=context))

    return {
        "action": "ADD",  # ADD | UPDATE | NOOP
        "memories": [
            {
                "type": "user_style",
                "content": "Prefers async/await with type hints for all handlers",
            }
        ],
        "confidence": 0.85
    }
```

INGEST Prompt:
```
Analyze this coding activity. Extract stable patterns worth remembering.

Activity:
[user] Add a new endpoint to get inventory items by category
[assistant] I'll create a GET endpoint...
[user] Use async def, add type hints, and write a pytest fixture

Decide:
- Is there a memorable pattern? (user_style, project_fact, pitfall, recipe)
- Does it duplicate existing memory?

Return: {action: ADD|UPDATE|NOOP, memories: [{type, content}], confidence: 0.0-1.0}
```

### Step 3.2: Save Memory

If confidence >= 0.7 and action is ADD/UPDATE:

```rust
let memory = Memory {
    id: generate_uuid(),
    content_hash: hash(&content),
    content: "Prefers async/await with type hints for all handlers",
    memory_type: "user_style",
    repo: "/Users/alice/projects/inventory-api",
    embedding: embed(&content),  // 384-dim ONNX
    confidence: 0.85,
    created_at: now(),
    updated_at: now(),
};
storage.save_memory(memory)?;
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
    "max_tokens": 400
  }
}
```

### Step 4.2: Router Agent ROUTE Mode

```python
async def route_mode(payload: dict) -> dict:
    task = payload["task"]
    candidates = payload["candidates"]

    # LLM selects relevant memories and generates "why"
    response = await llm.call(ROUTE_PROMPT.format(
        task=task,
        candidates=format_candidates(candidates)
    ))

    return {
        "memories": [
            {
                "type": "user_style",
                "content": "Prefers async/await with type hints",
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
      "why": "Relevant because you're adding an HTTP endpoint"
    },
    {
      "type": "project_fact",
      "content": "Uses FastAPI with Pydantic models",
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
    memory_type TEXT NOT NULL,  -- user_style | project_fact | pitfall | recipe
    repo TEXT NOT NULL,
    embedding BLOB,             -- 384-dim float32
    confidence REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

---

## Summary

| Phase | What Happens |
|-------|--------------|
| Setup | `sqrl init` registers project |
| Learning | Daemon watches CLI logs, parses to Events |
| Batching | Groups events into Episodes (4-hour window OR 50 events) |
| Extraction | Router Agent INGEST decides ADD/UPDATE/NOOP |
| Retrieval | MCP tool → Router Agent ROUTE → memories with "why" |

---

## Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| Episode trigger | 4-hour window OR 50 events | Balance context vs LLM cost |
| Session tracking | None | Simpler, CLI-agnostic |
| Event schema | Normalized (no CLI field) | All CLIs treated equally |
| Episode storage | Not stored | Just internal batching |
