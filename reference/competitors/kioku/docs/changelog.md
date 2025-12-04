# Changelog

All notable changes to Kioku will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-11

### 🎉 Major Release - Advanced Context Intelligence

Version 2.0 represents a complete evolution of Kioku with enhanced AI capabilities, improved developer experience, and production-ready features.

### ✨ Added

#### 🚀 Phase 11: Guided Onboarding
- **Interactive setup wizard** (`kioku setup`) - Complete onboarding in 2 minutes
- **API key validation** - Real-time validation for OpenAI and Anthropic keys
- **Auto-configuration** - Automatic MCP config generation for Claude Desktop and Zed
- **Non-interactive mode** - Scriptable setup with CLI flags (`--skip-prompts`, `-y`)
- **Smart detection** - Detects existing setup and offers reconfiguration
- **Environment management** - Automatic `.env` file creation with `.gitignore` integration
- **Beautiful UX** - Progress indicators, success messages, and helpful next steps

#### 🏥 Phase 12: Advanced Diagnostics
- **Health check system** (`kioku doctor`) - Comprehensive system diagnostics
- **Component checks** - Database, vector DB, file system, disk space, API keys
- **Auto-repair functionality** (`--repair`) - One-click fix for common issues
- **Dry-run mode** (`--dry-run`) - Preview repairs before applying
- **Verbose diagnostics** (`--verbose`) - Detailed system information
- **Export reports** (`--export`) - JSON diagnostics for debugging
- **Quick checks** (`--quick`) - Fast health verification
- **Component-specific** (`--check <component>`) - Target individual components
- **Performance diagnostics** - Query performance, embeddings speed, context usage
- **Exit codes** - Proper status codes for CI/CD integration

#### 📊 Phase 10: Visual Context Dashboard
- **Real-time dashboard** (`kioku dashboard`) - Web UI at `localhost:3456`
- **Project overview** - Stats, tech stack, module/file counts
- **Session timeline** - Expandable session history with files and discoveries
- **Module graph** - Visual dependency graph with activity indicators
- **Embeddings stats** - Queue status, error tracking, disk usage
- **Context window usage** - Real-time capacity monitoring
- **Auto-refresh** - 5-second polling for live updates
- **CORS support** - Secure cross-origin requests
- **Custom ports** - Configurable API and dashboard ports

#### ⚡ Advanced Context Intelligence (Phase 2-9)
- **Git integration** - `git_log`, `git_blame`, `git_diff` MCP tools
- **Smart chunking** - AST-based code splitting with Babel parser
- **AI discovery refinement** - Optional Claude-powered discovery enhancement
- **Multi-project support** - Workspace-level context management
- **Embeddings generation** - Batch processing with OpenAI embeddings
- **Ranking system** - Multi-factor search result ranking with boost factors
- **File watching** - Real-time project change detection
- **Background services** - Context scorer, pruner, embeddings generator
- **Metrics collection** - Prometheus-compatible metrics server

### 🔧 Changed

#### Architecture & Code Quality
- **Onion Architecture** - Complete restructuring with domain/application/infrastructure layers
- **Functional programming** - Pure functions in domain layer, immutable data structures
- **TypeScript strict mode** - Full type safety with `exactOptionalPropertyTypes`
- **ESLint architecture rules** - Automated boundary enforcement
- **Test coverage 90%+** - Comprehensive unit and integration tests
- **Dependency injection** - Ports and adapters pattern throughout

#### Developer Experience
- **CLI commands expanded** - From 4 to 7 commands (added setup, doctor, dashboard)
- **Help system improved** - Detailed examples and option documentation
- **Error messages enhanced** - Actionable recommendations for all errors
- **Logging system** - Structured logging with Winston, proper log levels
- **Performance optimized** - Faster startup, efficient database queries

#### Storage & Data
- **Database migrations** - Versioned schema with migration system (v2)
- **Chunk storage refactored** - Improved performance and reliability
- **Vector database** - ChromaDB integration for semantic search
- **YAML validation** - Schema validation for project.yaml
- **Session tracking** - Enhanced session metadata and statistics

### 🐛 Fixed
- **Context window calculation** - Accurate token counting
- **Database connection pooling** - Prevent connection leaks
- **File watcher stability** - Handle rapid file changes gracefully
- **MCP server lifecycle** - Proper startup/shutdown handling
- **API endpoint errors** - Graceful error handling for missing data
- **Dashboard CORS issues** - Proper cross-origin configuration
- **TypeScript compilation** - All strict mode compliance issues resolved
- **Test flakiness** - Eliminated race conditions in integration tests

