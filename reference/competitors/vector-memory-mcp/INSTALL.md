# Installation Guide for Testing

## Quick Local Setup

To test the MCP memory server in Claude Code:

### 1. Install dependencies
```bash
cd /home/aerion/dev/vector-memory-mcp
bun install
```

### 2. Configure Claude Code

Edit `~/.claude/config.json` and add:

```json
{
  "mcpServers": {
    "memory": {
      "command": "bun",
      "args": ["run", "/home/aerion/dev/vector-memory-mcp/src/index.ts"]
    }
  }
}
```

> **Note:** This server requires running with Bun.

### 3. Restart Claude Code

Restart your Claude Code session to load the new MCP server.

### 4. Test the Memory Tools

Try these commands in Claude Code:

```
You: "Remember that we use TypeScript for this project"
[Claude should call the store_memory tool]

You: "What language are we using?"
[Claude should call search_memories and find the answer]
```

## Available Tools

Once installed, Claude Code will have access to these tools:

- `store_memory` - Store a new memory with optional metadata
- `search_memories` - Search for memories using semantic similarity
- `get_memory` - Retrieve a specific memory by ID
- `delete_memory` - Delete a memory by ID

## Database Location

Memories are stored in:
```
~/.local/share/vector-memory-mcp/memories.db
```

You can inspect the database using LanceDB tools if needed.

## Troubleshooting

### Test the server manually
```bash
cd /home/aerion/dev/vector-memory-mcp
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | bun run src/index.ts
```

You should see a JSON response with server info.

### Check Claude Code logs

If the server isn't loading, check the Claude Code logs for error messages.

### Verify Bun is installed
```bash
bun --version
```

Should show Bun 1.0 or higher.

## Development Mode

For development with auto-reload:
```bash
bun run dev
```

This will watch for file changes and restart the server automatically.
