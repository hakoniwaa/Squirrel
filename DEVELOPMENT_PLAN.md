# Squirrel Development Plan (v1)

Modular development plan for v1 architecture with Rust daemon + Python Memory Service communicating via Unix socket IPC.

## v1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        RUST DAEMON                              │
│  Log Watcher → Events → Episodes → IPC → Memory Service         │
│  SQLite/sqlite-vec storage                                      │
│  MCP Server (2 tools)                                           │
│  CLI (sqrl init/config/daemon/status/mcp)                       │
└─────────────────────────────────────────────────────────────────┘
                             ↕ Unix socket IPC
┌─────────────────────────────────────────────────────────────────┐
│                     PYTHON MEMORY SERVICE                       │
│  Router Agent (dual-mode: INGEST + ROUTE)                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ INGEST Mode: LLM analyzes Episode in one call:            │  │
│  │   1. Identify Tasks (user goals within the episode)       │  │
│  │   2. Classify each Task: SUCCESS | FAILURE | UNCERTAIN    │  │
│  │   3. Extract memories: SUCCESS→recipe/project_fact,       │  │
│  │      FAILURE→pitfall, UNCERTAIN→skip                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ONNX Embeddings (all-MiniLM-L6-v2, 384-dim)                    │
│  Retrieval + "Why" generation                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Insight: Success Detection

Passive learning from logs requires knowing WHAT succeeded and WHAT failed. Unlike explicit APIs where users call `memory.add()`, we must infer success from conversation patterns.

**Success signals (implicit):**
- AI says "done" / "complete" + User moves to next task → SUCCESS
- Tests pass, build succeeds → SUCCESS
- User says "thanks", "perfect", "works" → SUCCESS

**Failure signals:**
- Same error reappears after attempted fix → FAILURE
- User says "still broken", "that didn't work" → FAILURE
- User abandons task mid-conversation → UNCERTAIN

**The LLM-decides-everything approach:**
- One LLM call per Episode (4-hour window)
- LLM segments tasks, classifies outcomes, extracts memories
- No rules engine, no heuristics for task detection
- 100% passive - no user prompts or confirmations

## Development Tracks

```
Phase 0: Scaffolding (1-2 days)
    |
    v
+-------+-------+-------+
|       |       |       |
v       v       v       v
Track A Track B Track C Track D
(Rust   (Rust   (Python (Python
Storage) Daemon) Router) Retrieval)
    |       |       |       |
    +---+---+       +---+---+
        |               |
        v               v
    Week 1-2        Week 2-3
        |               |
        +-------+-------+
                |
                v
            Track E (Week 3)
            MCP Layer
                |
                v
            Phase X (Week 4+)
            Hardening
```

---

## Phase 0 – Scaffolding (1-2 days)

### Rust Module (`agent/`)

- [ ] Create `Cargo.toml`:
  - `tokio` (async runtime)
  - `rusqlite` + `sqlite-vec` (storage)
  - `serde`, `serde_json` (serialization)
  - `notify` (file watching)
  - `clap` (CLI)
  - `uuid`, `chrono` (ID, timestamps)

- [ ] Directory structure:
  ```
  agent/src/
  ├── main.rs
  ├── lib.rs
  ├── daemon.rs       # Process management
  ├── watcher.rs      # Log file watching
  ├── storage.rs      # SQLite + sqlite-vec
  ├── events.rs       # Event/Episode structs
  ├── config.rs       # Config management
  ├── mcp.rs          # MCP server
  └── ipc.rs          # Unix socket client
  ```

### Python Module (`memory_service/`)

- [ ] Create `pyproject.toml`:
  - `onnxruntime` (embeddings)
  - `sentence-transformers` (model loading)
  - `anthropic` / `openai` (Router Agent)
  - `pydantic` (schemas)

- [ ] Directory structure:
  ```
  memory_service/
  ├── squirrel_memory/
  │   ├── __init__.py
  │   ├── server.py       # Unix socket server
  │   ├── router_agent.py # Dual-mode router
  │   ├── embeddings.py   # ONNX embeddings
  │   ├── retrieval.py    # Similarity search
  │   └── schemas/
  └── tests/
  ```

