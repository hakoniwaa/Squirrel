# Tasks: Documentation Organization and Monorepo Restructure

**Feature**: 003-documentation-organization-and  
**Branch**: `003-documentation-organization-and`  
**Prerequisites**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**Input**: Design documents from `.specify/specs/003-documentation-organization-and/`

---

## Task Organization

Tasks are grouped by user story to enable independent implementation and testing of each story:
- **Setup (Phase 1)**: Project initialization
- **Foundational (Phase 2)**: Blocking prerequisites for all user stories
- **User Story 1 (Phase 3 - P1)**: Documentation organization 🎯 MVP
- **User Story 2 (Phase 4 - P2)**: Monorepo structure
- **User Story 3 (Phase 5 - P3)**: Package boundaries validation
- **Polish (Final Phase)**: Cross-cutting concerns

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and verification

- [x] T001 Verify clean git status and all tests passing
- [x] T002 [P] Create feature branch backup tag `pre-restructure-backup`
- [x] T003 Document current directory structure for rollback reference

**Checkpoint**: Setup complete - ready for user story implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Verify Bun 1.0+ installed and functional
- [x] T005 Verify TypeScript 5.x compiler available
- [x] T006 Verify Vitest test runner functional
- [x] T007 Run baseline test coverage report (must be ≥90%)
- [x] T008 Create `.gitignore` entries for future package dist/ directories

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Centralized Documentation Discovery (Priority: P1) 🎯 MVP

**Goal**: Move markdown files to centralized `docs/` folder for easy discovery

**Independent Test**: Navigate to `docs/` folder and verify all 6 files present with kebab-case names, README.md and CLAUDE.md have correct links, developer can find any doc in <30 seconds

### Implementation for User Story 1

- [x] T009 [P] [US1] Create `docs/` directory at repository root
- [x] T010 [P] [US1] Move `SETUP_GUIDE.md` to `docs/setup-guide.md`
- [x] T011 [P] [US1] Move `CHANGELOG.md` to `docs/changelog.md`
- [x] T012 [P] [US1] Move `kioku.md` to `docs/project-overview.md`
- [x] T013 [P] [US1] Move `research.md` to `docs/research.md`
- [x] T014 [P] [US1] Move `MERGE_READINESS.md` to `docs/merge-readiness.md`
- [x] T015 [P] [US1] Move `FUTURE_FEATURES.md` to `docs/future-features.md`
- [x] T016 [US1] Update `README.md` links to point to `docs/` locations (e.g., `./SETUP_GUIDE.md` → `./docs/setup-guide.md`)
- [x] T017 [US1] Update `CLAUDE.md` links to point to `docs/` locations
- [x] T018 [US1] Verify no broken links in README.md by manual review
- [x] T019 [US1] Verify no broken links in CLAUDE.md by manual review
- [x] T020 [US1] Verify docs/ contains exactly 6 files with correct names
- [x] T021 [US1] Commit documentation reorganization: `git commit -m "docs: reorganize documentation into docs/ folder"`

**Checkpoint**: User Story 1 complete and independently testable ✓ (MVP delivered!)

---

## Phase 4: User Story 2 - Independent Package Development (Priority: P2)

**Goal**: Create monorepo structure with independent packages (cli, api, ui, shared)

**Independent Test**: Run `bun test` in each package directory independently, verify builds are isolated, workspace dependencies resolve automatically

### Implementation for User Story 2 - Part A: Structure Creation

- [ ] T022 [P] [US2] Create `packages/` directory at repository root
- [ ] T023 [P] [US2] Create `packages/shared/src/` directory structure
- [ ] T024 [P] [US2] Create `packages/shared/tests/` directory
- [ ] T025 [P] [US2] Create `packages/cli/src/` directory structure
- [ ] T026 [P] [US2] Create `packages/cli/tests/` directory
- [ ] T027 [P] [US2] Create `packages/api/src/` directory structure
- [ ] T028 [P] [US2] Create `packages/api/tests/` directory
- [ ] T029 [P] [US2] Create `packages/ui/src/` directory structure
- [ ] T030 [P] [US2] Create `packages/ui/tests/` directory

### Implementation for User Story 2 - Part B: Package Configuration

- [ ] T031 [P] [US2] Create `packages/shared/package.json` with name `@kioku/shared`, scripts, and zero dependencies
- [ ] T032 [P] [US2] Create `packages/cli/package.json` with dependencies on `@kioku/shared:workspace:*` and `@kioku/api:workspace:*`
- [ ] T033 [P] [US2] Create `packages/api/package.json` with dependency on `@kioku/shared:workspace:*`
- [ ] T034 [P] [US2] Create `packages/ui/package.json` with dependencies on `@kioku/shared:workspace:*` and `@kioku/api:workspace:*`
- [ ] T035 [US2] Update root `package.json`: add `workspaces: ["packages/*"]` field
- [ ] T036 [US2] Update root `package.json`: add build scripts (`build:shared`, `build:api`, `build:cli`, `build:ui`, `build`)
- [ ] T037 [US2] Update root `package.json`: add test scripts (`test:shared`, `test:api`, `test:cli`, `test:ui`)

