# Context Tool - Functional Specification

**Feature Name:** Context Tool MVP  
**Version:** 1.0  
**Date:** 2025-01-15  
**Status:** Ready for Planning

---

## Overview

### What We're Building

Context Tool is a persistent, self-enriching context management system for AI coding assistants. It solves the "context amnesia" problem where AI assistants forget project structure, conventions, and past decisions between sessions.

**Core Value:** Zero manual context management while AI gets progressively smarter about your project.

### Why We're Building It

**Current Pain:**
- Spend 10-15 minutes every session explaining project structure to AI
- AI forgets past decisions and conversations
- Context window saturates with too much information
- No learning across sessions - start from scratch every time

**Impact:**
- Wasted time on repetitive explanations
- Inconsistent AI responses
- Frustration with "dumb" AI behavior
- Doesn't scale to multiple projects

### Success Metrics

**Quantitative:**
- Context setup time: 0 min (down from 10-15 min)
- Session continuity: 100% (never lose context)
- Context window usage: <80% always
- Discovery extraction: 3-5 per session

**Qualitative:**
- AI understands project better in session 10 vs session 1
- Users never need to repeat themselves
- Seamless workflow - tool is invisible during coding

---

## User Stories

### Epic 1: Project Initialization

#### User Story 1.1: Quick Setup
**As a** developer starting with Context Tool  
**I want to** initialize my project with one command  
**So that** AI understands my codebase structure immediately

**Acceptance Criteria:**
- [ ] Run `context-tool init` in project root
- [ ] Tool scans directory structure in <2 minutes
- [ ] Detects tech stack automatically (Next.js, React, Express, etc.)
- [ ] Identifies architecture pattern from folder structure
- [ ] Detects modules/domains (auth, users, payments, etc.)
- [ ] Generates `.context/project.yaml` with all findings
- [ ] User can manually edit YAML if needed
- [ ] Creates SQLite database for sessions
- [ ] Initializes Chroma vector database
- [ ] Output shows success with summary

**Example Flow:**
```bash
$ cd ~/projects/my-saas
$ context-tool init

✓ Scanning project structure...
✓ Detected: Next.js 14 + Express + TypeScript
✓ Found 3 modules: auth, users, payments
✓ Generated .context/project.yaml
✓ Initialized databases
✓ Context initialized! Run 'context-tool serve' to start.
```

---

### Epic 2: Daily Coding Sessions

#### User Story 2.1: Automatic Context Loading
**As a** developer using Claude Desktop  
**I want** AI to have full project context automatically  
**So that** I can focus on coding, not context management

**Acceptance Criteria:**
- [ ] Open Claude Desktop → MCP server auto-starts
- [ ] MCP server loads project.yaml into memory
- [ ] Resources available: `context://project/overview`, `context://module/{name}`, `context://session/current`
- [ ] AI can access resources via @ mentions
- [ ] No manual setup needed
- [ ] Server logs show successful initialization

**Example Flow:**
```
User: Opens Claude Desktop
      (MCP server starts in background)

User: "@context How does our auth work?"
Claude: [Reads context://module/auth]
        "Your auth module uses JWT tokens with httpOnly cookies..."
```

---

#### User Story 2.2: Intelligent Context Search
**As a** developer asking AI about past work  
**I want** AI to find relevant past context semantically  
**So that** I get accurate answers based on previous sessions

**Acceptance Criteria:**
- [ ] AI can use `context_search(query)` tool
- [ ] Tool performs semantic search via RAG (embeddings)
- [ ] Returns top 5 most relevant results
- [ ] Results include discoveries, sessions, and code snippets
- [ ] Falls back to grep for exact matches when embeddings not yet generated (cold start scenario only)
- [ ] Response includes metadata (source, date, relevance score)
- [ ] Search completes in <2 seconds

**Example Flow:**
```
User: "What did we decide about token refresh?"
Claude: [Calls context_search("token refresh JWT")]
        [Receives discovery from session-123]
        "In session from 2025-01-18, you decided to use a mutex lock 
         to prevent token refresh race conditions..."
```

