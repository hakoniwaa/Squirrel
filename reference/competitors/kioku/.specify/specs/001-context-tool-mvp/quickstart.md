# Quickstart Guide: Context Tool MVP

**Date**: 2025-01-15  
**Audience**: Developers implementing the Context Tool MVP  
**Purpose**: Step-by-step implementation guide  
**Status**: Complete

---

## Prerequisites

Before starting implementation:

- [x] Read `.specify/memory/constitution.md` (CRITICAL)
- [x] Read `.specify/specs/001-context-tool-mvp/spec.md`
- [x] Read `.specify/specs/001-context-tool-mvp/plan.md`
- [x] Read `.specify/specs/001-context-tool-mvp/research.md`
- [x] Read `.specify/specs/001-context-tool-mvp/data-model.md`
- [x] Bun installed (`curl -fsSL https://bun.sh/install | bash`)
- [x] OpenAI API key ready (`export OPENAI_API_KEY=sk-...`)
- [x] Zed editor with Claude Code (recommended)

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Storage layer working, basic project structure setup

#### Step 1.1: Project Setup

```bash
# Initialize project
cd /Users/sovanaryththorng/sanzoku_labs/kioku
bun init

# Install dependencies
bun add @modelcontextprotocol/sdk
bun add chromadb
bun add yaml
bun add zod
bun add winston
bun add @babel/parser @babel/traverse

# Install dev dependencies
bun add -d @types/node
bun add -d vitest
bun add -d typescript
```

#### Step 1.2: TypeScript Configuration

Create `tsconfig.json`:

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

#### Step 1.3: Vitest Configuration

Create `vitest.config.ts`:

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

#### Step 1.4: Create Project Structure

```bash
# Create directory structure
mkdir -p src/domain/{models,calculations,rules}
mkdir -p src/application/{use-cases,services,ports}
mkdir -p src/infrastructure/{storage,mcp,cli,background,external}
mkdir -p src/infrastructure/mcp/{resources,tools}
mkdir -p src/infrastructure/cli/commands
mkdir -p src/shared/{types,utils,errors}
mkdir -p tests/{unit,integration}
mkdir -p tests/unit/{domain,application,infrastructure}
```

#### Step 1.5: Domain Models (Pure TypeScript)

**Create: `src/domain/models/ProjectContext.ts`**

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

**Create similar files for:**
- `src/domain/models/Session.ts`
- `src/domain/models/Discovery.ts`
- `src/domain/models/ContextItem.ts`
- `src/domain/models/Config.ts`

(See data-model.md for full definitions)

#### Step 1.6: Storage Layer (Infrastructure)

**Create: `src/infrastructure/storage/sqlite-adapter.ts`**

```typescript
import { Database } from 'bun:sqlite';
import type { Session, Discovery, ContextItem } from '@domain/models';

export class SQLiteAdapter {
  private db: Database;

  constructor(dbPath: string) {
    this.db = new Database(dbPath, { create: true, readwrite: true });
    this.initialize();
  }

  private initialize(): void {
    // Enable WAL mode (critical for performance!)
    this.db.run('PRAGMA journal_mode = WAL;');
    this.db.run('PRAGMA synchronous = NORMAL;');
    this.db.run('PRAGMA cache_size = -64000;');
    
    // Create tables
    this.createTables();
  }

  private createTables(): void {
    // Sessions table
    this.db.run(`
      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL,
        started_at INTEGER NOT NULL,
        ended_at INTEGER,
        status TEXT NOT NULL CHECK(status IN ('active', 'completed', 'archived')),
        files_accessed TEXT NOT NULL DEFAULT '[]',
        topics TEXT NOT NULL DEFAULT '[]',
        metadata TEXT NOT NULL DEFAULT '{}',
        created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
        updated_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
      )
    `);

    this.db.run('CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id)');
    this.db.run('CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)');
    this.db.run('CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started_at DESC)');

    // Discoveries table (see data-model.md for full schema)
    // Context items table (see data-model.md for full schema)
  }

  // Methods: saveSession, getSession, findSessions, etc.
  // See research.md for patterns
}
```

