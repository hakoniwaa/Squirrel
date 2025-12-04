# ⚙️ Claude Cache Configuration Guide

Complete guide to configuring Claude Cache for your specific needs.

## Table of Contents
1. [Quick Configuration](#quick-configuration)
2. [Environment Variables](#environment-variables)
3. [Configuration Files](#configuration-files)
4. [MCP Server Setup](#mcp-server-setup)
5. [Database Settings](#database-settings)
6. [Search Configuration](#search-configuration)
7. [Learning Parameters](#learning-parameters)
8. [Performance Tuning](#performance-tuning)
9. [Privacy & Security](#privacy--security)
10. [Advanced Options](#advanced-options)

---

## Quick Configuration

### Minimal Setup (Just Works)
```bash
# Install and run - zero configuration needed
pip install claude-cache
cache start
```

### Recommended Setup
```bash
# Install with all features
pip install "claude-cache[mcp]"

# Create configuration
cat > ~/.claude/config.yml << EOF
learning:
  confidence_threshold: 0.8
  auto_capture: true
search:
  mode: semantic
  limit: 10
monitoring:
  watch_interval: 1
EOF

# Start with configuration
cache start --config ~/.claude/config.yml
```

---

## Environment Variables

### Core Settings

```bash
# Cache directory location (default: ~/.claude)
export CLAUDE_CACHE_DIR="$HOME/.claude"

# Knowledge database path
export CLAUDE_CACHE_DB="$HOME/.claude/knowledge/cache.db"

# Log level (DEBUG, INFO, WARNING, ERROR)
export CLAUDE_CACHE_LOG_LEVEL="INFO"

# Disable colored output
export NO_COLOR=1
```

### Search Settings

```bash
# Search mode (semantic, keyword, hybrid)
export CLAUDE_CACHE_SEARCH_MODE="semantic"

# Disable semantic search (use keyword only)
export CLAUDE_CACHE_SEMANTIC="false"

# Default search result limit
export CLAUDE_CACHE_SEARCH_LIMIT="5"

# Minimum confidence for results
export CLAUDE_CACHE_MIN_CONFIDENCE="0.6"
```

### Learning Settings

```bash
# Auto-capture patterns from conversations
export CLAUDE_CACHE_AUTO_LEARN="true"

# Confidence threshold for auto-capture
export CLAUDE_CACHE_CONFIDENCE_THRESHOLD="0.8"

# Pattern quality thresholds
export CLAUDE_CACHE_GOLD_THRESHOLD="0.95"
export CLAUDE_CACHE_SILVER_THRESHOLD="0.85"
export CLAUDE_CACHE_BRONZE_THRESHOLD="0.70"

# Anti-pattern detection sensitivity
export CLAUDE_CACHE_ANTI_PATTERN_THRESHOLD="0.90"
```

### Performance Settings

```bash
# Maximum patterns to process per session
export CLAUDE_CACHE_MAX_PATTERNS="1000"

# Database connection pool size
export CLAUDE_CACHE_POOL_SIZE="5"

# Search timeout (milliseconds)
export CLAUDE_CACHE_SEARCH_TIMEOUT="500"

# Background process nice level
export CLAUDE_CACHE_NICE_LEVEL="10"
```

---

## Configuration Files

### YAML Configuration (~/.claude/config.yml)

```yaml
# Complete configuration example
version: 1.0

# Core settings
core:
  cache_dir: ~/.claude
  database: ~/.claude/knowledge/cache.db
  log_level: INFO
  color_output: true

# Learning engine
learning:
  # Pattern detection
  auto_capture: true
  confidence_threshold: 0.8

  # Pattern classification thresholds
  gold_threshold: 0.95
  silver_threshold: 0.85
  bronze_threshold: 0.70
  anti_pattern_threshold: 0.90

  # Success signals
  success_signals:
    - "perfect"
    - "works"
    - "solved"
    - "excellent"
    - "thanks"

  # Failure signals
  failure_signals:
    - "failed"
    - "broken"
    - "doesn't work"
    - "error"
    - "wrong"

  # Journey detection
  journey_min_attempts: 3
  journey_time_window: 3600  # seconds

# Search configuration
search:
  # Mode: semantic, keyword, hybrid
  mode: semantic

  # Result settings
  default_limit: 5
  max_limit: 50
  min_confidence: 0.6

  # Semantic search
  semantic:
    model: all-MiniLM-L6-v2
    dimensions: 384
    similarity_threshold: 0.7

  # Keyword search
  keyword:
    algorithm: tfidf
    min_term_frequency: 2
    max_document_frequency: 0.8

# Monitoring settings
monitoring:
  # File watching
  watch_interval: 1  # seconds
  watch_directories:
    - ~/.claude/projects

  # Incremental processing
  incremental: true
  state_file: ~/.claude/state/processor_state.json

  # Pattern detection
  batch_size: 100
  max_queue_size: 1000

# Database settings
database:
  # Connection
  connection_timeout: 5
  pool_size: 5

  # Optimization
  vacuum_on_startup: false
  analyze_on_startup: true

  # Backup
  backup_enabled: true
  backup_interval: 86400  # daily
  backup_retention: 7  # days

# MCP server settings
mcp:
  enabled: true
  transport: stdio
  log_file: /tmp/cache-mcp.log

  # Tool availability
  tools:
    query: true
    learn: true
    suggest: true
    stats: true
    browse: true

# Privacy settings
privacy:
  # Local only - no external connections
  local_only: true

  # No telemetry
  telemetry_enabled: false

  # Pattern filtering
  filter_secrets: true
  secret_patterns:
    - "api[_-]?key"
    - "secret[_-]?key"
    - "password"
    - "token"
    - "bearer"

# Performance tuning
performance:
  # Processing
  max_patterns_per_session: 1000
  max_file_size_mb: 100

  # Memory limits
  max_memory_mb: 500
  gc_threshold: 100  # MB

  # Threading
  worker_threads: 4
  queue_size: 1000

  # Caching
  cache_size: 100
  cache_ttl: 3600  # seconds
```

### JSON Configuration (~/.claude/config.json)

```json
{
  "version": "1.0",
  "learning": {
    "auto_capture": true,
    "confidence_threshold": 0.8,
    "pattern_classification": {
      "gold": 0.95,
      "silver": 0.85,
      "bronze": 0.70
    }
  },
  "search": {
    "mode": "semantic",
    "limit": 10,
    "min_confidence": 0.6
  },
  "monitoring": {
    "watch_interval": 1,
    "incremental": true
  }
}
```

### Project Configuration (.claude.json)

```json
{
  "mcpServers": {
    "cache": {
      "type": "stdio",
      "command": "cache-mcp",
      "args": ["--config", ".claude/config.yml"]
    }
  },
  "cache": {
    "project_name": "my-app",
    "tags": ["react", "typescript", "nextjs"],
    "exclude_patterns": [
      "node_modules",
      "dist",
      "build"
    ],
    "custom_signals": {
      "success": ["ship it", "lgtm"],
      "failure": ["revert", "rollback"]
    }
  }
}
```

---

## MCP Server Setup

### Basic MCP Configuration

```json
// .claude.json
{
  "mcpServers": {
    "cache": {
      "type": "stdio",
      "command": "cache-mcp"
    }
  }
}
```

### Advanced MCP Configuration

```json
// .claude.json
{
  "mcpServers": {
    "cache": {
      "type": "stdio",
      "command": "cache-mcp",
      "args": [
        "--config", "~/.claude/config.yml",
        "--log-file", "/tmp/cache-mcp.log",
        "--verbose"
      ],
      "env": {
        "CLAUDE_CACHE_SEARCH_MODE": "semantic",
        "CLAUDE_CACHE_AUTO_LEARN": "true"
      }
    }
  }
}
```

### MCP Server Options

```bash
# Start MCP server with options
cache-mcp \
  --config ~/.claude/config.yml \
  --log-file /tmp/cache-mcp.log \
  --verbose \
  --port 8080  # For HTTP transport
```

---

## Database Settings

### SQLite Optimization

```yaml
# config.yml
database:
  # Performance settings
  pragma:
    journal_mode: WAL
    synchronous: NORMAL
    cache_size: -64000  # 64MB
    temp_store: MEMORY
    mmap_size: 268435456  # 256MB

  # Maintenance
  vacuum_interval: 604800  # Weekly
  analyze_interval: 86400  # Daily
  checkpoint_interval: 3600  # Hourly
```

### Database Migration

```bash
# Backup before migration
cache db backup ~/claude-cache-backup.db

# Export patterns
cache export --format json > patterns.json

# Reset database (if needed)
cache db reset --confirm

# Import patterns
cache import patterns.json
```

### Database Maintenance

```bash
# Optimize database
cache db optimize

# Vacuum database
cache db vacuum

# Analyze statistics
cache db analyze

# Check integrity
cache db check
```

---

## Search Configuration

### Semantic Search Tuning

```yaml
# config.yml
search:
  semantic:
    # Model selection
    model: all-MiniLM-L6-v2  # Fast, good quality
    # model: all-mpnet-base-v2  # Slower, better quality
    # model: multi-qa-MiniLM-L6-cos-v1  # Question answering

    # Similarity settings
    similarity_metric: cosine
    similarity_threshold: 0.7

    # Performance
    batch_size: 32
    cache_embeddings: true
    embedding_cache_size: 10000
```

### Keyword Search Tuning

```yaml
# config.yml
search:
  keyword:
    # TF-IDF parameters
    min_term_frequency: 2
    max_document_frequency: 0.8
    use_idf: true
    sublinear_tf: true

    # Tokenization
    tokenizer: simple
    lowercase: true
    remove_stopwords: true
    stem_words: false
```

### Hybrid Search Configuration

```yaml
# config.yml
search:
  mode: hybrid
  hybrid:
    # Weight distribution
    semantic_weight: 0.7
    keyword_weight: 0.3

    # Fallback strategy
    fallback_to_keyword: true
    min_semantic_results: 3
```

---

## Learning Parameters

### Pattern Quality Configuration

```yaml
# config.yml
learning:
  # Quality thresholds
  quality:
    gold:
      min_confidence: 0.95
      max_attempts: 1
      success_rate: 1.0

    silver:
      min_confidence: 0.85
      max_attempts: 3
      success_rate: 0.8

    bronze:
      min_confidence: 0.70
      max_attempts: 5
      success_rate: 0.6

    anti_pattern:
      failure_rate: 0.9
      min_occurrences: 2

    journey:
      min_attempts: 3
      completion_required: true
```

### Auto-Learning Rules

```yaml
# config.yml
learning:
  rules:
    # Capture conditions
    capture:
      min_conversation_length: 3
      require_tool_calls: true
      require_success_signal: false

    # Ignore conditions
    ignore:
      patterns_containing:
        - "test"
        - "debug"
        - "tmp"
        - "todo"

      projects:
        - "sandbox"
        - "playground"
```

### Context Detection

```yaml
# config.yml
learning:
  context:
    # Auto-detect from files
    detect_framework: true
    detect_language: true
    detect_dependencies: true

    # Context sources
    sources:
      - package.json
      - requirements.txt
      - Gemfile
      - go.mod
      - Cargo.toml
```

---

## Performance Tuning

### Memory Optimization

```yaml
# config.yml
performance:
  memory:
    # Limits
    max_heap_mb: 512
    max_patterns_in_memory: 1000

    # Garbage collection
    gc_enabled: true
    gc_interval: 300  # seconds
    gc_threshold_mb: 100

    # Caching
    pattern_cache_size: 500
    embedding_cache_size: 1000
    search_cache_ttl: 3600
```

### Processing Optimization

```yaml
# config.yml
performance:
  processing:
    # Batch processing
    batch_size: 100
    max_batch_wait_ms: 1000

    # Parallel processing
    worker_threads: 4
    queue_size: 1000

    # Rate limiting
    max_patterns_per_minute: 600
    max_files_per_minute: 60
```

### Network Optimization (MCP)

```yaml
# config.yml
mcp:
  performance:
    # Connection pooling
    connection_pool_size: 10
    connection_timeout_ms: 5000

    # Request handling
    max_concurrent_requests: 20
    request_timeout_ms: 10000

    # Response caching
    cache_responses: true
    cache_ttl_seconds: 300
```

---

## Privacy & Security

### Secret Filtering

```yaml
# config.yml
privacy:
  # Filter sensitive data
  filter:
    enabled: true

    # Patterns to redact
    redact_patterns:
      - regex: 'api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]+'
        replacement: "API_KEY_REDACTED"
      - regex: 'password["\']?\s*[:=]\s*["\']?[^"\'\\s]+'
        replacement: "PASSWORD_REDACTED"
      - regex: 'token["\']?\s*[:=]\s*["\']?[\w-]+'
        replacement: "TOKEN_REDACTED"

    # Files to skip
    skip_files:
      - .env
      - .env.local
      - secrets.yml
      - credentials.json
```

### Data Isolation

```yaml
# config.yml
privacy:
  isolation:
    # Project isolation
    isolate_projects: true
    cross_project_sharing: false

    # User isolation
    user_specific_db: true
    shared_patterns_opt_in: false
```

### Audit Logging

```yaml
# config.yml
privacy:
  audit:
    enabled: true
    log_file: ~/.claude/audit.log

    # What to log
    log_pattern_creation: true
    log_pattern_access: true
    log_exports: true
    log_imports: true
```

---

## Advanced Options

### Custom Pattern Detectors

```python
# ~/.claude/custom_detectors.py
class CustomSuccessDetector:
    def detect(self, message):
        custom_signals = ["ship it", "deployed", "merged"]
        return any(signal in message.lower()
                  for signal in custom_signals)

# Register in config
```

```yaml
# config.yml
advanced:
  custom_detectors:
    - module: ~/.claude/custom_detectors.py
      class: CustomSuccessDetector
      type: success
```

### Plugin System

```yaml
# config.yml
plugins:
  enabled: true
  directory: ~/.claude/plugins

  # Load specific plugins
  load:
    - name: jira_integration
      config:
        api_url: https://company.atlassian.net
        project_key: PROJ

    - name: slack_notifier
      config:
        webhook_url: ${SLACK_WEBHOOK_URL}
        notify_on: ["gold_pattern", "anti_pattern"]
```

### Export/Import Configuration

```bash
# Export all settings
cache config export > my-config.yml

# Import configuration
cache config import my-config.yml

# Validate configuration
cache config validate ~/.claude/config.yml

# Show effective configuration (with defaults)
cache config show --effective
```

### Debugging Configuration

```bash
# Test configuration
cache config test

# Show configuration problems
cache config diagnose

# Debug specific component
cache debug --component search --verbose
cache debug --component learning --trace
```

---

## Configuration Best Practices

### 1. Start Simple
```yaml
# Minimal config for most users
learning:
  auto_capture: true
search:
  mode: semantic
```

### 2. Tune for Your Workflow
```yaml
# For heavy debugging work
learning:
  failure_signals: ["bug", "broken", "error", "crash"]
  anti_pattern_threshold: 0.85

# For feature development
learning:
  success_signals: ["works", "done", "complete"]
  journey_min_attempts: 2
```

### 3. Optimize for Performance
```yaml
# For large codebases
performance:
  worker_threads: 8
  batch_size: 200
database:
  cache_size: -128000  # 128MB
```

### 4. Maintain Privacy
```yaml
# For sensitive projects
privacy:
  filter_secrets: true
  local_only: true
  audit:
    enabled: true
```

---

## Troubleshooting Configuration

### Common Issues

```bash
# Configuration not loading
cache config validate
# Shows: "Error on line 23: invalid key 'databse'"

# Wrong search mode
cache config get search.mode
# Shows: "keyword" when expecting "semantic"

# Performance issues
cache config recommend --optimize
# Suggests optimal settings based on usage
```

### Reset Configuration

```bash
# Reset to defaults
cache config reset

# Reset specific section
cache config reset search

# Create fresh configuration
cache config init --interactive
```

---

## Environment-Specific Configurations

### Development
```bash
export CLAUDE_CACHE_ENV=development
# Uses ~/.claude/config.dev.yml
```

### Production
```bash
export CLAUDE_CACHE_ENV=production
# Uses ~/.claude/config.prod.yml
```

### Testing
```bash
export CLAUDE_CACHE_ENV=test
# Uses in-memory database, no persistence
```

---

## Quick Reference Card

### Essential Environment Variables
```bash
CLAUDE_CACHE_DIR          # Cache directory
CLAUDE_CACHE_SEARCH_MODE  # semantic|keyword|hybrid
CLAUDE_CACHE_AUTO_LEARN   # true|false
CLAUDE_CACHE_LOG_LEVEL    # DEBUG|INFO|WARNING|ERROR
```

### Essential Config Keys
```yaml
learning.auto_capture     # Enable auto-learning
search.mode              # Search algorithm
search.limit             # Result count
monitoring.watch_interval # Check frequency
database.cache_size      # SQLite cache
```

### Essential Commands
```bash
cache config validate    # Check configuration
cache config show       # Display current config
cache config test       # Test configuration
cache start --config    # Use specific config
```

---

*For quick setup, see [QUICK_START.md](QUICK_START.md)*
*For detailed usage, see [HOW_IT_WORKS.md](HOW_IT_WORKS.md)*
*For examples, see [USE_CASES.md](USE_CASES.md)*