# Context Tool - Product Requirements Document

**Version:** 1.0  
**Date:** 2025-01-15  
**Author:** Sovanaryth  
**Status:** Draft - Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Problem Statement](#problem-statement)
3. [Solution Overview](#solution-overview)
4. [User Stories](#user-stories)
5. [MVP Features](#mvp-features)
6. [Technical Architecture](#technical-architecture)
7. [Data Models](#data-models)
8. [System Flows](#system-flows)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Success Metrics](#success-metrics)
11. [Future Enhancements](#future-enhancements)

---

## Executive Summary

**Context Tool** is a personal development tool that provides **persistent, self-enriching context management** for AI coding assistants via the Model Context Protocol (MCP).

### Core Value Proposition

Instead of re-explaining project architecture, conventions, and past decisions to AI assistants in every session, Context Tool:
- **Initializes** with a comprehensive project understanding (architecture, stack, modules)
- **Tracks** work sessions and automatically extracts discoveries
- **Enriches** the general context progressively over time
- **Retrieves** relevant context intelligently using RAG (semantic search)
- **Manages** context window efficiently with smart pruning

### Target User

**Primary:** Personal use for a full-stack developer working on multiple TypeScript/React projects  
**Secondary:** Developers who want better AI assistance without constant context repetition

### Success Criteria

- Zero manual context explanation after initial setup
- AI understands project after 5+ sessions better than at session 1
- Context window never saturates (smart pruning works)
- Developer can work seamlessly across multiple sessions

---

## Problem Statement

### Current Pain Points

**1. Context Amnesia**
- AI forgets project structure between sessions
- Must re-explain architecture patterns every time
- Loses track of past decisions and work done

**2. Context Repetition**
- Manually paste same context at start of each session
- Time wasted explaining conventions repeatedly
- Inconsistent context → inconsistent AI responses

**3. Context Window Saturation**
- Loading too much context → window full
- AI loses focus, performance degrades
- No intelligent pruning of irrelevant info

**4. No Learning Over Time**
- Each session starts from scratch
- Past discoveries not retained
- No accumulation of project knowledge

### Impact

- **Time waste:** 10-15 min per session on context setup
- **Frustration:** Repeating same explanations
- **Quality loss:** Inconsistent AI assistance
- **Scaling issue:** More projects = more repetition

---

## Solution Overview

### Approach

**Progressive Disclosure + Persistent Memory**

Context Tool creates a **living context** that:
1. Starts with comprehensive project overview (init)
2. Loads relevant context dynamically (on-demand)
3. Tracks sessions and extracts discoveries automatically
4. Enriches the general context over time
5. Uses RAG to find relevant past context semantically

### Key Principles

**1. Transparency**
- User sees where AI gets its context
- Reasoning exposed for debugging
- No black box behavior

**2. Zero Intervention**
- Auto-save sessions (IDE close, inactivity)
- Auto-extract discoveries (rules + AI)
- Auto-enrich context (background)

**3. Intelligence**
- Smart pruning (score-based, not random)
- Semantic search (RAG, not just grep)
- Dependency-aware file loading

**4. Persistence**
- Context survives across sessions
- Knowledge accumulates over time
- Nothing lost between restarts

---

## User Stories

### Primary Workflows

**Story 1: First-Time Setup**
```
As a developer,
I want to initialize context for my project,
So that AI understands my codebase structure.

Acceptance Criteria:
- Run `context-tool init` in project root
- Tool scans structure, detects stack, identifies modules
- Generates .context/project.yaml with comprehensive overview
- Takes < 2 minutes for typical project
- Can manually edit generated context if needed
```

**Story 2: Daily Coding Session**
```
As a developer,
I want AI to understand my project without manual setup,
So I can focus on coding, not context management.

Acceptance Criteria:
- Open IDE → MCP server auto-starts
- Ask AI "Fix auth bug" → AI has full project context
- AI can search past sessions for relevant info
- AI loads files + dependencies automatically
- Session auto-saves when I close IDE
- Zero manual commands needed
```

**Story 3: Context Grows Over Time**
```
As a developer,
I want the context to learn from my work sessions,
So future sessions are more intelligent.

Acceptance Criteria:
- After session, discoveries extracted automatically
- project.yaml enriched with new patterns/rules
- Embeddings generated for semantic search
- Next session, AI "remembers" past work
- Suggestions improve over time
```

**Story 4: Multi-Day Task**
```
As a developer,
I want to resume work seamlessly,
So I don't lose context between days.

Acceptance Criteria:
- Day 1: Work on auth feature
- Day 2: Ask "Continue auth work" → AI recalls yesterday's context
- Related files, past decisions automatically loaded
- No need to re-explain what was done
```

**Story 5: Context Window Management**
```
As a developer,
I want the AI to stay focused on relevant context,
So it doesn't get overwhelmed with irrelevant info.

Acceptance Criteria:
- Context window never exceeds 80% capacity
- Low-score items archived automatically
- Archived items retrievable via RAG if needed
- No loss of information (full archive, not summary)
- Pruning transparent (can see what was archived)
```

---

## MVP Features

### 5.1 Context Initialization

**Scope:** Auto-scan project and generate initial context

**Features:**
- File structure analysis (tree scanning)
- Tech stack detection (package.json, tsconfig, etc.)
- Architecture pattern inference (folder structure)
- Module identification (domain boundaries)
- Generate `.context/project.yaml`

**Out of Scope (v2+):**
- Guided init with interactive questions
- Deep metadata (LOC, contributors)
- Multi-language support (focus TypeScript/JavaScript MVP)

**Acceptance Criteria:**
- `context-tool init` completes in < 2 min for 500-file project
- Generated YAML contains: project name, type, stack, architecture, modules
- User can manually edit YAML after generation

---

### 5.2 Session Management

**Scope:** Transparent session tracking with auto-save

**Features:**
- Auto-detect session start (IDE open, MCP connection)
- Track files accessed, topics discussed
- Auto-save triggers:
  - IDE closed
  - 30 min inactivity
- Store session metadata in SQLite
- Display reasoning (show context sources)

**Out of Scope (v2+):**
- AI-based task completion detection
- Manual session commands (start/end)
- Session resumption prompts

**Acceptance Criteria:**
- Session tracked silently, no user intervention
- Session saved automatically on IDE close
- Session data includes: files accessed, topic, timestamp
- User can inspect session via `context-tool show`

---

### 5.3 Dynamic Context Discovery

**Scope:** Intelligent context loading with RAG + dependency graph

**Features:**
- **RAG Search:** Semantic search via Chroma vector DB
- **Grep Search:** Textual fallback for exact matches
- **Dependency Graph:** Parse imports, load related files
- **Smart File Loading:** Load file + level 1 dependencies
- **Smart Pruning:** Score-based archiving (preserve full content)

**Out of Scope (v2+):**
- AST-based smart chunking
- Context window re-ranking with boost
- Real-time file watching

**Acceptance Criteria:**
- `context_search("auth")` returns relevant files/sessions
- `read_file("AuthSession.ts")` loads file + direct imports
- Context pruning activates at 80% window capacity
- Archived items still searchable via RAG
- Pruning visible in logs (what was archived, why)

---

### 5.4 Context Enrichment

**Scope:** Auto-extract discoveries and enrich context

**Features:**
- **Discovery Types:** Patterns, business rules, decisions, issues
- **Extraction:** Rules-based (regex patterns for common discoveries)
- **Embeddings:** Generate via OpenAI API (simple text chunks)
- **Enrichment:** Update project.yaml with discoveries
- **Storage:** Save sessions + discoveries in SQLite

**Out of Scope (v2+):**
- AI-based discovery extraction (GPT refinement)
- Smart chunking (AST-aware)
- Cross-session linking visualization

**Acceptance Criteria:**
- After session end, 3-5 discoveries extracted
- project.yaml updated with new patterns/rules
- Embeddings generated and stored in Chroma
- Next session can find past discoveries via RAG

---

### 5.5 MCP Integration

**Scope:** Expose context via Model Context Protocol

**Resources:**
```
context://project/overview       - General project context
context://module/{name}          - Module-specific context
context://session/current        - Active session context
```

**Tools:**
```
context_search(query, type, limit)     - RAG + grep search
read_file(path, includeDeps, depth)    - Read file + dependencies
grep_codebase(pattern, filePattern)    - Textual search
```

**Background Services:**
```
ContextScorer   - Update scores every 5 min
ContextPruner   - Archive low-score items at 80% threshold
SessionAutoSave - Save session on triggers
EmbeddingsGen   - Generate embeddings async
```

**Out of Scope (v2+):**
- Git tools (log, blame, diff)
- File watcher (real-time updates)
- Multi-repo context linking

**Acceptance Criteria:**
- MCP server starts with `context-tool serve`
- Claude Desktop can access all resources via @ mentions
- All tools callable from AI interface
- Background services run without blocking

---

### 5.6 CLI/UX

**Scope:** Essential commands for setup and debugging

**Commands:**
```bash
context-tool init              # Initialize project context
context-tool serve             # Start MCP server
context-tool show              # Display current context
context-tool status            # Check server status
```

**Logging:**
- Verbose mode: `--verbose` flag
- Log levels: info, debug
- Output: stdout (can redirect to file)

**Out of Scope (v2+):**
- Dashboard web UI
- Auto-diagnostics (`doctor` command)
- Session management commands (list, show)
- Maintenance commands (clean, reindex)

**Acceptance Criteria:**
- All commands work as expected
- Verbose logs help debug issues
- Status shows if server running + project loaded

---

## Technical Architecture

### 6.1 System Architecture

```
┌─────────────────────────────────┐
│   MCP Client                    │
│   (Claude Desktop)              │
└──────────────┬──────────────────┘
               │ MCP Protocol
               ↓
┌─────────────────────────────────┐
│   MCP Server                    │
│   - Resources Handler           │
│   - Tools Handler               │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Core Engine                   │
│   - ContextManager              │
│   - SessionManager              │
│   - SearchEngine (RAG+Grep)     │
│   - FileAnalyzer                │
│   - EnrichmentEngine            │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Background Services           │
│   - Scorer, Pruner, AutoSave    │
│   - EmbeddingsGenerator         │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│   Storage Layer                 │
│   - project.yaml (YAML)         │
│   - sessions.db (SQLite)        │
│   - embeddings/ (Chroma)        │
└─────────────────────────────────┘
```

### 6.2 Technology Stack

**Core:**
- Language: TypeScript 5.x
- Runtime: Node.js 18+
- MCP: @modelcontextprotocol/sdk

**Storage:**
- YAML: js-yaml
- SQLite: better-sqlite3
- Vector DB: chromadb (JS client)

**LLM APIs:**
- Embeddings: OpenAI API (text-embedding-3-small)
- Discovery Extraction (optional): Anthropic Claude API

**Code Analysis:**
- AST: @babel/parser (JavaScript/TypeScript)
- Git: simple-git
- Grep: fast-glob

**Utils:**
- Validation: zod
- Logging: winston

---

## Data Models

### 7.1 Project Context (YAML)

```yaml
version: "1.0"
project:
  name: string
  type: "web-app" | "api" | "fullstack"
  created: timestamp
  lastUpdated: timestamp

architecture:
  pattern: string
  layers:
    - name: string
      path: string

stack:
  frontend:
    framework: string
    language: string
  backend:
    framework: string
    language: string

modules:
  [moduleName]:
    description: string
    keyFiles:
      - path: string
        role: string
    patterns: string[]
    businessRules: string[]
    commonIssues:
      - issue: string
        solution: string
        session: string
```

### 7.2 Sessions Database (SQLite)

```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  project_id TEXT,
  topic TEXT,
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  status TEXT,
  summary TEXT
);

CREATE TABLE discoveries (
  id TEXT PRIMARY KEY,
  session_id TEXT,
  type TEXT,
  content TEXT,
  metadata TEXT,
  created_at TIMESTAMP
);

CREATE TABLE files_accessed (
  id INTEGER PRIMARY KEY,
  session_id TEXT,
  filepath TEXT,
  access_count INTEGER,
  last_accessed TIMESTAMP
);

CREATE TABLE context_scores (
  id TEXT PRIMARY KEY,
  item_type TEXT,
  item_id TEXT,
  score REAL,
  last_updated TIMESTAMP
);
```

### 7.3 Vector DB (Chroma)

```typescript
interface EmbeddingDocument {
  document: string;
  embedding: number[];  // 1536 dimensions
  metadata: {
    type: "discovery" | "message" | "code";
    project: string;
    module?: string;
    session?: string;
    filepath?: string;
    date: string;
  };
  id: string;
}
```

---

## System Flows

### 8.1 Initialization Flow

```
User: $ context-tool init

1. ProjectScanner
   - Scan directory tree
   - Detect package.json, tsconfig.json
   - Identify folder patterns

2. ArchitectureDetector
   - Infer architecture from structure
   - Identify modules/domains

3. ContextGenerator
   - Create project.yaml
   - Populate with detected info

4. Storage Setup
   - Create .context/ directory
   - Init sessions.db (SQLite)
   - Init Chroma collection

Output: "Context initialized. Ready to use."
```

### 8.2 Active Session Flow

```
User: Opens Claude Desktop

1. MCP Server starts automatically
   - Load project.yaml
   - Connect to Chroma

User: "Fix auth bug"

2. AI calls: context_search("auth bug")

3. SearchEngine
   - RAG search in Chroma
   - Find relevant discoveries/sessions
   - Return top 5 results

4. AI calls: read_file("AuthSession.ts")

5. FileAnalyzer
   - Read file
   - Parse imports
   - Load level 1 dependencies

6. [Background] ContextScorer
   - Update scores (accessed files = high)

7. [Background] ContextPruner (if > 80%)
   - Archive low-score items

User: Closes IDE

8. SessionAutoSave
   - Detect IDE close
   - Save session to sessions.db
```

### 8.3 Enrichment Flow

```
Trigger: Session end

1. DiscoveryExtractor
   - Scan conversation
   - Apply regex patterns
   - Extract discoveries

2. ContextEnricher
   - Update project.yaml
   - Add discoveries to modules

3. EmbeddingsGenerator (async)
   - Generate embeddings for discoveries
   - Batch insert into Chroma

4. SessionSaver
   - Save to sessions.db
   - Mark session complete
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Goals:**
- Project structure setup
- Storage layer working
- Basic MCP server

**Deliverables:**
- TypeScript project with dependencies installed
- YAML read/write working
- SQLite schema created
- Chroma connection established
- MCP server responds to ping

**Validation:**
- Can write/read project.yaml
- Can insert/query sessions.db
- Can create Chroma collection

---

### Phase 2: Core Logic (Weeks 3-4)

**Goals:**
- Init command functional
- Context loading working
- Basic RAG search

**Deliverables:**
- `context-tool init` scans project
- Generates accurate project.yaml
- MCP resources exposed
- context_search tool working (RAG only)

**Validation:**
- Init creates valid context for test project
- Claude Desktop can read context:// resources
- RAG search returns relevant results

---

### Phase 3: Enrichment (Weeks 5-6)

**Goals:**
- Discovery extraction working
- Embeddings generation
- Background services

**Deliverables:**
- Discovery extraction (rules-based)
- OpenAI embeddings integration
- Auto-save on session end
- Background scorer/pruner

**Validation:**
- Discoveries extracted from test session
- Embeddings stored in Chroma
- Context enriched after session
- Pruning archives items correctly

---

### Phase 4: Polish & Testing (Weeks 7-8)

**Goals:**
- All CLI commands working
- Logging/debugging solid
- Real-world testing

**Deliverables:**
- All MVP commands implemented
- Verbose logging
- Documentation (README)
- Test on real project (mon-saas)

**Validation:**
- Complete workflow: init → sessions → enrichment
- Use tool daily for 1 week
- Identify pain points, iterate
- MVP ready for personal use

---

## Success Metrics

### Quantitative

**Efficiency:**
- Context setup time: 0 min (vs 10-15 min manual)
- Session continuity: 100% (never lose context)
- Context window usage: < 80% (smart pruning works)

**Quality:**
- Discovery extraction: 3-5 per session
- RAG search relevance: Top 3 results useful
- Context enrichment: 10+ new patterns after 5 sessions

### Qualitative

**User Experience:**
- "AI understands my project better over time"
- "I never repeat myself anymore"
- "Context stays manageable, never saturates"

**Workflow:**
- Zero manual context commands during coding
- Transparent (can see where AI gets info)
- Reliable (auto-save never loses work)

### Validation Criteria

**MVP Success = All 3 conditions met:**
1. Used daily for 2+ weeks without reverting to manual context
2. AI gives better answers in session 10 than session 1
3. Zero context window saturation issues

---

## Future Enhancements (v2+)

### High Priority (Post-MVP)

**1. Git Integration**
- Tools: git_log, git_blame, git_diff
- Context from commit history
- "Who wrote this?" queries

**2. Smart Chunking**
- AST-based code chunking
- Function/class level granularity
- Better embedding quality

**3. Multi-Repo Support**
- Context linking between projects
- Workspace management
- Cross-project search

**4. Dashboard UI**
- Web interface for context inspection
- Visualization of dependency graph
- Session timeline

### Medium Priority

**5. Re-ranking & Boost**
- Recency boost for recent files
- Module boost for current module
- User activity boost

**6. File Watcher**
- Real-time change detection
- Auto-invalidate outdated embeddings
- Live dependency graph updates

**7. AI-based Discovery**
- GPT-4 refinement of discoveries
- Smarter pattern detection
- Higher quality enrichment

### Low Priority (Nice-to-Have)

**8. Onboarding & Help**
- Interactive guided setup
- In-app tutorials
- Better error messages

**9. Advanced Diagnostics**
- `context-tool doctor` command
- Auto-fix common issues
- Health checks

**10. Multi-Language Support**
- Python, Go, Rust, etc.
- Language-specific patterns
- Polyglot projects

---

## Appendix A: Environment Setup

### Prerequisites
```bash
Node.js >= 18
npm or pnpm
API Keys:
  - ANTHROPIC_API_KEY (optional, for AI enrichment)
  - OPENAI_API_KEY (required, for embeddings)
```

### Installation (Future)
```bash
npm install -g context-tool
context-tool init
context-tool serve
```

### Configuration
```bash
# ~/.context-tool/config.yaml (optional)
embeddings:
  provider: "openai"
  apiKey: "${OPENAI_API_KEY}"
  
llm:
  provider: "anthropic"
  apiKey: "${ANTHROPIC_API_KEY}"
```

---

## Appendix B: Glossary

**Context:** Information about a project that helps AI understand the codebase

**Session:** A period of work tracked by the tool (e.g., one coding session)

**Discovery:** Knowledge extracted from a session (pattern, rule, decision)

**Enrichment:** Process of updating project context with new discoveries

**RAG (Retrieval-Augmented Generation):** Semantic search using embeddings

**Pruning:** Archiving low-relevance items to manage context window

**MCP (Model Context Protocol):** Standard for connecting AI to tools/data

**Embedding:** Vector representation of text for semantic search

---

## Document Control

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | Sovanaryth | Initial PRD - MVP scope defined |

**Approval:**

| Role | Name | Status | Date |
|------|------|--------|------|
| Product Owner | Sovanaryth | ✅ Approved | 2025-01-15 |

---

**END OF DOCUMENT**