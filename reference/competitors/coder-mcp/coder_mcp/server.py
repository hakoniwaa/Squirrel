#!/usr/bin/env python3
"""
Modular MCP Server - World-Class Architecture
Clean orchestration layer using the new modular components
"""

import asyncio
import logging
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .context.manager import ContextManager
from .core import ConfigurationManager
from .core.config import ServerConfig  # Import ServerConfig for type checking
from .core.config.models import MCPConfiguration
from .security.exceptions import MCPServerError
from .tool_response_handler import ToolResponseHandler
from .tools import ToolHandlers
from .workspace_detector import WorkspaceDetector

# Configure logging to stderr only (stdout is reserved for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # Critical: MCP protocol requires clean stdout
)
logger = logging.getLogger(__name__)


class ModularMCPServer:
    """
    World-class MCP Server with modular architecture

    This server provides:
    - Persistent context management across sessions
    - Intelligent code analysis and suggestions
    - Template-based scaffolding
    - Vector-based semantic search
    - Production-ready security and performance
    """

    def __init__(self, workspace_root: Optional[Union[Path, ServerConfig]] = None):
        self.server: Server = Server("coder-mcp-enhanced")
        self.workspace_detector = WorkspaceDetector()
        self.response_handler = ToolResponseHandler()

        # Handle different input types for workspace_root
        self._server_config: Optional[ServerConfig]
        if isinstance(workspace_root, ServerConfig):
            # Extract workspace from ServerConfig (for tests)
            self.workspace_root = workspace_root.workspace_root
            self._server_config = workspace_root
        else:
            # Handle Path or None (for normal usage)
            self.workspace_root = workspace_root or self.workspace_detector.detect_workspace_root()
            self._server_config = None

        # Thread safety
        self._init_lock = threading.RLock()
        self._initialized = False

        # Core components (lazy initialized)
        self.config_manager: Optional[ConfigurationManager] = None
        self.context_manager: Optional[ContextManager] = None
        self.tool_handlers: Optional[ToolHandlers] = None

        # Track initialization state for components
        self._initialization_errors: List[str] = []
        self._partial_initialization = False

        logger.info("Initializing MCP Server for workspace: %s", self.workspace_root)

    async def initialize(self):
        """Initialize all components with proper error handling"""
        with self._init_lock:
            if self._initialized:
                return

            self._initialization_errors.clear()

            # Initialize each component with individual error handling
            await self._initialize_configuration()
            await self._initialize_context_manager()
            await self._initialize_tool_handlers()

            # Setup MCP handlers regardless of component failures
            self._setup_mcp_handlers()
            self._initialized = True

            if self._initialization_errors:
                self._partial_initialization = True
                logger.warning("Server initialized with errors: %s", self._initialization_errors)
            else:
                logger.info("✅ MCP Server initialized successfully")

    async def _initialize_configuration(self):
        """Initialize configuration manager with error handling"""
        try:
            # Use ServerConfig if provided, otherwise load from file
            if self._server_config:
                # For tests - use provided configuration directly
                test_config = MCPConfiguration(server=self._server_config)
                self.config_manager = ConfigurationManager(config=test_config)
            else:
                # Normal initialization from .env.mcp file
                env_file = self.workspace_root / ".env.mcp"
                self.config_manager = ConfigurationManager(env_file=env_file)

            # Validate configuration
            status = self.config_manager.validate_configuration()
            logger.info("Configuration status: %s", status)

        except Exception as e:  # pylint: disable=broad-except
            error_msg = f"Configuration initialization failed: {str(e)}"
            self._initialization_errors.append(error_msg)
            logger.error("%s", error_msg)
            # Create minimal config for fallback
            try:
                self.config_manager = ConfigurationManager()
            except Exception:  # pylint: disable=broad-except
                # If we can't even create a minimal config, leave it None
                self.config_manager = None

    async def _initialize_context_manager(self):
        """Initialize context manager with error handling"""
        try:
            if not self.config_manager:
                raise ValueError("Configuration manager not initialized")

            self.context_manager = ContextManager(self.workspace_root, self.config_manager)

            # Context manager doesn't have an initialize method - it initializes in __init__

        except Exception as e:  # pylint: disable=broad-except
            error_msg = f"Context manager initialization failed: {str(e)}"
            self._initialization_errors.append(error_msg)
            logger.error("%s", error_msg)
            # Context manager is optional - continue without it

    async def _initialize_tool_handlers(self):
        """Initialize tool handlers with error handling"""
        try:
            if not self.config_manager:
                raise ValueError("Configuration manager not initialized")

            self.tool_handlers = ToolHandlers(
                config_manager=self.config_manager, context_manager=self.context_manager
            )

            # Validate tool handlers have tools available
            available_tools = self.tool_handlers.get_all_tools() if self.tool_handlers else []
            logger.info("Loaded %d tools", len(available_tools))

        except Exception as e:  # pylint: disable=broad-except
            error_msg = f"Tool handlers initialization failed: {str(e)}"
            self._initialization_errors.append(error_msg)
            logger.error("%s", error_msg)
            # Tool handlers are critical - create minimal fallback
            self.tool_handlers = None

    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle tool execution for tests and direct usage"""
        # Input validation
        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError("Tool name must be a non-empty string")

        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a dictionary")

        await self._ensure_initialization()

        if not self.tool_handlers:
            raise MCPServerError("Tool handlers not available - server not properly initialized")

        try:
            result = await self.tool_handlers.handle_tool(tool_name, arguments)
            return self.response_handler.process_tool_result(result, tool_name)

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error executing tool %s: %s", tool_name, e, exc_info=True)
            raise

    async def _ensure_initialization(self):
        """Ensure server is initialized"""
        with self._init_lock:
            if not self._initialized:
                await self.initialize()

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        if not self.tool_handlers:
            return []

        try:
            tools = self.tool_handlers.get_all_tools()
            # Ensure we return the correct type - convert Tool objects to dicts if needed
            if not tools:
                return []

            # If tools is already a list of dicts, return as is
            if isinstance(tools[0], dict):
                return tools

            # Convert Tool objects to dictionaries
            tool_dicts = []
            for tool in tools:
                if hasattr(tool, "dict"):
                    # Pydantic model style
                    tool_dicts.append(tool.model_dump())
                elif hasattr(tool, "__dict__"):
                    # Regular object with __dict__
                    tool_dicts.append(tool.__dict__)
                else:
                    # Convert to dict manually
                    tool_dicts.append(dict(tool))

            return tool_dicts

        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error getting available tools: %s", e)
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of all components"""
        health_status: Dict[str, Any] = {
            "status": "healthy",
            "initialized": self._initialized,
            "partial_initialization": self._partial_initialization,
            "initialization_errors": self._initialization_errors.copy(),
            "components": {},
        }
        components: Dict[str, Any] = health_status["components"]
        components["config"] = self._check_config_health()
        components["context"] = self._check_context_health()
        components["tools"] = self._check_tools_health()

        # Determine overall status
        component_statuses = [comp.get("status", "unknown") for comp in components.values()]
        if "error" in component_statuses or not self._initialized:
            health_status["status"] = "degraded"
        elif self._partial_initialization:
            health_status["status"] = "partial"

        return health_status

    def _check_config_health(self) -> Dict[str, Any]:
        if self.config_manager:
            try:
                if hasattr(self.config_manager, "health_check"):
                    return self.config_manager.health_check()
                return {"status": "healthy", "message": "Configuration manager available"}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "not_initialized"}

    def _check_context_health(self) -> Dict[str, Any]:
        if self.context_manager:
            try:
                return {
                    "status": "healthy",
                    "vector_store_available": bool(
                        getattr(self.context_manager, "vector_store", None)
                    ),
                    "memory_store_available": bool(
                        getattr(self.context_manager, "memory_store", None)
                    ),
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "not_initialized"}

    def _check_tools_health(self) -> Dict[str, Any]:
        if self.tool_handlers:
            try:
                tool_count = len(self.get_available_tools())
                return {"status": "healthy", "available_tools": tool_count}
            except Exception as e:
                return {"status": "error", "error": str(e)}
        return {"status": "not_initialized"}

    def _setup_mcp_handlers(self):
        """Setup MCP protocol handlers"""
        self.server.list_tools()(self._handle_list_tools)
        self.server.call_tool()(self._handle_call_tool)

    async def _handle_list_tools(self):
        """List all available tools"""
        try:
            if not self.tool_handlers:
                return []
            tools = self.tool_handlers.get_all_tools()
            return tools if tools else []
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error listing tools: %s", e)
            return []

    async def _handle_call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool execution with centralized error handling"""
        try:
            await self._ensure_initialization()
            if not self.tool_handlers:
                return [TextContent(type="text", text="❌ Tool handlers not available")]
            result = await self.tool_handlers.handle_tool(name, arguments)
            return [TextContent(type="text", text=result)]
        except ValueError as e:
            return [TextContent(type="text", text=f"❌ Invalid input: {str(e)}")]
        except MCPServerError as e:
            return [TextContent(type="text", text=f"❌ Server error: {str(e)}")]
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Unexpected error executing tool %s: %s", name, e, exc_info=True)
            return [TextContent(type="text", text=f"❌ Unexpected error: {str(e)}")]

    async def run(self):
        """Run the MCP server"""
        try:
            await self._ensure_initialization()
            await self._log_configuration_summary()
            await self._run_server()

        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Server error: %s", e, exc_info=True)
            raise

    async def _log_configuration_summary(self):
        """Log configuration summary"""
        if self.config_manager and hasattr(self.config_manager, "get_summary"):
            try:
                summary = self.config_manager.get_summary()
                logger.info("Server configuration: %s", summary)
            except Exception as e:  # pylint: disable=broad-except
                logger.warning("Could not get configuration summary: %s", e)

    async def _run_server(self):
        """Run the MCP server with stdio"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="coder-mcp-enhanced",
                    server_version="5.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(), experimental_capabilities={}
                    ),
                ),
            )


async def main():
    """Main entry point"""
    try:
        server = ModularMCPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Fatal error: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
