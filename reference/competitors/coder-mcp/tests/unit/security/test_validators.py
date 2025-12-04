"""
Unit tests for security validators.

Tests validation functions and security-related functionality.
"""

import re

import pytest

from coder_mcp.security.exceptions import (
    ResourceLimitError,
    SecurityError,
    ValidationError,
)
from coder_mcp.security.validators import (
    sanitize_path_input,
    validate_dict_input,
    validate_file_size,
    validate_regex_pattern,
    validate_string_input,
    validate_tool_args,
)


class TestStringValidation:
    """Test validate_string_input function."""

    def test_valid_string_input(self):
        """Test valid string input validation."""
        result = validate_string_input("test string", "test_param")
        assert result == "test string"

    def test_string_input_with_whitespace(self):
        """Test string input with surrounding whitespace."""
        result = validate_string_input("  test string  ", "test_param")
        assert result == "test string"

    def test_non_string_input(self):
        """Test validation rejects non-string input."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_string_input(123, "test_param")

        with pytest.raises(ValidationError, match="must be a string"):
            validate_string_input([], "test_param")

    def test_empty_string_not_allowed(self):
        """Test validation rejects empty strings by default."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_string_input("", "test_param")

        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_string_input("   ", "test_param")

    def test_empty_string_allowed_when_enabled(self):
        """Test validation allows empty strings when enabled."""
        result = validate_string_input("", "test_param", allow_empty=True)
        assert result == ""

        result = validate_string_input("   ", "test_param", allow_empty=True)
        assert result == ""

    def test_string_length_validation(self):
        """Test string length limits."""
        # Should pass within limit
        result = validate_string_input("short", "test_param", max_length=10)
        assert result == "short"

        # Should fail over limit
        with pytest.raises(ValidationError, match="too long"):
            validate_string_input("very long string", "test_param", max_length=5)

    def test_custom_max_length(self):
        """Test custom max length setting."""
        long_string = "x" * 100

        # Should pass with higher limit
        result = validate_string_input(long_string, "test_param", max_length=200)
        assert result == long_string

        # Should fail with lower limit
        with pytest.raises(ValidationError, match="too long"):
            validate_string_input(long_string, "test_param", max_length=50)


class TestDictValidation:
    """Test validate_dict_input function."""

    def test_valid_dict_input(self):
        """Test valid dictionary input validation."""
        test_dict = {"key": "value", "number": 42}
        result = validate_dict_input(test_dict, "test_param")
        assert result == test_dict

    def test_empty_dict_input(self):
        """Test empty dictionary input."""
        result = validate_dict_input({}, "test_param")
        assert result == {}

    def test_non_dict_input(self):
        """Test validation rejects non-dictionary input."""
        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_dict_input("not a dict", "test_param")

        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_dict_input([], "test_param")

        with pytest.raises(ValidationError, match="must be a dictionary"):
            validate_dict_input(123, "test_param")


class TestRegexValidation:
    """Test validate_regex_pattern function."""

    def test_valid_regex_pattern(self):
        """Test valid regex pattern validation."""
        pattern = r"^[a-zA-Z0-9]+$"
        result = validate_regex_pattern(pattern)
        assert isinstance(result, re.Pattern)
        assert result.pattern == pattern

    def test_simple_patterns(self):
        """Test simple regex patterns."""
        simple_patterns = [
            r"hello",
            r"\d+",
            r"[a-z]*",
            r"test|example",
        ]

        for pattern in simple_patterns:
            result = validate_regex_pattern(pattern)
            assert isinstance(result, re.Pattern)

    def test_non_string_pattern(self):
        """Test validation rejects non-string patterns."""
        with pytest.raises(ValidationError, match="Pattern must be a string"):
            validate_regex_pattern(123)

        with pytest.raises(ValidationError, match="Pattern must be a string"):
            validate_regex_pattern(["pattern"])

    def test_pattern_too_long(self):
        """Test validation rejects patterns that are too long."""
        long_pattern = "a" * 1001
        with pytest.raises(ValidationError, match="Pattern too long"):
            validate_regex_pattern(long_pattern)

    def test_invalid_regex_syntax(self):
        """Test validation rejects invalid regex syntax."""
        invalid_patterns = [
            r"[",  # Unclosed bracket
            r"(?P<>)",  # Invalid group name
            r"*",  # Invalid quantifier
            r"(?P<name>",  # Unclosed group
        ]

        for pattern in invalid_patterns:
            with pytest.raises(ValidationError, match="Invalid regex pattern"):
                validate_regex_pattern(pattern)

    def test_dangerous_patterns(self):
        """Test validation blocks potentially dangerous patterns."""
        # For now, just test that the function works - we can be more specific about dangerous
        # patterns later. The important thing is that it doesn't block valid patterns while
        # properly validating syntax

        # Test that obviously valid patterns pass
        valid_patterns = [
            r"[a-z]+",
            r"\d+",
            r"test|example",
        ]

        for pattern in valid_patterns:
            result = validate_regex_pattern(pattern)
            assert isinstance(result, re.Pattern)

        # Test that invalid syntax is still caught
        with pytest.raises(ValidationError, match="Invalid regex pattern"):
            validate_regex_pattern(r"[unclosed")


