#!/usr/bin/env python3
"""
Enhanced File Editing Handler
Provides advanced file editing capabilities with AI assistance and session management
"""

import logging
from typing import Any, Dict, List

from mcp.types import Tool

from ...context.manager import ContextManager
from ...core import ConfigurationManager
from ...editing.tools import (
    close_edit_session_handler,
    edit_file_handler,
    get_edit_suggestions_handler,
    list_edit_sessions_handler,
    preview_edit_handler,
    session_apply_edit_handler,
    session_redo_handler,
    session_undo_handler,
    smart_edit_handler,
    start_edit_session_handler,
)
from ..base_handler import BaseHandler

logger = logging.getLogger(__name__)


class EditingHandler(BaseHandler):
    """Handler for enhanced file editing operations"""

    def __init__(self, config_manager: ConfigurationManager, context_manager: ContextManager):
        super().__init__(config_manager, context_manager)
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def get_tools() -> List[Tool]:
        """Get all editing tools"""
        return [
            Tool(
                name="edit_file",
                description="Enhanced file editing with multiple strategies"
                " (line-based, pattern-based, AST-based)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file to edit"},
                        "edits": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["line_based", "pattern_based", "ast_based"],
                                        "description": "Type of edit to perform",
                                    },
                                    "old_content": {
                                        "type": "string",
                                        "description": "Content to replace "
                                        "(for pattern_based edits)",
                                    },
                                    "new_content": {
                                        "type": "string",
                                        "description": "New content to insert",
                                    },
                                    "line_number": {
                                        "type": "integer",
                                        "description": "Line number for line-based edits",
                                    },
                                    "start_line": {
                                        "type": "integer",
                                        "description": "Start line for range edits",
                                    },
                                    "end_line": {
                                        "type": "integer",
                                        "description": "End line for range edits",
                                    },
                                },
                                "required": ["type", "new_content"],
                            },
                        },
                        "strategy": {
                            "type": "string",
                            "enum": ["line_based", "pattern_based", "ast_based"],
                            "default": "pattern_based",
                            "description": "Default editing strategy",
                        },
                        "create_backup": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to create a backup before editing",
                        },
                        "validate_syntax": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to validate syntax after editing",
                        },
                        "preview_only": {
                            "type": "boolean",
                            "default": False,
                            "description": "Only preview changes without applying them",
                        },
                    },
                    "required": ["file_path", "edits"],
                },
            ),
            Tool(
                name="smart_edit",
                description="AI-powered file editing using natural language instructions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file to edit"},
                        "instruction": {
                            "type": "string",
                            "description": "Natural language instruction for the edit "
                            "(e.g., 'add error handling', 'add type hints')",
                        },
                        "create_backup": {
                            "type": "boolean",
                            "default": True,
                            "description": "Whether to create a backup before editing",
                        },
                        "preview_only": {
                            "type": "boolean",
                            "default": False,
                            "description": "Only preview changes without applying them",
                        },
                    },
                    "required": ["file_path", "instruction"],
                },
            ),
            Tool(
                name="start_edit_session",
                description="Start a new editing session with undo/redo capabilities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_name": {
                            "type": "string",
                            "description": "Name for the editing session",
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description of the editing session",
                        },
                    },
                    "required": ["session_name"],
                },
            ),
            Tool(
                name="session_apply_edit",
                description="Apply an edit within an editing session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "ID of the editing session",
                        },
                        "file_path": {"type": "string", "description": "Path to the file to edit"},
                        "edit": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["line_based", "pattern_based", "ast_based"],
                                    "description": "Type of edit to perform",
                                },
                                "old_content": {
                                    "type": "string",
                                    "description": "Content to replace (for pattern_based edits)",
                                },
                                "new_content": {
                                    "type": "string",
                                    "description": "New content to insert",
                                },
                                "line_number": {
                                    "type": "integer",
                                    "description": "Line number for line-based edits",
                                },
                                "start_line": {
                                    "type": "integer",
                                    "description": "Start line for range edits",
                                },
                                "end_line": {
                                    "type": "integer",
                                    "description": "End line for range edits",
                                },
                            },
                            "required": ["type", "new_content"],
                        },
                        "description": {"type": "string", "description": "Description of the edit"},
                    },
                    "required": ["session_id", "file_path", "edit"],
                },
            ),
            Tool(
                name="session_undo",
                description="Undo the last edit in a session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the editing session"}
                    },
                    "required": ["session_id"],
                },
            ),
            Tool(
                name="session_redo",
                description="Redo the last undone edit in a session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "ID of the editing session"}
                    },
                    "required": ["session_id"],
                },
            ),
            Tool(
                name="get_edit_suggestions",
                description="Get AI-powered suggestions for improving a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to analyze",
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": [
                                    "performance",
                                    "readability",
                                    "security",
                                    "maintainability",
                                    "style",
                                ],
                            },
                            "description": "Areas to focus suggestions on",
                        },
                        "max_suggestions": {
                            "type": "integer",
                            "default": 5,
                            "description": "Maximum number of suggestions to return",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
            Tool(
                name="preview_edit",
                description="Preview the changes that would be made by an edit "
                "without applying them",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to preview edits for",
                        },
                        "edit": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["line_based", "pattern_based", "ast_based"],
                                    "description": "Type of edit to preview",
                                },
                                "old_content": {
                                    "type": "string",
                                    "description": "Content to replace (for pattern_based edits)",
                                },
                                "new_content": {
                                    "type": "string",
                                    "description": "New content to insert",
                                },
                                "line_number": {
                                    "type": "integer",
                                    "description": "Line number for line-based edits",
                                },
                                "start_line": {
                                    "type": "integer",
                                    "description": "Start line for range edits",
                                },
                                "end_line": {
                                    "type": "integer",
                                    "description": "End line for range edits",
                                },
                            },
                            "required": ["type", "new_content"],
                        },
                    },
                    "required": ["file_path", "edit"],
                },
            ),
            Tool(
                name="list_edit_sessions",
                description="List all active editing sessions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_closed": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether to include closed sessions",
                        }
                    },
                },
            ),
            Tool(
                name="close_edit_session",
                description="Close an editing session and clean up resources",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {
                            "type": "string",
                            "description": "ID of the editing session to close",
                        },
                        "cleanup_backups": {
                            "type": "boolean",
                            "default": False,
                            "description": "Whether to clean up backup files",
                        },
                    },
                    "required": ["session_id"],
                },
            ),
        ]

    async def edit_file(self, arguments: Dict[str, Any]) -> str:
        """Handle enhanced file editing"""
        try:
            result = await edit_file_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("edit_file", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("edit_file", arguments, success=False)
            return self.format_error("edit_file", str(e))

    async def smart_edit(self, arguments: Dict[str, Any]) -> str:
        """Handle AI-powered smart editing"""
        try:
            result = await smart_edit_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("smart_edit", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("smart_edit", arguments, success=False)
            return self.format_error("smart_edit", str(e))

    async def start_edit_session(self, arguments: Dict[str, Any]) -> str:
        """Handle starting an editing session"""
        try:
            result = await start_edit_session_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("start_edit_session", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("start_edit_session", arguments, success=False)
            return self.format_error("start_edit_session", str(e))

    async def session_apply_edit(self, arguments: Dict[str, Any]) -> str:
        """Handle applying an edit within a session"""
        try:
            result = await session_apply_edit_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("session_apply_edit", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("session_apply_edit", arguments, success=False)
            return self.format_error("session_apply_edit", str(e))

    async def session_undo(self, arguments: Dict[str, Any]) -> str:
        """Handle undoing an edit in a session"""
        try:
            result = await session_undo_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("session_undo", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("session_undo", arguments, success=False)
            return self.format_error("session_undo", str(e))

    async def session_redo(self, arguments: Dict[str, Any]) -> str:
        """Handle redoing an edit in a session"""
        try:
            result = await session_redo_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("session_redo", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("session_redo", arguments, success=False)
            return self.format_error("session_redo", str(e))

    async def get_edit_suggestions(self, arguments: Dict[str, Any]) -> str:
        """Handle getting AI-powered edit suggestions"""
        try:
            result = await get_edit_suggestions_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("get_edit_suggestions", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("get_edit_suggestions", arguments, success=False)
            return self.format_error("get_edit_suggestions", str(e))

    async def preview_edit(self, arguments: Dict[str, Any]) -> str:
        """Handle previewing edits"""
        try:
            result = await preview_edit_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("preview_edit", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("preview_edit", arguments, success=False)
            return self.format_error("preview_edit", str(e))

    async def list_edit_sessions(self, arguments: Dict[str, Any]) -> str:
        """Handle listing edit sessions"""
        try:
            result = await list_edit_sessions_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("list_edit_sessions", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("list_edit_sessions", arguments, success=False)
            return self.format_error("list_edit_sessions", str(e))

    async def close_edit_session(self, arguments: Dict[str, Any]) -> str:
        """Handle closing an edit session"""
        try:
            result = await close_edit_session_handler(arguments)
            success = result.get("success", False)
            await self.log_tool_usage("close_edit_session", arguments, success=success)
            display = result.get("_mcp_display")
            return str(display) if display is not None else str(result)
        except Exception as e:
            await self.log_tool_usage("close_edit_session", arguments, success=False)
            return self.format_error("close_edit_session", str(e))