- [ ] CI basics (GitHub Actions: lint, test)

---

## Track A – Rust: Storage + Config + Events (Week 1)

### A1. Storage layer (`storage.rs`)

- [ ] SQLite + sqlite-vec initialization:
  ```rust
  fn init_project_db(path: &Path) -> Result<Connection>
  fn init_global_db() -> Result<Connection>  // ~/.sqrl/squirrel.db
  ```

- [ ] Create tables:
  ```sql
  CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content_hash TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    memory_type TEXT NOT NULL,        -- user_style | project_fact | pitfall | recipe
    repo TEXT NOT NULL,               -- repo path OR 'global' for user-level memories
    embedding BLOB,
    confidence REAL NOT NULL,
    importance TEXT NOT NULL DEFAULT 'medium',  -- critical | high | medium | low
    state TEXT NOT NULL DEFAULT 'active',       -- active | deleted (soft-delete)
    user_id TEXT NOT NULL DEFAULT 'local',
    assistant_id TEXT NOT NULL DEFAULT 'squirrel',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT                             -- NULL unless state='deleted'
  );

  CREATE TABLE events (
    id TEXT PRIMARY KEY,
    repo TEXT NOT NULL,
    kind TEXT NOT NULL,        -- user | assistant | tool | system
    content TEXT NOT NULL,
    file_paths TEXT,           -- JSON array
    ts TEXT NOT NULL,
    processed INTEGER DEFAULT 0
  );

  -- History table for audit trail (tracks memory changes)
  CREATE TABLE memory_history (
    id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL,
    old_content TEXT,          -- Previous content (NULL for ADD)
    new_content TEXT NOT NULL, -- New content
    event TEXT NOT NULL,       -- ADD | UPDATE | DELETE
    created_at TEXT NOT NULL,
    FOREIGN KEY (memory_id) REFERENCES memories(id)
  );

  -- Access log for debugging memory retrieval behavior
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
  -- Note: No episodes table - episodes are in-memory batching only
  ```

- [ ] CRUD operations for events and memories

### A2. Event model (`events.rs`)

- [ ] Define `Event` struct (normalized, CLI-agnostic):
  ```rust
  struct Event {
      id: String,
      repo: String,
      kind: EventKind,     // User | Assistant | Tool | System
      content: String,
      file_paths: Vec<String>,
      ts: DateTime<Utc>,
      processed: bool,
  }
  ```

- [ ] Define `Episode` struct (in-memory only, not persisted):
  ```rust
  struct Episode {
      id: String,
      repo: String,
      start_ts: DateTime<Utc>,
      end_ts: DateTime<Utc>,
      events: Vec<Event>,  // Contains actual events, not IDs
  }
  ```

- [ ] Dedup hash computation
- [ ] Episode batching: 4-hour time window OR 50 events max (whichever first)

### A3. Config (`config.rs`)

- [ ] Path helpers:
  ```rust
  fn get_sqrl_dir() -> PathBuf          // ~/.sqrl/
  fn get_project_sqrl_dir(repo: &Path) -> PathBuf  // <repo>/.sqrl/
  ```

- [ ] Config management:
  ```rust
  struct Config {
      user_id: String,
      anthropic_api_key: Option<String>,
      default_model: String,
      socket_path: String,
  }
  ```

- [ ] Projects registry (track which repos are initialized)

### A4. CLI skeleton (`main.rs`)

- [ ] Command structure:
  ```
  sqrl init              # Initialize project
  sqrl config            # Set user_id, API keys
  sqrl daemon start      # Start daemon
  sqrl daemon stop       # Stop daemon
  sqrl status            # Show memory stats
  sqrl mcp               # Run MCP server
  ```

- [ ] Implement `sqrl init`:
  - Create `<repo>/.sqrl/` directory
  - Initialize `squirrel.db`
  - Register in projects registry

---

## Track B – Rust: Daemon + Watcher + IPC (Week 1-2)

### B1. Daemon (`daemon.rs`)

