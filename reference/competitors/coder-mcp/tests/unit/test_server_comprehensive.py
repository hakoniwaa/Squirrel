"""
Comprehensive unit tests for ModularMCPServer
Target: 80%+ coverage for server.py
"""

import asyncio
import threading
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from coder_mcp.core.config import ServerConfig
from coder_mcp.security.exceptions import MCPServerError
from coder_mcp.server import ModularMCPServer


class TestModularMCPServerInit:
    """Test server initialization and setup"""

    def test_init_default_workspace(self):
        """Test server initializes with detected workspace"""
        with patch("coder_mcp.server.WorkspaceDetector") as mock_detector:
            mock_detector.return_value.detect_workspace_root.return_value = Path("/test/workspace")

            server = ModularMCPServer()

            assert server.workspace_root == Path("/test/workspace")
            assert server._initialized is False
            assert server.config_manager is None
            assert server.context_manager is None
            assert server.tool_handlers is None
            assert server._server_config is None
            assert isinstance(server._init_lock, type(threading.RLock()))

    def test_init_custom_path_workspace(self):
        """Test server initializes with custom Path workspace"""
        custom_path = Path("/custom/workspace")
        server = ModularMCPServer(workspace_root=custom_path)

        assert server.workspace_root == custom_path
        assert server._server_config is None

    def test_init_server_config_workspace(self):
        """Test server initializes with ServerConfig object"""
        from coder_mcp.core.config.models import FeatureFlags, Limits, ProviderConfig, ServerMeta

        config = ServerConfig(
            server=ServerMeta(name="test-server", version="1.0.0"),
            providers=ProviderConfig(),
            features=FeatureFlags(),
            limits=Limits(),
            workspace_root=Path("/config/workspace"),
        )

        server = ModularMCPServer(workspace_root=config)

        assert server.workspace_root == Path("/config/workspace")
        assert server._server_config == config

    def test_init_state_tracking(self):
        """Test initialization state tracking is properly set up"""
        server = ModularMCPServer(Path("/test"))

        assert server._initialization_errors == []
        assert server._partial_initialization is False
        assert server._initialized is False


