# mem0/OpenMemory Learning Analysis

## Overview
mem0 is an open-source memory layer for LLM applications providing semantic, episodic, and procedural memory types with vector storage, graph relationships, and optional reranking.

**Repository**: https://github.com/mem0ai/mem0
**Threat Level**: Short-term LOW, Long-term MEDIUM

Short-term: Different activation pattern (explicit API vs passive logs), chatbot-focused, heavy infrastructure.
Long-term: They already have an MCP server (`openmemory/api/app/mcp_server.py`). If they ship dev-tool log ingesters or deeper CLI integrations, they move closer to our space. Their B2B/SaaS infrastructure makes them a natural candidate for IDEs/agents wanting to outsource memory.

## Files Analyzed

### Core Library (mem0/)
- `memory/main.py` - Memory class with add/search/update operations
- `memory/storage.py` - SQLite history tracking
- `memory/utils.py` - JSON extraction, vision parsing, entity formatting
- `configs/prompts.py` - FACT_RETRIEVAL_PROMPT, UPDATE_MEMORY_PROMPT, PROCEDURAL_MEMORY_PROMPT
- `configs/base.py` - MemoryConfig, MemoryItem schemas
- `configs/enums.py` - MemoryType enum (SEMANTIC, EPISODIC, PROCEDURAL)
- `reranker/llm_reranker.py` - LLM-based reranking implementation
- `graphs/utils.py` - EXTRACT_RELATIONS_PROMPT, UPDATE_GRAPH_PROMPT
- `graphs/tools.py` - Function tools for graph operations
- `exceptions.py` - Structured exception hierarchy with error codes
- `vector_stores/configs.py` - 22 vector store backend configs
- `embeddings/configs.py` - 11 embedding provider configs
- `llms/configs.py` - 17 LLM provider configs

### OpenMemory Server (openmemory/)
- `api/app/models.py` - User, App, Memory, Category, AccessControl, MemoryStatusHistory
- `api/app/mcp_server.py` - MCP tools (add_memories, search_memory, list_memories, delete)
- `api/app/utils/memory.py` - Memory client initialization, Docker URL handling
- `api/app/utils/permissions.py` - check_memory_access_permissions
- `api/app/utils/categorization.py` - LLM-based category assignment

## Architecture Summary

### Memory Types
```python
class MemoryType(Enum):
    SEMANTIC = "semantic_memory"    # Facts and knowledge
    EPISODIC = "episodic_memory"    # Conversation history
    PROCEDURAL = "procedural_memory"  # Agent execution steps
```

### Two-Phase Memory Processing
1. **FACT_RETRIEVAL_PROMPT** - Extracts facts from conversation as JSON
2. **UPDATE_MEMORY_PROMPT** - Decides ADD/UPDATE/DELETE/NONE for each fact

### Session Identifiers
- `user_id` - User scope
- `agent_id` - Agent scope
- `run_id` - Run/conversation scope

At least one is required for all operations.

### Data Models (OpenMemory)
```python
class Memory(Base):
    id = Column(UUID)
    user_id = Column(UUID, ForeignKey("users.id"))
    app_id = Column(UUID, ForeignKey("apps.id"))
    content = Column(String)
    state = Column(Enum(MemoryState))  # active/paused/archived/deleted
    created_at, updated_at, archived_at, deleted_at
    categories = relationship("Category", secondary="memory_categories")

class MemoryStatusHistory(Base):  # Audit trail
    memory_id, changed_by, old_state, new_state, changed_at

class MemoryAccessLog(Base):  # Access tracking
    memory_id, app_id, access_type, metadata_
```

## What We Should NOT Copy

### 1. Explicit API Calls Required
```python
# Their approach - manual call every time
memory.add("User likes Python", user_id="user1")
memory.search("preferences", user_id="user1")
```
No passive observation. Developer must explicitly call add/search.
**Our approach is better**: Watch CLI output passively.

### 2. Two LLM Calls Per Memory Add
```python
# Phase 1: Extract facts
response = self.llm.generate_response(messages=[system: FACT_RETRIEVAL, user: input])
facts = json.loads(response)["facts"]

# Phase 2: Decide action
response = self.llm.generate_response(messages=[user: UPDATE_MEMORY_PROMPT])
actions = json.loads(response)["memory"]  # ADD/UPDATE/DELETE per fact
```
Expensive - two LLM round-trips for every add operation.
**We can be smarter with single-pass extraction.**

### 3. Heavy Infrastructure
- 22 vector store backends
- 17 LLM providers
- 11 embedding providers
- Optional Neo4j for graph memory
- PostgreSQL for OpenMemory server

