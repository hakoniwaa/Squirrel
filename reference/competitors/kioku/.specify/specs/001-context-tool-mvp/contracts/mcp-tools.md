# MCP Tools Contract

**Date**: 2025-01-15  
**Purpose**: Define all MCP tools exposed by Context Tool server  
**Protocol**: Model Context Protocol (MCP)  
**Status**: Complete

---

## Overview

MCP tools provide callable functions that AI assistants can invoke to interact with project context. Unlike resources (read-only), tools perform actions and can have side effects (e.g., tracking file access).

**Tool Invocation:** Tools are called automatically by AI when needed, with parameters validated via Zod schemas.

---

## Tool Definitions

### 1. Context Search

**Name:** `context_search`

**Description:** Search project context semantically using RAG (Retrieval-Augmented Generation) with embeddings. Returns relevant discoveries, sessions, and code snippets ranked by similarity.

**Input Schema:**
```typescript
const ContextSearchSchema = z.object({
  query: z.string()
    .min(3)
    .max(500)
    .describe('Search query describing what to find'),
  
  type: z.enum(['all', 'pattern', 'rule', 'decision', 'issue'])
    .optional()
    .default('all')
    .describe('Filter by discovery type'),
  
  module: z.string()
    .optional()
    .describe('Filter by module name'),
  
  limit: z.number()
    .int()
    .min(1)
    .max(20)
    .default(5)
    .describe('Maximum number of results to return'),
});
```

**Output Format:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{JSON stringified SearchResult[]}"
    }
  ]
}

// SearchResult structure
{
  "results": [
    {
      "id": "discovery-uuid",
      "type": "pattern",
      "content": "Use JWT tokens in httpOnly cookies",
      "module": "auth",
      "session": "session-uuid",
      "date": "2025-01-15T10:00:00Z",
      "score": 0.92,
      "source": "discovery"
    }
  ],
  "query": "JWT authentication",
  "totalFound": 5,
  "searchTime": 120
}
```

**Examples:**

```typescript
// Example 1: General search
{
  "query": "how does authentication work",
  "type": "all",
  "limit": 5
}

// Returns:
{
  "results": [
    {
      "content": "Use JWT tokens stored in httpOnly cookies for auth",
      "type": "pattern",
      "module": "auth",
      "score": 0.95
    },
    {
      "content": "Implement token refresh with mutex locks to prevent race conditions",
      "type": "pattern",
      "module": "auth",
      "score": 0.88
    }
  ]
}

// Example 2: Filtered search
{
  "query": "token refresh issue",
  "type": "issue",
  "module": "auth",
  "limit": 3
}

// Returns:
{
  "results": [
    {
      "content": "Token refresh race condition fixed with mutex lock",
      "type": "issue",
      "module": "auth",
      "score": 0.96
    }
  ]
}
```

**Error Cases:**
```json
// Query too short
{
  "content": [
    {
      "type": "text",
      "text": "{\"error\": \"Query must be at least 3 characters\"}"
    }
  ],
  "isError": true
}

// No embeddings available
{
  "content": [
    {
      "type": "text",
      "text": "{\"error\": \"No embeddings found. Run initial session to generate context.\", \"fallback\": \"Use grep_codebase for text search\"}"
    }
  ],
  "isError": true
}