### Implementation for User Story 2 - Part C: TypeScript Configuration

- [ ] T038 [P] [US2] Create `packages/shared/tsconfig.json` extending root config
- [ ] T039 [P] [US2] Create `packages/cli/tsconfig.json` extending root config with CLI-specific paths
- [ ] T040 [P] [US2] Create `packages/api/tsconfig.json` extending root config with API-specific paths
- [ ] T041 [P] [US2] Create `packages/ui/tsconfig.json` extending root config with UI-specific paths

### Implementation for User Story 2 - Part D: Package READMEs

**Quality Criteria**: Each README must include: (1) Package purpose, (2) Installation/setup instructions, (3) Usage example, (4) Link to main docs or API reference

- [ ] T042 [P] [US2] Create `packages/shared/README.md` - Document: purpose (shared types/utils), what's exported, how other packages use it, example import
- [ ] T043 [P] [US2] Create `packages/cli/README.md` - Document: purpose (CLI tool), available commands (init/serve/status), installation, usage examples
- [ ] T044 [P] [US2] Create `packages/api/README.md` - Document: purpose (MCP server), architecture (domain/app/infra), how to run, API endpoints/tools
- [ ] T045 [P] [US2] Create `packages/ui/README.md` - Document: purpose (dashboard), tech stack, how to run dev server, build for production

### Implementation for User Story 2 - Part E: Install Workspace Dependencies

- [ ] T046 [US2] Run `bun install` to initialize workspace
- [ ] T047 [US2] Verify workspace packages linked with `bun pm ls --all`
- [ ] T048 [US2] Commit package structure: `git commit -m "feat: setup monorepo structure with 4 packages"`

### Implementation for User Story 2 - Part F: Code Migration (CRITICAL SECTION)

**⚠️ HIGH RISK: Proceed carefully, verify after each step**

- [ ] T049 [P] [US2] Copy `types/` directory to `packages/shared/src/types/`
- [ ] T050 [US2] Create `packages/shared/src/index.ts` exporting all types
- [ ] T051 [US2] Build shared package: `cd packages/shared && bun run build`
- [ ] T052 [P] [US2] Copy `src/domain/` to `packages/api/src/domain/`
- [ ] T053 [P] [US2] Copy `src/application/` to `packages/api/src/application/`
- [ ] T054 [P] [US2] Copy `src/infrastructure/mcp/` to `packages/api/src/infrastructure/mcp/`
- [ ] T055 [P] [US2] Copy `src/infrastructure/storage/` to `packages/api/src/infrastructure/storage/`
- [ ] T056 [P] [US2] Copy `src/infrastructure/background/` to `packages/api/src/infrastructure/background/`
- [ ] T057 [US2] Create `packages/api/src/index.ts` with public API exports
- [ ] T058 [P] [US2] Copy `src/infrastructure/cli/` to `packages/cli/src/`
- [ ] T059 [US2] Create `packages/cli/src/index.ts` as CLI entry point with shebang
- [ ] T060 [P] [US2] Copy `dashboard/` contents to `packages/ui/src/`
- [ ] T061 [US2] Create `packages/ui/src/main.ts` as UI entry point
- [ ] T062 [P] [US2] Copy `tests/unit/domain/` to `packages/api/tests/domain/`
- [ ] T063 [P] [US2] Copy `tests/unit/application/` to `packages/api/tests/application/`
- [ ] T064 [P] [US2] Copy `tests/integration/` to `packages/api/tests/integration/`
- [ ] T065 [P] [US2] Copy `tests/unit/infrastructure/cli/` to `packages/cli/tests/`
- [ ] T066 [P] [US2] Copy UI tests (if exist) to `packages/ui/tests/`
- [ ] T066.5 [US2] **VERIFICATION**: Verify test fixtures copied correctly: `find packages/*/tests -name "__fixtures__" -o -name "fixtures" -type d` (ensure all test data migrated)

### Implementation for User Story 2 - Part G: Import Path Updates (MOST CRITICAL)

**⚠️ EXTREMELY HIGH RISK: This is the most error-prone step**

