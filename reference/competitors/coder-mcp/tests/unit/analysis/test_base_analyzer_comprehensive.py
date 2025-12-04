"""
Comprehensive tests for BaseAnalyzer module.

This module provides complete test coverage for the BaseAnalyzer abstract class
and AnalysisError exception, including edge cases and error handling.
"""

import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from coder_mcp.analysis.base_analyzer import AnalysisError, BaseAnalyzer


class TestAnalysisError:
    """Test AnalysisError exception class."""

    def test_basic_creation(self):
        """Test basic AnalysisError creation."""
        error = AnalysisError("Test error")
        assert str(error) == "Test error"
        assert error.file_path is None
        assert error.cause is None

    def test_creation_with_file_path(self, tmp_path):
        """Test AnalysisError with file path."""
        test_file = tmp_path / "test.py"
        error = AnalysisError("Test error", file_path=test_file)

        assert str(error) == "Test error"
        assert error.file_path == test_file

    def test_creation_with_cause(self):
        """Test AnalysisError with cause exception."""
        original_error = ValueError("Original error")
        error = AnalysisError("Wrapper error", cause=original_error)

        assert str(error) == "Wrapper error"
        assert error.cause == original_error

    def test_creation_with_all_parameters(self, tmp_path):
        """Test AnalysisError with all parameters."""
        test_file = tmp_path / "test.py"
        original_error = IOError("IO error")
        error = AnalysisError("Analysis failed", file_path=test_file, cause=original_error)

        assert str(error) == "Analysis failed"
        assert error.file_path == test_file
        assert error.cause == original_error


class ConcreteAnalyzer(BaseAnalyzer):
    """Concrete implementation of BaseAnalyzer for testing."""

    def __init__(self, workspace_root):
        super().__init__(workspace_root)
        self.analyze_file_called = False
        self.detect_code_smells_called = False

    async def analyze_file(self, file_path, analysis_type="quick"):
        """Mock implementation of analyze_file."""
        self.analyze_file_called = True
        return {
            "file": str(file_path.relative_to(self.workspace_root)),
            "analysis_type": analysis_type,
            "quality_score": 8.5,
            "issues": [],
            "suggestions": [],
            "metrics": {},
        }

    def get_file_extensions(self):
        """Mock implementation returning test extensions."""
        return [".test", ".mock"]

    def detect_code_smells(self, content, file_path, smell_types):
        """Mock implementation of detect_code_smells."""
        self.detect_code_smells_called = True
        return []


