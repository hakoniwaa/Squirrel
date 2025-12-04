# Feature Specification: Documentation Organization and Monorepo Restructure

**Feature Branch**: `003-documentation-organization-and`  
**Created**: 2025-10-11  
**Status**: Draft  
**Input**: User description: "create a doc folder at the root of the project where we will keep all the md files in it and rename them while providing structured to them, also we need to restructure the project to be a monorepo where cli/api/ui are the packages for kioku app"

## Clarifications

### Session 2025-10-11

- Q: What should the shared package be named? → A: packages/shared
- Q: How should README.md be handled? → A: Keep root README.md as-is, create new package-specific READMEs from scratch. CLAUDE.md also stays at root.
- Q: What subdirectory structure should docs/ have? → A: Flat structure - all files directly in docs/ with descriptive names (no subdirectories)
- Q: Out of Scope clarifications → A: Creating package READMEs is IN scope (exception to "no new content"). Link updates in markdown files IN scope. Import path updates IN scope (required for functionality). Bug fixes during implementation require validation before inclusion.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Centralized Documentation Discovery (Priority: P1)

Developers need to quickly find and understand project documentation without hunting through scattered markdown files at the repository root.

**Why this priority**: This is foundational for project comprehension. Scattered documentation causes confusion and slows onboarding. Centralizing docs improves discoverability and reduces cognitive load.

**Independent Test**: Can be fully tested by navigating to the `docs/` folder and verifying all documentation files are present with clear, descriptive names in a flat structure (no subdirectories). Developer can find any piece of information within 30 seconds.

**Acceptance Scenarios**:

1. **Given** a developer cloning the Kioku repository, **When** they want to understand the project, **Then** they find a centralized `docs/` folder with clearly named documentation files organized by category
2. **Given** a developer looking for setup instructions, **When** they navigate to `docs/`, **Then** they find a setup guide in the appropriate category without searching the root directory
3. **Given** scattered markdown files at root (CLAUDE.md, README.md, SETUP_GUIDE.md, etc.), **When** documentation is reorganized, **Then** files (except README.md and CLAUDE.md) are moved to `docs/` with descriptive names in a flat structure
4. **Given** the new docs structure, **When** a developer needs specific documentation, **Then** they can locate it directly in `docs/` folder by its descriptive filename

---

### User Story 2 - Independent Package Development (Priority: P2)

Developers need to work on CLI, API, or UI components independently without conflicts, enabling parallel development and clear separation of concerns.

**Why this priority**: Monorepo structure with separate packages enables team scalability, clearer ownership, and independent deployment. This is critical for growing the Kioku ecosystem beyond a single application.

**Independent Test**: Can be fully tested by running commands in each package independently (`bun test` in packages/cli, packages/api, packages/ui) and verifying builds, tests, and dependencies are isolated. Each package can be developed, tested, and published independently.

**Acceptance Scenarios**:

1. **Given** a monorepo structure with packages, **When** a developer wants to work on the CLI, **Then** they can navigate to `packages/cli/` and run tests, build, and develop without touching API or UI code
2. **Given** separate packages for cli/api/ui, **When** each package is built, **Then** build artifacts are isolated (packages/cli/dist, packages/api/dist, packages/ui/dist) without conflicts
3. **Given** the current single-package structure, **When** restructured as monorepo, **Then** existing src/ code is organized into appropriate packages (cli = src/infrastructure/cli, api = src/infrastructure/mcp + services, ui = dashboard)
4. **Given** multiple packages, **When** dependencies are shared, **Then** common code is in packages/shared reusable across cli/api/ui
5. **Given** a monorepo workspace, **When** a developer installs dependencies, **Then** workspace management (Bun workspaces or similar) resolves cross-package dependencies correctly

---

### User Story 3 - Clear Package Boundaries (Priority: P3)

Developers need to understand what code belongs in which package (CLI vs API vs UI) to maintain architectural consistency and prevent coupling.

**Why this priority**: Clear boundaries prevent architectural erosion and make the codebase easier to reason about. This ensures long-term maintainability as the project grows.

