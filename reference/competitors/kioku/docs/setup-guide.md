# Kioku - Local Development Setup Guide

This guide will help you set up and use Kioku locally for testing and development.

## Prerequisites

- Bun installed (`curl -fsSL https://bun.sh/install | bash`)
- Node.js 18+ (optional, Bun is preferred)

## Quick Start

### 1. Install Kioku Globally

From the Kioku repository:

```bash
cd /path/to/kioku
bun install
bun link
```

This makes the `kioku` command available globally.

### 2. Initialize Kioku in Your Project

Navigate to any project where you want to use Kioku:

```bash
cd /path/to/your-project
kioku init
```

This creates a `.context/` directory with:
- `project.yaml` - Project metadata
- `sessions.db` - SQLite database for sessions
- `chroma/` - Vector database (created when needed)

### 3. Start the Dashboard

**Option A: Using the `kioku dashboard` command (Recommended)**

```bash
cd /path/to/your-project
kioku dashboard
```

This will:
- Start the API server on `http://localhost:9090`
- Start the dashboard UI on `http://localhost:3456`
- Automatically open your browser

**Options:**
```bash
kioku dashboard --no-browser        # Don't auto-open browser
kioku dashboard --port 8080         # Use custom dashboard port
kioku dashboard --api-port 9000     # Use custom API port
```

**Option B: For development (separate processes)**

If you're developing the dashboard itself:

```bash
# Terminal 1: Start the API server manually
cd /path/to/kioku
bun run src/infrastructure/monitoring/api-server.ts

# Terminal 2: Start the dashboard dev server
cd dashboard
bun run dev
```

Note: Option B requires modifying Vite proxy config to point to the correct API port.

## How It Works

### Architecture

```
┌─────────────────┐
│   Dashboard UI  │ (React, port 3456)
│  (Vite + React) │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   API Server    │ (Fastify, port 9090)
│  (REST Endpoints)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  sessions.db    │ (SQLite)
│  + chroma/      │ (Vector DB)
└─────────────────┘
```

### Dashboard Features

The dashboard shows real-time context information:

- **Project Overview**: Name, tech stack, module/file counts, database size
- **Session Timeline**: Past sessions with expandable details
- **Module Graph**: Interactive dependency visualization
- **Embeddings Stats**: Embeddings count, queue, errors, disk usage
- **Context Window**: Usage percentage with health indicators

All data updates every 5 seconds automatically.

## Troubleshooting

### Error: "Database not found"

**Problem**: Dashboard can't find the database.

**Solution**:
```bash
# Make sure you're in a directory with .context/
cd /path/to/your-project
ls .context/sessions.db

# If missing, run init again
kioku init
```

### Error: "Axios 500 error" in Dashboard

**Problem**: The API server is not running.

**Solution**:
- If using `kioku dashboard`, make sure both servers start (check terminal output)
- If developing dashboard separately, start the API server first (see Option B above)
- Check that port 9090 is not already in use

### Error: "Dashboard not built"

**Problem**: The dashboard hasn't been compiled.

**Solution**:
```bash
cd /path/to/kioku/dashboard
bun install
bun run build
```

This creates `dashboard/dist/` with the compiled assets.

### Port Already in Use

**Problem**: Port 3456 or 9090 is already taken.

**Solution**:
```bash
# Use custom ports
kioku dashboard --port 4000 --api-port 5000
```

### Dashboard Shows Empty Data

**Expected Behavior**: On a fresh init, the dashboard will show:
- 0 modules
- 0 files
- No sessions
- Empty graphs

This is normal! The dashboard displays whatever is in the database. To see real data:

1. Use the MCP server (`kioku serve`) with an AI assistant
2. Have conversations that access files
3. The system will create sessions and populate the database
4. Then the dashboard will show meaningful data

## Development Workflow

### Making Changes to the Dashboard

1. **Edit React components**:
   ```bash
   cd dashboard/src/components
   # Edit ProjectOverview.tsx, SessionTimeline.tsx, etc.
   ```

2. **Test with hot reload**:
   ```bash
   cd dashboard
   bun run dev
   ```

3. **Build for production**:
   ```bash
   cd dashboard
   bun run build
   ```