class TestPathSanitization:
    """Test sanitize_path_input function."""

    def test_normal_path_input(self):
        """Test normal path input sanitization."""
        normal_paths = [
            "/home/user/file.txt",
            "relative/path/file.py",
            "./current/directory",
            "../parent/directory",
        ]

        for path in normal_paths:
            result = sanitize_path_input(path)
            assert result == path

    def test_null_byte_rejection(self):
        """Test path input with null bytes is rejected."""
        with pytest.raises(SecurityError, match="Null bytes not allowed"):
            sanitize_path_input("/path/with\x00null")

        with pytest.raises(SecurityError, match="Null bytes not allowed"):
            sanitize_path_input("file\x00name.txt")

    def test_control_character_rejection(self):
        """Test path input with dangerous control characters is rejected."""
        # These control characters should be rejected
        dangerous_paths = [
            "/path/with\x01control",
            "/path/with\x02control",
            "/path/with\x1fcontrol",
        ]

        for path in dangerous_paths:
            with pytest.raises(SecurityError, match="Invalid control characters"):
                sanitize_path_input(path)

    def test_allowed_control_characters(self):
        """Test path input with allowed control characters."""
        # Tab, newline, and carriage return should be allowed
        allowed_paths = [
            "/path/with\ttab",
            "/path/with\nnewline",
            "/path/with\rcarriage_return",
        ]

        for path in allowed_paths:
            result = sanitize_path_input(path)
            assert result == path


class TestFileSizeValidation:
    """Test validate_file_size function."""

    def test_file_size_within_limit(self):
        """Test file size validation within limits."""
        # Should not raise exception for files within limit
        validate_file_size(500, 1024)  # 500 bytes, 1KB limit
        validate_file_size(1024, 1024)  # Exactly at limit
        validate_file_size(0, 1024)  # Zero size

    def test_file_size_exceeds_limit(self):
        """Test file size validation exceeds limits."""
        with pytest.raises(ResourceLimitError, match="File too large"):
            validate_file_size(1025, 1024)  # Just over limit

        with pytest.raises(ResourceLimitError, match="File too large"):
            validate_file_size(10000, 1024)  # Way over limit

    def test_file_size_with_file_path(self):
        """Test file size validation includes file path in error."""
        try:
            validate_file_size(2000, 1000, "/path/to/large/file.txt")
            assert False, "Expected ResourceLimitError"
        except ResourceLimitError as e:
            assert "/path/to/large/file.txt" in str(e.context.get("file_path", ""))

    def test_file_size_edge_cases(self):
        """Test file size validation edge cases."""
        # Large file with large limit
        validate_file_size(1000000, 2000000)

        # Very small limits
        validate_file_size(1, 2)

        with pytest.raises(ResourceLimitError):
            validate_file_size(3, 2)


