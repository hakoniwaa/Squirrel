# Kioku - AI Development Guide

**Version:** 1.0.0
**Editor:** Zed with Claude Code / Claude Desktop
**Runtime:** Bun
**Status:** MVP Complete - Ready for Dogfooding

---

## Project Overview

**Kioku** (記憶, "memory") is an MCP (Model Context Protocol) server that provides persistent, self-enriching context management for AI coding assistants.

**What this is:**
- An MCP stdio server (NOT a web app, NOT a GUI)
- A CLI tool for initialization and debugging
- Background services for context scoring, pruning, and enrichment
- Local-first data storage (no cloud services except OpenAI/Anthropic APIs)

**What problem it solves:**
- AI assistants forget project context between sessions
- Developers waste 10-15 minutes per session re-explaining architecture
- Context windows saturate with irrelevant information
- No learning accumulation across coding sessions

**Core Value:** Zero manual context management while AI gets progressively smarter about your project.

---

## Essential Reading (READ THESE FIRST!)

Before doing ANY work on this project, you MUST read these documents in order:

1. **`.specify/memory/constitution.md`** (CRITICAL - READ FIRST)
   - Project principles: Transparency, Zero Intervention, Progressive Intelligence, Simplicity
   - Code standards, architecture patterns, decision frameworks
   - Non-negotiable constraints and guidelines

2. **`.specify/specs/001-context-tool-mvp/spec.md`**
   - User stories with acceptance criteria
   - Functional requirements (FR-1 through FR-10)
   - Data models, system flows, success metrics

3. **`.specify/specs/001-context-tool-mvp/plan.md`** (if exists)
   - Technical implementation plan
   - Architecture decisions with rationale
   - Data models, API contracts, implementation phases

4. **`.specify/specs/001-context-tool-mvp/tasks.md`** (if exists)
   - Task breakdown with dependencies
   - Acceptance criteria per task
   - Test requirements

---

## Available Slash Commands

You have access to these commands for structured development:

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/constitution` | Create/update project principles | Once at start, rarely updated |
| `/specify` | Define WHAT to build (requirements) | After constitution, before planning |
| `/clarify` | Ask questions to fill gaps in spec | After /specify, before /plan |
| `/plan` | Define HOW to build (technical) | After spec is clear |
| `/tasks` | Break plan into actionable tasks | After plan is complete |
| `/analyze` | Validate spec ↔ plan ↔ tasks consistency | After /tasks, before /implement |
| `/implement` | Execute all tasks, build the feature | After validation passes |

**Current Phase:** Ready for `/plan` (constitution.md ✅, spec.md ✅)

---

## Project Structure

```
context-tool/
├── .specify/                       # Spec-Driven Development files
│   ├── memory/
│   │   └── constitution.md         # Project principles (READ FIRST!)
│   ├── specs/
│   │   └── 001-context-tool-mvp/
│   │       ├── spec.md             # Feature specification
│   │       ├── plan.md             # Technical plan (you'll create)
│   │       └── tasks.md            # Task breakdown (you'll create)
│   ├── scripts/                    # Helper bash/PowerShell scripts
│   └── templates/                  # Document templates
│
├── src/                            # Source code (create during /implement)
│   ├── domain/                     # 🟢 Pure business logic (INNERMOST)
│   │   ├── models/                 # Data structures, types
│   │   ├── calculations/           # Pure functions (no I/O)
│   │   └── rules/                  # Business rules (pure)
│   │
│   ├── application/                # 🟡 Application logic (MIDDLE)
│   │   ├── use-cases/              # Orchestrate domain logic
│   │   ├── services/               # Application services
│   │   └── ports/                  # Interfaces for adapters
│   │
│   ├── infrastructure/             # 🔴 External world (OUTERMOST)
│   │   ├── storage/                # Database, file I/O
│   │   ├── mcp/                    # MCP server, protocol
│   │   ├── cli/                    # Command-line interface
│   │   ├── background/             # Background services
│   │   └── external/               # OpenAI, Anthropic APIs
│   │
│   └── shared/                     # Utilities, types, constants
│       ├── types/                  # Shared TypeScript types
│       ├── utils/                  # Pure utility functions
│       └── errors/                 # Custom error classes
│
├── tests/
│   ├── unit/                       # Unit tests (mirror src/)
│   └── integration/                # Integration tests
│
├── package.json
├── tsconfig.json
├── bunfig.toml                     # Bun configuration
└── README.md
```

---

## Onion Architecture & Functional Programming

This project follows **Onion Architecture** with a **functional programming mindset** inspired by *Grokking Simplicity*.

### Layer Structure (Inside → Out)

```
┌─────────────────────────────────────────────────┐
│  Infrastructure (🔴 I/O Layer)                  │
│  - Storage, MCP, CLI, Background Services       │
│  - Side effects, external systems               │
│  - Depends on: Application + Domain             │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │  Application (🟡 Orchestration)           │  │
│  │  - Use cases, application services        │  │
│  │  - Coordinates domain logic               │  │
│  │  - Depends on: Domain only                │  │
│  │                                            │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  Domain (🟢 Pure Business Logic)    │  │  │
│  │  │  - Models, calculations, rules       │  │  │
│  │  │  - Pure functions, no I/O            │  │  │
│  │  │  - Depends on: Nothing              │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### Dependency Rule (CRITICAL!)