### 🔒 Security
- **API key masking** - Keys never logged or displayed in full
- **Environment file protection** - Automatic `.gitignore` entry
- **Input validation** - All user inputs validated and sanitized
- **Path traversal prevention** - Safe file access only within project
- **Dependency audit** - Regular security checks with `bun audit`

### 📚 Documentation
- **README updated** - Complete v2.0 feature documentation
- **SETUP_GUIDE.md created** - Comprehensive local development guide
- **CLAUDE.md enhanced** - Full development guide with architecture patterns
- **API documentation** - JSDoc comments for all public APIs
- **CLI help expanded** - Detailed command documentation with examples

### ⚠️ Breaking Changes

#### Configuration
- **MCP server path changed** - Now requires `kioku setup` or manual reconfiguration
- **Database schema v2** - Automatic migration from v1, but backup recommended
- **Environment variables** - Must set `OPENAI_API_KEY` (required) and `ANTHROPIC_API_KEY` (optional)

#### CLI
- **`kioku init` behavior** - Now requires project type (auto-detected or prompted)
- **Server command** - `kioku serve` now requires API keys to be configured

#### Storage
- **`.context` directory structure** - New files: `project.yaml` schema changed, `chroma/` for vector DB
- **Session database** - `sessions.db` has new tables and columns (auto-migrated)

### 🔄 Migration from v1.0

1. **Backup your data:**
   ```bash
   cp -r .context .context.backup
   ```

2. **Run setup wizard:**
   ```bash
   kioku setup
   ```

3. **Reconfigure editor:**
   - The wizard handles this automatically
   - Or manually update your MCP config with new paths

4. **Verify health:**
   ```bash
   kioku doctor --verbose
   ```

### 📊 Statistics

- **Commits:** 50+ commits across 12 phases
- **Files changed:** 150+ files
- **Lines of code:** 15,000+ lines (excluding tests)
- **Test coverage:** 90%+ across all layers
- **Tests:** 200+ unit tests, 50+ integration tests
- **Commands:** 7 CLI commands (up from 4)
- **MCP resources:** 3 resource types
- **MCP tools:** 6 tools (up from 3)

### 🙏 Acknowledgments

- **MCP Protocol** - Anthropic's Model Context Protocol
- **Bun Runtime** - Fast JavaScript runtime
- **ChromaDB** - Vector database for embeddings
- **OpenAI** - Embedding models
- **Contributors** - All community contributors

---

## [1.0.0] - 2024-12-XX

### 🎉 Initial Release - MVP

First production release of Kioku with core context management features.

### ✨ Added

#### Core Features
- **Project initialization** (`kioku init`) - Scan and initialize project context
- **MCP server** (`kioku serve`) - Serve context to AI editors
- **Context display** (`kioku show`) - View current project context
- **System status** (`kioku status`) - Check system health

#### Context Management
- **Project scanning** - Automatic tech stack detection
- **Module detection** - Identify project architecture and modules
- **Context storage** - YAML-based context in `.context/project.yaml`
- **Session tracking** - Track AI assistant interactions
- **Discovery extraction** - Rules-based pattern extraction from conversations

#### MCP Integration
- **Resources** - `context://project`, `context://modules`, `context://session_history`
- **Tools** - `context_search`, `read_file`, `grep_codebase`
- **Protocol compliance** - Full MCP stdio protocol implementation

#### Storage
- **SQLite database** - Session and discovery storage
- **YAML configuration** - Human-readable project context
- **File tracking** - Monitor file access patterns

### 📚 Documentation
- README.md - Basic setup and usage
- SETUP.md - Editor configuration guide
- CLAUDE.md - AI development guide

### 🏗️ Architecture
- TypeScript with Bun runtime
- Basic layered architecture
- Functional programming principles
- Test-driven development

---

## Versioning Strategy

**MAJOR.MINOR.PATCH**

- **MAJOR** - Breaking changes, major architectural changes
- **MINOR** - New features, non-breaking changes
- **PATCH** - Bug fixes, documentation updates

## Links

- [Repository](https://github.com/sanzoku-labs/kioku)
- [Documentation](https://github.com/sanzoku-labs/kioku/wiki)
- [Issues](https://github.com/sanzoku-labs/kioku/issues)
- [Releases](https://github.com/sanzoku-labs/kioku/releases)

---

**Note:** This changelog follows [Keep a Changelog](https://keepachangelog.com/) format.
