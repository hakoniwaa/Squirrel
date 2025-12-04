# coder-mcp Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Poetry Installation Fails

**Problem**: `poetry install` fails with dependency conflicts

**Solution**:
```bash
# Clear Poetry cache
poetry cache clear pypi --all

# Update Poetry
poetry self update

# Try installing with verbose output
poetry install -vvv

# If specific package fails, install without it first
poetry install --without problematic-group
```

#### Python Version Mismatch

**Problem**: Wrong Python version error

**Solution**:
```bash
# Check Python version
python --version

# Use pyenv to install correct version
pyenv install 3.11.7
pyenv local 3.11.7

# Tell Poetry to use specific Python
poetry env use 3.11.7
```

#### MCP SDK Installation Issues

**Problem**: Can't install MCP SDK from Git

**Solution**:
```bash
# Install Git if missing
# macOS: brew install git
# Ubuntu: sudo apt-get install git
# Windows: download from git-scm.com

# Try HTTPS instead of SSH
poetry add git+https://github.com/modelcontextprotocol/python-sdk.git#main

# Or clone and install locally
git clone https://github.com/modelcontextprotocol/python-sdk.git
cd python-sdk
pip install -e .
```

### Configuration Issues

#### Environment Variables Not Loading

**Problem**: Settings from `.env.mcp` not being used

**Solution**:
```bash
# Check file exists and is readable
ls -la .env.mcp

# Verify format (no spaces around =)
OPENAI_API_KEY=sk-xxx  # Correct # pragma: allowlist secret
OPENAI_API_KEY = sk-xxx  # Wrong

# Test loading manually
python -c "from dotenv import load_dotenv; load_dotenv('.env.mcp'); import os; print(os.getenv('OPENAI_API_KEY'))"

# Check working directory
pwd  # Should be project root
```

#### Invalid Configuration Error

**Problem**: "Configuration validation failed"

**Solution**:
```python
# Run configuration validator
poetry run coder-mcp validate-config

# Check specific issues
poetry run python -c "
from coder_mcp.core import ConfigurationManager
cm = ConfigurationManager()
result = cm.validate_configuration()
print(result)
"
```

### Redis Connection Issues

#### Cannot Connect to Redis

**Problem**: "Redis connection refused" or timeout

**Solution**:
```bash
# Check if Redis is running
redis-cli ping
# Should return "PONG"

# Start Redis
# macOS: brew services start redis
# Ubuntu: sudo systemctl start redis
# Docker: docker run -d -p 6379:6379 redis:alpine

# Test connection with URL
redis-cli -u redis://localhost:6379/0 ping

# Check Redis logs
redis-server --version
tail -f /usr/local/var/log/redis.log  # macOS
tail -f /var/log/redis/redis-server.log  # Ubuntu
```

#### Redis Authentication Failed

**Problem**: "NOAUTH Authentication required"

**Solution**:
```bash
# Add password to .env.mcp
REDIS_PASSWORD=your-redis-password

# Test with password
redis-cli -a your-redis-password ping

# Or use URL format
REDIS_URL=redis://:password@localhost:6379/0
```

### OpenAI API Issues

#### Invalid API Key

**Problem**: "Invalid API key provided"

**Solution**:
```bash
# Verify API key format
# Should start with "sk-" and be 48+ characters

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check environment variable
echo $OPENAI_API_KEY

# Ensure no extra spaces or quotes
OPENAI_API_KEY=sk-your-actual-key-here  # Correct  # pragma: allowlist secret
OPENAI_API_KEY="sk-your-actual-key-here"  # Wrong - no quotes needed  # pragma: allowlist secret
```

#### Rate Limit Errors

**Problem**: "Rate limit exceeded"

**Solution**:
```bash
# Add rate limiting configuration
OPENAI_MAX_RETRIES=5
OPENAI_RETRY_DELAY=2
OPENAI_RATE_LIMIT_BUFFER=0.8  # Use only 80% of limit

# Use local embeddings instead
MCP_EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### File Operation Issues

#### Permission Denied

**Problem**: "Permission denied" when reading/writing files

**Solution**:
```bash
# Check file permissions
ls -la problem-file.py

# Fix permissions
chmod 644 problem-file.py  # Read for all, write for owner
chmod 755 problem-directory  # Execute needed for directories

# Check workspace root permissions
ls -la $MCP_WORKSPACE_ROOT

