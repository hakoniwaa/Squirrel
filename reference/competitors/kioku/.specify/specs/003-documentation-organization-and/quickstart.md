# Quickstart: Documentation Organization and Monorepo Restructure

**Feature**: 003-documentation-organization-and  
**Date**: 2025-10-11  
**Status**: Ready for Implementation

## Purpose

This guide provides step-by-step instructions for implementing the documentation organization and monorepo restructure.

---

## Prerequisites

Before starting:
- [ ] All changes committed to git (clean working directory)
- [ ] All tests passing (`bun test`)
- [ ] On feature branch `003-documentation-organization-and`
- [ ] Bun 1.0+ installed
- [ ] Read research.md and data-model.md

---

## Phase 1: Documentation Reorganization (Low Risk)

**Estimated Time**: 30 minutes  
**Risk Level**: Low (no code changes)

### Step 1.1: Create docs/ Directory

```bash
mkdir docs
```

### Step 1.2: Move and Rename Files

```bash
# Move files to docs/ with new names
mv SETUP_GUIDE.md docs/setup-guide.md
mv CHANGELOG.md docs/changelog.md
mv kioku.md docs/project-overview.md
mv research.md docs/research.md
mv MERGE_READINESS.md docs/merge-readiness.md
mv FUTURE_FEATURES.md docs/future-features.md
```

**Verify**:
```bash
ls docs/
# Should show: setup-guide.md, changelog.md, project-overview.md,
#              research.md, merge-readiness.md, future-features.md
```

### Step 1.3: Update README.md Links

Open `README.md` and update any links to moved files:

```markdown
<!-- OLD -->
See [Setup Guide](./SETUP_GUIDE.md)

<!-- NEW -->
See [Setup Guide](./docs/setup-guide.md)
```

### Step 1.4: Update CLAUDE.md Links

Open `CLAUDE.md` and update any links to moved files:

```markdown
<!-- OLD -->
See [Project Overview](./kioku.md)

<!-- NEW -->
See [Project Overview](./docs/project-overview.md)
```

### Step 1.5: Commit Documentation Changes

```bash
git add docs/ README.md CLAUDE.md
git status  # Verify 6 files moved, 2 files modified
git commit -m "docs: reorganize documentation into docs/ folder

- Move 6 markdown files to docs/ with kebab-case names
- Update README.md and CLAUDE.md with correct links
- Flat structure for easy navigation

Related to 003-documentation-organization-and"
```

**Checkpoint**: Documentation phase complete ✓

---

## Phase 2: Monorepo Structure Setup (Medium Risk)

**Estimated Time**: 1 hour  
**Risk Level**: Medium (structural changes)

### Step 2.1: Create Package Directories

```bash
# Create packages structure
mkdir -p packages/cli/src packages/cli/tests
mkdir -p packages/api/src packages/api/tests
mkdir -p packages/ui/src packages/ui/tests
mkdir -p packages/shared/src packages/shared/tests
```

**Verify**:
```bash
tree packages/ -L 2
```

### Step 2.2: Create Package Configuration Files

Create `packages/shared/package.json`:
```json
{
  "name": "@kioku/shared",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "bun test"
  }
}
```

Create `packages/cli/package.json`:
```json
{
  "name": "@kioku/cli",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "bin": {
    "kioku": "dist/index.js"
  },
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "bun test"
  },
  "dependencies": {
    "@kioku/shared": "workspace:*",
    "@kioku/api": "workspace:*"
  }
}
```