- [ ] Daemon structure:
  ```rust
  struct Daemon {
      watchers: Vec<LogWatcher>,
      memory_service: Option<ChildProcess>,
      ipc_client: IpcClient,
  }
  ```

- [ ] Startup sequence:
  1. Load projects registry
  2. For each project, spawn watcher
  3. Spawn Python Memory Service as child process
  4. Connect to Memory Service via Unix socket

- [ ] Shutdown: kill Python, stop watchers

### B2. Log Watchers (`watcher.rs`)

- [ ] Multi-CLI log discovery:
  ```rust
  fn find_log_paths() -> Vec<PathBuf> {
      // ~/.claude/projects/**/*.jsonl    → Claude Code
      // ~/.codex-cli/logs/**/*.jsonl     → Codex CLI
      // ~/.gemini/logs/**/*.jsonl        → Gemini CLI
      // Note: All CLIs normalized to same Event schema
  }
  ```

- [ ] JSONL tailer using `notify` crate:
  ```rust
  struct LogWatcher {
      log_dirs: Vec<PathBuf>,
      file_positions: HashMap<PathBuf, u64>,
  }
  ```

- [ ] Line parsers for each CLI format → normalized Event
- [ ] Write events to SQLite

### B3. Episode Batching

- [ ] Per-repo event buffer:
  ```rust
  struct EventBuffer {
      repo: String,
      events: Vec<Event>,
      oldest_ts: DateTime<Utc>,
  }
  ```

- [ ] Flush triggers:
  ```rust
  fn should_flush(buffer: &EventBuffer) -> bool {
      const MAX_EVENTS: usize = 50;
      const WINDOW_HOURS: i64 = 4;

      buffer.events.len() >= MAX_EVENTS ||
      buffer.age() >= Duration::hours(WINDOW_HOURS)
  }
  ```

- [ ] On flush: create Episode, send to Python via IPC, mark events processed

### B4. IPC Client (`ipc.rs`)

- [ ] Unix socket client:
  ```rust
  struct IpcClient {
      socket_path: PathBuf,
  }

  impl IpcClient {
      async fn router_agent(&self, mode: &str, payload: Value) -> Result<Value>
      async fn fetch_memories(&self, params: FetchParams) -> Result<Vec<Memory>>
  }
  ```

- [ ] JSON-RPC style protocol:
  ```json
  {"method": "router_agent", "params": {...}, "id": 123}
  {"result": {...}, "id": 123}
  ```

---

## Track C – Python: Router Agent + Server (Week 1-2)

### C1. Unix Socket Server (`server.py`)

- [ ] Socket server listening at `/tmp/sqrl_router.sock`:
  ```python
  async def handle_connection(reader, writer):
      request = await read_json(reader)
      if request["method"] == "router_agent":
          result = await router_agent(request["params"])
      elif request["method"] == "fetch_memories":
          result = await fetch_memories(request["params"])
      await write_json(writer, {"result": result, "id": request["id"]})
  ```

### C2. Router Agent (`router_agent.py`)

- [ ] Dual-mode router:
  ```python
  async def router_agent(mode: str, payload: dict) -> dict:
      if mode == "ingest":
          return await ingest_mode(payload)
      elif mode == "route":
          return await route_mode(payload)
  ```