4. **Test the production build**:
   ```bash
   cd /path/to/test-project
   kioku dashboard
   ```

### Making Changes to API Endpoints

1. **Edit API code**:
   ```bash
   # Edit src/infrastructure/monitoring/api-endpoints.ts
   ```

2. **Rebuild**:
   ```bash
   cd /path/to/kioku
   bun run build
   ```

3. **Test**:
   ```bash
   cd /path/to/test-project
   kioku dashboard
   ```

## Testing with Sample Data

To see the dashboard with actual data, you can:

### Option 1: Use with Claude Desktop (MCP)

1. Add Kioku to Claude Desktop config:
   ```json
   {
     "mcpServers": {
       "kioku": {
         "command": "kioku",
         "args": ["serve"]
       }
     }
   }
   ```

2. Start Claude Desktop
3. Have conversations about your codebase
4. Open dashboard: `kioku dashboard`

### Option 2: Manually Insert Test Data

```bash
cd /path/to/test-project
sqlite3 .context/sessions.db

-- Insert a test session
INSERT INTO sessions (id, start_time, created_at, updated_at)
VALUES ('test-session-1', datetime('now'), datetime('now'), datetime('now'));

-- Insert test chunks
INSERT INTO chunks (id, file_path, module_path, start_line, end_line, code, created_at, updated_at)
VALUES 
  ('chunk-1', 'src/index.ts', 'src', 1, 10, 'console.log("test");', datetime('now'), datetime('now')),
  ('chunk-2', 'src/utils.ts', 'src', 1, 20, 'export const add = (a, b) => a + b;', datetime('now'), datetime('now'));
```

Then refresh the dashboard to see the data.

## File Locations

```
your-project/
├── .context/                    # Created by `kioku init`
│   ├── project.yaml            # Project metadata
│   ├── sessions.db             # SQLite database
│   ├── sessions.db-shm         # SQLite shared memory
│   ├── sessions.db-wal         # SQLite write-ahead log
│   └── chroma/                 # Vector database (created when needed)
│       └── [vector data]
```

```
kioku/
├── src/
│   ├── infrastructure/
│   │   ├── cli/
│   │   │   ├── commands/
│   │   │   │   └── dashboard.ts    # Dashboard CLI command
│   │   │   └── index.ts            # Main CLI entry
│   │   └── monitoring/
│   │       └── api-endpoints.ts    # REST API routes
│   └── ...
├── dashboard/
│   ├── src/
│   │   ├── components/             # React components
│   │   │   ├── ProjectOverview.tsx
│   │   │   ├── SessionTimeline.tsx
│   │   │   ├── ModuleGraph.tsx
│   │   │   └── EmbeddingsStats.tsx
│   │   ├── services/
│   │   │   └── api-client.ts       # API client
│   │   └── App.tsx                 # Main app
│   ├── dist/                       # Built dashboard (after `bun run build`)
│   └── package.json
└── SETUP_GUIDE.md                  # This file
```

## API Endpoints

The dashboard consumes these REST endpoints:

- `GET /api/project` - Project overview
- `GET /api/sessions` - Sessions list
- `GET /api/sessions/:id` - Session details
- `GET /api/modules` - Module dependency graph
- `GET /api/embeddings` - Embeddings statistics
- `GET /api/context` - Context window usage
- `GET /api/health` - Service health
- `GET /api/linked-projects` - Linked projects

All endpoints support CORS for `localhost:*`.

## Next Steps

1. ✅ Initialize Kioku: `kioku init`
2. ✅ Start dashboard: `kioku dashboard`
3. 📝 Use with Claude Desktop (add MCP config)
4. 🎨 Explore the dashboard UI
5. 🔧 Make changes and rebuild as needed

## Support

For issues or questions:
- Check logs in terminal output
- Look for error messages in browser console (F12)
- Check that `.context/sessions.db` exists
- Verify ports 3456 and 9090 are available

## Summary

**To use Kioku locally:**

```bash
# 1. Link Kioku globally (one time)
cd /path/to/kioku
bun link

# 2. Initialize in your project
cd /path/to/your-project
kioku init

# 3. Start the dashboard
kioku dashboard

# 4. Open http://localhost:3456 in your browser
```

That's it! 🎉
