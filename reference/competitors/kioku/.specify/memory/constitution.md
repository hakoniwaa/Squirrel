# Context Tool - Project Constitution

**Version:** 1.0  
**Date:** 2025-01-15  
**Status:** Foundational

---

## Project Purpose

Context Tool is a personal development tool that provides **persistent, self-enriching context management** for AI coding assistants via the Model Context Protocol (MCP). Our mission is to eliminate context amnesia and enable AI assistants to become progressively smarter about projects over time.

---

## Core Principles

### 1. Transparency First
**Principle:** Users must always understand where AI gets its context and why.

**Guidelines:**
- All context sources must be traceable and visible
- Reasoning for context selection must be exposed
- No black-box behavior in context retrieval or enrichment
- Logs should clearly show what context was loaded, scored, and pruned
- Users can inspect and debug context at any time

**Enforcement:**
- Every context retrieval operation must log its source
- MCP tool responses include metadata about where information came from
- CLI commands (`show`, `status`) provide full visibility into context state

---

### 2. Zero Manual Intervention
**Principle:** Context management must be automatic and invisible during normal coding.

**Guidelines:**
- No manual commands required during active coding sessions
- Auto-detect session start/end without user input
- Auto-save sessions on IDE close or inactivity
- Auto-extract discoveries from sessions
- Auto-generate embeddings in the background
- Only initialization (`init`) and debugging (`show`, `status`) require manual commands

**Enforcement:**
- Session lifecycle managed entirely by MCP connection events
- Background services run without blocking or requiring user interaction
- Users should forget the tool exists during coding

---

### 3. Progressive Intelligence
**Principle:** Context quality must improve over time, not degrade.

**Guidelines:**
- Each session should leave the context richer than it started
- Discoveries must be extracted and persisted
- Embeddings enable semantic search of accumulated knowledge
- No information loss - archive, don't delete
- Past decisions inform future sessions

**Enforcement:**
- Discovery extraction runs after every session
- Context enrichment updates project.yaml with new patterns
- RAG search finds relevant past work automatically
- Archived context remains searchable

---

### 4. Smart Resource Management
**Principle:** Never overwhelm the AI with irrelevant context; never lose important information.