class TestBaseAnalyzer:
    """Test BaseAnalyzer abstract base class."""

    @pytest.fixture
    def analyzer(self, tmp_path):
        """Create ConcreteAnalyzer instance."""
        return ConcreteAnalyzer(tmp_path)

    def test_initialization_valid_workspace(self, tmp_path):
        """Test successful initialization with valid workspace."""
        analyzer = ConcreteAnalyzer(tmp_path)

        assert analyzer.workspace_root == tmp_path.resolve()
        assert hasattr(analyzer, "logger")
        assert analyzer.logger.name.endswith("ConcreteAnalyzer")

    def test_initialization_with_string_path(self, tmp_path):
        """Test initialization with string workspace path."""
        analyzer = ConcreteAnalyzer(str(tmp_path))

        assert analyzer.workspace_root == tmp_path.resolve()

    def test_initialization_nonexistent_workspace(self):
        """Test initialization with non-existent workspace."""
        nonexistent_path = Path("/nonexistent/workspace")

        with pytest.raises(AnalysisError) as exc_info:
            ConcreteAnalyzer(nonexistent_path)

        assert "Workspace root does not exist" in str(exc_info.value)

    def test_initialization_file_instead_of_directory(self, tmp_path):
        """Test initialization with file instead of directory."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with pytest.raises(AnalysisError) as exc_info:
            ConcreteAnalyzer(test_file)

        assert "Workspace root is not a directory" in str(exc_info.value)

    def test_initialization_invalid_path(self):
        """Test initialization with invalid path."""
        with pytest.raises(AnalysisError) as exc_info:
            ConcreteAnalyzer("\x00invalid")

        assert "Invalid workspace root" in str(exc_info.value)

    def test_validate_analysis_type_valid_types(self, analyzer):
        """Test validation of valid analysis types."""
        valid_types = ["quick", "deep", "security", "performance"]

        for analysis_type in valid_types:
            result = analyzer.validate_analysis_type(analysis_type)
            assert result == analysis_type

    def test_validate_analysis_type_case_insensitive(self, analyzer):
        """Test case-insensitive analysis type validation."""
        test_cases = [
            ("QUICK", "quick"),
            ("Deep", "deep"),
            ("SECURITY", "security"),
            ("Performance", "performance"),
            ("  quick  ", "quick"),  # With whitespace
        ]

        for input_type, expected in test_cases:
            result = analyzer.validate_analysis_type(input_type)
            assert result == expected

    def test_validate_analysis_type_invalid_type(self, analyzer):
        """Test validation with invalid analysis type."""
        result = analyzer.validate_analysis_type("invalid_type")
        assert result == "quick"  # Should default to quick

    def test_validate_analysis_type_non_string(self, analyzer):
        """Test validation with non-string input."""
        with pytest.raises(AnalysisError) as exc_info:
            analyzer.validate_analysis_type(123)

        assert "Analysis type must be a string" in str(exc_info.value)

    def test_validate_file_path_valid_file(self, analyzer, tmp_path):
        """Test validation of valid file path."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        result = analyzer.validate_file_path(test_file)
        assert result == test_file.resolve()

    def test_validate_file_path_nonexistent_file(self, analyzer, tmp_path):
        """Test validation of non-existent file."""
        nonexistent_file = tmp_path / "nonexistent.py"

        with pytest.raises(FileNotFoundError) as exc_info:
            analyzer.validate_file_path(nonexistent_file)

        assert "File does not exist" in str(exc_info.value)

    def test_validate_file_path_directory_instead_of_file(self, analyzer, tmp_path):
        """Test validation when directory is passed instead of file."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        with pytest.raises(OSError) as exc_info:
            analyzer.validate_file_path(test_dir)

        assert "Path is not a file" in str(exc_info.value)

    def test_validate_file_path_outside_workspace(self, analyzer, tmp_path):
        """Test validation of file outside workspace."""
        # Create a file outside the workspace
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "outside.py"
        outside_file.write_text("content")

        # Should still validate but log warning
        with patch.object(analyzer.logger, "warning") as mock_warning:
            result = analyzer.validate_file_path(outside_file)

        assert result == outside_file.resolve()
        mock_warning.assert_called_once()
        assert "outside workspace root" in mock_warning.call_args[0][0]

    def test_validate_file_path_invalid_path(self, analyzer):
        """Test validation with invalid file path."""
        with pytest.raises(AnalysisError) as exc_info:
            analyzer.validate_file_path("\x00invalid")

        assert "Invalid file path" in str(exc_info.value)

    def test_create_base_result_inside_workspace(self, analyzer, tmp_path):
        """Test creating base result for file inside workspace."""
        test_file = tmp_path / "subdir" / "test.py"
        test_file.parent.mkdir()
        test_file.write_text("content")

        result = analyzer.create_base_result(test_file, "deep")

        assert result["file"] == "subdir/test.py"
        assert result["analysis_type"] == "deep"
        assert result["quality_score"] == 0
        assert result["issues"] == []
        assert result["suggestions"] == []
        assert result["metrics"] == {}
        assert result["analyzer"] == "ConcreteAnalyzer"
        assert "timestamp" in result

        # Verify timestamp is valid ISO format
        datetime.fromisoformat(result["timestamp"])

    def test_create_base_result_outside_workspace(self, analyzer, tmp_path):
        """Test creating base result for file outside workspace."""
        outside_file = tmp_path.parent / "outside.py"
        outside_file.write_text("content")

        result = analyzer.create_base_result(outside_file, "quick")

        assert result["file"] == str(outside_file)  # Should use full path

    @patch("coder_mcp.analysis.file_metrics.FileMetricsCollector.collect_basic_metrics")
    def test_get_basic_metrics_success(self, mock_collect, analyzer, tmp_path):
        """Test successful basic metrics collection."""
        test_file = tmp_path / "test.py"
        content = "print('hello')"

        mock_collect.return_value = {"lines": 1, "chars": 13}

        result = analyzer.get_basic_metrics(content, test_file)

        assert result == {"lines": 1, "chars": 13}
        mock_collect.assert_called_once_with(content, test_file)

    @patch("coder_mcp.analysis.file_metrics.FileMetricsCollector.collect_basic_metrics")
    def test_get_basic_metrics_failure(self, mock_collect, analyzer, tmp_path):
        """Test basic metrics collection failure."""
        test_file = tmp_path / "test.py"
        content = "print('hello')"

        mock_collect.side_effect = Exception("Metrics collection failed")

        with pytest.raises(AnalysisError) as exc_info:
            analyzer.get_basic_metrics(content, test_file)

        assert "Failed to collect basic metrics" in str(exc_info.value)
        assert exc_info.value.file_path == test_file

    def test_supports_file_with_supported_extensions(self, analyzer, tmp_path):
        """Test supports_file with supported extensions."""
        # ConcreteAnalyzer supports .test and .mock extensions
        test_cases = [
            (tmp_path / "file.test", True),
            (tmp_path / "file.mock", True),
            (tmp_path / "file.TEST", True),  # Case insensitive
            (tmp_path / "file.py", False),
            (tmp_path / "file.js", False),
        ]

        for file_path, expected in test_cases:
            result = analyzer.supports_file(file_path)
            assert result == expected

    def test_supports_file_with_generic_extensions(self, analyzer):
        """Test supports_file with generic analyzer (supports all)."""
        # Mock analyzer that supports all files
        analyzer.get_file_extensions = lambda: ["*"]

        test_files = [
            Path("file.py"),
            Path("file.js"),
            Path("file.unknown"),
            Path("no_extension"),
        ]

        for file_path in test_files:
            assert analyzer.supports_file(file_path) is True

    def test_log_analysis_start(self, analyzer, tmp_path):
        """Test analysis start logging."""
        test_file = tmp_path / "test.py"

        with patch.object(analyzer.logger, "debug") as mock_debug:
            analyzer.log_analysis_start(test_file, "deep")

        mock_debug.assert_called_once()
        log_message = mock_debug.call_args[0][0]
        assert "Starting deep analysis" in log_message
        assert str(test_file) in log_message

    def test_log_analysis_complete(self, analyzer, tmp_path):
        """Test analysis completion logging."""
        test_file = tmp_path / "test.py"
        quality_score = 7.5

        with patch.object(analyzer.logger, "debug") as mock_debug:
            analyzer.log_analysis_complete(test_file, quality_score)

        mock_debug.assert_called_once()
        log_message = mock_debug.call_args[0][0]
        assert "Completed analysis" in log_message
        assert str(test_file) in log_message
        assert "7.5" in log_message

    def test_abstract_methods_implementation(self, analyzer):
        """Test that abstract methods are properly implemented."""
        # These should not raise NotImplementedError
        extensions = analyzer.get_file_extensions()
        assert isinstance(extensions, list)

        smells = analyzer.detect_code_smells("content", Path("test.py"), ["test"])
        assert isinstance(smells, list)

        # analyze_file is async, test it separately in async test

    @pytest.mark.asyncio
    async def test_analyze_file_implementation(self, analyzer, tmp_path):
        """Test analyze_file implementation."""
        test_file = tmp_path / "test.py"
        test_file.write_text("content")

        result = await analyzer.analyze_file(test_file, "security")

        assert analyzer.analyze_file_called
        assert result["analysis_type"] == "security"
        assert isinstance(result, dict)

    def test_logger_configuration(self, analyzer):
        """Test logger is properly configured."""
        assert analyzer.logger is not None
        assert analyzer.logger.name == "coder_mcp.analysis.base_analyzer.ConcreteAnalyzer"
        assert isinstance(analyzer.logger, logging.Logger)


class TestBaseAnalyzerEdgeCases:
    """Test edge cases and boundary conditions for BaseAnalyzer."""

    def test_very_long_paths(self, tmp_path):
        """Test handling of very long file paths."""
        # Create nested directory structure
        long_path = tmp_path
        for i in range(10):
            long_path = long_path / f"very_long_directory_name_{i}"
        long_path.mkdir(parents=True)

        analyzer = ConcreteAnalyzer(tmp_path)

        test_file = long_path / "test_file_with_very_long_name.test"
        test_file.write_text("content")

        # Should handle long paths gracefully
        result = analyzer.validate_file_path(test_file)
        assert result == test_file.resolve()

    def test_unicode_paths(self, tmp_path):
        """Test handling of unicode file paths."""
        analyzer = ConcreteAnalyzer(tmp_path)

        # Create file with unicode characters
        unicode_file = tmp_path / "тест_файл.test"
        unicode_file.write_text("content")

        result = analyzer.validate_file_path(unicode_file)
        assert result == unicode_file.resolve()

    def test_special_characters_in_paths(self, tmp_path):
        """Test handling of special characters in paths."""
        analyzer = ConcreteAnalyzer(tmp_path)

        # Create files with special characters
        special_files = [
            tmp_path / "file with spaces.test",
            tmp_path / "file-with-dashes.test",
            tmp_path / "file_with_underscores.test",
            tmp_path / "file@with$symbols.test",
        ]

        for file_path in special_files:
            file_path.write_text("content")
            result = analyzer.validate_file_path(file_path)
            assert result == file_path.resolve()

    def test_symlink_handling(self, tmp_path):
        """Test handling of symbolic links."""
        analyzer = ConcreteAnalyzer(tmp_path)

        # Create original file
        original_file = tmp_path / "original.test"
        original_file.write_text("content")

        # Create symlink (skip if not supported)
        try:
            symlink_file = tmp_path / "symlink.test"
            symlink_file.symlink_to(original_file)

            result = analyzer.validate_file_path(symlink_file)
            assert result == symlink_file.resolve()
        except OSError:
            # Symlinks not supported on this system, skip test
            pytest.skip("Symlinks not supported")

    def test_concurrent_access(self, tmp_path):
        """Test thread safety of BaseAnalyzer."""
        import threading

        analyzer = ConcreteAnalyzer(tmp_path)
        results = []
        errors = []

        def validate_file_worker(file_num):
            try:
                test_file = tmp_path / f"test_{file_num}.test"
                test_file.write_text(f"content {file_num}")
                result = analyzer.validate_file_path(test_file)
                results.append((file_num, result))
            except Exception as e:
                errors.append((file_num, e))

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=validate_file_worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0
        assert len(results) == 10

        for file_num, result in results:
            expected_file = tmp_path / f"test_{file_num}.test"
            assert result == expected_file.resolve()

    def test_memory_usage_with_large_operations(self, tmp_path):
        """Test memory efficiency with large file operations."""
        analyzer = ConcreteAnalyzer(tmp_path)

        # Create file with substantial content
        large_content = "x" * 10000  # 10KB content
        test_file = tmp_path / "large_file.test"
        test_file.write_text(large_content)

        # Should handle large files without issues
        result = analyzer.validate_file_path(test_file)
        assert result == test_file.resolve()

        # Test creating base result for large file
        base_result = analyzer.create_base_result(test_file, "deep")
        assert base_result["file"] == "large_file.test"

    def test_error_chaining(self, tmp_path):
        """Test proper error chaining in exception handling."""
        analyzer = ConcreteAnalyzer(tmp_path)

        # Test with mock that raises ValueError (which gets wrapped in AnalysisError)
        with patch.object(Path, "resolve", side_effect=ValueError("Invalid path")):
            with pytest.raises(AnalysisError) as exc_info:
                analyzer.validate_file_path(tmp_path / "test.py")

            # Should have cause set
            assert exc_info.value.cause is not None
            assert isinstance(exc_info.value.cause, ValueError)

    def test_workspace_root_edge_cases(self):
        """Test workspace root validation edge cases."""
        # Test with root directory (if accessible)
        try:
            root_analyzer = ConcreteAnalyzer(Path("/"))
            assert root_analyzer.workspace_root == Path("/").resolve()
        except (PermissionError, AnalysisError):
            # Root not accessible, which is fine
            pass

        # Test with current directory
        cwd_analyzer = ConcreteAnalyzer(Path("."))
        assert cwd_analyzer.workspace_root == Path(".").resolve()

    def test_analysis_type_normalization_edge_cases(self, tmp_path):
        """Test analysis type normalization with edge cases."""
        analyzer = ConcreteAnalyzer(tmp_path)

        edge_cases = [
            ("", "quick"),  # Empty string
            ("   ", "quick"),  # Only whitespace
            ("QUICK", "quick"),  # All caps
            ("Quick", "quick"),  # Mixed case
            ("unknown", "quick"),  # Unknown type
            ("123", "quick"),  # Numeric string
        ]

        for input_type, expected in edge_cases:
            result = analyzer.validate_analysis_type(input_type)
            assert result == expected
