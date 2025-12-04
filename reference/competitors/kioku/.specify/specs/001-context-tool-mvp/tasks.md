# Implementation Tasks: Context Tool MVP

**Branch**: `001-context-tool-mvp` | **Date**: 2025-01-15  
**Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

---

## Overview

This document breaks down the Context Tool MVP implementation into concrete, executable tasks organized by user story. Each phase represents a complete, independently testable increment.

**Total Tasks**: 87  
**Phases**: 13 (Setup + Foundational + 11 User Stories)  
**Target Coverage**: 90%+ (TDD enforced)

---

## Task Organization Strategy

### Phases

1. **Phase 1: Project Setup** - Project initialization, tooling, structure
2. **Phase 2: Foundational Infrastructure** - Core systems needed by all user stories
3. **Phase 3-13: User Story Implementation** - One phase per user story (US1.1 through US5.2)

### Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational: Domain models, storage adapters, shared infrastructure)
    ↓
Phase 3 (US1.1) ──→ Phase 4 (US2.1) ──→ Phase 5 (US2.2)
                         ↓                    ↓
                    Phase 6 (US2.3)      Phase 7 (US2.4)
                         ↓                    ↓
                    Phase 8 (US3.1) ──→ Phase 9 (US3.2)
                         ↓
                    Phase 10 (US4.1) ──→ Phase 11 (US4.2)
                         ↓
                    Phase 12 (US5.1) ──→ Phase 13 (US5.2)
```

**Key Parallelization Opportunities:**
- After Phase 2: US1.1 can start
- After US2.1: US2.2, US2.3, US2.4 can run in parallel
- After US3.1: US3.2, US4.1 can run in parallel
- After US4.1: US4.2, US5.1 can run in parallel

---

## Functional Requirements Coverage

This table maps each functional requirement (FR) from spec.md to the specific tasks that implement it.

| Requirement | Description | Primary Tasks | Supporting Tasks | Status |
|-------------|-------------|---------------|------------------|--------|
| **FR-1: Project Scanning** | Analyze project structure and generate initial context | T020, T021, T022 | T008 (ProjectContext model) | ✅ Covered |
| **FR-2: Session Tracking** | Monitor coding sessions transparently | T052, T053, T054 | T015 (Session model) | ✅ Covered |
| **FR-3: Discovery Extraction** | Extract learnings from session automatically | T055, T056, T057 | T016 (Discovery model) | ✅ Covered |
| **FR-4: Context Enrichment** | Update project.yaml with new discoveries | T060, T061, T062 | T018 (enrichment logic) | ✅ Covered |
| **FR-5: Semantic Search (RAG)** | Find relevant context via embeddings | T039, T040, T041 | T037 (embeddings), T019 (VectorDB) | ✅ Covered |
| **FR-6: Context Scoring** | Calculate relevance scores for context items | T063, T064, T067 | T010 (scoring model) | ✅ Covered |
| **FR-7: Context Pruning** | Archive low-score items to manage window size | T068, T069, T070 | T010 (scoring), T011 (ContextWindow model) | ✅ Covered |
| **FR-8: Embeddings Generation** | Create vector embeddings for semantic search | T037, T038, T083 | T019 (VectorDB adapter) | ✅ Covered |
| **FR-9: File Analysis** | Parse file imports and build dependency tree | T043, T044, T045 | T009 (FileInfo model) | ✅ Covered |
| **FR-10: Configuration Management** | Load and validate configuration | T023, T024, T025 | T007 (Config model) | ✅ Covered |

**Coverage Summary:**
- ✅ All 10 functional requirements mapped to implementation tasks
- ✅ All 11 user stories have dedicated phases (Phase 3-13)
- ✅ 87 total tasks with clear acceptance criteria
- ✅ TDD enforced: Each feature task has corresponding test task
- ✅ 90%+ coverage target for all code

---

## Phase 1: Project Setup

**Goal**: Initialize project structure, configure tooling, establish development environment

**Duration**: 1-2 hours  
**Dependencies**: None  
**Deliverable**: Working TypeScript project with Bun, Vitest, and onion architecture structure

### T001: Initialize Bun Project
**File**: `package.json`, `bunfig.toml`  
**Story**: [Setup]  
**Type**: Configuration

**Tasks**:
1. Run `bun init` in project root
2. Configure `package.json`:
   - Name: "context-tool"
   - Version: "0.1.0"
   - Type: "module"
   - Main: "dist/infrastructure/cli/index.js"
   - Bin: { "context-tool": "dist/infrastructure/cli/index.js" }
3. Create `bunfig.toml` for Bun configuration

**Acceptance Criteria**:
- `bun --version` shows Bun is installed
- `package.json` exists with correct fields
- Project name is "context-tool"

---

### T002: Install Core Dependencies
**File**: `package.json`  
**Story**: [Setup]  
**Type**: Configuration  
**Parallel**: [P] Can run with T003

**Dependencies to install**:
```bash
# Production
bun add @modelcontextprotocol/sdk
bun add chromadb
bun add yaml
bun add zod
bun add winston
bun add @babel/parser
bun add @babel/traverse

# Development
bun add -d @types/node
bun add -d vitest
bun add -d typescript
bun add -d @types/babel__parser
bun add -d @types/babel__traverse
```

**Acceptance Criteria**:
- All packages listed in `package.json` dependencies
- `bun install` completes without errors
- Total production dependencies: 7
- Total dev dependencies: 5

---

### T003: Configure TypeScript
**File**: `tsconfig.json`  
**Story**: [Setup]  
**Type**: Configuration  
**Parallel**: [P] Can run with T002

**Create `tsconfig.json`**:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "lib": ["ES2022"],
    "moduleResolution": "bundler",
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@domain/*": ["src/domain/*"],
      "@application/*": ["src/application/*"],
      "@infrastructure/*": ["src/infrastructure/*"],
      "@shared/*": ["src/shared/*"]
    }
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

**Acceptance Criteria**:
- TypeScript strict mode enabled
- Path aliases configured for onion architecture
- `bun run build` compiles (once src/ exists)

---

### T004: Configure Vitest
**File**: `vitest.config.ts`  
**Story**: [Setup]  
**Type**: Configuration  
**Parallel**: [P] Can run with T002, T003

**Create `vitest.config.ts`**:
```typescript
import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        'tests/',
        '**/*.test.ts',
        '**/*.config.ts',
      ],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 90,
        statements: 90,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@domain': path.resolve(__dirname, './src/domain'),
      '@application': path.resolve(__dirname, './src/application'),
      '@infrastructure': path.resolve(__dirname, './src/infrastructure'),
      '@shared': path.resolve(__dirname, './src/shared'),
    },
  },
});
```

**Acceptance Criteria**:
- Vitest configured with 90% coverage thresholds
- Path aliases match tsconfig.json
- Coverage fails if <90%

---

### T005: Create Project Directory Structure
**Files**: All `src/` directories  
**Story**: [Setup]  
**Type**: Structure

**Create directories**:
```bash
mkdir -p src/domain/{models,calculations,rules}
mkdir -p src/application/{use-cases,services,ports}
mkdir -p src/infrastructure/{storage,mcp,cli,background,external}
mkdir -p src/infrastructure/mcp/{resources,tools}
mkdir -p src/infrastructure/cli/commands
mkdir -p src/shared/{types,utils,errors}
mkdir -p tests/{unit,integration}
mkdir -p tests/unit/{domain,application,infrastructure}
```

**Acceptance Criteria**:
- All directories exist
- Structure matches onion architecture in plan.md
- 3 layers: domain, application, infrastructure

---

### T006: Setup Git Ignore
**File**: `.gitignore`  
**Story**: [Setup]  
**Type**: Configuration  
**Parallel**: [P] Can run with T005

**Create `.gitignore`**:
```
node_modules/
dist/
.context/
*.log
.env
.env.local
coverage/
.DS_Store
```

**Acceptance Criteria**:
- `.context/` directory excluded (local context storage)
- `node_modules/` and `dist/` excluded
- `.env` files excluded (API keys) — **Satisfies Security NFR**: "API Keys never committed"

---

### T007: Add Build and Test Scripts
**File**: `package.json`  
**Story**: [Setup]  
**Type**: Configuration

**Add scripts to `package.json`**:
```json
{
  "scripts": {
    "build": "bun run tsc",
    "test": "vitest run",
    "test:watch": "vitest watch",
    "test:coverage": "vitest run --coverage",
    "lint": "tsc --noEmit",
    "dev": "bun run src/infrastructure/cli/index.ts"
  }
}
```

**Acceptance Criteria**:
- `bun run build` compiles TypeScript
- `bun test` runs Vitest
- `bun test:coverage` shows coverage report

---

**Phase 1 Checkpoint**: ✅ Project structure ready, tooling configured, ready for implementation

---

## Phase 2: Foundational Infrastructure

**Goal**: Build core systems required by ALL user stories (domain models, storage, logging)

**Duration**: 4-6 hours  
**Dependencies**: Phase 1  
**Deliverable**: Domain models, storage adapters, shared utilities ready for use

### T008: Create Domain Models - ProjectContext
**File**: `src/domain/models/ProjectContext.ts`  
**Story**: [Foundational]  
**Type**: Domain Model  
**Parallel**: [P] Can run with T009-T012

**Implementation**:
```typescript
export interface ProjectContext {
  version: string;
  project: {
    name: string;
    type: 'web-app' | 'api' | 'cli' | 'library' | 'fullstack';
    path: string;
  };
  tech: {
    stack: string[];
    runtime: string;
    packageManager: 'npm' | 'yarn' | 'pnpm' | 'bun';
  };
  architecture: {
    pattern: 'feature-based' | 'layered' | 'modular' | 'monorepo' | 'unknown';
    description: string;
  };
  modules: Record<string, ModuleContext>;
  metadata: {
    createdAt: Date;
    updatedAt: Date;
    lastScanAt: Date;
  };
}