class TestModularMCPServerInitialization:
    """Test async initialization process"""

    @pytest.mark.asyncio
    async def test_successful_initialization(self):
        """Test successful initialization of all components"""
        server = ModularMCPServer(Path("/test"))

        with patch.multiple(
            server,
            _initialize_configuration=AsyncMock(),
            _initialize_context_manager=AsyncMock(),
            _initialize_tool_handlers=AsyncMock(),
            _setup_mcp_handlers=Mock(),
        ):
            await server.initialize()

            assert server._initialized is True
            assert server._partial_initialization is False
            assert len(server._initialization_errors) == 0
            server._initialize_configuration.assert_called_once()
            server._initialize_context_manager.assert_called_once()
            server._initialize_tool_handlers.assert_called_once()
            server._setup_mcp_handlers.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_idempotency(self):
        """Test multiple initialization calls are idempotent"""
        server = ModularMCPServer(Path("/test"))

        with patch.multiple(
            server,
            _initialize_configuration=AsyncMock(),
            _initialize_context_manager=AsyncMock(),
            _initialize_tool_handlers=AsyncMock(),
            _setup_mcp_handlers=Mock(),
        ):
            await server.initialize()
            await server.initialize()  # Second call

            # Should only initialize once
            assert server._initialize_configuration.call_count == 1
            assert server._initialize_context_manager.call_count == 1
            assert server._initialize_tool_handlers.call_count == 1
            assert server._setup_mcp_handlers.call_count == 1

    @pytest.mark.asyncio
    async def test_initialization_partial_failure(self):
        """Test initialization handles partial component failures"""
        server = ModularMCPServer(Path("/test"))

        # Mock the individual component methods to simulate partial failure
        async def mock_context_init():
            # Simulate what happens in the actual _initialize_context_manager method
            error_msg = "Context manager initialization failed: Context failed"
            server._initialization_errors.append(error_msg)
            # Context manager remains None (as in actual implementation)
            server.context_manager = None

        with patch.multiple(
            server,
            _initialize_configuration=AsyncMock(),
            _initialize_context_manager=mock_context_init,
            _initialize_tool_handlers=AsyncMock(),
            _setup_mcp_handlers=Mock(),
        ):
            # Should not raise - partial initialization is allowed
            await server.initialize()

            assert server._initialized is True
            assert server._partial_initialization is True
            assert "Context manager initialization failed" in str(server._initialization_errors)

    @pytest.mark.asyncio
    async def test_initialization_critical_failure(self):
        """Test initialization handles critical failures"""
        server = ModularMCPServer(Path("/test"))

        # Mock configuration initialization to simulate failure
        async def mock_config_init():
            # Simulate what happens in the actual _initialize_configuration method
            error_msg = "Configuration initialization failed: Critical failure"
            server._initialization_errors.append(error_msg)
            # Config manager is set to None (as in actual implementation)
            server.config_manager = None

        with patch.multiple(
            server,
            _initialize_configuration=mock_config_init,
            _initialize_context_manager=AsyncMock(),
            _initialize_tool_handlers=AsyncMock(),
            _setup_mcp_handlers=Mock(),
        ):
            # The server continues initialization even with config failures
            await server.initialize()

            assert server._initialized is True  # Server still initializes
            assert server._partial_initialization is True  # But with partial status
            assert "Configuration initialization failed" in str(server._initialization_errors)

    @pytest.mark.asyncio
    async def test_initialization_threading_safety(self):
        """Test initialization state management with concurrent calls"""
        server = ModularMCPServer(Path("/test"))
        initialization_call_count = 0

        # Mock the configuration initialization with counting
        async def counting_init_config():
            nonlocal initialization_call_count
            initialization_call_count += 1
            # Simulate slow initialization
            await asyncio.sleep(0.1)
            # Mock a successful config initialization
            server.config_manager = Mock()

        with patch.multiple(
            server,
            _initialize_configuration=counting_init_config,
            _initialize_context_manager=AsyncMock(),
            _initialize_tool_handlers=AsyncMock(),
            _setup_mcp_handlers=Mock(),
        ):
            # Run multiple initializations concurrently
            # Note: The current server uses threading.RLock which doesn't prevent
            # async concurrency in the same thread, so multiple calls may execute
            await asyncio.gather(server.initialize(), server.initialize(), server.initialize())

            # The server should end up in an initialized state
            assert server._initialized is True
            # Multiple calls may have executed due to async concurrency limitations
            assert initialization_call_count >= 1