---

#### User Story 2.3: Smart File Loading
**As a** developer asking AI to modify a file  
**I want** AI to load the file with its dependencies automatically  
**So that** AI has full context for making changes

**Acceptance Criteria:**
- [ ] AI can use `read_file(path, includeDeps)` tool
- [ ] Tool reads target file content
- [ ] Parses imports/requires using Babel parser
- [ ] Optionally loads level 1 dependencies
- [ ] Returns file content with dependency tree
- [ ] Tracks file access for scoring
- [ ] Handles errors gracefully (file not found, parse errors)

**Example Flow:**
```
User: "Fix the bug in AuthService.ts"
Claude: [Calls read_file("src/server/auth/AuthService.ts", includeDeps=true)]
        [Receives AuthService.ts + TokenManager.ts + UserRepository.ts]
        "I see the issue in AuthService.ts line 45..."
```

---

#### User Story 2.4: Session Auto-Save
**As a** developer closing my IDE  
**I want** my session to be saved automatically  
**So that** I never lose context between work sessions

**Acceptance Criteria:**
- [ ] Session tracked from MCP connection start
- [ ] Files accessed logged to database
- [ ] Topics discussed tracked
- [ ] Auto-save triggers:
  - IDE closed (MCP disconnection)
  - 30 minutes of inactivity
- [ ] Session saved to SQLite with metadata
- [ ] Background discovery extraction starts
- [ ] User sees no prompts or confirmation dialogs

**Example Flow:**
```
User: Working on auth feature for 2 hours
      Accesses: AuthService.ts (5x), TokenManager.ts (3x)
      Closes VS Code at end of day

System: [Detects MCP disconnection]
        [Saves session to database]
        [Status: active → completed]
        [Triggers discovery extraction]
        (All happens silently)
```

---

### Epic 3: Context Enrichment

#### User Story 3.1: Discovery Extraction
**As a** developer finishing a work session  
**I want** the system to extract learnings automatically  
**So that** future sessions benefit from past work

**Acceptance Criteria:**
- [ ] Runs automatically after session ends
- [ ] Scans session conversation history
- [ ] Applies regex patterns to find discoveries:
  - Patterns: "we use X for Y"
  - Business rules: "must always Z"
  - Decisions: "decided to use A"
  - Issues: "bug with B, fixed by C"
- [ ] Extracts 3-5 discoveries per session
- [ ] Stores in database with metadata
- [ ] Generates embeddings for each discovery
- [ ] No user interaction required

**Example Discoveries:**
```
Pattern: "Use JWT tokens stored in httpOnly cookies for auth"
Business Rule: "Sessions must expire after 7 days"
Decision: "Switched from localStorage to httpOnly cookies for security"
Issue: "Token refresh race condition fixed with mutex lock"
```

---

#### User Story 3.2: Context Enrichment
**As a** developer using the tool over multiple sessions  
**I want** the project context to get richer over time  
**So that** AI gives better answers as I work more

**Acceptance Criteria:**
- [ ] Runs after discovery extraction
- [ ] Loads current project.yaml
- [ ] Maps discoveries to relevant modules
- [ ] Updates module patterns, rules, issues
- [ ] Deduplicates similar discoveries
- [ ] Preserves existing context
- [ ] Saves updated project.yaml
- [ ] Logs all changes made

**Example Enrichment:**
```yaml
# Before (Day 1)
modules:
  auth:
    description: "Authentication module"
    keyFiles:
      - path: "src/server/auth/AuthService.ts"

# After (Day 5)
modules:
  auth:
    description: "Authentication module"
    keyFiles:
      - path: "src/server/auth/AuthService.ts"
      - path: "src/server/auth/TokenManager.ts"
    patterns:
      - "Use JWT tokens in httpOnly cookies"
      - "Implement token refresh with mutex locks"
    businessRules:
      - "Sessions expire after 7 days"
      - "Require 2FA for admin users"
    commonIssues:
      - issue: "Token refresh race condition"
        solution: "Use mutex lock in TokenManager"
        session: "session-123"
```

---

### Epic 4: Context Management