- [ ] T067 [US2] Create import path update script in `/tmp/update-imports.sh` (see quickstart.md for script)
- [ ] T067.5 [US2] **CRITICAL BACKUP**: Create backup of packages/ before import updates: `cp -r packages/ packages-backup/` (allows rollback if script fails)
- [ ] T068 [US2] Run import update script on all TypeScript files in `packages/`
- [ ] T069 [US2] Manually review import updates in `packages/api/src/domain/` (sample 5 files)
- [ ] T070 [US2] Manually review import updates in `packages/cli/src/` (sample 3 files)
- [ ] T071 [US2] Run TypeScript compiler: `bun run type-check` (fix any errors before proceeding)
- [ ] T072 [US2] Run ESLint: `bun run lint` (fix any import errors)

### Implementation for User Story 2 - Part H: Testing & Validation

- [ ] T073 [US2] Run shared package tests: `bun --filter=@kioku/shared test`
- [ ] T074 [US2] Run API package tests: `bun --filter=@kioku/api test`
- [ ] T075 [US2] Run CLI package tests: `bun --filter=@kioku/cli test`
- [ ] T076 [US2] Run UI package tests (if applicable): `bun --filter=@kioku/ui test`
- [ ] T077 [US2] Run all tests: `bun test` (must pass 100%)
- [ ] T078 [US2] Run test coverage: `bun test:coverage` (must be ≥90%)
- [ ] T079 [US2] Build all packages: `bun run build` (must succeed for all 4 packages)
- [ ] T080 [US2] Verify individual package builds: `bun run build:cli` completes in <5 seconds

### Implementation for User Story 2 - Part I: Cleanup

**⚠️ ONLY proceed if ALL tests pass**

- [ ] T081 [US2] Delete old `src/` directory: `rm -rf src/`
- [ ] T082 [US2] Delete old `tests/` directory: `rm -rf tests/`
- [ ] T083 [US2] Delete old `types/` directory: `rm -rf types/`
- [ ] T084 [US2] Delete old `dashboard/` directory: `rm -rf dashboard/`
- [ ] T085 [US2] Commit code migration: `git commit -m "feat: migrate code to monorepo packages"`

**Checkpoint**: User Story 2 complete and independently testable ✓ (Monorepo structure delivered!)

---

## Phase 5: User Story 3 - Clear Package Boundaries (Priority: P3)

**Goal**: Validate package boundaries and prevent architectural violations

**Independent Test**: Review package structure, verify no circular dependencies, confirm linting catches boundary violations

### Implementation for User Story 3

- [ ] T086 [P] [US3] Run `bun pm ls --all` and verify no circular dependencies in output
- [ ] T087 [US3] Review `packages/cli/src/` - confirm only CLI code (commands, arg parsing, terminal output)
- [ ] T088 [US3] Review `packages/api/src/` - confirm only MCP server, domain, application, infrastructure
- [ ] T089 [US3] Review `packages/ui/src/` - confirm only UI components, routes, static assets
- [ ] T090 [US3] Review `packages/shared/src/` - confirm only types, utilities, constants (no business logic)
- [ ] T091 [US3] Verify CLI package does not import from UI package (search imports manually or with grep)
- [ ] T092 [US3] Verify UI package does not import from CLI package
- [ ] T093 [US3] Verify API package does not import from CLI or UI packages
- [ ] T094 [US3] Update ESLint config to enforce package boundary rules (if not already configured)
- [ ] T095 [US3] Run `bun run lint` and verify no package boundary violations
- [ ] T096 [US3] Document package dependencies in `docs/architecture.md` (create if needed)
- [ ] T096.5 [US3] **CONSTITUTION CHECK**: Validate Principle 5 (Simplicity Over Features) - verify each package has <3 directory nesting levels, <20 files, and no unnecessary complexity introduced
- [ ] T097 [US3] Commit boundary validation: `git commit -m "feat: validate and document package boundaries"`

**Checkpoint**: User Story 3 complete ✓ (Architectural boundaries validated!)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T098 [P] Update root README.md to explain monorepo structure and new commands
- [ ] T099 [P] Verify `.gitignore` covers all package dist/ directories
- [ ] T100 [US2] Run full quality gate: `bun run quality-gate` (type-check + lint + test)
- [ ] T101 Create rollback documentation in `docs/rollback-guide.md`
- [ ] T102 Run quickstart.md validation (manual walkthrough)
- [ ] T103 Tag completion: `git tag -a v0.2.0-monorepo -m "Complete monorepo restructure"`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - **US1 (Phase 3 - P1)**: Can start after Foundational - No dependencies on other stories (MVP!)
  - **US2 (Phase 4 - P2)**: Can start after Foundational - No dependencies on US1 (but logically follows)
  - **US3 (Phase 5 - P3)**: Depends on US2 completion (validates monorepo structure)
- **Polish (Phase 6)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1) - Documentation**: ✅ Independent - can deliver as MVP
- **User Story 2 (P2) - Monorepo**: ✅ Independent (but builds on US1 conceptually)
- **User Story 3 (P3) - Boundaries**: ⚠️ Depends on US2 (validates structure created in US2)

### Critical Path

