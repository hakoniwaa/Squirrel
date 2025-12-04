#!/usr/bin/env python3
"""
Main tool handlers using the new modular architecture
Central orchestrator that uses the tool registry and individual handlers
"""

import logging
from typing import Any, Dict, List, Type

from mcp.types import Tool

from ..context.manager import ContextManager
from ..core import ConfigurationManager
from .base_handler import BaseHandler
from .handlers import (  # AIAnalysisHandler temporarily removed
    AnalysisHandler,
    ContextHandler,
    EditingHandler,
    FileHandler,
    SystemHandler,
    TemplateHandler,
)
from .registry import ToolRegistry

logger = logging.getLogger(__name__)


class ModularToolHandlers:
    """Main tool handlers orchestrator using the registry pattern"""

    def __init__(self, config_manager: ConfigurationManager, context_manager: ContextManager):
        self.config_manager = config_manager
        self.context_manager = context_manager

        # Initialize the tool registry
        self.registry = ToolRegistry()

        # Initialize individual handlers
        self.context_handler = ContextHandler(config_manager, context_manager)
        self.file_handler = FileHandler(config_manager, context_manager)
        self.analysis_handler = AnalysisHandler(config_manager, context_manager)
        self.template_handler = TemplateHandler(config_manager, context_manager)
        self.system_handler = SystemHandler(config_manager, context_manager)
        self.editing_handler = EditingHandler(config_manager, context_manager)

        # Register all handlers with the registry
        self._register_handlers()

    def _register_handlers(self):
        """Register all handler tools with the registry"""
        handlers = [
            self.context_handler,
            self.file_handler,
            self.analysis_handler,
            self.template_handler,
            self.system_handler,
            self.editing_handler,
        ]

        for handler in handlers:
            self.registry.register_handler_tools(handler)

    def get_all_tools(self) -> List[Tool]:
        """Get all available tools from the registry"""
        return self.registry.get_all_tools()

    async def handle_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Handle tool execution using the registry"""
        return await self.registry.handle_tool(name, arguments)

    def get_tools_by_category(self) -> Dict[str, List[str]]:
        """Get tools organized by category"""
        return self.registry.list_tools_by_category()

    def get_handler_info(self) -> Dict[str, Any]:
        """Get information about all registered handlers"""
        return {
            "total_tools": len(self.registry.get_all_tools()),
            "tools_by_category": self.get_tools_by_category(),
            "handlers": [
                {"name": handler.__class__.__name__, "tools": handler.get_tool_names()}
                for handler in [
                    self.context_handler,
                    self.file_handler,
                    self.analysis_handler,
                    self.template_handler,
                    self.system_handler,
                    self.editing_handler,
                ]
            ],
        }

    @staticmethod
    def get_handlers() -> Dict[str, Any]:
        """Get all available tool handlers"""
        # Return empty dict since this method is not used in the current architecture
        return {}


# Backward compatibility - maintain the same interface as the original ToolHandlers
class ToolHandlers(ModularToolHandlers):
    """Backward compatible wrapper for the modular tool handlers"""


def get_all_handlers() -> Dict[str, Type[BaseHandler]]:
    """Get all available tool handlers"""
    # Return empty dict since this function is not used in the current architecture
    return {}


def register_all_handlers(registry: ToolRegistry) -> List[str]:
    """Register all handlers with the tool registry"""
    # This function is not used in the current architecture
    logger.info("Handler registration not needed in current architecture")
    return []
