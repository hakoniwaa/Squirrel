"""
Specialized helpers for testing ModularMCPServer with optimized patterns.

This module provides pre-configured server instances, mock setups, and common
test scenarios to make server testing faster and more reliable.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

from coder_mcp.core.config import ServerConfig
from coder_mcp.server import ModularMCPServer
from tests.helpers.mocks import create_mock_context_manager


class ServerTestBuilder:
    """Builder for creating pre-configured test servers with optimized mocking."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset to default configuration."""
        self._workspace_root = Path("/test")
        self._initialized = True
        self._with_config_manager = True
        self._with_context_manager = True
        self._with_tool_handlers = True
        self._mock_tools = ["read_file", "write_file", "analyze_code"]
        self._custom_tool_responses = {}
        self._health_status = "healthy"
        self._init_errors = []
        self._server_config = None
        return self

    def with_workspace(self, workspace_root: Path):
        """Set workspace root."""
        self._workspace_root = workspace_root
        return self

    def with_server_config(self, config: ServerConfig):
        """Set a specific server config."""
        self._server_config = config
        return self

    def not_initialized(self):
        """Create server that isn't initialized."""
        self._initialized = False
        return self

    def without_config_manager(self):
        """Create server without config manager."""
        self._with_config_manager = False
        return self

    def without_context_manager(self):
        """Create server without context manager."""
        self._with_context_manager = False
        return self

    def without_tool_handlers(self):
        """Create server without tool handlers."""
        self._with_tool_handlers = False
        return self

    def with_tools(self, tools: List[str]):
        """Set available tools."""
        self._mock_tools = tools
        return self

    def with_tool_response(self, tool_name: str, response: Any):
        """Set custom response for a tool."""
        self._custom_tool_responses[tool_name] = response
        return self

    def with_health_status(self, status: str):
        """Set health status."""
        self._health_status = status
        return self

    def with_init_errors(self, errors: List[str]):
        """Add initialization errors."""
        self._init_errors = errors
        return self

    def build(self) -> ModularMCPServer:
        """Build the configured server."""
        # Create server instance
        workspace_arg = self._server_config or self._workspace_root
        server = ModularMCPServer(workspace_root=workspace_arg)

        # Set initialization state
        server._initialized = self._initialized
        server._initialization_errors = self._init_errors.copy()
        server._partial_initialization = bool(self._init_errors)

        # Setup config manager
        if self._with_config_manager:
            server.config_manager = Mock()
            server.config_manager.health_check.return_value = {"status": self._health_status}
            server.config_manager.validate_configuration.return_value = {"valid": True}
            server.config_manager.get_summary.return_value = {
                "providers": "redis",
                "features": "enabled",
            }
        else:
            server.config_manager = None

        # Setup context manager
        if self._with_context_manager:
            server.context_manager = create_mock_context_manager()
        else:
            server.context_manager = None

        # Setup tool handlers
        if self._with_tool_handlers:
            server.tool_handlers = Mock()
            server.tool_handlers.get_all_tools.return_value = [
                {"name": tool, "description": f"Mock {tool}"} for tool in self._mock_tools
            ]

            # Setup tool responses
            async def mock_handle_tool(tool_name: str, arguments: Dict[str, Any]):
                if tool_name in self._custom_tool_responses:
                    return self._custom_tool_responses[tool_name]
                return f"Mock response for {tool_name}"

            server.tool_handlers.handle_tool = AsyncMock(side_effect=mock_handle_tool)
        else:
            server.tool_handlers = None

        # Setup response handler
        server.response_handler = Mock()
        server.response_handler.process_tool_result.return_value = "Processed result"

        return server


class ServerTestScenarios:
    """Pre-configured test scenarios for common server testing patterns."""

    @staticmethod
    def healthy_server() -> ModularMCPServer:
        """Create a fully functional healthy server."""
        return ServerTestBuilder().build()

    @staticmethod
    def server_with_partial_failure() -> ModularMCPServer:
        """Create server with partial component failures."""
        return (
            ServerTestBuilder()
            .without_context_manager()
            .with_init_errors(["Context manager initialization failed"])
            .build()
        )

    @staticmethod
    def uninitialized_server() -> ModularMCPServer:
        """Create server that hasn't been initialized."""
        return ServerTestBuilder().not_initialized().build()

    @staticmethod
    def server_with_custom_tools(
        tools: List[str], responses: Dict[str, Any] = None
    ) -> ModularMCPServer:
        """Create server with specific tools and responses."""
        builder = ServerTestBuilder().with_tools(tools)
        if responses:
            for tool, response in responses.items():
                builder = builder.with_tool_response(tool, response)
        return builder.build()

    @staticmethod
    def minimal_server() -> ModularMCPServer:
        """Create minimal server with only basic components."""
        return (
            ServerTestBuilder()
            .without_context_manager()
            .without_tool_handlers()
            .with_tools([])
            .build()
        )


