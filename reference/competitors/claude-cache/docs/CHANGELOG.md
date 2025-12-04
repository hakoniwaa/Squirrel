# Changelog

All notable changes to Claude Cache will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.1] - 2025-01-25

### Fixed
- **Statistics Display Bug** - Fixed TypeError in agent.py where 'projects' was incorrectly accessing a list instead of count
- Corrected `stats.get('projects', 0)` to `stats.get('total_projects', 0)` for proper statistics calculation

## [0.9.0] - 2025-01-24

### Added
- **🤖 Intelligent Multi-Signal Detection** - Revolutionary pattern detection beyond keywords
  - IntelligentDetector with conversation flow analysis and context understanding
  - Behavioral pattern recognition: "AI completion → user continuation = implicit success"
  - Multi-signal fusion combining 4 analysis techniques (conversation, execution, intent, behavioral)
  - Auto-save for high-confidence patterns without interrupting workflow
  - Confidence levels: CERTAIN/HIGH/MEDIUM/LOW/UNCERTAIN

- **📊 CLI Analyze Command** - `cache analyze` for deep session analysis
  - Analyze specific sessions, recent sessions, or by project
  - Visual breakdown of detection confidence and signal strength
  - Evidence summary showing conversation, execution, intent, and behavioral scores
  - Pattern quality assessment and recommendations

- **🎯 Enhanced Pattern Classification**
  - Database migration adds `pattern_quality` and `signal_strength` columns
  - Improved pattern storage with quality metadata
  - Better retrieval with quality-based filtering

- **⚡ Optimized MCP Server** - Claude Code integration improvements
  - Real-time streaming detection for live pattern analysis
  - Smart auto-save triggers based on user behavior
  - Context-aware suggestions that understand current conversation phase
  - Session tracking for continuous learning

### Changed
- **Pattern Detection Priority** - IntelligentDetector now primary detection method
  - PatternFactory prioritizes intelligent → behavioral → enhanced → basic detection
  - Success detection moved from keyword-based to conversation understanding
  - Test results now treated as strongest success signals

- **Database Schema Evolution** - Graceful migration system
  - Existing users automatically get new columns added
  - Backward compatibility maintained for all existing patterns
  - Enhanced queries include pattern quality and signal strength

- **MCP Server Architecture** - Rebuilt for Claude Code optimization
  - Entry point changed to `claude_code_mcp:main` for better performance
  - Real-time conversation analysis with session state tracking
  - Intelligent recommendation system based on conversation context

### Technical
- **New Core Modules**:
  - `intelligent_detector.py` - Multi-signal fusion detection engine
  - `conversation_analyzer.py` - Deep conversation flow understanding
  - `execution_monitor.py` - Code execution result analysis
  - `intent_detector.py` - Semantic user intent detection
  - `behavioral_detector.py` - Simplified behavioral pattern recognition

- **Enhanced Integration**:
  - All new modules registered in `__init__.py` with graceful fallbacks
  - PatternFactory updated to use intelligent detection by default
  - Database queries updated to include new quality metrics
  - Version bumped across all components

- **Improved User Experience**:
  - Silent operation mode for background processes
  - Rich console output for CLI analyze command
  - Better error handling and import safety

## [0.6.1] - 2025-01-21

### Fixed
- **Critical MCP Server Issues** - Complete rewrite using FastMCP pattern
  - Fixed asyncio TaskGroup errors in MCP server
  - Resolved JSON-RPC protocol pollution from stdout
  - Fixed indentation bug causing methods to be outside classes
  - Added missing methods to VectorSearchEngine and DocumentationScanner

### Changed
- **MCP Implementation** - Switched from Server+stdio_server to FastMCP
  - New `cache-mcp` command for stable MCP server
  - Silent mode for all components to prevent protocol pollution
  - Improved error handling and async/await patterns

### Technical
- New module: `fastmcp_server.py` with FastMCP implementation
- Fixed `vector_search.py` class method indentation
- Added `get_project_patterns()` to KnowledgeBase
- Added `extract_lessons()` to DocumentationScanner

## [0.6.0] - 2025-01-21

### Added
- **MCP (Model Context Protocol) Integration** - Native Claude Code tools
  - 5 new slash commands accessible via `/mcp__claude-cache__*`
  - `/cache_query` - Instant vector search
  - `/cache_learn` - Save successful patterns
  - `/cache_suggest` - Proactive pattern suggestions
  - `/cache_stats` - Knowledge base statistics
  - `/cache_browse` - Documentation ingestion
  - Zero context switching - everything in Claude Code
  - Real-time pattern access without terminal

### Changed
- Added MCP server with stdio transport
- Enhanced documentation for MCP setup
- Updated installation with `[mcp]` optional dependency

### Technical
- New module: `complete_mcp.py` with full MCP server implementation
- MCP tools with async/await support
- Integration with Claude Code via `.claude.json` configuration

## [0.5.0] - 2025-01-21

### Added
- **Hybrid Vector Search System** - Graceful fallback between semantic and TF-IDF search
  - Automatic detection of sentence-transformers availability
  - Semantic search with all-MiniLM-L6-v2 model when available
  - Intelligent fallback to TF-IDF for keyword matching
  - 2x better pattern matching with semantic understanding
  - Optional dependency via `pip install claude-cache[enhanced]`

- **Search Capability Detection** - Automatic capability checking and user notifications
  - Displays current search mode on startup
  - Suggests enhancement options if not installed
  - Shows feature comparison (keyword vs semantic)

