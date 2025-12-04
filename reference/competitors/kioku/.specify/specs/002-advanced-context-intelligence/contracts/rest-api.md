# REST API Contract (Metrics & Dashboard)

**Feature**: Kioku v2.0 - Observability & Dashboard  
**Base URL**: `http://localhost:9090`  
**Protocol**: HTTP/1.1  
**Format**: JSON (except /metrics which is Prometheus text format)

---

## Metrics Endpoint

### GET /metrics

**Purpose**: Prometheus-compatible metrics scraping endpoint.

**Response Format**: Prometheus text exposition format

**Response Headers**:
```
Content-Type: text/plain; version=0.0.4; charset=utf-8
```

**Response Body Example**:
```prometheus
# HELP kioku_embedding_queue_depth Number of files waiting for embedding generation
# TYPE kioku_embedding_queue_depth gauge
kioku_embedding_queue_depth 12

# HELP kioku_api_latency_seconds API call latency in seconds
# TYPE kioku_api_latency_seconds histogram
kioku_api_latency_seconds_bucket{provider="openai",operation="embed",le="0.005"} 10
kioku_api_latency_seconds_bucket{provider="openai",operation="embed",le="0.01"} 25
kioku_api_latency_seconds_bucket{provider="openai",operation="embed",le="0.025"} 45
kioku_api_latency_seconds_bucket{provider="openai",operation="embed",le="0.05"} 80
kioku_api_latency_seconds_bucket{provider="openai",operation="embed",le="0.1"} 95
kioku_api_latency_seconds_bucket{provider="openai",operation="embed",le="+Inf"} 100
kioku_api_latency_seconds_sum{provider="openai",operation="embed"} 2.5
kioku_api_latency_seconds_count{provider="openai",operation="embed"} 100

# HELP kioku_file_watcher_events_total Total number of file system events detected
# TYPE kioku_file_watcher_events_total counter
kioku_file_watcher_events_total{event_type="add"} 45
kioku_file_watcher_events_total{event_type="change"} 230
kioku_file_watcher_events_total{event_type="unlink"} 12

# HELP kioku_errors_total Total number of errors by type
# TYPE kioku_errors_total counter
kioku_errors_total{error_type="embedding_failed"} 3
kioku_errors_total{error_type="api_rate_limit"} 1

# HELP kioku_active_sessions Number of currently active MCP sessions
# TYPE kioku_active_sessions gauge
kioku_active_sessions 1

# HELP kioku_context_window_usage_percent Percentage of context window currently in use (0-100)
# TYPE kioku_context_window_usage_percent gauge
kioku_context_window_usage_percent 67.5
```

**Performance**: <50ms p99 (response cached for 1 second)

**Error Responses**:
```
HTTP 500 Internal Server Error
Content-Type: text/plain

Error collecting metrics
```

---

## Health Check Endpoint

### GET /health

**Purpose**: Service health check for load balancers and monitoring.

**Response Format**: JSON

**Response (Healthy)**:
```json
HTTP 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "checks": {
    "database": true,
    "vectordb": true,
    "file_watcher": true,
    "embedding_service": true
  },
  "uptime_seconds": 3600,
  "timestamp": "2025-10-09T12:00:00.000Z"
}
```

**Response (Degraded)**:
```json
HTTP 429 Too Many Requests
Content-Type: application/json

{
  "status": "degraded",
  "checks": {
    "database": true,
    "vectordb": true,
    "file_watcher": false,       // Non-critical service down
    "embedding_service": true
  },
  "uptime_seconds": 3600,
  "timestamp": "2025-10-09T12:00:00.000Z",
  "message": "File watcher unavailable, core functionality operational"
}
```

**Response (Unhealthy)**:
```json
HTTP 503 Service Unavailable
Content-Type: application/json

{
  "status": "unhealthy",
  "checks": {
    "database": false,             // Critical service down
    "vectordb": true,
    "file_watcher": true,
    "embedding_service": true
  },
  "uptime_seconds": 3600,
  "timestamp": "2025-10-09T12:00:00.000Z",
  "message": "Database unavailable, service cannot operate"
}
```

