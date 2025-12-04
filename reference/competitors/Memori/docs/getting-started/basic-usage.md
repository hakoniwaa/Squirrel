# Basic Usage

Learn Memori's core concepts with practical examples.

## Core Concepts

### Memory Types

| Type | Purpose | Example |
|------|---------|---------|
| **Facts** | Objective information | "I use PostgreSQL for databases" |
| **Preferences** | User choices | "I prefer clean, readable code" |
| **Skills** | Abilities & knowledge | "Experienced with FastAPI" |
| **Rules** | Constraints & guidelines | "Always write tests first" |
| **Context** | Session information | "Working on e-commerce project" |

### Memory Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Conscious Ingest** | One-shot working memory injection | Quick access to essential info |
| **Auto Ingest** | Dynamic database search per query | Context-aware conversations |
| **Manual** | Explicit memory operations | Full control over memory |

### How It Works

```mermaid
graph LR
    A[LLM Conversation] --> B[Universal Recording]
    B --> C[Memory Agent Processing]
    C --> D[Structured Storage]
    D --> E[Context Injection]
    E --> A
```

1. **Universal Recording**: All LLM conversations automatically captured
2. **Memory Processing**: Pydantic-based entity extraction and categorization  
3. **Structured Storage**: Organized in SQLite/PostgreSQL/MySQL
4. **Context Injection**: Relevant memories added to future conversations

## Simple Example

```python
from memori import Memori

# Initialize with conscious ingestion (recommended)
memori = Memori(
    database_connect="sqlite:///my_project.db",
    conscious_ingest=True,  # Enable intelligent context injection
    auto_ingest=False,      # Optional: dynamic memory search
    openai_api_key="sk-..."
)

# Enable recording
memori.enable()

# Use any LLM library
from litellm import completion

# Establish preferences
completion(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": "I'm a Python developer who prefers clean, well-documented code"
    }]
)

# Later conversation - preferences remembered
completion(
    model="gpt-4o-mini", 
    messages=[{
        "role": "user",
        "content": "Help me write a function to validate emails"
    }]
)
# Response will include clean code with documentation!
```

## Memory Modes Explained

### Conscious Ingest Mode
```python
memori = Memori(conscious_ingest=True)
```
- **One-shot injection**: Essential memories injected once at conversation start
- **Background analysis**: AI analyzes patterns every 6 hours
- **Working memory**: Like human short-term memory for immediate access
- **Performance**: Minimal token usage, fast response times

### Auto Ingest Mode
```python
memori = Memori(auto_ingest=True)
```
- **Dynamic search**: Analyzes each query for relevant memories
- **Full database search**: Searches entire memory database
- **Context-aware**: Injects 3-5 most relevant memories per call
- **Performance**: Higher token usage, intelligent context

## Manual Memory Operations

### Record Conversations
```python
# Manual conversation recording
chat_id = memori.record_conversation(
    user_input="I'm learning machine learning",
    ai_output="Start with Python basics and scikit-learn...",
    model="gpt-4o-mini"
)

# Trigger conscious analysis manually
memori.trigger_conscious_analysis()
```

## Configuration Options

### Basic Configuration
```python
memori = Memori(
    database_connect="sqlite:///memori.db",  # Database connection
    conscious_ingest=True,                   # Enable smart context injection
    auto_ingest=False,                       # Disable dynamic search
    namespace="default",                     # Memory namespace
    openai_api_key="sk-..."                 # OpenAI API key
)
```

### Advanced Configuration
```python
memori = Memori(
    database_connect="postgresql://user:pass@localhost/memori",
    template="basic",
    conscious_ingest=True,
    auto_ingest=True,                        # Enable both modes
    namespace="web_project", 
    shared_memory=False,
    memory_filters={
        "importance_threshold": 0.4,
        "categories": ["fact", "preference", "skill"]
    },
    openai_api_key="sk-..."
)
```

### Provider Configuration
```python
from memori.core.providers import ProviderConfig

# Azure OpenAI
azure_provider = ProviderConfig.from_azure(
    api_key="your-azure-key",
    azure_endpoint="https://your-resource.openai.azure.com/",
    azure_deployment="gpt-4o",
    api_version="2024-12-01-preview"
)

memori = Memori(
    database_connect="sqlite:///azure_memory.db",
    provider_config=azure_provider,
    conscious_ingest=True
)
```

## Memory Namespaces

Separate memories for different projects:

```python
# Work project memory
work_memori = Memori(namespace="work_project")
work_memori.enable()

# Personal project memory  
personal_memori = Memori(namespace="personal")
personal_memori.enable()

# Each maintains separate memory context
```

## Integration Examples

