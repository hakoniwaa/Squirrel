# Research: Documentation Organization and Monorepo Restructure

**Feature**: 003-documentation-organization-and  
**Date**: 2025-10-11  
**Status**: Complete

## Purpose

This document records research decisions for implementing documentation reorganization and monorepo restructure for the Kioku project.

---

## Research Areas

### 1. Bun Workspaces Configuration

**Question**: How to configure Bun workspaces for monorepo management?

**Decision**: Use Bun's native workspace support via `package.json` workspaces field

**Rationale**:
- Bun has first-class workspace support (no additional tools needed)
- Compatible with npm/pnpm workspace conventions
- Fast dependency resolution and linking
- Already using Bun as runtime

**Implementation**:
```json
{
  "name": "kioku",
  "workspaces": ["packages/*"]
}
```

**Alternatives Considered**:
- **Nx**: Rejected - out of scope per constitution (adds complexity)
- **Turborepo**: Rejected - out of scope per constitution (adds build orchestration)
- **Lerna**: Rejected - out of scope per constitution (legacy tool, adds overhead)

**References**:
- Bun workspaces documentation: https://bun.sh/docs/install/workspaces

---

### 2. Package Dependency Management

**Question**: How should packages declare dependencies on each other?

**Decision**: Use workspace protocol (`workspace:*`) for inter-package dependencies

**Rationale**:
- Ensures packages always use local versions during development
- Bun automatically resolves workspace dependencies
- Clear distinction between workspace and external dependencies
- Prevents version mismatch issues

**Implementation Example**:
```json
// packages/cli/package.json
{
  "dependencies": {
    "@kioku/shared": "workspace:*",
    "@kioku/api": "workspace:*"
  }
}
```

**Alternatives Considered**:
- **File protocol**: Rejected - less explicit, harder to understand
- **Version numbers**: Rejected - requires manual synchronization

---

### 3. Import Path Update Strategy

**Question**: How to systematically update all import paths after code moves?

**Decision**: Multi-step approach with automated search-and-replace

**Rationale**:
- Cannot rely solely on TypeScript compiler (may miss dynamic imports)
- Need comprehensive solution covering all import styles
- Must be repeatable and verifiable

**Implementation Steps**:
1. Create import path mapping (old → new)
2. Use `find` + `sed` for bulk replacements
3. Run TypeScript compiler to catch missed imports
4. Run tests to verify functionality
5. Manual review of any ambiguous cases

**Alternatives Considered**:
- **ts-morph**: Rejected - adds dependency, overkill for this task
- **Manual updates**: Rejected - error-prone, time-consuming
- **jscodeshift**: Rejected - complexity not justified

---

### 4. Documentation File Naming Convention

**Question**: What naming convention for files moved to docs/?

**Decision**: keb

ab-case with descriptive names

**Rationale**:
- Clarified in spec (FR-003)
- Consistent with modern web conventions
- URL-friendly (if docs ever served via web)
- Easy to read and autocomplete

**Examples**:
- `SETUP_GUIDE.md` → `docs/setup-guide.md`
- `MERGE_READINESS.md` → `docs/merge-readiness.md`
- `FUTURE_FEATURES.md` → `docs/future-features.md`
- `kioku.md` → `docs/project-overview.md`

**Alternatives Considered**:
- **UPPER_CASE**: Rejected - not as readable
- **camelCase**: Rejected - less common for markdown files
- **PascalCase**: Rejected - typically for code files

---

### 5. Test Organization Strategy

**Question**: How to organize tests in monorepo packages?

**Decision**: Co-locate tests with source code in each package

**Rationale**:
- Tests belong to the package they're testing
- Enables independent package testing
- Maintains existing test structure (mirrors src/)
- Vitest already configured for this pattern

**Structure**:
```
packages/cli/
├── src/
│   └── commands/
│       └── init.ts
└── tests/
    └── commands/
        └── init.test.ts
```

**Alternatives Considered**:
- **Centralized tests/**: Rejected - breaks package independence
- **Inline __tests__/**: Rejected - clutters source directories

---

### 6. Build Script Organization

**Question**: How to manage build scripts across packages?

**Decision**: Package-level scripts + root-level orchestration scripts

**Rationale**:
- Each package has own build/test/lint scripts
- Root package.json has aggregate scripts (build:all, test:all)
- Bun runs workspace scripts efficiently
- Enables both individual and collective builds

**Implementation**:
```json
// Root package.json
{
  "scripts": {
    "build": "bun run build:shared && bun run build:api && bun run build:cli && bun run build:ui",
    "build:shared": "bun --filter=@kioku/shared run build",
    "build:api": "bun --filter=@kioku/api run build",
    "build:cli": "bun --filter=@kioku/cli run build",
    "build:ui": "bun --filter=@kioku/ui run build",
    "test": "bun test",
    "test:cli": "bun --filter=@kioku/cli test"
  }
}
```

**Build Order**: Sequential builds with dependency order (shared → api → cli/ui) for MVP. Parallel builds are post-MVP optimization.

**Rationale for Sequential**:
- Safer - ensures dependencies built before dependents
- Easier to debug build failures (clear order)
- Performance acceptable for MVP (<20 seconds total)
- Parallel builds add complexity (require topological sorting)

**Alternatives Considered**:
- **Parallel builds**: Deferred to post-MVP - requires tooling like Nx or custom orchestration
- **Task runner (Nx/Turborepo)**: Rejected - out of scope
- **Make/Shell scripts**: Rejected - less cross-platform

---

### 7. TypeScript Configuration Strategy

**Question**: How to organize TypeScript configurations in monorepo?

**Decision**: Root tsconfig.json with package-specific extends

**Rationale**:
- Shared compiler options at root (strict mode, target, etc.)
- Package-specific overrides where needed (paths, includes)
- Maintains consistency across packages
- Standard TypeScript monorepo pattern

**Structure**:
```
tsconfig.json              # Root config (shared options)
packages/cli/tsconfig.json # Extends root, adds cli-specific paths
packages/api/tsconfig.json # Extends root, adds api-specific paths
```

**Alternatives Considered**:
- **Separate configs**: Rejected - duplicates configuration
- **Single config**: Rejected - doesn't handle package-specific needs

---

### 8. Package Naming Convention

**Question**: What naming convention for package names in package.json?

**Decision**: Scoped packages under `@kioku/` namespace

**Rationale**:
- Clear ownership (all packages under @kioku)
- Prevents npm naming conflicts (if published later)
- Professional convention for monorepos
- Easy to identify kioku-specific dependencies

**Examples**:
- `@kioku/cli`
- `@kioku/api`
- `@kioku/ui`
- `@kioku/shared`

**Alternatives Considered**:
- **Unscoped**: Rejected - harder to distinguish from external packages
- **Different scope per package**: Rejected - adds confusion

---

## Summary of Decisions

| Area | Decision | Key Benefit |
|------|----------|-------------|
| Workspace Management | Bun native workspaces | Zero additional tooling |
| Package Dependencies | `workspace:*` protocol | Automatic local linking |
| Import Updates | Automated find-replace | Systematic and verifiable |
| Doc Naming | kebab-case | Consistent, readable |
| Test Organization | Co-located with packages | Independent testing |
| Build Scripts | Package + root scripts | Flexible execution |
| TypeScript Config | Root + extends | Shared + customizable |
| Package Naming | `@kioku/` scoped | Clear ownership |

---

## Open Questions

None - all technical decisions resolved.

---

## Next Steps

Proceed to Phase 1:
1. Generate data-model.md (file mappings, package structure)
2. Generate quickstart.md (migration steps)
3. Update agent context files