- [ ] INGEST mode (write-side):
  ```python
  async def ingest_mode(payload: dict) -> dict:
      """
      Input: {episode: {...}, events: [...]}
      Output: {
          tasks: [
              {
                  task: str,                          # What user was trying to do
                  outcome: SUCCESS | FAILURE | UNCERTAIN,
                  evidence: str,                      # Why this classification
                  memories: [                         # Only if outcome != UNCERTAIN
                      {type, content, importance, repo}
                  ]
              }
          ],
          confidence: float
      }

      LLM analyzes entire Episode in ONE call:
      1. Segment into distinct Tasks (user goals like "fix bug X", "add feature Y")
      2. For each Task, classify outcome:
         - SUCCESS: User moved to next task, tests passed, "thanks"
         - FAILURE: Same error recurs, "still broken", abandoned
         - UNCERTAIN: Incomplete information, skip memory extraction
      3. Extract memories based on outcome:
         - SUCCESS → recipe (reusable pattern) or project_fact (learned info)
         - FAILURE → pitfall (what NOT to do, with why it failed)
         - UNCERTAIN → nothing

      This is the core passive learning insight: we MUST know what succeeded
      before extracting patterns. Competitors with explicit APIs (mem0) don't
      need this - users explicitly call memory.add() for successes only.

      Near-duplicate check (before ADD):
      - Query sqlite-vec for similar memories (same type + repo, similarity > 0.9)
      - If found, LLM decides: NOOP (exact dup) or UPDATE (merge info)

      UUID→Integer Mapping (prevents LLM hallucination):
      - When showing existing memories to LLM for dedup, map UUIDs to "0", "1", "2"
      - LLM references memories by simple integer
      - Map back to real UUIDs after LLM response
      """
  ```

- [ ] ROUTE mode (read-side):
  ```python
  async def route_mode(payload: dict) -> dict:
      """
      Input: {task: str, candidates: [...], context_budget_tokens: int}
      Output: {selected: [...], why: {...}}

      v1: Heuristic scoring to select within token budget
      score = w_sim * similarity + w_imp * importance_weight + w_rec * recency_score
      (importance_weight: critical=1.0, high=0.75, medium=0.5, low=0.25)

      v1.1 (future): LLM-based selection for complex disambiguation
      """
  ```

### C3. Schemas (`schemas/`)

- [ ] Memory schema:
  ```python
  class MemoryState(str, Enum):
      active = "active"
      deleted = "deleted"

  class Memory(BaseModel):
      id: str
      content_hash: str
      content: str
      memory_type: Literal["user_style", "project_fact", "pitfall", "recipe"]
      repo: str                    # repo path OR 'global' for user-level memories
      embedding: Optional[bytes]
      confidence: float
      importance: Literal["critical", "high", "medium", "low"] = "medium"
      state: MemoryState = MemoryState.active  # Soft-delete support
      user_id: str = "local"
      assistant_id: str = "squirrel"
      created_at: datetime
      updated_at: datetime
      deleted_at: Optional[datetime] = None    # NULL unless state='deleted'
  ```

- [ ] IPC request/response schemas:
  ```python
  class RouterAgentRequest(BaseModel):
      mode: Literal["ingest", "route"]
      payload: dict

  class FetchMemoriesRequest(BaseModel):
      repo: str
      task: Optional[str]
      memory_types: Optional[list[str]]
      context_budget_tokens: int = 400   # Token limit for memory injection
      max_results: int = 20
  ```

### C4. Structured Exceptions (`exceptions.py`)

- [ ] Exception hierarchy with error codes and suggestions:
  ```python
  class SquirrelError(Exception):
      """Base exception with error code and user-friendly suggestion."""
      def __init__(self, message: str, error_code: str, suggestion: str = None, details: dict = None):
          self.message = message
          self.error_code = error_code
          self.suggestion = suggestion
          self.details = details or {}
          super().__init__(message)

  class MemoryNotFoundError(SquirrelError):
      """Memory ID does not exist."""
      pass

  class ExtractionError(SquirrelError):
      """LLM extraction failed."""
      pass

  class EmbeddingError(SquirrelError):
      """ONNX embedding failed."""
      pass

  class StorageError(SquirrelError):
      """SQLite/sqlite-vec operation failed."""
      pass

  # Usage:
  # raise MemoryNotFoundError(
  #     message=f"Memory {memory_id} not found",
  #     error_code="MEM_404",
  #     suggestion="Check if the memory ID is correct or if it was deleted"
  # )
  ```

---

## Track D – Python: Embeddings + Retrieval (Week 2-3)

### D1. ONNX Embeddings (`embeddings.py`)

- [ ] Load all-MiniLM-L6-v2 via ONNX:
  ```python
  class EmbeddingModel:
      def __init__(self):
          self.session = ort.InferenceSession("all-MiniLM-L6-v2.onnx")

      def embed(self, text: str) -> np.ndarray:
          # Tokenize and run inference
          # Returns 384-dim vector
  ```

