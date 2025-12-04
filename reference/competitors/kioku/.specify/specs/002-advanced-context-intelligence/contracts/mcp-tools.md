# MCP Tools API Contract

**Feature**: Kioku v2.0 - Advanced Context Intelligence  
**Protocol**: Model Context Protocol (MCP)  
**Transport**: stdio

---

## New Tools (v2.0)

### 1. git_log

**Description**: Query git commit history with filters.

**Input Schema**:
```typescript
{
  name: "git_log",
  description: "Get git commit history for files or the repository",
  inputSchema: {
    type: "object",
    properties: {
      filePath: {
        type: "string",
        description: "Optional file path to filter commits (relative to project root)"
      },
      since: {
        type: "string",
        description: "Show commits after this date/tag (e.g., '2025-01-01', '30 days ago', 'v1.0.0')"
      },
      until: {
        type: "string",
        description: "Show commits before this date/tag"
      },
      author: {
        type: "string",
        description: "Filter by author name or email"
      },
      maxCount: {
        type: "number",
        description: "Maximum number of commits to return (default: 10, max: 100)"
      }
    }
  }
}
```

**Output Format**:
```markdown
# Git Log

## Commit: abc1234 (2025-10-09)
**Author**: John Doe <john@example.com>  
**Message**: feat(auth): add JWT authentication

**Files Changed** (3):
- src/auth/jwt.ts (added)
- src/auth/middleware.ts (modified)
- tests/auth.test.ts (added)

---

## Commit: def5678 (2025-10-08)
...
```

**Error Handling**:
- Not a git repository → Return clear message: "This project is not a git repository"
- Invalid SHA/tag → "Invalid commit reference: {ref}"
- Permission denied → "Cannot access git repository"

---

### 2. git_blame

**Description**: Show line-by-line authorship for a file.

**Input Schema**:
```typescript
{
  name: "git_blame",
  description: "Show who last modified each line of a file",
  inputSchema: {
    type: "object",
    properties: {
      filePath: {
        type: "string",
        description: "File path relative to project root (required)"
      },
      startLine: {
        type: "number",
        description: "Start line number (optional, 1-indexed)"
      },
      endLine: {
        type: "number",
        description: "End line number (optional, inclusive)"
      }
    },
    required: ["filePath"]
  }
}
```