**Our SQLite-only approach is simpler and sufficient for local-first.**

### 4. No Session/Episode Concept
They use arbitrary string IDs (user_id, agent_id, run_id).
**Our Episode-based 4-hour windows are more natural for developer workflows.**

### 5. LLM Categorization on Every Insert
```python
@event.listens_for(Memory, 'after_insert')
def after_memory_insert(mapper, connection, target):
    categorize_memory(target, db)  # Calls gpt-4o-mini!
```
Calls LLM for every memory just to assign categories. Expensive.
**We can use source-based categories (system/tool) without LLM.**

### 6. No Tool Awareness
Their prompts focus on personal preferences, relationships, plans:
```
Types of Information to Remember:
1. Store Personal Preferences
2. Maintain Important Personal Details
3. Track Plans and Intentions
...
```
Nothing about tool invocations, file paths, or debugging patterns.
**Our tool-aware extraction is more relevant for coding AI.**

## What We Should Learn From

### 1. UUID → Integer Mapping (Prevents LLM Hallucination)
```python
# mem0/memory/main.py:490-494
temp_uuid_mapping = {}
for idx, item in enumerate(retrieved_old_memory):
    temp_uuid_mapping[str(idx)] = item["id"]
    retrieved_old_memory[idx]["id"] = str(idx)

# Send to LLM with simple integers "0", "1", "2"
# Then map back:
memory_id = temp_uuid_mapping[resp.get("id")]
```
LLMs can hallucinate UUIDs. Using simple integers prevents invalid ID references.

**Recommendation**: Use this pattern when LLM needs to reference existing memories.

### 2. History Table with Old/New Content
```sql
-- mem0/memory/storage.py
CREATE TABLE history (
    id TEXT PRIMARY KEY,
    memory_id TEXT,
    old_memory TEXT,    -- Previous content
    new_memory TEXT,    -- Updated content
    event TEXT,         -- ADD, UPDATE, DELETE
    created_at DATETIME,
    updated_at DATETIME,
    is_deleted INTEGER,
    actor_id TEXT,
    role TEXT
);
```
Tracks what changed, what it was before, and what action occurred.

**Recommendation**: Add `old_content` column when updating memories.

### 3. Reranker Layer Pattern
```python
# mem0/memory/main.py:846-851
if rerank and self.reranker and original_memories:
    reranked_memories = self.reranker.rerank(query, original_memories, limit)
    original_memories = reranked_memories
```
Two-stage retrieval:
1. Fast vector search (get candidates)
2. LLM/Cohere/SentenceTransformer reranking (improve quality)

LLM reranker scores each document 0.0-1.0:
```python
# mem0/reranker/llm_reranker.py
prompt = """Score the relevance on a scale from 0.0 to 1.0:
- 1.0 = Perfectly relevant
- 0.8-0.9 = Highly relevant
- 0.6-0.7 = Moderately relevant
- 0.4-0.5 = Slightly relevant
- 0.0-0.3 = Not relevant
"""
```

**Recommendation**: Consider for v2 when memory count grows large.

### 4. Structured Exception Hierarchy
```python
# mem0/exceptions.py
class MemoryError(Exception):
    def __init__(self, message, error_code, details=None, suggestion=None, debug_info=None):
        self.message = message
        self.error_code = error_code  # "VAL_001", "MEM_404", etc.
        self.details = details or {}
        self.suggestion = suggestion  # User-friendly fix message
        self.debug_info = debug_info or {}

class ValidationError(MemoryError): pass
class MemoryNotFoundError(MemoryError): pass
class VectorStoreError(MemoryError): pass
class EmbeddingError(MemoryError): pass
class LLMError(MemoryError): pass
```
Every exception has error code, suggestion, and debug info.

**Recommendation**: Adopt structured exceptions with codes and suggestions.

### 5. Memory State Machine
```python
class MemoryState(enum.Enum):
    active = "active"      # Normal state
    paused = "paused"      # Temporarily disabled
    archived = "archived"  # Old but preserved
    deleted = "deleted"    # Soft delete
```
Memories can be paused/archived, not just deleted. Allows recovery.

**Recommendation**: Consider adding memory states for soft-delete.

### 6. Previous Memory in Update Response
```python
# When updating, return what the old value was
returned_memories.append({
    "id": memory_id,
    "memory": new_content,
    "event": "UPDATE",
    "previous_memory": old_content,  # Good for auditing
})
```