#### User Story 4.1: Smart Context Window Management
**As a** developer working on a large project  
**I want** the system to manage context window automatically  
**So that** AI never gets overwhelmed with information

**Acceptance Criteria:**
- [ ] Context scorer runs every 5 minutes
- [ ] Scores all loaded context items:
  - Recency: Recently accessed = higher score
  - Access count: Frequently accessed = higher score
- [ ] Monitors context window usage (token count)
- [ ] Pruner activates at 80% capacity
- [ ] Archives bottom 20% by score
- [ ] Archived items stored in database (full content)
- [ ] Archived items remain searchable via RAG
- [ ] Pruning logged with reasons

**Scoring Formula:**
```
Score = (0.6 × recency_factor) + (0.4 × access_factor)

Where:
- recency_factor = days_since_access / 30 (capped at 1.0)
- access_factor = access_count / max_access_count (normalized 0-1)
```

**Example Pruning:**
```
Context Window: 82% full (82,000 / 100,000 tokens)
Pruner: Activated

Archived:
- old-module.md (score: 0.12, last accessed 25 days ago)
- unused-component.tsx (score: 0.18, accessed 1x)
- legacy-config.ts (score: 0.21, last accessed 20 days ago)

Result: Context Window: 64% full
```

---

#### User Story 4.2: Context Inspection
**As a** developer debugging context issues  
**I want** to see what context is loaded  
**So that** I can verify the system is working correctly

**Acceptance Criteria:**
- [ ] Run `context-tool show` command
- [ ] Displays current project info
- [ ] Shows loaded modules
- [ ] Lists active session details
- [ ] Shows recent discoveries count
- [ ] Displays context window usage percentage
- [ ] Optional flags: `--module <name>`, `--sessions`, `--stats`

**Example Output:**
```bash
$ context-tool show

Project: My SaaS App (fullstack)
Stack: Next.js 14 + Express + TypeScript
Architecture: Feature-based modular

Modules (3):
  ✓ auth - Authentication and authorization
  ✓ users - User management  
  ✓ payments - Payment processing

Active Session: session-abc123 (started 2h ago)
Files Accessed: 8 (AuthService.ts, TokenManager.ts, ...)

Discoveries: 47 total
  - 18 patterns
  - 12 business rules
  - 10 decisions
  - 7 issues resolved

Context Usage: 65% (65,000 / 100,000 tokens)
```

---

### Epic 5: MCP Integration

#### User Story 5.1: Resource Access
**As a** Claude Desktop user  
**I want** to access project context via @ mentions  
**So that** I can give AI specific context on demand

**Acceptance Criteria:**
- [ ] Resource: `context://project/overview`
  - Contains project name, type, stack, architecture
  - Formatted as readable markdown
- [ ] Resource: `context://module/{name}`  
  - Contains module description, key files, patterns, rules
  - Includes common issues and solutions
- [ ] Resource: `context://session/current`
  - Shows active session info
  - Lists files accessed and topics
- [ ] All resources return valid markdown
- [ ] Handle resource not found gracefully

---

#### User Story 5.2: Tool Invocation
**As a** Claude Desktop user  
**I want** AI to use context tools automatically  
**So that** I get intelligent responses without manual tool calls

**Acceptance Criteria:**
- [ ] Tool: `context_search(query, type?, limit?)`
  - Semantic search via embeddings
  - Type filter: all, discovery, session, code
  - Returns ranked results
- [ ] Tool: `read_file(path, includeDeps?, depth?)`
  - Reads file content
  - Optionally includes dependencies
  - Tracks access for scoring
- [ ] Tool: `grep_codebase(pattern, filePattern?)`
  - Text search with regex
  - File pattern filtering
  - Fast results: <1 second (p95) for typical 500-file project
- [ ] All tools log usage
- [ ] All tools handle errors gracefully

---

## Functional Requirements

### FR-1: Project Scanning
**Description:** Analyze project structure and generate initial context

