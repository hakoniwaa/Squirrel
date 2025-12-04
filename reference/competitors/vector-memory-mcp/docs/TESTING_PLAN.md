# Testing & Development Flow Plan

## Overview

This document outlines the comprehensive testing strategy and development workflow for the vector-memory-mcp project, including test repository structure, isolation strategies, and dogfooding approaches.

---

## Part 1: Language & Technology Stack

### Final Decision: TypeScript ✅

**Rationale:**
- **Language:** TypeScript 5.0+ for type safety and modern ecosystem
- **Runtime:** Bun for fast startup and great DX
- **Vector Database:** LanceDB for fast, local vector search without heavy dependencies
- **Embeddings:** @huggingface/transformers (local, no Python dependency)
- **SDK:** Official @modelcontextprotocol/sdk

**Technology Stack:**
```
- MCP Framework: @modelcontextprotocol/sdk
- Database: LanceDB
- Embeddings: @huggingface/transformers (Xenova/all-MiniLM-L6-v2, 384d)
- Testing: bun test
- Transport: stdio (Claude Code requirement)
```

---

## Part 2: Dogfooding Strategy

### The Challenge

When developing an MCP memory server, we want to dogfood it (use it while building it), but:
- Development changes can corrupt production memories
- Test data pollutes real memories
- Debugging requires isolated test databases
- Crashes could lose important data

### Selected Approach: Environment Variables

**Implementation:**

#### Claude Code Configuration
```json
// ~/.claude/config.json
{
  "mcpServers": {
    "memory": {
      "command": "bunx",
      "args": ["vector-memory-mcp"],
      "env": {
        "VECTOR_MEMORY_DB_PATH": "/home/user/.local/share/vector-memory-mcp/memories.db"
      }
    }
  }
}
```

#### Development Mode
Use a separate environment variable for development:

```bash
export VECTOR_MEMORY_DB_PATH="/home/user/.local/share/vector-memory-mcp/dev.db"
bun run src/index.ts
```

---

## Part 3: Test Repository Structure

### Hybrid Tiered Approach

Start simple and grow complexity as features mature.

#### Phase 1: Simple Structure

```
vector-memory-mcp/
├── tests/
│   ├── memory.test.ts          # Unit tests for MemoryService
│   ├── embeddings.test.ts      # Unit tests for EmbeddingsService
│   ├── server.test.ts          # Integration tests for MCP Server
│   └── store.test.ts           # Integration tests for LanceDB storage
```

---

## Part 4: Testing Strategy

### Test Hierarchy

#### Level 1: Unit Tests

**Purpose:** Test individual components in isolation

**Characteristics:**
- Mock dependencies where possible
- Fast execution
- Verify logic (scoring, validation)

#### Level 2: Integration Tests

**Purpose:** Test component interactions with real dependencies

**Characteristics:**
- Real embeddings (small model or subset)
- Real LanceDB (temporary directory)
- Test actual storage and retrieval

**Example:**
```typescript
// tests/store.test.ts
import { describe, expect, test } from "bun:test";
// ... setup ...

test("stores and searches memory", async () => {
  await service.store("test content");
  const results = await service.search("test");
  expect(results.length).toBeGreaterThan(0);
});
```

#### Level 3: E2E Tests

**Purpose:** Test complete system with MCP protocol

**Characteristics:**
- Full client-server interaction simulation
- Verify MCP tool calls works as expected

---

## Part 5: Development Workflow

### Daily Development Flow

#### Morning Setup
```bash
# 1. Install dependencies
bun install

# 2. Run tests
bun test
```

#### Development Loop
```bash
# 1. Write failing test first (TDD)
# Edit: tests/new-feature.test.ts

# 2. Run specific test
bun test tests/new-feature.test.ts

# 3. Implement feature

# 4. Re-run test until passing

# 5. Run all tests
bun test
```

#### Watch Mode
```bash
bun run dev
```

---

## Part 6: Testing Tools & Configuration

### Required Packages

```json
// package.json
{
  "devDependencies": {
    "@types/bun": "latest",
    "typescript": "^5.0.0"
  }
}
```

### Running Tests

```bash
# All tests
bun test

# Specific file
bun test tests/memory.test.ts

# Watch mode
bun test --watch

# With coverage
bun test --coverage
```

---

## Part 7: Performance Testing

### Benchmarks

Use simple scripts to measure latency:

```typescript
const start = performance.now();
await service.search("query");
const end = performance.now();
console.log(`Search took ${end - start}ms`);
```

**Success Metrics:**
- Search latency < 100ms for 1000 memories
- Storage < 10MB for 1000 memories

---

## Summary

### Key Decisions

1. **Language:** TypeScript + Bun
2. **Database:** LanceDB
3. **Testing:** Bun built-in test runner

### Quick Reference Commands

```bash
bun install       # Install dependencies
bun test          # Run tests
bun run dev       # Run in watch mode
bun run build     # Build for production
```

---

*Last Updated: 2025-11-27*
*Version: 2.0 (Refactored for LanceDB)*