Create `packages/api/package.json`:
```json
{
  "name": "@kioku/api",
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

Create `packages/ui/package.json`:
```json
{
  "name": "@kioku/ui",
  "version": "0.1.0",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "bun test",
    "dev": "vite"
  },
  "dependencies": {
    "@kioku/shared": "workspace:*",
    "@kioku/api": "workspace:*"
  }
}
```

### Step 2.3: Configure Root Workspace

Update root `package.json`, add workspaces field:
```json
{
  "name": "kioku-monorepo",
  "workspaces": [
    "packages/*"
  ],
  "scripts": {
    "build": "bun run build:shared && bun run build:api && bun run build:cli && bun run build:ui",
    "build:shared": "bun --filter=@kioku/shared run build",
    "build:api": "bun --filter=@kioku/api run build",
    "build:cli": "bun --filter=@kioku/cli run build",
    "build:ui": "bun --filter=@kioku/ui run build",
    "test": "bun test",
    "test:cli": "bun --filter=@kioku/cli test",
    "test:api": "bun --filter=@kioku/api test"
  }
}
```

### Step 2.4: Create TypeScript Configurations

Create `packages/shared/tsconfig.json`:
```json
{
  "extends": "../../tsconfig.json",
  "compilerOptions": {
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src/**/*"]
}
```

Repeat for `cli`, `api`, `ui` (same pattern).

### Step 2.5: Create Package READMEs

Create `packages/cli/README.md`:
```markdown
# @kioku/cli

Command-line interface for Kioku.

## Usage

\`\`\`bash
kioku init
kioku serve
kioku status
\`\`\`
```

Create similar READMEs for api, ui, shared.

### Step 2.6: Install Workspace Dependencies

```bash
bun install
```

**Verify**:
```bash
bun pm ls --all
# Should show @kioku/* packages linked
```

**⚠️ Troubleshooting: If workspace resolution fails**

If `bun pm ls --all` shows errors or packages aren't linked:

1. **Verify workspace configuration**: Check `package.json` has `"workspaces": ["packages/*"]`
2. **Check package names**: Ensure all package.json files have correct `@kioku/*` names
3. **Clear and reinstall**: `rm -rf node_modules/ bun.lockb && bun install`
4. **Manual symlink fallback** (last resort):
   ```bash
   # Create symlinks manually if Bun workspace resolution fails
   cd packages/cli/node_modules
   mkdir -p @kioku
   ln -s ../../shared @kioku/shared
   ln -s ../../api @kioku/api
   
   cd ../../api/node_modules
   mkdir -p @kioku
   ln -s ../../shared @kioku/shared
   
   cd ../../ui/node_modules
   mkdir -p @kioku
   ln -s ../../shared @kioku/shared
   ln -s ../../api @kioku/api
   ```

**Note**: Manual symlinks are a temporary workaround. Investigate and fix the root cause of workspace resolution failure before proceeding to production.

### Step 2.7: Commit Structure Changes

```bash
git add packages/ package.json
git commit -m "feat: setup monorepo structure with 4 packages

- Create packages/cli, packages/api, packages/ui, packages/shared
- Configure Bun workspaces
- Add package.json for each package with workspace dependencies
- Setup TypeScript configurations
- Add package READMEs

Related to 003-documentation-organization-and"
```

**Checkpoint**: Structure phase complete ✓

---

## Phase 3: Code Migration (High Risk)

**Estimated Time**: 2-3 hours  
**Risk Level**: High (code movement + import updates)

### Step 3.1: Move Shared Code First

```bash
# Move types to shared package
cp -r types/ packages/shared/src/types/

# Create shared index
cat > packages/shared/src/index.ts << 'EOF'
export * from './types';
EOF
```

**Verify**:
```bash
cd packages/shared
bun run build
cd ../..
```

### Step 3.2: Move API Code

```bash
# Move domain logic
cp -r src/domain packages/api/src/

# Move application logic
cp -r src/application packages/api/src/

# Move API infrastructure
mkdir -p packages/api/src/infrastructure
cp -r src/infrastructure/mcp packages/api/src/infrastructure/
cp -r src/infrastructure/storage packages/api/src/infrastructure/
cp -r src/infrastructure/background packages/api/src/infrastructure/

# Move API tests
cp -r tests/unit/domain packages/api/tests/
cp -r tests/unit/application packages/api/tests/
cp -r tests/integration packages/api/tests/

# Create API index
cat > packages/api/src/index.ts << 'EOF'
// Export public API
export * from './domain';
export * from './application';
EOF
```

### Step 3.3: Move CLI Code

```bash
# Move CLI source
cp -r src/infrastructure/cli packages/cli/src/

# Move CLI tests
cp -r tests/unit/infrastructure/cli packages/cli/tests/

# Create CLI index
cat > packages/cli/src/index.ts << 'EOF'
#!/usr/bin/env node
import { runCLI } from './cli';
runCLI();
EOF
```

### Step 3.4: Move UI Code

```bash
# Move dashboard
cp -r dashboard/* packages/ui/src/

# If dashboard has tests
if [ -d "dashboard/tests" ]; then
  cp -r dashboard/tests packages/ui/tests/
fi
```

### Step 3.5: Update Import Paths (Critical Step)

This is the most error-prone step. Proceed carefully:

```bash
# Find all TypeScript files that need import updates
find packages/ -name "*.ts" -o -name "*.tsx" > /tmp/ts-files.txt

# Create import path update script
cat > /tmp/update-imports.sh << 'EOF'
#!/bin/bash
for file in $(cat /tmp/ts-files.txt); do
  # Update @/ imports to workspace imports
  sed -i.bak "s|from '@/domain/|from '@kioku/api/domain/|g" "$file"
  sed -i.bak "s|from '@/application/|from '@kioku/api/application/|g" "$file"
  sed -i.bak "s|from '@/infrastructure/cli/|from '@kioku/cli/|g" "$file"
  sed -i.bak "s|from '@/shared/|from '@kioku/shared/|g" "$file"
  sed -i.bak "s|from 'types/|from '@kioku/shared/types/|g" "$file"
  
  # Clean up backup files
  rm -f "$file.bak"
done
EOF

chmod +x /tmp/update-imports.sh
/tmp/update-imports.sh
```

**Manual Review Required**: Some imports may need hand-tuning. Check for:
- Circular dependencies
- Incorrectly updated relative imports
- Missing exports from package indexes

### Step 3.6: Verify TypeScript Compilation

```bash
bun run type-check
```

Fix any errors before proceeding.

### Step 3.7: Run Tests

```bash
# Test each package
bun run test:shared
bun run test:api
bun run test:cli

# Run all tests
bun test
```

### Step 3.8: Verify Coverage

```bash
bun test:coverage
# Must be ≥90%
```

### Step 3.9: Delete Old Directories

**Only after all tests pass**:

```bash
rm -rf src/
rm -rf tests/
rm -rf types/
rm -rf dashboard/
```

### Step 3.10: Commit Code Migration

```bash
git add packages/ 
git rm -r src/ tests/ types/ dashboard/
git commit -m "feat: migrate code to monorepo packages

- Move domain/application/infrastructure to packages/api
- Move CLI code to packages/cli
- Move dashboard to packages/ui
- Move types to packages/shared
- Update all import paths to workspace protocol
- All tests passing with ≥90% coverage

BREAKING: Source code structure completely reorganized

Related to 003-documentation-organization-and"
```

**Checkpoint**: Code migration complete ✓

---

## Phase 4: Final Validation

**Estimated Time**: 30 minutes  
**Risk Level**: Low (verification only)

### Step 4.1: Build All Packages

```bash
bun run build
```

**Verify**: All packages build successfully

### Step 4.2: Run Quality Gates

```bash
bun run quality-gate
```

**Must Pass**:
- ✓ Type checking
- ✓ Linting
- ✓ Tests (≥90% coverage)

### Step 4.3: Manual Functionality Test

```bash
# Test CLI (use helper script or global binary)
bun run kioku --help
# Or if linked globally:
kioku --help

# Test API (if applicable)
bun packages/api/dist/index.js

# Test UI dev server (if applicable)
cd packages/ui
bun run dev
```

### Step 4.4: Verify Success Criteria

Check against spec success criteria (SC-001 to SC-010):

- [ ] **SC-001**: Can locate docs in <30 seconds
- [ ] **SC-002**: All markdown files moved successfully
- [ ] **SC-003**: Each package builds independently
- [ ] **SC-005**: All tests pass, no regressions
- [ ] **SC-007**: No circular dependencies (check with `bun pm ls`)
- [ ] **SC-008**: Package builds <5 seconds
- [ ] **SC-009**: Workspace dependencies resolve automatically
- [ ] **SC-010**: 100% of imports updated correctly

### Step 4.5: Final Commit

```bash
git status  # Verify clean state
git log --oneline -5  # Review commits

# Tag the completion
git tag -a v0.2.0-monorepo -m "Complete monorepo restructure"
```

---

## Rollback Plan

If issues arise:

```bash
# Reset to before migration
git reset --hard <commit-before-phase-3>

# Or revert specific commits
git revert <commit-hash>
```

---

## Post-Migration Tasks

After successful migration:

1. Update CI/CD pipelines (if any) for monorepo structure
2. Update documentation references to new structure
3. Notify team members of new structure
4. Update development guides with new build commands

---

## Common Issues & Solutions

### Issue: Import errors after migration

**Solution**: 
1. Check package.json exports
2. Verify workspace dependencies installed
3. Run `bun install` again

### Issue: Tests fail in specific package

**Solution**:
1. Check test file paths are correct
2. Verify test imports use correct workspace protocol
3. Check package-specific tsconfig.json

### Issue: Circular dependency detected

**Solution**:
1. Review dependency graph in data-model.md
2. Move shared code to @kioku/shared
3. Ensure packages only depend on shared, not each other

### Issue: Build fails for one package

**Solution**:
1. Build shared first: `bun run build:shared`
2. Then build dependent packages in order
3. Check tsconfig.json outDir and rootDir settings

---

## Success Indicators

✅ All phases complete  
✅ All tests passing  
✅ All builds successful  
✅ No broken imports  
✅ Git history preserved  
✅ Documentation updated  
✅ Quality gates passing  

**Status**: Ready for production ✓

---

## Timeline

- **Phase 1 (Docs)**: 30 minutes
- **Phase 2 (Structure)**: 1 hour
- **Phase 3 (Code)**: 2-3 hours
- **Phase 4 (Validation)**: 30 minutes

**Total Estimated Time**: 4-5 hours

**Recommendation**: Execute in a single session to maintain context and momentum.
