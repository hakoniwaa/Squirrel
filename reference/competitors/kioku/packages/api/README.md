# @kioku/api

**MCP server and core business logic** for Kioku context management.

## Purpose

This package contains the core functionality of Kioku:
- **MCP Server** - Model Context Protocol implementation
- **Domain Logic** - Pure business logic and calculations
- **Application Services** - Use cases and orchestration
- **Infrastructure** - Storage, external APIs, background services

## Installation

This package is internal to the Kioku monorepo and uses workspace dependencies:

```json
{
  "dependencies": {
    "@kioku/api": "workspace:*"
  }
}
```

## Usage

The API package is used by the CLI to provide functionality:

```typescript
// From @kioku/cli
import { ProjectScanner, ContextManager } from '@kioku/api';
import { DiscoveryExtractor } from '@kioku/api';

const scanner = new ProjectScanner();
const context = await scanner.scan('/path/to/project');
```

## Architecture

This package follows **Onion Architecture**:

```
Infrastructure (🔴)  ← I/O, MCP, Storage, External APIs
    ↓
Application (🟡)     ← Use Cases, Services
    ↓
Domain (🟢)          ← Pure Business Logic
```

### Directory Structure

- **`src/domain/`** - Pure business logic (no I/O)
  - `models/` - Data structures
  - `calculations/` - Pure functions
  - `rules/` - Business rules

- **`src/application/`** - Application logic
  - `use-cases/` - Feature workflows
  - `services/` - Application services
  - `ports/` - Interfaces for infrastructure

- **`src/infrastructure/`** - External world
  - `mcp/` - MCP server implementation
  - `storage/` - SQLite, ChromaDB, YAML
  - `background/` - Scorer, pruner, auto-save services
  - `external/` - OpenAI, Anthropic API clients

## MCP Resources

Available via the MCP server:

- `context://project` - Project context
- `context://modules` - Module documentation
- `context://session_history` - Session summaries

## MCP Tools

- `context_search` - Semantic search
- `read_file` - File access with tracking
- `grep_codebase` - Pattern search
- `git_log`, `git_blame`, `git_diff` - Git analysis

## Development

```bash
# Build the package
bun run build

# Run tests
bun test

# Type check
tsc --noEmit
```

## Testing

This package has **90%+ test coverage requirement**:
- Unit tests for domain logic (100% coverage)
- Integration tests for MCP server
- Service tests with dependency injection

---

**See also**: [Main README](../../README.md) | [CLI Package](../cli/) | [Shared Package](../shared/)