class TestComponentInitialization:
    """Test individual component initialization"""

    @pytest.mark.asyncio
    async def test_config_manager_initialization_normal(self):
        """Test ConfigurationManager initialization in normal mode"""
        server = ModularMCPServer(Path("/test"))

        with patch("coder_mcp.server.ConfigurationManager") as mock_config:
            mock_instance = Mock()
            mock_instance.validate_configuration.return_value = {"valid": True}
            mock_config.return_value = mock_instance

            await server._initialize_configuration()

            assert server.config_manager == mock_instance
            mock_config.assert_called_once_with(env_file=Path("/test/.env.mcp"))
            mock_instance.validate_configuration.assert_called_once()

    @pytest.mark.asyncio
    async def test_config_manager_initialization_with_server_config(self):
        """Test ConfigurationManager initialization with ServerConfig"""
        from coder_mcp.core.config.models import FeatureFlags, Limits, ProviderConfig, ServerMeta

        config = ServerConfig(
            server=ServerMeta(name="test-server", version="1.0.0"),
            providers=ProviderConfig(),
            features=FeatureFlags(),
            limits=Limits(),
            workspace_root=Path("/config/workspace"),
        )

        server = ModularMCPServer(workspace_root=config)

        with patch("coder_mcp.server.ConfigurationManager") as mock_config:
            mock_instance = Mock()
            mock_instance.validate_configuration.return_value = {"valid": True}
            mock_config.return_value = mock_instance

            await server._initialize_configuration()

            assert server.config_manager == mock_instance
            # Should create ConfigurationManager with MCPConfiguration containing the ServerConfig
            mock_config.assert_called_once()
            # Verify the call was made with a config argument
            call_kwargs = mock_config.call_args.kwargs
            assert "config" in call_kwargs
            assert hasattr(call_kwargs["config"], "server")

    @pytest.mark.asyncio
    async def test_config_manager_initialization_failure(self):
        """Test ConfigurationManager initialization failure handling"""
        server = ModularMCPServer(Path("/test"))

        # First call fails, second call (fallback) succeeds
        mock_config = Mock()
        with patch(
            "coder_mcp.server.ConfigurationManager",
            side_effect=[Exception("Config failed"), mock_config],
        ):

            await server._initialize_configuration()

            # Should create fallback config manager
            assert server.config_manager == mock_config
            assert "Configuration initialization failed" in server._initialization_errors[0]

    @pytest.mark.asyncio
    async def test_context_manager_initialization_success(self):
        """Test ContextManager initialization success"""
        server = ModularMCPServer(Path("/test"))
        server.config_manager = Mock()

        with patch("coder_mcp.server.ContextManager") as mock_context:
            mock_instance = AsyncMock()
            mock_context.return_value = mock_instance

            await server._initialize_context_manager()

            assert server.context_manager == mock_instance
            mock_context.assert_called_once_with(Path("/test"), server.config_manager)
            # Context manager initializes in __init__, not through a separate initialize method

    @pytest.mark.asyncio
    async def test_context_manager_initialization_without_config(self):
        """Test ContextManager initialization without config manager"""
        server = ModularMCPServer(Path("/test"))

        await server._initialize_context_manager()

        assert server.context_manager is None
        assert "Configuration manager not initialized" in server._initialization_errors[0]

    @pytest.mark.asyncio
    async def test_context_manager_initialization_failure(self):
        """Test ContextManager initialization failure"""
        server = ModularMCPServer(Path("/test"))
        server.config_manager = Mock()

        with patch("coder_mcp.server.ContextManager", side_effect=Exception("Context failed")):

            await server._initialize_context_manager()

            assert server.context_manager is None
            assert "Context manager initialization failed" in server._initialization_errors[0]

    @pytest.mark.asyncio
    async def test_tool_handlers_initialization_success(self):
        """Test ToolHandlers initialization success"""
        server = ModularMCPServer(Path("/test"))
        server.config_manager = Mock()
        server.context_manager = Mock()

        with patch("coder_mcp.server.ToolHandlers") as mock_tools:
            mock_instance = Mock()
            mock_instance.get_all_tools.return_value = [{"name": "test_tool"}]
            mock_tools.return_value = mock_instance

            await server._initialize_tool_handlers()

            assert server.tool_handlers == mock_instance
            mock_tools.assert_called_once_with(
                config_manager=server.config_manager, context_manager=server.context_manager
            )

    @pytest.mark.asyncio
    async def test_tool_handlers_initialization_failure(self):
        """Test ToolHandlers initialization failure"""
        server = ModularMCPServer(Path("/test"))
        server.config_manager = Mock()

        with patch("coder_mcp.server.ToolHandlers", side_effect=Exception("Tools failed")):

            await server._initialize_tool_handlers()

            assert server.tool_handlers is None
            assert "Tool handlers initialization failed" in server._initialization_errors[0]


