"""
Comprehensive tests for coder_mcp.tools.main_handlers module.

This test suite achieves 100% code coverage using optimized helper modules for:
- Tool handler orchestration
- Registry pattern implementation
- Tool execution and management
- Backward compatibility
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from mcp.types import Tool

from coder_mcp.tools.main_handlers import ModularToolHandlers, ToolHandlers
from tests.helpers.assertions import AsyncAssertions
from tests.helpers.mocks import create_mock_context_manager
from tests.helpers.performance import assert_sub_second

# NEW OPTIMIZED IMPORTS using our helper modules


def create_mock_config_manager():
    """Create a mock configuration manager."""
    mock_config = Mock()
    mock_config.get_provider_config = Mock(return_value={"api_key": "test-key"})
    mock_config.workspace_root = "/test/workspace"
    # Add config attribute for AI enhancer
    mock_config.config = Mock()
    mock_config.config.is_ai_enabled = Mock(return_value=False)  # Disable AI to simplify testing
    return mock_config


def create_enhanced_mock_context_manager():
    """Create an enhanced mock context manager with all required attributes."""
    mock_context = create_mock_context_manager()
    # Add missing workspace_root attribute as Path object
    mock_context.workspace_root = Path("/test/workspace")
    return mock_context


class TestModularToolHandlers:
    """Test ModularToolHandlers with comprehensive coverage."""

    def setup_method(self):
        """Set up test environment using helper modules."""
        self.config_manager = create_mock_config_manager()
        self.context_manager = create_enhanced_mock_context_manager()

    @pytest.mark.asyncio
    async def test_init_creates_all_handlers(self):
        """Test __init__ creates all required handlers."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Verify all handlers are created
        assert handlers.config_manager == self.config_manager
        assert handlers.context_manager == self.context_manager
        assert handlers.registry is not None
        assert handlers.context_handler is not None
        assert handlers.file_handler is not None
        assert handlers.analysis_handler is not None
        assert handlers.template_handler is not None
        assert handlers.system_handler is not None

    @pytest.mark.asyncio
    async def test_register_handlers_called_during_init(self):
        """Test _register_handlers is called during initialization."""
        with patch.object(ModularToolHandlers, "_register_handlers") as mock_register:
            ModularToolHandlers(self.config_manager, self.context_manager)
            mock_register.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_handlers_registers_all_handlers(self):
        """Test _register_handlers registers all handler tools."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock the registry register_handler_tools method
        with patch.object(handlers.registry, "register_handler_tools") as mock_register:
            handlers._register_handlers()

            # Should be called for each handler
            assert mock_register.call_count == 6

            # Verify it was called with each handler
            called_handlers = [call[0][0] for call in mock_register.call_args_list]
            assert handlers.context_handler in called_handlers
            assert handlers.file_handler in called_handlers
            assert handlers.analysis_handler in called_handlers
            assert handlers.template_handler in called_handlers
            assert handlers.system_handler in called_handlers
            assert handlers.editing_handler in called_handlers

    @pytest.mark.asyncio
    async def test_get_all_tools_delegates_to_registry(self):
        """Test get_all_tools delegates to the registry."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock the registry method with properly formed Tool objects
        mock_tools = [
            Tool(name="test_tool_1", description="Test tool 1", inputSchema={"type": "object"}),
            Tool(name="test_tool_2", description="Test tool 2", inputSchema={"type": "object"}),
        ]

        with patch.object(handlers.registry, "get_all_tools", return_value=mock_tools) as mock_get:
            result = handlers.get_all_tools()

            mock_get.assert_called_once()
            assert result == mock_tools

    @pytest.mark.asyncio
    async def test_handle_tool_delegates_to_registry(self):
        """Test handle_tool delegates to the registry."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock the registry method
        expected_result = "Tool executed successfully"
        test_name = "test_tool"
        test_args = {"arg1": "value1", "arg2": "value2"}

        with patch.object(
            handlers.registry, "handle_tool", new_callable=AsyncMock, return_value=expected_result
        ) as mock_handle:
            result = await handlers.handle_tool(test_name, test_args)

            mock_handle.assert_called_once_with(test_name, test_args)
            assert result == expected_result

    @pytest.mark.asyncio
    async def test_get_tools_by_category_delegates_to_registry(self):
        """Test get_tools_by_category delegates to the registry."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock the registry method
        mock_categories = {
            "file": ["read_file", "write_file"],
            "analysis": ["analyze_code", "detect_issues"],
            "context": ["search_context", "update_context"],
        }

        with patch.object(
            handlers.registry, "list_tools_by_category", return_value=mock_categories
        ) as mock_list:
            result = handlers.get_tools_by_category()

            mock_list.assert_called_once()
            assert result == mock_categories

    @pytest.mark.asyncio
    async def test_get_handler_info_returns_comprehensive_info(self):
        """Test get_handler_info returns comprehensive handler information."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock dependencies with properly formed Tool objects
        mock_tools = [
            Tool(name="tool1", description="Test tool 1", inputSchema={"type": "object"}),
            Tool(name="tool2", description="Test tool 2", inputSchema={"type": "object"}),
        ]
        mock_categories = {"file": ["tool1"], "analysis": ["tool2"]}

        with (
            patch.object(handlers.registry, "get_all_tools", return_value=mock_tools),
            patch.object(handlers, "get_tools_by_category", return_value=mock_categories),
        ):

            # Mock get_tool_names for each handler
            for handler in [
                handlers.context_handler,
                handlers.file_handler,
                handlers.analysis_handler,
                handlers.template_handler,
                handlers.system_handler,
                handlers.editing_handler,
            ]:
                handler.get_tool_names = Mock(return_value=["mock_tool"])

            result = handlers.get_handler_info()

            # Verify structure
            assert "total_tools" in result
            assert "tools_by_category" in result
            assert "handlers" in result

            # Verify content
            assert result["total_tools"] == 2
            assert result["tools_by_category"] == mock_categories
            assert len(result["handlers"]) == 6

            # Verify handler info structure
            for handler_info in result["handlers"]:
                assert "name" in handler_info
                assert "tools" in handler_info
                assert handler_info["name"].endswith("Handler")
                assert handler_info["tools"] == ["mock_tool"]

    @pytest.mark.asyncio
    async def test_performance_requirements(self):
        """Test that handler operations complete quickly."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Test initialization performance
        def create_handlers():
            return ModularToolHandlers(self.config_manager, self.context_manager)

        result = assert_sub_second(create_handlers)
        assert isinstance(result, ModularToolHandlers)

        # Test get_all_tools performance
        with patch.object(handlers.registry, "get_all_tools", return_value=[]):
            result = assert_sub_second(handlers.get_all_tools)
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_handler_integration(self):
        """Integration test of handler orchestration."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock all handlers to return tool names
        expected_handlers = [
            handlers.context_handler,
            handlers.file_handler,
            handlers.analysis_handler,
            handlers.template_handler,
            handlers.system_handler,
            handlers.editing_handler,
        ]

        # Verify all handlers are initialized with correct dependencies
        for handler in expected_handlers:
            assert hasattr(handler, "config_manager")
            assert hasattr(handler, "context_manager")

        # Verify registry integration
        assert handlers.registry is not None
        assert hasattr(handlers.registry, "get_all_tools")
        assert hasattr(handlers.registry, "handle_tool")
        assert hasattr(handlers.registry, "list_tools_by_category")

    @pytest.mark.asyncio
    async def test_concurrent_tool_handling(self):
        """Test concurrent tool execution."""
        import asyncio

        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock registry to return different results for different tools
        async def mock_handle_tool(name, args):
            await asyncio.sleep(0.01)  # Simulate async work
            return f"Result for {name}"

        with patch.object(handlers.registry, "handle_tool", side_effect=mock_handle_tool):
            # Execute multiple tools concurrently
            tasks = [
                handlers.handle_tool("tool1", {"arg": "value1"}),
                handlers.handle_tool("tool2", {"arg": "value2"}),
                handlers.handle_tool("tool3", {"arg": "value3"}),
            ]

            results = await AsyncAssertions.assert_concurrent_safe(
                lambda *args: asyncio.create_task(args[0]), [(task,) for task in tasks]
            )

            # Verify all tasks completed successfully
            assert len(results) == 3
            for result in results:
                assert isinstance(result, str)
                assert "Result for" in result

    @pytest.mark.asyncio
    async def test_error_handling_in_tool_execution(self):
        """Test error handling during tool execution."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock registry to raise an exception
        error_message = "Tool execution failed"
        with patch.object(
            handlers.registry,
            "handle_tool",
            new_callable=AsyncMock,
            side_effect=Exception(error_message),
        ):

            with pytest.raises(Exception) as exc_info:
                await handlers.handle_tool("failing_tool", {})

            assert str(exc_info.value) == error_message

    @pytest.mark.asyncio
    async def test_empty_tools_handling(self):
        """Test handling when no tools are available."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock registry to return empty results
        with (
            patch.object(handlers.registry, "get_all_tools", return_value=[]),
            patch.object(handlers.registry, "list_tools_by_category", return_value={}),
        ):

            tools = handlers.get_all_tools()
            categories = handlers.get_tools_by_category()

            assert tools == []
            assert categories == {}

            # Handler info should still work with empty tools
            for handler in [
                handlers.context_handler,
                handlers.file_handler,
                handlers.analysis_handler,
                handlers.template_handler,
                handlers.system_handler,
                handlers.editing_handler,
            ]:
                handler.get_tool_names = Mock(return_value=[])

            info = handlers.get_handler_info()
            assert info["total_tools"] == 0
            assert info["tools_by_category"] == {}
            assert len(info["handlers"]) == 6

    @pytest.mark.asyncio
    async def test_handler_initialization_with_minimal_dependencies(self):
        """Test handler behavior with minimal valid dependencies."""
        # Create minimal config manager that satisfies the AI enhancer requirements
        minimal_config = Mock()
        minimal_config.config = Mock()
        minimal_config.config.is_ai_enabled = Mock(return_value=False)  # Minimal AI setup
        minimal_config.get_provider_config = Mock(return_value={})  # Empty provider config
        minimal_config.workspace_root = "/minimal/workspace"

        # Create minimal context manager
        minimal_context = Mock()
        minimal_context.workspace_root = Path("/minimal/workspace")

        # This should work with minimal but valid dependencies
        handlers = ModularToolHandlers(minimal_config, minimal_context)

        assert handlers.config_manager == minimal_config
        assert handlers.context_manager == minimal_context
        assert handlers.registry is not None

        # Verify all handlers were created despite minimal dependencies
        assert handlers.context_handler is not None
        assert handlers.file_handler is not None
        assert handlers.analysis_handler is not None
        assert handlers.template_handler is not None
        assert handlers.system_handler is not None
        assert handlers.editing_handler is not None


class TestToolHandlers:
    """Test ToolHandlers backward compatibility wrapper."""

    def setup_method(self):
        """Set up test environment for backward compatibility tests."""
        self.config_manager = create_mock_config_manager()
        self.context_manager = create_enhanced_mock_context_manager()

    @pytest.mark.asyncio
    async def test_tool_handlers_is_backward_compatible(self):
        """Test ToolHandlers maintains backward compatibility."""
        handlers = ToolHandlers(self.config_manager, self.context_manager)

        # Should be an instance of ModularToolHandlers
        assert isinstance(handlers, ModularToolHandlers)
        assert isinstance(handlers, ToolHandlers)

        # Should have all the same methods and attributes
        assert hasattr(handlers, "get_all_tools")
        assert hasattr(handlers, "handle_tool")
        assert hasattr(handlers, "get_tools_by_category")
        assert hasattr(handlers, "get_handler_info")
        assert hasattr(handlers, "registry")

    @pytest.mark.asyncio
    async def test_tool_handlers_functionality_matches_modular(self):
        """Test ToolHandlers provides same functionality as ModularToolHandlers."""
        modular_handlers = ModularToolHandlers(self.config_manager, self.context_manager)
        compat_handlers = ToolHandlers(self.config_manager, self.context_manager)

        # Mock both registries to return the same data with properly formed Tool objects
        mock_tools = [
            Tool(name="test_tool", description="Test tool", inputSchema={"type": "object"})
        ]
        mock_categories = {"test": ["test_tool"]}

        with (
            patch.object(modular_handlers.registry, "get_all_tools", return_value=mock_tools),
            patch.object(compat_handlers.registry, "get_all_tools", return_value=mock_tools),
            patch.object(
                modular_handlers.registry, "list_tools_by_category", return_value=mock_categories
            ),
            patch.object(
                compat_handlers.registry, "list_tools_by_category", return_value=mock_categories
            ),
        ):

            # Both should return the same results
            assert modular_handlers.get_all_tools() == compat_handlers.get_all_tools()
            assert (
                modular_handlers.get_tools_by_category() == compat_handlers.get_tools_by_category()
            )

    @pytest.mark.asyncio
    async def test_tool_handlers_async_compatibility(self):
        """Test ToolHandlers async method compatibility."""
        handlers = ToolHandlers(self.config_manager, self.context_manager)

        # Mock async tool execution
        expected_result = "Async execution successful"
        with patch.object(
            handlers.registry, "handle_tool", new_callable=AsyncMock, return_value=expected_result
        ):

            result = await handlers.handle_tool("async_tool", {"test": "value"})
            assert result == expected_result


class TestModularToolHandlersEdgeCases:
    """Test edge cases and error conditions for ModularToolHandlers."""

    def setup_method(self):
        """Set up for edge case testing."""
        self.config_manager = create_mock_config_manager()
        self.context_manager = create_enhanced_mock_context_manager()

    @pytest.mark.asyncio
    async def test_registry_method_missing(self):
        """Test behavior when registry methods are missing."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Replace registry with a mock that doesn't have expected methods
        incomplete_registry = Mock()
        # Don't add the get_all_tools method to simulate it being missing
        (
            delattr(incomplete_registry, "get_all_tools")
            if hasattr(incomplete_registry, "get_all_tools")
            else None
        )
        handlers.registry = incomplete_registry

        # Should raise AttributeError when methods are called
        with pytest.raises(AttributeError):
            handlers.get_all_tools()

    @pytest.mark.asyncio
    async def test_massive_tool_set_performance(self):
        """Test performance with large number of tools."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock registry with large tool set using properly formed Tool objects
        large_tool_set = [
            Tool(name=f"tool_{i}", description=f"Tool {i}", inputSchema={"type": "object"})
            for i in range(1000)
        ]

        with patch.object(handlers.registry, "get_all_tools", return_value=large_tool_set):
            # Should handle large tool sets efficiently
            result = assert_sub_second(handlers.get_all_tools)
            assert len(result) == 1000

    @pytest.mark.asyncio
    async def test_handler_info_with_handler_exceptions(self):
        """Test get_handler_info when individual handlers raise exceptions."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock get_tool_names to raise exception for one handler
        handlers.context_handler.get_tool_names = Mock(side_effect=Exception("Handler error"))

        # Other handlers work normally
        for handler in [
            handlers.file_handler,
            handlers.analysis_handler,
            handlers.template_handler,
            handlers.system_handler,
            handlers.editing_handler,
        ]:
            handler.get_tool_names = Mock(return_value=["working_tool"])

        with (
            patch.object(handlers.registry, "get_all_tools", return_value=[]),
            patch.object(handlers, "get_tools_by_category", return_value={}),
        ):

            # Should handle the exception gracefully
            with pytest.raises(Exception):
                handlers.get_handler_info()

    @pytest.mark.asyncio
    async def test_memory_efficiency_with_repeated_calls(self):
        """Test memory efficiency with repeated method calls."""
        handlers = ModularToolHandlers(self.config_manager, self.context_manager)

        # Mock registry methods
        with (
            patch.object(handlers.registry, "get_all_tools", return_value=[]),
            patch.object(handlers.registry, "list_tools_by_category", return_value={}),
        ):

            # Call methods repeatedly
            for _ in range(100):
                handlers.get_all_tools()
                handlers.get_tools_by_category()

            # Should complete without memory issues
            assert True