```
Setup → Foundational → US1 (Docs) → [Can stop here for MVP]
                      ↓
                    US2 (Monorepo) → US3 (Validation) → Polish
```

### Parallel Opportunities

**Within User Story 1** (Tasks T010-T015):
```bash
# All file moves can happen in parallel
Task T010, T011, T012, T013, T014, T015
```

**Within User Story 2 - Structure Creation** (Tasks T023-T030):
```bash
# All directory creation tasks
Task T023, T024, T025, T026, T027, T028, T029, T030
```

**Within User Story 2 - Package Config** (Tasks T031-T034):
```bash
# All package.json creation tasks
Task T031, T032, T033, T034
```

**Within User Story 2 - Code Copying** (Tasks T052-T056, T062-T066):
```bash
# Different directories can be copied in parallel
Task T052, T053, T054, T055, T056  # API code
Task T062, T063, T064, T065, T066  # Test code
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**Timeline**: ~30 minutes

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Documentation)
4. **STOP and VALIDATE**: Verify docs are organized, links work
5. Commit and tag: `v0.1.1-docs-organized`
6. **MVP delivered!** - Improved documentation discoverability

**Benefits**:
- Low risk (just file moves)
- Immediate value (better docs navigation)
- Can pause before complex monorepo migration

### Incremental Delivery

**Timeline**: 4-5 hours total

1. Deliver US1 (~30 min) → Commit → Test
2. Add US2 Part A-E (~1 hour) → Commit → Test (structure only)
3. Add US2 Part F-I (~2-3 hours) → Commit → Test (code migration)
4. Add US3 (~30 min) → Commit → Test (validation)
5. Polish (~30 min) → Final commit → Tag

**Benefits**:
- Each phase adds value independently
- Can pause between phases for review
- Git history shows clear progression
- Easy to rollback to last working state

### Parallel Team Strategy

If multiple developers available:

**After Foundational completes**:
- Developer A: US1 (Documentation) - 30 min
- Developer B: US2 Part A-E (Structure setup) - 1 hour
  - **Wait for Developer B to finish US2 Part A-E**
  - Then Developer A helps with US2 Part F-I (Code migration)
- After US2 complete:
  - Developer A: US3 (Validation) - 30 min
  - Developer B: Polish tasks

---

## Notes

- **[P] tasks**: Different files, no dependencies, can run in parallel
- **[Story] labels**: US1 (docs), US2 (monorepo), US3 (validation)
- **Each user story is independently testable** per acceptance scenarios
- **MVP = User Story 1 only** (30 minutes, low risk)
- **High risk section**: US2 Part F-G (code migration + import updates)
- **Validation checkpoints** after each user story phase
- **Rollback plan**: Git reset to pre-US2 if imports fail
- **Quality gates enforced**: 90% coverage, type-check, lint must pass

---

## Task Count Summary

- **Total Tasks**: 106 (added 3 verification/quality tasks from analysis findings)
- **Setup**: 3 tasks
- **Foundational**: 5 tasks
- **User Story 1** (P1 - Docs): 13 tasks (T009-T021)
- **User Story 2** (P2 - Monorepo): 67 tasks (T022-T085 + T066.5, T067.5)
  - Part A (Structure): 9 tasks
  - Part B (Config): 7 tasks
  - Part C (TypeScript): 4 tasks
  - Part D (READMEs): 4 tasks
  - Part E (Install): 3 tasks
  - Part F (Code Migration): 19 tasks (+T066.5 verification)
  - Part G (Import Updates): 7 tasks (+T067.5 backup)
  - Part H (Testing): 8 tasks
  - Part I (Cleanup): 5 tasks
- **User Story 3** (P3 - Validation): 13 tasks (T086-T097 + T096.5)
- **Polish**: 6 tasks (T098-T103)

**Parallel Opportunities**: 45 tasks marked [P] (can run simultaneously if multiple devs)

---

## Success Criteria Validation

After all tasks complete, verify against spec success criteria:

- [ ] **SC-001**: Developer locates any doc in <30 seconds (test manually)
- [ ] **SC-002**: All 6 markdown files moved to docs/ successfully
- [ ] **SC-003**: Each package builds independently in <5 seconds
- [ ] **SC-004**: Onboarding time reduced (measure with new contributor)
- [ ] **SC-005**: All tests pass, zero functionality regressions
- [ ] **SC-006**: Doc search time reduced by 50% (user survey)
- [ ] **SC-007**: Zero circular dependencies (`bun pm ls`)
- [ ] **SC-008**: Individual package builds <5 seconds
- [ ] **SC-009**: Workspace dependencies resolve automatically
- [ ] **SC-010**: 100% of import paths updated correctly (type-check passes)

---

**Status**: Ready for `/speckit.implement` or manual execution following quickstart.md