**Create similar adapters:**
- `src/infrastructure/storage/yaml-handler.ts`
- `src/infrastructure/storage/chroma-adapter.ts`

(See research.md for implementation patterns)

#### Step 1.7: Write Tests FIRST (TDD)

**Create: `tests/unit/infrastructure/storage/sqlite-adapter.test.ts`**

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { SQLiteAdapter } from '@infrastructure/storage/sqlite-adapter';
import { unlinkSync } from 'fs';

describe('SQLiteAdapter', () => {
  const testDbPath = './.context/test.db';
  let adapter: SQLiteAdapter;

  beforeEach(() => {
    adapter = new SQLiteAdapter(testDbPath);
  });

  afterEach(() => {
    adapter.close();
    try { unlinkSync(testDbPath); } catch {}
  });

  describe('saveSession', () => {
    it('should save session to database', async () => {
      const session = {
        id: 'session-1',
        projectId: 'project-1',
        startedAt: new Date(),
        status: 'active' as const,
        filesAccessed: [],
        topics: [],
        metadata: {},
      };

      await adapter.saveSession(session);
      const loaded = await adapter.getSession('session-1');

      expect(loaded).toBeDefined();
      expect(loaded.id).toBe('session-1');
      expect(loaded.status).toBe('active');
    });
  });
});
```

**Run tests:**
```bash
bun test                    # Run all tests
bun test --coverage         # Check coverage (must be >= 90%)
```

---

### Phase 2: Core Logic (Weeks 3-4)

**Goal:** Init command working, context loading, RAG search functional

#### Step 2.1: Domain Calculations (Pure Functions)

**Create: `src/domain/calculations/context-scoring.ts`**

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
  const decayedScore = Math.max(0, 1 - (daysSince / 30));
  return decayedScore;
}

function normalizeAccessCount(count: number, maxCount: number = 100): number {
  return Math.min(count / maxCount, 1.0);
}
```

**Write tests FIRST:**

```typescript
// tests/unit/domain/calculations/context-scoring.test.ts
describe('calculateContextScore', () => {
  it('should return high score for recently accessed items', () => {
    const now = new Date('2025-01-15');
    const recent = new Date('2025-01-14');
    const score = calculateContextScore(recent, 10, now);
    expect(score).toBeGreaterThan(0.8);
  });

  it('should return low score for old items', () => {
    const now = new Date('2025-01-15');
    const old = new Date('2024-12-01');
    const score = calculateContextScore(old, 0, now);
    expect(score).toBeLessThan(0.3);
  });
});
```

#### Step 2.2: Use Cases (Application Layer)

**Create: `src/application/use-cases/InitializeProject.ts`**

```typescript
import type { IStorage } from '@application/ports/IStorage';
import type { ProjectContext } from '@domain/models/ProjectContext';

export class InitializeProject {
  constructor(private storage: IStorage) {}

  async execute(projectPath: string): Promise<ProjectContext> {
    // 1. Scan project directory
    const projectInfo = await this.scanProject(projectPath);
    
    // 2. Detect tech stack
    const techStack = await this.detectTechStack(projectPath);
    
    // 3. Identify modules
    const modules = await this.identifyModules(projectPath);
    
    // 4. Create project context
    const context: ProjectContext = {
      version: '1.0',
      project: projectInfo,
      tech: techStack,
      architecture: this.inferArchitecture(modules),
      modules,
      metadata: {
        createdAt: new Date(),
        updatedAt: new Date(),
        lastScanAt: new Date(),
      },
    };
    
    // 5. Save to storage
    await this.storage.saveProjectContext(context);
    
    return context;
  }

  // Implementation methods...
}
```

**Write tests FIRST:**