- [ ] Batch embedding for memory items
- [ ] Cache model in memory

### D2. Retrieval (`retrieval.py`)

- [ ] Similarity search:
  ```python
  async def retrieve_candidates(
      repo: str,
      task: str,
      memory_types: list[str] = None,
      top_k: int = 20
  ) -> list[Memory]:
      # 1. Embed task description
      # 2. Query sqlite-vec for similar memories
      # 3. Filter by repo and types
      # 4. Return top candidates
  ```

- [ ] "Why" generation (heuristic templates):
  ```python
  def generate_why(memory: Memory, task: str) -> str:
      templates = {
          "user_style": "Relevant because {task_verb} matches your preference for {pattern}",
          "project_fact": "Relevant because {task_verb} involves {entity}",
          "pitfall": "Warning: {issue} may occur when {task_verb}",
          "recipe": "Useful pattern for {task_verb}",
      }
      # Simple keyword matching + template filling
  ```

### D3. UUID Mapping Helpers (`utils.py`)

- [ ] UUID→integer mapping (prevents LLM hallucination):
  ```python
  def prepare_memories_for_llm(memories: list[Memory]) -> tuple[list[dict], dict[str, str]]:
      """Map UUIDs to integers before sending to LLM."""
      uuid_mapping = {}
      prepared = []
      for idx, memory in enumerate(memories):
          uuid_mapping[str(idx)] = memory.id
          prepared.append({"id": str(idx), "content": memory.content, "type": memory.memory_type})
      return prepared, uuid_mapping

  def restore_memory_ids(llm_response: list[dict], uuid_mapping: dict[str, str]) -> list[dict]:
      """Map integers back to UUIDs after LLM response."""
      for item in llm_response:
          if item.get("id") in uuid_mapping:
              item["id"] = uuid_mapping[item["id"]]
      return llm_response
  ```

### D4. Near-Duplicate Check + Memory Update

- [ ] Near-duplicate detection (before ADD):
  ```python
  async def check_near_duplicate(
      memory: Memory,
      similarity_threshold: float = 0.9
  ) -> tuple[bool, Optional[Memory]]:
      """
      Query sqlite-vec for similar memories with same type + repo.
      Returns (is_duplicate, existing_memory_if_found)
      """
      candidates = await retrieve_candidates(
          repo=memory.repo,
          task=memory.content,
          memory_types=[memory.memory_type],
          top_k=5
      )
      for candidate in candidates:
          if candidate.similarity >= similarity_threshold:
              return True, candidate
      return False, None
  ```

- [ ] Confidence threshold (0.7) + dedup:
  ```python
  async def process_ingest_result(result: dict) -> Memory | None:
      if result["action"] == "NOOP":
          return None
      if result["confidence"] < 0.7:
          return None

      if result["action"] == "ADD":
          memory = build_memory(result["memory"])
          is_dup, existing = await check_near_duplicate(memory)
          if is_dup:
              # LLM already handled dedup, but double-check via embedding
              # If truly duplicate, return None; else merge
              return await merge_or_skip(memory, existing)
          return create_memory(memory)
      elif result["action"] == "UPDATE":
          return update_memory(result["memory"])
  ```

### D5. History Tracking + Access Logging