// OpenAI API error
{
  "content": [
    {
      "type": "text",
      "text": "{\"error\": \"Failed to generate query embedding\", \"details\": \"API rate limit exceeded\"}"
    }
  ],
  "isError": true
}
```

**Side Effects:**
- Generates query embedding (OpenAI API call)
- Logs search query and results count
- No state changes

**Performance:**
- Target: <2 seconds for search
- Embeddings cached (no regeneration)
- Metadata pre-filtering before vector search

**Use Cases:**
- "How did we handle authentication?"
- "Find issues related to token refresh"
- "What patterns do we use for API calls?"
- "Show me decisions about database choice"

---

### 2. Read File

**Name:** `read_file`

**Description:** Read file content with optional dependency tree loading. Tracks file access for context scoring.

**Input Schema:**
```typescript
const ReadFileSchema = z.object({
  path: z.string()
    .min(1)
    .describe('File path relative to project root'),
  
  includeDeps: z.boolean()
    .optional()
    .default(false)
    .describe('Include level 1 dependencies (imports)'),
  
  maxDepth: z.number()
    .int()
    .min(0)
    .max(1)
    .default(1)
    .describe('Dependency tree depth (MVP: max 1)'),
});
```

**Output Format:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{JSON stringified ReadFileResult}"
    }
  ]
}

// ReadFileResult structure
{
  "file": {
    "path": "src/server/auth/AuthService.ts",
    "content": "... file content ...",
    "size": 2048,
    "lines": 75,
    "language": "typescript"
  },
  "dependencies": [
    {
      "path": "src/server/auth/TokenManager.ts",
      "type": "import",
      "level": 1
    },
    {
      "path": "src/server/users/UserRepository.ts",
      "type": "import",
      "level": 1
    }
  ],
  "metadata": {
    "module": "auth",
    "role": "core",
    "lastModified": "2025-01-15T09:00:00Z"
  }
}
```

**Examples:**

```typescript
// Example 1: Simple file read
{
  "path": "src/server/auth/AuthService.ts",
  "includeDeps": false
}

// Returns file content only

// Example 2: With dependencies
{
  "path": "src/server/auth/AuthService.ts",
  "includeDeps": true,
  "maxDepth": 1
}

// Returns file content + level 1 imports with their content
```

**Error Cases:**
```json
// File not found
{
  "content": [
    {
      "type": "text",
      "text": "{\"error\": \"File not found\", \"path\": \"invalid/path.ts\"}"
    }
  ],
  "isError": true
}

// Parse error
{
  "content": [
    {
      "type": "text",
      "text": "{\"error\": \"Failed to parse imports\", \"path\": \"file.ts\", \"details\": \"Syntax error at line 15\"}"
    }
  ],
  "isError": true
}

// Permission denied
{
  "content": [
    {
      "type": "text",
      "text": "{\"error\": \"Permission denied\", \"path\": \".env\"}"
    }
  ],
  "isError": true
}
```

**Side Effects:**
- Tracks file access in context items table
- Updates access count and last accessed timestamp
- Triggers context scorer (async)

**Performance:**
- File read: <100ms
- With deps: <500ms (depends on file count)
- AST parsing cached

**Security:**
- Never read: `.env`, `.git/*`, `node_modules/*`
- Path traversal protection (reject `../`)
- File size limit: 1MB per file

**Use Cases:**
- "Show me the AuthService implementation"
- "Read UserRepository with its dependencies"
- "What's in the config file?"

---

### 3. Grep Codebase

**Name:** `grep_codebase`

**Description:** Fast text search across codebase using regex patterns. Fallback when semantic search not available or for exact matches.

**Input Schema:**
```typescript
const GrepCodebaseSchema = z.object({
  pattern: z.string()
    .min(1)
    .max(200)
    .describe('Regex pattern to search for'),
  
  filePattern: z.string()
    .optional()
    .describe('Glob pattern to filter files (e.g., "**/*.ts")'),
  
  caseSensitive: z.boolean()
    .optional()
    .default(false)
    .describe('Case-sensitive search'),
  
  limit: z.number()
    .int()
    .min(1)
    .max(100)
    .default(50)
    .describe('Maximum number of matches to return'),
});
```

**Output Format:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "{JSON stringified GrepResult[]}"
    }
  ]
}

// GrepResult structure
{
  "matches": [
    {
      "file": "src/server/auth/AuthService.ts",
      "line": 42,
      "column": 10,
      "text": "  const token = jwt.sign(payload, SECRET);",
      "context": {
        "before": ["  // Generate JWT token", "  function generateToken(payload) {"],
        "after": ["    return token;", "  }"]
      }
    }
  ],
  "pattern": "jwt\\.sign",
  "totalMatches": 3,
  "filesSearched": 127,
  "searchTime": 45
}
```

**Examples:**

```typescript
// Example 1: Simple text search
{
  "pattern": "jwt.sign",
  "caseSensitive": false
}

// Example 2: TypeScript files only
{
  "pattern": "interface.*Context",
  "filePattern": "**/*.ts",
  "limit": 20
}