### OpenAI Direct
```python
import openai

memori.enable()  # Records all OpenAI calls

client = openai.OpenAI()
response = client.chat.completions.create(...)
# Automatically recorded with context injection
```

### Anthropic Direct
```python
import anthropic

memori.enable()  # Records all Anthropic calls

client = anthropic.Anthropic()
response = client.messages.create(...)
# Automatically recorded with context injection
```

### LiteLLM (Recommended)
```python
from litellm import completion

memori.enable()  # Uses native LiteLLM callbacks

completion(model="gpt-4", messages=[...])
completion(model="claude-3", messages=[...]) 
completion(model="gemini-pro", messages=[...])
# All providers automatically supported
```

## Memory Search Tools

### Function Calling Integration
```python
from memori import create_memory_tool

# Create search tool for AI agents
memory_tool = create_memory_tool(memori)

# Use in function calling frameworks
def search_memory(query: str) -> str:
    """Search agent's memory for past conversations"""
    result = memory_tool.execute(query=query)
    return str(result) if result else "No relevant memories found"

# Use with LLM function calling
response = completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What did I say about testing?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search memory for relevant past conversations",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    }]
)
```

### Direct Search
```python
# Search by content
memories = memori.retrieve_context("machine learning", limit=5)

# Get all memories
all_memories = memori.get_memories(limit=10)

# Memory statistics
stats = memori.get_memory_stats()
print(f"Total conversations: {stats['chat_history_count']}")
print(f"Long-term memories: {stats['long_term_count']}")
```

## Best Practices

### 1. Choose the Right Memory Mode
```python
# For immediate context and essential info
memori = Memori(conscious_ingest=True, auto_ingest=False)

# For intelligent, context-aware conversations
memori = Memori(conscious_ingest=True, auto_ingest=True)

# For maximum control
memori = Memori(conscious_ingest=False, auto_ingest=False)
```

### 2. Use Namespaces for Organization
```python
# Separate memories by project/context
work = Memori(namespace="work_project")
personal = Memori(namespace="personal_assistant")
research = Memori(namespace="research_project")
```

### 3. Configure for Your Use Case
```python
# Performance-focused
memori = Memori(
    conscious_ingest=True,
    auto_ingest=False,  # Reduce token usage
    memory_filters={"importance_threshold": 0.5}
)

# Context-rich conversations
memori = Memori(
    conscious_ingest=True,
    auto_ingest=True,   # Enable dynamic search
    memory_filters={"importance_threshold": 0.3}
)
```

### 4. Use Configuration Files
```python
from memori import ConfigManager

config = ConfigManager()
config.auto_load()  # Loads from memori.json, env vars

memori = Memori()  # Uses loaded config
memori.enable()
```

### 5. Monitor Memory Usage
```python
stats = memori.get_memory_stats()
print(f"Conversations: {stats.get('chat_history_count', 0)}")
print(f"Short-term: {stats.get('short_term_count', 0)}")
print(f"Long-term: {stats.get('long_term_count', 0)}")

# Trigger cleanup if needed
if stats.get('short_term_count', 0) > 1000:
    memori.trigger_conscious_analysis()
```

## Troubleshooting

### Memory Not Recording
```python
# Check if enabled
if not memori._enabled:
    memori.enable()

# Verify API key configuration
config_info = memori.memory_manager.get_config_info() if hasattr(memori, 'memory_manager') else {}
print(f"Configuration loaded: {config_info}")

# Check conscious ingestion
print(f"Conscious ingest: {memori.conscious_ingest}")
print(f"Auto ingest: {memori.auto_ingest}")
```

### Context Not Injecting
```python
# Ensure conscious_ingest is enabled
memori = Memori(conscious_ingest=True)

# Check for relevant memories
memories = memori.retrieve_context("your query", limit=3)
print(f"Found {len(memories)} relevant memories")

# Manually trigger conscious analysis
memori.trigger_conscious_analysis()
```

### Performance Issues
```python
# Check memory statistics
stats = memori.get_memory_stats()
print(f"Total memories: {stats.get('total_memories', 0)}")

# Optimize settings for performance
memori = Memori(
    conscious_ingest=True,
    auto_ingest=False,  # Disable if not needed
    memory_filters={"importance_threshold": 0.5}  # Higher threshold
)
```

### Database Issues
```python
# Test database connection
try:
    stats = memori.get_memory_stats()
    print("Database connection OK")
    print(f"Database URL: {memori.database_connect}")
except Exception as e:
    print(f"Database error: {e}")
    
# Check database path for SQLite
import os
if memori.database_connect.startswith("sqlite:///"):
    db_path = memori.database_connect.replace("sqlite:///", "")
    print(f"Database file exists: {os.path.exists(db_path)}")
```