# Kioku (記憶) - AI Context Memory for Developers

**Version 2.0** | Persistent, self-enriching context management for AI coding assistants

**Kioku** (記憶, Japanese for "memory") is an MCP (Model Context Protocol) server that provides intelligent context management for AI coding assistants like Claude and Zed, helping them remember your project across sessions.

## What Problem Does This Solve?

- 🧠 **AI assistants forget** your project between sessions
- ⏱️ **You waste 10-15 minutes** every session re-explaining your architecture  
- 💾 **Context windows saturate** with irrelevant information
- 📚 **No learning accumulation** across coding sessions

**Kioku's Promise:** Zero manual context management while your AI gets progressively smarter about your project.

---

## ✨ What's New in v2.0

### 🚀 **Guided Onboarding**
- Interactive setup wizard with API key validation
- Auto-configuration for Claude Desktop and Zed
- One command to get started: `kioku setup`

### 🏥 **Health Diagnostics**
- System health checks with `kioku doctor`
- Auto-repair for common issues
- Performance diagnostics and warnings

### 📊 **Visual Dashboard**
- Real-time project overview at `localhost:3456`
- Session timeline and module graph
- Embeddings and context window stats

### ⚡ **Advanced Context Intelligence**
- Git integration (log, blame, diff)
- Refined discovery extraction with AI
- Multi-project workspace support
- Smart chunking with AST analysis

---

## 📦 Monorepo Structure

Kioku is organized as a monorepo with 4 packages:

```
packages/
├── shared/      # Shared utilities, types, error classes
├── api/         # Core business logic (MCP server, domain, application, infrastructure)
├── cli/         # Command-line interface (commands, logger)
└── ui/          # Dashboard web interface (React + Vite)
```

**Build Commands:**
```bash
bun run build          # Build all packages (shared → api → cli → ui)
bun run build:api      # Build API package only
bun run build:cli      # Build CLI package only
bun run build:ui       # Build UI package only
```

**Quality Gates:**
```bash
bun run quality-gate   # Type check + lint + tests
bun run type-check     # TypeScript strict mode
bun run lint           # ESLint with architecture boundaries
bun test:api           # Run API tests (338 passing)
```

**Documentation:**
- 📚 **[Monorepo Usage Guide](./docs/monorepo-usage.md)** - Daily development workflow
- 🏗️ **[Architecture](./docs/architecture.md)** - Package dependencies and principles
- 🔄 **[Rollback Guide](./docs/rollback-guide.md)** - Safety and rollback procedures

---

## Quick Start

### 1. Install & Setup (2 minutes)

```bash
# Clone and build
git clone https://github.com/yourusername/kioku.git
cd kioku
bun install
bun run build

# Interactive setup wizard
kioku setup
```

The setup wizard will:
- ✅ Validate your API keys (OpenAI/Anthropic)
- ✅ Configure your editor (Claude Desktop or Zed)
- ✅ Initialize your project
- ✅ Create MCP configuration automatically

### 2. Start Using Kioku

```bash
# Check system health
kioku doctor

# View dashboard
kioku dashboard

# Show current context
kioku show
```

### 3. Your AI Now Has Superpowers! 🦸

Open your project in Claude Desktop or Zed. Your AI assistant automatically has access to:

**MCP Resources:**
- `context://project` - Project context (architecture, tech stack, patterns)
- `context://modules` - Module documentation
- `context://session_history` - Recent coding session summaries

**MCP Tools:**
- `context_search` - Semantic search across project knowledge
- `read_file` - File access with automatic tracking
- `grep_codebase` - Pattern search with context awareness
- `git_log`, `git_blame`, `git_diff` - Git history analysis

---

## 📚 CLI Commands

### Core Commands

```bash
# 🚀 Setup & Initialization
kioku setup                    # Interactive setup wizard (recommended!)
kioku init                     # Initialize current project

# 🔌 Server
kioku serve                    # Start MCP server (auto-started by editor)

# 📊 Information
kioku show                     # Display context overview
kioku status                   # Show system health & statistics

# 🏥 Diagnostics
kioku doctor                   # Run health checks
kioku doctor --repair          # Auto-fix detected issues
kioku doctor --verbose         # Detailed diagnostics
kioku doctor --export report.json  # Export diagnostics report

# 📈 Dashboard
kioku dashboard                # Start visual dashboard (localhost:3456)
kioku dashboard --no-browser   # Start without opening browser
kioku dashboard --port 8080    # Use custom port

# 🧹 Maintenance
kioku cleanup-sessions         # Clean up orphaned sessions
kioku cleanup-sessions --dry-run    # Preview cleanup
kioku cleanup-sessions --force      # Skip confirmation
```