**Independent Test**: Can be fully tested by reviewing the package structure and verifying: (1) CLI package contains only command-line interface code, (2) API package contains only MCP server and business logic, (3) UI package contains only dashboard/web interface, (4) No circular dependencies between packages.

**Acceptance Scenarios**:

1. **Given** the monorepo structure, **When** reviewing package contents, **Then** CLI package contains only CLI-specific code (commands, argument parsing, terminal output)
2. **Given** the monorepo structure, **When** reviewing package contents, **Then** API package contains MCP server, business logic, storage, and background services
3. **Given** the monorepo structure, **When** reviewing package contents, **Then** UI package contains only web dashboard code (components, routes, static assets)
4. **Given** shared utilities or domain logic, **When** multiple packages need them, **Then** they are in a shared package imported by dependent packages
5. **Given** package boundaries defined, **When** linting or validation runs, **Then** violations (e.g., CLI importing from UI) are detected and prevented

---

### Edge Cases

- README.md and CLAUDE.md remain at repository root (not moved to docs/). All other markdown files move to docs/.
- Markdown links in README.md and CLAUDE.md must be updated to point to new locations in docs/
- What happens to build scripts and configuration files (package.json, tsconfig.json) when split into packages?
- How are cross-package dependencies managed (e.g., API and CLI both need core domain logic)?
- What happens to existing tests when code is moved into packages?
- How do environment variables and configuration files work across packages?
- **UI Package Scope**: Dashboard frontend code (React/Vue components, routes, static assets) goes in packages/ui/. Any backend API routes for serving the dashboard go in packages/api/src/infrastructure/http/ (not in UI package). UI package has no server-side logic.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST create a `docs/` directory at the repository root to centralize all documentation
- **FR-002**: System MUST move markdown files from root directly into `docs/` folder (flat structure, no subdirectories), EXCEPT README.md and CLAUDE.md which remain at root
- **FR-003**: System MUST rename markdown files to be descriptive and follow a consistent naming convention (e.g., kebab-case: setup-guide.md, project-overview.md)
- **FR-004**: System MUST create a `packages/` directory at repository root to house monorepo packages
- **FR-005**: System MUST create three primary packages: `packages/cli/`, `packages/api/`, `packages/ui/`
- **FR-006**: System MUST move existing CLI code (src/infrastructure/cli/) into `packages/cli/src/`
- **FR-007**: System MUST move existing API/MCP server code (src/infrastructure/mcp/, src/application/, src/domain/) into `packages/api/src/`
- **FR-008**: System MUST move existing dashboard code (dashboard/) into `packages/ui/src/`
- **FR-009**: System MUST create shared package `packages/shared/` for common domain logic, types, and utilities used across packages
- **FR-010**: System MUST configure workspace management to link packages (bun workspaces or equivalent)
- **FR-011**: System MUST update all import paths to reflect new package structure
- **FR-012**: System MUST ensure each package has independent package.json with appropriate dependencies
- **FR-013**: System MUST preserve existing tests and move them to appropriate package test directories
- **FR-014**: System MUST update build scripts to support monorepo builds (build all packages or individual packages)
- **FR-015**: System MUST maintain existing functionality - no features break during restructure
- **FR-016**: Root-level README.md remains at repository root, updated to reference docs/ folder and fix any broken links to moved files
- **FR-017**: Root-level CLAUDE.md remains at repository root (AI development guide), updated to fix any broken links to moved files
- **FR-018**: Each package MUST have its own README.md explaining package purpose and usage (created new, not moved from root)
- **FR-019**: System MUST update internal markdown links when files are moved (e.g., links in README.md pointing to moved documentation files)

### Key Entities

- **Documentation File**: Markdown file containing project information (guides, architecture, API docs, setup instructions)
  - Attributes: original filename, new filename, category/subdirectory, content type (guide, reference, overview)
  
- **Package**: Independent module in the monorepo (cli, api, ui, shared)
  - Attributes: name, source directory, dependencies, build output, package.json configuration
  - Note: Shared package is named `packages/shared/`
  
- **Documentation Category**: Logical categorization reflected in filenames (not directory structure)
  - Examples: setup-guide.md, architecture-overview.md, api-reference.md, contribution-guide.md (all in docs/ root)

