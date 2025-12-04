# Configuration

Comprehensive guide to configuring Memori for your needs.

## Configuration Methods

### 1. Direct Configuration
```python
from memori import Memori

memori = Memori(
    database_connect="sqlite:///memori.db",
    conscious_ingest=True,
    auto_ingest=True,
    openai_api_key="sk-..."
)
```

### 2. Configuration File
Create `memori.json`:
```json
{
  "database": {
    "connection_string": "sqlite:///memori_example.db",
    "database_type": "sqlite",
    "pool_size": 5,
    "echo_sql": false,
    "migration_auto": true,
    "backup_enabled": false
  },
  "agents": {
    "openai_api_key": "sk-your-openai-key-here",
    "default_model": "gpt-4o-mini",
    "fallback_model": "gpt-3.5-turbo",
    "conscious_ingest": true,
    "max_tokens": 2000,
    "temperature": 0.1,
    "timeout_seconds": 30,
    "retry_attempts": 3
  },
  "memory": {
    "namespace": "example_project",
    "shared_memory": false,
    "retention_policy": "30_days",
    "auto_cleanup": true,
    "importance_threshold": 0.3,
    "context_limit": 3,
    "context_injection": true,
    "max_short_term_memories": 1000
  },
  "logging": {
    "level": "INFO",
    "log_to_file": false,
    "structured_logging": false
  },
  "integrations": {
    "litellm_enabled": true,
    "auto_enable_on_import": false
  }
}
```

```python
from memori import ConfigManager, Memori

# Recommended approach using ConfigManager
config = ConfigManager()
config.auto_load()  # Loads memori.json automatically

memori = Memori()  # Uses loaded configuration
memori.enable()
```

### 3. Provider Configuration with Azure/Custom Endpoints
For Azure OpenAI, custom endpoints, or advanced provider configurations:

```python
from memori import Memori
from memori.core.providers import ProviderConfig

# Azure OpenAI Configuration
azure_provider = ProviderConfig.from_azure(
    api_key="your-azure-openai-api-key",
    azure_endpoint="https://your-resource.openai.azure.com/",
    azure_deployment="gpt-4o",
    api_version="2024-12-01-preview",
    model="gpt-4o"
)

memori = Memori(
    database_connect="sqlite:///azure_memory.db",
    provider_config=azure_provider,
    conscious_ingest=True,
    namespace="azure_project"
)
memori.enable()
```

### 4. Environment Variables
```bash
export MEMORI_AGENTS__OPENAI_API_KEY="sk-..."
export MEMORI_DATABASE__CONNECTION_STRING="postgresql://..."
export MEMORI_MEMORY__NAMESPACE="production"
export MEMORI_LOGGING__LEVEL="INFO"
export MEMORI_DATABASE__POOL_SIZE="20"
export MEMORI_MEMORY__AUTO_CLEANUP="true"
```

```python
from memori import ConfigManager, Memori

config = ConfigManager()
config.load_from_env()

memori = Memori()
memori.enable()
```

## Configuration Sections

### Database Settings

```python
database = {
    "connection_string": "sqlite:///memori.db",
    "database_type": "sqlite",  # sqlite, postgresql, mysql
    "template": "basic",
    "pool_size": 10,
    "echo_sql": False,
    "migration_auto": True,
    "backup_enabled": False,
    "backup_interval_hours": 24
}
```

#### Connection Strings
```python
# SQLite (recommended for development)
"sqlite:///path/to/database.db"

# PostgreSQL (recommended for production)
"postgresql://user:password@localhost:5432/memori"

# MySQL
"mysql://user:password@localhost:3306/memori"

# Cloud Databases
"postgresql://user:pass@neon-host:5432/memori"  # Neon
"postgresql://user:pass@supabase-host:5432/memori"  # Supabase
```

### Agent Settings

```python
agents = {
    "openai_api_key": "sk-...",
    "default_model": "gpt-4o-mini",  # Updated default model
    "fallback_model": "gpt-3.5-turbo", 
    "max_tokens": 2000,
    "temperature": 0.1,
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "conscious_ingest": True
}
```