### Setup Options

```bash
# Non-interactive setup
kioku setup -y \
  --project-type web-app \
  --openai-key sk-xxx \
  --anthropic-key sk-ant-xxx \
  --editor claude
```

### Doctor Options

```bash
kioku doctor --repair          # Auto-repair issues
kioku doctor --dry-run         # Preview repairs without applying
kioku doctor --quick           # Fast health check (skip expensive checks)
kioku doctor --check database  # Check specific component
```

---

## 🎯 Key Features

### Context Management
- 🧠 **Automatic project scanning** - Detects tech stack, architecture, modules
- 📝 **Self-enriching context** - Learns from every coding session
- 🔍 **Semantic search** - Vector embeddings with ChromaDB
- 🎯 **Smart pruning** - Keeps context window optimal (80% threshold)
- 📊 **Usage tracking** - Monitors file access and discovery patterns

### Developer Experience
- ⚡ **Zero-config setup** - Interactive wizard handles everything
- 🏥 **Self-healing** - Auto-repair with `kioku doctor --repair`
- 📈 **Visual dashboard** - Real-time project insights
- 🎨 **Beautiful CLI** - Icons, colors, progress indicators
- 📚 **Comprehensive help** - In-tool documentation

### AI Integration
- 🔌 **MCP Protocol** - Works with Claude Desktop, Zed, and more
- 🛠️ **Rich tooling** - Search, read, grep, git analysis
- 📖 **Resource exposure** - Project, modules, session history
- 🔄 **Background services** - Scoring, pruning, enrichment
- 💡 **Progressive learning** - AI gets smarter each session

### Technical Excellence
- ✅ **90%+ test coverage** - Comprehensive test suite
- 🏗️ **Onion architecture** - Clean separation of concerns
- 🔐 **Type-safe** - TypeScript strict mode everywhere
- 📦 **Dependency injection** - Testable and maintainable
- 🚀 **Fast runtime** - Built on Bun

---

## 🛠️ Tech Stack

### Core
- **Runtime:** Bun (fast JavaScript runtime)
- **Language:** TypeScript (strict mode)
- **Architecture:** Onion Architecture + Functional Programming

### Storage
- **Relational:** SQLite (sessions, discoveries, chunks)
- **Vector:** ChromaDB (semantic embeddings)
- **Config:** YAML (project context)

### AI & APIs
- **Embeddings:** OpenAI text-embedding-3-small
- **Discovery Refinement:** Anthropic Claude (optional)
- **Protocol:** Model Context Protocol (MCP)

### Frontend (Dashboard)
- **Framework:** React 18 + Vite
- **Styling:** Tailwind CSS
- **State:** TanStack Query (React Query)
- **Server:** Fastify + CORS

### DevOps
- **Testing:** Vitest
- **Linting:** ESLint (with architecture boundaries)
- **Type Checking:** TypeScript Compiler
- **Package Manager:** Bun
- **Git Integration:** Custom git client

---

## How It Works

### Session 1
1. You initialize Kioku: `kioku init`
2. AI scans your project structure
3. Basic context available (file tree, tech stack)

### Session 2+
1. After each session, Kioku extracts discoveries:
   - Architecture patterns you discussed
   - Coding conventions you established  
   - Gotchas and workarounds you found
   - Business rules you explained

2. These discoveries enrich `.context/project.yaml`

3. Next session, AI automatically knows:
   - Your project's architecture
   - Your team's conventions
   - Past decisions and context
   - Module-specific patterns

### Result
**By session 10:** Your AI assistant answers questions like a senior team member who's been on the project for months.

**Your manual context setup time:** 0 minutes

---

## Architecture

Kioku follows **Onion Architecture** with **Functional Programming** principles:

```
Infrastructure (🔴)  ← I/O, MCP Server, Storage
    ↓
Application (🟡)     ← Use Cases, Orchestration  
    ↓
Domain (🟢)          ← Pure Business Logic
```

**Key Principles:**
- ✅ Domain = 100% pure functions (no I/O)
- ✅ Dependencies point inward only
- ✅ Immutable data structures
- ✅ Comprehensive test coverage (90%+)

See [CLAUDE.md](./CLAUDE.md) for full development guide.

---

## CLI Commands

### `init`
Initialize context for current project
```bash
kioku init
```

### `serve`
Start MCP server (used by editors automatically)
```bash
kioku serve
```

### `show`
Display current project context
```bash
kioku show
```

### `status`
Show Kioku system health and diagnostics
```bash
kioku status
```

---

## Development

### Running Tests
```bash
bun test                  # Run all tests
bun test --watch          # Watch mode
bun test --coverage       # With coverage report
```