class ServerAssertions:
    """Specialized assertions for server testing."""

    @staticmethod
    def assert_server_healthy(server: ModularMCPServer):
        """Assert server is in healthy state."""
        assert server._initialized is True
        assert server._partial_initialization is False
        assert len(server._initialization_errors) == 0

    @staticmethod
    def assert_server_partial(server: ModularMCPServer):
        """Assert server is in partial failure state."""
        assert server._initialized is True
        assert server._partial_initialization is True
        assert len(server._initialization_errors) > 0

    @staticmethod
    async def assert_tool_callable(
        server: ModularMCPServer, tool_name: str, arguments: Dict[str, Any] = None
    ):
        """Assert that a tool can be called successfully."""
        arguments = arguments or {}
        result = await server.handle_tool_call(tool_name, arguments)
        assert result is not None

    @staticmethod
    async def assert_health_check_valid(server: ModularMCPServer):
        """Assert health check returns valid structure."""
        health = await server.health_check()
        assert "status" in health
        assert "initialized" in health
        assert "components" in health
        assert "config" in health["components"]


class ServerMockManager:
    """Centralized mock management for server components."""

    def __init__(self):
        self.mocks = {}
        self.patches = []

    def mock_configuration_manager(self, config_data: Dict[str, Any] = None):
        """Mock ConfigurationManager with optional config data."""
        config_data = config_data or {"providers": "redis", "features": "enabled"}

        mock_config = Mock()
        mock_config.health_check.return_value = {"status": "healthy"}
        mock_config.validate_configuration.return_value = {"valid": True}
        mock_config.get_summary.return_value = config_data
        mock_config.is_ai_enabled.return_value = True
        mock_config.get_ai_limits.return_value = {"max_tokens": 4096}

        self.mocks["config_manager"] = mock_config
        return mock_config

    def mock_context_manager(self):
        """Mock ContextManager with realistic behavior."""
        mock_context = create_mock_context_manager()
        self.mocks["context_manager"] = mock_context
        return mock_context

    def mock_tool_handlers(self, tools: List[str] = None):
        """Mock ToolHandlers with configurable tools."""
        tools = tools or ["read_file", "write_file", "analyze_code"]

        mock_handlers = Mock()
        mock_handlers.get_all_tools.return_value = [
            {"name": tool, "description": f"Mock {tool}"} for tool in tools
        ]

        async def mock_handle_tool(tool_name: str, arguments: Dict[str, Any]):
            return f"Mock response for {tool_name} with args {arguments}"

        mock_handlers.handle_tool = AsyncMock(side_effect=mock_handle_tool)
        self.mocks["tool_handlers"] = mock_handlers
        return mock_handlers

    def patch_server_components(self):
        """Apply patches for server component initialization."""
        config_patch = patch("coder_mcp.server.ConfigurationManager")
        context_patch = patch("coder_mcp.server.ContextManager")
        tools_patch = patch("coder_mcp.server.ToolHandlers")

        # Start patches
        mock_config_class = config_patch.start()
        mock_context_class = context_patch.start()
        mock_tools_class = tools_patch.start()

        # Configure mocks
        mock_config_class.return_value = self.mock_configuration_manager()
        mock_context_class.return_value = self.mock_context_manager()
        mock_tools_class.return_value = self.mock_tool_handlers()

        self.patches.extend([config_patch, context_patch, tools_patch])

        return {
            "config_manager": mock_config_class,
            "context_manager": mock_context_class,
            "tool_handlers": mock_tools_class,
        }

    def cleanup(self):
        """Clean up all patches."""
        for patch_obj in self.patches:
            patch_obj.stop()
        self.patches.clear()
        self.mocks.clear()


# Convenience functions
def create_test_server(**kwargs) -> ModularMCPServer:
    """Quick server creation with common defaults."""
    builder = ServerTestBuilder()

    for key, value in kwargs.items():
        if hasattr(builder, f"with_{key}"):
            getattr(builder, f"with_{key}")(value)
        elif hasattr(builder, key):
            getattr(builder, key)()

    return builder.build()


async def quick_server_test(
    server: ModularMCPServer, tool_name: str, arguments: Dict[str, Any] = None
) -> Any:
    """Quick test of server tool functionality."""
    arguments = arguments or {}
    return await server.handle_tool_call(tool_name, arguments)


def patch_server_for_test():
    """Decorator to automatically patch server components for a test."""

    def decorator(test_func):
        async def wrapper(*args, **kwargs):
            mock_manager = ServerMockManager()
            mock_manager.patch_server_components()

            try:
                if asyncio.iscoroutinefunction(test_func):
                    return await test_func(*args, **kwargs)
                else:
                    return test_func(*args, **kwargs)
            finally:
                mock_manager.cleanup()

        return wrapper

    return decorator