**Dependencies only point INWARD:**
- 🔴 Infrastructure → Application → Domain
- 🟡 Application → Domain
- 🟢 Domain → Nothing (completely independent)

**NEVER:**
- Domain imports from Application or Infrastructure ❌
- Application imports from Infrastructure ❌

### Functional Programming Principles (from Grokking Simplicity)

#### 1. **Separate Actions, Calculations, and Data**

**Data (Pure data structures):**
```typescript
// src/domain/models/ProjectContext.ts
export interface ProjectContext {
  version: string;
  project: {
    name: string;
    type: 'web-app' | 'api' | 'fullstack';
  };
  modules: Record<string, ModuleContext>;
}
```

**Calculations (Pure functions - no I/O):**
```typescript
// src/domain/calculations/context-scoring.ts
export function calculateContextScore(
  lastAccessedAt: Date,
  accessCount: number,
  now: Date = new Date()
): number {
  const recencyFactor = calculateRecencyFactor(lastAccessedAt, now);
  const accessFactor = normalizeAccessCount(accessCount);
  return 0.6 * recencyFactor + 0.4 * accessFactor;
}

// Pure - given same inputs, always returns same output
// No side effects, no I/O, easily testable
```

**Actions (Functions with side effects):**
```typescript
// src/infrastructure/storage/yaml-handler.ts
export async function saveProjectContext(
  context: ProjectContext,
  path: string
): Promise<void> {
  // I/O operation - writes to filesystem
  const yaml = stringify(context);
  await writeFile(path, yaml);
}
```

#### 2. **Prefer Immutability**

```typescript
// ✅ GOOD - Pure, immutable
export function enrichContext(
  context: ProjectContext,
  discoveries: Discovery[]
): ProjectContext {
  return {
    ...context,
    modules: {
      ...context.modules,
      [moduleName]: enrichModule(context.modules[moduleName], discoveries)
    }
  };
}

// ❌ BAD - Mutates input
export function enrichContext(
  context: ProjectContext,
  discoveries: Discovery[]
): void {
  context.modules[moduleName].patterns.push(...newPatterns); // mutation!
}
```

#### 3. **Stratified Design**

Organize code in layers of abstraction:

```typescript
// Layer 1: Low-level primitives (domain/calculations)
function normalizeScore(value: number, max: number): number;

// Layer 2: Domain operations (domain/rules)
function shouldPruneItem(score: number, threshold: number): boolean;

// Layer 3: Use cases (application/use-cases)
function pruneContextWindow(items: ContextItem[]): ContextItem[];

// Layer 4: Infrastructure (infrastructure/background)
class ContextPrunerService {
  async run(): Promise<void>; // Uses layer 3
}
```

#### 4. **Push Side Effects to the Edges**

```typescript
// ✅ GOOD - Pure core, side effects at edges

// Domain (Pure)
export function extractDiscoveries(
  messages: string[],
  patterns: RegExp[]
): Discovery[] {
  // Pure logic, no I/O
}

// Application (Orchestration)
export function extractSessionDiscoveries(
  sessionId: string,
  messages: string[]
): Discovery[] {
  const patterns = DISCOVERY_PATTERNS;
  return extractDiscoveries(messages, patterns);
}

// Infrastructure (Side effects)
export async function extractAndSaveDiscoveries(
  sessionId: string
): Promise<void> {
  const messages = await loadSessionMessages(sessionId); // I/O
  const discoveries = extractSessionDiscoveries(sessionId, messages);
  await saveDiscoveries(discoveries); // I/O
}
```