**Status Code Semantics**:
- `200 OK`: All systems healthy, fully operational
- `429 Too Many Requests`: Degraded (non-critical services down, core functional)
- `503 Service Unavailable`: Unhealthy (critical services down, not operational)

**Performance**: <100ms (includes actual health checks with retries)

---

## Dashboard API Endpoints

### GET /api/project

**Purpose**: Get project overview for dashboard.

**Response**:
```json
HTTP 200 OK
Content-Type: application/json

{
  "name": "my-awesome-app",
  "version": "2.0.0",
  "techStack": ["TypeScript", "React", "Node.js"],
  "statistics": {
    "totalFiles": 1234,
    "totalChunks": 5678,
    "moduleCount": 15,
    "embeddingsCount": 5680,
    "contextWindowUsagePercent": 67.5
  },
  "activeSession": {
    "id": "session-uuid",
    "startedAt": "2025-10-09T10:00:00.000Z",
    "duration": 7200,  // seconds
    "contextTokens": 67500
  }
}
```

---

### GET /api/sessions

**Purpose**: Get session timeline for dashboard.

**Query Parameters**:
- `limit` (number, optional): Max sessions to return (default: 50, max: 100)
- `since` (ISO date, optional): Show sessions after this date

**Response**:
```json
HTTP 200 OK
Content-Type: application/json

{
  "sessions": [
    {
      "id": "session-uuid-1",
      "startedAt": "2025-10-09T10:00:00.000Z",
      "endedAt": "2025-10-09T12:00:00.000Z",
      "duration": 7200,
      "contextTokens": 67500,
      "filesAccessed": 25,
      "gitToolsUsed": 5,
      "discoveriesExtracted": 3,
      "status": "completed"
    },
    {
      "id": "session-uuid-2",
      "startedAt": "2025-10-08T14:00:00.000Z",
      "endedAt": "2025-10-08T16:30:00.000Z",
      "duration": 9000,
      "contextTokens": 72000,
      "filesAccessed": 30,
      "gitToolsUsed": 8,
      "discoveriesExtracted": 5,
      "status": "completed"
    }
  ],
  "total": 150,
  "hasMore": true
}
```

---

### GET /api/sessions/:sessionId

**Purpose**: Get detailed session information.

**Response**:
```json
HTTP 200 OK
Content-Type: application/json

{
  "id": "session-uuid-1",
  "startedAt": "2025-10-09T10:00:00.000Z",
  "endedAt": "2025-10-09T12:00:00.000Z",
  "duration": 7200,
  "contextTokens": 67500,
  "status": "completed",
  
  "filesAccessed": [
    {
      "path": "src/auth/jwt.ts",
      "accessCount": 5,
      "lastAccessedAt": "2025-10-09T11:30:00.000Z"
    },
    {
      "path": "src/api/routes.ts",
      "accessCount": 3,
      "lastAccessedAt": "2025-10-09T11:00:00.000Z"
    }
  ],
  
  "gitCommitsQueried": [
    "abc1234 - feat(auth): add JWT authentication",
    "def5678 - fix(auth): handle expired tokens"
  ],
  
  "discoveries": [
    {
      "id": "discovery-uuid-1",
      "type": "pattern",
      "description": "Use middleware pattern for authentication",
      "confidence": 0.85,
      "accepted": true
    }
  ]
}
```

---

### GET /api/modules

**Purpose**: Get module dependency graph for visualization.

**Response**:
```json
HTTP 200 OK
Content-Type: application/json

{
  "nodes": [
    {
      "id": "auth",
      "name": "auth",
      "fileCount": 15,
      "recentAccessCount": 25,
      "activityLevel": "high"  // high/medium/low
    },
    {
      "id": "api",
      "name": "api",
      "fileCount": 20,
      "recentAccessCount": 10,
      "activityLevel": "medium"
    }
  ],
  "edges": [
    {
      "source": "api",
      "target": "auth",
      "importCount": 8,
      "weight": 0.8  // Normalized 0-1
    }
  ]
}
```

---

### GET /api/embeddings

**Purpose**: Get embedding statistics for dashboard.

