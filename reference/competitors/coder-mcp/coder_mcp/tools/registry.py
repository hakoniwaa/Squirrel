#!/usr/bin/env python3
"""
Central tool registry for MCP server tools
Handles tool discovery, registration, and routing
"""

import importlib
import logging
from typing import Any, Callable, Dict, List, Optional

from mcp.types import Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all tools and their handlers"""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._handler_instances: Dict[str, Any] = {}

    def register_tool(
        self, tool: Tool, handler_func: Callable[..., Any], handler_instance: Any = None
    ) -> None:
        """Register a tool with its handler function and instance"""
        self._tools[tool.name] = tool
        self._handlers[tool.name] = handler_func
        if handler_instance:
            self._handler_instances[tool.name] = handler_instance

    def register_handler_tools(self, handler_instance: Any) -> None:
        """Register all tools from a handler instance"""
        # Get tools from the handler's get_tools() method
        if hasattr(handler_instance, "get_tools"):
            tools = handler_instance.get_tools()
            for tool in tools:
                # Find the corresponding handler method
                handler_method_name = tool.name
                if hasattr(handler_instance, handler_method_name):
                    handler_method = getattr(handler_instance, handler_method_name)
                    self.register_tool(tool, handler_method, handler_instance)

    def discover_tools(self, handler_modules: List[str]) -> None:
        """Auto-discover tools from handler modules"""
        for module_name in handler_modules:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "register_tools"):
                    module.register_tools(self)
            except ImportError as e:
                logger.warning(f"Could not import {module_name}: {e}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def get_handler(self, name: str) -> Optional[Callable[..., Any]]:
        """Get a handler function by tool name"""
        return self._handlers.get(name)

    def get_handler_instance(self, name: str) -> Any:
        """Get the handler instance for a tool"""
        return self._handler_instances.get(name)

    def get_all_tools(self) -> List[Tool]:
        """Get all registered tools"""
        return list(self._tools.values())

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered"""
        return name in self._tools

    async def handle_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Handle a tool call by routing to the appropriate handler"""
        if not self.has_tool(name):
            return f"Error: Unknown tool '{name}'"

        handler = self.get_handler(name)
        if not handler:
            return f"Error: No handler found for tool '{name}'"

        try:
            # Call the handler with arguments
            result = await handler(arguments)
            return str(result)  # Ensure we return a string
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"

    def list_tools_by_category(self) -> Dict[str, List[str]]:
        """Group tools by their category/prefix"""
        categories: Dict[str, List[str]] = {}
        for tool_name in self._tools.keys():
            # Determine category from handler instance type
            handler_instance = self.get_handler_instance(tool_name)
            if handler_instance:
                category = handler_instance.__class__.__name__.replace("Handler", "").replace(
                    "Handlers", ""
                )
                if category not in categories:
                    categories[category] = []
                categories[category].append(tool_name)
            else:
                # Fallback to generic category
                if "other" not in categories:
                    categories["other"] = []
                categories["other"].append(tool_name)

        return categories