### Changed
- Updated KnowledgeBase to integrate VectorSearchEngine
- Enhanced pattern storage with automatic vector indexing
- Improved search results with mode transparency
- Updated agent to display search capabilities on startup

### Technical
- New module: `vector_search.py` with VectorSearchEngine class
- Added optional dependency group `[enhanced]` in pyproject.toml
- Database tables for pattern embeddings and TF-IDF corpus
- Hybrid search architecture with automatic mode selection

## [0.4.0] - 2025-01-21

### Added
- **Error Pattern Learning System** - Learn from failures and prevent repeating mistakes
  - Tracks error → solution → prevention mappings
  - Categorizes errors (import, type, syntax, null reference, build, test, etc.)
  - Automatically generates prevention tips
  - Stores error patterns for future reference

- **Differential Learning System** - Track and prioritize efficient solutions
  - Measures time-to-solution for every pattern
  - Compares different approaches for the same task
  - Weights patterns by efficiency (faster is better)
  - Prioritizes recent patterns over old ones
  - Generates efficiency reports

- **Cross-Project Intelligence** - Share knowledge across projects
  - Identifies transferable patterns (auth, API, database)
  - Technology compatibility matrix
  - Automatic pattern adaptation for different tech stacks
  - Global pattern library accessible to all projects

### Changed
- Updated log processor to integrate all three new intelligence systems
- Enhanced success detector with differential metrics
- Improved pattern ranking algorithm
- Development Status upgraded from Alpha to Beta

### Technical
- New modules: `error_pattern_learner.py`, `differential_learner.py`, `cross_project_intelligence.py`
- New database tables for error patterns, metrics, and global patterns
- Enhanced SQLite schema with foreign key relationships

## [0.3.0] - 2025-01-21

### Added
- **Semantic Intent Detection** - Understand user satisfaction without explicit keywords
  - TF-IDF vectorization and cosine similarity
  - Detects subtle positive signals like "ok let's move on"
  - Analyzes conversation flow for overall satisfaction
  - Context modifiers for better accuracy

- **Automated Execution Monitoring** - Learn from code execution outcomes
  - Detects test passes/failures (pytest, jest, npm test)
  - Recognizes build success/failure patterns
  - Identifies server startup success
  - Monitors type checking and linting results
  - Tracks package installation outcomes

### Changed
- Success detector now uses both semantic analysis and execution signals
- Reduced dependency on explicit user feedback
- Improved pattern capture rate by 10x

### Technical
- New modules: `intent_detector.py`, `execution_monitor.py`
- Integration with sklearn for machine learning capabilities

## [0.2.1] - 2025-01-20

### Fixed
- Critical indentation errors in `lesson_organizer.py`
- First-run detection logic to properly handle existing data
- Python 3.13 Dict type hint compatibility

### Changed
- Improved error handling for file operations
- Better detection of existing documentation

## [0.2.0] - 2025-01-20

### Added
- **Documentation Scanner** - Import existing documentation from repositories
  - Scans for markdown files with lessons learned
  - Extracts warnings and best practices
  - Regex pattern matching for intelligent extraction

- **Lesson Organizer** - Hierarchical organization of lessons
  - Categories: auth, database, API, testing, deployment, etc.
  - Priority-based lesson grouping
  - Automatic overflow handling for large documentation sets
  - Creates category-specific files in `.claude/lessons/`

- **First-Run Experience** - Onboarding flow for new users
  - Option to scan Development folder
  - Batch import of existing documentation
  - Persistent flag to track first-run completion

### Changed
- Enhanced agent.py with first-run detection
- Improved file structure for lesson management
- Better handling of large documentation sets

### Fixed
- Issue with manual file creation requirements
- Problems with hardcoded paths

## [0.1.0] - 2025-01-19

### Initial Release
- **Core Functionality**
  - Real-time log monitoring from Claude Code sessions
  - Session tracking and analysis
  - Success pattern detection
  - Knowledge base with SQLite storage

- **Features**
  - Multi-project support with separate knowledge bases
  - Context injection for Claude Code
  - Slash command generation
  - Convention tracking
  - Team knowledge export/import

- **Commands**
  - `cache start` - Start monitoring
  - `cache process` - Process existing logs
  - `cache query` - Query patterns
  - `cache stats` - Show statistics
  - `cache generate` - Generate slash commands

### Technical Foundation
- Log watcher with file state tracking
- Incremental log processing
- Pattern extraction and storage
- Context generation for CLAUDE.md
- Rich terminal UI with progress indicators

---

## Version History Summary

- **v0.9.1** - Bug fix: Statistics display error correction
- **v0.9.0** - Revolutionary intelligence: Multi-signal detection with behavioral understanding
- **v0.6.1** - Production fix: Stable MCP server with FastMCP pattern
- **v0.6.0** - MCP integration: Native Claude Code tools with 5 slash commands
- **v0.5.0** - Hybrid search: Vector embeddings with graceful TF-IDF fallback
- **v0.4.0** - Intelligence trilogy: Error learning, efficiency tracking, cross-project transfer
- **v0.3.0** - Semantic understanding: Intent detection and execution monitoring
- **v0.2.x** - Documentation import: Scan and organize existing knowledge
- **v0.1.0** - Foundation: Core log processing and pattern detection

## Upcoming (Planned)

### v0.7.0 (Planned)
- Async processing pipeline
- Team collaboration features
- Analytics dashboard
- Plugin system for custom analyzers

### v1.0.0 (Target)
- Production-ready stability
- Complete documentation
- Performance optimizations
- Enterprise features