```typescript
// tests/unit/application/use-cases/InitializeProject.test.ts
describe('InitializeProject', () => {
  it('should create project context', async () => {
    const mockStorage = {
      saveProjectContext: vi.fn(),
    };
    const useCase = new InitializeProject(mockStorage);
    
    const context = await useCase.execute('/path/to/project');
    
    expect(context.version).toBe('1.0');
    expect(mockStorage.saveProjectContext).toHaveBeenCalled();
  });
});
```

#### Step 2.3: MCP Server (Infrastructure)

**Create: `src/infrastructure/mcp/server.ts`**

```typescript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

export async function startMCPServer(): Promise<void> {
  const server = new Server(
    { name: 'context-tool', version: '1.0.0' },
    { capabilities: { resources: {}, tools: {} } }
  );

  // Register resources
  registerResources(server);
  
  // Register tools
  registerTools(server);

  // Connect transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('Context Tool MCP server started');
}
```

(See research.md and contracts/ for full implementation)

---

### Phase 3: Enrichment (Weeks 5-6)

**Goal:** Discovery extraction, embeddings, background services

#### Step 3.1: Discovery Extraction (Domain Rules)

**Create: `src/domain/rules/discovery-patterns.ts`**

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
  const discoveries: Discovery[] = [];
  
  for (const message of messages) {
    for (const [type, regex] of Object.entries(patterns)) {
      const matches = message.matchAll(regex);
      for (const match of matches) {
        discoveries.push({
          type: type as DiscoveryType,
          content: match[1].trim(),
          confidence: 1.0,  // Regex match = 100% confidence
        });
      }
    }
  }
  
  return discoveries;
}
```

#### Step 3.2: Background Services

**Create: `src/infrastructure/background/ContextScorer.ts`**

```typescript
export class ContextScorer {
  private intervalId?: Timer;

  constructor(
    private storage: IStorage,
    private intervalMs: number = 5 * 60 * 1000  // 5 minutes
  ) {}

  start(): void {
    this.intervalId = setInterval(() => this.run(), this.intervalMs);
    logger.info('Context scorer started');
  }

  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      logger.info('Context scorer stopped');
    }
  }

  private async run(): Promise<void> {
    try {
      const items = await this.storage.getActiveContextItems();
      const scored = items.map(item => ({
        ...item,
        score: calculateContextScore(item.lastAccessedAt, item.accessCount),
      }));
      await this.storage.updateContextScores(scored);
      
      logger.debug('Context scoring complete', { itemsScored: scored.length });
    } catch (error) {
      logger.error('Context scoring failed', { error });
    }
  }
}
```

---

### Phase 4: Polish (Weeks 7-8)

**Goal:** CLI commands, logging, testing, documentation

#### Step 4.1: CLI Commands

**Create: `src/infrastructure/cli/commands/init.ts`**

```typescript
import { InitializeProject } from '@application/use-cases/InitializeProject';

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

#### Step 4.2: Logging Setup

**Create: `src/infrastructure/cli/logger.ts`**

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
    new winston.transports.File({
      filename: '.context/context-tool.log',
    }),
  ],
});
```

---

## Testing Strategy

### Test Pyramid

```
        Integration Tests (10%)
              /\
             /  \
            /    \
           /      \
          /        \
         /          \
        /            \
       /  Unit Tests  \
      /     (90%)      \
     /__________________\
```

**Unit Tests:**
- Domain: 100% coverage (pure functions, easy to test)
- Application: 95% coverage (use cases with mocks)
- Infrastructure: 80% coverage (adapters with mocks)

**Integration Tests:**
- Full workflow: init → serve → search → enrich
- MCP server integration
- Real database operations (test DB)

### Running Tests

```bash
# Run all tests
bun test

# Run with coverage
bun test --coverage

# Run specific test file
bun test tests/unit/domain/calculations/context-scoring.test.ts

# Run in watch mode (during development)
bun test --watch