# Run with correct user
whoami  # Check current user
```

#### Path Traversal Blocked

**Problem**: "Path traversal attempt blocked"

**Solution**:
```python
# Use relative paths within workspace
# Good: "src/file.py", "./config/settings.json"
# Bad: "/etc/passwd", "../../../secret.key"

# Check workspace root
print(server.workspace_root)

# Ensure file is within workspace
from pathlib import Path
workspace = Path("/project")
file_path = workspace / "src/file.py"
assert file_path.resolve().is_relative_to(workspace.resolve())
```

### Memory Issues

#### High Memory Usage

**Problem**: Server using too much memory

**Solution**:
```bash
# Reduce cache sizes
MCP_EMBEDDING_CACHE_SIZE=1000  # Default: 10000
MCP_TEMPLATE_CACHE_SIZE=50  # Default: 100
MCP_MAX_FILES_TO_INDEX=500  # Default: 1000

# Use local storage instead of Redis
MCP_VECTOR_STORE=local
MCP_CACHE_PROVIDER=memory

# Enable garbage collection
MCP_GC_INTERVAL=300  # Run GC every 5 minutes
MCP_GC_THRESHOLD=1000  # Trigger at 1000 objects
```

#### Out of Memory Errors

**Problem**: "MemoryError" or system kills process

**Solution**:
```bash
# Monitor memory usage
# macOS/Linux
top -p $(pgrep -f coder-mcp)

# Limit memory usage
ulimit -v 2097152  # 2GB limit

# Process files in batches
MCP_INDEX_BATCH_SIZE=50  # Process 50 files at a time
MCP_ENABLE_INCREMENTAL_INDEXING=true
```

### Performance Issues

#### Slow Initialization

**Problem**: Server takes too long to start

**Solution**:
```bash
# Skip indexing on startup
MCP_INDEX_ON_STARTUP=false
MCP_CACHE_WARMING=false

# Reduce number of files to index
MCP_MAX_FILES_TO_INDEX=100
MCP_IGNORE_PATTERNS=*.log,*.tmp,node_modules,__pycache__

# Use faster providers
MCP_VECTOR_INDEX_TYPE=FLAT  # Faster than HNSW
LOCAL_EMBEDDING_DEVICE=cuda  # If GPU available
```

#### Slow Search Operations

**Problem**: Search queries take too long

**Solution**:
```bash
# Enable caching
MCP_ENABLE_CACHING=true
MCP_SEARCH_CACHE_TTL=3600  # Cache for 1 hour

# Optimize vector search
MCP_VECTOR_INDEX_TYPE=HNSW
MCP_HNSW_M=16  # Connections per node
MCP_HNSW_EF_CONSTRUCTION=200  # Build-time parameter

# Limit search scope
MCP_SEARCH_MAX_RESULTS=20  # Return fewer results
MCP_SEARCH_MIN_SCORE=0.7  # Higher threshold
```

### Claude Desktop Integration Issues

#### Server Not Starting

**Problem**: Claude Desktop can't start coder-mcp

**Solution**:
```json
// Check Claude Desktop config
// macOS: ~/Library/Application Support/Claude/claude_desktop_config.json

{
  "mcpServers": {
    "coder-mcp": {
      "command": "/usr/bin/python3",  // Use full path
      "args": ["-m", "coder_mcp.server"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/coder-mcp",
        "PATH": "/usr/local/bin:/usr/bin:/bin"  // Include PATH
      }
    }
  }
}
```

#### Tools Not Appearing

**Problem**: coder-mcp tools don't show up in Claude

**Solution**:
1. Check server is running:
```bash
# Look for coder-mcp process
ps aux | grep coder-mcp

# Check Claude Desktop logs
# macOS: ~/Library/Logs/Claude/
tail -f ~/Library/Logs/Claude/claude.log
```

2. Verify MCP protocol:
```bash
# Test server manually
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | \
  python -m coder_mcp.server
```

### Debugging Steps

#### Enable Debug Logging

```bash
# In .env.mcp
MCP_LOG_LEVEL=DEBUG
MCP_DEBUG_MODE=true
MCP_LOG_FILE=/tmp/coder-mcp.log

# Watch logs
tail -f /tmp/coder-mcp.log
```

#### Test Individual Components

```python
# Test configuration
from coder_mcp.core import ConfigurationManager
cm = ConfigurationManager()
print(cm.get_config())

# Test Redis connection
import redis
r = redis.from_url("redis://localhost:6379/0")
r.ping()