### Quality Gates
```bash
bun run quality-gate      # Type check + lint + tests
bun run type-check        # TypeScript strict mode
bun run lint              # ESLint (includes architecture boundaries)
bun run lint:fix          # Auto-fix issues
```

### Build
```bash
bun run build             # Compile TypeScript to dist/
```

---

## Project Structure

```
kioku/
├── src/
│   ├── domain/              # 🟢 Pure business logic
│   │   ├── models/          # Data structures
│   │   ├── calculations/    # Pure functions
│   │   └── rules/           # Business rules
│   │
│   ├── application/         # 🟡 Application logic
│   │   ├── use-cases/       # Feature workflows
│   │   ├── services/        # Application services
│   │   └── ports/           # Interfaces
│   │
│   └── infrastructure/      # 🔴 External world
│       ├── mcp/             # MCP server
│       ├── storage/         # Database, file I/O
│       ├── cli/             # Commands
│       └── external/        # OpenAI, Anthropic APIs
│
├── tests/
│   ├── unit/                # Unit tests (90%+ coverage)
│   └── integration/         # Integration tests
│
├── .specify/                # Spec-Driven Development
│   ├── memory/
│   │   └── constitution.md  # Project principles
│   └── specs/
│       └── 001-kioku-mvp/
│           ├── spec.md      # Feature requirements
│           ├── plan.md      # Technical design
│           └── tasks.md     # Implementation tasks
│
├── SETUP.md                 # Configuration guide
└── CLAUDE.md                # AI development guide
```

---

## Tech Stack

**Runtime:** Bun  
**Language:** TypeScript (strict mode)  
**MCP SDK:** @modelcontextprotocol/sdk  
**Storage:** SQLite + YAML + ChromaDB (local)  
**Embeddings:** OpenAI (text-embedding-3-small)  
**Testing:** Vitest  
**Linting:** ESLint (with architecture boundary enforcement)

---

## Requirements

- **Bun** v1.1.29+ (runtime)
- **OpenAI API Key** (for embeddings)
- **Anthropic API Key** (optional, for future AI extraction)
- **Supported Editors:**
  - Zed Editor
  - Claude Code (CLI)

---

## MVP Scope

**In Scope:**
- ✅ TypeScript/JavaScript projects
- ✅ Rules-based discovery extraction
- ✅ OpenAI embeddings
- ✅ Local SQLite + ChromaDB
- ✅ Single user, local development

**Out of Scope (Post-MVP):**
- ❌ Multi-language support (Python, Go, Rust)
- ❌ AI-based extraction (GPT-4 refinement)
- ❌ Git integration (git_log, git_blame)
- ❌ Real-time file watching
- ❌ Web dashboard UI
- ❌ Team/collaboration features

---

## Documentation

- **[docs/setup-guide.md](./docs/setup-guide.md)** - Configuration guide for Zed/Claude Code
- **[CLAUDE.md](./CLAUDE.md)** - AI development guide (principles, architecture, TDD)
- **[docs/project-overview.md](./docs/project-overview.md)** - Project overview and architecture
- **[docs/changelog.md](./docs/changelog.md)** - Version history and changes
- **[.specify/memory/constitution.md](./.specify/memory/constitution.md)** - Project principles
- **[.specify/specs/001-context-tool-mvp/spec.md](./.specify/specs/001-context-tool-mvp/spec.md)** - Feature specification (legacy path)

---

## Testing Your Setup

### 1. Manual Server Test
```bash
cd ~/your-project-with-context
bun /path/to/kioku/dist/infrastructure/cli/index.js serve
```

You should see: `Server running on stdio`

### 2. View Context
```bash
cd ~/your-project-with-context
bun /path/to/kioku/dist/infrastructure/cli/index.js show
```

### 3. AI Integration
In your editor, ask your AI:
```
What resources are available from the Kioku MCP server?
```

---

## Contributing

This project follows **Spec-Driven Development**:

1. Read `.specify/memory/constitution.md` (principles)
2. Review `.specify/specs/001-context-tool-mvp/spec.md` (requirements)
3. Follow **Test-Driven Development** (tests before code)
4. Maintain **90%+ test coverage**
5. Respect **Onion Architecture** boundaries (enforced by ESLint)

See [CLAUDE.md](./CLAUDE.md) for full development workflow.

---

## License

MIT (or your preferred license)

---

## Support

**Issues:** https://github.com/sanzoku-labs/kioku/issues  
**Documentation:** See `.specify/specs/001-context-tool-mvp/` and project README

---

**Built with ❤️ using Bun, TypeScript, and MCP**

**Let your AI remember. Focus on building. 🚀**
