# Kioku Architecture

This document describes the monorepo architecture and package dependencies for the Kioku project.

## Package Structure

Kioku is organized as a monorepo with 4 packages:

```
packages/
├── shared/      # Shared utilities, types, error classes
├── api/         # Core business logic (MCP server, domain, application, infrastructure)
├── cli/         # Command-line interface
└── ui/          # Dashboard web interface
```

## Package Dependencies

### Dependency Graph

```
shared (no workspace dependencies)
  ↑
  ├── api → shared
  ↑
  ├── cli → shared, api
  └── ui → shared, api
```

### Dependency Rules

**Allowed:**
- `api` can import from `shared` ✅
- `cli` can import from `shared`, `api` ✅
- `ui` can import from `shared`, `api` ✅

**Forbidden:**
- `shared` cannot import from any workspace package ❌
- `api` cannot import from `cli` or `ui` ❌
- `cli` cannot import from `ui` ❌
- `ui` cannot import from `cli` ❌
- No circular dependencies ❌

These rules are enforced by ESLint with `no-restricted-imports` rules.

## Package Details

### @kioku/shared

**Purpose:** Shared utilities, types, and constants used across multiple packages.

**Contents:**
- Error classes (`src/errors/`)
- Shared types (future)
- Pure utility functions (future)

**Dependencies:** None (must remain dependency-free)

**Exports:** `index.ts` re-exports all shared utilities

### @kioku/api

**Purpose:** Core business logic following Onion Architecture.

**Contents:**
- **Domain Layer** (`src/domain/`): Pure business logic
  - Models: Data structures
  - Calculations: Pure functions
  - Rules: Business rules
- **Application Layer** (`src/application/`): Use cases and orchestration
  - Use cases: Feature workflows
  - Services: Application services
  - Ports: Interfaces for infrastructure
- **Infrastructure Layer** (`src/infrastructure/`): External integrations
  - Storage: Database, file system (SQLite, Chroma, YAML)
  - MCP: Model Context Protocol server
  - External: OpenAI, Anthropic APIs
  - Background: Scorer, pruner services
  - Monitoring: Metrics, health checks

**Dependencies:** `@kioku/shared`

**Exports:** Domain models, application services, use cases, infrastructure adapters

**Architecture Rules (enforced by ESLint):**
- Domain layer: Pure functions, no dependencies on other layers
- Application layer: Can depend on Domain only
- Infrastructure layer: Can depend on Domain, Application, Shared

### @kioku/cli

**Purpose:** Command-line interface for Kioku.

**Contents:**
- Commands: `init`, `serve`, `status`, `show`, `dashboard`, `doctor`, `setup`
- Logger: Winston-based logging
- Entry point: `index.ts` with command parsing

**Dependencies:** `@kioku/shared`, `@kioku/api`

**Build:** TypeScript compilation to `dist/`

**Binary:** Configured in `package.json` as `kioku` executable

### @kioku/ui

**Purpose:** Web dashboard for visualizing project context and metrics.

**Contents:**
- React components (`src/components/`)
- API client (`src/services/`)
- Types (`src/types/`)
- Utilities (`src/utils/`)

**Dependencies:** `@kioku/shared`, `@kioku/api`, React ecosystem

**Build:** Vite for optimized production bundles

**Tech Stack:**
- React 18.3
- TanStack Query (data fetching)
- Recharts + D3 (charts)
- Tailwind CSS (styling)

## Build System

**Package Manager:** Bun with workspaces

**Root Scripts:**
```bash
bun run build          # Build all packages (shared → api → cli → ui)
bun run build:shared   # Build @kioku/shared
bun run build:api      # Build @kioku/api
bun run build:cli      # Build @kioku/cli
bun run build:ui       # Build @kioku/ui (Vite)
```

**Build Order:**
1. `@kioku/shared` (no dependencies)
2. `@kioku/api` (depends on shared)
3. `@kioku/cli` (depends on shared, api)
4. `@kioku/ui` (depends on shared, api)

## Quality Gates

**Type Checking:**
```bash
bun run type-check     # TypeScript strict mode for all packages
```

**Linting:**
```bash
bun run lint           # ESLint with architecture boundary enforcement
bun run lint:fix       # Auto-fix issues
```

**Testing:**
```bash
bun run test:api       # Run API package tests (338 passing)
bun run test:cli       # Run CLI package tests
bun run test:shared    # Run shared package tests
```