**Guidelines:**
- Context window must stay under 80% capacity
- Score-based pruning removes low-relevance items
- Pruned items archived, not deleted (full content preserved)
- Archived items remain searchable via semantic search
- Dependency-aware file loading (load what's needed, not everything)

**Enforcement:**
- Context scorer runs every 5 minutes
- Pruner activates automatically at 80% threshold
- All pruning decisions are logged and reversible
- RAG search works across active and archived context

---

### 5. Simplicity Over Features
**Principle:** Build the minimum viable tool that solves the core problem excellently.

**Guidelines:**
- MVP scope is sacred - no feature creep
- Every feature must directly serve one of the core workflows
- Prefer simple rules-based solutions over complex AI-driven ones (MVP)
- Defer nice-to-haves to post-MVP (Git integration, web UI, multi-language support)
- TypeScript/JavaScript projects only for MVP

**Enforcement:**
- All feature proposals evaluated against MVP scope in PRD
- Post-MVP features documented but not implemented
- Code reviews reject out-of-scope additions

---

## Technical Standards

### Code Quality

**TypeScript:**
- Strict mode enabled (`strict: true`)
- No `any` types unless absolutely necessary (document why)
- Explicit return types on all public functions
- Interfaces over types for extensibility

**Error Handling:**
- All async operations wrapped in try-catch
- Errors logged with context (what, where, why)
- User-friendly error messages (no raw stack traces to users)
- Custom error classes for different error types

**Testing:**
- Unit tests for all core business logic
- Integration tests for full workflows
- Mock external dependencies (OpenAI, filesystem)
- Target 80%+ code coverage
- Tests run in CI before merge

**Documentation:**
- JSDoc comments on all public APIs
- README with quick start and full command reference
- Architecture documentation in `/docs`
- Inline comments for complex algorithms only

---

### Architecture Patterns

**Separation of Concerns:**
- `/core` - Pure business logic, no I/O
- `/storage` - All database and file operations
- `/mcp` - MCP server protocol handling only
- `/services` - Background jobs and async work
- `/cli` - Command-line interface layer

**Dependency Flow:**
- CLI → Core → Storage
- MCP → Core → Storage
- Services → Core → Storage
- Storage layer never depends on higher layers

**Single Responsibility:**
- Each class/module has one clear purpose
- Keep functions small (<50 lines ideally)
- Extract helper functions for complex logic
- No god objects or manager classes that do everything

---

### Data Management

**Persistence:**
- YAML for human-editable project context
- SQLite for structured session/discovery data
- Chroma for vector embeddings
- No data duplication across stores

**Data Integrity:**
- Validate all YAML with Zod schemas before loading
- Foreign key constraints in SQLite
- Atomic writes (no partial saves)
- Backup project.yaml before enrichment updates

**Performance:**
- Index all frequently queried SQLite columns
- Batch embedding generation (don't call OpenAI per-discovery)
- Cache loaded project context in memory
- Background services don't block main thread

---

### Security & Privacy

**API Keys:**
- Never commit API keys to git
- Use environment variables or config files
- Config files in `.gitignore`
- Clear error messages when keys missing

**User Data:**
- All context stored locally (`.context/` directory)
- No telemetry or data collection
- No external services except OpenAI embeddings
- User owns all data, can delete anytime

**Dependencies:**
- Audit npm packages before adding
- Use only well-maintained, popular packages
- Pin major versions in package.json
- Regular security updates

---

## Development Workflow

### Git Practices

**Branching:**
- `main` branch always stable
- Feature branches: `feature/short-description`
- One feature per branch
- Delete branches after merge

**Commits:**
- Follow conventional commits: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`
- Clear, descriptive commit messages
- Reference issues when applicable

**Pull Requests:**
- One PR per feature/fix
- Description includes context and testing notes
- All tests pass before merge
- Code review required (even for solo project - self-review)

---

### Release Process

**Versioning:**
- Semantic versioning (MAJOR.MINOR.PATCH)
- MVP is 0.1.0 until all features complete
- 1.0.0 when production-ready (after 2-week dogfooding)

**Releases:**
- Tag releases in git
- Generate changelog from commits
- Publish to npm (post-MVP)
- Update documentation with each release

---

## User Experience Principles

### CLI Design

**Commands:**
- Clear, memorable names (`init`, `serve`, `show`, `status`)
- Consistent flag patterns (`--verbose`, `--help`)
- Helpful error messages with suggestions
- Progress indicators for long operations

**Output:**
- Success with checkmarks: `✓ Context initialized`
- Info with icons: `ℹ Press Ctrl+C to stop`
- Errors with clear descriptions: `✗ Error: Missing OPENAI_API_KEY`
- Verbose mode shows debug details

---

### MCP Integration

**Resources:**
- Descriptive URIs: `context://project/overview`
- Markdown formatted for readability
- Concise but complete information
- Always available (no loading states)

**Tools:**
- Clear parameter descriptions
- Examples in tool descriptions
- Fast responses (<2 seconds for search)
- Graceful degradation if service unavailable

---

## Project Constraints

### MVP Scope
**In Scope:**
- TypeScript/JavaScript projects only
- Single-user, local development
- Rules-based discovery extraction
- Basic embeddings (OpenAI text-embedding-3-small)

**Out of Scope (Post-MVP):**
- Multi-language support (Python, Go, etc.)
- Multi-user/team features
- AI-based discovery refinement
- Git tool integration
- Web dashboard UI
- Real-time file watching

---

### Performance Targets

**Initialization:**
- `context-tool init` completes in <2 minutes for 500-file project
- Project scanning uses streaming to avoid memory issues

**Runtime:**
- MCP server starts in <5 seconds
- Context search returns results in <2 seconds
- Background services don't impact IDE performance
- Session auto-save completes in <1 second

**Storage:**
- SQLite database <100MB for typical project
- Embeddings storage <500MB for typical project
- YAML file stays human-readable (<10K lines)

---

## Decision-Making Framework

### When to Add a Feature
1. Does it solve a real pain point from the PRD?
2. Is it in MVP scope?
3. Can it be implemented simply?
4. Does it align with core principles?
5. Will it be used in every session?

**If 4+ are YES → Consider implementation**  
**If <4 are YES → Defer to post-MVP**

### When to Choose a Technology
1. Does it solve the specific problem?
2. Is it well-maintained and popular?
3. Does it add minimal dependencies?
4. Is it TypeScript-compatible?
5. Have we used it successfully before?

**Prefer boring, proven technology over cutting-edge**

### When to Refactor
1. Is the code hard to understand?
2. Are there repeated patterns (DRY violation)?
3. Is a component doing too many things?
4. Are tests brittle or hard to write?
5. Is performance noticeably degraded?

**Refactor when it improves quality, not just aesthetics**

---

## Success Criteria

### MVP is Complete When:

**Functional:**
- ✓ All commands work (`init`, `serve`, `show`, `status`)
- ✓ MCP server connects to Claude Desktop
- ✓ All resources accessible (`context://...`)
- ✓ All tools functional (`context_search`, `read_file`, `grep_codebase`)
- ✓ Sessions tracked and auto-saved
- ✓ Discoveries extracted after sessions
- ✓ Context enriched in project.yaml
- ✓ RAG search returns relevant results
- ✓ Context pruning prevents saturation

**Quality:**
- ✓ 80%+ test coverage
- ✓ All tests passing
- ✓ No critical bugs
- ✓ Documentation complete
- ✓ Can be used on real project (mon-saas)

**Validation:**
- ✓ Used daily for 2 weeks without reverting to manual context
- ✓ AI gives better answers in session 10 vs session 1
- ✓ Zero context window saturation issues
- ✓ Context setup time = 0 minutes

---

## Amendment Process

This constitution is a living document. Changes can be proposed via:

1. Create an issue describing the proposed change and rationale
2. Discuss impact on existing principles and code
3. Update constitution if accepted
4. Update implementation to align with new principle

**Amendments should be rare** - foundational principles should be stable.

---

## Commitment

By contributing to Context Tool, you commit to upholding these principles. When in doubt about a decision, refer to this constitution. If the constitution doesn't provide guidance, propose an amendment.

**Our North Star:** Build a tool that makes AI coding assistants genuinely intelligent about your projects, with zero manual overhead.

---

**END OF CONSTITUTION**
