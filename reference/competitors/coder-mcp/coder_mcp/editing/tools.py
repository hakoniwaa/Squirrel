"""
MCP tool handlers for the enhanced file editing system.

This module provides tool handlers that integrate the editing capabilities
with the Model Context Protocol (MCP) server.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

from .core.editor import EnhancedFileEditor
from .core.types import EditConfig, EditResult, EditStrategy, EditType, FileEdit
from .session.manager import EditSessionManager
from .strategies.ai_editor import AIFileEditor

# Global instances
_config = EditConfig()
_file_editor = EnhancedFileEditor(_config)
_ai_editor = AIFileEditor(_config)
_session_manager = EditSessionManager(_config)


def resolve_file_path(file_path: str) -> str:
    """
    Resolve file path to absolute path.

    Args:
        file_path: Relative or absolute file path

    Returns:
        Absolute file path
    """
    path = Path(file_path)

    # If already absolute, return as is
    if path.is_absolute():
        return str(path)

    # Try to resolve relative to current working directory
    cwd_path = Path.cwd() / path
    if cwd_path.exists():
        return str(cwd_path.resolve())

    # Try to resolve relative to workspace root if set
    workspace_root = os.environ.get("MCP_WORKSPACE_ROOT")
    if workspace_root:
        workspace_path = Path(workspace_root) / path
        if workspace_path.exists():
            return str(workspace_path.resolve())

    # Return the resolved path even if it doesn't exist
    # (let the editor handle the file not found error)
    return str(path.resolve())


def _convert_dict_to_file_edits(edits: List[Dict[str, Any]]) -> List[FileEdit]:
    """Convert dictionary edits to FileEdit objects."""
    file_edits = []
    for edit_dict in edits:
        # Map pattern_based type to REPLACE type since the validation logic
        # expects REPLACE with pattern
        edit_type_str = edit_dict["type"]
        if edit_type_str == "pattern_based":
            edit_type = EditType.REPLACE
            # For pattern_based edits, ensure we use PATTERN_BASED strategy
            default_strategy = "pattern_based"
        else:
            edit_type = EditType(edit_type_str)
            # For other types, use line_based as default
            default_strategy = "line_based"

        strategy = EditStrategy(edit_dict.get("strategy", default_strategy))

        # Handle mapping between MCP tool schema and internal schema
        pattern = edit_dict.get("pattern")
        replacement = edit_dict.get("replacement")
        content = edit_dict.get("content")

        # Map old_content to pattern and new_content to replacement for pattern-based edits
        if edit_dict.get("old_content") is not None:
            pattern = edit_dict["old_content"]
        if edit_dict.get("new_content") is not None:
            replacement = edit_dict["new_content"]
            if content is None:
                content = edit_dict["new_content"]

        file_edit = FileEdit(
            type=edit_type,
            start_line=edit_dict.get("start_line"),
            end_line=edit_dict.get("end_line"),
            pattern=pattern,
            replacement=replacement,
            content=content,
            target_line=edit_dict.get("target_line"),
            strategy=strategy,
        )
        file_edits.append(file_edit)
    return file_edits


def _format_edit_response(result: EditResult, path: str, preview: bool) -> Dict[str, Any]:
    """Format the response for edit operations."""
    response = {
        "success": result.success,
        "changes_made": result.changes_made,
        "diff": result.diff,
    }

    if result.backup_path:
        response["backup_path"] = result.backup_path
    if result.error:
        response["error"] = result.error
    if result.preview:
        response["preview"] = result.preview
    if result.warnings:
        response["warnings"] = result.warnings

    # Add MCP display formatting
    if result.success:
        status_emoji = "👁️" if preview else "✅"
        action = "Preview" if preview else "Applied"
        response["_mcp_display"] = (
            f"{status_emoji} {action} {result.changes_made} changes to {path}"
        )
        if result.backup_path:
            display_text = response["_mcp_display"]
            assert isinstance(display_text, str), "display_text should be a string"
            response["_mcp_display"] = display_text + f"\n📄 Backup: {result.backup_path}"
    else:
        response["_mcp_display"] = f"❌ Edit failed: {result.error}"

    return response


async def edit_file_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle edit_file tool calls.

    Args:
        arguments: Dictionary containing:
            - path: Path to the file to edit
            - edits: List of edit operations as dictionaries
            - preview: If True, show changes without applying (optional)
            - create_backup: If True, create backup before editing (optional)

    Returns:
        Dictionary with edit results
    """
    try:
        path = arguments["file_path"]
        edits = arguments["edits"]
        preview = arguments.get("preview_only", False)
        create_backup = arguments.get("create_backup", True)

        # Resolve the file path
        resolved_path = resolve_file_path(path)

        # Convert dict edits to FileEdit objects
        try:
            file_edits = _convert_dict_to_file_edits(edits)
        except (ValueError, KeyError) as e:
            return {
                "success": False,
                "error": f"Invalid edit specification: {str(e)}",
                "_mcp_display": f"❌ Invalid edit: {str(e)}",
            }

        # Apply edits
        result: EditResult = _file_editor.edit_file(
            resolved_path, file_edits, preview, create_backup
        )

        # Format and return response (use original path in response)
        return _format_edit_response(result, path, preview)

    except Exception as e:
        return {"success": False, "error": str(e), "_mcp_display": f"❌ Unexpected error: {str(e)}"}