- [ ] History tracking on memory changes:
  ```python
  async def create_memory(memory: Memory) -> Memory:
      """Create memory and log to history table."""
      # Insert memory
      await db.execute("INSERT INTO memories (...) VALUES (...)", memory)
      # Log to history
      await db.execute("""
          INSERT INTO memory_history (id, memory_id, old_content, new_content, event, created_at)
          VALUES (?, ?, NULL, ?, 'ADD', datetime('now'))
      """, (uuid4(), memory.id, memory.content))
      return memory

  async def update_memory(memory_id: str, new_content: str) -> Memory:
      """Update memory and log old→new to history table."""
      old = await db.fetch_one("SELECT content FROM memories WHERE id = ?", memory_id)
      await db.execute("UPDATE memories SET content = ?, updated_at = datetime('now') WHERE id = ?",
                       (new_content, memory_id))
      await db.execute("""
          INSERT INTO memory_history (id, memory_id, old_content, new_content, event, created_at)
          VALUES (?, ?, ?, ?, 'UPDATE', datetime('now'))
      """, (uuid4(), memory_id, old.content, new_content))

  async def delete_memory(memory_id: str) -> None:
      """Soft-delete memory (set state='deleted') and log to history."""
      await db.execute("""
          UPDATE memories SET state = 'deleted', deleted_at = datetime('now')
          WHERE id = ?
      """, memory_id)
      await db.execute("""
          INSERT INTO memory_history (id, memory_id, old_content, new_content, event, created_at)
          VALUES (?, ?, NULL, NULL, 'DELETE', datetime('now'))
      """, (uuid4(), memory_id))
  ```

- [ ] Access logging for debugging:
  ```python
  async def log_memory_access(
      memory_id: str,
      access_type: str,  # "search" | "get_context" | "list"
      query: str = None,
      score: float = None,
      metadata: dict = None
  ) -> None:
      """Log memory access for debugging retrieval behavior."""
      await db.execute("""
          INSERT INTO memory_access_log (id, memory_id, access_type, query, score, metadata, accessed_at)
          VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
      """, (uuid4(), memory_id, access_type, query, score, json.dumps(metadata or {})))

  # Usage in retrieval.py:
  async def retrieve_candidates(...) -> list[Memory]:
      results = await vector_search(...)
      for r in results:
          await log_memory_access(r.id, "search", query=task, score=r.similarity)
      return results
  ```

---

## Track E – MCP Layer (Week 3)

### E1. MCP Server (`mcp.rs`)

- [ ] MCP stdio protocol handler
- [ ] 2 tool definitions:
  ```rust
  // Primary tool
  ToolDefinition {
      name: "squirrel_get_task_context",
      description: "Get task-aware memory with 'why' explanations",
      input_schema: {
          "project_root": "string (required)",
          "task": "string (required)",
          "context_budget_tokens": "integer (default: 400)",  // Token limit for memory injection
          "memory_types": "array of strings (optional)"
      }
  }

  // Search tool
  ToolDefinition {
      name: "squirrel_search_memory",
      description: "Semantic search across all memory",
      input_schema: {
          "project_root": "string (required)",
          "query": "string (required)",
          "top_k": "integer (default: 10)",
          "memory_types": "array of strings (optional)"
      }
  }
  ```

### E2. Tool Handlers

- [ ] `squirrel_get_task_context`:
  ```rust
  async fn handle_get_task_context(args: Value) -> Result<Value> {
      // 1. Retrieve candidates via IPC (fetch_memories)
      // 2. Call Router Agent (route mode) via IPC with context_budget_tokens
      // 3. Route mode scores: w_sim * similarity + w_imp * importance + w_rec * recency
      // 4. Select memories until token budget exhausted
      // 5. Format response with "why" explanations
  }
  ```

- [ ] `squirrel_search_memory`:
  ```rust
  async fn handle_search_memory(args: Value) -> Result<Value> {
      // 1. Retrieve via IPC (fetch_memories with query)
      // 2. Return with similarity scores
  }
  ```

### E3. `sqrl mcp` Command

- [ ] Entry point:
  ```rust
  fn cmd_mcp() {
      ensure_daemon_running()?;
      let server = McpServer::new();
      server.run_stdio();  // Blocks, handles MCP protocol
  }
  ```

### E4. Claude Code Integration

- [ ] MCP config snippet:
  ```json
  {
    "mcpServers": {
      "squirrel": {
        "command": "sqrl",
        "args": ["mcp"]
      }
    }
  }
  ```

---

## Phase X – Hardening (Week 4+)

### Logging & Observability

- [ ] Structured logging (Rust: `tracing`, Python: `structlog`)
- [ ] Metrics: events/episodes/memories processed, latency

### Testing

- [ ] Unit tests:
  - Rust: storage, events, episode grouping
  - Python: router agent, embeddings, retrieval

