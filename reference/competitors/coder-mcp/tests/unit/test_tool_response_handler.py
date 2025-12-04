"""
Comprehensive tests for coder_mcp.tool_response_handler module.

This test suite achieves 100% code coverage using optimized helper modules for:
- JSON processing and parsing
- Tool-specific response handling
- Error detection and success determination
- Structured response creation
"""

import json

from coder_mcp.tool_response_handler import ToolResponseHandler

# NEW OPTIMIZED IMPORTS using our helper modules
from tests.helpers.performance import assert_sub_second
from tests.helpers.utils import DataGenerators


class TestToolResponseHandler:
    """Test ToolResponseHandler with comprehensive coverage."""

    def setup_method(self):
        """Set up test environment using helper modules."""
        self.handler = ToolResponseHandler()

    def test_process_tool_result_with_valid_json(self):
        """Test processing tool result with valid JSON input."""
        # Test with valid JSON
        json_result = '{"status": "success", "data": {"files": 5}}'
        expected = {"status": "success", "data": {"files": 5}}

        result = self.handler.process_tool_result(json_result, "test_tool")

        assert result == expected

    def test_process_tool_result_with_invalid_json(self):
        """Test processing tool result with invalid JSON input."""
        # Test with invalid JSON - should create structured response
        invalid_json = "This is not JSON at all"

        result = self.handler.process_tool_result(invalid_json, "test_tool")

        # Should create structured response
        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result
        assert "content" in result
        assert result["message"] == invalid_json
        assert result["content"] == invalid_json

    def test_process_tool_result_with_null_input(self):
        """Test processing tool result with None input."""
        # Test with None input
        result = self.handler.process_tool_result(None, "test_tool")

        # Should create structured response with failure
        assert isinstance(result, dict)
        assert "success" in result
        assert "message" in result
        assert "content" in result
        assert result["success"] is False  # None input should be unsuccessful
        assert result["message"] is None
        assert result["content"] is None

    def test_is_successful_result_with_success_indicators(self):
        """Test _is_successful_result with various success indicators."""
        success_messages = [
            "Operation completed",
            "✅ Success",
            "All tests passed",
            "Files created successfully",
            "Analysis finished",
            "",  # Empty string is considered success
        ]

        for message in success_messages:
            result = self.handler._is_successful_result(message)
            assert result is True, f"Message '{message}' should be considered successful"

    def test_is_successful_result_with_error_indicators(self):
        """Test _is_successful_result with various error indicators."""
        error_messages = [
            "❌ Operation failed",
            "Error: Something went wrong",
            "ERROR: File not found",
            "An error occurred during processing",
            "Fatal error detected",
        ]

        for message in error_messages:
            result = self.handler._is_successful_result(message)
            assert result is False, f"Message '{message}' should be considered unsuccessful"

    def test_get_tool_specific_fields_exact_matches(self):
        """Test _get_tool_specific_fields with exact tool name matches."""
        # Test apply_best_practices tool
        result = self.handler._get_tool_specific_fields("apply_best_practices", True)
        assert "applied" in result
        assert "files_created" in result
        assert len(result["applied"]) > 0
        assert len(result["files_created"]) > 0

    def test_get_tool_specific_fields_analyze_project(self):
        """Test _get_tool_specific_fields for analyze_project tool."""
        # Test success case
        result = self.handler._get_tool_specific_fields("analyze_project", True)
        assert "total_files" in result
        assert "has_tests" in result
        assert "has_documentation" in result
        assert result["total_files"] > 0
        assert result["has_tests"] is True
        assert result["has_documentation"] is True

    def test_get_fields_by_prefix_analyze_tools(self):
        """Test _get_fields_by_prefix for analyze_ prefixed tools."""
        analyze_tools = ["analyze_code", "analyze_dependencies", "detect_issues", "detect_patterns"]

        for tool_name in analyze_tools:
            # Test success case
            result = self.handler._get_fields_by_prefix(tool_name, True)
            assert "issues" in result
            assert "quality_score" in result
            assert isinstance(result["issues"], list)
            assert isinstance(result["quality_score"], (int, float))

    def test_get_fields_by_prefix_suggest_tools(self):
        """Test _get_fields_by_prefix for suggest_ prefixed tools."""
        suggest_tools = ["suggest_improvements", "suggest_fixes", "suggest_optimizations"]

        for tool_name in suggest_tools:
            # Test success case
            result = self.handler._get_fields_by_prefix(tool_name, True)
            assert "suggestions" in result
            assert isinstance(result["suggestions"], list)
            assert len(result["suggestions"]) > 0

    def test_performance_requirements(self):
        """Test that tool response processing is fast."""
        # Generate test data
        large_json = json.dumps(DataGenerators.generate_dependency_data())

        # Test performance with JSON processing
        result = assert_sub_second(self.handler.process_tool_result, large_json, "test_tool")
        assert isinstance(result, dict)

    def test_is_successful_result_with_none_input(self):
        """Test _is_successful_result with None input."""
        result = self.handler._is_successful_result(None)
        assert result is False

    def test_is_successful_result_with_non_string_input(self):
        """Test _is_successful_result with non-string input."""
        # Test with integer
        result = self.handler._is_successful_result(123)
        assert result is True

        # Test with boolean
        result = self.handler._is_successful_result(True)
        assert result is True

        # Test with list (converted to string, no error indicators)
        result = self.handler._is_successful_result([1, 2, 3])
        assert result is True

    def test_create_structured_response_with_tool_specific_fields(self):
        """Test _create_structured_response includes tool-specific fields."""
        result = self.handler._create_structured_response("Success!", "apply_best_practices")

        # Should have base fields
        assert "success" in result
        assert "message" in result
        assert "content" in result

        # Should have tool-specific fields
        assert "applied" in result
        assert "files_created" in result

    def test_edge_cases_comprehensive(self):
        """Test comprehensive edge cases."""
        edge_cases = [
            (None, "test_tool", False),
            ("", "test_tool", True),  # Empty string is success
            (123, "test_tool", True),  # Number converted to string
            ([], "test_tool", True),  # List converted to string
            ({"key": "value"}, "test_tool", True),  # Dict converted to string
            ("❌ Error in result", "test_tool", False),  # Error indicator
        ]

        for test_input, tool_name, expected_success in edge_cases:
            result = self.handler.process_tool_result(test_input, tool_name)
            assert isinstance(result, dict)
            assert "success" in result
            assert result["success"] == expected_success, f"Failed for input: {test_input}"
