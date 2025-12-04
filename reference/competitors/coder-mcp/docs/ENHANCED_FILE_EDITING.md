# Enhanced File Editing System

The Enhanced File Editing System provides Cursor-like editing capabilities with AI assistance, session management, and comprehensive backup/restore functionality.

## Table of Contents

- [Overview](#overview)
- [Core Features](#core-features)
- [Quick Start](#quick-start)
- [Editing Strategies](#editing-strategies)
- [AI-Powered Editing](#ai-powered-editing)
- [Session Management](#session-management)
- [Backup and Restore](#backup-and-restore)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

The Enhanced File Editing System extends coder-mcp with advanced file editing capabilities that rival modern code editors. It provides:

- **Multiple Editing Strategies**: Line-based, pattern-based, and AST-based editing
- **AI-Powered Natural Language Editing**: Edit files using natural language instructions
- **Session Management**: Undo/redo functionality with session isolation
- **Comprehensive Backup System**: Automatic backups with verification and restoration
- **Syntax Validation**: Prevent breaking changes with built-in syntax checking
- **Preview Mode**: See changes before applying them

## Core Features

### 🎯 **Multi-Strategy Editing**
- **Line-based**: Direct line insertion, replacement, and deletion
- **Pattern-based**: Find and replace using exact text matching
- **AST-based**: Structural code modifications using abstract syntax trees

### 🤖 **AI-Powered Editing**
- **Natural Language Instructions**: "add error handling", "add type hints", "remove comments"
- **Intelligent Pattern Recognition**: Automatically detects common editing patterns
- **Context-Aware Suggestions**: Provides improvement suggestions based on code analysis

### 📝 **Session Management**
- **Isolated Sessions**: Multiple editing sessions with separate undo/redo stacks
- **Persistent History**: Edit history survives across tool calls
- **Atomic Operations**: All-or-nothing edit application

### 🔒 **Safety Features**
- **Automatic Backups**: Creates timestamped backups before edits
- **Syntax Validation**: Validates code syntax after edits (configurable)
- **Preview Mode**: Test edits without modifying files
- **Rollback Support**: Restore from backups or undo changes

## Quick Start

### Basic File Editing

```python
# Simple pattern-based edit
await edit_file({
    "file_path": "src/main.py",
    "edits": [{
        "type": "pattern_based",
        "old_content": 'print("Hello, World!")',
        "new_content": 'print("Hello, Enhanced World!")'
    }]
})
```

### AI-Powered Editing

```python
# Natural language instruction
await smart_edit({
    "file_path": "src/utils.py",
    "instruction": "add error handling to all functions"
})
```

### Session-Based Editing

```python
# Start a session
session = await start_edit_session({
    "session_name": "refactor_auth",
    "description": "Refactoring authentication module"
})

# Apply edits in session
await session_apply_edit({
    "session_id": session["session_id"],
    "file_path": "src/auth.py",
    "edit": {
        "type": "pattern_based",
        "old_content": "def login(username, password):",
        "new_content": "async def login(username: str, password: str):"
    }
})

# Undo if needed
await session_undo({"session_id": session["session_id"]})
```

## Editing Strategies

### Line-Based Editing

Direct manipulation of file lines by line number.

```python
{
    "type": "line_based",
    "new_content": "import logging",
    "line_number": 1  # Insert at line 1
}

{
    "type": "line_based",
    "new_content": "# Updated function",
    "start_line": 10,
    "end_line": 15  # Replace lines 10-15
}
```

**Best for:**
- Adding imports at specific positions
- Inserting new functions or classes
- Replacing entire code blocks

### Pattern-Based Editing

Find and replace using exact text matching.

```python
{
    "type": "pattern_based",
    "old_content": "def old_function_name():",
    "new_content": "def new_function_name():"
}
```

**Best for:**
- Renaming functions, variables, or classes
- Updating string literals
- Modifying specific code patterns

### AST-Based Editing

Structural modifications using abstract syntax trees (Python only).

```python
{
    "type": "ast_based",
    "old_content": "function_call(arg1, arg2)",
    "new_content": "function_call(arg1, arg2, new_arg=True)"
}
```

**Best for:**
- Adding function parameters
- Modifying class inheritance
- Restructuring code while preserving semantics

## AI-Powered Editing

### Natural Language Instructions

The AI editor understands common programming instructions:

| Instruction | Example | Result |
|-------------|---------|---------|
| `add imports` | "add import os" | Adds import statement |
| `add error handling` | "add error handling to parse_file" | Wraps function in try/catch |
| `add type hints` | "add type hints to all functions" | Adds Python type annotations |
| `add docstrings` | "add docstrings" | Adds documentation strings |
| `remove comments` | "remove all comments" | Removes comment lines |
| `format code` | "format this code" | Applies code formatting |
| `rename variable` | "rename x to count" | Renames variables |

### Advanced AI Features

```python
# Get improvement suggestions
suggestions = await get_edit_suggestions({
    "file_path": "src/complex_module.py",
    "focus_areas": ["performance", "readability", "security"],
    "max_suggestions": 5
})

# Apply multiple AI-driven improvements
await smart_edit({
    "file_path": "src/legacy_code.py",
    "instruction": "modernize this code with type hints, error handling, and better variable names"
})
```

## Session Management

### Creating Sessions

```python
session = await start_edit_session({
    "session_name": "feature_implementation",
    "description": "Implementing new user authentication feature"
})
```

### Managing Edit History

```python
# Apply multiple edits
await session_apply_edit({
    "session_id": session_id,
    "file_path": "src/auth.py",
    "edit": {...},
    "description": "Add login function"
})

await session_apply_edit({
    "session_id": session_id,
    "file_path": "src/auth.py",
    "edit": {...},
    "description": "Add logout function"
})

# Undo last edit
await session_undo({"session_id": session_id})

# Redo the undone edit
await session_redo({"session_id": session_id})

# Get session information
info = await get_session_info({"session_id": session_id})
```

### Session Cleanup

```python
# Close session and optionally clean up backups
await close_edit_session({
    "session_id": session_id,
    "cleanup_backups": True
})

# List all active sessions
sessions = await list_edit_sessions({
    "include_closed": False
})
```

## Backup and Restore

### Automatic Backups

All edits automatically create timestamped backups:

```
.backups/
├── main.py_20240108_143022_abc123.bak
├── utils.py_20240108_143045_def456.bak
└── auth.py_20240108_143102_ghi789.bak
```

### Backup Management

```python
# Create manual backup
backup_path = backup_manager.create_backup(file_path)

# Verify backup integrity
is_valid = backup_manager.verify_backup(backup_path, original_file)

# Restore from backup
backup_manager.restore_backup(backup_path, target_file)

# Clean up old backups (keep last 10)
backup_manager.cleanup_old_backups(file_path, keep_count=10)
```

### Backup Configuration

```python
backup_config = {
    "enabled": True,
    "max_backups_per_file": 10,
    "backup_dir": ".backups",
    "compress_backups": True,
    "verify_checksums": True
}
```

## API Reference

### Core Editing Tools

#### edit_file

Enhanced file editing with multiple strategies.

```python
await edit_file({
    "file_path": str,           # Path to file
    "edits": List[Edit],        # List of edits to apply
    "strategy": str,            # Default strategy: "pattern_based"
    "create_backup": bool,      # Create backup: True
    "validate_syntax": bool,    # Validate syntax: True
    "preview_only": bool        # Preview only: False
})
```

#### smart_edit

AI-powered editing using natural language.

```python
await smart_edit({
    "file_path": str,           # Path to file
    "instruction": str,         # Natural language instruction
    "create_backup": bool,      # Create backup: True
    "preview_only": bool        # Preview only: False
})
```

#### preview_edit

Preview changes without applying them.

```python
await preview_edit({
    "file_path": str,           # Path to file
    "edit": Edit               # Single edit to preview
})
```

### Session Management Tools

#### start_edit_session

Start a new editing session.

```python
await start_edit_session({
    "session_name": str,        # Session name
    "description": str          # Optional description
})
```

#### session_apply_edit

Apply an edit within a session.

```python
await session_apply_edit({
    "session_id": str,          # Session ID
    "file_path": str,           # Path to file
    "edit": Edit,               # Edit to apply
    "description": str          # Optional edit description
})
```

#### session_undo / session_redo

Undo or redo edits in a session.

```python
await session_undo({"session_id": str})
await session_redo({"session_id": str})
```

### Analysis Tools

#### get_edit_suggestions

Get AI-powered improvement suggestions.

```python
await get_edit_suggestions({
    "file_path": str,                    # Path to file
    "focus_areas": List[str],            # Focus areas
    "max_suggestions": int               # Max suggestions: 5
})
```

Focus areas: `"performance"`, `"readability"`, `"security"`, `"maintainability"`, `"style"`

## Examples

### Example 1: Refactoring a Function

```python
# Original code in utils.py:
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result

# Refactor with multiple edits
await edit_file({
    "file_path": "utils.py",
    "edits": [
        {
            "type": "pattern_based",
            "old_content": "def process_data(data):",
            "new_content": "def process_data(data: List[int]) -> List[int]:"
        },
        {
            "type": "pattern_based",
            "old_content": "result = []",
            "new_content": "result: List[int] = []"
        }
    ]
})

# Or use AI to do it automatically
await smart_edit({
    "file_path": "utils.py",
    "instruction": "add type hints and improve the function"
})
```

### Example 2: Session-Based Refactoring

```python
# Start refactoring session
session = await start_edit_session({
    "session_name": "api_refactor",
    "description": "Refactoring API endpoints for v2"
})

session_id = session["session_id"]

# Refactor multiple files
for file_path in ["api/auth.py", "api/users.py", "api/posts.py"]:
    await session_apply_edit({
        "session_id": session_id,
        "file_path": file_path,
        "edit": {
            "type": "pattern_based",
            "old_content": "from flask import",
            "new_content": "from fastapi import"
        },
        "description": f"Migrate {file_path} from Flask to FastAPI"
    })

# If something goes wrong, undo the last change
await session_undo({"session_id": session_id})

# When done, close the session
await close_edit_session({"session_id": session_id})
```

### Example 3: Preview and Apply Workflow

```python
# Preview a complex change first
preview = await preview_edit({
    "file_path": "src/complex_module.py",
    "edit": {
        "type": "pattern_based",
        "old_content": "class OldAPI:",
        "new_content": "class NewAPI:"
    }
})

print("Preview:", preview)

# If preview looks good, apply the change
await edit_file({
    "file_path": "src/complex_module.py",
    "edits": [{
        "type": "pattern_based",
        "old_content": "class OldAPI:",
        "new_content": "class NewAPI:"
    }]
})
```

## Best Practices

### 1. Always Use Backups

```python
# Enable backups for important changes
await edit_file({
    "file_path": "critical_module.py",
    "edits": [...],
    "create_backup": True  # Always True for production code
})
```

### 2. Validate Syntax for Code Files

```python
# Enable syntax validation for Python files
await edit_file({
    "file_path": "module.py",
    "edits": [...],
    "validate_syntax": True
})
```

### 3. Use Preview for Complex Changes

```python
# Preview complex changes first
preview = await preview_edit({
    "file_path": "complex_file.py",
    "edit": complex_edit
})

# Review the preview before applying
if looks_good(preview):
    await edit_file({
        "file_path": "complex_file.py",
        "edits": [complex_edit]
    })
```

### 4. Use Sessions for Related Changes

```python
# Group related edits in sessions
session = await start_edit_session({
    "session_name": "feature_xyz",
    "description": "Implementing feature XYZ"
})

# All related edits in the same session
# Enables easy undo/redo of the entire feature
```

### 5. Choose the Right Strategy

- **Line-based**: For precise insertions and deletions
- **Pattern-based**: For find/replace operations
- **AST-based**: For structural code changes
- **AI-powered**: For high-level improvements

### 6. Use Descriptive Session Names

```python
# Good session names
"fix_authentication_bug"
"implement_user_profiles"
"refactor_database_layer"

# Bad session names
"changes"
"updates"
"fixes"
```

## Troubleshooting

### Common Issues

#### Edit Not Applied
```
❌ Error: Pattern not found in file
```
**Solution**: Check that the `old_content` exactly matches the text in the file, including whitespace.

#### Syntax Error After Edit
```
❌ Error: Syntax error detected after edit
```
**Solution**: Review the edit for syntax issues. Use preview mode to test changes first.

#### Session Not Found
```
❌ Error: Session 'xyz' not found
```
**Solution**: Ensure the session was created successfully and hasn't been closed.

#### Backup Restoration Failed
```
❌ Error: Backup verification failed
```
**Solution**: Check backup file integrity. The original file may have been modified after backup creation.

### Debug Mode

Enable debug logging for detailed information:

```python
# In .env.mcp
LOG_LEVEL=DEBUG
EDITING_DEBUG=true
```

### Recovery Procedures

#### Restore from Backup
```python
# List available backups
backups = backup_manager.list_backups("problematic_file.py")

# Restore from specific backup
backup_manager.restore_backup(
    backup_path=backups[0],  # Most recent backup
    target_file="problematic_file.py"
)
```

#### Reset Session
```python
# If session is corrupted, close and restart
await close_edit_session({"session_id": session_id})
new_session = await start_edit_session({
    "session_name": "recovery_session"
})
```

### Performance Optimization

#### Large Files
For files > 10MB, consider:
- Using line-based edits instead of pattern-based
- Breaking large edits into smaller chunks
- Disabling syntax validation for performance

#### Many Sessions
- Close unused sessions regularly
- Use descriptive names for easier management
- Clean up old backups periodically

---

## Integration with coder-mcp

The Enhanced File Editing System integrates seamlessly with coder-mcp's existing features:

- **Context Awareness**: Edits are indexed and searchable
- **AI Enhancement**: Leverages coder-mcp's AI capabilities
- **Security**: Uses coder-mcp's security framework
- **Configuration**: Configurable through coder-mcp's config system

For more information, see the main [coder-mcp documentation](../README.md).