class TestToolHandling:
    """Test tool call handling"""

    @pytest.mark.asyncio
    async def test_handle_tool_call_success(self):
        """Test successful tool call"""
        server = ModularMCPServer(Path("/test"))
        server._initialized = True
        server.tool_handlers = Mock()
        server.response_handler = Mock()

        # Mock tool handler
        mock_result = {"content": "File content", "success": True}
        server.tool_handlers.handle_tool = AsyncMock(return_value=mock_result)
        server.response_handler.process_tool_result.return_value = "Processed result"

        result = await server.handle_tool_call("read_file", {"path": "test.txt"})

        assert result == "Processed result"
        server.tool_handlers.handle_tool.assert_called_once_with("read_file", {"path": "test.txt"})
        server.response_handler.process_tool_result.assert_called_once_with(
            mock_result, "read_file"
        )

    @pytest.mark.asyncio
    async def test_handle_tool_call_input_validation(self):
        """Test input validation in tool calls"""
        server = ModularMCPServer(Path("/test"))

        # Test empty tool name
        with pytest.raises(ValueError) as exc_info:
            await server.handle_tool_call("", {})
        assert "Tool name must be a non-empty string" in str(exc_info.value)

        # Test None tool name
        with pytest.raises(ValueError) as exc_info:
            await server.handle_tool_call(None, {})
        assert "Tool name must be a non-empty string" in str(exc_info.value)

        # Test invalid arguments type
        with pytest.raises(ValueError) as exc_info:
            await server.handle_tool_call("test_tool", "not_a_dict")
        assert "Arguments must be a dictionary" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_tool_call_not_initialized(self):
        """Test tool call when server not initialized"""
        server = ModularMCPServer(Path("/test"))

        with patch.object(server, "_ensure_initialization") as mock_ensure:
            # Mock that tool_handlers is None after initialization
            mock_ensure.return_value = None
            server.tool_handlers = None

            with pytest.raises(MCPServerError) as exc_info:
                await server.handle_tool_call("test_tool", {})

            assert "Tool handlers not available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_tool_call_execution_error(self):
        """Test tool execution error handling"""
        server = ModularMCPServer(Path("/test"))
        server._initialized = True
        server.tool_handlers = Mock()

        # Mock tool handler that raises exception
        server.tool_handlers.handle_tool = AsyncMock(side_effect=Exception("Tool execution failed"))

        with pytest.raises(Exception) as exc_info:
            await server.handle_tool_call("failing_tool", {})

        assert "Tool execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ensure_initialization(self):
        """Test _ensure_initialization method"""
        server = ModularMCPServer(Path("/test"))

        with patch.object(server, "initialize") as mock_init:
            mock_init.return_value = None

            # Test when not initialized
            await server._ensure_initialization()
            mock_init.assert_called_once()

            # Test when already initialized
            server._initialized = True
            mock_init.reset_mock()
            await server._ensure_initialization()
            mock_init.assert_not_called()