# Test OpenAI
from openai import OpenAI
client = OpenAI()
client.models.list()

# Test file operations
from coder_mcp.tools import FileOperations
fo = FileOperations(Path.cwd())
fo.read_file("README.md")
```

#### Check System Resources

```bash
# Disk space
df -h

# Memory
free -h  # Linux
vm_stat  # macOS

# CPU
top
htop  # If installed

# Open files
lsof -p $(pgrep -f coder-mcp) | wc -l
ulimit -n  # Check limit
```

### Getting Help

#### Collect Diagnostic Information

```bash
# Create diagnostic report
poetry run coder-mcp diagnose > diagnostic_report.txt

# Include:
# - Python version
# - Poetry version
# - OS information
# - Configuration (without secrets)
# - Recent logs
# - Error messages
```

#### Report Issues

When reporting issues, include:

1. **Environment**:
   - OS and version
   - Python version
   - Poetry version
   - Redis version (if applicable)

2. **Configuration** (remove sensitive data):
   ```bash
   cat .env.mcp | grep -v "KEY\|PASSWORD\|TOKEN"
   ```

3. **Error Messages**:
   - Full error traceback
   - Relevant log entries

4. **Steps to Reproduce**:
   - Exact commands run
   - Expected behavior
   - Actual behavior

5. **What You've Tried**:
   - Solutions attempted
   - Results of diagnostic steps

### Quick Fixes Checklist

- [ ] Redis is running and accessible
- [ ] OpenAI API key is valid (if using)
- [ ] Python version is 3.10+
- [ ] All dependencies installed via Poetry
- [ ] Working directory is project root
- [ ] File permissions are correct
- [ ] No syntax errors in .env.mcp
- [ ] Sufficient disk space and memory
- [ ] No firewall blocking connections
- [ ] Latest version of coder-mcp

## MCP Timeout Errors

### Error: MCP error -32001: Request timed out

**Symptoms:**
- Operations like `list_files` fail with timeout errors
- Error message: "Failed to call tool list_files: Error: MCP error -32001: Request timed out"
- Operations work on small directories but fail on large ones

**Root Causes:**
1. **Default timeout too low**: MCP request timeout was set to 30 seconds by default
2. **Inefficient file operations**: Large directory scans can take longer than expected
3. **No performance limits**: Operations don't have built-in safeguards against processing too many files

**Solutions Implemented:**

#### 1. Increased MCP Request Timeout
- **Changed**: Default MCP request timeout from 30s to 60s
- **File**: `coder_mcp/core/config/defaults.py`
- **Setting**: `MCP_REQUEST_TIMEOUT: 60`

#### 2. Optimized File Listing Performance
- **Added**: Performance limits to prevent runaway operations
- **File**: `coder_mcp/tools/handlers/file.py`
- **Limits**:
  - Maximum files to process: 1,000
  - Maximum processing time: 55 seconds
  - Async yielding every 100 items

#### 3. Enhanced Error Handling
- **Added**: Graceful timeout handling with partial results
- **Added**: Clear error messages when operations are limited
- **Added**: Performance statistics in results

**Configuration Options:**

You can customize timeout settings via environment variables:

```bash
# Set MCP request timeout (seconds)
export MCP_REQUEST_TIMEOUT=120

# Set maximum files to list
export MCP_MAX_FILES_TO_INDEX=2000
```

**Best Practices:**

1. **Use specific patterns**: Instead of `*`, use specific patterns like `*.py` to reduce scope
2. **Work with smaller directories**: Navigate to subdirectories for more focused operations
3. **Monitor performance**: Pay attention to timeout warnings in results

**Example Usage:**

```bash
# Good: Specific pattern
list_files path="src" pattern="*.py"

# Good: Smaller scope
list_files path="src/components" pattern="*"

# Caution: May timeout on large projects
list_files path="." pattern="*"
```

**Performance Indicators:**

The system will show performance information:
- ⚠️ **Limited to 1000 items for performance**
- 📊 **Total found: 2500** (showing first 1000)
- 🕐 **Operation completed in 45.2s**

**Advanced Configuration:**

For very large projects, you can create a custom configuration:

```python
# .mcp/config.json
{
  "limits": {
    "max_files_to_index": 5000,
    "max_file_size": 20971520  // 20MB
  },
  "timeouts": {
    "mcp_request_timeout": 180,  // 3 minutes
    "file_operation_timeout": 120
  }
}
```