### 7. Memory Access Logging
```python
class MemoryAccessLog(Base):
    memory_id = Column(UUID)
    app_id = Column(UUID)
    access_type = Column(String)  # "search", "list", "delete"
    accessed_at = Column(DateTime)
    metadata_ = Column(JSON)  # query, score, etc.
```
Logs every access. Useful for understanding usage patterns.

### 8. Entity Relationship Format
```python
def format_entities(entities):
    for entity in entities:
        simplified = f"{entity['source']} -- {entity['relationship']} -- {entity['destination']}"
```
Simple triple format for LLM consumption: `user -- prefers -- Python`

### 9. Procedural Memory for Agent Steps
```
PROCEDURAL_MEMORY_SYSTEM_PROMPT = """
You are a memory summarization system...

### Sequential Agent Actions (Numbered Steps):
1. **Agent Action**: Clicked on the 'Blog' link
   **Action Result**: Navigated to blog listing page
   **Key Findings**: Blog listing shows 10 previews
   **Current Context**: Ready to extract blog posts
"""
```
Specialized format for tracking agent execution history with action + result + findings.

**Could inspire**: How we format tool execution memories.

## Key Differences from Squirrel

| Aspect | mem0 | Squirrel |
|--------|------|----------|
| Activation | Explicit API call | Passive CLI watching |
| Session Model | user_id/agent_id/run_id | Episode (4-hour windows) |
| Infrastructure | Docker + Postgres + Vector DB | Local SQLite only |
| Extraction | Two LLM calls | Single-pass extraction |
| Tool Awareness | None (chatbot-focused) | Extracts tool patterns |
| Memory Categories | LLM-assigned | Source-based (system/tool) |
| Graph Support | Neo4j integration | None (simpler) |
| Reranking | Optional LLM/Cohere | None (v1) |

## Implementation Recommendations

### For v1 (Adopt Now)
| Pattern | Effort | Value |
|---------|--------|-------|
| History tracking (old_content column) | Low | Debug, rollback |
| UUID→integer mapping for LLM | Low | Prevent hallucination |
| Structured exceptions with codes | Low | Better error handling |

### For v2 (Consider Later)
| Pattern | Effort | Value |
|---------|--------|-------|
| Reranker layer | Medium | Quality at scale |
| Memory states (active/archived) | Low | Soft delete |
| Access logging | Low | Usage analytics |
| Previous memory in update response | Low | Auditing |

## Sample Patterns

### UUID Mapping Pattern
```python
def _prepare_memories_for_llm(memories):
    """Map UUIDs to integers before sending to LLM."""
    uuid_mapping = {}
    prepared = []
    for idx, memory in enumerate(memories):
        uuid_mapping[str(idx)] = memory["id"]
        prepared.append({"id": str(idx), "content": memory["content"]})
    return prepared, uuid_mapping

def _restore_memory_ids(llm_response, uuid_mapping):
    """Map integers back to UUIDs after LLM response."""
    for item in llm_response:
        if item.get("id") in uuid_mapping:
            item["id"] = uuid_mapping[item["id"]]
    return llm_response
```

### History Tracking Pattern
```python
def update_memory(memory_id, new_content, old_content):
    # Update the memory
    cursor.execute("UPDATE memories SET content = ? WHERE id = ?",
                   (new_content, memory_id))

    # Record history
    cursor.execute("""
        INSERT INTO memory_history (memory_id, old_content, new_content, event, created_at)
        VALUES (?, ?, ?, 'UPDATE', datetime('now'))
    """, (memory_id, old_content, new_content))
```

### Structured Exception Pattern
```python
class SquirrelError(Exception):
    def __init__(self, message, error_code, suggestion=None, details=None):
        self.message = message
        self.error_code = error_code
        self.suggestion = suggestion
        self.details = details or {}
        super().__init__(message)

class MemoryNotFoundError(SquirrelError):
    pass

class ExtractionError(SquirrelError):
    pass

# Usage
raise MemoryNotFoundError(
    message=f"Memory {memory_id} not found",
    error_code="MEM_404",
    suggestion="Check if the memory ID is correct"
)
```

## Conclusion
mem0 is a well-engineered general-purpose memory system for LLM chatbots. However, it solves a fundamentally different problem (explicit API-based memory for conversations) than Squirrel (passive CLI memory for developers).

**Patterns worth stealing:**
1. UUID→integer mapping to prevent LLM hallucination
2. History tracking with old/new content
3. Structured exceptions with codes and suggestions

**Patterns to avoid:**
1. Two LLM calls per memory (expensive)
2. Heavy infrastructure (we're local-first)
3. LLM categorization (we use source-based)
4. Explicit API approach (we're passive)

Their graph memory and reranking are interesting for future consideration, but not needed for v1.
