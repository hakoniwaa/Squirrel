# coder-mcp Configuration Guide

## Configuration Overview

coder-mcp uses a layered configuration system with the following precedence (highest to lowest):

1. Environment variables
2. `.env.mcp` file in workspace root
3. User configuration file (`~/.coder-mcp/config.json`)
4. Default configuration

## Configuration File (.env.mcp)

Create a `.env.mcp` file in your workspace root:

```bash
# Server Configuration
MCP_SERVER_NAME=coder-mcp-enhanced
MCP_SERVER_VERSION=5.0.0
MCP_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
MCP_WORKSPACE_ROOT=.  # or absolute path

# Provider Configuration
MCP_EMBEDDING_PROVIDER=openai  # openai, local
MCP_VECTOR_STORE=redis  # redis, local
MCP_CACHE_PROVIDER=redis  # redis, memory

# OpenAI Configuration (if using OpenAI embeddings)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=text-embedding-3-small
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=30

# Redis Configuration (if using Redis)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=  # optional
REDIS_SSL=false
REDIS_POOL_SIZE=10
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# Local Embedding Configuration (if using local embeddings)
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LOCAL_EMBEDDING_DEVICE=cpu  # cpu, cuda, mps
LOCAL_EMBEDDING_BATCH_SIZE=32

# Feature Flags
MCP_ENABLE_CACHING=true
MCP_ENABLE_VECTOR_SEARCH=true
MCP_ENABLE_CODE_ANALYSIS=true
MCP_ENABLE_TEMPLATES=true
MCP_ENABLE_SECURITY_CHECKS=true

# Performance Limits
MCP_MAX_FILE_SIZE=10485760  # 10MB
MCP_MAX_FILES_TO_INDEX=1000
MCP_CACHE_TTL=3600  # 1 hour
MCP_EMBEDDING_CACHE_SIZE=10000
MCP_SEARCH_RESULTS_LIMIT=50

# Security Configuration
MCP_ALLOWED_FILE_EXTENSIONS=.py,.js,.ts,.jsx,.tsx,.java,.go,.rs,.c,.cpp,.h,.hpp,.cs,.rb,.php,.swift,.kt,.scala,.r,.m,.mm,.md,.txt,.json,.yaml,.yml,.toml,.xml,.html,.css,.scss,.sql
MCP_FORBIDDEN_PATHS=.git,node_modules,__pycache__,.env,.venv,venv,env,dist,build,target
MCP_ENABLE_SYMLINK_FOLLOWING=false
MCP_MAX_PATH_DEPTH=10

# Advanced Configuration
MCP_VECTOR_DIMENSIONS=3072  # for OpenAI embeddings
MCP_VECTOR_INDEX_TYPE=HNSW  # HNSW, FLAT
MCP_VECTOR_DISTANCE_METRIC=COSINE  # COSINE, L2, IP
MCP_ANALYSIS_TIMEOUT=30
MCP_TEMPLATE_CACHE_SIZE=100
```

## Provider-Specific Configuration

### OpenAI Provider

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
OPENAI_MODEL=text-embedding-3-small  # or text-embedding-3-large
OPENAI_ORG_ID=org-...  # if using organization
OPENAI_BASE_URL=https://api.openai.com/v1  # for proxies
OPENAI_MAX_TOKENS=8191
OPENAI_TEMPERATURE=0.0  # for any generation tasks
```

### Redis Provider

```bash
# Connection
REDIS_URL=redis://localhost:6379/0
# or use individual settings:
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_USERNAME=  # Redis 6.0+
REDIS_PASSWORD=

# Connection Pool
REDIS_POOL_SIZE=10
REDIS_POOL_TIMEOUT=5
REDIS_MAX_CONNECTIONS=50

# Timeouts
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_SOCKET_KEEPALIVE=true

# SSL/TLS
REDIS_SSL=false
REDIS_SSL_CERTFILE=/path/to/cert.pem
REDIS_SSL_KEYFILE=/path/to/key.pem
REDIS_SSL_CA_CERTS=/path/to/ca.pem

# Cluster Mode
REDIS_CLUSTER_MODE=false
REDIS_CLUSTER_NODES=localhost:7000,localhost:7001,localhost:7002
```

### Local Embedding Provider

```bash
# Model Selection
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# Other good options:
# - sentence-transformers/all-mpnet-base-v2 (better quality)
# - sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (multilingual)

# Hardware
LOCAL_EMBEDDING_DEVICE=cpu  # cpu, cuda, mps (Apple Silicon)
LOCAL_EMBEDDING_USE_GPU=auto  # auto, true, false

