"""
Unit tests for coder_mcp.editing.core.errors module.
Tests all custom exception classes and their behavior.
"""

import pytest

from coder_mcp.editing.core.errors import (
    BackupError,
    ConcurrentEditError,
    EditError,
    EditValidationError,
    FileNotFoundError,
    FilePermissionError,
    FileSizeError,
    PatternNotFoundError,
    SyntaxValidationError,
)


class TestEditError:
    """Test the base EditError class."""

    def test_basic_initialization(self):
        """Test basic error initialization with message only."""
        error = EditError("Test error message")
        assert str(error) == "Test error message"
        assert error.details == {}
        assert error.error_type == "EditError"

    def test_initialization_with_details(self):
        """Test error initialization with details."""
        details = {"key": "value", "code": 123}
        error = EditError("Test error", details)
        assert str(error) == "Test error"
        assert error.details == details
        assert error.error_type == "EditError"

    def test_inheritance(self):
        """Test that EditError inherits from Exception."""
        error = EditError("Test")
        assert isinstance(error, Exception)


class TestFileNotFoundError:
    """Test FileNotFoundError class."""

    def test_initialization(self):
        """Test FileNotFoundError initialization."""
        file_path = "/path/to/missing/file.py"
        error = FileNotFoundError(file_path)

        assert str(error) == f"File not found: {file_path}"
        assert error.details["file_path"] == file_path
        assert error.error_type == "FileNotFoundError"

    def test_inheritance(self):
        """Test inheritance chain."""
        error = FileNotFoundError("test.py")
        assert isinstance(error, EditError)
        assert isinstance(error, Exception)


class TestFilePermissionError:
    """Test FilePermissionError class."""

    @pytest.mark.parametrize("operation", ["read", "write", "delete", "execute"])
    def test_initialization_with_operations(self, operation):
        """Test FilePermissionError with different operations."""
        file_path = "/protected/file.py"
        error = FilePermissionError(file_path, operation)

        expected_msg = f"Permission denied for {operation} on: {file_path}"
        assert str(error) == expected_msg
        assert error.details["file_path"] == file_path
        assert error.details["operation"] == operation
        assert error.error_type == "FilePermissionError"


class TestSyntaxValidationError:
    """Test SyntaxValidationError class."""

    def test_initialization(self):
        """Test SyntaxValidationError initialization."""
        file_path = "test.py"
        line = 42
        column = 15
        error_msg = "unexpected indent"

        error = SyntaxValidationError(file_path, line, column, error_msg)

        expected = f"Syntax error in {file_path} at line {line}, column {column}: {error_msg}"
        assert str(error) == expected
        assert error.details["file_path"] == file_path
        assert error.details["line"] == line
        assert error.details["column"] == column
        assert error.details["syntax_error"] == error_msg

    @pytest.mark.parametrize("line,column", [(0, 0), (1, 1), (999, 999)])
    def test_different_positions(self, line, column):
        """Test with different line and column positions."""
        error = SyntaxValidationError("file.py", line, column, "error")
        assert error.details["line"] == line
        assert error.details["column"] == column


class TestEditValidationError:
    """Test EditValidationError class."""

    def test_basic_initialization(self):
        """Test basic EditValidationError."""
        edit_type = "pattern_based"
        reason = "Pattern not unique"

        error = EditValidationError(edit_type, reason)

        expected = f"Invalid {edit_type} edit: {reason}"
        assert str(error) == expected
        assert error.details["edit_type"] == edit_type
        assert error.details["reason"] == reason

    def test_with_extra_kwargs(self):
        """Test EditValidationError with additional keyword arguments."""
        error = EditValidationError(
            "line_based", "Line out of range", line_number=1000, max_lines=500
        )

        assert error.details["line_number"] == 1000
        assert error.details["max_lines"] == 500
        assert error.details["edit_type"] == "line_based"
        assert error.details["reason"] == "Line out of range"


class TestConcurrentEditError:
    """Test ConcurrentEditError class."""

    def test_initialization(self):
        """Test ConcurrentEditError initialization."""
        file_path = "shared_file.py"
        conflicts = {
            "conflicting_lines": [10, 11, 12],
            "editors": ["user1", "user2"],
            "timestamps": ["2025-01-01T10:00:00", "2025-01-01T10:00:01"],
        }

        error = ConcurrentEditError(file_path, conflicts)

        expected = f"Concurrent edit conflict in {file_path}"
        assert str(error) == expected
        assert error.details["file_path"] == file_path
        assert error.details["conflicts"] == conflicts


class TestPatternNotFoundError:
    """Test PatternNotFoundError class."""

    def test_initialization(self):
        """Test PatternNotFoundError initialization."""
        pattern = "def old_function():"
        file_path = "module.py"

        error = PatternNotFoundError(pattern, file_path)

        expected = f"Pattern '{pattern}' not found in {file_path}"
        assert str(error) == expected
        assert error.details["pattern"] == pattern
        assert error.details["file_path"] == file_path

    def test_with_regex_pattern(self):
        """Test with regex pattern."""
        pattern = r"\d{3}-\d{3}-\d{4}"  # Phone number pattern
        error = PatternNotFoundError(pattern, "contacts.txt")
        assert error.details["pattern"] == pattern