export interface ModuleContext {
  name: string;
  description: string;
  keyFiles: KeyFile[];
  patterns: string[];
  businessRules: string[];
  commonIssues: Issue[];
  dependencies: string[];
}

export interface KeyFile {
  path: string;
  role: 'entry' | 'config' | 'core' | 'test';
  description?: string;
}

export interface Issue {
  description: string;
  solution: string;
  sessionId: string;
  discoveredAt: Date;
}
```

**Acceptance Criteria**:
- All interfaces defined per data-model.md
- No implementation logic (pure types)
- Exported from module

---

### T009: Create Domain Models - Session
**File**: `src/domain/models/Session.ts`  
**Story**: [Foundational]  
**Type**: Domain Model  
**Parallel**: [P] Can run with T008, T010-T012

**Implementation**:
```typescript
export interface Session {
  id: string;
  projectId: string;
  startedAt: Date;
  endedAt?: Date;
  status: 'active' | 'completed' | 'archived';
  filesAccessed: FileAccess[];
  topics: string[];
  metadata: {
    duration?: number;
    toolCallsCount: number;
    discoveryCount: number;
  };
}

export interface FileAccess {
  path: string;
  accessCount: number;
  firstAccessedAt: Date;
  lastAccessedAt: Date;
}
```

**Acceptance Criteria**:
- Session model matches data-model.md
- All state transitions supported (active → completed → archived)

---

### T010: Create Domain Models - Discovery
**File**: `src/domain/models/Discovery.ts`  
**Story**: [Foundational]  
**Type**: Domain Model  
**Parallel**: [P] Can run with T008-T009, T011-T012

**Implementation**:
```typescript
export interface Discovery {
  id: string;
  sessionId: string;
  type: 'pattern' | 'rule' | 'decision' | 'issue';
  content: string;
  module?: string;
  context: {
    extractedFrom: string;
    confidence: number;
  };
  embedding?: {
    id: string;
    model: string;
    dimensions: number;
  };
  createdAt: Date;
}
```

**Acceptance Criteria**:
- Discovery types: pattern, rule, decision, issue
- Confidence 0.0-1.0
- Optional embedding reference

---

### T011: Create Domain Models - ContextItem
**File**: `src/domain/models/ContextItem.ts`  
**Story**: [Foundational]  
**Type**: Domain Model  
**Parallel**: [P] Can run with T008-T010, T012

**Implementation**:
```typescript
export interface ContextItem {
  id: string;
  type: 'file' | 'module' | 'discovery' | 'session';
  content: string;
  metadata: {
    source: string;
    module?: string;
    sessionId?: string;
  };
  scoring: {
    score: number;
    recencyFactor: number;
    accessFactor: number;
    lastAccessedAt: Date;
    accessCount: number;
  };
  tokens: number;
  status: 'active' | 'archived';
}
```

**Acceptance Criteria**:
- Scoring fields for context management
- Status: active or archived
- Token count for window management

---

### T012: Create Domain Models - Config
**File**: `src/domain/models/Config.ts`  
**Story**: [Foundational]  
**Type**: Domain Model  
**Parallel**: [P] Can run with T008-T011

**Implementation**:
```typescript
export interface Config {
  storage: {
    contextDir: string;
    dbPath: string;
    chromaPath: string;
  };
  embeddings: {
    provider: 'openai';
    model: string;
    apiKey: string;
    batchSize: number;
  };
  services: {
    scorerInterval: number;
    prunerThreshold: number;
    sessionTimeout: number;
    embeddingsInterval: number;
  };
  contextWindow: {
    maxTokens: number;
    pruneTarget: number;
  };
  logging: {
    level: 'debug' | 'info' | 'warn' | 'error';
    file?: string;
  };
}
```

**Acceptance Criteria**:
- Default values documented
- All configuration sections present

---

### T013: Create Shared Error Classes
**File**: `src/shared/errors/index.ts`  
**Story**: [Foundational]  
**Type**: Shared Utility  
**Parallel**: [P] Can run with T008-T012

**Implementation**:
```typescript
export class ConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigError';
  }
}

export class StorageError extends Error {
  constructor(message: string, public cause?: Error) {
    super(message);
    this.name = 'StorageError';
  }
}

export class MCPError extends Error {
  constructor(message: string, public code?: number) {
    super(message);
    this.name = 'MCPError';
  }
}
```

**Acceptance Criteria**:
- Custom error classes for each layer
- Error context preserved

---

### T014: Setup Winston Logger
**File**: `src/infrastructure/cli/logger.ts`  
**Story**: [Foundational]  
**Type**: Infrastructure  
**Parallel**: [P] Can run with T008-T013

**Implementation**:
```typescript
import winston from 'winston';

export const logger = winston.createLogger({
  level: process.env.CONTEXT_TOOL_LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple(),
    }),
  ],
});

