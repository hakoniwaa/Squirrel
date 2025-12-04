# @kioku/cli

**Command-line interface** for Kioku context management tool.

## Purpose

This package provides the CLI commands for interacting with Kioku:
- `kioku init` - Initialize project context
- `kioku serve` - Start MCP server (used by editors)
- `kioku show` - Display current context
- `kioku status` - Show system health
- `kioku setup` - Interactive setup wizard
- `kioku doctor` - Health diagnostics and auto-repair
- `kioku dashboard` - Start visual dashboard

## Installation

This package is internal to the Kioku monorepo. The CLI is built and made available via the root package's `bin` field.

## Usage

After building the monorepo:

```bash
# From repository root
bun run build

# Run CLI commands
kioku init
kioku serve
kioku show
kioku status
kioku setup
kioku doctor
kioku dashboard
```

## Available Commands

### Core Commands
- **init** - Initialize context for current project
- **serve** - Start MCP server (stdio mode)
- **show** - Display project context overview
- **status** - Show system health and statistics

### Setup & Diagnostics
- **setup** - Interactive setup wizard with API key validation
- **doctor** - Run health checks with optional auto-repair
- **dashboard** - Start visual dashboard (default: localhost:3456)

### Command Options

```bash
# Setup
kioku setup -y --project-type web-app --editor claude

# Doctor
kioku doctor --repair        # Auto-fix issues
kioku doctor --verbose       # Detailed diagnostics
kioku doctor --export report.json

# Dashboard
kioku dashboard --port 8080  # Custom port
kioku dashboard --no-browser # Don't auto-open browser
```

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

The CLI package:
- Depends on `@kioku/api` for business logic
- Depends on `@kioku/shared` for types and utilities
- Handles command-line argument parsing
- Provides terminal output formatting
- No business logic (orchestrates API package)

---

**See also**: [Main README](../../README.md) | [API Package](../api/) | [Shared Package](../shared/)