# Performance
LOCAL_EMBEDDING_BATCH_SIZE=32
LOCAL_EMBEDDING_MAX_LENGTH=512
LOCAL_EMBEDDING_NORMALIZE=true
LOCAL_EMBEDDING_NUM_THREADS=4  # for CPU

# Model Cache
LOCAL_EMBEDDING_CACHE_DIR=~/.cache/coder-mcp/models
LOCAL_EMBEDDING_FORCE_DOWNLOAD=false
```

## Claude Desktop Integration

### 1. Configure Claude Desktop

Edit Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "coder-mcp": {
      "command": "python",
      "args": ["-m", "coder_mcp.server"],
      "env": {
        "PYTHONPATH": "/path/to/coder-mcp",
        "MCP_WORKSPACE_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

### 2. Using Poetry

If using Poetry:

```json
{
  "mcpServers": {
    "coder-mcp": {
      "command": "poetry",
      "args": ["run", "coder-mcp"],
      "cwd": "/path/to/coder-mcp",
      "env": {
        "MCP_WORKSPACE_ROOT": "/path/to/your/project"
      }
    }
  }
}
```

### 3. Using Docker

```json
{
  "mcpServers": {
    "coder-mcp": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v", "/path/to/project:/workspace",
        "-e", "MCP_WORKSPACE_ROOT=/workspace",
        "coder-mcp:latest"
      ]
    }
  }
}
```

## Environment-Specific Configurations

### Development

```bash
# .env.mcp.development
MCP_LOG_LEVEL=DEBUG
MCP_ENABLE_PROFILING=true
MCP_ENABLE_DEBUG_TOOLS=true
MCP_CACHE_PROVIDER=memory  # Faster for development
MCP_VECTOR_STORE=local  # No external dependencies
```

### Testing

```bash
# .env.mcp.test
MCP_LOG_LEVEL=WARNING
MCP_CACHE_PROVIDER=memory
MCP_VECTOR_STORE=local
MCP_MAX_FILES_TO_INDEX=100  # Smaller for faster tests
REDIS_URL=redis://localhost:6380/1  # Separate test database
```

### Production

```bash
# .env.mcp.production
MCP_LOG_LEVEL=INFO
MCP_ENABLE_PROFILING=false
MCP_ENABLE_DEBUG_TOOLS=false
REDIS_URL=redis://redis.internal:6379/0
REDIS_PASSWORD=${REDIS_PASSWORD}  # From secrets
OPENAI_API_KEY=${OPENAI_API_KEY}  # From secrets
```

## Performance Tuning

### Memory Usage

```bash
# Reduce memory usage
MCP_MAX_FILES_TO_INDEX=500  # Default: 1000
MCP_EMBEDDING_CACHE_SIZE=5000  # Default: 10000
MCP_TEMPLATE_CACHE_SIZE=50  # Default: 100
MCP_VECTOR_STORE=local  # Uses less memory than Redis

# For large codebases
MCP_ENABLE_INCREMENTAL_INDEXING=true
MCP_INDEX_BATCH_SIZE=50  # Process files in batches
MCP_INDEX_PARALLEL_WORKERS=4  # Parallel processing
```

### Speed Optimization

```bash
# Faster operations
MCP_ENABLE_CACHING=true
MCP_CACHE_WARMING=true  # Pre-populate cache on startup
MCP_VECTOR_INDEX_TYPE=FLAT  # Faster than HNSW for small datasets
MCP_ANALYSIS_PARALLEL=true
MCP_SEARCH_USE_CACHE=true

# Batch operations
MCP_EMBEDDING_BATCH_SIZE=64  # Process multiple texts
MCP_FILE_READ_BUFFER_SIZE=65536  # 64KB chunks
```

### Network Optimization

```bash
# Connection pooling
REDIS_POOL_SIZE=20
REDIS_POOL_TIMEOUT=10
OPENAI_CONNECTION_POOL_SIZE=10

# Timeouts
REDIS_SOCKET_TIMEOUT=10
OPENAI_TIMEOUT=60
MCP_REQUEST_TIMEOUT=120

# Compression
MCP_ENABLE_COMPRESSION=true
MCP_COMPRESSION_LEVEL=6  # 1-9
```

## Security Configuration

### Basic Security

```bash
# File access
MCP_SANDBOX_MODE=true
MCP_ALLOWED_PATHS=/home/user/projects
MCP_FORBIDDEN_PATHS=~/.ssh,~/.aws,/etc,/sys,/proc
MCP_FOLLOW_SYMLINKS=false