**Output Format**:
```markdown
# Git Blame: src/auth/jwt.ts

## Lines 15-20

```typescript
15  abc1234 (John Doe    2025-10-09) function verifyToken(token: string) {
16  abc1234 (John Doe    2025-10-09)   const decoded = jwt.verify(token, secret);
17  def5678 (Jane Smith  2025-10-08)   if (!decoded.userId) {
18  def5678 (Jane Smith  2025-10-08)     throw new Error('Invalid token');
19  abc1234 (John Doe    2025-10-09)   }
20  abc1234 (John Doe    2025-10-09)   return decoded;
```

### Commit abc1234
**Author**: John Doe <john@example.com>  
**Date**: 2025-10-09  
**Message**: feat(auth): add JWT verification

### Commit def5678
**Author**: Jane Smith <jane@example.com>  
**Date**: 2025-10-08  
**Message**: fix(auth): add token validation
```

**Error Handling**:
- File not in repository → "File not tracked by git: {filePath}"
- Invalid line range → "Invalid line range: {start}-{end}"
- File has uncommitted changes → Note in output: "⚠ File has local modifications"

---

### 3. git_diff

**Description**: Show changes between commits, branches, or tags.

**Input Schema**:
```typescript
{
  name: "git_diff",
  description: "Compare two git references (commits/branches/tags) or show unstaged changes",
  inputSchema: {
    type: "object",
    properties: {
      ref1: {
        type: "string",
        description: "First reference (commit SHA, branch, tag). Leave empty for working directory."
      },
      ref2: {
        type: "string",
        description: "Second reference. If omitted, compares ref1 to working directory."
      },
      filePath: {
        type: "string",
        description: "Optional file path to show diff for specific file only"
      },
      summary: {
        type: "boolean",
        description: "If true, return summary only (no line-by-line diff). Default: false"
      }
    }
  }
}
```

**Output Format (Full Diff)**:
```markdown
# Git Diff: main...feature-branch

## Summary
- **Files Changed**: 3
- **Insertions**: +45 lines
- **Deletions**: -12 lines

---

## File: src/auth/jwt.ts (modified)
**Changes**: +25 -5

```diff
@@ -10,7 +10,12 @@
 import jwt from 'jsonwebtoken';
 
-function verifyToken(token: string) {
+/**
+ * Verifies a JWT token and returns decoded payload
+ * @throws {Error} If token is invalid or expired
+ */
+function verifyToken(token: string): DecodedToken {
   const decoded = jwt.verify(token, secret);
+  if (!decoded.userId) throw new Error('Invalid token');
   return decoded;
 }
```

---

## File: tests/auth.test.ts (added)
**Changes**: +20 -0

```typescript
describe('verifyToken', () => {
  it('should verify valid token', () => {
    // Test implementation
  });
});
```
```

**Output Format (Summary Only)**:
```markdown
# Git Diff Summary: v1.0.0...v2.0.0

- **Files Changed**: 47
- **Insertions**: +1,234 lines
- **Deletions**: -567 lines

### Modified Files (15):
- src/auth/jwt.ts (+25 -5)
- src/api/routes.ts (+50 -20)
...

### Added Files (20):
- src/monitoring/metrics.ts (+100)
- src/file-watcher/service.ts (+200)
...

### Deleted Files (12):
- src/legacy/old-auth.ts (-150)
...

**Binary Files**: 3 binary files changed (images, fonts)
```

**Error Handling**:
- Invalid reference → "Invalid git reference: {ref}"
- Binary files → Show "Binary file changed" instead of diff
- Large diffs (>1000 lines) → Automatically switch to summary mode with note

---

## Enhanced Tools (v2.0 Updates to v1.0 Tools)

### context_search (Enhanced)

**Changes from v1.0**:
- Returns chunk-level results instead of file-level
- Includes ranking metadata (boosts applied)
- Supports multi-project search

**Input Schema** (extended):
```typescript
{
  name: "context_search",
  description: "Semantic search across project context (function/class level)",
  inputSchema: {
    type: "object",
    properties: {
      query: {
        type: "string",
        description: "Natural language search query"
      },
      limit: {
        type: "number",
        description: "Max results to return (default: 5, max: 20)"
      },
      // NEW v2.0 parameters
      projectScope: {
        type: "string",
        enum: ["current", "all_linked"],
        description: "Search current project only or all linked projects (default: current)"
      },
      chunkType: {
        type: "array",
        items: {
          type: "string",
          enum: ["function", "class", "method", "interface", "type"]
        },
        description: "Filter by chunk types (default: all types)"
      }
    },
    required: ["query"]
  }
}
```

**Output Format** (enhanced):
```markdown
# Search Results for "authentication logic"

## Result 1: authenticateUser (src/auth/middleware.ts:15-45) [Score: 0.92]

**Type**: function  
**Project**: backend  
**Last Accessed**: 2 hours ago (15 times this week)

```typescript
/**
 * Authenticates user by verifying JWT token
 * @throws {UnauthorizedError} If token invalid
 */
async function authenticateUser(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) throw new UnauthorizedError('No token provided');
  
  const decoded = await verifyToken(token);
  req.user = await getUserById(decoded.userId);
  next();
}
```

**Ranking Details**:
- Semantic Score: 0.85
- Recency Boost: ×1.5 (accessed <24h ago)
- Module Boost: ×1.3 (same module as current work)
- Frequency Boost: ×1.2 (15 accesses this week)
- **Final Score**: 0.92

---

## Result 2: validateToken (src/auth/jwt.ts:20-35) [Score: 0.88]
...
```

---

## Tool Error Responses

All tools follow consistent error format:

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: {error_type}\n\nDetails: {error_message}\n\nSuggestion: {how_to_fix}"
    }
  ],
  "isError": true
}
```

**Error Types**:
- `GitRepositoryError`: Not a git repository or git not installed
- `InvalidInputError`: Invalid parameters (SHA, file path, line range)
- `PermissionError`: Cannot read file or access repository
- `NotFoundError`: File, commit, or reference not found
- `ProcessingError`: Unexpected error during execution

---

## Performance Targets

| Tool | p50 Latency | p95 Latency | p99 Latency |
|------|-------------|-------------|-------------|
| git_log | <100ms | <300ms | <500ms |
| git_blame | <150ms | <400ms | <800ms |
| git_diff | <200ms | <500ms | <1000ms |
| context_search | <500ms | <1500ms | <2000ms |

---

## Security Considerations

### Input Validation

**Git Tools**:
- File paths: Must match `^[a-zA-Z0-9._/-]+$` (no shell metacharacters)
- Commit SHAs: Must match `^[a-f0-9]{7,40}$`
- Branch names: Must match `^[a-zA-Z0-9._/-]+$`
- Date strings: Validated against known formats or passed through git parser

### Command Injection Prevention

```typescript
// ❌ NEVER: String interpolation
await execSync(`git log --author=${userInput}`);

// ✅ ALWAYS: Array arguments with validation
if (!/^[a-zA-Z0-9._/-]+$/.test(author)) {
  throw new InvalidInputError('Invalid author format');
}
await git.log({ '--author': author });
```

### Rate Limiting

- Git tools: No rate limiting (local operations)
- context_search: 100 requests/minute per session (prevent abuse)

---

**END OF MCP TOOLS CONTRACT**