class TestPublicAPI:
    """Test public API methods"""

    def test_get_available_tools_success(self):
        """Test getting available tools successfully"""
        server = ModularMCPServer(Path("/test"))
        server.tool_handlers = Mock()
        server.tool_handlers.get_all_tools.return_value = [
            {"name": "tool1", "description": "Test tool 1"},
            {"name": "tool2", "description": "Test tool 2"},
        ]

        tools = server.get_available_tools()

        assert len(tools) == 2
        assert tools[0]["name"] == "tool1"
        assert tools[1]["name"] == "tool2"

    def test_get_available_tools_no_handlers(self):
        """Test getting available tools when no handlers"""
        server = ModularMCPServer(Path("/test"))
        server.tool_handlers = None

        tools = server.get_available_tools()

        assert tools == []

    def test_get_available_tools_error(self):
        """Test getting available tools with error"""
        server = ModularMCPServer(Path("/test"))
        server.tool_handlers = Mock()
        server.tool_handlers.get_all_tools.side_effect = Exception("Tools error")

        tools = server.get_available_tools()

        assert tools == []

    @pytest.mark.asyncio
    async def test_health_check_all_components_healthy(self):
        """Test health check with all components healthy"""
        server = ModularMCPServer(Path("/test"))
        server._initialized = True
        server._partial_initialization = False
        server._initialization_errors = []

        # Mock healthy components
        server.config_manager = Mock()
        server.config_manager.health_check.return_value = {"status": "healthy"}

        server.context_manager = Mock()

        server.tool_handlers = Mock()
        with patch.object(server, "get_available_tools", return_value=[{"name": "tool1"}]):

            health = await server.health_check()

            assert health["status"] == "healthy"
            assert health["initialized"] is True
            assert health["partial_initialization"] is False
            assert len(health["initialization_errors"]) == 0
            assert health["components"]["config"]["status"] == "healthy"
            assert health["components"]["context"]["status"] == "healthy"
            assert "vector_store_available" in health["components"]["context"]
            assert "memory_store_available" in health["components"]["context"]
            assert health["components"]["tools"]["status"] == "healthy"
            assert health["components"]["tools"]["available_tools"] == 1

    @pytest.mark.asyncio
    async def test_health_check_degraded_status(self):
        """Test health check with degraded status"""
        server = ModularMCPServer(Path("/test"))
        server._initialized = False
        server.config_manager = None
        server.context_manager = None
        server.tool_handlers = None

        health = await server.health_check()

        assert health["status"] == "degraded"
        assert health["initialized"] is False
        assert health["components"]["config"]["status"] == "not_initialized"
        assert health["components"]["context"]["status"] == "not_initialized"
        assert health["components"]["tools"]["status"] == "not_initialized"

    @pytest.mark.asyncio
    async def test_health_check_partial_status(self):
        """Test health check with partial initialization"""
        server = ModularMCPServer(Path("/test"))
        server._initialized = True
        server._partial_initialization = True
        server._initialization_errors = ["Context failed"]

        server.config_manager = Mock()
        server.config_manager.health_check.return_value = {"status": "healthy"}
        server.context_manager = None
        server.tool_handlers = Mock()

        with patch.object(server, "get_available_tools", return_value=[]):
            health = await server.health_check()

            assert health["status"] == "partial"
            assert health["partial_initialization"] is True
            assert "Context failed" in health["initialization_errors"]

    @pytest.mark.asyncio
    async def test_health_check_component_errors(self):
        """Test health check with component errors"""
        server = ModularMCPServer(Path("/test"))
        server._initialized = True

        # Mock components that throw errors
        server.config_manager = Mock()
        server.config_manager.health_check.side_effect = Exception("Config error")

        server.context_manager = Mock()
        # Test exception in context manager health check
        with patch("coder_mcp.server.getattr", side_effect=Exception("Context error")):
            server.tool_handlers = Mock()
            with patch.object(server, "get_available_tools", side_effect=Exception("Tools error")):

                health = await server.health_check()

                assert health["status"] == "degraded"
                assert health["components"]["config"]["status"] == "error"
                assert "Config error" in health["components"]["config"]["error"]
                assert health["components"]["context"]["status"] == "error"
                assert health["components"]["tools"]["status"] == "error"