class TestFileSizeError:
    """Test FileSizeError class."""

    @pytest.mark.parametrize(
        "size_mb,max_size_mb",
        [
            (10.5, 5.0),
            (100.0, 50.0),
            (1024.0, 100.0),
        ],
    )
    def test_initialization(self, size_mb, max_size_mb):
        """Test FileSizeError with different sizes."""
        file_path = "large_file.bin"
        error = FileSizeError(file_path, size_mb, max_size_mb)

        expected = (
            f"File {file_path} is too large ({size_mb:.1f}MB). " f"Maximum size is {max_size_mb}MB"
        )
        assert str(error) == expected
        assert error.details["file_path"] == file_path
        assert error.details["size_mb"] == size_mb
        assert error.details["max_size_mb"] == max_size_mb


class TestBackupError:
    """Test BackupError class."""

    def test_initialization(self):
        """Test BackupError initialization."""
        message = "Cannot create backup directory /tmp/backup: Permission denied"
        error = BackupError(message)

        assert str(error) == message
        assert error.error_type == "BackupError"
        assert isinstance(error.details, dict)

    @pytest.mark.parametrize(
        "message",
        [
            "Cannot create backup directory /tmp/backup: Permission denied",
            "File not found: /path/to/file.py",
            "Failed to create backup: Disk full",
            "Backup file not found: backup_123.py",
            "Backup file checksum mismatch",
            "Failed to restore backup: Permission denied",
        ],
    )
    def test_different_messages(self, message):
        """Test with different backup error messages."""
        error = BackupError(message)
        assert str(error) == message
        assert error.error_type == "BackupError"


class TestErrorHierarchy:
    """Test the overall error hierarchy and relationships."""

    def test_all_errors_inherit_from_edit_error(self):
        """Verify all custom errors inherit from EditError."""
        errors = [
            FileNotFoundError("test.py"),
            FilePermissionError("test.py", "read"),
            SyntaxValidationError("test.py", 1, 1, "error"),
            EditValidationError("type", "reason"),
            ConcurrentEditError("test.py", {}),
            PatternNotFoundError("pattern", "test.py"),
            FileSizeError("test.py", 10.0, 5.0),
            BackupError("Failed to create backup"),
        ]

        for error in errors:
            assert isinstance(error, EditError)
            assert isinstance(error, Exception)
            assert hasattr(error, "details")
            assert hasattr(error, "error_type")

    def test_error_types_are_unique(self):
        """Verify each error has its unique error_type."""
        error_types = {
            FileNotFoundError("test.py").error_type,
            FilePermissionError("test.py", "read").error_type,
            SyntaxValidationError("test.py", 1, 1, "error").error_type,
            EditValidationError("type", "reason").error_type,
            ConcurrentEditError("test.py", {}).error_type,
            PatternNotFoundError("pattern", "test.py").error_type,
            FileSizeError("test.py", 10.0, 5.0).error_type,
            BackupError("Failed to create backup").error_type,
        }

        # All error types should be unique
        assert len(error_types) == 8


class TestErrorUsageScenarios:
    """Test realistic usage scenarios for the errors."""

    def test_file_editing_workflow_errors(self):
        """Test errors that might occur in a file editing workflow."""
        # File not found
        with pytest.raises(FileNotFoundError) as exc_info:
            raise FileNotFoundError("/nonexistent/file.py")
        assert "File not found" in str(exc_info.value)

        # Permission denied
        with pytest.raises(FilePermissionError) as exc_info:
            raise FilePermissionError("/root/protected.py", "write")
        assert "Permission denied" in str(exc_info.value)

        # Pattern not found
        with pytest.raises(PatternNotFoundError) as exc_info:
            raise PatternNotFoundError("oldFunction()", "module.py")
        assert "Pattern 'oldFunction()' not found" in str(exc_info.value)

    def test_validation_workflow_errors(self):
        """Test validation-related errors."""
        # Syntax error
        with pytest.raises(SyntaxValidationError) as exc_info:
            raise SyntaxValidationError("bad.py", 10, 5, "invalid syntax")
        error = exc_info.value
        assert error.details["line"] == 10
        assert error.details["column"] == 5

        # Edit validation
        with pytest.raises(EditValidationError) as exc_info:
            raise EditValidationError(
                "ast_based",
                "Invalid node type",
                node_type="InvalidNode",
                expected_types=["FunctionDef", "ClassDef"],
            )
        error = exc_info.value
        assert error.details["node_type"] == "InvalidNode"

    def test_concurrent_editing_scenario(self):
        """Test concurrent editing error scenario."""
        conflicts = {
            "conflicting_ranges": [(10, 20), (15, 25)],
            "conflict_type": "overlapping_edits",
            "resolution_strategy": "manual",
        }

        with pytest.raises(ConcurrentEditError) as exc_info:
            raise ConcurrentEditError("shared_module.py", conflicts)

        error = exc_info.value
        assert error.details["conflicts"]["conflict_type"] == "overlapping_edits"
