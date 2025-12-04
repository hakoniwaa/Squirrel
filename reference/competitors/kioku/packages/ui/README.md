# @kioku/ui

**Visual dashboard** for Kioku context management.

## Purpose

This package provides the web-based dashboard for visualizing Kioku's context and insights:
- Real-time project overview
- Session timeline and history
- Module dependency graph
- Embeddings visualization
- Context window statistics
- Performance metrics

## Installation

This package is internal to the Kioku monorepo and uses workspace dependencies:

```json
{
  "dependencies": {
    "@kioku/ui": "workspace:*"
  }
}
```

## Usage

Start the dashboard:

```bash
# From CLI
kioku dashboard

# With custom port
kioku dashboard --port 8080

# Without auto-opening browser
kioku dashboard --no-browser
```

The dashboard will be available at `http://localhost:3456` (default).

## Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **API Client**: Fetch to Fastify backend

## Development

```bash
# Build the package
bun run build

# Run dev server (with hot reload)
bun run dev

# Run tests
bun test
```

## Architecture

This package contains **frontend code only**:
- React components for UI
- Routes and navigation
- Static assets (icons, styles)

**Backend API routes** are in `@kioku/api/src/infrastructure/http/` (not in this package).

### Directory Structure

- `src/components/` - React components
- `src/services/` - API client services
- `src/types/` - UI-specific TypeScript types
- `src/utils/` - Frontend utilities
- `public/` - Static assets

## Features

- **Project Overview** - Tech stack, architecture, module count
- **Session Timeline** - Recent coding sessions with summaries
- **Module Graph** - Visual dependency map
- **Embeddings Stats** - Vector database insights
- **Context Window** - Usage and pruning statistics
- **Real-time Updates** - Live data refresh

---

**See also**: [Main README](../../README.md) | [API Package](../api/) | [CLI Package](../cli/)