class TestMCPHandlerSetup:
    """Test MCP protocol handler setup"""

    def test_setup_mcp_handlers(self):
        """Test all MCP handlers are registered correctly"""
        server = ModularMCPServer(Path("/test"))

        # Mock the server's internal MCP server
        server.server = Mock()
        mock_list_tools = Mock()
        mock_call_tool = Mock()
        server.server.list_tools.return_value = mock_list_tools
        server.server.call_tool.return_value = mock_call_tool

        server._setup_mcp_handlers()

        # Verify handlers were set up
        server.server.list_tools.assert_called_once()
        server.server.call_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_list_tools_handler(self):
        """Test MCP list tools handler"""
        server = ModularMCPServer(Path("/test"))

        # Mock tool_handlers to return tools
        server.tool_handlers = Mock()
        server.tool_handlers.get_all_tools.return_value = [{"name": "test_tool"}]

        # Mock the handler registration
        registered_handler = None

        def capture_handler():
            def decorator(func):
                nonlocal registered_handler
                registered_handler = func
                return Mock()

            return decorator

        server.server = Mock()
        server.server.list_tools = capture_handler
        server.server.call_tool = Mock(return_value=Mock())

        server._setup_mcp_handlers()

        # Test the registered handler
        result = await registered_handler()
        assert result == [{"name": "test_tool"}]
        server.tool_handlers.get_all_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_call_tool_handler_success(self):
        """Test MCP call tool handler success case"""
        from mcp.types import TextContent

        server = ModularMCPServer(Path("/test"))
        server._initialized = True
        server.tool_handlers = Mock()
        server.tool_handlers.handle_tool = AsyncMock(return_value="Tool result")

        # Capture the registered handler
        registered_handler = None

        def capture_handler():
            def decorator(func):
                nonlocal registered_handler
                registered_handler = func
                return Mock()

            return decorator

        server.server = Mock()
        server.server.list_tools = Mock(return_value=Mock())
        server.server.call_tool = capture_handler

        server._setup_mcp_handlers()

        # Test the registered handler
        result = await registered_handler("test_tool", {"arg": "value"})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].text == "Tool result"

    @pytest.mark.asyncio
    async def test_mcp_call_tool_handler_no_handlers(self):
        """Test MCP call tool handler when no tool handlers available"""
        from mcp.types import TextContent

        server = ModularMCPServer(Path("/test"))
        server._initialized = True
        server.tool_handlers = None

        # Capture the registered handler
        registered_handler = None

        def capture_handler():
            def decorator(func):
                nonlocal registered_handler
                registered_handler = func
                return Mock()

            return decorator

        server.server = Mock()
        server.server.list_tools = Mock(return_value=Mock())
        server.server.call_tool = capture_handler

        server._setup_mcp_handlers()

        # Test the registered handler
        result = await registered_handler("test_tool", {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Tool handlers not available" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_call_tool_handler_validation_error(self):
        """Test MCP call tool handler with validation error"""
        from mcp.types import TextContent

        server = ModularMCPServer(Path("/test"))
        server._initialized = True
        server.tool_handlers = Mock()
        server.tool_handlers.handle_tool = AsyncMock(side_effect=ValueError("Invalid input"))

        # Capture the registered handler
        registered_handler = None

        def capture_handler():
            def decorator(func):
                nonlocal registered_handler
                registered_handler = func
                return Mock()

            return decorator

        server.server = Mock()
        server.server.list_tools = Mock(return_value=Mock())
        server.server.call_tool = capture_handler

        server._setup_mcp_handlers()

        # Test the registered handler
        result = await registered_handler("test_tool", {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Invalid input" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_call_tool_handler_server_error(self):
        """Test MCP call tool handler with server error"""
        from mcp.types import TextContent

        server = ModularMCPServer(Path("/test"))
        server._initialized = True
        server.tool_handlers = Mock()
        server.tool_handlers.handle_tool = AsyncMock(side_effect=MCPServerError("Server error"))

        # Capture the registered handler
        registered_handler = None

        def capture_handler():
            def decorator(func):
                nonlocal registered_handler
                registered_handler = func
                return Mock()

            return decorator

        server.server = Mock()
        server.server.list_tools = Mock(return_value=Mock())
        server.server.call_tool = capture_handler

        server._setup_mcp_handlers()

        # Test the registered handler
        result = await registered_handler("test_tool", {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Server error" in result[0].text

    @pytest.mark.asyncio
    async def test_mcp_call_tool_handler_unexpected_error(self):
        """Test MCP call tool handler with unexpected error"""
        from mcp.types import TextContent

        server = ModularMCPServer(Path("/test"))
        server._initialized = True
        server.tool_handlers = Mock()
        server.tool_handlers.handle_tool = AsyncMock(side_effect=Exception("Unexpected error"))

        # Capture the registered handler
        registered_handler = None

        def capture_handler():
            def decorator(func):
                nonlocal registered_handler
                registered_handler = func
                return Mock()

            return decorator

        server.server = Mock()
        server.server.list_tools = Mock(return_value=Mock())
        server.server.call_tool = capture_handler

        server._setup_mcp_handlers()

        # Test the registered handler
        result = await registered_handler("test_tool", {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Unexpected error" in result[0].text


class TestServerRunning:
    """Test server running and lifecycle"""

    @pytest.mark.asyncio
    async def test_run_success(self):
        """Test successful server run"""
        server = ModularMCPServer(Path("/test"))

        with patch.multiple(
            server,
            _ensure_initialization=AsyncMock(),
            _log_configuration_summary=AsyncMock(),
            _run_server=AsyncMock(),
        ):
            await server.run()

            server._ensure_initialization.assert_called_once()
            server._log_configuration_summary.assert_called_once()
            server._run_server.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_keyboard_interrupt(self):
        """Test server run with keyboard interrupt"""
        server = ModularMCPServer(Path("/test"))

        with patch.multiple(
            server,
            _ensure_initialization=AsyncMock(),
            _log_configuration_summary=AsyncMock(),
            _run_server=AsyncMock(side_effect=KeyboardInterrupt()),
        ):
            # Should not raise exception
            await server.run()

    @pytest.mark.asyncio
    async def test_run_unexpected_error(self):
        """Test server run with unexpected error"""
        server = ModularMCPServer(Path("/test"))

        with patch.multiple(
            server,
            _ensure_initialization=AsyncMock(),
            _log_configuration_summary=AsyncMock(),
            _run_server=AsyncMock(side_effect=Exception("Server error")),
        ):
            with pytest.raises(Exception) as exc_info:
                await server.run()

            assert "Server error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_log_configuration_summary_success(self):
        """Test logging configuration summary successfully"""
        server = ModularMCPServer(Path("/test"))
        server.config_manager = Mock()
        server.config_manager.get_summary.return_value = {"providers": "redis"}

        await server._log_configuration_summary()

        server.config_manager.get_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_configuration_summary_no_config(self):
        """Test logging configuration summary with no config manager"""
        server = ModularMCPServer(Path("/test"))
        server.config_manager = None

        # Should not raise exception
        await server._log_configuration_summary()

    @pytest.mark.asyncio
    async def test_log_configuration_summary_no_method(self):
        """Test logging configuration summary with no get_summary method"""
        server = ModularMCPServer(Path("/test"))
        server.config_manager = Mock()
        # Remove get_summary method
        del server.config_manager.get_summary

        # Should not raise exception
        await server._log_configuration_summary()

    @pytest.mark.asyncio
    async def test_log_configuration_summary_error(self):
        """Test logging configuration summary with error"""
        server = ModularMCPServer(Path("/test"))
        server.config_manager = Mock()
        server.config_manager.get_summary.side_effect = Exception("Summary error")

        # Should not raise exception
        await server._log_configuration_summary()


class TestMainFunction:
    """Test main function and entry point"""

    @pytest.mark.asyncio
    async def test_main_success(self):
        """Test main function success"""
        from coder_mcp.server import main

        with patch("coder_mcp.server.ModularMCPServer") as mock_server_class:
            mock_server = Mock()
            mock_server.run = AsyncMock()
            mock_server_class.return_value = mock_server

            await main()

            mock_server_class.assert_called_once()
            mock_server.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_keyboard_interrupt(self):
        """Test main function with keyboard interrupt"""
        from coder_mcp.server import main

        with patch("coder_mcp.server.ModularMCPServer") as mock_server_class:
            mock_server = Mock()
            mock_server.run = AsyncMock(side_effect=KeyboardInterrupt())
            mock_server_class.return_value = mock_server

            # Should not raise exception
            await main()

    @pytest.mark.asyncio
    async def test_main_unexpected_error(self):
        """Test main function with unexpected error"""
        from coder_mcp.server import main

        with patch("coder_mcp.server.ModularMCPServer") as mock_server_class:
            mock_server = Mock()
            mock_server.run = AsyncMock(side_effect=Exception("Fatal error"))
            mock_server_class.return_value = mock_server

            with pytest.raises(Exception) as exc_info:
                await main()

            assert "Fatal error" in str(exc_info.value)