async def smart_edit_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle smart_edit tool calls.

    Args:
        arguments: Dictionary containing:
            - file_path: Path to the file to edit
            - instruction: Natural language description of changes
            - context_files: Additional files for context (optional)
            - use_ai: Whether to use AI for understanding instructions (optional)

    Returns:
        Dictionary with edit results
    """
    try:
        path = arguments["file_path"]
        instruction = arguments["instruction"]
        context_files = arguments.get("context_files")
        use_ai = arguments.get("use_ai", True)

        result: EditResult = _ai_editor.ai_edit(path, instruction, context_files, use_ai)

        response = {
            "success": result.success,
            "changes_made": result.changes_made,
            "diff": result.diff,
            "instruction": instruction,
        }

        if result.backup_path:
            response["backup_path"] = result.backup_path
        if result.error:
            response["error"] = result.error
        if result.warnings:
            response["warnings"] = result.warnings

        # Add MCP display formatting
        if result.success:
            response["_mcp_display"] = (
                f"🤖 Applied AI edit: '{instruction}' to {path}\n"
                f"✅ {result.changes_made} changes made"
            )
            if result.backup_path:
                display_text = response["_mcp_display"]
                assert isinstance(display_text, str), "display_text should be a string"
                response["_mcp_display"] = display_text + f"\n📄 Backup: {result.backup_path}"
        else:
            response["_mcp_display"] = f"❌ AI edit failed: {result.error}"

        return response

    except Exception as e:
        return {"success": False, "error": str(e), "_mcp_display": f"❌ Unexpected error: {str(e)}"}


async def start_edit_session_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle start_edit_session tool calls.

    Args:
        arguments: Dictionary containing:
            - session_name: Name for the editing session
            - files: Optional list of files for the session

    Returns:
        Dictionary with session information
    """
    try:
        session_name = arguments["session_name"]
        files = arguments.get("files", [])

        session = _session_manager.create_session(files, session_name)

        return {
            "success": True,
            "session_id": session.session_id,
            "session_name": session_name,
            "files": session.files,
            "_mcp_display": f"✅ Created editing session: {session_name} (ID: {session.session_id})",
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "_mcp_display": f"❌ Session creation failed: {str(e)}",
        }


async def session_apply_edit_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle session_apply_edit tool calls.

    Args:
        arguments: Dictionary containing:
            - session_id: ID of the session
            - file_path: Path to the file to edit
            - edit: Edit operation as dictionary (or edits list for backward compatibility)
            - description: Optional description of the edit

    Returns:
        Dictionary with edit results
    """
    try:
        session_id = arguments["session_id"]
        file_path = arguments["file_path"]
        description = arguments.get("description")

        # Get edits from arguments
        edits = _extract_edits_from_arguments(arguments)
        if not edits:
            return {
                "success": False,
                "error": "Missing 'edit' or 'edits' in arguments",
                "_mcp_display": "❌ Missing edit specification",
            }

        # Convert dict edits to FileEdit objects
        try:
            file_edits = _convert_dict_to_file_edits(edits)
        except (ValueError, KeyError) as e:
            return {
                "success": False,
                "error": f"Invalid edit specification: {str(e)}",
                "_mcp_display": f"❌ Invalid edit: {str(e)}",
            }

        # Apply edit within session
        result = _session_manager.apply_edit(session_id, file_path, file_edits, description)
        return _format_session_edit_response(result, session_id, file_path)

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "_mcp_display": f"❌ Session edit error: {str(e)}",
        }


def _extract_edits_from_arguments(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract edits from arguments, handling both single edit and edits list."""
    if "edit" in arguments:
        return [arguments["edit"]]
    elif "edits" in arguments:
        edits = arguments["edits"]
        # Ensure we return a list of dictionaries
        if isinstance(edits, list):
            return edits
        else:
            return [edits]
    return []


