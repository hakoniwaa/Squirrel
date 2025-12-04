# Data Model: Documentation Organization and Monorepo Restructure

**Feature**: 003-documentation-organization-and  
**Date**: 2025-10-11  
**Status**: Complete

## Purpose

This document defines the file mapping and package structure for the monorepo reorganization.

---

## 1. Documentation File Mapping

### Files to Move to `docs/`

| Current Location | Target Location | New Name Rationale |
|------------------|-----------------|-------------------|
| `/SETUP_GUIDE.md` | `/docs/setup-guide.md` | Descriptive, kebab-case |
| `/CHANGELOG.md` | `/docs/changelog.md` | Lowercase for consistency |
| `/kioku.md` | `/docs/project-overview.md` | More descriptive name |
| `/research.md` | `/docs/research.md` | Already kebab-case |
| `/MERGE_READINESS.md` | `/docs/merge-readiness.md` | Kebab-case conversion |
| `/FUTURE_FEATURES.md` | `/docs/future-features.md` | Kebab-case conversion |

### Files Staying at Root

| File | Location | Rationale |
|------|----------|-----------|
| `README.md` | `/README.md` | Primary project entry point |
| `CLAUDE.md` | `/CLAUDE.md` | AI development guide (spec requirement) |

### Files Not Moving (Special Directories)

| Path | Status | Rationale |
|------|--------|-----------|
| `.specify/` | Unchanged | Spec-driven development artifacts |
| `dashboard/README.md` | Moves with dashboard | Part of UI package |

---

## 2. Source Code Package Mapping

### Package: `@kioku/cli`

**Purpose**: Command-line interface for Kioku

**Source Mappings**:
| Current Path | Target Path | Notes |
|--------------|-------------|-------|
| `src/infrastructure/cli/` | `packages/cli/src/` | All CLI command code |
| `src/infrastructure/cli/commands/` | `packages/cli/src/commands/` | Command implementations |
| `tests/unit/infrastructure/cli/` | `packages/cli/tests/` | CLI unit tests |

**Dependencies**:
- `@kioku/shared` (types, utilities)
- `@kioku/api` (for invoking API functionality)

**Entry Point**: `packages/cli/src/index.ts`

---

### Package: `@kioku/api`

**Purpose**: MCP server and core business logic

**Source Mappings**:
| Current Path | Target Path | Notes |
|--------------|-------------|-------|
| `src/domain/` | `packages/api/src/domain/` | Pure business logic |
| `src/application/` | `packages/api/src/application/` | Use cases, services |
| `src/infrastructure/mcp/` | `packages/api/src/infrastructure/mcp/` | MCP protocol |
| `src/infrastructure/storage/` | `packages/api/src/infrastructure/storage/` | Database, files |
| `src/infrastructure/background/` | `packages/api/src/infrastructure/background/` | Background services |
| `tests/unit/domain/` | `packages/api/tests/domain/` | Domain tests |
| `tests/unit/application/` | `packages/api/tests/application/` | Application tests |
| `tests/integration/` | `packages/api/tests/integration/` | Integration tests |

**Dependencies**:
- `@kioku/shared` (types, utilities)

**Entry Point**: `packages/api/src/index.ts`

---

### Package: `@kioku/ui`

**Purpose**: Web dashboard interface

**Source Mappings**:
| Current Path | Target Path | Notes |
|--------------|-------------|-------|
| `dashboard/` | `packages/ui/src/` | All UI code |
| `dashboard/public/` | `packages/ui/public/` | Static assets |
| `dashboard/README.md` | `packages/ui/README.md` | UI-specific docs |

**Dependencies**:
- `@kioku/shared` (types, utilities)
- `@kioku/api` (for API calls)

**Entry Point**: `packages/ui/src/index.ts` or `packages/ui/src/main.ts`

---

### Package: `@kioku/shared`

**Purpose**: Shared types, utilities, and constants

**Source Mappings**:
| Current Path | Target Path | Notes |
|--------------|-------------|-------|
| `types/` | `packages/shared/src/types/` | TypeScript type definitions |
| `src/shared/` (if exists) | `packages/shared/src/` | Shared utilities |

**Dependencies**:
- None (shared package should be dependency-free)

**Entry Point**: `packages/shared/src/index.ts`

---

## 3. Configuration File Mapping

### Root-Level Configuration

| File | Location | Changes |
|------|----------|---------|
| `package.json` | Root | Add `workspaces: ["packages/*"]` |
| `tsconfig.json` | Root | Becomes base config |
| `bunfig.toml` | Root | Update for monorepo if needed |
| `.gitignore` | Root | Unchanged |
| `eslint.config.mjs` | Root | May need paths update |

### Package-Level Configuration

Each package gets:
- `package.json` (name, dependencies, scripts)
- `tsconfig.json` (extends root, package-specific paths)
- `README.md` (package documentation)

---

## 4. Test File Mapping

