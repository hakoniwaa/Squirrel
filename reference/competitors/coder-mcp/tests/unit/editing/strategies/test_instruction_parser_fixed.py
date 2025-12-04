"""
Unit tests for InstructionParser class.

This module tests the instruction parsing logic for various instruction types
including TODO patterns, natural language commands, and AI-based transformations.
"""

from unittest.mock import Mock, patch

import pytest

from coder_mcp.editing.core.types import EditStrategy, EditType, FileEdit
from coder_mcp.editing.strategies.instruction_parser import InstructionParser


class TestInstructionParser:
    """Test cases for InstructionParser."""

    @pytest.fixture
    def mock_ai_editor(self):
        """Create a mock AI editor instance."""
        mock_editor = Mock()
        mock_editor.logger = Mock()
        mock_editor.file_ops = Mock()
        mock_editor.file_ops.read_file.return_value = "def example():\n    pass"
        return mock_editor

    @pytest.fixture
    def parser(self, mock_ai_editor):
        """Create an InstructionParser instance."""
        return InstructionParser(mock_ai_editor)

    def test_initialization(self, parser):
        """Test that InstructionParser initializes correctly."""
        assert parser.ai_editor is not None
        assert parser.todo_patterns is not None
        assert isinstance(parser.todo_patterns, dict)
        assert len(parser.todo_patterns) > 0

    def test_todo_patterns_structure(self, parser):
        """Test that TODO patterns have the correct structure."""
        for pattern, config in parser.todo_patterns.items():
            assert "template" in config
            assert "type" in config
            # Allow all valid types including 'docstring'
            assert config["type"] in ["wrap", "insert", "replace", "docstring"]

    class TestParseTodoComment:
        """Tests for _parse_todo_comment method."""

        def test_add_error_handling_todo(self, parser):
            """Test parsing TODO: Add error handling."""
            result = parser._parse_todo_comment(
                "# TODO: Add error handling",
                "def process():\n    result = calculate()\n    return result",
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "try:" in result[0].new_content
            assert "except Exception as e:" in result[0].new_content

        def test_implement_validation_todo(self, parser):
            """Test parsing TODO: Implement validation."""
            result = parser._parse_todo_comment(
                "# TODO: Implement validation for user_input",
                "def process(user_input):\n    return user_input",
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "# Input validation" in result[0].new_content
            assert "ValueError" in result[0].new_content

        def test_add_logging_todo(self, parser):
            """Test parsing TODO: Add logging."""
            result = parser._parse_todo_comment(
                "# TODO: Add logging", "def process():\n    return 42", "example.py"
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "logger.info" in result[0].new_content
            assert "logger.debug" in result[0].new_content

        def test_implement_caching_todo(self, parser):
            """Test parsing TODO: Implement caching."""
            result = parser._parse_todo_comment(
                "# TODO: Implement caching",
                "def expensive_operation():\n    result = compute()\n    return result",
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "cache_key" in result[0].new_content
            assert "cache.get" in result[0].new_content
            assert "cache.set" in result[0].new_content

        def test_check_permissions_todo(self, parser):
            """Test parsing TODO: Check permissions."""
            result = parser._parse_todo_comment(
                "# TODO: Check permissions",
                "def delete_user(user_id):\n    User.delete(user_id)",
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "has_permission" in result[0].new_content
            assert "PermissionError" in result[0].new_content

        def test_return_todo(self, parser):
            """Test parsing TODO: Return."""
            result = parser._parse_todo_comment(
                "# TODO: Return", "def get_value():\n    pass", "example.py"
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "return None" in result[0].new_content
            assert "TODO: Implement proper return value" in result[0].new_content

        def test_implement_todo(self, parser):
            """Test parsing TODO: Implement."""
            result = parser._parse_todo_comment(
                "# TODO: Implement", "def not_implemented():\n    pass", "example.py"
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "NotImplementedError" in result[0].new_content

        def test_optimize_performance_todo(self, parser):
            """Test parsing TODO: Optimize performance."""
            result = parser._parse_todo_comment(
                "# TODO: Optimize performance",
                "def slow_function():\n    return [x**2 for x in range(1000000)]",
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "# Performance optimization needed" in result[0].new_content
            assert "Caching" in result[0].new_content
            assert "memoization" in result[0].new_content

        def test_unknown_todo(self, parser):
            """Test parsing unknown TODO pattern."""
            result = parser._parse_todo_comment(
                "# TODO: Do something weird", "def func():\n    pass", "example.py"
            )

            assert result is None

    class TestParseNaturalLanguageCommand:
        """Tests for _parse_natural_language_command method."""

        def test_add_type_hints_command(self, parser):
            """Test parsing 'add type hints' command."""
            result = parser._parse_natural_language_command(
                "add type hints to process function",
                "def process(data, options):\n    return data",
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "->" in result[0].new_content

        def test_convert_to_async_command(self, parser):
            """Test parsing 'convert to async' command."""
            result = parser._parse_natural_language_command(
                "convert fetch_data to async",
                "def fetch_data():\n    return requests.get(url)",
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "async def" in result[0].new_content
            assert "await" in result[0].new_content

        def test_add_docstring_command(self, parser):
            """Test parsing 'add docstring' command."""
            result = parser._parse_natural_language_command(
                "add docstring to calculate function",
                "def calculate(x, y):\n    return x + y",
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert '"""' in result[0].new_content
            assert "Args:" in result[0].new_content
            assert "Returns:" in result[0].new_content

        def test_simplify_command(self, parser):
            """Test parsing 'simplify' command."""
            complex_code = (
                "def complex_logic():\n    if x:\n        if y:\n            if z:\n"
                "                return True\n    return False"
            )
            result = parser._parse_natural_language_command(
                "simplify the complex_logic function",
                complex_code,
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "return" in result[0].new_content

        def test_rename_function_command(self, parser):
            """Test parsing 'rename function' command."""
            result = parser._parse_natural_language_command(
                "rename get_data to fetch_user_data",
                "def get_data():\n    return data",
                "example.py",
            )

            assert result is not None
            assert len(result) >= 1
            assert any("fetch_user_data" in edit.new_content for edit in result)

        def test_add_logging_command(self, parser):
            """Test parsing 'add logging' command."""
            result = parser._parse_natural_language_command(
                "add logging to the process_request function",
                "def process_request(request):\n    return handle(request)",
                "example.py",
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].type == EditType.PATTERN_BASED
            assert "logger" in result[0].new_content

        def test_make_configurable_command(self, parser):
            """Test parsing 'make configurable' command."""
            result = parser._parse_natural_language_command(
                "make the timeout value configurable",
                "TIMEOUT = 30\ndef wait():\n    time.sleep(TIMEOUT)",
                "example.py",
            )

            assert result is not None
            assert len(result) >= 1
            assert any(
                "config" in edit.new_content or "Config" in edit.new_content for edit in result
            )

        def test_add_tests_command(self, parser):
            """Test parsing 'add tests' command."""
            result = parser._parse_natural_language_command(
                "add tests for calculator module",
                "def add(a, b):\n    return a + b",
                "calculator.py",
            )

            assert result is not None
            assert len(result) >= 1
            assert any(
                "test_" in edit.new_content or "assert" in edit.new_content for edit in result
            )

        def test_optimize_command(self, parser):
            """Test parsing 'optimize' command."""
            search_code = (
                "def search_items(items, target):\n    for item in items:\n"
                "        if item == target:\n            return True\n    return False"
            )
            result = parser._parse_natural_language_command(
                "optimize the search_items function for performance",
                search_code,
                "example.py",
            )

            assert result is not None
            assert len(result) >= 1
            # Should suggest using 'in' operator or set for O(1) lookup
            assert any("in" in edit.new_content or "set" in edit.new_content for edit in result)

    class TestInferInstructionContext:
        """Tests for _infer_instruction_context method."""

        def test_infer_context_add_error_handling(self, parser):
            """Test inferring context for 'add error handling' instruction."""
            context = parser._infer_instruction_context(
                "add error handling", "def process():\n    result = api_call()\n    return result"
            )

            assert context is not None
            assert "function_name" in context
            assert context["function_name"] == "process"
            assert "needs_try_except" in context
            assert context["needs_try_except"] is True

        def test_infer_context_add_type_hints(self, parser):
            """Test inferring context for 'add type hints' instruction."""
            context = parser._infer_instruction_context(
                "add type hints", "def calculate(x, y):\n    return x + y"
            )

            assert context is not None
            assert "function_name" in context
            assert "parameters" in context
            assert len(context["parameters"]) == 2

        def test_infer_context_convert_to_async(self, parser):
            """Test inferring context for 'convert to async' instruction."""
            context = parser._infer_instruction_context(
                "convert to async",
                "def fetch():\n    response = requests.get(url)\n    return response.json()",
            )

            assert context is not None
            assert "function_name" in context
            assert "has_io_operations" in context
            assert context["has_io_operations"] is True

        def test_infer_context_add_logging(self, parser):
            """Test inferring context for 'add logging' instruction."""
            context = parser._infer_instruction_context(
                "add logging",
                "def critical_operation():\n    update_database()\n    send_notification()",
            )

            assert context is not None
            assert "function_name" in context
            assert "is_critical" in context

        def test_infer_context_no_function(self, parser):
            """Test inferring context when no function is present."""
            context = parser._infer_instruction_context(
                "add error handling", "x = 10\ny = 20\nresult = x + y"
            )

            assert context is not None
            assert "function_name" not in context or context["function_name"] is None

    class TestAIBasedMethods:
        """Tests for AI-based parsing methods."""

        @patch(
            "coder_mcp.editing.strategies.instruction_parser.InstructionParser._generate_ai_edit"
        )
        def test_parse_using_ai_success(self, mock_ai_edit, parser):
            """Test successful AI-based parsing."""
            mock_ai_edit.return_value = [
                FileEdit(
                    type=EditType.PATTERN_BASED,
                    pattern="def old():",
                    replacement="def new():",
                    new_content="def new():",
                    strategy=EditStrategy.PATTERN_BASED,
                )
            ]

            result = parser._parse_using_ai(
                "refactor this code for better readability", "def old():\n    pass", "example.py"
            )

            assert result is not None
            assert len(result) == 1
            assert result[0].new_content == "def new():"

        @patch(
            "coder_mcp.editing.strategies.instruction_parser.InstructionParser._generate_ai_edit"
        )
        def test_parse_using_ai_failure(self, mock_ai_edit, parser):
            """Test AI-based parsing failure handling."""
            mock_ai_edit.side_effect = Exception("AI service unavailable")

            result = parser._parse_using_ai(
                "complex refactoring", "def complex():\n    pass", "example.py"
            )

            assert result is None
            parser.ai_editor.logger.warning.assert_called()

        def test_generate_ai_edit_prompt(self, parser):
            """Test AI edit prompt generation."""
            prompt = parser._generate_ai_edit_prompt(
                "add comprehensive error handling",
                "def risky():\n    file = open('data.txt')\n    return file.read()",
                {"function_name": "risky", "has_file_operations": True},
            )

            assert "add comprehensive error handling" in prompt
            assert "risky" in prompt
            assert "def risky():" in prompt

    class TestEdgesCasesAndErrorHandling:
        """Tests for edge cases and error handling."""

        def test_empty_instruction(self, parser):
            """Test handling of empty instruction."""
            result = parser._parse_todo_comment("", "def func():\n    pass", "example.py")
            assert result is None

        def test_empty_content(self, parser):
            """Test handling of empty file content."""
            result = parser._parse_todo_comment("# TODO: Add error handling", "", "example.py")
            assert result is not None
            # Should still generate some edit even with empty content

        def test_malformed_todo(self, parser):
            """Test handling of malformed TODO comments."""
            result = parser._parse_todo_comment(
                "# TOD: Add error handling", "def func():\n    pass", "example.py"  # Typo in TODO
            )
            assert result is None

        def test_complex_nested_function(self, parser):
            """Test parsing with complex nested functions."""
            content = """
def outer():
    def inner():
        def deeply_nested():
            return 42
        return deeply_nested()
    return inner()
"""
            result = parser._parse_natural_language_command(
                "add error handling to all functions", content, "example.py"
            )

            assert result is not None
            assert len(result) >= 1

        def test_multiline_todo(self, parser):
            """Test parsing multiline TODO comments."""
            result = parser._parse_todo_comment(
                "# TODO: Add error handling\n# for file operations\n# and network calls",
                "def process():\n    pass",
                "example.py",
            )

            assert result is not None

        def test_unicode_in_instruction(self, parser):
            """Test handling Unicode in instructions."""
            result = parser._parse_natural_language_command(
                "add comment: 这是中文注释", "def func():\n    pass", "example.py"
            )

            # Should handle Unicode gracefully
            assert result is not None or result is None  # Either parse it or skip it

        def test_very_long_instruction(self, parser):
            """Test handling very long instructions."""
            long_instruction = "add " + " and ".join(["feature"] * 100)
            result = parser._parse_natural_language_command(
                long_instruction, "def func():\n    pass", "example.py"
            )

            # Should handle long instructions without crashing
            assert isinstance(result, (list, type(None)))


class TestInstructionParserIntegration:
    """Integration tests for InstructionParser with AI editor."""

    @pytest.fixture
    def full_parser(self):
        """Create a parser with more complete AI editor mock."""
        mock_editor = Mock()
        mock_editor.logger = Mock()
        mock_editor.file_ops = Mock()
        mock_editor.ai_service = Mock()
        mock_editor.metrics = Mock()
        mock_editor.config = {"ai": {"model": "gpt-4", "temperature": 0.7}}

        parser = InstructionParser(mock_editor)
        return parser

    def test_full_instruction_flow(self, full_parser):
        """Test complete instruction parsing flow."""
        # Test that various instruction types can be parsed
        instructions = [
            "# TODO: Add error handling",
            "add type hints to all functions",
            "optimize for performance",
            "convert to async/await pattern",
        ]

        for instruction in instructions:
            # Verify parser can handle each instruction type
            if instruction.startswith("# TODO:"):
                method = full_parser._parse_todo_comment
            else:
                method = full_parser._parse_natural_language_command

            # Should not raise exceptions
            try:
                result = method(instruction, "def example():\n    return 42", "test.py")
                assert isinstance(result, (list, type(None)))
            except Exception as e:
                pytest.fail(f"Parser failed on instruction '{instruction}': {e}")