#### 5. **Copy-on-Write for Updates**

```typescript
// ✅ GOOD - Returns new object
export function updateModulePatterns(
  module: ModuleContext,
  newPatterns: string[]
): ModuleContext {
  return {
    ...module,
    patterns: [...module.patterns, ...newPatterns]
  };
}

// ❌ BAD - Mutates
export function updateModulePatterns(
  module: ModuleContext,
  newPatterns: string[]
): void {
  module.patterns.push(...newPatterns);
}
```

---

## Code Standards & Conventions

### TypeScript

**Strict Mode (Mandatory):**
```typescript
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

**No `any` Types:**
```typescript
// ❌ NEVER do this
function process(data: any): any { }

// ✅ ALWAYS be explicit
function process(data: ProjectContext): Result<ProjectContext, Error> { }
```

**Explicit Return Types:**
```typescript
// ✅ GOOD - Return type declared
export function calculateScore(item: ContextItem): number {
  return 0.6 * item.recency + 0.4 * item.accessCount;
}

// ❌ BAD - No return type
export function calculateScore(item: ContextItem) {
  return 0.6 * item.recency + 0.4 * item.accessCount;
}
```

**Functional Style:**
```typescript
// ✅ GOOD - Pure, composable
const enriched = discoveries
  .filter(d => d.type === 'pattern')
  .map(d => normalizeDiscovery(d))
  .reduce((acc, d) => addToModule(acc, d), context);

// ❌ BAD - Imperative, mutations
for (let i = 0; i < discoveries.length; i++) {
  if (discoveries[i].type === 'pattern') {
    context.modules[name].patterns.push(discoveries[i]);
  }
}
```

### Function Guidelines

**Keep Functions Small:**
- Maximum 50 lines per function
- If longer, extract helper functions
- One level of abstraction per function

**Descriptive Names:**
```typescript
// ✅ GOOD
function calculateContextScoreWithRecencyAndAccess(item: ContextItem): number

// ❌ BAD
function calc(x: any): number
```

**Pure Functions First:**
- Prefer pure functions (calculations) over actions
- Push I/O to infrastructure layer
- Domain layer = 100% pure functions

---

## Testing Standards (MANDATORY)

### Test-Driven Development (TDD)

**Red-Green-Refactor Cycle:**
1. 🔴 **RED:** Write failing test first
2. 🟢 **GREEN:** Write minimum code to pass
3. 🔵 **REFACTOR:** Improve code quality

**You MUST:**
- Write tests BEFORE implementation
- Never write production code without a failing test first
- Each task starts with tests

### Test Coverage Requirements

**Minimum Coverage: 90%**

```bash
# Run tests with coverage
bun test --coverage

# Coverage must be >= 90% for:
- Statements
- Branches
- Functions
- Lines
```

**If coverage < 90%:** Implementation is NOT complete.

### Test Structure

```typescript
// tests/unit/domain/calculations/context-scoring.test.ts

import { describe, it, expect } from 'vitest';
import { calculateContextScore } from '@/domain/calculations/context-scoring';

describe('calculateContextScore', () => {
  describe('when item was accessed recently', () => {
    it('should return high score', () => {
      const lastAccessed = new Date('2025-10-09');
      const now = new Date('2025-10-10');
      const score = calculateContextScore(lastAccessed, 10, now);

      expect(score).toBeGreaterThan(0.8);
    });
  });

  describe('when item was not accessed', () => {
    it('should return low score', () => {
      const lastAccessed = new Date('2025-09-01');
      const now = new Date('2025-10-09');
      const score = calculateContextScore(lastAccessed, 0, now);

      expect(score).toBeLessThan(0.3);
    });
  });
});
```

### Test Organization

```
tests/
├── unit/                    # Unit tests (90% of tests)
│   ├── domain/              # Pure function tests
│   ├── application/         # Use case tests
│   └── infrastructure/      # Adapter tests (with mocks)
│
└── integration/             # Integration tests (10% of tests)
    ├── full-workflow.test.ts
    └── mcp-server.test.ts
```

### What to Test

**Domain Layer (100% coverage):**
- All pure functions
- All business rules
- All calculations
- Edge cases, boundary conditions

**Application Layer (95% coverage):**
- Use cases
- Service orchestration
- Error handling

**Infrastructure Layer (80% coverage):**
- Adapter logic (mock external dependencies)
- Error handling
- Skip testing external libraries themselves

### Testing Pure Functions (Easy!)

```typescript
// Pure functions are EASY to test - no mocks needed!

