# coder-mcp API Reference

## Table of Contents

- [Server API](#server-api)
- [Configuration API](#configuration-api)
- [Context API](#context-api)
- [Tool APIs](#tool-apis)
- [Analysis API](#analysis-api)
- [Template API](#template-api)

## Server API

### ModularMCPServer

Main server class that handles MCP protocol communication.

```python
class ModularMCPServer:
    def __init__(self, workspace_root: Optional[Path] = None)
```

#### Methods

##### initialize()
```python
async def initialize() -> None
```
Initialize all server components. Must be called before using the server.

**Raises:**
- `ConfigurationError`: If configuration is invalid
- `ProviderError`: If required providers cannot be initialized

##### run()
```python
async def run() -> None
```
Start the MCP server and listen for requests.

##### get_available_tools()
```python
def get_available_tools() -> List[Dict[str, Any]]
```
Get list of available tools with their schemas.

**Returns:**
```python
[
    {
        "name": "read_file",
        "description": "Read contents of a file",
        "inputSchema": {...}
    },
    ...
]
```

##### handle_tool_call()
```python
async def handle_tool_call(
    tool_name: str,
    arguments: Dict[str, Any]
) -> Dict[str, Any]
```
Execute a tool with given arguments.

**Parameters:**
- `tool_name`: Name of the tool to execute
- `arguments`: Tool-specific arguments

**Returns:**
- Tool-specific response dictionary

**Raises:**
- `ToolNotFoundError`: If tool doesn't exist
- `ValidationError`: If arguments are invalid
- `ExecutionError`: If tool execution fails

## Configuration API

### ConfigurationManager

```python
class ConfigurationManager:
    def __init__(self, env_file: Optional[Path] = None)
```

#### Methods

##### get_config()
```python
def get_config() -> MCPConfiguration
```
Get the current configuration.

##### validate_configuration()
```python
def validate_configuration() -> ValidationResult
```
Validate the current configuration.

**Returns:**
```python
{
    "valid": bool,
    "errors": List[str],
    "warnings": List[str]
}
```

##### update_config()
```python
def update_config(updates: Dict[str, Any]) -> None
```
Update configuration values.

### Configuration Models

#### MCPConfiguration
```python
class MCPConfiguration(BaseModel):
    server: ServerConfig
    providers: ProvidersConfig
    features: FeaturesConfig
    limits: LimitsConfig
```

#### ServerConfig
```python
class ServerConfig(BaseModel):
    name: str = "coder-mcp"
    version: str = "5.0.0"
    workspace_root: Path
    log_level: str = "INFO"
```

#### ProvidersConfig
```python
class ProvidersConfig(BaseModel):
    embedding: str = "openai"  # "openai" | "local"
    vector_store: str = "redis"  # "redis" | "local"
    cache: str = "redis"  # "redis" | "memory"
```

## Context API

### ContextManager

Manages project context and memory.

```python
class ContextManager:
    def __init__(
        self,
        workspace_root: Path,
        config_manager: ConfigurationManager
    )
```

#### Methods

##### initialize_context()
```python
async def initialize_context(force_refresh: bool = False) -> ContextInfo
```
Initialize or load project context.

**Returns:**
```python
{
    "files_indexed": int,
    "quality_score": float,
    "last_indexed": datetime,
    "file_types": Dict[str, int]
}
```

##### update_context()
```python
async def update_context(
    section: str,
    updates: Dict[str, Any]
) -> None
```
Update a specific section of context.

**Parameters:**
- `section`: One of ["structure", "dependencies", "quality_metrics", "patterns", "improvements_made", "known_issues"]
- `updates`: Section-specific updates

##### search_context()
```python
async def search_context(
    query: str,
    search_type: str = "all",
    limit: int = 10
) -> List[SearchResult]
```
Search through project context.

## Enhanced File Editing API

### EditingHandler

Provides advanced file editing capabilities with AI assistance and session management.

```python
class EditingHandler(BaseHandler):
    def __init__(
        self,
        config_manager: ConfigurationManager,
        context_manager: ContextManager
    )
```

#### Core Editing Methods

##### edit_file()
```python
async def edit_file(arguments: Dict[str, Any]) -> str
```
Enhanced file editing with multiple strategies.

**Parameters:**
```python
{
    "file_path": str,           # Path to the file to edit
    "edits": List[Edit],        # List of edits to apply
    "strategy": str,            # Default strategy: "pattern_based"
    "create_backup": bool,      # Create backup: True
    "validate_syntax": bool,    # Validate syntax: True
    "preview_only": bool        # Preview only: False
}
```

**Edit Types:**
- `line_based`: Direct line manipulation by line number
- `pattern_based`: Find and replace using exact text matching
- `ast_based`: Structural modifications using AST (Python only)

##### smart_edit()
```python
async def smart_edit(arguments: Dict[str, Any]) -> str
```
AI-powered editing using natural language instructions.

**Parameters:**
```python
{
    "file_path": str,           # Path to the file to edit
    "instruction": str,         # Natural language instruction
    "create_backup": bool,      # Create backup: True
    "preview_only": bool        # Preview only: False
}
```

**Common Instructions:**
- "add error handling"
- "add type hints"
- "add docstrings"
- "remove comments"
- "format code"
- "rename variable X to Y"

##### preview_edit()
```python
async def preview_edit(arguments: Dict[str, Any]) -> str
```
Preview changes without applying them.

**Parameters:**
```python
{
    "file_path": str,           # Path to the file
    "edit": Edit               # Single edit to preview
}
```

#### Session Management Methods

##### start_edit_session()
```python
async def start_edit_session(arguments: Dict[str, Any]) -> str
```
Start a new editing session with undo/redo capabilities.

**Parameters:**
```python
{
    "session_name": str,        # Unique session name
    "description": str          # Optional description
}
```

##### session_apply_edit()
```python
async def session_apply_edit(arguments: Dict[str, Any]) -> str
```
Apply an edit within a session.

**Parameters:**
```python
{
    "session_id": str,          # Session ID
    "file_path": str,           # Path to file
    "edit": Edit,               # Edit to apply
    "description": str          # Optional edit description
}
```

##### session_undo() / session_redo()
```python
async def session_undo(arguments: Dict[str, Any]) -> str
async def session_redo(arguments: Dict[str, Any]) -> str
```
Undo or redo the last edit in a session.

**Parameters:**
```python
{
    "session_id": str          # Session ID
}
```

##### list_edit_sessions()
```python
async def list_edit_sessions(arguments: Dict[str, Any]) -> str
```
List all active editing sessions.

**Parameters:**
```python
{
    "include_closed": bool     # Include closed sessions: False
}
```

##### close_edit_session()
```python
async def close_edit_session(arguments: Dict[str, Any]) -> str
```
Close an editing session and clean up resources.

**Parameters:**
```python
{
    "session_id": str,         # Session ID
    "cleanup_backups": bool    # Clean up backups: False
}
```

#### Analysis Methods

##### get_edit_suggestions()
```python
async def get_edit_suggestions(arguments: Dict[str, Any]) -> str
```
Get AI-powered suggestions for improving a file.

**Parameters:**
```python
{
    "file_path": str,                    # Path to file
    "focus_areas": List[str],            # Focus areas
    "max_suggestions": int               # Max suggestions: 5
}
```

**Focus Areas:**
- `performance`: Performance optimizations
- `readability`: Code clarity improvements
- `security`: Security vulnerability fixes
- `maintainability`: Code maintenance improvements
- `style`: Code style and formatting

### Edit Data Models

#### Edit
```python
{
    "type": str,               # "line_based" | "pattern_based" | "ast_based"
    "new_content": str,        # Content to insert/replace
    "old_content": str,        # Content to replace (pattern_based)
    "line_number": int,        # Target line (line_based)
    "start_line": int,         # Start line for range (line_based)
    "end_line": int           # End line for range (line_based)
}
```

#### EditResult
```python
{
    "success": bool,           # Whether edit succeeded
    "message": str,            # Result message
    "changes_made": int,       # Number of changes
    "backup_path": str,        # Path to backup file
    "preview_content": str     # Preview content (preview mode)
}
```

### Error Handling

The editing system provides comprehensive error handling:

**Common Errors:**
- `FileNotFoundError`: Target file doesn't exist
- `SyntaxError`: Invalid syntax after edit (when validation enabled)
- `PatternNotFoundError`: Pattern not found in file
- `SessionNotFoundError`: Edit session doesn't exist
- `BackupError`: Backup creation or restoration failed

**Error Response Format:**
```python
{
    "success": False,
    "error": str,              # Error type
    "message": str,            # Human-readable message
    "details": Dict[str, Any]  # Additional error details
}
```

**Parameters:**
- `query`: Search query
- `search_type`: One of ["context", "memories", "code", "all"]
- `limit`: Maximum results to return

**Returns:**
```python
[
    {
        "file_path": str,
        "content": str,
        "score": float,
        "metadata": Dict[str, Any]
    },
    ...
]
```

##### add_memory()
```python
async def add_memory(
    content: str,
    memory_type: str,
    tags: List[str] = None
) -> str
```
Add a memory/note about the project.

**Parameters:**
- `content`: Memory content
- `memory_type`: One of ["decision", "todo", "warning", "insight", "pattern", "collaboration"]
- `tags`: Optional tags for categorization

**Returns:**
- Memory ID

## Tool APIs

### File Operations

#### read_file
```python
async def read_file(path: str) -> Dict[str, Any]
```

**Returns:**
```python
{
    "content": str,
    "file_type": str,
    "size": int,
    "encoding": str
}
```

#### write_file
```python
async def write_file(
    path: str,
    content: str,
    create_directories: bool = True
) -> Dict[str, Any]
```

**Returns:**
```python
{
    "success": bool,
    "path": str,
    "size": int
}
```

#### list_files
```python
async def list_files(
    path: str = ".",
    pattern: str = "*",
    recursive: bool = False
) -> Dict[str, Any]
```

**Returns:**
```python
{
    "files": [
        {
            "path": str,
            "type": str,
            "size": int,
            "modified": str
        },
        ...
    ]
}
```

### Search Tools

#### search_files
```python
async def search_files(
    pattern: str,
    file_pattern: str = "*",
    path: str = ".",
    max_results: int = 50
) -> Dict[str, Any]
```

**Returns:**
```python
{
    "matches": [
        {
            "file": str,
            "line": int,
            "content": str,
            "context": List[str]
        },
        ...
    ]
}
```

#### advanced_search
```python
async def advanced_search(
    query: str,
    search_type: str = "hybrid",
    filters: Dict[str, Any] = None
) -> Dict[str, Any]
```

**Parameters:**
- `search_type`: One of ["semantic", "fulltext", "pattern", "hybrid"]
- `filters`: Optional filters like file_type, modified_after, etc.

### Analysis Tools

#### analyze_code
```python
async def analyze_code(
    path: str,
    analysis_type: str = "quick"
) -> Dict[str, Any]
```

**Parameters:**
- `analysis_type`: One of ["quick", "deep", "security", "performance"]

**Returns:**
```python
{
    "language": str,
    "metrics": {
        "lines": int,
        "functions": int,
        "classes": int,
        "complexity": float,
        "maintainability": float
    },
    "issues": List[Dict],
    "patterns": List[Dict]
}
```

#### detect_code_smells
```python
async def detect_code_smells(
    path: str = ".",
    severity_threshold: str = "medium",
    smell_types: List[str] = None
) -> Dict[str, Any]
```

**Returns:**
```python
{
    "smells": [
        {
            "type": str,
            "severity": str,
            "file": str,
            "line": int,
            "description": str,
            "suggestion": str
        },
        ...
    ]
}
```

### Template Tools

#### scaffold_feature
```python
async def scaffold_feature(
    feature_type: str,
    name: str,
    options: Dict[str, Any] = None
) -> Dict[str, Any]
```

**Parameters:**
- `feature_type`: One of ["api_endpoint", "database_model", "test_suite", "cli_command", "react_component", "service_class"]
- `name`: Feature name
- `options`: Feature-specific options

**Returns:**
```python
{
    "created_files": List[str],
    "main_file": str,
    "instructions": str
}
```

## Analysis API

### CodeAnalyzer

```python
class CodeAnalyzer:
    def __init__(self, workspace_root: Path)
```

#### Methods

##### analyze_file()
```python
async def analyze_file(
    file_path: Path,
    include_ast: bool = False
) -> FileAnalysis
```

**Returns:**
```python
{
    "file_path": str,
    "language": str,
    "metrics": MetricsDict,
    "imports": List[str],
    "exports": List[str],
    "dependencies": List[str],
    "ast": Optional[Dict]  # if include_ast=True
}
```

##### analyze_project()
```python
async def analyze_project(
    include_dependencies: bool = True
) -> ProjectAnalysis
```

**Returns:**
```python
{
    "total_files": int,
    "languages": Dict[str, int],
    "total_lines": int,
    "average_complexity": float,
    "dependency_graph": Dict,
    "quality_score": float
}
```

## Template API

### TemplateManager

```python
class TemplateManager:
    def __init__(self, template_dir: Path)
```

#### Methods

##### list_templates()
```python
def list_templates() -> List[TemplateInfo]
```

**Returns:**
```python
[
    {
        "name": str,
        "type": str,
        "language": str,
        "description": str,
        "variables": List[str]
    },
    ...
]
```

##### render_template()
```python
def render_template(
    template_name: str,
    context: Dict[str, Any]
) -> str
```

**Parameters:**
- `template_name`: Name of template to render
- `context`: Variables to inject into template

**Returns:**
- Rendered template content

## Error Types

### Base Errors

```python
class MCPServerError(Exception):
    """Base exception for all MCP server errors"""

class ConfigurationError(MCPServerError):
    """Configuration-related errors"""

class ProviderError(MCPServerError):
    """Provider-related errors"""

class SecurityError(MCPServerError):
    """Security-related errors"""

class ToolError(MCPServerError):
    """Tool execution errors"""
```

### Specific Errors

```python
class PathTraversalError(SecurityError):
    """Attempted path traversal detected"""

class RateLimitError(ProviderError):
    """Rate limit exceeded"""

class ValidationError(ToolError):
    """Invalid tool arguments"""

class FileNotFoundError(ToolError):
    """Requested file not found"""

class TemplateSyntaxError(ToolError):
    """Template syntax error"""
```

## Response Formats

### Success Response
```python
{
    "success": True,
    "data": Any,  # Tool-specific data
    "metadata": {
        "timestamp": str,
        "duration_ms": float,
        "cache_hit": bool
    }
}
```

### Error Response
```python
{
    "success": False,
    "error": {
        "type": str,
        "message": str,
        "details": Optional[Dict]
    }
}
```

## Rate Limits

| Operation | Limit | Window |
|-----------|-------|---------|
| File operations | 100 | 1 minute |
| Search operations | 50 | 1 minute |
| Analysis operations | 20 | 1 minute |
| Template operations | 30 | 1 minute |
| Embedding generation | 100 | 1 minute |

## Best Practices

### 1. Error Handling
Always wrap API calls in try-except blocks:

```python
try:
    result = await server.handle_tool_call("read_file", {"path": "test.py"})
except ValidationError as e:
    # Handle validation errors
except ToolError as e:
    # Handle other tool errors
```

### 2. Resource Management
Use context managers for server lifecycle:

```python
async with ModularMCPServer() as server:
    # Server is initialized and will be cleaned up
    result = await server.handle_tool_call(...)
```

### 3. Caching
Leverage caching for expensive operations:

```python
# Results are automatically cached
result1 = await analyze_code("large_file.py")
result2 = await analyze_code("large_file.py")  # Cache hit
```

### 4. Batch Operations
Use batch operations when possible:

```python
# Instead of multiple calls
for file in files:
    await analyze_code(file)

# Use batch analysis
await analyze_project()
```