// Add file transport if .context directory exists
if (process.env.CONTEXT_DIR) {
  logger.add(new winston.transports.File({
    filename: `${process.env.CONTEXT_DIR}/context-tool.log`,
  }));
}
```

**Acceptance Criteria**:
- Logger configured with Winston
- Log level from environment variable
- Console and file transports

---

### T015: Create SQLite Adapter
**File**: `src/infrastructure/storage/sqlite-adapter.ts`  
**Story**: [Foundational]  
**Type**: Infrastructure

**Implementation**:
- Use `bun:sqlite` (built-in, not better-sqlite3)
- Enable WAL mode for performance
- Create sessions, discoveries, context_items tables
- Implement: saveSession, getSession, saveDiscovery, etc.

**Acceptance Criteria**:
- WAL mode enabled
- All tables created per data-model.md schema
- Indexes created for common queries
- Methods for CRUD operations

**Dependencies**: T009, T010, T011

---

### T016: Write Tests for SQLite Adapter
**File**: `tests/unit/infrastructure/storage/sqlite-adapter.test.ts`  
**Story**: [Foundational]  
**Type**: Test

**Test Cases**:
```typescript
describe('SQLiteAdapter', () => {
  describe('saveSession', () => {
    it('should save session to database');
    it('should update existing session');
  });
  
  describe('getSession', () => {
    it('should load session by ID');
    it('should return undefined for non-existent session');
  });
  
  describe('saveDiscovery', () => {
    it('should save discovery with session FK');
    it('should reject discovery with invalid session ID');
  });
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Tests use temporary test database
- Cleanup after each test

**Dependencies**: T015

---

### T017: Create YAML Handler
**File**: `src/infrastructure/storage/yaml-handler.ts`  
**Story**: [Foundational]  
**Type**: Infrastructure  
**Parallel**: [P] Can run with T015-T016

**Implementation**:
- Read/write project.yaml
- Parse with `yaml` package
- Validate with Zod schema
- Atomic writes (backup before save)

**Acceptance Criteria**:
- loadProjectContext() reads and validates YAML
- saveProjectContext() writes with backup
- Validation errors throw ConfigError

**Dependencies**: T008

---

### T018: Write Tests for YAML Handler
**File**: `tests/unit/infrastructure/storage/yaml-handler.test.ts`  
**Story**: [Foundational]  
**Type**: Test  
**Parallel**: [P] Can run with T016

**Test Cases**:
```typescript
describe('YAMLHandler', () => {
  it('should load valid project.yaml');
  it('should validate with Zod schema');
  it('should reject invalid YAML');
  it('should backup before save');
  it('should restore from backup on failure');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Tests use temporary files

**Dependencies**: T017

---

### T019: Create Chroma Adapter
**File**: `src/infrastructure/storage/chroma-adapter.ts`  
**Story**: [Foundational]  
**Type**: Infrastructure  
**Parallel**: [P] Can run with T015-T018

**Implementation**:
- Initialize ChromaDB client (persistent mode)
- Create collection with HNSW parameters
- Implement batch insertion (100 items)
- Implement semantic search with metadata filtering

**Acceptance Criteria**:
- Collection created with cosine similarity
- Batch operations for embeddings
- Metadata filtering support

**Dependencies**: T010

---

### T020: Write Tests for Chroma Adapter
**File**: `tests/unit/infrastructure/storage/chroma-adapter.test.ts`  
**Story**: [Foundational]  
**Type**: Test

**Test Cases**:
```typescript
describe('ChromaAdapter', () => {
  it('should create collection');
  it('should batch insert embeddings');
  it('should search with metadata filters');
  it('should return top N results');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Tests use temporary collection

**Dependencies**: T019

---

**Phase 2 Checkpoint**: ✅ Foundation complete - models, storage, logging ready

---

## Phase 3: US1.1 - Quick Setup (`context-tool init`)

**Goal**: Project initialization command that scans directory and creates .context/project.yaml

**User Story**: US1.1 - Quick Setup  
**Duration**: 4-6 hours  
**Dependencies**: Phase 2  
**Deliverable**: Working `context-tool init` command

### T021: Create Domain - Context Scoring Calculation
**File**: `src/domain/calculations/context-scoring.ts`  
**Story**: [US1.1]  
**Type**: Domain (Pure Function)

**Implementation**:
```typescript
export function calculateContextScore(
  lastAccessedAt: Date,
  accessCount: number,
  now: Date = new Date()
): number {
  const recencyFactor = calculateRecencyFactor(lastAccessedAt, now);
  const accessFactor = normalizeAccessCount(accessCount);
  return 0.6 * recencyFactor + 0.4 * accessFactor;
}

function calculateRecencyFactor(lastAccessed: Date, now: Date): number {
  const daysSince = (now.getTime() - lastAccessed.getTime()) / (1000 * 60 * 60 * 24);
  return Math.max(0, 1 - (daysSince / 30));
}

function normalizeAccessCount(count: number, maxCount: number = 100): number {
  return Math.min(count / maxCount, 1.0);
}
```

**Acceptance Criteria**:
- Pure function (no I/O)
- Returns 0.0-1.0
- Recent items score higher

**Dependencies**: Phase 2

---

### T022: Write Tests for Context Scoring
**File**: `tests/unit/domain/calculations/context-scoring.test.ts`  
**Story**: [US1.1]  
**Type**: Test

**Test Cases**:
```typescript
describe('calculateContextScore', () => {
  it('should return high score for recently accessed items');
  it('should return low score for old items');
  it('should weigh recency at 60%');
  it('should weigh access count at 40%');
  it('should cap score at 1.0');
  it('should floor score at 0.0');
});
```

**Acceptance Criteria**:
- Coverage 100% (pure functions easy to test)
- All edge cases covered

**Dependencies**: T021

---

### T023: Create Use Case - Initialize Project
**File**: `src/application/use-cases/InitializeProject.ts`  
**Story**: [US1.1]  
**Type**: Application

**Implementation**:
- Scan project directory recursively
- Detect tech stack from package.json
- Infer architecture from folder structure
- Identify modules by folder patterns
- Create ProjectContext
- Save to .context/project.yaml
- Initialize databases (SQLite, Chroma)

**Acceptance Criteria**:
- Scans <2min for 500 files
- Detects Next.js, React, Express, TypeScript
- Creates .context directory
- Generates valid project.yaml

**Dependencies**: T008, T017, T015, T019

---

### T024: Write Tests for Initialize Project Use Case
**File**: `tests/unit/application/use-cases/InitializeProject.test.ts`  
**Story**: [US1.1]  
**Type**: Test

**Test Cases**:
```typescript
describe('InitializeProject', () => {
  it('should scan directory structure');
  it('should detect tech stack from package.json');
  it('should identify modules from folders');
  it('should create .context directory');
  it('should generate project.yaml');
  it('should initialize databases');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock filesystem and storage

**Dependencies**: T023

---

### T025: Create CLI Command - Init
**File**: `src/infrastructure/cli/commands/init.ts`  
**Story**: [US1.1]  
**Type**: Infrastructure

**Implementation**:
```typescript
import { InitializeProject } from '@application/use-cases/InitializeProject';
import { logger } from '../logger';

export async function initCommand(): Promise<void> {
  console.log('✓ Scanning project structure...');
  
  const useCase = new InitializeProject(storage);
  const context = await useCase.execute(process.cwd());
  
  console.log('✓ Detected:', context.tech.stack.join(', '));
  console.log('✓ Found', Object.keys(context.modules).length, 'modules');
  console.log('✓ Generated .context/project.yaml');
  console.log('✓ Initialized databases');
  console.log('✓ Context initialized! Run \'context-tool serve\' to start.');
}
```

**Acceptance Criteria**:
- User-friendly output with checkmarks
- Error handling with clear messages
- Completes in <2min

**Dependencies**: T023

---

### T026: Create CLI Entry Point
**File**: `src/infrastructure/cli/index.ts`  
**Story**: [US1.1]  
**Type**: Infrastructure

**Implementation**:
```typescript
#!/usr/bin/env bun

import { initCommand } from './commands/init';
import { logger } from './logger';

const command = process.argv[2];

switch (command) {
  case 'init':
    await initCommand();
    break;
  default:
    console.log('Usage: context-tool <command>');
    console.log('Commands: init');
    process.exit(1);
}
```

**Acceptance Criteria**:
- Shebang for executable
- Command routing
- Help text

**Dependencies**: T025

---

### T027: Integration Test - Init Command
**File**: `tests/integration/init-command.test.ts`  
**Story**: [US1.1]  
**Type**: Integration Test

**Test Cases**:
```typescript
describe('Init Command Integration', () => {
  it('should initialize project in real directory');
  it('should create .context/project.yaml');
  it('should create SQLite database');
  it('should create Chroma collection');
  it('should complete in <2 minutes');
});
```

**Acceptance Criteria**:
- End-to-end test with real filesystem
- Cleanup test artifacts

**Dependencies**: T026

---

**Phase 3 Checkpoint**: ✅ US1.1 Complete - `context-tool init` working

---

## Phase 4: US2.1 - Automatic Context Loading (MCP Server)

**Goal**: MCP server that auto-starts with Claude Desktop and loads project context

**User Story**: US2.1 - Automatic Context Loading  
**Duration**: 6-8 hours  
**Dependencies**: Phase 3  
**Deliverable**: MCP server serving resources

### T028: Create MCP Server Entry Point
**File**: `src/infrastructure/mcp/server.ts`  
**Story**: [US2.1]  
**Type**: Infrastructure

**Implementation**:
```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { logger } from '@infrastructure/cli/logger';

export async function startMCPServer(): Promise<void> {
  const server = new Server(
    { name: 'context-tool', version: '1.0.0' },
    { capabilities: { resources: {}, tools: {} } }
  );

  // Load project context
  await loadProjectContext();

  // Register resources and tools
  registerResources(server);
  registerTools(server);

  // Connect stdio transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  logger.info('Context Tool MCP server started');
}
```

**Acceptance Criteria**:
- MCP server initializes
- Connects via stdio
- Loads project.yaml
- Logs startup

**Dependencies**: T017, T014

---

### T029: Create MCP Resource - Project Overview
**File**: `src/infrastructure/mcp/resources/ProjectResource.ts`  
**Story**: [US2.1]  
**Type**: Infrastructure  
**Parallel**: [P] Can run with T030-T031

**Implementation**:
- Resource URI: `context://project/overview`
- Load ProjectContext from YAML
- Format as markdown
- Return via MCP protocol

**Acceptance Criteria**:
- Returns valid markdown
- Includes tech stack, architecture, modules
- Handles missing project.yaml gracefully

**Dependencies**: T008, T017

---

### T030: Create MCP Resource - Module Detail
**File**: `src/infrastructure/mcp/resources/ModuleResource.ts`  
**Story**: [US2.1]  
**Type**: Infrastructure  
**Parallel**: [P] Can run with T029, T031

**Implementation**:
- Resource URI: `context://module/{name}`
- Load specific module from project.yaml
- Format module patterns, rules, issues as markdown
- Return via MCP protocol

**Acceptance Criteria**:
- Returns module details
- Handles invalid module name
- Includes key files, patterns, rules

**Dependencies**: T008, T017

---

### T031: Create MCP Resource - Current Session
**File**: `src/infrastructure/mcp/resources/SessionResource.ts`  
**Story**: [US2.1]  
**Type**: Infrastructure  
**Parallel**: [P] Can run with T029-T030

**Implementation**:
- Resource URI: `context://session/current`
- Query active session from SQLite
- Format session info as markdown
- Return via MCP protocol

**Acceptance Criteria**:
- Shows active session details
- Lists files accessed
- Handles no active session

**Dependencies**: T009, T015

---

### T032: Register MCP Resources
**File**: `src/infrastructure/mcp/server.ts` (update)  
**Story**: [US2.1]  
**Type**: Infrastructure

**Implementation**:
```typescript
function registerResources(server: Server): void {
  server.setRequestHandler(ListResourcesRequestSchema, async () => {
    return {
      resources: [
        {
          uri: 'context://project/overview',
          name: 'Project Overview',
          mimeType: 'text/markdown',
          description: 'High-level project information',
        },
        // Add module, session resources
      ],
    };
  });

  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const uri = new URL(request.params.uri);
    // Route to appropriate handler
  });
}
```

**Acceptance Criteria**:
- All 3 resources registered
- URI routing works
- Error handling for unknown URIs

**Dependencies**: T029, T030, T031

---

### T033: Write Tests for MCP Resources
**File**: `tests/unit/infrastructure/mcp/resources.test.ts`  
**Story**: [US2.1]  
**Type**: Test

**Test Cases**:
```typescript
describe('MCP Resources', () => {
  it('should list all resources');
  it('should return project overview');
  it('should return module detail');
  it('should return current session');
  it('should handle unknown resource URI');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock project context and sessions

**Dependencies**: T032

---

### T034: Create CLI Command - Serve
**File**: `src/infrastructure/cli/commands/serve.ts`  
**Story**: [US2.1]  
**Type**: Infrastructure

**Implementation**:
```typescript
export async function serveCommand(): Promise<void> {
  logger.info('Starting MCP server...');
  await startMCPServer();
}
```

**Acceptance Criteria**:
- Starts MCP server
- Runs in foreground
- Graceful shutdown on SIGINT

**Dependencies**: T028, T032

---

### T035: Update CLI Entry Point for Serve
**File**: `src/infrastructure/cli/index.ts` (update)  
**Story**: [US2.1]  
**Type**: Infrastructure

**Add serve command to router**:
```typescript
case 'serve':
  await serveCommand();
  break;
```

**Acceptance Criteria**:
- `context-tool serve` starts MCP server
- Help text updated

**Dependencies**: T034

---

### T036: Integration Test - MCP Server
**File**: `tests/integration/mcp-server.test.ts`  
**Story**: [US2.1]  
**Type**: Integration Test

**Test Cases**:
```typescript
describe('MCP Server Integration', () => {
  it('should start server and respond to resource requests');
  it('should return project overview via stdio');
  it('should handle multiple resource requests');
});
```

**Acceptance Criteria**:
- End-to-end MCP server test
- Uses real project.yaml

**Dependencies**: T035

---

**Phase 4 Checkpoint**: ✅ US2.1 Complete - MCP server serving resources

---

## Phase 5: US2.2 - Intelligent Context Search (RAG)

**Goal**: `context_search` tool with semantic search via embeddings

**User Story**: US2.2 - Intelligent Context Search  
**Duration**: 6-8 hours  
**Dependencies**: Phase 4  
**Deliverable**: Working semantic search tool

### T037: Create OpenAI Client
**File**: `src/infrastructure/external/OpenAIClient.ts`  
**Story**: [US2.2]  
**Type**: Infrastructure

**Implementation**:
- Initialize OpenAI SDK
- Generate embeddings (text-embedding-3-small)
- Batch processing (100 items)
- Retry with exponential backoff

**Acceptance Criteria**:
- API key from environment variable
- Error handling for rate limits
- Returns 1536-dim vectors

**Dependencies**: Phase 2

---

### T038: Write Tests for OpenAI Client
**File**: `tests/unit/infrastructure/external/OpenAIClient.test.ts`  
**Story**: [US2.2]  
**Type**: Test

**Test Cases**:
```typescript
describe('OpenAIClient', () => {
  it('should generate embeddings');
  it('should batch process multiple texts');
  it('should retry on rate limit');
  it('should throw on missing API key');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock OpenAI API

**Dependencies**: T037

---

### T039: Create Use Case - Search Context
**File**: `src/application/use-cases/SearchContext.ts`  
**Story**: [US2.2]  
**Type**: Application

**Implementation**:
- Generate query embedding
- Search Chroma with metadata filters
- Return top N results
- Include metadata (source, date, score)
- **Grep fallback**: If Chroma collection empty (cold start before embeddings generated), fall back to text search using GrepCodebase use case for exact matches only

**Acceptance Criteria**:
- Semantic search via RAG
- Completes in <2 seconds
- Type filtering (discovery, session, code)
- **Graceful degradation**: Falls back to grep when embeddings not yet available (cold start scenario only) — **Satisfies Usability NFR**: "Zero manual intervention"

**Dependencies**: T019, T037

---

### T040: Write Tests for Search Context Use Case
**File**: `tests/unit/application/use-cases/SearchContext.test.ts`  
**Story**: [US2.2]  
**Type**: Test

**Test Cases**:
```typescript
describe('SearchContext', () => {
  it('should perform semantic search');
  it('should filter by type');
  it('should filter by module');
  it('should return top 5 results');
  it('should include relevance scores');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock vector DB and embeddings

**Dependencies**: T039

---

### T041: Create MCP Tool - Context Search
**File**: `src/infrastructure/mcp/tools/ContextSearchTool.ts`  
**Story**: [US2.2]  
**Type**: Infrastructure

**Implementation**:
- Tool name: `context_search`
- Zod schema for validation
- Call SearchContext use case
- Return JSON results

**Acceptance Criteria**:
- Tool registered in MCP
- Parameters validated
- Results formatted as JSON

**Dependencies**: T039

---

### T042: Write Tests for Context Search Tool
**File**: `tests/unit/infrastructure/mcp/tools/ContextSearchTool.test.ts`  
**Story**: [US2.2]  
**Type**: Test

**Test Cases**:
```typescript
describe('ContextSearchTool', () => {
  it('should validate input parameters');
  it('should return search results');
  it('should handle errors gracefully');
  it('should include metadata in response');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock use case

**Dependencies**: T041

---

### T043: Register Context Search Tool in MCP Server
**File**: `src/infrastructure/mcp/server.ts` (update)  
**Story**: [US2.2]  
**Type**: Infrastructure

**Implementation**:
```typescript
function registerTools(server: Server): void {
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: 'context_search',
          description: 'Search project context semantically',
          inputSchema: zodToJsonSchema(ContextSearchSchema),
        },
      ],
    };
  });

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    // Route to context_search handler
  });
}
```

**Acceptance Criteria**:
- Tool listed in MCP
- Tool callable from Claude Desktop
- Error handling

**Dependencies**: T041

---

### T044: Integration Test - Context Search
**File**: `tests/integration/context-search.test.ts`  
**Story**: [US2.2]  
**Type**: Integration Test

**Test Cases**:
```typescript
describe('Context Search Integration', () => {
  it('should search real embeddings');
  it('should return relevant results');
  it('should complete in <2 seconds');
});
```

**Acceptance Criteria**:
- End-to-end test with real Chroma
- Performance validation

**Dependencies**: T043

---

**Phase 5 Checkpoint**: ✅ US2.2 Complete - Semantic search working

---

## Phase 6: US2.3 - Smart File Loading (Dependencies)

**Goal**: `read_file` tool that loads files with dependency parsing

**User Story**: US2.3 - Smart File Loading  
**Duration**: 4-6 hours  
**Dependencies**: Phase 4 (can run parallel with Phase 5)  
**Deliverable**: Working read_file tool with dependency loading

### T045: Create File Parser Utility
**File**: `src/shared/utils/file-parser.ts`  
**Story**: [US2.3]  
**Type**: Shared Utility

**Implementation**:
- Parse TypeScript/JavaScript with Babel
- Extract import statements
- Extract require() calls
- Resolve relative paths

**Acceptance Criteria**:
- Parses .ts, .tsx, .js, .jsx files
- Handles syntax errors gracefully
- Returns list of imports

**Dependencies**: Phase 2

---

### T046: Write Tests for File Parser
**File**: `tests/unit/shared/utils/file-parser.test.ts`  
**Story**: [US2.3]  
**Type**: Test

**Test Cases**:
```typescript
describe('FileParser', () => {
  it('should parse TypeScript imports');
  it('should parse ES6 imports');
  it('should parse require() calls');
  it('should resolve relative paths');
  it('should handle syntax errors');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Test various import styles

**Dependencies**: T045

---

### T047: Create Use Case - Read File With Dependencies
**File**: `src/application/use-cases/ReadFileWithDependencies.ts`  
**Story**: [US2.3]  
**Type**: Application

**Implementation**:
- Read file content
- Parse imports
- Load level 1 dependencies (optional)
- Track file access
- Return file + dependency tree

**Acceptance Criteria**:
- Loads file content
- Optionally loads dependencies
- Tracks access for scoring
- Handles file not found

**Dependencies**: T045

---

### T048: Write Tests for Read File Use Case
**File**: `tests/unit/application/use-cases/ReadFileWithDependencies.test.ts`  
**Story**: [US2.3]  
**Type**: Test

**Test Cases**:
```typescript
describe('ReadFileWithDependencies', () => {
  it('should read file content');
  it('should load level 1 dependencies');
  it('should track file access');
  it('should handle missing file');
  it('should handle parse errors');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock filesystem

**Dependencies**: T047

---

### T049: Create MCP Tool - Read File
**File**: `src/infrastructure/mcp/tools/ReadFileTool.ts`  
**Story**: [US2.3]  
**Type**: Infrastructure

**Implementation**:
- Tool name: `read_file`
- Parameters: path, includeDeps, depth
- Call ReadFileWithDependencies use case
- Return JSON with file content + deps

**Acceptance Criteria**:
- Tool registered in MCP
- Parameters validated
- Security: reject path traversal

**Dependencies**: T047

---

### T050: Write Tests for Read File Tool
**File**: `tests/unit/infrastructure/mcp/tools/ReadFileTool.test.ts`  
**Story**: [US2.3]  
**Type**: Test

**Test Cases**:
```typescript
describe('ReadFileTool', () => {
  it('should validate parameters');
  it('should read file content');
  it('should load dependencies when requested');
  it('should reject path traversal');
  it('should handle errors');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Security tests for path validation

**Dependencies**: T049

---

### T051: Register Read File Tool in MCP Server
**File**: `src/infrastructure/mcp/server.ts` (update)  
**Story**: [US2.3]  
**Type**: Infrastructure

**Add to tools registration**:
```typescript
{
  name: 'read_file',
  description: 'Read file with optional dependency loading',
  inputSchema: zodToJsonSchema(ReadFileSchema),
}
```

**Acceptance Criteria**:
- Tool available in MCP
- Callable from Claude Desktop

**Dependencies**: T049

---

**Phase 6 Checkpoint**: ✅ US2.3 Complete - File reading with dependencies working

---

## Phase 7: US2.4 - Session Auto-Save

**Goal**: Automatic session tracking and saving on MCP disconnect

**User Story**: US2.4 - Session Auto-Save  
**Duration**: 4-6 hours  
**Dependencies**: Phase 4  
**Deliverable**: Automatic session lifecycle management

### T052: Create Service - Session Manager
**File**: `src/application/services/SessionManager.ts`  
**Story**: [US2.4]  
**Type**: Application

**Implementation**:
- Track active session
- Create session on MCP connect
- Update session on activity
- Save session on disconnect
- Handle inactivity timeout (30 min)

**Session State Machine**:
```
┌─────────┐
│ (start) │
└────┬────┘
     │ MCP connect
     ▼
┌─────────┐  activity      ┌─────────┐
│ active  │───────────────▶│ active  │ (self-loop)
└────┬────┘                └─────────┘
     │
     │ disconnect OR 30min inactivity
     ▼
┌───────────┐  prune trigger  ┌──────────┐
│ completed │────────────────▶│ archived │
└───────────┘                 └──────────┘
```

**State Transitions**:
- `active`: Session ongoing, tracking file access and topics
- `completed`: Session ended, pending enrichment
- `archived`: Context pruned to long-term storage (post-MVP)

**Acceptance Criteria**:
- Session created automatically
- Files accessed tracked
- Topics tracked
- Status transitions: active → completed → archived (archived state reserved for post-MVP pruning)

**Dependencies**: T009, T015

---

### T053: Write Tests for Session Manager
**File**: `tests/unit/application/services/SessionManager.test.ts`  
**Story**: [US2.4]  
**Type**: Test

**Test Cases**:
```typescript
describe('SessionManager', () => {
  it('should create session on start');
  it('should track file access');
  it('should track topics');
  it('should save session on end');
  it('should handle inactivity timeout');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock storage

**Dependencies**: T052

---

### T054: Integrate Session Manager into MCP Server
**File**: `src/infrastructure/mcp/server.ts` (update)  
**Story**: [US2.4]  
**Type**: Infrastructure

**Implementation**:
- Create session on server start
- Track tool calls
- Save session on server shutdown
- Handle SIGINT/SIGTERM

**Acceptance Criteria**:
- Session lifecycle automated
- Graceful shutdown
- No data loss

**Dependencies**: T052, T028

---

### T055: Add File Access Tracking to Read File Tool
**File**: `src/infrastructure/mcp/tools/ReadFileTool.ts` (update)  
**Story**: [US2.4]  
**Type**: Infrastructure

**Implementation**:
- Call SessionManager.trackFileAccess() on file read
- Update access count
- Update last accessed timestamp

**Acceptance Criteria**:
- File access tracked automatically
- Session updated

**Dependencies**: T052, T049

---

**Phase 7 Checkpoint**: ✅ US2.4 Complete - Sessions auto-tracked and saved

---

## Phase 8: US3.1 - Discovery Extraction

**Goal**: Automatic discovery extraction from session conversations

**User Story**: US3.1 - Discovery Extraction  
**Duration**: 6-8 hours  
**Dependencies**: Phase 7  
**Deliverable**: Background discovery extraction working

### T056: Create Domain - Discovery Patterns
**File**: `src/domain/rules/discovery-patterns.ts`  
**Story**: [US3.1]  
**Type**: Domain (Rules)

**Implementation**:
```typescript
export const DISCOVERY_PATTERNS = {
  pattern: /(?:we use|pattern is|convention:)\s+(.+)/gi,
  rule: /(?:rule:|must always|requirement:)\s+(.+)/gi,
  decision: /(?:decided to|chose|went with)\s+(.+)/gi,
  issue: /(?:bug:|issue:|fixed:)\s+(.+)/gi,
};

export function extractDiscoveries(
  messages: string[],
  patterns: typeof DISCOVERY_PATTERNS
): Discovery[] {
  // Pure extraction logic
}
```

**Acceptance Criteria**:
- Pure function (no I/O)
- 4 discovery types supported
- Returns 3-5 discoveries per session

**Dependencies**: T010

---

### T057: Write Tests for Discovery Patterns
**File**: `tests/unit/domain/rules/discovery-patterns.test.ts`  
**Story**: [US3.1]  
**Type**: Test

**Test Cases**:
```typescript
describe('extractDiscoveries', () => {
  it('should extract patterns');
  it('should extract rules');
  it('should extract decisions');
  it('should extract issues');
  it('should handle no matches');
  it('should deduplicate discoveries');
});
```

**Acceptance Criteria**:
- Coverage 100% (pure function)
- Test all regex patterns

**Dependencies**: T056

---

### T058: Create Use Case - Extract Discoveries
**File**: `src/application/use-cases/ExtractDiscoveries.ts`  
**Story**: [US3.1]  
**Type**: Application

**Implementation**:
- Load session messages
- Apply discovery patterns
- Save discoveries to database
- Generate embeddings (async)
- Return discovery count

**Acceptance Criteria**:
- Extracts 3-5 discoveries per session
- Saves to SQLite
- Triggers embedding generation

**Dependencies**: T056, T015

---

### T059: Write Tests for Extract Discoveries Use Case
**File**: `tests/unit/application/use-cases/ExtractDiscoveries.test.ts`  
**Story**: [US3.1]  
**Type**: Test

**Test Cases**:
```typescript
describe('ExtractDiscoveries', () => {
  it('should extract from session messages');
  it('should save to database');
  it('should trigger embedding generation');
  it('should handle no discoveries');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock storage

**Dependencies**: T058

---

### T060: Create Background Service - Discovery Extractor
**File**: `src/infrastructure/background/DiscoveryExtractor.ts`  
**Story**: [US3.1]  
**Type**: Infrastructure

**Implementation**:
- Run on session completion
- Call ExtractDiscoveries use case
- Handle errors gracefully
- Log extraction results

**Acceptance Criteria**:
- Runs automatically after session end
- Non-blocking
- Error handling

**Dependencies**: T058

---

### T061: Integrate Discovery Extractor with Session Manager
**File**: `src/application/services/SessionManager.ts` (update)  
**Story**: [US3.1]  
**Type**: Application

**Implementation**:
- Trigger discovery extraction on session end
- Don't block session save

**Acceptance Criteria**:
- Extraction triggered automatically
- Session save not blocked

**Dependencies**: T060, T052

---

**Phase 8 Checkpoint**: ✅ US3.1 Complete - Discovery extraction working

---

## Phase 9: US3.2 - Context Enrichment

**Goal**: Update project.yaml with discoveries

**User Story**: US3.2 - Context Enrichment  
**Duration**: 4-6 hours  
**Dependencies**: Phase 8  
**Deliverable**: Automatic context enrichment working

### T062: Create Use Case - Enrich Context
**File**: `src/application/use-cases/EnrichContext.ts`  
**Story**: [US3.2]  
**Type**: Application

**Implementation**:
- Load project.yaml
- Load recent discoveries
- Map discoveries to modules
- Update module patterns, rules, issues
- Deduplicate similar entries
- Save updated project.yaml

**Acceptance Criteria**:
- Updates patterns, rules, issues
- Preserves existing context
- Deduplicates entries
- Atomic write with backup

**Dependencies**: T008, T017, T010

---

### T063: Write Tests for Enrich Context Use Case
**File**: `tests/unit/application/use-cases/EnrichContext.test.ts`  
**Story**: [US3.2]  
**Type**: Test

**Test Cases**:
```typescript
describe('EnrichContext', () => {
  it('should map discoveries to modules');
  it('should update patterns');
  it('should update business rules');
  it('should update common issues');
  it('should deduplicate entries');
  it('should preserve existing context');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock storage

**Dependencies**: T062

---

### T064: Create Background Service - Context Enricher
**File**: `src/infrastructure/background/ContextEnricher.ts`  
**Story**: [US3.2]  
**Type**: Infrastructure

**Implementation**:
- Run after discovery extraction
- Call EnrichContext use case
- Log enrichment results
- Handle errors

**Acceptance Criteria**:
- Runs automatically
- Non-blocking
- Error handling

**Dependencies**: T062

---

### T065: Integrate Enricher with Discovery Extractor
**File**: `src/infrastructure/background/DiscoveryExtractor.ts` (update)  
**Story**: [US3.2]  
**Type**: Infrastructure

**Implementation**:
- Trigger enrichment after extraction
- Chain async operations

**Acceptance Criteria**:
- Enrichment runs after extraction
- Errors don't crash system

**Dependencies**: T064, T060

---

**Phase 9 Checkpoint**: ✅ US3.2 Complete - Context enrichment working

---

## Phase 10: US4.1 - Smart Context Window Management

**Goal**: Background scorer and pruner to manage context window

**User Story**: US4.1 - Smart Context Window Management  
**Duration**: 6-8 hours  
**Dependencies**: Phase 8 (can run parallel with Phase 9)  
**Deliverable**: Automatic context window management

### T066: Create Use Case - Prune Context
**File**: `src/application/use-cases/PruneContext.ts`  
**Story**: [US4.1]  
**Type**: Application

**Implementation**:
- Calculate window usage (token count)
- Check if > 80% threshold
- Load all active context items
- Sort by score (ascending)
- Archive bottom 20%
- Update status to 'archived'
- Log pruning decisions

**Acceptance Criteria**:
- Activates at 80% threshold
- Archives bottom 20%
- Items remain searchable
- Pruning logged

**Dependencies**: T011, T021

---

### T067: Write Tests for Prune Context Use Case
**File**: `tests/unit/application/use-cases/PruneContext.test.ts`  
**Story**: [US4.1]  
**Type**: Test

**Test Cases**:
```typescript
describe('PruneContext', () => {
  it('should calculate window usage');
  it('should activate at 80% threshold');
  it('should archive bottom 20%');
  it('should preserve high-score items');
  it('should log pruning decisions');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock storage

**Dependencies**: T066

---

### T068: Create Background Service - Context Scorer
**File**: `src/infrastructure/background/ContextScorer.ts`  
**Story**: [US4.1]  
**Type**: Infrastructure

**Implementation**:
- Run every 5 minutes (setInterval)
- Load all context items
- Calculate scores using domain function
- Update scores in database
- Use AbortController for clean shutdown

**Acceptance Criteria**:
- Runs every 5 minutes
- Non-blocking
- Graceful shutdown

**Dependencies**: T021, T011

---

### T069: Create Background Service - Context Pruner
**File**: `src/infrastructure/background/ContextPruner.ts`  
**Story**: [US4.1]  
**Type**: Infrastructure

**Implementation**:
- Run every 10 minutes
- Call PruneContext use case
- Handle errors
- Log results

**Acceptance Criteria**:
- Runs every 10 minutes
- Calls pruner when threshold exceeded
- Error handling

**Dependencies**: T066

---

### T070: Create Background Service Manager
**File**: `src/infrastructure/background/ServiceManager.ts`  
**Story**: [US4.1]  
**Type**: Infrastructure

**Implementation**:
- Manage multiple background services
- Start all services
- Stop all services (graceful shutdown)
- Handle SIGINT/SIGTERM

**Acceptance Criteria**:
- Starts scorer, pruner, enricher
- Graceful shutdown on signal
- Error handling per service

**Dependencies**: T068, T069

---

### T071: Integrate Background Services into MCP Server
**File**: `src/infrastructure/mcp/server.ts` (update)  
**Story**: [US4.1]  
**Type**: Infrastructure

**Implementation**:
- Start ServiceManager on server start
- Stop ServiceManager on server shutdown

**Acceptance Criteria**:
- Services run in background
- Clean shutdown

**Dependencies**: T070

---

**Phase 10 Checkpoint**: ✅ US4.1 Complete - Context window managed automatically

---

## Phase 11: US4.2 - Context Inspection

**Goal**: `context-tool show` command for debugging

**User Story**: US4.2 - Context Inspection  
**Duration**: 2-3 hours  
**Dependencies**: Phase 10  
**Deliverable**: Working show command

### T072: Create CLI Command - Show
**File**: `src/infrastructure/cli/commands/show.ts`  
**Story**: [US4.2]  
**Type**: Infrastructure

**Implementation**:
```typescript
export async function showCommand(): Promise<void> {
  const context = await loadProjectContext();
  const usage = await getContextWindowUsage();
  const activeSession = await getActiveSession();
  const discoveries = await getDiscoveryStats();
  
  console.log(`Project: ${context.project.name} (${context.project.type})`);
  console.log(`Stack: ${context.tech.stack.join(', ')}`);
  console.log(`\nModules (${Object.keys(context.modules).length}):`);
  // ... format output
  console.log(`\nContext Usage: ${(usage * 100).toFixed(1)}%`);
}
```

**Acceptance Criteria**:
- Displays project info
- Shows modules
- Shows active session
- Shows discovery stats
- Shows context window usage

**Dependencies**: T017, T015

---

### T073: Update CLI Entry Point for Show
**File**: `src/infrastructure/cli/index.ts` (update)  
**Story**: [US4.2]  
**Type**: Infrastructure

**Add show command**:
```typescript
case 'show':
  await showCommand();
  break;
```

**Acceptance Criteria**:
- `context-tool show` works
- Help text updated

**Dependencies**: T072

---

**Phase 11 Checkpoint**: ✅ US4.2 Complete - Inspection command working

---

## Phase 12: US5.1 - Resource Access (Additional Resources)

**Goal**: Complete all MCP resources (sessions history)

**User Story**: US5.1 - Resource Access  
**Duration**: 2-3 hours  
**Dependencies**: Phase 4  
**Deliverable**: All MCP resources available

### T074: Create MCP Resource - Recent Sessions
**File**: `src/infrastructure/mcp/resources/SessionsResource.ts`  
**Story**: [US5.1]  
**Type**: Infrastructure

**Implementation**:
- Resource URI: `context://sessions/recent?limit={n}`
- Query recent sessions from SQLite
- Format as markdown list
- Include summary per session

**Acceptance Criteria**:
- Returns recent sessions
- Limit parameter works
- Formatted as markdown

**Dependencies**: T009, T015

---

### T075: Register Sessions Resource in MCP Server
**File**: `src/infrastructure/mcp/server.ts` (update)  
**Story**: [US5.1]  
**Type**: Infrastructure

**Add to resources list**:
```typescript
{
  uri: 'context://sessions/recent',
  name: 'Recent Sessions',
  mimeType: 'text/markdown',
  description: 'List of recent coding sessions',
}
```

**Acceptance Criteria**:
- Resource listed
- Accessible from Claude Desktop

**Dependencies**: T074

---

**Phase 12 Checkpoint**: ✅ US5.1 Complete - All resources available

---

## Phase 13: US5.2 - Tool Invocation (Grep Tool)

**Goal**: Complete all MCP tools (grep_codebase)

**User Story**: US5.2 - Tool Invocation  
**Duration**: 4-6 hours  
**Dependencies**: Phase 4  
**Deliverable**: All MCP tools available

### T076: Create Use Case - Grep Codebase
**File**: `src/application/use-cases/GrepCodebase.ts`  
**Story**: [US5.2]  
**Type**: Application

**Implementation**:
- Execute grep with regex pattern
- Filter by file pattern (glob)
- Return matches with context
- Complete in <1 second

**Acceptance Criteria**:
- Regex search working
- File filtering working
- Context lines included
- Fast (<1 second)

**Dependencies**: Phase 2

---

### T077: Write Tests for Grep Codebase Use Case
**File**: `tests/unit/application/use-cases/GrepCodebase.test.ts`  
**Story**: [US5.2]  
**Type**: Test

**Test Cases**:
```typescript
describe('GrepCodebase', () => {
  it('should search with regex');
  it('should filter by file pattern');
  it('should return context lines');
  it('should handle no matches');
  it('should validate regex');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock filesystem

**Dependencies**: T076

---

### T078: Create MCP Tool - Grep Codebase
**File**: `src/infrastructure/mcp/tools/GrepCodebaseTool.ts`  
**Story**: [US5.2]  
**Type**: Infrastructure

**Implementation**:
- Tool name: `grep_codebase`
- Parameters: pattern, filePattern, caseSensitive, limit
- Call GrepCodebase use case
- Return JSON results

**Acceptance Criteria**:
- Tool registered
- Parameters validated
- Results formatted

**Dependencies**: T076

---

### T079: Write Tests for Grep Codebase Tool
**File**: `tests/unit/infrastructure/mcp/tools/GrepCodebaseTool.test.ts`  
**Story**: [US5.2]  
**Type**: Test

**Test Cases**:
```typescript
describe('GrepCodebaseTool', () => {
  it('should validate parameters');
  it('should return grep results');
  it('should handle invalid regex');
  it('should respect file patterns');
});
```

**Acceptance Criteria**:
- Coverage >= 90%
- Mock use case

**Dependencies**: T078

---

### T080: Register Grep Tool in MCP Server
**File**: `src/infrastructure/mcp/server.ts` (update)  
**Story**: [US5.2]  
**Type**: Infrastructure

**Add to tools**:
```typescript
{
  name: 'grep_codebase',
  description: 'Fast text search with regex',
  inputSchema: zodToJsonSchema(GrepSchema),
}
```

**Acceptance Criteria**:
- Tool available in MCP
- Callable from Claude Desktop

**Dependencies**: T078

---

**Phase 13 Checkpoint**: ✅ US5.2 Complete - All tools available

---

## Final Phase: Polish & Integration

**Goal**: End-to-end testing, documentation, deployment readiness

**Duration**: 4-6 hours  
**Dependencies**: All user story phases  
**Deliverable**: Production-ready MVP

### T081: Create Status Command
**File**: `src/infrastructure/cli/commands/status.ts`  
**Story**: [Polish]  
**Type**: Infrastructure

**Implementation**:
```typescript
export async function statusCommand(): Promise<void> {
  // Query ServiceManager for background service status
  const serviceManager = ServiceManager.getInstance();
  const services = {
    scorer: serviceManager.isScorerRunning(),
    pruner: serviceManager.isPrunerRunning(),
    embeddings: serviceManager.isEmbeddingsRunning()
  };
  
  // Query ContextManager for window usage
  const contextManager = new ContextManager();
  const usage = await contextManager.getWindowUsage(); // Returns 0.0-1.0
  
  // Query SessionManager for active session
  const sessionManager = new SessionManager();
  const session = sessionManager.getActiveSession();
  
  console.log('Context Tool Status:');
  console.log('- Context Scorer:', services.scorer ? '✓ Running (5min interval)' : '✗ Stopped');
  console.log('- Context Pruner:', services.pruner ? '✓ Running (80% threshold)' : '✗ Stopped');
  console.log('- Embeddings Generator:', services.embeddings ? '✓ Running' : '✗ Stopped');
  console.log('- Window Usage:', `${(usage * 100).toFixed(1)}%`);
  console.log('- Active Session:', session ? `${session.id} (${session.filesAccessed.length} files)` : 'None');
}
```

**Implementation Details**:
- **ServiceManager.getInstance()**: Singleton pattern to access background service state
- **ServiceManager.isScorerRunning()**: Returns boolean, checks if scorer interval is active
- **ServiceManager.isPrunerRunning()**: Returns boolean, checks if pruner is monitoring
- **ServiceManager.isEmbeddingsRunning()**: Returns boolean, checks if embeddings queue is processing
- **ContextManager.getWindowUsage()**: Returns float 0.0-1.0 (current tokens / 100k max)
- **SessionManager.getActiveSession()**: Returns Session | null

**Acceptance Criteria**:
- Shows service status (scorer, pruner, embeddings)
- Shows window usage percentage
- Shows active session with file count

**Dependencies**: T070

---

### T082: Update CLI Entry Point for Status
**File**: `src/infrastructure/cli/index.ts` (update)  
**Story**: [Polish]  
**Type**: Infrastructure

**Add status command**:
```typescript
case 'status':
  await statusCommand();
  break;
```

**Acceptance Criteria**:
- `context-tool status` works
- Help text complete

**Dependencies**: T081

---

### T083: Create Embeddings Background Service
**File**: `src/infrastructure/background/EmbeddingsGenerator.ts`  
**Story**: [Polish]  
**Type**: Infrastructure

**Implementation**:
- Run every 15 minutes
- Find discoveries without embeddings
- Batch generate embeddings (100 at a time)
- Store in Chroma
- Handle rate limits

**Acceptance Criteria**:
- Runs every 15 minutes
- Batch processing
- Error handling

**Dependencies**: T037, T019

---

### T084: Integrate Embeddings Generator into Service Manager
**File**: `src/infrastructure/background/ServiceManager.ts` (update)  
**Story**: [Polish]  
**Type**: Infrastructure

**Add embeddings generator to managed services**

**Acceptance Criteria**:
- Generator runs in background
- Graceful shutdown

**Dependencies**: T083, T070

---

### T085: End-to-End Integration Test
**File**: `tests/integration/full-workflow.test.ts`  
**Story**: [Polish]  
**Type**: Integration Test

**Test Cases**:
```typescript
describe('Full Workflow', () => {
  it('should initialize project');
  it('should start MCP server');
  it('should handle session lifecycle');
  it('should extract discoveries');
  it('should enrich context');
  it('should search context');
  it('should manage window usage');
  
  // Error Recovery Tests (NFR: Reliability)
  it('should handle OpenAI rate limit (429) with exponential backoff');
  it('should gracefully degrade when embeddings unavailable');
  it('should handle network failures during embedding generation');
  it('should handle Chroma connection failures');
});
```

**Acceptance Criteria**:
- Complete workflow tested
- All features integrated
- Performance validated
- **Error recovery validated** — **Satisfies Reliability NFR**: "Graceful handling of API failures"

**Dependencies**: All previous tasks

---

### T086: Update README with Usage Instructions
**File**: `README.md`  
**Story**: [Polish]  
**Type**: Documentation

**Content**:
- Installation instructions
- Quick start guide
- Command reference
- Configuration
- Troubleshooting

**Acceptance Criteria**:
- Complete documentation
- Examples provided
- Clear and concise

**Dependencies**: All previous tasks

---

### T087: Final Coverage and Quality Check
**File**: N/A  
**Story**: [Polish]  
**Type**: Quality Assurance

**Checklist**:
- [ ] Run `bun test --coverage`
- [ ] Verify coverage >= 90%
- [ ] Run `bun run build`
- [ ] Verify TypeScript compiles
- [ ] Test all CLI commands
- [ ] Test MCP integration with Claude Desktop
- [ ] Review logs for errors
- [ ] Performance check (init <2min, search <2s)

**Acceptance Criteria**:
- All tests pass
- Coverage >= 90%
- TypeScript compiles
- All commands work
- Performance targets met

**Dependencies**: T086

---

## Implementation Strategy

### MVP Scope (Minimal Viable Product)

**Recommended MVP**: US1.1 + US2.1 + US2.2 only
- Initialize project (`context-tool init`)
- MCP server with resources
- Basic semantic search

**This provides**:
- Core value: Context loading
- Testable: Can validate with real usage
- Foundation: Rest builds on this

**Total tasks for MVP**: ~45 tasks (Phase 1 + Phase 2 + Phase 3 + Phase 4 + Phase 5)

### Incremental Delivery

**Sprint 1 (Weeks 1-2)**: MVP (US1.1, US2.1, US2.2)
**Sprint 2 (Weeks 3-4)**: File loading + Sessions (US2.3, US2.4)
**Sprint 3 (Weeks 5-6)**: Enrichment (US3.1, US3.2)
**Sprint 4 (Weeks 7-8)**: Context Management + Polish (US4.1, US4.2, US5.1, US5.2)

### Parallel Execution Opportunities

**After Phase 2 (Foundation)**:
- Phase 3 (US1.1) starts

**After Phase 4 (US2.1)**:
- Phase 5 (US2.2), Phase 6 (US2.3), Phase 7 (US2.4) can run in parallel

**After Phase 8 (US3.1)**:
- Phase 9 (US3.2) and Phase 10 (US4.1) can run in parallel

**After Phase 10 (US4.1)**:
- Phase 11 (US4.2), Phase 12 (US5.1), Phase 13 (US5.2) can run in parallel

### Task Execution Example

```bash
# Phase 1: Setup (sequential)
T001 → T002 [P] T003 [P] T004 → T005 [P] T006 → T007

# Phase 2: Foundation (parallel opportunities)
T008 [P] T009 [P] T010 [P] T011 [P] T012 [P] T013 [P] T014
→ T015 → T016 [P] (T017 → T018) [P] (T019 → T020)

# Phase 3: US1.1 (sequential with test pairs)
T021 → T022 → T023 → T024 → T025 → T026 → T027

# And so on...
```

---

## Success Criteria

### MVP Complete When:

**Functional**:
- [x] `context-tool init` creates project.yaml
- [x] `context-tool serve` starts MCP server
- [x] Resources accessible in Claude Desktop
- [x] `context_search` tool returns relevant results
- [x] All tests pass
- [x] Coverage >= 90%

**Quality**:
- [x] TypeScript compiles with no errors
- [x] No `any` types (unless justified)
- [x] All acceptance criteria met
- [x] Performance targets hit

**Validation**:
- [x] Used on real project (mon-saas)
- [x] AI can access context without manual loading
- [x] Search returns relevant discoveries

---

## Task Summary

**Total Tasks**: 87  
**Domain Tasks**: 8 (pure functions, models)  
**Application Tasks**: 18 (use cases, services)  
**Infrastructure Tasks**: 34 (MCP, CLI, storage, background)  
**Test Tasks**: 20 (unit tests)  
**Integration Tests**: 4  
**Documentation/Polish**: 3

**Coverage Target**: 90%+ enforced by Vitest config

**Parallel Opportunities**: 45+ tasks can run in parallel with others

---

**END OF TASKS**