**Full Quality Gate:**
```bash
bun run quality-gate   # Type check + lint + tests
```

## Architecture Principles

### Onion Architecture (API Package)

The API package follows Onion Architecture with dependency inversion:

```
Infrastructure (🔴 I/O Layer)
  → Application (🟡 Orchestration)
    → Domain (🟢 Pure Logic)
```

**Benefits:**
- Testable: Pure domain logic is easy to test
- Flexible: Infrastructure can be swapped without changing domain
- Maintainable: Clear separation of concerns

### Functional Programming

**Domain layer uses functional programming:**
- Pure functions (no side effects)
- Immutable data structures
- Composable operations
- Easy to test and reason about

**Infrastructure layer handles side effects:**
- File I/O
- Database operations
- API calls
- Background jobs

### Package Boundaries

Packages are organized by **deployment unit** and **responsibility**:

- **shared**: Truly shared code (minimal)
- **api**: Business logic (deployed as MCP server)
- **cli**: User interface (deployed as CLI tool)
- **ui**: Web interface (deployed as dashboard)

This prevents tight coupling and enables independent deployment.

## File Organization

### Recommended Structure Within Packages

```
packages/[package-name]/
├── src/
│   ├── index.ts           # Public API (exports)
│   ├── [feature]/         # Feature directories
│   │   ├── index.ts       # Feature exports
│   │   └── *.ts           # Feature implementation
│   └── ...
├── tests/                 # Tests mirror src/ structure
│   └── [feature]/
│       └── *.test.ts
├── dist/                  # Build output (gitignored)
├── package.json           # Package metadata
└── tsconfig.json          # TypeScript config
```

### Import Conventions

**Within a package:**
```typescript
import { Model } from 'domain/models';        // Path alias (API package)
import { logger } from '../logger';           // Relative import
```

**Across packages:**
```typescript
import { ErrorClass } from '@kioku/shared';   // Workspace import
import { UseCase } from '@kioku/api';         // Workspace import
```

## Adding New Packages

To add a new package to the monorepo:

1. **Create package directory:**
   ```bash
   mkdir -p packages/new-package/src
   ```

2. **Create package.json:**
   ```json
   {
     "name": "@kioku/new-package",
     "version": "0.1.0",
     "type": "module",
     "main": "dist/index.js",
     "types": "dist/index.d.ts",
     "scripts": {
       "build": "tsc -p tsconfig.json",
       "test": "bun test"
     },
     "dependencies": {
       "@kioku/shared": "workspace:*"
     }
   }
   ```

3. **Create tsconfig.json:**
   ```json
   {
     "extends": "../../tsconfig.json",
     "compilerOptions": {
       "outDir": "dist",
       "rootDir": "src",
       "declaration": true,
       "declarationMap": true
     },
     "include": ["src/**/*"]
   }
   ```

4. **Add build script to root package.json:**
   ```json
   {
     "scripts": {
       "build:new-package": "bun --filter=@kioku/new-package run build"
     }
   }
   ```

5. **Update ESLint config** with package boundary rules if needed

6. **Run:** `bun install` to link workspace packages

## Troubleshooting

### Import Errors

**Problem:** `Cannot find module '@kioku/xxx'`

**Solution:** Run `bun install` to link workspace packages

**Problem:** TypeScript can't find types for workspace package

**Solution:** Ensure the package has `declaration: true` in tsconfig and rebuild with `bun run build:[package]`

### Build Errors

**Problem:** Package builds fail with "Cannot find module"

**Solution:** Build dependencies first (shared → api → cli/ui)

**Problem:** Circular dependency warnings

**Solution:** Check dependency graph with `bun pm ls --all`, fix import cycles

### Lint Errors

**Problem:** "PACKAGE BOUNDARY VIOLATION" error

**Solution:** Follow the dependency rules above. Don't import from CLI/UI in API package.

**Problem:** "APPLICATION LAYER VIOLATION" in API package

**Solution:** Application layer can only import from Domain. Move shared code to domain or use dependency injection.

## References

- [Onion Architecture](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/)
- [Functional Programming in TypeScript](https://www.manning.com/books/grokking-simplicity)
- [Bun Workspaces](https://bun.sh/docs/install/workspaces)
- [TypeScript Project References](https://www.typescriptlang.org/docs/handbook/project-references.html)
