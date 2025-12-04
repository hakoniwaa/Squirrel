# Kioku (記憶)

**Type**: Developer Tool (MCP Server + CLI)
**Status**: Active - MVP Complete, Ready for Dogfooding

## Overview

Kioku (記憶, Japanese for "memory") is an MCP (Model Context Protocol) server that provides persistent, self-enriching context management for AI coding assistants. It eliminates the 10-15 minute context setup developers waste each coding session by automatically learning and remembering project architecture, patterns, and decisions across sessions.

## Role in Sanzoku Labs

- **Category:** Developer Tool / Infrastructure
- **Purpose:**
  - Enable AI coding assistants (Claude, Zed) to maintain persistent project memory across sessions
  - Automatically extract and accumulate architectural knowledge from coding conversations
  - Provide semantic search over project context and past decisions
  - Eliminate manual context re-explanation in every session
- **Related projects:**
  - Can be used with any Sanzoku Labs project that uses AI coding assistants
  - Demonstrates MCP protocol implementation for potential integration into other tools
  - Architecture patterns (Onion + Functional) applicable to other Sanzoku projects

## Current State

- **Implemented:**
  - MCP stdio server with resources and tools (context://, context_search, read_file, grep_codebase)
  - Project initialization and scanning (detects tech stack, modules, architecture)
  - Session tracking with automatic start/end detection
  - Discovery extraction using regex patterns (architecture, conventions, patterns, gotchas)
  - Context enrichment (updates project.yaml with learned knowledge)
  - SQLite storage for sessions, discoveries, chunks, and file access tracking
  - ChromaDB vector database for semantic embeddings
  - OpenAI embeddings generation (text-embedding-3-small)
  - Background services: Context scorer (every 5 min), pruner (at 80% threshold), session auto-save
  - CLI commands: init, serve, show, status, setup, doctor, dashboard, cleanup-sessions
  - Interactive setup wizard with API key validation and editor auto-configuration
  - Health diagnostics with auto-repair capabilities
  - Visual dashboard (React + Vite) at localhost:3456
  - Git integration tools (log, blame, diff)
  - Comprehensive test suite (338 passing tests, 90%+ coverage)
  - Quality gates (type-check, lint with architecture boundaries, tests)
  - Monorepo structure (shared, api, cli, ui packages)

- **In Progress:**
  - Documentation organization and improvement (current branch: 003-documentation-organization-and)
  - Cross-artifact consistency validation
  - Real-world dogfooding on production projects

- **Planned / Future:**
  - Multi-language support (Python, Go, Rust, Java)
  - AI-based discovery refinement (GPT-4 for better extraction)
  - Advanced git analytics and change pattern detection
  - Real-time file watching and context updates
  - Multi-project workspace coordination
  - Team/collaboration features (shared context, conflict resolution)
  - AST-based smart chunking for better code comprehension
  - Re-ranking with boost factors (recent files, frequently accessed)
  - Additional editor integrations (VS Code, IntelliJ)
  - Performance optimizations (caching strategies, incremental updates)

- **On Hold:**
  - None - all MVP features complete and tested

## Tech Stack

- **Language:** TypeScript (strict mode, no implicit any)
- **Framework / Runtime:**
  - Bun (JavaScript runtime - fast, TypeScript-native)
  - Node.js compatible via Bun
- **Architecture:**
  - Onion Architecture (Domain → Application → Infrastructure)
  - Functional Programming principles (pure functions, immutability, copy-on-write)
- **Storage:**
  - SQLite (relational data - sessions, discoveries, chunks)
  - ChromaDB (vector embeddings for semantic search)
  - YAML (human-editable project context)
- **AI & APIs:**
  - @modelcontextprotocol/sdk (MCP protocol implementation)
  - OpenAI API (text-embedding-3-small for embeddings)
  - Anthropic API (optional, for future AI-based extraction)
- **Frontend (Dashboard):**
  - React 18 + Vite
  - Tailwind CSS
  - TanStack Query (React Query)
  - Fastify (API server with CORS)
- **Tooling:**
  - Vitest (testing with 90%+ coverage requirement)
  - ESLint (with custom architecture boundary enforcement)
  - TypeScript Compiler (strict mode type checking)
  - Bun package manager
  - Git integration (custom git client implementation)

## Folder Structure

Monorepo organized as 4 packages:

```
kioku/
├── packages/
│   ├── shared/              # Shared utilities, types, error classes
│   │   ├── errors/          # Custom error classes
│   │   ├── types/           # Shared TypeScript types
│   │   └── utils/           # Pure utility functions
│   │
│   ├── api/                 # Core business logic (MCP server)
│   │   ├── src/
│   │   │   ├── domain/      # 🟢 Pure business logic (no I/O)
│   │   │   │   ├── models/          # Data structures, types
│   │   │   │   ├── calculations/    # Pure functions (scoring, metrics)
│   │   │   │   └── rules/           # Business rules (discovery patterns)
│   │   │   │
│   │   │   ├── application/         # 🟡 Application logic (orchestration)
│   │   │   │   ├── use-cases/       # Feature workflows
│   │   │   │   ├── services/        # Application services
│   │   │   │   └── ports/           # Interfaces for adapters
│   │   │   │
│   │   │   └── infrastructure/      # 🔴 External world (I/O)
│   │   │       ├── storage/         # SQLite, ChromaDB, YAML handlers
│   │   │       ├── mcp/             # MCP server implementation
│   │   │       ├── background/      # Background services (scorer, pruner)
│   │   │       └── external/        # OpenAI, Anthropic API clients
│   │   │
│   │   └── tests/
│   │       ├── unit/                # Unit tests (mirror src/ structure)
│   │       └── integration/         # Integration tests
│   │
│   ├── cli/                 # Command-line interface
│   │   ├── src/
│   │   │   └── commands/    # CLI commands (init, serve, show, status, etc.)
│   │   └── tests/
│   │
│   └── ui/                  # Visual dashboard (React)
│       ├── src/
│       │   ├── components/  # React components
│       │   ├── hooks/       # Custom React hooks
│       │   └── api/         # API client for backend
│       └── public/
│
├── .specify/                # Spec-Driven Development artifacts
│   ├── memory/
│   │   └── constitution.md  # Project principles (CRITICAL - read first!)
│   └── specs/
│       └── 001-context-tool-mvp/
│           ├── spec.md      # Feature requirements
│           ├── plan.md      # Technical implementation plan
│           └── tasks.md     # Task breakdown with dependencies
│
├── docs/                    # Documentation
│   ├── monorepo-usage.md    # Daily development workflow
│   ├── architecture.md      # Package dependencies and principles
│   ├── rollback-guide.md    # Safety and rollback procedures
│   └── session-management.md # Session lifecycle documentation
│
├── CLAUDE.md                # AI development guide (principles, TDD, architecture)
├── README.md                # User-facing documentation
└── DESCRIPTION.md           # This file (Sanzoku Labs project description)
```

**Key Characteristics:**

- **Onion Architecture:** Dependencies flow inward (Infrastructure → Application → Domain)
- **100% Pure Domain Layer:** No I/O, easily testable, framework-agnostic
- **Dependency Injection:** Infrastructure adapters injected into application layer
- **ESLint Enforcement:** Architecture boundaries validated automatically
- **Test Coverage:** 90%+ required, enforced by quality gates
- **Monorepo Benefits:** Shared code reuse, coordinated releases, single source of truth

