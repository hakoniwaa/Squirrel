# coder-mcp Architecture

## Overview

coder-mcp is a Model Context Protocol (MCP) server that provides intelligent code assistance with persistent memory and advanced code analysis capabilities. This document describes the system architecture and design decisions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Client (Claude)                      │
└─────────────────────────┬───────────────────────────────────────┘
                          │ MCP Protocol (stdio)
┌─────────────────────────▼───────────────────────────────────────┐
│                      ModularMCPServer                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Tool Handlers                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │   File   │ │  Search  │ │ Analysis │ │ Template │  │   │
│  │  │Operations│ │  Tools   │ │  Tools   │ │  Tools   │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Context Manager                         │   │
│  │  ┌──────────────┐ ┌─────────────┐ ┌────────────────┐   │   │
│  │  │   Project    │ │   Vector    │ │    Memory      │   │   │
│  │  │   Context    │ │   Search    │ │  Persistence   │   │   │
│  │  └──────────────┘ └─────────────┘ └────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Configuration Manager                       │   │
│  │  ┌──────────────┐ ┌─────────────┐ ┌────────────────┐   │   │
│  │  │   Config     │ │  Provider   │ │   Security     │   │   │
│  │  │   Loader     │ │  Registry   │ │  Validation    │   │   │
│  │  └──────────────┘ └─────────────┘ └────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                     External Services                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │   Redis    │ │  OpenAI    │ │Local Model │ │   File     │  │
│  │  (Vector)  │ │(Embeddings)│ │(Embeddings)│ │  System    │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. ModularMCPServer (`coder_mcp/server.py`)

The main server class that orchestrates all components:

- **Responsibility**: MCP protocol handling, request routing, lifecycle management
- **Key Features**:
  - Lazy initialization of components
  - Thread-safe operations
  - Graceful error handling
  - Health monitoring

### 2. Configuration System (`coder_mcp/core/`)

Manages all configuration aspects:

- **ConfigurationManager**: Central configuration orchestrator
- **ConfigurationLoader**: Loads config from `.env.mcp` files
- **ConfigurationValidator**: Validates configuration integrity
- **Models**: Pydantic models for type-safe configuration

### 3. Context Management (`coder_mcp/context/`)

Provides intelligent context awareness:

- **ContextManager**: Orchestrates context operations
- **ProjectIndexer**: Indexes project files for search
- **VectorStore**: Manages vector embeddings
- **MemoryManager**: Handles cross-session persistence

### 4. Tool System (`coder_mcp/tools/`)

Implements MCP tool handlers:

- **ToolHandlers**: Central tool registry and router
- **FileOperations**: File reading/writing with safety checks
- **SearchTools**: Code and context search capabilities
- **AnalysisTools**: Code quality and structure analysis
- **TemplateTools**: Code generation and scaffolding

### 5. Code Analysis (`coder_mcp/analysis/`)

Provides deep code understanding:

- **CodeAnalyzer**: Main analysis orchestrator
- **Language Analyzers**: Language-specific AST analysis
- **Metrics Calculator**: Complexity and quality metrics
- **Pattern Detector**: Code smell and pattern detection

### 6. Template System (`coder_mcp/templates/`)

Manages code generation:

- **TemplateManager**: Template loading and rendering
- **Template Builders**: Language-specific builders
- **Template Registry**: Available templates catalog

## Design Patterns

### 1. Provider Pattern

```python
# Abstract interface for swappable implementations
class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        pass

# Concrete implementations
class OpenAIProvider(EmbeddingProvider):
    async def embed(self, text: str) -> List[float]:
        # OpenAI implementation

class LocalProvider(EmbeddingProvider):
    async def embed(self, text: str) -> List[float]:
        # Local model implementation
```

### 2. Factory Pattern

Used for creating providers based on configuration:

```python
class ProviderFactory:
    @staticmethod
    def create_embedding_provider(config: Dict) -> EmbeddingProvider:
        if config["type"] == "openai":
            return OpenAIProvider(config)
        elif config["type"] == "local":
            return LocalProvider(config)
```

### 3. Repository Pattern

For data access abstraction:

```python
class VectorRepository:
    async def store(self, key: str, vector: List[float], metadata: Dict)
    async def search(self, vector: List[float], limit: int) -> List[Result]
    async def delete(self, key: str)
```

### 4. Chain of Responsibility

For request processing:

```python
Tool Request → Validation → Security Check → Cache Check → Execution → Cache Update → Response
```

## Data Flow

### 1. Tool Request Flow

```
1. MCP Client sends tool request
2. Server validates request format
3. Security middleware checks permissions
4. Tool handler processes request
5. Context manager updates if needed
6. Response sent back to client
```

### 2. Context Indexing Flow

```
1. File change detected
2. File content extracted
3. Code analysis performed
4. Embeddings generated
5. Vector store updated
6. Context cache invalidated
```

### 3. Search Flow

```
1. Search query received
2. Query embedded to vector
3. Vector similarity search
4. Results ranked and filtered
5. Content retrieved
6. Response formatted
```

## Security Architecture

### 1. Path Traversal Prevention

- All file paths are resolved and validated
- Operations restricted to workspace root
- Symlink resolution with security checks

### 2. Input Validation

- Pydantic models for all inputs
- Size limits on file operations
- Rate limiting on expensive operations

### 3. Secret Management

- Secrets loaded from `.env.mcp`
- Never logged or exposed in errors
- Secure provider initialization

## Performance Optimizations

### 1. Caching Strategy

- **Redis Cache**: For embeddings and search results
- **Memory Cache**: For hot paths and frequent operations
- **TTL Management**: Configurable expiration times

### 2. Lazy Loading

- Components initialized only when needed
- Provider connections established on first use
- Index building done asynchronously

### 3. Batch Operations

- Vector embeddings processed in batches
- File operations optimized for bulk processing
- Database queries minimized through aggregation

## Extension Points

### 1. Adding New Providers

1. Implement provider interface
2. Register in ProviderRegistry
3. Add configuration model
4. Update factory method

### 2. Adding New Tools

1. Create tool handler class
2. Register with ToolHandlers
3. Add input/output models
4. Update tool documentation

### 3. Adding Language Support

1. Create language analyzer
2. Implement AST visitor
3. Add to analyzer registry
4. Create language templates

## Error Handling

### 1. Error Hierarchy

```
MCPServerError
├── ConfigurationError
├── ProviderError
│   ├── ConnectionError
│   └── RateLimitError
├── SecurityError
│   ├── PathTraversalError
│   └── PermissionError
└── ToolError
    ├── ValidationError
    └── ExecutionError
```

### 2. Error Recovery

- Automatic retry with exponential backoff
- Fallback to local providers
- Graceful degradation of features

## Monitoring and Observability

### 1. Health Checks

- Provider connectivity
- Cache availability
- File system access
- Memory usage

### 2. Metrics

- Request latency
- Cache hit rates
- Embedding generation time
- Error rates by type

### 3. Logging

- Structured logging to stderr
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request tracing with correlation IDs

## Future Considerations

### 1. Scalability

- Multi-process support
- Distributed caching
- Horizontal scaling of providers

### 2. Advanced Features

- Real-time collaboration
- Git integration
- Custom analyzer plugins
- WebSocket support

### 3. Performance

- GPU acceleration for embeddings
- Incremental indexing
- Streaming responses
- Query optimization