**Requirements:**
- Scan directory tree recursively
- Ignore: node_modules, .git, dist, build, .next
- Detect tech stack from:
  - package.json dependencies
  - tsconfig.json / jsconfig.json
  - Framework-specific files (next.config.js, etc.)
- Infer architecture from folder patterns:
  - `/components` → Component-based
  - `/features` → Feature-based
  - `/server` + `/client` → Client-server
- Identify modules by folder structure
- Complete in <2 minutes for 500-file project

---

### FR-2: Session Tracking
**Description:** Monitor coding sessions transparently

**Requirements:**
- Detect session start: MCP connection established
- Detect session end: 
  - MCP disconnection
  - 30 minutes inactivity
- Track per session:
  - Files accessed (path + count)
  - Topics discussed (derived from queries)
  - Start/end timestamps
- Store in SQLite with unique session ID
- No UI prompts or confirmations

---

### FR-3: Discovery Extraction
**Description:** Extract learnings from session automatically

**Requirements:**
- Trigger: Session end
- Process: Scan all session messages
- Regex patterns:
  - Pattern: `/(?:we use|pattern is|convention:)\s+(.+)/i`
  - Rule: `/(?:rule:|must always|requirement:)\s+(.+)/i`
  - Decision: `/(?:decided to|chose|went with)\s+(.+)/i`
  - Issue: `/(?:bug:|issue:|fixed:)\s+(.+)/i`
- Extract 3-5 discoveries per session
- Store with metadata: type, content, session_id, timestamp
- No AI calls (rules-based only for MVP)

---

### FR-4: Context Enrichment
**Description:** Update project.yaml with new discoveries

**Requirements:**
- Trigger: After discovery extraction
- Load current project.yaml
- Map discoveries to modules (by file path or keywords)
- Update relevant sections:
  - Add new patterns
  - Add new business rules
  - Add new common issues with solutions
- Deduplicate similar entries
- Preserve existing structure and content
- Save atomically (backup before write)
- Log all changes

---

### FR-5: Semantic Search (RAG)
**Description:** Find relevant context via embeddings

**Requirements:**
- Input: Search query string
- Process:
  1. Generate query embedding (OpenAI API)
  2. Search Chroma vector DB
  3. Return top 5 results by similarity score
- Filter by type if specified (discovery, session, code)
- Include metadata: type, source, date, score
- Complete in <2 seconds
- Fallback to grep if embeddings unavailable

---

### FR-6: Context Scoring
**Description:** Calculate relevance scores for context items

**Requirements:**
- Run every 5 minutes (background service)
- Score formula:
  - `Score = (0.6 × recency) + (0.4 × access_count)`
  - Recency: 1.0 for today, decays to 0.0 over 30 days
  - Access count: Normalized to 0-1 range
- Store scores in database
- Update on every file access

---

### FR-7: Context Pruning
**Description:** Archive low-score items to manage window size

**Requirements:**
- Trigger: Context window > 80% capacity
- Calculate token count for all loaded context
- Sort items by score (ascending)
- Archive bottom 20%:
  - Mark as archived in database
  - Remove from active context
  - Keep full content (no summarization)
  - Keep in Chroma with archived flag
- Log what was archived and why
- Items still searchable via RAG

---

### FR-8: Embeddings Generation
**Description:** Create vector embeddings for semantic search

**Requirements:**
- Trigger: After discovery extraction (async)
- Use OpenAI API: text-embedding-3-small
- Process discoveries in batches (max 100)
- Store in Chroma with metadata:
  - type: discovery
  - project: project name
  - module: module name
  - session: session ID
  - date: creation date
- Handle rate limits and errors gracefully
- Retry failed embeddings

---

### FR-9: File Analysis
**Description:** Parse file imports and build dependency tree

**Requirements:**
- Parse TypeScript/JavaScript with Babel parser
- Extract import statements
- Resolve relative paths to absolute
- Build dependency graph (level 1 only for MVP)
- Return file content + dependencies
- Handle syntax errors gracefully
- Support: .ts, .tsx, .js, .jsx files

---

### FR-10: Configuration Management
**Description:** Load and validate configuration