### Test Organization Pattern

```
packages/{package-name}/
├── src/
│   └── {feature}/
│       └── file.ts
└── tests/
    └── {feature}/
        └── file.test.ts
```

### Test Mappings

| Current Test Path | Target Test Path | Package |
|-------------------|------------------|---------|
| `tests/unit/infrastructure/cli/` | `packages/cli/tests/` | cli |
| `tests/unit/domain/` | `packages/api/tests/domain/` | api |
| `tests/unit/application/` | `packages/api/tests/application/` | api |
| `tests/unit/infrastructure/mcp/` | `packages/api/tests/infrastructure/mcp/` | api |
| `tests/integration/` | `packages/api/tests/integration/` | api |

---

## 5. Import Path Transformations

### Current Import Patterns

```typescript
// Absolute imports
import { Something } from '@/domain/models/Something';
import { Service } from '@/application/services/Service';
import { Command } from '@/infrastructure/cli/commands/Command';

// Relative imports
import { helper } from '../../../utils/helper';
import type { Type } from '../../types';
```

### Target Import Patterns

```typescript
// Cross-package imports (via workspace)
import { Something } from '@kioku/api';
import { Type } from '@kioku/shared';

// Within-package imports
import { helper } from '../utils/helper';
import { Service } from './Service';
```

### Transformation Rules

| Current Pattern | Target Pattern | Condition |
|-----------------|----------------|-----------|
| `@/domain/**` | `@kioku/api` or relative | If in API package, use relative; if external, use @kioku/api |
| `@/application/**` | `@kioku/api` or relative | Same as above |
| `@/infrastructure/cli/**` | `@kioku/cli` or relative | If in CLI package, use relative; if external, use @kioku/cli |
| `@/infrastructure/mcp/**` | `@kioku/api` or relative | Part of API package |
| `@/shared/**` | `@kioku/shared` | Always use workspace import |
| `types/**` | `@kioku/shared` | Types moved to shared package |

---

## 6. Package Dependency Graph

```
@kioku/cli
├── depends on: @kioku/shared
└── depends on: @kioku/api

@kioku/api
└── depends on: @kioku/shared

@kioku/ui
├── depends on: @kioku/shared
└── depends on: @kioku/api

@kioku/shared
└── (no dependencies)
```

**Rules**:
- No circular dependencies allowed
- Shared package is leaf node (no internal dependencies)
- CLI and UI can depend on API
- API cannot depend on CLI or UI

---

## 7. Build Output Mapping

### Current Build Output

```
dist/
└── (all compiled files)
```

### Target Build Output

```
packages/cli/dist/
packages/api/dist/
packages/ui/dist/
packages/shared/dist/
```

Each package builds independently to its own `dist/` folder.

---

## 8. Entry Points

### Package Entry Points

| Package | Entry Point | Purpose |
|---------|-------------|---------|
| `@kioku/cli` | `packages/cli/src/index.ts` | CLI command router |
| `@kioku/api` | `packages/api/src/index.ts` | MCP server entry |
| `@kioku/ui` | `packages/ui/src/main.ts` | Web app entry |
| `@kioku/shared` | `packages/shared/src/index.ts` | Exports all shared code |

### Binary/Executable Configuration

```json
// Root package.json
{
  "bin": {
    "kioku": "./packages/cli/dist/index.js"
  }
}
```

---

## 9. Migration Validation Checkpoints

### Checkpoint 1: Documentation Moved
- [ ] All 6 files moved to docs/
- [ ] All files renamed to kebab-case
- [ ] README.md and CLAUDE.md updated with correct links
- [ ] No broken links in any markdown files

### Checkpoint 2: Package Structure Created
- [ ] packages/ directory exists
- [ ] All 4 package directories created (cli, api, ui, shared)
- [ ] Each package has package.json, tsconfig.json, README.md
- [ ] Root package.json has workspaces configured

### Checkpoint 3: Code Moved
- [ ] All source files moved to correct packages
- [ ] All test files moved to correct packages
- [ ] Original src/ directory empty (can be deleted)
- [ ] Original tests/ directory empty (can be deleted)

### Checkpoint 4: Imports Updated
- [ ] No references to old paths (src/, tests/ at root)
- [ ] All imports use workspace protocol or relative paths
- [ ] TypeScript compiler shows zero errors
- [ ] ESLint passes with no import errors

### Checkpoint 5: Tests Pass
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Test coverage remains ≥90%
- [ ] No test files missed in migration

---

## Summary

**Files Affected**: ~500 source files + 8 documentation files  
**Packages Created**: 4 (@kioku/cli, @kioku/api, @kioku/ui, @kioku/shared)  
**Import Path Updates**: ~200+ estimated import statements  
**Build Configuration Changes**: 5 new package.json files + root updates

**Risk Mitigation**:
- Migrate in phases (docs first, then code)
- Run tests after each phase
- Keep git history intact
- Create validation checkpoints