# Check coverage meets threshold (90%)
bun test --coverage --reporter=verbose
```

---

## Development Workflow

### For Each Task:

1. **Read task description** (from tasks.md when available)
2. **Write tests FIRST** (Red)
   ```bash
   # Create test file
   touch tests/unit/domain/calculations/my-feature.test.ts
   
   # Write failing test
   bun test tests/unit/domain/calculations/my-feature.test.ts
   # ❌ Test fails (expected)
   ```

3. **Implement code** (Green)
   ```bash
   # Write minimum code to pass test
   bun test tests/unit/domain/calculations/my-feature.test.ts
   # ✅ Test passes
   ```

4. **Refactor** (Blue)
   ```bash
   # Improve code quality
   # Run tests to ensure still passing
   bun test
   ```

5. **Check coverage**
   ```bash
   bun test --coverage
   # Verify >= 90%
   ```

6. **Build**
   ```bash
   bun run build
   # Verify TypeScript compiles
   ```

7. **Ready for commit** (tell user when ready)

### Quality Gates

Before marking task complete:

- [x] All tests pass (`bun test`)
- [x] Coverage >= 90% (`bun test --coverage`)
- [x] TypeScript compiles (`bun run build`)
- [x] No linter errors
- [x] Acceptance criteria met
- [x] Error handling implemented
- [x] Logging added
- [x] No `console.log` (use logger)
- [x] No `any` types

---

## Common Patterns

### Pure Function Pattern (Domain)

```typescript
// ✅ GOOD - Pure, immutable
export function enrichModule(
  module: ModuleContext,
  discoveries: Discovery[]
): ModuleContext {
  return {
    ...module,
    patterns: [...module.patterns, ...extractPatterns(discoveries)],
  };
}

// ❌ BAD - Mutates input
export function enrichModule(
  module: ModuleContext,
  discoveries: Discovery[]
): void {
  module.patterns.push(...extractPatterns(discoveries));
}
```

### Use Case Pattern (Application)

```typescript
export class SearchContext {
  constructor(
    private vectorDB: IVectorDB,
    private embeddings: IEmbedding
  ) {}

  async execute(query: string, limit: number = 5): Promise<SearchResult[]> {
    // 1. Generate query embedding
    const embedding = await this.embeddings.generate(query);
    
    // 2. Search vector DB
    const results = await this.vectorDB.search(embedding, limit);
    
    // 3. Return formatted results
    return results.map(formatSearchResult);
  }
}
```

### Adapter Pattern (Infrastructure)

```typescript
export class ChromaAdapter implements IVectorDB {
  private client: ChromaClient;
  private collection: Collection;

  async search(embedding: number[], limit: number): Promise<SearchResult[]> {
    const results = await this.collection.query({
      queryEmbeddings: [embedding],
      nResults: limit,
    });
    
    return this.mapToSearchResults(results);
  }
}
```

---

## Troubleshooting

### Tests Failing

1. Check error message carefully
2. Verify test expectations vs. actual
3. Ensure function is pure (for domain)
4. Run: `bun install` (dependencies)
5. Run: `bun run build` (TypeScript errors)

### TypeScript Errors

1. Check `tsconfig.json` settings
2. Verify import paths
3. Check for circular dependencies
4. Ensure return types explicit
5. No `any` types

### Coverage < 90%

1. Run: `bun test --coverage`
2. Check which lines uncovered
3. Add missing tests
4. Consider if code is testable

---

## Next Steps

After completing Phase 1-4:

1. **Manual Testing**
   - Run on real project (mon-saas)
   - Test all commands
   - Verify MCP integration with Claude Desktop

2. **Documentation**
   - Update README.md
   - Add JSDoc comments
   - Create user guide

3. **Deployment**
   - Publish to npm (optional)
   - Create release notes
   - Tag version

---

**Ready to implement! Start with Phase 1, Step 1.1.**

For detailed technical decisions, see:
- `research.md` - Technology patterns
- `data-model.md` - Data structures
- `contracts/` - API definitions
- `plan.md` - Architecture overview

**Remember:** TDD is mandatory, coverage >= 90%, tests before code!

---

**END OF QUICKSTART**
