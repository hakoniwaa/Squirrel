# MCP Resources Contract

**Date**: 2025-01-15  
**Purpose**: Define all MCP resources exposed by Context Tool server  
**Protocol**: Model Context Protocol (MCP)  
**Status**: Complete

---

## Overview

MCP resources provide read-only access to project context via URI-based addressing. Resources are automatically available to Claude Desktop when the MCP server is running.

**Resource URI Pattern:** `context://{category}/{identifier}`

---

## Resource Definitions

### 1. Project Overview

**URI:** `context://project/overview`

**Description:** High-level project information including tech stack, architecture, and module summary.

**MIME Type:** `text/markdown`

**Content Structure:**
```markdown
# Project: {project.name}

**Type:** {project.type}  
**Path:** {project.path}

## Tech Stack

- **Stack:** {tech.stack.join(', ')}
- **Runtime:** {tech.runtime}
- **Package Manager:** {tech.packageManager}

## Architecture

**Pattern:** {architecture.pattern}  
**Description:** {architecture.description}

## Modules ({module count})

{For each module:}
### {module.name}
{module.description}

**Key Files:**
{module.keyFiles.map(f => `- ${f.path} (${f.role})`)}

**Patterns:** {module.patterns.length}  
**Business Rules:** {module.businessRules.length}  
**Common Issues:** {module.commonIssues.length}
```

**Example Response:**
```json
{
  "contents": [
    {
      "uri": "context://project/overview",
      "mimeType": "text/markdown",
      "text": "# Project: My SaaS App\n\n**Type:** fullstack..."
    }
  ]
}
```

**Use Cases:**
- Initial project understanding
- Quick reference for stack and architecture
- Module discovery

**Access Frequency:** Medium (once per session typically)

---

### 2. Module Detail

**URI:** `context://module/{moduleName}`

**Description:** Detailed information about a specific module including patterns, rules, issues, and dependencies.

**MIME Type:** `text/markdown`

**URI Parameters:**
- `moduleName` (string, required): Module identifier (e.g., "auth", "users", "payments")

**Content Structure:**
```markdown
# Module: {module.name}

{module.description}

## Key Files

{For each file:}
### {file.path}
**Role:** {file.role}  
{file.description}

## Patterns ({count})

{For each pattern:}
- {pattern}

## Business Rules ({count})

{For each rule:}
- {rule}

## Common Issues ({count})

{For each issue:}
### {issue.description}
**Solution:** {issue.solution}  
**Discovered:** {issue.discoveredAt} (Session: {issue.sessionId})

## Dependencies

{module.dependencies.join(', ') or 'None'}
```

**Example Request:**
```json
{
  "method": "resources/read",
  "params": {
    "uri": "context://module/auth"
  }
}
```

**Example Response:**
```json
{
  "contents": [
    {
      "uri": "context://module/auth",
      "mimeType": "text/markdown",
      "text": "# Module: auth\n\nAuthentication and authorization...\n\n## Patterns (2)\n\n- Use JWT tokens in httpOnly cookies\n- Implement token refresh with mutex locks..."
    }
  ]
}
```

**Error Cases:**
```json
{
  "error": {
    "code": -32602,
    "message": "Module not found: invalidModule"
  }
}
```

**Use Cases:**
- Deep dive into specific module
- Understanding module patterns and conventions
- Finding solutions to known issues
- Checking module dependencies

**Access Frequency:** High (multiple times per session)

---

### 3. Current Session

**URI:** `context://session/current`

**Description:** Active session information including files accessed, topics, and activity summary.

**MIME Type:** `text/markdown`

**Content Structure:**
```markdown
# Active Session

**Started:** {session.startedAt}  
**Duration:** {duration in human-readable format}  
**Status:** {session.status}

## Files Accessed ({count})

{For each file (top 10 by access count):}
### {file.path}
**Access Count:** {file.accessCount}  
**Last Accessed:** {file.lastAccessedAt}

## Topics ({count})

{For each topic:}
- {topic}

## Activity Summary

- **Tool Calls:** {metadata.toolCallsCount}
- **Discoveries:** {metadata.discoveryCount}
```

**Example Response:**
```json
{
  "contents": [
    {
      "uri": "context://session/current",
      "mimeType": "text/markdown",
      "text": "# Active Session\n\n**Started:** 2025-01-15T10:00:00Z\n**Duration:** 2 hours 15 minutes..."
    }
  ]
}
```

**Error Cases:**
```json
{
  "error": {
    "code": -32602,
    "message": "No active session"
  }
}
```

**Use Cases:**
- Check what's been worked on in current session
- See which files have been accessed most
- Track session duration and activity
- Understand session context

**Access Frequency:** Low (mainly for debugging/inspection)

---

### 4. Session History

**URI:** `context://sessions/recent?limit={n}`

**Description:** List of recent sessions with summary information.

**MIME Type:** `text/markdown`

**URI Parameters:**
- `limit` (number, optional, default: 10): Number of recent sessions to return

**Content Structure:**
```markdown
# Recent Sessions ({count})

{For each session:}
## Session {session.id.slice(0, 8)}
**Started:** {session.startedAt}  
**Duration:** {duration}  
**Status:** {session.status}  
**Files:** {session.filesAccessed.length}  
**Topics:** {session.topics.join(', ')}  
**Discoveries:** {session.metadata.discoveryCount}
```

**Example Request:**
```json
{
  "method": "resources/read",
  "params": {
    "uri": "context://sessions/recent?limit=5"
  }
}
```