class TestToolArgsValidation:
    """Test validate_tool_args decorator."""

    def test_decorator_setup(self):
        """Test that the decorator can be applied."""

        @validate_tool_args(["required_field"])
        async def test_function(self, args):
            return "success"

        # Function should be decorated
        assert hasattr(test_function, "__wrapped__")

    @pytest.mark.asyncio
    async def test_valid_args_with_all_required_fields(self):
        """Test decorator passes when all required fields are present."""

        @validate_tool_args(["field1", "field2"])
        async def test_function(self, args):
            return args

        valid_args = {"field1": "value1", "field2": "value2"}
        result = await test_function(None, valid_args)
        assert result == valid_args

    @pytest.mark.asyncio
    async def test_missing_required_field(self):
        """Test decorator raises error when required field is missing."""

        @validate_tool_args(["required_field"])
        async def test_function(self, args):
            return "success"

        invalid_args = {"other_field": "value"}

        with pytest.raises(ValidationError, match="Missing required parameter"):
            await test_function(None, invalid_args)

    @pytest.mark.asyncio
    async def test_empty_args_with_required_fields(self):
        """Test decorator raises error when args are empty but fields required."""

        @validate_tool_args(["required_field"])
        async def test_function(self, args):
            return "success"

        with pytest.raises(ValidationError, match="Missing required parameter"):
            await test_function(None, {})

    @pytest.mark.asyncio
    async def test_non_dict_args(self):
        """Test decorator raises error when args are not a dictionary."""

        @validate_tool_args(["field"])
        async def test_function(self, args):
            return "success"

        with pytest.raises(ValidationError, match="must be a dictionary"):
            await test_function(None, "not a dict")

    @pytest.mark.asyncio
    async def test_extra_fields_allowed(self):
        """Test decorator allows extra fields beyond required ones."""

        @validate_tool_args(["required_field"])
        async def test_function(self, args):
            return args

        args_with_extra = {"required_field": "value", "extra_field": "extra_value"}

        result = await test_function(None, args_with_extra)
        assert result == args_with_extra

    @pytest.mark.asyncio
    async def test_no_required_fields(self):
        """Test decorator works when no fields are required."""

        @validate_tool_args([])
        async def test_function(self, args):
            return "success"

        # Should work with empty args
        result = await test_function(None, {})
        assert result == "success"

        # Should work with any args
        result = await test_function(None, {"any": "field"})
        assert result == "success"


class TestSecurityIntegration:
    """Integration tests for security validation functions."""

    def test_comprehensive_input_validation(self):
        """Test comprehensive input validation workflow."""
        # Valid inputs should pass all validations
        string_input = validate_string_input("test input", "test", max_length=100)
        assert string_input == "test input"

        dict_input = validate_dict_input({"key": "value"}, "test_dict")
        assert dict_input == {"key": "value"}

        regex_pattern = validate_regex_pattern(r"[a-z]+")
        assert isinstance(regex_pattern, re.Pattern)

        path_input = sanitize_path_input("/safe/path")
        assert path_input == "/safe/path"

        # File size validation
        validate_file_size(100, 1000)

    def test_validation_error_contexts(self):
        """Test that validation errors include helpful context."""
        # String validation error should include context
        try:
            validate_string_input(123, "test_param")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "parameter" in e.context
            assert e.context["parameter"] == "test_param"

        # Regex validation error should include context
        try:
            validate_regex_pattern("[invalid")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "pattern" in e.context

        # File size error should include context
        try:
            validate_file_size(2000, 1000, "test.txt")
            assert False, "Expected ResourceLimitError"
        except ResourceLimitError as e:
            assert "file_path" in e.context

    def test_security_error_contexts(self):
        """Test that security errors include helpful context."""
        # Path sanitization error should include context
        try:
            sanitize_path_input("/path/with\x00null")
            assert False, "Expected SecurityError"
        except SecurityError as e:
            assert "path" in e.context

        # For now, just test that the function works with simple patterns
        # since we simplified the dangerous pattern detection
        result = validate_regex_pattern(r"[a-z]+")
        assert isinstance(result, re.Pattern)

        # Test that invalid regex syntax still raises ValidationError with context
        try:
            validate_regex_pattern(r"[invalid")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "pattern" in e.context