**Response**:
```json
HTTP 200 OK
Content-Type: application/json

{
  "statistics": {
    "totalEmbeddings": 5680,
    "chunkEmbeddings": 5000,
    "fileEmbeddings": 680,  // Fallback embeddings
    "lastGeneratedAt": "2025-10-09T11:55:00.000Z",
    "queueDepth": 12,
    "diskUsageMB": 245.7,
    "avgGenerationTimeMs": 150
  },
  
  "recentErrors": [
    {
      "timestamp": "2025-10-09T10:30:00.000Z",
      "type": "api_rate_limit",
      "message": "OpenAI rate limit exceeded, retrying in 5s",
      "resolved": true
    }
  ]
}
```

---

### GET /api/context

**Purpose**: Get current context window state.

**Response**:
```json
HTTP 200 OK
Content-Type: application/json

{
  "currentTokens": 67500,
  "maxTokens": 100000,
  "usagePercent": 67.5,
  "status": "healthy",  // healthy/warning/critical
  
  "breakdown": {
    "projectContext": 20000,
    "sessionFiles": 35000,
    "discoveries": 8500,
    "history": 4000
  },
  
  "recommendations": [
    "Context usage is healthy (67.5%)",
    "Top 5 files account for 40% of context"
  ]
}
```

---

### GET /api/linked-projects

**Purpose**: Get linked projects in workspace (for multi-project setups).

**Response**:
```json
HTTP 200 OK
Content-Type: application/json

{
  "projects": [
    {
      "name": "frontend",
      "path": "/Users/user/projects/my-app/frontend",
      "linkType": "workspace",
      "status": "available",
      "lastAccessed": "2025-10-09T12:00:00.000Z",
      "statistics": {
        "fileCount": 500,
        "moduleCount": 10,
        "embeddingsCount": 2000
      }
    },
    {
      "name": "backend",
      "path": "/Users/user/projects/my-app/backend",
      "linkType": "workspace",
      "status": "available",
      "lastAccessed": "2025-10-09T11:30:00.000Z",
      "statistics": {
        "fileCount": 400,
        "moduleCount": 8,
        "embeddingsCount": 1500
      }
    }
  ],
  
  "crossReferences": [
    {
      "source": "frontend:/src/api/client.ts",
      "target": "backend:/src/routes/api.ts",
      "type": "api_call",
      "confidence": 0.9
    }
  ]
}
```

---

## Error Responses

All API endpoints follow consistent error format:

```json
HTTP 4xx/5xx
Content-Type: application/json

{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      // Additional context (optional)
    }
  },
  "timestamp": "2025-10-09T12:00:00.000Z"
}
```

**Error Codes**:
- `INTERNAL_SERVER_ERROR` (500): Unexpected server error
- `NOT_FOUND` (404): Resource not found
- `BAD_REQUEST` (400): Invalid request parameters
- `SERVICE_UNAVAILABLE` (503): Service temporarily unavailable

---

## CORS Configuration

```javascript
// Allow dashboard to access API from different port
headers: {
  'Access-Control-Allow-Origin': 'http://localhost:3456',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
}
```

---

## Performance Targets

| Endpoint | p50 | p95 | p99 |
|----------|-----|-----|-----|
| GET /metrics | <20ms | <40ms | <50ms |
| GET /health | <50ms | <80ms | <100ms |
| GET /api/project | <50ms | <100ms | <150ms |
| GET /api/sessions | <100ms | <200ms | <300ms |
| GET /api/sessions/:id | <80ms | <150ms | <200ms |
| GET /api/modules | <150ms | <300ms | <500ms |
| GET /api/embeddings | <50ms | <100ms | <150ms |

---

## Security

### Authentication

- **Metrics/Health**: No authentication (designed for local access only)
- **Dashboard API**: No authentication in v2.0 (single-user, local only)
- **Future (v3.0+)**: Add token-based auth for team deployments

### Network Binding

```typescript
// Bind to localhost only (not exposed to network)
server.listen(9090, '127.0.0.1');
```

### Rate Limiting

- **Metrics**: No rate limiting (designed for Prometheus scraping)
- **Dashboard API**: 100 requests/minute per IP (prevent abuse)

---

**END OF REST API CONTRACT**
