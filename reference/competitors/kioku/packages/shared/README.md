# @kioku/shared

**Shared types, utilities, and constants** used across Kioku packages.

## Purpose

This package contains common code that is reused by `@kioku/cli`, `@kioku/api`, and `@kioku/ui`:
- TypeScript type definitions
- Utility functions (pure, reusable logic)
- Constants and configuration values

## Installation

This package is internal to the Kioku monorepo and uses workspace dependencies:

```json
{
  "dependencies": {
    "@kioku/shared": "workspace:*"
  }
}
```

## Usage

Import types and utilities from other packages:

```typescript
// From @kioku/cli, @kioku/api, or @kioku/ui
import { ProjectContext, ModuleContext } from '@kioku/shared/types';
import { calculateScore } from '@kioku/shared/utils';
```

## What's Exported

- **Types** (`src/types/`): TypeScript interfaces and types
  - `ProjectContext` - Project context structure
  - `ModuleContext` - Module metadata
  - `Discovery` - Extracted insights
  - And more...

- **Utils** (`src/utils/`): Pure utility functions
  - Score calculations
  - Data transformations
  - Validation helpers

- **Constants**: Shared configuration values

## Development

```bash
# Build the package
bun run build

# Run tests
bun test

# Type check
tsc --noEmit
```

## Architecture

This package follows **pure functional programming** principles:
- All functions are pure (no side effects)
- Immutable data structures
- No I/O operations (those belong in infrastructure packages)

---

**See also**: [Main README](../../README.md) | [API Package](../api/) | [CLI Package](../cli/)