# Network security
MCP_ALLOWED_DOMAINS=api.openai.com,github.com
MCP_ENABLE_HTTPS_ONLY=true
MCP_VERIFY_SSL_CERTS=true
```

### Advanced Security

```bash
# Rate limiting
MCP_RATE_LIMIT_ENABLED=true
MCP_RATE_LIMIT_REQUESTS=100
MCP_RATE_LIMIT_WINDOW=60  # seconds

# Authentication (future feature)
MCP_AUTH_ENABLED=true
MCP_AUTH_METHOD=token  # token, oauth2
MCP_AUTH_TOKEN=${MCP_AUTH_TOKEN}

# Audit logging
MCP_AUDIT_LOG_ENABLED=true
MCP_AUDIT_LOG_FILE=/var/log/coder-mcp/audit.log
MCP_AUDIT_LOG_LEVEL=INFO
```

## Monitoring Configuration

### Metrics

```bash
# Metrics collection
MCP_METRICS_ENABLED=true
MCP_METRICS_EXPORT_INTERVAL=60  # seconds
MCP_METRICS_INCLUDE_LABELS=true

# Prometheus integration
MCP_PROMETHEUS_ENABLED=true
MCP_PROMETHEUS_PORT=9090
MCP_PROMETHEUS_PATH=/metrics
```

### Logging

```bash
# Log configuration
MCP_LOG_FORMAT=json  # json, text
MCP_LOG_LEVEL=INFO
MCP_LOG_FILE=/var/log/coder-mcp/server.log
MCP_LOG_MAX_SIZE=100  # MB
MCP_LOG_MAX_FILES=10
MCP_LOG_COMPRESS=true

# Structured logging
MCP_LOG_INCLUDE_TIMESTAMP=true
MCP_LOG_INCLUDE_LEVEL=true
MCP_LOG_INCLUDE_MODULE=true
MCP_LOG_INCLUDE_FUNCTION=false
MCP_LOG_INCLUDE_LINE=false
```

### Health Checks

```bash
# Health check configuration
MCP_HEALTH_CHECK_ENABLED=true
MCP_HEALTH_CHECK_INTERVAL=30  # seconds
MCP_HEALTH_CHECK_TIMEOUT=5
MCP_HEALTH_CHECK_INCLUDE_DETAILS=true

# Component checks
MCP_CHECK_REDIS=true
MCP_CHECK_OPENAI=true
MCP_CHECK_DISK_SPACE=true
MCP_CHECK_MEMORY_USAGE=true
```

## Troubleshooting Configuration

### Debug Mode

```bash
# Enable all debug features
MCP_DEBUG_MODE=true
MCP_LOG_LEVEL=DEBUG
MCP_ENABLE_PROFILING=true
MCP_PRINT_STACK_TRACES=true
MCP_SAVE_DEBUG_FILES=true
MCP_DEBUG_OUTPUT_DIR=/tmp/coder-mcp-debug
```

### Common Issues

1. **Redis Connection Failed**
```bash
# Test with redis-cli
redis-cli -h localhost -p 6379 ping

# Check configuration
REDIS_URL=redis://localhost:6379/0
REDIS_SOCKET_CONNECT_TIMEOUT=10
REDIS_RETRY_ON_TIMEOUT=true
```

2. **OpenAI Rate Limits**
```bash
# Reduce rate
OPENAI_MAX_RETRIES=5
OPENAI_RETRY_DELAY=2
OPENAI_RATE_LIMIT_BUFFER=0.8  # Use 80% of limit
```

3. **Memory Issues**
```bash
# Reduce memory usage
MCP_CACHE_PROVIDER=memory
MCP_EMBEDDING_CACHE_SIZE=1000
MCP_MAX_FILES_TO_INDEX=100
MCP_GC_INTERVAL=300  # Run GC every 5 minutes
```

## Configuration Validation

Run configuration validation:

```bash
# Validate current configuration
poetry run coder-mcp validate-config

# Test specific configuration file
poetry run coder-mcp validate-config --config .env.mcp.production

# Dry run with configuration
poetry run coder-mcp --dry-run --config .env.mcp.test
```

## Best Practices

1. **Use environment-specific files**
   - `.env.mcp.development`
   - `.env.mcp.test`
   - `.env.mcp.production`

2. **Never commit secrets**
   - Add `.env.mcp*` to `.gitignore`
   - Use secret management systems in production

3. **Start with minimal configuration**
   - Use defaults where possible
   - Only override what you need

4. **Monitor resource usage**
   - Set appropriate limits
   - Use monitoring tools

5. **Regular configuration audits**
   - Review security settings
   - Update deprecated options
   - Remove unused configuration