- [ ] Integration tests:
  - Full flow: log → event → episode → memory
  - MCP tool calls end-to-end

### CLI Polish

- [ ] `sqrl status`: daemon status, project stats, memory counts
- [ ] `sqrl config`: interactive API key setup

---

## Timeline Summary

| Week | Track A | Track B | Track C | Track D | Track E |
|------|---------|---------|---------|---------|---------|
| 0 | Scaffold | Scaffold | Scaffold | - | - |
| 1 | Storage, Events, Config, CLI | Daemon start | Socket server, Router Agent | - | - |
| 2 | - | Watchers, IPC client, Batch loop | - | Embeddings, Retrieval | - |
| 3 | - | Integration | - | Update logic | MCP layer (2 tools) |
| 4+ | - | Hardening | - | Why templates | Integration |

---

## Team Assignment (3 developers)

**Developer 1 (Rust focus):**
- Phase 0: Rust scaffold
- Track A: All
- Track B: All
- Track E: All

**Developer 2 (Python focus):**
- Phase 0: Python scaffold
- Track C: All
- Track D: All

**Developer 3 (Full-stack / Prompts):**
- Phase 0: CI, docs
- Router Agent prompts
- Phase X: Testing, documentation

---

## v1.1 Scope (Future Enhancement)

Deferred from v1:
- Two-level ROUTE: LLM-based selection for complex disambiguation
- User override of importance via CLI (`sqrl memory set-importance <id> critical`)
- Memory state expansion: add `paused` and `archived` states (v1 uses active/deleted only)
- `sqrl debug` command: query memory_access_log to debug retrieval behavior

## v2 Scope (Future)

Not in v1:
- Hooks output for Claude Code / Gemini CLI
- File injection for AGENTS.md / GEMINI.md
- Cloud sync (user_id/assistant_id fields prepared)
- Team memory sharing
- Web dashboard
- Reranker layer: post-retrieval LLM reranking for improved precision at scale
- Previous memory in update response (for client audit display)

---

## Patterns Adopted from Competitor Analysis

The following patterns were incorporated from analyzing mem0/OpenMemory, Memori, and claude-cache:

| Pattern | Source | Location in Plan |
|---------|--------|------------------|
| UUID→integer mapping for LLM | mem0 | Track C (INGEST mode), Track D (D3) |
| History tracking (old/new content) | mem0 | Track A (memory_history table), Track D (D5) |
| Structured exceptions with codes | mem0 | Track C (C4) |
| Memory state machine (soft-delete) | mem0 | Track A (state column), Track C (MemoryState enum) |
| Access logging for debugging | mem0 | Track A (memory_access_log table), Track D (D5) |
| **Success detection (implicit signals)** | claude-cache | Core Architecture, Track C (INGEST mode) |
| **Anti-pattern/pitfall learning** | claude-cache | Memory types (pitfall), INGEST mode |
| **LLM-decides-everything approach** | claude-cache + simplification | Track C (INGEST mode) |

### Critical Insight from claude-cache (0-star repo)

claude-cache solved the core problem we overlooked: **how do you know what to learn from passive observation?**

Their approach (multi-signal success detection):
- Explicit: "thanks", "that worked", tests pass
- Implicit: AI says "done" + User moves to next task = SUCCESS
- Behavioral: Task transition without complaints = SUCCESS

Our simplification:
- No complex rules engine or signal weighting
- Single LLM call per Episode decides everything (task segmentation + outcome + memories)
- Let the LLM understand conversation semantics instead of regex patterns

This is why mem0 (50k stars) didn't help us - their users explicitly call `memory.add()`.
Only passive learning systems need success detection.

Patterns explicitly NOT adopted:
- Two LLM calls per memory add (expensive) - we use single-pass extraction
- Heavy infrastructure (22 vector stores) - we use SQLite-only
- LLM-based categorization on insert - we use source-based categories
- Explicit API approach - we use passive CLI watching
- Complex Task/Attempt hierarchy - we let LLM segment tasks naturally
- Rules engines for success detection - LLM understands context better