#### Supported Models
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`
- **Azure OpenAI**: Any deployed model name
- **LiteLLM**: Any supported model from 100+ providers
- **Custom endpoints**: Any compatible model

### Memory Settings

```python
memory = {
    "namespace": "default",
    "shared_memory": False,
    "retention_policy": "30_days",  # 7_days, 30_days, 90_days, permanent
    "auto_cleanup": True,
    "cleanup_interval_hours": 24,
    "importance_threshold": 0.3,
    "max_short_term_memories": 1000,
    "max_long_term_memories": 10000,
    "context_injection": True,
    "context_limit": 3
}
```

#### Memory Features
- **Conscious Ingest**: Intelligent filtering of memory-worthy content
- **Auto Ingest**: Automatic memory recording for all conversations
- **Namespace Isolation**: Separate memory spaces for different projects
- **Retention Policies**: Automatic cleanup based on time or importance
- **Context Injection**: Relevant memories injected into conversations

### Logging Settings

```python
logging = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "<green>{time}</green> | <level>{level}</level> | {message}",
    "log_to_file": False,
    "log_file_path": "logs/memori.log",
    "log_rotation": "10 MB",
    "log_retention": "30 days",
    "structured_logging": False
}
```

### Integration Settings

```python
integrations = {
    "litellm_enabled": True,
    "openai_wrapper_enabled": False,
    "anthropic_wrapper_enabled": False,
    "auto_enable_on_import": False,
    "callback_timeout": 5
}
```

#### Supported Integrations
- **LiteLLM**: Universal LLM wrapper (100+ providers)
- **OpenAI**: Direct OpenAI API integration
- **Anthropic**: Claude models integration
- **Azure AI Foundry**: Enterprise Azure AI platform
- **Custom**: Any OpenAI-compatible endpoint

## Configuration Manager

### Auto-Loading
```python
from memori import ConfigManager

config = ConfigManager()
config.auto_load()  # Loads from multiple sources in priority order
```

Priority (highest to lowest):
1. Environment variables (`MEMORI_*`)
2. `MEMORI_CONFIG_PATH` environment variable
3. `memori.json` in current directory
4. `memori.yaml`/`memori.yml` in current directory
5. `config/memori.json`
6. `config/memori.yaml`/`config/memori.yml`
7. `~/.memori/config.json`
8. `~/.memori/config.yaml`
9. `/etc/memori/config.json` (Linux/macOS)
10. Default settings

### Manual Configuration
```python
# Load from specific file
config.load_from_file("custom_config.json")

# Load from environment
config.load_from_env()

# Update specific setting
config.update_setting("database.pool_size", 20)

# Get setting value
db_url = config.get_setting("database.connection_string")

# Save configuration
config.save_to_file("memori_backup.json")

# Get configuration info
info = config.get_config_info()
print(f"Sources: {', '.join(info['sources'])}")
print(f"Debug mode: {info['debug_mode']}")
print(f"Production: {info['is_production']}")

# Validate configuration
is_valid = config.validate_configuration()
```

## Production Configuration

## Production Configuration

### Development
```json
{
  "database": {
    "connection_string": "sqlite:///dev_memori.db",
    "echo_sql": true
  },
  "agents": {
    "default_model": "gpt-4o-mini",
    "conscious_ingest": true
  },
  "memory": {
    "namespace": "development",
    "auto_cleanup": false
  },
  "logging": {
    "level": "DEBUG",
    "log_to_file": false
  },
  "debug": true,
  "verbose": true
}
```

### Production
```json
{
  "database": {
    "connection_string": "postgresql://user:pass@prod-db:5432/memori",
    "pool_size": 20,
    "backup_enabled": true,
    "migration_auto": true
  },
  "agents": {
    "default_model": "gpt-4o",
    "retry_attempts": 5,
    "timeout_seconds": 60
  },
  "memory": {
    "namespace": "production",
    "auto_cleanup": true,
    "importance_threshold": 0.4,
    "max_short_term_memories": 5000
  },
  "logging": {
    "level": "INFO",
    "log_to_file": true,
    "log_file_path": "/var/log/memori/memori.log",
    "structured_logging": true
  },
  "integrations": {
    "litellm_enabled": true
  },
  "debug": false,
  "verbose": false
}
```

### Docker Environment
```dockerfile
# Basic configuration
ENV MEMORI_DATABASE__CONNECTION_STRING="postgresql://user:pass@db:5432/memori"
ENV MEMORI_AGENTS__OPENAI_API_KEY="sk-..."
ENV MEMORI_MEMORY__NAMESPACE="production"
ENV MEMORI_LOGGING__LEVEL="INFO"
ENV MEMORI_LOGGING__LOG_TO_FILE="true"