**Requirements:**
- Load from: `~/.context-tool/config.yaml` (optional)
- Override with environment variables
- Required: OPENAI_API_KEY
- Optional: ANTHROPIC_API_KEY (for future AI extraction)
- Defaults for all settings
- Validate with Zod schema
- Clear error messages for missing keys

---

## Non-Functional Requirements

### Performance
- **Initialization:** <2 min for 500-file project
- **MCP Server Start:** <5 seconds
- **Context Search:** <2 seconds
- **Session Auto-Save:** <1 second
- **Background Services:** No impact on IDE performance

### Reliability
- **Data Persistence:** All sessions and discoveries persisted
- **Error Recovery:** Graceful handling of API failures
- **No Data Loss:** Archive, never delete context

### Usability
- **Zero Configuration:** Works with defaults after init
- **Clear Feedback:** All commands show success/error clearly
- **Transparency:** User can inspect all context via CLI

### Maintainability
- **Code Coverage:** 90%+ test coverage (exceeds constitution's 80% baseline for higher quality assurance)
- **Documentation:** Complete API docs and user guides
- **Logging:** All operations logged with context

### Security
- **API Keys:** Never committed, only in env vars or config
- **Local Storage:** All data stored locally, no external services (except OpenAI)
- **No Telemetry:** Zero data collection

---

## Out of Scope (Post-MVP)

### Explicitly NOT in MVP
- Git integration (git_log, git_blame, git_diff tools)
- AI-based discovery extraction (GPT-4 refinement)
- AST-based smart chunking
- Real-time file watching
- Multi-language support (Python, Go, Rust, etc.)
- Multi-user/team features
- Web dashboard UI
- Cross-project context linking
- Re-ranking with boost factors
- Advanced diagnostics (doctor command)
- Session management commands (list, show, resume)

---

## Dependencies & Assumptions

### Technical Dependencies
- Bun 1.0+ (Note: Originally scoped for Node.js, but Bun selected during technical planning for superior performance—3-6x faster SQLite, native TypeScript support. See research.md for rationale.)
- TypeScript 5.x
- MCP SDK (@modelcontextprotocol/sdk)
- SQLite (bun:sqlite built-in—no npm package needed)
- Chroma (chromadb)
- OpenAI API (embeddings)
- Babel parser (AST analysis)

### Assumptions
- User has Claude Desktop installed
- User works on TypeScript/JavaScript projects
- User has OpenAI API key
- Projects have standard structure (src/, package.json)
- Single user, local development only

---

## System Flows

### Flow 1: Initialization Flow

**Trigger:** User runs `context-tool init`

**Sequence:**
1. **ProjectScanner**
   - Scan directory tree recursively
   - Ignore: node_modules, .git, dist, build
   - Detect package.json, tsconfig.json
   - Identify folder patterns

2. **ArchitectureDetector**
   - Infer architecture from structure
   - Identify modules/domains

3. **ContextGenerator**
   - Create project.yaml with detected info
   - Populate: name, type, stack, architecture, modules

4. **Storage Setup**
   - Create `.context/` directory
   - Initialize sessions.db (SQLite)
   - Initialize Chroma collection

**Output:** "Context initialized. Ready to use."

**Time:** <2 minutes for 500-file project

---

### Flow 2: Active Session Flow

**Trigger:** User opens Claude Desktop

**Sequence:**
1. **MCP Server Auto-Start**
   - Load project.yaml into memory
   - Connect to Chroma vector DB
   - Start background services

2. **User Query:** "Fix auth bug"

3. **AI Tool Call:** `context_search("auth bug")`

4. **SearchEngine**
   - Generate query embedding (OpenAI)
   - RAG search in Chroma
   - Find relevant discoveries/sessions
   - Return top 5 results

5. **AI Tool Call:** `read_file("AuthSession.ts")`

6. **FileAnalyzer**
   - Read file content
   - Parse imports (Babel)
   - Load level 1 dependencies

7. **[Background] ContextScorer**
   - Update scores for accessed files
   - Calculate: (0.6 × recency) + (0.4 × access_count)

8. **[Background] ContextPruner (if > 80%)**
   - Archive low-score items
   - Remove from active context
   - Keep searchable in Chroma

9. **User:** Closes IDE

10. **SessionAutoSave**
    - Detect MCP disconnection
    - Save session to sessions.db
    - Trigger discovery extraction

---

### Flow 3: Enrichment Flow

**Trigger:** Session end (IDE close or 30min inactivity)

**Sequence:**
1. **DiscoveryExtractor**
   - Scan session conversation history
   - Apply regex patterns:
     - Pattern: `/(?:we use|pattern is|convention:)\s+(.+)/i`
     - Rule: `/(?:rule:|must always|requirement:)\s+(.+)/i`
     - Decision: `/(?:decided to|chose|went with)\s+(.+)/i`
     - Issue: `/(?:bug:|issue:|fixed:)\s+(.+)/i`
   - Extract 3-5 discoveries
   - Store in discoveries table

2. **ContextEnricher**
   - Load current project.yaml
   - Map discoveries to modules (by filepath/keywords)
   - Update relevant sections:
     - Add patterns
     - Add business rules
     - Add common issues with solutions
   - Deduplicate similar entries
   - Save updated project.yaml atomically

3. **EmbeddingsGenerator (async, background)**
   - Process discoveries in batches (max 100)
   - Generate embeddings via OpenAI API
   - Store in Chroma with metadata:
     - type, project, module, session, date
   - Handle rate limits with retry logic

4. **SessionSaver**
   - Mark session status: active → completed
   - Save final metadata
   - Log completion

**Result:** Context enriched, ready for next session

---

## Testing Strategy

### Unit Tests
- All core logic functions (scoring, extraction, enrichment)
- Storage layer (YAML, SQLite, Chroma)
- Regex pattern matching
- Dependency parsing

### Integration Tests
- Full workflow: init → serve → search → enrich
- Session lifecycle
- MCP resource access
- MCP tool execution

### Manual Testing
- Real-world usage on mon-saas project
- 1-week dogfooding period
- Metrics collection (time saved, discoveries extracted)

---

## Acceptance Criteria

### MVP is Complete When:

**Functional:**
- ✅ All user stories implemented
- ✅ All functional requirements met
- ✅ All commands work (`init`, `serve`, `show`, `status`)
- ✅ MCP integration functional (resources + tools)
- ✅ Sessions tracked and enriched

**Quality:**
- ✅ 90%+ test coverage
- ✅ All tests passing
- ✅ No critical bugs
- ✅ Documentation complete

**Validation:**
- ✅ Used on real project for 2 weeks
- ✅ AI improves over time (session 10 > session 1)
- ✅ Zero manual context management needed
- ✅ No context window saturation issues

---

## Clarifications

### Questions to Resolve Before Planning

1. **Embedding Model:** Stick with text-embedding-3-small or consider alternatives?
   - **Decision:** Use text-embedding-3-small (1536 dimensions, good cost/performance)

2. **Context Window Size:** Assume 100k tokens or configurable?
   - **Decision:** Start with 100k, make configurable in post-MVP

3. **Pruning Threshold:** 80% fixed or user-adjustable?
   - **Decision:** Fixed at 80% for MVP, configurable in post-MVP

4. **Discovery Extraction:** Only rules-based or allow AI fallback?
   - **Decision:** Rules-based only for MVP (no AI calls for extraction)

5. **File Types:** Only .ts/.tsx/.js/.jsx or include .json/.yaml?
   - **Decision:** Code files only for MVP; add config files in post-MVP

---

## Review & Acceptance Checklist

**Pre-Planning Validation:**
- [ ] All user stories have clear acceptance criteria
- [ ] All functional requirements are testable
- [ ] Non-functional requirements have measurable targets
- [ ] Dependencies and assumptions documented
- [ ] Out-of-scope items clearly defined
- [ ] Questions resolved or deferred appropriately

**Stakeholder Sign-off:**
- [ ] Product Owner reviewed and approved
- [ ] Technical Lead reviewed architecture implications
- [ ] All ambiguities clarified

---

**END OF SPECIFICATION**