// Example 3: Case-sensitive function search
{
  "pattern": "function handleAuth",
  "caseSensitive": true,
  "filePattern": "src/server/**/*.ts"
}
```

**Error Cases:**
```json
// Invalid regex
{
  "content": [
    {
      "type": "text",
      "text": "{\"error\": \"Invalid regex pattern\", \"pattern\": \"[invalid(\"}"
    }
  ],
  "isError": true
}

// No matches
{
  "content": [
    {
      "type": "text",
      "text": "{\"matches\": [], \"totalMatches\": 0, \"message\": \"No matches found for pattern 'nonexistent'\"}"
    }
  ]
}
```

**Side Effects:**
- Logs search pattern and results count
- No state changes

**Performance:**
- Target: <1 second for typical project
- Uses ripgrep (fast Rust implementation)
- Respects .gitignore

**Excluded Paths:**
- `node_modules/`, `.git/`, `dist/`, `build/`, `.next/`, `.context/`

**Use Cases:**
- "Find all uses of jwt.sign"
- "Search for 'TODO' comments"
- "Find interface definitions"
- "Locate function calls"

---

## Tool Registration

### ListTools Handler

```typescript
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'context_search',
        description: 'Search project context semantically using RAG. Returns relevant discoveries, patterns, rules, and past decisions.',
        inputSchema: zodToJsonSchema(ContextSearchSchema),
      },
      {
        name: 'read_file',
        description: 'Read file content with optional dependency tree. Tracks access for context scoring.',
        inputSchema: zodToJsonSchema(ReadFileSchema),
      },
      {
        name: 'grep_codebase',
        description: 'Fast text search across codebase using regex. Good for exact matches and when semantic search unavailable.',
        inputSchema: zodToJsonSchema(GrepCodebaseSchema),
      },
    ],
  };
});
```

### CallTool Handler

```typescript
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    switch (name) {
      case 'context_search': {
        const params = ContextSearchSchema.parse(args);
        const results = await executeContextSearch(params);
        return {
          content: [{ type: 'text', text: JSON.stringify(results, null, 2) }],
        };
      }
      
      case 'read_file': {
        const params = ReadFileSchema.parse(args);
        const results = await executeReadFile(params);
        return {
          content: [{ type: 'text', text: JSON.stringify(results, null, 2) }],
        };
      }
      
      case 'grep_codebase': {
        const params = GrepCodebaseSchema.parse(args);
        const results = await executeGrep(params);
        return {
          content: [{ type: 'text', text: JSON.stringify(results, null, 2) }],
        };
      }
      
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    logger.error('Tool execution failed', { name, error });
    
    // Return error in result (not protocol error)
    return {
      content: [{
        type: 'text',
        text: JSON.stringify({
          error: error.message,
          tool: name,
        }),
      }],
      isError: true,
    };
  }
});
```

---

## Error Handling Strategy

### Validation Errors

```typescript
try {
  const params = ContextSearchSchema.parse(args);
} catch (error) {
  return {
    content: [{
      type: 'text',
      text: JSON.stringify({
        error: 'Invalid parameters',
        details: error.errors,
      }),
    }],
    isError: true,
  };
}
```

### Runtime Errors

```typescript
try {
  const results = await executeContextSearch(params);
  return { content: [{ type: 'text', text: JSON.stringify(results) }] };
} catch (error) {
  logger.error('Context search failed', { error });
  
  return {
    content: [{
      type: 'text',
      text: JSON.stringify({
        error: 'Search failed',
        message: error.message,
        fallback: 'Try using grep_codebase for text search',
      }),
    }],
    isError: true,
  };
}
```

### Graceful Degradation

```typescript
// If embeddings unavailable, suggest alternative
if (!hasEmbeddings) {
  return {
    content: [{
      type: 'text',
      text: JSON.stringify({
        error: 'No embeddings available',
        suggestion: 'Use grep_codebase for text search',
        action: 'Embeddings will be generated in background',
      }),
    }],
    isError: true,
  };
}
```

---

## Performance Targets

| Tool | Target Time | Max Time | Notes |
|------|-------------|----------|-------|
| context_search | <2s | 5s | Includes embedding generation |
| read_file | <100ms | 500ms | Without deps |
| read_file (deps) | <500ms | 2s | With level 1 deps |
| grep_codebase | <1s | 3s | For 500-file project |

**Monitoring:**
- Log execution time for all tool calls
- Alert if > max time
- Track success/failure rates

---

## Access Control & Security

### Path Validation

```typescript
function validateFilePath(path: string): void {
  // Reject absolute paths
  if (path.startsWith('/')) {
    throw new Error('Absolute paths not allowed');
  }
  
  // Reject path traversal
  if (path.includes('../')) {
    throw new Error('Path traversal not allowed');
  }
  
  // Reject sensitive files
  const blocked = ['.env', '.env.local', '.git', 'node_modules'];
  if (blocked.some(b => path.includes(b))) {
    throw new Error('Access to sensitive paths denied');
  }
}
```

### Rate Limiting

```typescript
// Per-tool rate limits (requests per minute)
const RATE_LIMITS = {
  context_search: 30,   // Expensive (OpenAI API)
  read_file: 100,       // Moderate
  grep_codebase: 60,    // Moderate
};