# Performance tuning
ENV MEMORI_DATABASE__POOL_SIZE="50"
ENV MEMORI_MEMORY__IMPORTANCE_THRESHOLD="0.4"
ENV MEMORI_AGENTS__RETRY_ATTEMPTS="5"
```

### Azure Container Apps
```yaml
# Environment variables for Azure deployment
- name: MEMORI_DATABASE__CONNECTION_STRING
  value: "postgresql://user:pass@azure-postgres:5432/memori"
- name: MEMORI_AGENTS__OPENAI_API_KEY
  secretRef: openai-api-key
- name: MEMORI_MEMORY__NAMESPACE
  value: "azure-production"
- name: MEMORI_INTEGRATIONS__LITELLM_ENABLED
  value: "true"
```

## Configuration Examples

## Configuration Examples

### Multi-Project Setup
```python
from memori import ConfigManager, Memori

# Project A
config_a = ConfigManager()
config_a.update_setting("memory.namespace", "project_a")
config_a.update_setting("database.connection_string", "sqlite:///project_a.db")
memori_a = Memori()
memori_a.enable()

# Project B  
config_b = ConfigManager()
config_b.update_setting("memory.namespace", "project_b")
config_b.update_setting("database.connection_string", "sqlite:///project_b.db")
memori_b = Memori()
memori_b.enable()
```

### Azure AI Foundry Integration
```python
from memori import Memori
from memori.core.providers import ProviderConfig

# Azure provider configuration
azure_provider = ProviderConfig.from_azure(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
    api_version="2024-12-01-preview",
    model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
)

memory_system = Memori(
    database_connect="sqlite:///azure_ai_foundry_memory.db",
    conscious_ingest=True,
    auto_ingest=True,
    provider_config=azure_provider,
    namespace="azure_ai_foundry_example"
)
memory_system.enable()
```

### High-Performance Setup
```json
{
  "database": {
    "connection_string": "postgresql://user:pass@high-perf-db:5432/memori",
    "pool_size": 50,
    "migration_auto": true
  },
  "memory": {
    "importance_threshold": 0.5,
    "max_short_term_memories": 5000,
    "max_long_term_memories": 50000,
    "context_limit": 5,
    "auto_cleanup": true
  },
  "agents": {
    "default_model": "gpt-4o",
    "max_tokens": 4000,
    "retry_attempts": 2,
    "timeout_seconds": 60
  },
  "integrations": {
    "litellm_enabled": true,
    "callback_timeout": 10
  }
}
```

### Cloud-Native Setup (Neon + Vercel)
```json
{
  "database": {
    "connection_string": "postgresql://user:pass@neon-serverless:5432/memori",
    "pool_size": 1,
    "migration_auto": true
  },
  "memory": {
    "namespace": "vercel-production",
    "retention_policy": "90_days",
    "auto_cleanup": true
  },
  "logging": {
    "level": "INFO",
    "structured_logging": true
  }
}
```

### Memory Tools Integration
```python
from memori import Memori, create_memory_tool

# Initialize Memori with tool support
memori = Memori(
    database_connect="sqlite:///tool_memory.db",
    conscious_ingest=True,
    auto_ingest=True,
    namespace="tool_integration"
)
memori.enable()

# Create memory tool for AI agents/frameworks
memory_tool = create_memory_tool(memori)

# Use with function calling frameworks
def search_memory(query: str) -> str:
    """Search agent's memory for past conversations"""
    result = memory_tool.execute(query=query)
    return str(result) if result else "No relevant memories found"
