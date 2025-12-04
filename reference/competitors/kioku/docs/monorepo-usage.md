# Using the Kioku Monorepo

This guide explains how to work with the Kioku monorepo on a daily basis.

## Table of Contents

- [Quick Start](#quick-start)
- [Development Workflow](#development-workflow)
- [Working with Packages](#working-with-packages)
- [Building](#building)
- [Testing](#testing)
- [Adding New Features](#adding-new-features)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### First Time Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/kioku.git
cd kioku

# Install all dependencies (for all packages)
bun install

# Build all packages
bun run build

# Verify everything works
bun run quality-gate
```

### Using Kioku After Setup

```bash
# Start using Kioku (CLI is in packages/cli)
bun run packages/cli/dist/index.js setup

# Or if you have it linked globally
kioku setup
```

---

## Development Workflow

### Daily Development

```bash
# 1. Pull latest changes
git pull

# 2. Install/update dependencies
bun install

# 3. Build packages you're working on
bun run build:api    # If working on API
bun run build:cli    # If working on CLI
bun run build:ui     # If working on UI

# 4. Run tests
cd packages/api && bun test --watch
```

### Before Committing

```bash
# Run quality checks
bun run quality-gate

# This runs:
# - Type check (all packages)
# - Lint (with boundary checks)
# - Tests (API package)
```

---

## Working with Packages

### Understanding the Packages

```
packages/
├── shared/      # Shared utilities (errors, types)
│   └── src/
│       ├── errors/
│       └── index.ts
│
├── api/         # Core business logic
│   └── src/
│       ├── domain/          # Pure business logic
│       ├── application/     # Use cases
│       └── infrastructure/  # External integrations
│
├── cli/         # Command-line interface
│   └── src/
│       ├── commands/
│       └── index.ts
│
└── ui/          # Web dashboard
    └── src/
        ├── components/
        └── services/
```

### Which Package to Modify?

**Working on error classes or types?**
→ Edit `packages/shared/src/`

**Working on business logic (domain models, calculations)?**
→ Edit `packages/api/src/domain/`

**Working on MCP tools or storage?**
→ Edit `packages/api/src/infrastructure/`

**Working on CLI commands?**
→ Edit `packages/cli/src/commands/`

**Working on dashboard UI?**
→ Edit `packages/ui/src/components/`

---

## Building

### Build All Packages

```bash
# Build in dependency order (shared → api → cli → ui)
bun run build
```

### Build Individual Packages

```bash
# Build only what you need
bun run build:shared
bun run build:api
bun run build:cli
bun run build:ui
```

### Build from Within a Package

```bash
# Navigate to package and build
cd packages/api
bun run build

# Or with filter
bun --filter=@kioku/api run build
```

### Watch Mode (Auto-rebuild)

```bash
# API package with auto-rebuild
cd packages/api
bun run build --watch

# UI package with Vite dev server
cd packages/ui
bun run dev
```

---

## Testing

### Run All Tests

```bash
# Run tests in API package (main test suite)
bun run test:api

# Or from within package
cd packages/api
bun test
```

### Run Tests in Watch Mode

```bash
cd packages/api
bun test --watch
```

### Run Specific Test File

```bash
cd packages/api
bun test src/domain/calculations/context-scoring.test.ts
```

### Run Tests with Coverage

```bash
cd packages/api
bun test --coverage
```

---

## Adding New Features

### Adding to Existing Package

**Example: Add a new CLI command**

```bash
# 1. Create the command file
touch packages/cli/src/commands/my-command.ts

# 2. Implement the command
cat > packages/cli/src/commands/my-command.ts << 'EOF'
export async function myCommand(): Promise<void> {
  console.log('My new command!');
}
EOF

# 3. Register in CLI index
# Edit packages/cli/src/index.ts to add command

# 4. Build CLI
bun run build:cli

# 5. Test it
bun run packages/cli/dist/index.js my-command
```

**Example: Add a new domain model**

```bash
# 1. Create model file
touch packages/api/src/domain/models/MyModel.ts

# 2. Define the model
cat > packages/api/src/domain/models/MyModel.ts << 'EOF'
export interface MyModel {
  id: string;
  name: string;
  createdAt: Date;
}
EOF

# 3. Export from index
# Edit packages/api/src/domain/models/index.ts
# Add: export * from './MyModel';

# 4. Build API
bun run build:api

# 5. Use in other packages
# packages/cli/src/commands/example.ts
# import { MyModel } from '@kioku/api';
```

### Adding to Shared Package

**Example: Add a new error class**

```bash
# 1. Create error file
touch packages/shared/src/errors/MyError.ts

# 2. Implement the error
cat > packages/shared/src/errors/MyError.ts << 'EOF'
export class MyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'MyError';
  }
}
EOF

# 3. Export from errors/index.ts
echo "export * from './MyError';" >> packages/shared/src/errors/index.ts

# 4. Build shared
bun run build:shared

# 5. Rebuild packages that depend on shared
bun run build:api
bun run build:cli
```

---

## Common Tasks

### Installing a New Dependency

**For a specific package:**

```bash
# Add to API package
cd packages/api
bun add some-package

# Add dev dependency
bun add -D some-dev-package
```

**For the root (workspace-level):**

```bash
# Add to root (tools like eslint, typescript)
bun add -D some-tool
```

### Adding a Workspace Dependency

**Example: CLI needs to use something from API**

Already configured in `packages/cli/package.json`:
```json
{
  "dependencies": {
    "@kioku/api": "workspace:*"
  }
}
```

After adding, run:
```bash
bun install
```

### Updating Dependencies

```bash
# Update all dependencies
bun update

# Update specific package
bun update some-package
```

### Type Checking

```bash
# Check all packages
bun run type-check

# Check specific package
bun run type-check:api
bun run type-check:cli
bun run type-check:shared

# Or from within package
cd packages/api
tsc --noEmit
```

### Linting

```bash
# Lint all packages
bun run lint

# Auto-fix issues
bun run lint:fix
```

### Running the CLI During Development

**Option 1: Use the built CLI**
```bash
bun run packages/cli/dist/index.js [command]
```

**Option 2: Run from source with Bun**
```bash
bun run packages/cli/src/index.ts [command]
```

**Option 3: Link globally**
```bash
cd packages/cli
bun link

# Then from anywhere
kioku [command]
```

### Starting the Dashboard

```bash
# Development mode (with hot reload)
cd packages/ui
bun run dev

# Open http://localhost:3456
```

### Starting the MCP Server

**Note:** You typically don't need to manually start the MCP server!

The MCP server starts automatically when you use:
- **Claude Desktop** (configured in MCP settings)
- **Zed** (configured in settings.json)

**Only manual start if:**
- Testing the server in isolation
- Debugging MCP protocol issues

```bash
# Manual start (rarely needed)
bun run packages/cli/dist/index.js serve

# The server runs via stdio (not HTTP)
# Your editor communicates with it automatically
```

---

## Import Patterns

### Importing Within Same Package

**API package (use path aliases):**
```typescript
// packages/api/src/application/use-cases/MyUseCase.ts
import { Model } from 'domain/models/Model';
import { Calculator } from 'domain/calculations/calculator';
import { Storage } from 'infrastructure/storage/sqlite-adapter';
```

**CLI package (use relative imports):**
```typescript
// packages/cli/src/commands/my-command.ts
import { logger } from '../logger';
```

### Importing Across Packages

**From shared:**
```typescript
import { MyError } from '@kioku/shared';
```

**From API:**
```typescript
import { MyModel, MyService } from '@kioku/api';
```

**What NOT to do:**
```typescript
// ❌ Don't import internal paths from other packages
import { Model } from '@kioku/api/domain/models/Model';

// ✅ Do use the package's public API
import { Model } from '@kioku/api';
```

---

## Package Boundaries (Important!)

### Rules You Must Follow

**❌ FORBIDDEN:**
- API cannot import from CLI or UI
- CLI cannot import from UI
- UI cannot import from CLI
- Shared cannot import from any workspace package

**✅ ALLOWED:**
- API can import from Shared
- CLI can import from API and Shared
- UI can import from API and Shared

**ESLint will catch violations:**
```typescript
// packages/api/src/domain/something.ts
import { command } from '@kioku/cli';  // ❌ ERROR!

// packages/cli/src/commands/something.ts
import { Component } from '@kioku/ui';  // ❌ ERROR!
```

### Why These Rules?

- **API** = Core business logic (should be independent)
- **CLI** = User interface (depends on API)
- **UI** = Web interface (depends on API)
- **Shared** = Foundation (no dependencies)

This prevents circular dependencies and keeps architecture clean.

---

## Debugging

### Debugging CLI Commands

```bash
# Use Bun's built-in debugger
bun --inspect run packages/cli/src/index.ts [command]

# Or add breakpoints in VS Code
# Create .vscode/launch.json:
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "bun",
      "request": "launch",
      "name": "Debug CLI",
      "program": "${workspaceFolder}/packages/cli/src/index.ts",
      "args": ["init"],
      "cwd": "${workspaceFolder}",
      "runtimeExecutable": "bun"
    }
  ]
}
```

### Debugging Tests

```bash
# Run single test with output
cd packages/api
bun test --bail src/domain/calculations/context-scoring.test.ts

# Debug with VS Code
# Configuration in .vscode/launch.json:
{
  "type": "bun",
  "request": "launch",
  "name": "Debug Test",
  "program": "${workspaceFolder}/packages/api/tests/domain/calculations/context-scoring.test.ts",
  "cwd": "${workspaceFolder}/packages/api"
}
```

### Debugging the Dashboard

```bash
# Vite has built-in source maps
cd packages/ui
bun run dev

# Then use browser DevTools
# Sources tab will show TypeScript source
```

---

## Performance Tips

### Faster Builds

**Build only what changed:**
```bash
# Changed API? Only rebuild API and CLI (depends on API)
bun run build:api
bun run build:cli
```

**Use watch mode during development:**
```bash
# Terminal 1: API watch mode
cd packages/api && bun run build --watch

# Terminal 2: CLI watch mode  
cd packages/cli && bun run build --watch
```

### Faster Tests

**Run specific tests:**
```bash
cd packages/api
bun test src/domain/  # Only domain tests
```

**Skip expensive tests:**
```bash
# Use .only() for focused testing
it.only('should test specific thing', () => {
  // ...
});
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: oven-sh/setup-bun@v1
        with:
          bun-version: latest
      
      - name: Install dependencies
        run: bun install
      
      - name: Type check
        run: bun run type-check
      
      - name: Lint
        run: bun run lint
      
      - name: Test
        run: bun run test:api
      
      - name: Build all packages
        run: bun run build
```

---

## Troubleshooting

### "Cannot find module '@kioku/xxx'"

**Problem:** Workspace packages not linked

**Solution:**
```bash
bun install
```

### "Module has no exported member 'X'"

**Problem:** Package needs to be rebuilt

**Solution:**
```bash
# Rebuild the package you're importing from
bun run build:shared  # If importing from @kioku/shared
bun run build:api     # If importing from @kioku/api
```

### Build fails with "Cannot find module"

**Problem:** Packages built out of order

**Solution:**
```bash
# Build in dependency order
bun run build:shared
bun run build:api
bun run build:cli
bun run build:ui

# Or use the main build command
bun run build
```

### Type errors about path aliases

**Problem:** Working in wrong package directory

**Solution:**
```bash
# Make sure you're in the package directory
cd packages/api  # Then run commands

# Or check your IDE's TypeScript settings
# VS Code: Select TypeScript version from status bar
```

### ESLint boundary violation errors

**Problem:** Importing from wrong package

**Solution:**
```bash
# Check the error message for which boundary you violated
# Fix by importing from allowed packages only
# See "Package Boundaries" section above
```

---

## Quick Reference

### Common Commands

```bash
# Development
bun install                    # Install all dependencies
bun run build                  # Build all packages
bun run build:api              # Build API package
bun run type-check             # Type check all packages
bun run lint                   # Lint all packages
bun run quality-gate           # Run all checks

# Testing
cd packages/api && bun test    # Run tests
cd packages/api && bun test --watch  # Watch mode

# Running
bun run packages/cli/dist/index.js [cmd]  # Run CLI
cd packages/ui && bun run dev             # Start dashboard
```

### Package Locations

```bash
packages/shared/dist/          # Shared build output
packages/api/dist/             # API build output
packages/cli/dist/             # CLI build output
packages/ui/dist/              # UI build output (Vite)
```

### Documentation

- **Architecture:** `docs/architecture.md`
- **Rollback:** `docs/rollback-guide.md`
- **This Guide:** `docs/monorepo-usage.md`

---

## Getting Help

**Found a bug?** File an issue with:
- Which package you were working in
- Commands you ran
- Error messages
- Output of `bun --version`

**Need help?** Check:
1. This guide
2. `docs/architecture.md`
3. Package README files
4. GitHub issues

---

**Last Updated:** 2025-10-11 (v0.2.0 monorepo)

**Happy coding! 🚀**