- **Source Code Module**: Existing codebase sections to be reorganized
  - Attributes: current path, target package, dependencies, imports to update

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can locate any documentation file within 30 seconds by navigating the `docs/` folder structure
- **SC-002**: All markdown files from repository root (except README.md and CLAUDE.md) are moved to `docs/` with zero files lost or corrupted
- **SC-003**: Each package (cli, api, ui) can be built and tested independently without requiring other packages to be built first
- **SC-004**: Monorepo structure reduces onboarding time for new contributors by 40% (measured by time to first successful contribution)
- **SC-005**: All existing tests pass after restructure with no functionality regressions
- **SC-006**: Documentation is easier to navigate with centralized docs/ folder compared to root-level files (validated by: developer can locate any doc in <30 seconds per SC-001, no scattered files at root per SC-002)
- **SC-007**: Package boundaries are enforced with zero circular dependencies detected by linting tools
- **SC-008**: Build time for individual packages is under 5 seconds, enabling fast iteration during development
- **SC-009**: Workspace configuration correctly resolves cross-package dependencies with zero manual linking required
- **SC-010**: 100% of import paths are updated correctly with zero broken imports after restructure

## Assumptions

- **Documentation Organization**: 
  - README.md and CLAUDE.md remain at repository root (special status as primary entry points)
  - Flat structure: all other markdown files move directly into docs/ with descriptive kebab-case names (e.g., kioku.md → docs/project-overview.md, SETUP_GUIDE.md → docs/setup-guide.md, CHANGELOG.md → docs/changelog.md)
  - No subdirectories within docs/ - simple flat list for easy navigation
  - Assumes existing .specify/ documentation remains in .specify/ (spec-driven development artifacts)
  
- **Monorepo Structure**:
  - Assumes Bun workspace support is sufficient for monorepo management (no Nx, Turborepo, or Lerna required for MVP)
  - Assumes CLI package is primarily for command-line interface concerns (kioku init, kioku serve, kioku status commands)
  - Assumes API package contains MCP server, business logic, storage layer, and background services
  - Assumes UI package is for dashboard web interface (currently in dashboard/ directory)
  - Assumes packages/shared is needed for domain models, types, and utilities used by multiple packages
  
- **Migration Strategy**:
  - Assumes gradual migration is acceptable (can be done in phases: docs first, then monorepo)
  - Assumes existing functionality must be preserved (no breaking changes to end users)
  - Assumes test coverage exists and should be maintained during restructure
  - Assumes build configuration (tsconfig, package.json) needs updating but format remains compatible

- **Tooling**:
  - Assumes Bun as runtime/package manager (already in use per package.json)
  - Assumes TypeScript as primary language (already in use)
  - Assumes current quality gates (lint, type-check, test) should work across packages

## Out of Scope

The following are explicitly NOT included in this feature:

- **Rewriting or expanding existing documentation content** (only organizing and moving files; exception: creating new package READMEs is IN scope per FR-018)
- **Changing build tools** (staying with Bun + TypeScript)
- **Adding new packages beyond cli/api/ui/shared** (future packages like plugins, extensions, etc. require separate discussion and validation)
- **Implementing package versioning or independent publishing to npm** (monorepo packages remain internal)
- **Setting up CI/CD pipeline for monorepo** (separate concern, different feature)
- **Adding monorepo tooling like Nx, Turborepo, or Lerna** (using Bun workspaces only; advanced tooling may be future enhancement)
- **Refactoring or rewriting code within packages** (only moving and organizing; exception: import path updates are IN scope per FR-011, and critical bugs discovered during implementation require validation before fixing)
- **Updating external documentation** (only internal markdown files; no changes to external wikis, websites, or third-party docs)

### Notes on Scope Boundaries

- **Link updates**: Updating internal markdown links when files move is IN scope (FR-016, FR-017, FR-019)
- **Import path updates**: Required for functionality after code moves, therefore IN scope (FR-011)
- **Package READMEs**: Creating new README.md files for each package is IN scope (FR-018) - this is the only "new content" allowed
- **Bug fixes**: Any bugs discovered during restructure must be validated together before inclusion (not automatic)