```

### Security-Focused Setup
```json
{
  "database": {
    "connection_string": "postgresql://user:pass@secure-db:5432/memori?sslmode=require"
  },
  "logging": {
    "level": "WARNING",
    "structured_logging": true
  },
  "agents": {
    "timeout_seconds": 10
  }
}
```

## Environment Variables Reference

All configuration can be set via environment variables with the prefix `MEMORI_`:

```bash
# Database Configuration
export MEMORI_DATABASE__CONNECTION_STRING="sqlite:///memori.db"
export MEMORI_DATABASE__DATABASE_TYPE="sqlite"
export MEMORI_DATABASE__POOL_SIZE="10"
export MEMORI_DATABASE__ECHO_SQL="false"
export MEMORI_DATABASE__MIGRATION_AUTO="true"
export MEMORI_DATABASE__BACKUP_ENABLED="false"

# Agent Configuration
export MEMORI_AGENTS__OPENAI_API_KEY="sk-..."
export MEMORI_AGENTS__DEFAULT_MODEL="gpt-4o-mini"
export MEMORI_AGENTS__FALLBACK_MODEL="gpt-3.5-turbo"
export MEMORI_AGENTS__CONSCIOUS_INGEST="true"
export MEMORI_AGENTS__MAX_TOKENS="2000"
export MEMORI_AGENTS__TEMPERATURE="0.1"
export MEMORI_AGENTS__TIMEOUT_SECONDS="30"
export MEMORI_AGENTS__RETRY_ATTEMPTS="3"

# Memory Configuration
export MEMORI_MEMORY__NAMESPACE="production"
export MEMORI_MEMORY__SHARED_MEMORY="false"
export MEMORI_MEMORY__RETENTION_POLICY="30_days"
export MEMORI_MEMORY__AUTO_CLEANUP="true"
export MEMORI_MEMORY__IMPORTANCE_THRESHOLD="0.3"
export MEMORI_MEMORY__CONTEXT_LIMIT="3"
export MEMORI_MEMORY__CONTEXT_INJECTION="true"

# Logging Configuration
export MEMORI_LOGGING__LEVEL="INFO"
export MEMORI_LOGGING__LOG_TO_FILE="false"
export MEMORI_LOGGING__STRUCTURED_LOGGING="false"

# Integration Configuration
export MEMORI_INTEGRATIONS__LITELLM_ENABLED="true"
export MEMORI_INTEGRATIONS__AUTO_ENABLE_ON_IMPORT="false"

# Global Settings
export MEMORI_DEBUG="false"
export MEMORI_VERBOSE="false"
export MEMORI_VERSION="1.0.0"
```

## Configuration Schema

The complete configuration schema with all available options:

```json
{
  "version": "1.0.0",
  "debug": false,
  "verbose": false,
  "database": {
    "connection_string": "sqlite:///memori.db",
    "database_type": "sqlite",
    "template": "basic",
    "pool_size": 10,
    "echo_sql": false,
    "migration_auto": true,
    "backup_enabled": false,
    "backup_interval_hours": 24
  },
  "agents": {
    "openai_api_key": null,
    "default_model": "gpt-4o-mini",
    "fallback_model": "gpt-3.5-turbo",
    "max_tokens": 2000,
    "temperature": 0.1,
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "conscious_ingest": true
  },
  "memory": {
    "namespace": "default",
    "shared_memory": false,
    "retention_policy": "30_days",
    "auto_cleanup": true,
    "cleanup_interval_hours": 24,
    "importance_threshold": 0.3,
    "max_short_term_memories": 1000,
    "max_long_term_memories": 10000,
    "context_injection": true,
    "context_limit": 3
  },
  "logging": {
    "level": "INFO",
    "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | {message}",
    "log_to_file": false,
    "log_file_path": "logs/memori.log",
    "log_rotation": "10 MB",
    "log_retention": "30 days",
    "log_compression": "gz",
    "structured_logging": false
  },
  "integrations": {
    "litellm_enabled": true,
    "openai_wrapper_enabled": false,
    "anthropic_wrapper_enabled": false,
    "auto_enable_on_import": false,
    "callback_timeout": 5
  },
  "custom_settings": {}
}
```