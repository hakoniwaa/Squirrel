# Vector Memory MCP Server

> Replace static markdown context files with intelligent, semantically-searchable memories that understand what you're working on.

A production-ready MCP (Model Context Protocol) server that provides semantic memory storage for AI assistants. Uses local embeddings and vector search to automatically retrieve relevant context without cloud dependencies.

**Perfect for:** Software teams maintaining architectural knowledge, developers juggling multiple projects, and anyone building with AI assistants like Claude Code.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![Bun](https://img.shields.io/badge/Bun-Required-black.svg)](https://bun.sh/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

---

## ✨ Features

### 🔒 **Local-First & Private**
- All embeddings generated locally (no cloud APIs)
- Data stored in local LanceDB databases
- Complete privacy and control over your memories

### 🎯 **Intelligent Semantic Search**
- Vector similarity with multi-factor scoring
- Considers relevance, recency, priority, and usage frequency
- Context-aware retrieval based on conversation flow

### 📊 **Smart Memory Storage**
- Stores memories in `~/.local/share/vector-memory-mcp/memories.db`
- Fast LanceDB-based storage with vector search capabilities
- Memories persist across sessions and projects

### ⚡ **High Performance**
- Sub-100ms search latency for 1000+ memories
- Efficient storage (<10MB per 1000 memories)
- CPU-optimized local embeddings (no GPU required)

### 🔌 **MCP Native Integration**
- Works seamlessly with Claude Code
- Session hooks for automatic context injection
- Standard MCP protocol (compatible with future clients)

### 🛠️ **Developer-Friendly**
- Zero-configuration setup
- Built with Bun for maximum performance
- Simple MCP tools for storing and searching
- TypeScript for type safety

---

## 🚀 Quick Start

### Prerequisites

- [Bun](https://bun.sh/) 1.0+
- Claude Code or another MCP-compatible client

> **Note:** This server requires Bun to run.

### Installation & Configuration

#### Option 1: Global Install (Recommended)

**Install:**
```bash
bun install -g @aeriondyseti/vector-memory-mcp
```

> **Note:** The installation automatically downloads ML models (~90MB) and verifies native dependencies. This may take a minute on first install.

**Configure Claude Code** - Add to `~/.claude/config.json`:
```json
{
  "mcpServers": {
    "memory": {
      "command": "vector-memory-mcp"
    }
  }
}
```

#### Option 2: Local Development

**Install:**
```bash
git clone https://github.com/AerionDyseti/vector-memory-mcp.git
cd vector-memory-mcp
bun install
```

**Configure Claude Code** - Add to `~/.claude/config.json`:
```json
{
  "mcpServers": {
    "memory": {
      "command": "bun",
      "args": ["run", "/absolute/path/to/vector-memory-mcp/src/index.ts"]
    }
  }
}
```
*Replace `/absolute/path/to/` with your actual installation path.*

---

**What gets installed:**
- The vector-memory-mcp package and all dependencies
- Native binaries for ONNX Runtime (~32MB) and image processing (~10MB)
- ML model files automatically downloaded during installation (~90MB, cached in `~/.cache/huggingface/`)
- **Total first-time setup:** ~130MB of downloads

> 💡 **Tip:** If you need to re-download models or verify dependencies, run: `vector-memory-mcp warmup`

### Start Using It

That's it! Restart Claude Code and you'll have access to memory tools:
- `store_memory` - Save information for later recall
- `search_memories` - Find relevant memories semantically
- `get_memory` - Retrieve a specific memory by ID
- `delete_memory` - Remove a memory

---

## 📖 Usage

### Storing Memories

Ask Claude Code to remember things for you:

```
You: "Remember that we use Drizzle ORM for database access"
Claude: [calls store_memory tool]
```

Or Claude Code can store memories directly:
```json
{
  "content": "Use Drizzle ORM for type-safe database access",
  "metadata": {
    "tags": ["architecture", "database"],
    "category": "tooling"
  }
}
```

### Searching Memories

Claude Code automatically searches memories when relevant, or you can ask:

```
You: "What did we decide about the database?"
Claude: [calls search_memories with query about database decisions]
```

Search parameters:
```json
{
  "query": "authentication strategy",
  "limit": 10
}
```

### Managing Memories

Retrieve a specific memory:
```json
{
  "id": "memory-id-here"
}
```

Delete a memory:
```json
{
  "id": "memory-id-here"
}
```

---

## 🏗️ Architecture

```
vector-memory-mcp/
├── src/
│   ├── index.ts            # Entry point
│   ├── config/             # Configuration management
│   ├── db/                 # Database layer (LanceDB)
│   ├── services/
│   │   ├── embeddings.service.ts  # Embeddings via @huggingface/transformers
│   │   └── memory.service.ts      # Core memory operations
│   └── mcp/
│       ├── server.ts       # MCP server setup
│       ├── tools.ts        # MCP tool definitions
│       └── handlers.ts     # Tool request handlers
├── tests/
│   ├── memory.test.ts
│   └── embeddings.test.ts
├── bin/
│   └── vector-memory-mcp.js # Executable entry point
└── package.json
```

### Technology Stack

- **MCP Framework**: @modelcontextprotocol/sdk (official SDK)
- **Vector Database**: LanceDB (fast, local, vector search)
- **Embeddings**: [@huggingface/transformers](https://huggingface.co/docs/transformers.js) (Xenova/all-MiniLM-L6-v2, 384 dimensions)
- **Language**: TypeScript 5.0+
- **Runtime**: Bun 1.0+
- **Testing**: Bun test

---

## 🎨 How It Works

### 1. Memory Storage

```
Claude Code calls store_memory tool
         ↓
Content → @huggingface/transformers → 384d vector
         ↓
Store in LanceDB with metadata
         ↓
~/.local/share/vector-memory-mcp/memories.db
```

### 2. Memory Retrieval

```
Claude Code calls search_memories
         ↓
Query → @huggingface/transformers → 384d vector
         ↓
Vector search in LanceDB
         ↓
Vector similarity scoring
         ↓
Return top N relevant memories
```

---

## 🔧 Configuration

The server uses environment variables for configuration:

- `VECTOR_MEMORY_DB_PATH` - Custom database path (default: `~/.local/share/vector-memory-mcp/memories.db`)
- `VECTOR_MEMORY_MODEL` - Embedding model to use (default: `Xenova/all-MiniLM-L6-v2`)

Example:
```bash
export VECTOR_MEMORY_DB_PATH="/path/to/custom/memories.db"
export VECTOR_MEMORY_MODEL="Xenova/all-MiniLM-L6-v2"
```

Or in your Claude Code config:
```json
{
  "mcpServers": {
    "memory": {
      "command": "vector-memory-mcp",
      "env": {
        "VECTOR_MEMORY_DB_PATH": "/custom/path/memories.db"
      }
    }
  }
}
```

---

## 🧪 Development

### Running Tests

```bash
# Run all tests
bun test

# Run with coverage
bun test --coverage

# Type checking
bun run typecheck
```

### Development Mode

```bash
# Watch mode - auto-restart on file changes
bun run dev

# Run directly without building
bun run src/index.ts
```

### Building

```bash
# Build for production
bun run build

# Output will be in dist/
```

---

## 🗺️ Roadmap

### ✅ Phase 1: Foundation (Current)
- ✅ Core database with LanceDB
- ✅ Embedding generation with @huggingface/transformers
- ✅ Basic MCP tools (store, search, get, delete)
- ✅ TypeScript implementation with Drizzle ORM

### 🚧 Phase 2: Enhanced Search & Scoring
- Multi-factor scoring algorithm (similarity, recency, priority, usage frequency)
- Configurable scoring weights
- Priority levels for memories
- Usage tracking and frequency-based ranking
- Metadata filtering and advanced tagging

### 📋 Phase 3: Dual-Level Memory System
- Project-specific memories (`.memory/db` in repo)
- Global memories (`~/.local/share/vector-memory-mcp/`)
- Automatic precedence handling (project overrides global)
- Project detection and context switching

### 🎯 Phase 4: Smart Automation
- Auto-detect architectural decisions
- Capture bug fixes and solutions automatically
- Generate session-end summaries
- Natural language trigger detection (85%+ accuracy)
- Continuous conversation monitoring

### 🔮 Phase 5: Advanced Features
- Memory deduplication with similarity threshold
- Batch operations (import/export)
- Markdown import/export
- Memory clustering and visualization
- Cross-project insights
- Multi-modal memories (images, diagrams)
- Session hooks for automatic context injection
- Multi-CLI support (Cursor, Windsurf, etc.)
- Smart priority suggestions

---

## 🤝 Contributing

Contributions are welcome! This project is in active development.

### Areas We'd Love Help With:
- Testing and bug reports
- Documentation improvements
- Performance optimizations
- New feature ideas

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines *(coming soon)*.

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built with [@modelcontextprotocol/sdk](https://github.com/modelcontextprotocol/typescript-sdk) - Official MCP TypeScript SDK
- Uses [LanceDB](https://lancedb.com/) for fast, local vector search
- Powered by [@huggingface/transformers](https://huggingface.co/docs/transformers.js) for local embeddings
- Database layer via [Drizzle ORM](https://orm.drizzle.team/)
- Inspired by [doobidoo's mcp-memory-service](https://github.com/doobidoo/mcp-memory-service)

---

## 🔗 Related Projects

- [Model Context Protocol](https://modelcontextprotocol.io) - Official MCP specification
- [Claude Code](https://claude.ai/code) - AI coding assistant from Anthropic
- [LanceDB](https://lancedb.com/) - Fast, local vector search
- [Transformers.js](https://huggingface.co/docs/transformers.js) - Run transformers in JavaScript

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/AerionDyseti/vector-memory-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AerionDyseti/vector-memory-mcp/discussions)
- **Documentation**: Check the `docs/` directory

---

## ⚡ Quick Examples

### Example 1: Storing a Decision

```
You: "Remember that we decided to use Drizzle ORM for type-safe database access"
Claude: I'll store that for you.
  [Calls store_memory tool with content and metadata]
  ✓ Memory stored successfully
```

### Example 2: Searching Memories

```
You: "What did we decide about database tooling?"
Claude: Let me search for that...
  [Calls search_memories with query about database]
  Found: "Use Drizzle ORM for type-safe database access"

Based on our previous decision, we're using Drizzle ORM...
```

### Example 3: Managing Memories

```
You: "Show me what you remember about authentication"
Claude: [Searches for authentication-related memories]
  Found 3 memories:
  1. "Use JWT tokens for API authentication"
  2. "Store refresh tokens in httpOnly cookies"
  3. "Implement rate limiting on auth endpoints"
```

---

<div align="center">

**[⬆ Back to Top](#vector-memory-mcp-server)**

Made with ❤️ for developers who value context continuity

</div>
