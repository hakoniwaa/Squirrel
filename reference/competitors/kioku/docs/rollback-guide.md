# Rollback Guide - Monorepo Migration

This guide explains how to rollback from the monorepo structure to the previous single-package structure if needed.

## Quick Rollback

If you encounter critical issues with the monorepo structure, you can quickly rollback using the backup tag:

```bash
# 1. View available backup tags
git tag | grep backup

# 2. Rollback to pre-monorepo state
git reset --hard pre-restructure-backup

# 3. Verify you're on the old structure
ls -la src/  # Should exist
ls -la packages/  # Should NOT exist

# 4. Rebuild with old structure
bun install
bun run build
```

**⚠️ Warning:** This will discard ALL changes made after the backup tag. Make sure to backup any work you want to keep.

## Partial Rollback (Cherry-pick Changes)

If you want to keep some changes but rollback the structure:

```bash
# 1. Create a branch with current work
git checkout -b my-work-backup

# 2. Checkout the pre-restructure state
git checkout pre-restructure-backup

# 3. Create a new branch from the old structure
git checkout -b rollback-with-changes

# 4. Cherry-pick specific commits you want to keep
git cherry-pick <commit-hash>

# 5. Rebuild
bun install
bun run build
```

## Understanding What Changed

### Files Added (Monorepo)
- `packages/shared/` - Shared utilities package
- `packages/api/` - Core business logic package
- `packages/cli/` - CLI commands package
- `packages/ui/` - Dashboard UI package
- `docs/architecture.md` - Architecture documentation
- `docs/*.md` - Moved documentation files

### Files Modified
- `package.json` - Added workspaces configuration
- `tsconfig.json` - Updated to include `packages/*/src`
- `tsconfig.build.json` - Updated for monorepo
- `tsconfig.tests.json` - Updated for monorepo
- `eslint.config.mjs` - Added package boundary rules
- `.gitignore` - Added `packages/*/dist`, `packages-backup/`
- `README.md` - Added monorepo section

### Files Removed
- `src/` - Moved to `packages/api/src/`
- `tests/` - Moved to `packages/api/tests/`
- `types/` - Moved to `packages/shared/src/`
- Old markdown files (moved to `docs/`)

## Backup Files

The migration created a backup in `packages-backup/` containing:
- Original `src/` directory
- Original `tests/` directory
- All code before import path changes

**Location:** `packages-backup/api/`

You can reference these files if you need to see the original structure.

## Restoring Specific Files

If you only need to restore specific files:

```bash
# Show files at the backup tag
git show pre-restructure-backup:src/domain/models/ProjectContext.ts

# Restore a specific file
git checkout pre-restructure-backup -- src/domain/models/ProjectContext.ts

# Or copy from the backup directory
cp packages-backup/api/src/domain/models/ProjectContext.ts src/domain/models/
```

## Migration Commits

The monorepo migration was completed in these commits:

1. **`feat(v2.0): complete Phases 10-13`** - Pre-migration work
2. **Backup tag: `pre-restructure-backup`** - Safe rollback point
3. **`feat(monorepo): complete Phase 4 - monorepo structure migration`** - Main migration
4. **`fix(ui): complete UI package setup`** - UI package fixes
5. **`feat(architecture): complete Phase 5 - package boundary validation`** - Boundary enforcement
6. **Current commit** - Polish and documentation

To see what changed in each commit:

```bash
# View commit history
git log --oneline --graph

# View specific commit changes
git show <commit-hash>

# View all changes since backup
git diff pre-restructure-backup..HEAD
```

## Common Rollback Scenarios

### Scenario 1: Build Failures After Migration

**Problem:** Packages won't build after migration

**Solution:**
```bash
# Clean all build artifacts
rm -rf packages/*/dist node_modules

# Reinstall dependencies
bun install

# Build in order
bun run build:shared
bun run build:api
bun run build:cli
bun run build:ui
```

**If still failing:** Rollback to backup and report the issue.

### Scenario 2: Import Errors in Your Code

**Problem:** Your code has import errors after migration

**Solution:**
```bash
# Check for old import patterns
grep -r "from '@/" packages/

# Fix manually or rollback
```

**Common fixes:**
- `from '@/domain/...'` → `from 'domain/...'` (in API package)
- `from '@/shared/...'` → `from '@kioku/shared'`
- Relative imports may need adjustment

### Scenario 3: Tests Not Running

**Problem:** Tests fail or don't run

**Solution:**
```bash
# Run tests from within package
cd packages/api
bun test

# Check test configuration
cat tsconfig.json  # Should include tests/
```

### Scenario 4: CLI Command Not Found

**Problem:** `kioku` command not working

**Solution:**
```bash
# Check if CLI package built
ls -la packages/cli/dist/

# Rebuild CLI
bun run build:cli

# Check package.json bin field
cat packages/cli/package.json | grep -A 3 bin
```

## Emergency Rollback Checklist

If you need to rollback immediately:

- [ ] Stop all running Kioku processes
- [ ] Commit or stash any uncommitted changes
- [ ] Note the current commit hash: `git rev-parse HEAD`
- [ ] Backup your `.context/` directory (project data)
- [ ] Execute rollback: `git reset --hard pre-restructure-backup`
- [ ] Clean node_modules: `rm -rf node_modules`
- [ ] Reinstall: `bun install`
- [ ] Rebuild: `bun run build`
- [ ] Test: `bun test`
- [ ] Verify CLI works: `./dist/infrastructure/cli/index.js --version`

## Post-Rollback

After rolling back:

1. **Report the issue** - Help us improve by reporting what went wrong
2. **Document what failed** - Include error messages, steps to reproduce
3. **Check .context/ directory** - Ensure your project data is intact
4. **Test the old structure** - Make sure everything works after rollback
5. **Consider reporting logs** - Export diagnostics with `kioku doctor --export rollback-report.json`

## Prevention Tips

To avoid needing rollback:

- ✅ Always commit your work before major changes
- ✅ Test the migration on a branch first
- ✅ Keep the `packages-backup/` directory until fully stable
- ✅ Run quality gate before and after: `bun run quality-gate`
- ✅ Check that all commands work: `kioku init`, `kioku serve`, `kioku status`

## Getting Help

If you're having trouble with the migration or rollback:

1. **Check GitHub Issues:** [github.com/yourusername/kioku/issues](https://github.com/yourusername/kioku/issues)
2. **Review Migration Docs:** [docs/architecture.md](./architecture.md)
3. **Run Diagnostics:** `kioku doctor --verbose --export diagnostics.json`
4. **File an Issue:** Include the diagnostics report and error messages

## Success Indicators

You know the rollback was successful when:

- ✅ `src/` directory exists (not `packages/`)
- ✅ `bun run build` completes successfully
- ✅ `bun test` shows 338+ passing tests
- ✅ `kioku init` works in a test project
- ✅ Quality gate passes: `bun run quality-gate`
- ✅ No import errors in your codebase

## Timeline Expectations

- **Quick rollback:** 2-3 minutes (using `git reset`)
- **Partial rollback:** 10-15 minutes (cherry-picking changes)
- **Full rebuild:** 5-10 minutes (after rollback)
- **Verification:** 5 minutes (running tests and checks)

**Total time:** ~15-30 minutes for a complete rollback and verification

---

**Last Updated:** 2025-10-11 (v0.2.0 monorepo migration)

**Backup Tag:** `pre-restructure-backup`

**Safe to Delete Backup:** Wait until you've used the monorepo structure for at least 2 weeks without issues.