def _format_session_edit_response(
    result: EditResult, session_id: str, file_path: str
) -> Dict[str, Any]:
    """Format the response for session edit operations."""
    response = {
        "success": result.success,
        "changes_made": result.changes_made,
        "diff": result.diff,
        "session_id": session_id,
    }

    if result.backup_path:
        response["backup_path"] = result.backup_path
    if result.error:
        response["error"] = result.error
    if result.warnings:
        response["warnings"] = result.warnings

    # Add MCP display formatting
    if result.success:
        response["_mcp_display"] = (
            f"✅ Applied edit in session {session_id}\n"
            f"📝 {result.changes_made} changes to {file_path}"
        )
        if result.backup_path:
            display_text = response["_mcp_display"]
            assert isinstance(display_text, str), "display_text should be a string"
            response["_mcp_display"] = display_text + f"\n📄 Backup: {result.backup_path}"
    else:
        response["_mcp_display"] = f"❌ Session edit failed: {result.error}"

    return response


async def session_undo_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle session_undo tool calls.

    Args:
        arguments: Dictionary containing:
            - session_id: ID of the session

    Returns:
        Dictionary with undo results
    """
    try:
        session_id = arguments["session_id"]
        result = _session_manager.undo(session_id)

        response = {
            "success": result.success,
            "changes_made": result.changes_made,
            "diff": result.diff,
            "session_id": session_id,
        }

        if result.error:
            response["error"] = result.error
        if result.warnings:
            response["warnings"] = result.warnings

        # Add MCP display formatting
        if result.success:
            response["_mcp_display"] = f"↩️ Undid last edit in session {session_id}"
        else:
            response["_mcp_display"] = f"❌ Undo failed: {result.error}"

        return response

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "_mcp_display": f"❌ Undo error: {str(e)}",
        }


async def session_redo_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle session_redo tool calls.

    Args:
        arguments: Dictionary containing:
            - session_id: ID of the session

    Returns:
        Dictionary with redo results
    """
    try:
        session_id = arguments["session_id"]
        result = _session_manager.redo(session_id)

        response = {
            "success": result.success,
            "changes_made": result.changes_made,
            "diff": result.diff,
            "session_id": session_id,
        }

        if result.error:
            response["error"] = result.error
        if result.warnings:
            response["warnings"] = result.warnings

        # Add MCP display formatting
        if result.success:
            response["_mcp_display"] = f"↪️ Redid edit in session {session_id}"
        else:
            response["_mcp_display"] = f"❌ Redo failed: {result.error}"

        return response

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "_mcp_display": f"❌ Redo error: {str(e)}",
        }


async def get_edit_suggestions_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle get_edit_suggestions tool calls.

    Args:
        arguments: Dictionary containing:
            - file_path: Path to the file to analyze
            - focus_areas: Optional list of areas to focus on

    Returns:
        Dictionary with suggestions
    """
    try:
        file_path = arguments["file_path"]
        focus_areas = arguments.get("focus_areas", [])

        suggestions = _ai_editor.get_suggestions(file_path)

        response = {
            "success": True,
            "file_path": file_path,
            "suggestions": suggestions,
            "focus_areas": focus_areas,
            "_mcp_display": f"💡 Found {len(suggestions)} suggestions for {file_path}",
        }

        return response

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "_mcp_display": f"❌ Suggestion error: {str(e)}",
        }


async def preview_edit_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle preview_edit tool calls.

    Args:
        arguments: Dictionary containing:
            - file_path: Path to the file to edit
            - edit: Edit operation as dictionary (or edits list for backward compatibility)

    Returns:
        Dictionary with preview results
    """
    try:
        # Extract edits from arguments
        edits = _extract_edits_from_arguments(arguments)
        if not edits:
            return {
                "success": False,
                "error": "Missing 'edit' or 'edits' in arguments",
                "_mcp_display": "❌ Missing edit specification",
            }

        # Set preview mode and call edit_file_handler
        preview_args = arguments.copy()
        preview_args["edits"] = edits
        preview_args["preview_only"] = True

        return await edit_file_handler(preview_args)

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "_mcp_display": f"❌ Preview error: {str(e)}",
        }


async def list_edit_sessions_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle list_edit_sessions tool calls.

    Args:
        arguments: Dictionary (no specific arguments needed)

    Returns:
        Dictionary with session list
    """
    try:
        sessions = _session_manager.list_sessions()

        response = {
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
            "_mcp_display": f"📋 Found {len(sessions)} active editing sessions",
        }

        return response

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "_mcp_display": f"❌ List sessions error: {str(e)}",
        }


async def close_edit_session_handler(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle close_edit_session tool calls.

    Args:
        arguments: Dictionary containing:
            - session_id: ID of the session to close

    Returns:
        Dictionary with close results
    """
    try:
        session_id = arguments["session_id"]
        result = _session_manager.close_session(session_id)

        if result:
            return {
                "success": True,
                "session_id": session_id,
                "_mcp_display": f"✅ Closed editing session: {session_id}",
            }
        else:
            return {
                "success": False,
                "error": f"Session not found: {session_id}",
                "_mcp_display": f"❌ Session not found: {session_id}",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "_mcp_display": f"❌ Close session error: {str(e)}",
        }