describe('enrichModule', () => {
  it('should add new patterns without mutating original', () => {
    const module = { patterns: ['pattern1'] };
    const discoveries = [{ type: 'pattern', content: 'pattern2' }];

    const result = enrichModule(module, discoveries);

    expect(result.patterns).toEqual(['pattern1', 'pattern2']);
    expect(module.patterns).toEqual(['pattern1']); // Original unchanged
  });
});
```

### Testing Actions (Use Mocks)

```typescript
// Actions need mocks for I/O

import { describe, it, expect, vi } from 'vitest';

describe('saveProjectContext', () => {
  it('should write YAML to file system', async () => {
    const mockWriteFile = vi.fn();
    const context = { version: '1.0', project: { name: 'test' } };

    await saveProjectContext(context, '/path/to/file.yaml', mockWriteFile);

    expect(mockWriteFile).toHaveBeenCalledWith(
      '/path/to/file.yaml',
      expect.stringContaining('version: "1.0"')
    );
  });
});
```

---

## Build & Development

### Tools

**Runtime:** Bun (not Node.js!)
```bash
# Install dependencies
bun install

# Run TypeScript compiler
bun run build

# Run tests
bun test

# Run tests with coverage
bun test --coverage

# Run tests in watch mode
bun test --watch

# Start MCP server (during development)
bun run src/infrastructure/cli/index.ts serve
```

**Test Runner:** Vitest
```bash
# Vitest config in vitest.config.ts
```

### Development Workflow

1. **Read constitution.md** (ALWAYS start here)
2. **Read current spec.md** (understand requirements)
3. **Use /plan** to create technical plan (if not exists)
4. **Use /tasks** to break into tasks (if not exists)
5. **Use /analyze** to validate consistency
6. **For each task:**
   ```
   a. Read task acceptance criteria
   b. Write tests FIRST (Red)
   c. Implement code to pass tests (Green)
   d. Refactor for quality (Refactor)
   e. Run: bun test --coverage
   f. Verify coverage >= 90%
   g. Verify TypeScript compiles: bun run build
   h. Tell me when ready to commit (I'll commit manually)
   ```

---

## Quality Gates

### Overview

Quality gates ensure code quality, architectural integrity, and type safety before any code is committed. All gates must pass before proceeding.

### Running Quality Checks

```bash
# Run all quality gates (type check + lint + tests with coverage)
bun run quality-gate

# Run individual checks
bun run type-check      # TypeScript strict type checking
bun run lint            # ESLint with architecture boundaries
bun run lint:fix        # Auto-fix ESLint issues
bun test:coverage       # Tests with 90% coverage requirement

# Pre-commit check (same as quality-gate)
bun run pre-commit
```

### What Each Gate Validates

#### 1. Type Checking (`bun run type-check`)

**Validates:**
- TypeScript strict mode compliance
- No implicit `any` types
- No unused locals or parameters
- Null safety with `strictNullChecks`
- Index access safety with `noUncheckedIndexedAccess`
- Function type safety with `strictFunctionTypes`

**Common Violations:**
```typescript
// ❌ BAD - Implicit any
function process(data) { }

// ✅ GOOD - Explicit type
function process(data: ProjectContext): void { }

// ❌ BAD - Unchecked index access
const value = obj[key];  // Could be undefined

// ✅ GOOD - Safe index access
const value = obj[key];
if (value !== undefined) {
  // Use value safely
}
```

#### 2. Linting (`bun run lint`)

**Validates:**
- Code style consistency
- Import/export correctness
- No unused variables
- Prefer const over let
- Consistent type imports
- **Architecture boundary enforcement**

**ESLint Configuration:**
- Uses flat config format (`eslint.config.mjs`)
- TypeScript strict + stylistic rules
- Custom architecture boundary rules

#### 3. Architecture Boundary Enforcement

**The Onion Architecture Rule:**

```
🔴 Infrastructure → 🟡 Application → 🟢 Domain
         ↓              ↓              ↓
      (I/O)      (orchestration)   (pure logic)
```

**Dependency Rules (Enforced by ESLint):**

| Layer | Can Import From | Cannot Import From | Emoji |
|-------|-----------------|-------------------|-------|
| **Domain** | Nothing | Application, Infrastructure, Shared | 🟢 |
| **Application** | Domain only | Infrastructure, Shared | 🟡 |
| **Infrastructure** | Domain, Application, Shared | Nothing (outermost) | 🔴 |
| **Shared** | Domain only | Application, Infrastructure | ⚪ |

**Violation Examples:**

```typescript
// ❌ VIOLATION: Domain importing from Infrastructure
// File: src/domain/models/User.ts
import { logger } from '@infrastructure/cli/logger';  // ❌ ERROR!

// ✅ FIX: Domain must be pure
// Domain models should have no dependencies

// ❌ VIOLATION: Application importing from Infrastructure
// File: src/application/use-cases/CreateUser.ts
import { SQLiteAdapter } from '@infrastructure/storage/sqlite-adapter';  // ❌ ERROR!

// ✅ FIX: Use dependency injection via ports
import type { IStorage } from '@application/ports/IStorage';

export class CreateUser {
  constructor(private storage: IStorage) { }
}

// ❌ VIOLATION: Domain importing Shared utilities
// File: src/domain/calculations/scoring.ts
import { logger } from '@shared/errors';  // ❌ ERROR!

// ✅ FIX: Domain must be pure, no logging
// If needed, return errors and let caller handle logging
```

**How to Fix Violations:**

1. **Domain violating boundaries:**
   - Remove all imports from other layers
   - Keep domain 100% pure (no I/O, no logging)
   - Move shared logic into domain if truly needed

2. **Application violating boundaries:**
   - Use dependency injection for infrastructure needs
   - Define interfaces (ports) in application layer
   - Implement adapters in infrastructure layer

3. **Shared violating boundaries:**
   - Shared should only contain pure utilities
   - Can import domain types if needed
   - Never import from application or infrastructure

**ESLint Error Messages:**

```
❌ DOMAIN LAYER VIOLATION: Domain (🟢) must be pure with ZERO dependencies. 
   Found import from infrastructure. Move shared code to domain if needed.

❌ APPLICATION LAYER VIOLATION: Application (🟡) can only import from Domain (🟢). 
   Found import from infrastructure. Move shared code to domain or use dependency injection.

❌ SHARED LAYER VIOLATION: Shared utilities should only import from Domain (🟢) or be pure. 
   Found import from application.
```

#### 4. Test Coverage (`bun test:coverage`)

**Requirements:**
- 90% minimum coverage (statements, branches, functions, lines)
- All tests must pass
- No skipped tests in production code

**Vitest Configuration:**
- Coverage provider: v8
- Thresholds enforced: 90% all metrics
- Fails build if coverage < 90%

### Architecture Boundary Testing

**Verify boundaries are enforced:**

```bash
# Create a test violation
echo 'import { logger } from "@infrastructure/cli/logger";' > src/domain/models/Test.ts

# Run lint - should fail with architecture violation
bun run lint

# Expected error:
# ❌ DOMAIN LAYER VIOLATION: Domain (🟢) must be pure with ZERO dependencies.

# Remove test file
rm src/domain/models/Test.ts
```

### Integration with Development Workflow

**Before Every Commit:**
```bash
# Run full quality gate
bun run pre-commit

# If any check fails, fix issues before committing
```

**During Development:**
```bash
# Watch mode for fast feedback
bun test:watch          # Tests in watch mode
bun run lint:fix        # Auto-fix linting issues
```

**Before Pull Request:**
```bash
# Ensure all gates pass
bun run quality-gate

# Manual checks:
# - No TODOs or FIXMEs
# - Documentation updated
# - CHANGELOG updated
```

### Common Quality Gate Failures

#### TypeScript Errors

**Problem:** `Property 'foo' does not exist on type 'Bar'`
**Solution:** Add proper type definitions or use type guards

**Problem:** `Object is possibly 'undefined'`
**Solution:** Add null checks or use optional chaining (`?.`)

#### ESLint Errors

**Problem:** `Unexpected any`
**Solution:** Add explicit type annotations

**Problem:** `Architecture violation: domain cannot import infrastructure`
**Solution:** Remove the import, keep domain pure

#### Test Coverage

**Problem:** `Coverage for statements (85%) does not meet threshold (90%)`
**Solution:** Add tests for uncovered code paths

### Quality Gate Configuration Files

**ESLint:** `eslint.config.mjs` (flat config format)
**TypeScript:** `tsconfig.json` (strict mode enabled)
**Tests:** `vitest.config.ts` (90% coverage threshold)
**Package Scripts:** `package.json` (quality-gate, pre-commit)

---

## Quality Gates Checklist (MUST PASS)

### Before Marking Task Complete

- [ ] **Quality gate passes** (`bun run quality-gate`)
  - [ ] TypeScript type check passes (`bun run type-check`)
  - [ ] ESLint passes with no errors (`bun run lint`)
  - [ ] All tests pass (`bun test`)
  - [ ] Coverage >= 90% (`bun test:coverage`)
- [ ] **Architecture boundaries respected** (enforced by ESLint)
- [ ] All acceptance criteria met
- [ ] Error handling implemented
- [ ] Logging added (comprehensive, for debugging)
- [ ] No `console.log` (use logger instead)
- [ ] No `any` types (unless justified in comments)
- [ ] Pure functions in domain layer (no I/O)
- [ ] Dependencies only point inward (onion architecture)

### Before Marking Feature Complete

- [ ] All tasks completed
- [ ] Integration tests pass
- [ ] Manual testing done
- [ ] Documentation updated (README, JSDoc)
- [ ] No TODOs or FIXMEs in code

---

## Environment Setup

### Required Environment Variables

```bash
# .env (create this file, add to .gitignore)
OPENAI_API_KEY=sk-...              # Required for embeddings
ANTHROPIC_API_KEY=sk-ant-...       # Required for future AI extraction
CONTEXT_TOOL_LOG_LEVEL=debug       # For development
```

**API Keys MUST be present:**
- If missing, show clear error message
- Never commit keys to git
- Use `.env` file locally (add to `.gitignore`)

### Configuration

```bash
# ~/.context-tool/config.yaml (optional)
embeddings:
  provider: "openai"
  model: "text-embedding-3-small"
  batchSize: 100

storage:
  contextDir: ".context"
  dbPath: ".context/sessions.db"

services:
  scorerInterval: 300000      # 5 minutes
  prunerThreshold: 0.8        # 80%
```

---

## Project-Specific Context (CRITICAL!)

### What This Project IS

✅ **MCP Server:**
- Communicates via stdio (standard input/output)
- NOT a web server (no HTTP, no Express, no REST API)
- Uses @modelcontextprotocol/sdk

✅ **CLI Tool:**
- Commands: `init`, `serve`, `show`, `status`
- NOT an interactive TUI
- Simple command execution

✅ **Background Services:**
- Context scorer (every 5 min)
- Context pruner (at 80% threshold)
- Session auto-save (on triggers)
- Embeddings generator (async)

✅ **Local-First:**
- All data in `.context/` directory
- No cloud storage
- No telemetry
- User owns all data

### What This Project IS NOT

❌ NOT a web application (no HTML, no CSS, no React)
❌ NOT a REST API (no HTTP endpoints)
❌ NOT a GUI (no Electron, no web UI)
❌ NOT multi-user (single developer, local only)
❌ NOT a SaaS (no authentication, no database server)

### MVP Scope Constraints (FROM CONSTITUTION)

**IN SCOPE:**
- TypeScript/JavaScript projects ONLY
- Rules-based discovery extraction (regex patterns)
- OpenAI embeddings (text-embedding-3-small)
- Local SQLite database
- Chroma vector database (local)
- Single user, local development

**OUT OF SCOPE (Post-MVP):**
- Multi-language support (Python, Go, Rust)
- AI-based discovery extraction (GPT-4 refinement)
- Git integration (git_log, git_blame, git_diff)
- Real-time file watching
- Web dashboard UI
- Team/collaboration features
- AST-based smart chunking
- Re-ranking with boost factors

### Architecture Constraints

**Dependency Flow (CRITICAL!):**
```
Infrastructure → Application → Domain
         ↓              ↓
      (I/O, external)  (orchestration)  (pure logic)
```

**NEVER:**
- Domain imports from Application ❌
- Domain imports from Infrastructure ❌
- Application imports from Infrastructure ❌
- Circular dependencies ❌

**File Organization:**
```
src/
  domain/           🟢 Pure (no imports from app/infra)
  application/      🟡 Uses domain (no imports from infra)
  infrastructure/   🔴 Uses domain + application
```

### Functional Programming Constraints

1. **Domain layer = 100% pure functions**
   - No I/O, no side effects
   - Given same input → always same output
   - Easily testable without mocks

2. **Prefer immutability**
   - Use spread operators, map/filter/reduce
   - Copy-on-write for updates
   - Never mutate function parameters

3. **Separate actions from calculations**
   - Calculations (pure) in domain/
   - Actions (I/O) in infrastructure/

4. **Push side effects to edges**
   - Core business logic = pure
   - I/O at infrastructure layer only

---

## Decision-Making Protocol

### When to Ask vs. When to Proceed

**ASK ME BEFORE:**
- Making architecture decisions not in constitution
- Adding dependencies not in plan
- Changing MVP scope (adding/removing features)
- Deviating from onion architecture
- Violating functional programming principles
- Making breaking API changes
- Adding external services or APIs

**PROCEED WITHOUT ASKING:**
- Implementing tasks as specified
- Writing tests
- Refactoring for quality (within task scope)
- Fixing bugs
- Adding helper functions in same layer
- Improving error messages
- Adding logging statements
- Following patterns already established in codebase

**IF UNCERTAIN:**
- Review constitution.md for principles
- Check spec.md for requirements
- Look for similar patterns in existing code
- ASK rather than guess

---

## Logging Strategy

**Comprehensive Logging for Debugging:**

```typescript
// Use Winston logger (not console.log)
import { logger } from '@/shared/logger';

// Log levels: error, warn, info, debug
logger.debug('Context scorer starting', { itemCount: items.length });
logger.info('Session saved', { sessionId, duration: elapsed });
logger.warn('Context window at 82%', { current: 82000, max: 100000 });
logger.error('Failed to save context', { error, filepath });
```

**What to Log:**
- All background service activity (scorer, pruner, auto-save)
- MCP tool calls (what was called, with what params)
- Context operations (load, prune, archive)
- Discovery extraction results
- Embeddings generation (batch size, duration)
- File access tracking
- Errors with full context (what, where, why)

**Log Format:**
```typescript
// Structured logging with context
logger.info('Operation completed', {
  operation: 'context_search',
  query: 'auth bug',
  resultsCount: 5,
  duration: 120, // ms
  timestamp: new Date().toISOString()
});
```

**Development Mode:**
```bash
# Set log level via environment variable
CONTEXT_TOOL_LOG_LEVEL=debug bun run serve
```

---

## Git & Commit Strategy

### Commit Policy

**Manual Commits Only:**
- I will tell you when to commit
- You never auto-commit
- You never push to remote

**When I Say "Commit":**
```bash
# Use conventional commit format
git commit -m "feat(domain): add context scoring calculation

- Implement calculateContextScore with recency + access factors
- Add pure functions for score normalization
- 100% test coverage
- Related to task #3"
```

**Conventional Commit Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Adding tests
- `refactor`: Code refactoring
- `chore`: Maintenance

**Scopes:**
- `domain`: Domain layer
- `application`: Application layer
- `infrastructure`: Infrastructure layer
- `mcp`: MCP server
- `cli`: CLI commands
- `storage`: Storage adapters

---

## Troubleshooting & Common Issues

### If Tests Fail

1. Read error message carefully
2. Check test expectations vs. actual output
3. Verify function is pure (for domain layer)
4. Check if dependencies installed: `bun install`
5. Check TypeScript compilation: `bun run build`
6. Review similar tests in codebase
7. Ask me if unclear

### If TypeScript Errors

1. Check `tsconfig.json` settings
2. Verify import paths are correct
3. Check for circular dependencies
4. Ensure return types are explicit
5. Verify no `any` types used

### If Coverage < 90%

1. Run: `bun test --coverage` to see what's missing
2. Add tests for uncovered lines
3. Consider if code is testable (pure functions easier)
4. Check if mocks needed for I/O operations

### If Architecture Violation

1. Review onion architecture diagram above
2. Check dependency direction (always inward)
3. Verify domain layer has no I/O
4. Move side effects to infrastructure

---

## Context Window Management

### Keep in Context

**Always:**
- `.specify/memory/constitution.md` (principles)
- Current task description and acceptance criteria
- Files being modified in current task

**When Needed:**
- Related domain models
- Related pure functions
- Test files for code being written

**Never:**
- node_modules/
- dist/, build/
- .git/
- Large data files
- Test fixtures
- Unrelated features

### When Context Window Full

1. Remove files not relevant to current task
2. Keep constitution.md always
3. Keep current task always
4. Remove old task files
5. Ask me if unsure what to remove

---

## Implementation Phases (From PRD)

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Storage layer working, basic MCP server

**Key Deliverables:**
- Project structure with onion architecture
- YAML handler (infrastructure/storage)
- SQLite database (infrastructure/storage)
- Chroma vector DB (infrastructure/storage)
- Basic MCP server (infrastructure/mcp)

### Phase 2: Core Logic (Weeks 3-4)
**Goal:** Init command, context loading, RAG search

**Key Deliverables:**
- Project scanner (domain/calculations)
- Context manager (application/use-cases)
- Search engine with RAG (application/services)
- MCP resources (infrastructure/mcp)
- MCP tools (infrastructure/mcp)

### Phase 3: Enrichment (Weeks 5-6)
**Goal:** Discovery extraction, embeddings, background services

**Key Deliverables:**
- Session manager (application/services)
- Discovery extractor (domain/rules)
- Context enricher (application/use-cases)
- Embeddings generator (infrastructure/external)
- Background services (infrastructure/background)

### Phase 4: Polish (Weeks 7-8)
**Goal:** CLI commands, logging, testing, documentation

**Key Deliverables:**
- All CLI commands (infrastructure/cli)
- Comprehensive logging
- 90%+ test coverage
- Documentation (README, JSDoc)
- Real-world testing on mon-saas project

---

## Success Criteria (From PRD)

### MVP is Complete When:

**Functional:**
- ✅ All commands work (`init`, `serve`, `show`, `status`)
- ✅ MCP server connects to Claude Desktop
- ✅ All resources accessible (`context://...`)
- ✅ All tools functional (`context_search`, `read_file`, `grep_codebase`)
- ✅ Sessions tracked and auto-saved
- ✅ Discoveries extracted after sessions
- ✅ Context enriched in project.yaml
- ✅ RAG search returns relevant results
- ✅ Context pruning prevents saturation

**Quality:**
- ✅ 90%+ test coverage
- ✅ All tests passing
- ✅ No critical bugs
- ✅ Documentation complete
- ✅ Can be used on real project (mon-saas)

**Validation:**
- ✅ Used daily for 2 weeks without manual context
- ✅ AI gives better answers in session 10 vs session 1
- ✅ Zero context window saturation issues
- ✅ Context setup time = 0 minutes

---

## Quick Reference

### File You'll Create During /implement

```
src/
  domain/                   # 🟢 Pure functions, no I/O
    models/                 # Data types
    calculations/           # Pure business logic
    rules/                  # Business rules

  application/              # 🟡 Use cases, orchestration
    use-cases/              # Feature workflows
    services/               # Application services
    ports/                  # Interfaces for infrastructure

  infrastructure/           # 🔴 I/O, external world
    storage/                # Database, file system
    mcp/                    # MCP protocol
    cli/                    # Commands
    background/             # Background jobs
    external/               # APIs (OpenAI, Anthropic)
```

### Commands to Run Often

```bash
# Run tests (do this constantly!)
bun test

# Run tests with coverage (before marking task complete)
bun test --coverage

# Build (verify TypeScript compiles)
bun run build

# Run in watch mode (during development)
bun test --watch
```

### Key Principles to Remember

1. **Read constitution.md FIRST** (always)
2. **TDD is mandatory** (tests before code)
3. **Coverage >= 90%** (non-negotiable)
4. **Domain = pure functions** (no I/O in 🟢 layer)
5. **Dependencies point inward** (🔴 → 🟡 → 🟢)
6. **Ask before big decisions** (architecture, scope, breaking changes)
7. **Commit when I tell you** (never auto-commit)
8. **Log comprehensively** (use logger, not console.log)

---

## Final Checklist Before Starting /implement

Before you start building, verify:

- [ ] I've read constitution.md completely
- [ ] I've read spec.md completely
- [ ] I've read plan.md (if exists)
- [ ] I've read tasks.md (if exists)
- [ ] I understand onion architecture (🟢 → 🟡 → 🔴)
- [ ] I understand functional programming principles
- [ ] I know TDD is mandatory (tests first)
- [ ] I know coverage must be >= 90%
- [ ] I know to ask before big decisions
- [ ] I know to wait for commit instructions
- [ ] I have Bun installed
- [ ] I have Vitest configured
- [ ] I have API keys ready (OPENAI_API_KEY, ANTHROPIC_API_KEY)

---

## Let's Build! 🚀

You're ready to create amazing context-aware AI coding experiences.

Remember:
- **Constitution = your North Star**
- **Pure functions = easy to test and reason about**
- **TDD = confidence in your code**
- **Onion architecture = maintainable, flexible system**

When in doubt, ask. When confident, proceed. Always test.

Now, let's use `/plan` to create the technical implementation plan!

---

**END OF GUIDE**