**Example Response:**
```json
{
  "contents": [
    {
      "uri": "context://sessions/recent?limit=5",
      "mimeType": "text/markdown",
      "text": "# Recent Sessions (5)\n\n## Session abc12345\n**Started:** 2025-01-15T10:00:00Z..."
    }
  ]
}
```

**Use Cases:**
- Review past work
- Find when specific work was done
- Track progress over time
- Context for resuming work

**Access Frequency:** Low (mainly for review)

---

## Resource Registration

### ListResources Handler

```typescript
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: 'context://project/overview',
        name: 'Project Overview',
        mimeType: 'text/markdown',
        description: 'High-level project information, tech stack, and architecture',
      },
      {
        uri: 'context://module/{name}',
        name: 'Module Detail',
        mimeType: 'text/markdown',
        description: 'Detailed module information including patterns, rules, and issues',
      },
      {
        uri: 'context://session/current',
        name: 'Current Session',
        mimeType: 'text/markdown',
        description: 'Active session information and activity',
      },
      {
        uri: 'context://sessions/recent',
        name: 'Recent Sessions',
        mimeType: 'text/markdown',
        description: 'List of recent coding sessions',
      },
    ],
  };
});
```

### ReadResource Handler

```typescript
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  const uri = new URL(request.params.uri);
  
  // Route to appropriate handler
  if (uri.pathname === '/project/overview') {
    return await handleProjectOverview();
  }
  
  if (uri.pathname.startsWith('/module/')) {
    const moduleName = uri.pathname.split('/')[2];
    return await handleModuleDetail(moduleName);
  }
  
  if (uri.pathname === '/session/current') {
    return await handleCurrentSession();
  }
  
  if (uri.pathname === '/sessions/recent') {
    const limit = parseInt(uri.searchParams.get('limit') || '10');
    return await handleRecentSessions(limit);
  }
  
  throw new McpError(
    ErrorCode.InvalidRequest,
    `Unknown resource: ${request.params.uri}`
  );
});
```

---

## Error Handling

### Error Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| -32602 | Invalid params | Module not found, invalid limit, etc. |
| -32603 | Internal error | Database error, file read error |
| -32600 | Invalid request | Malformed URI, unsupported resource |

### Error Response Format

```json
{
  "error": {
    "code": -32602,
    "message": "Human-readable error message",
    "data": {
      "resource": "context://module/invalid",
      "reason": "Module 'invalid' not found in project.yaml"
    }
  }
}
```

### Error Handling Pattern

```typescript
try {
  const module = await loadModule(moduleName);
  if (!module) {
    throw new McpError(
      ErrorCode.InvalidParams,
      `Module not found: ${moduleName}`
    );
  }
  return formatModuleResource(module);
} catch (error) {
  logger.error('Resource read failed', { uri: request.params.uri, error });
  
  if (error instanceof McpError) {
    throw error;
  }
  
  throw new McpError(
    ErrorCode.InternalError,
    'Failed to read resource',
    { originalError: error.message }
  );
}
```

---

## Performance Considerations

### Caching Strategy

**In-Memory Cache:**
- `project.yaml` cached on server start
- TTL: Until file modification detected
- Invalidate: On context enrichment

**No Caching:**
- Current session (real-time data)
- Recent sessions (queries database)

### Response Size Limits

| Resource | Typical Size | Max Size |
|----------|--------------|----------|
| Project Overview | 2-5 KB | 50 KB |
| Module Detail | 1-3 KB | 20 KB |
| Current Session | 1-2 KB | 10 KB |
| Recent Sessions | 5-10 KB | 50 KB |

**Total Response Limit:** 100 KB (enforced by MCP protocol)

---

## Access Patterns

### Typical Session Flow

1. **Session Start:**
   - Claude reads `context://project/overview`
   - Claude reads `context://module/{relevant}` based on query

2. **During Work:**
   - Tools called (search, read_file, grep)
   - Resources accessed as needed for context

3. **Session Review:**
   - User checks `context://session/current`
   - Optionally reviews `context://sessions/recent`

### Resource Dependencies

```
context://project/overview
    ↓ (user/AI discovers modules)
context://module/{name}
    ↓ (deep dive into specific module)
context://session/current
    ↓ (track current work)
context://sessions/recent
    ↓ (historical context)
```

---

## Testing Requirements

### Resource Tests

**Unit Tests:**
- Format functions (markdown generation)
- URI parsing
- Error handling

**Integration Tests:**
- Full MCP request/response cycle
- Resource caching behavior
- Error propagation

### Test Cases

```typescript
describe('MCP Resources', () => {
  test('project overview returns valid markdown', async () => {
    const response = await readResource('context://project/overview');
    expect(response.contents[0].mimeType).toBe('text/markdown');
    expect(response.contents[0].text).toContain('# Project:');
  });
  
  test('module detail with invalid name returns error', async () => {
    await expect(
      readResource('context://module/invalid')
    ).rejects.toThrow('Module not found');
  });
  
  test('current session when no session active returns error', async () => {
    await expect(
      readResource('context://session/current')
    ).rejects.toThrow('No active session');
  });
});
```

---

## Future Enhancements (Post-MVP)

**Out of Scope:**
- Dynamic resource templates (e.g., `context://file/{path}`)
- Writeable resources (MCP resources are read-only)
- Binary resources (images, diagrams)
- Paginated resources
- Filtered resources (e.g., `context://discoveries?type=pattern`)
- Real-time resource updates (push notifications)

---

**END OF MCP RESOURCES CONTRACT**