// Track in-memory (simple implementation)
const requestCounts = new Map<string, number>();

function checkRateLimit(toolName: string): void {
  const count = requestCounts.get(toolName) || 0;
  if (count >= RATE_LIMITS[toolName]) {
    throw new Error(`Rate limit exceeded for ${toolName}`);
  }
  requestCounts.set(toolName, count + 1);
}

// Reset every minute
setInterval(() => requestCounts.clear(), 60 * 1000);
```

---

## Testing Requirements

### Tool Tests

**Unit Tests:**
- Parameter validation (Zod schemas)
- Error handling
- Result formatting

**Integration Tests:**
- Full MCP tool call cycle
- Database interactions
- API calls (mocked)

### Test Cases

```typescript
describe('MCP Tools', () => {
  describe('context_search', () => {
    test('returns relevant results', async () => {
      const result = await callTool('context_search', {
        query: 'JWT authentication',
        limit: 5,
      });
      expect(result.content[0].text).toContain('results');
    });
    
    test('rejects query < 3 chars', async () => {
      const result = await callTool('context_search', { query: 'ab' });
      expect(result.isError).toBe(true);
    });
  });
  
  describe('read_file', () => {
    test('reads file content', async () => {
      const result = await callTool('read_file', {
        path: 'src/index.ts',
      });
      const data = JSON.parse(result.content[0].text);
      expect(data.file.content).toBeDefined();
    });
    
    test('rejects path traversal', async () => {
      const result = await callTool('read_file', { path: '../../../etc/passwd' });
      expect(result.isError).toBe(true);
    });
  });
  
  describe('grep_codebase', () => {
    test('finds matches', async () => {
      const result = await callTool('grep_codebase', {
        pattern: 'function',
        limit: 10,
      });
      const data = JSON.parse(result.content[0].text);
      expect(data.matches.length).toBeGreaterThan(0);
    });
    
    test('handles no matches gracefully', async () => {
      const result = await callTool('grep_codebase', {
        pattern: 'xyznonexistent123',
      });
      const data = JSON.parse(result.content[0].text);
      expect(data.totalMatches).toBe(0);
    });
  });
});
```

---

## Logging & Observability

### Tool Call Logging

```typescript
logger.info('Tool called', {
  tool: name,
  params: args,
  sessionId: currentSession?.id,
  timestamp: Date.now(),
});

// After execution
logger.info('Tool completed', {
  tool: name,
  success: !error,
  duration: elapsed,
  resultSize: result.content[0].text.length,
});
```

### Metrics to Track

- Tool call counts (by tool name)
- Success/failure rates
- Execution times (p50, p95, p99)
- Error types and frequencies
- Rate limit hits

---

## Future Enhancements (Post-MVP)

**Out of Scope:**
- `write_file` tool (modify files)
- `run_command` tool (execute shell commands)
- `refactor_code` tool (AI-assisted refactoring)
- `generate_test` tool (AI test generation)
- `explain_code` tool (AI code explanation)
- Tool chaining (one tool calling another)
- Streaming responses (large results)
- Parallel tool execution

---

**END OF MCP TOOLS CONTRACT**
