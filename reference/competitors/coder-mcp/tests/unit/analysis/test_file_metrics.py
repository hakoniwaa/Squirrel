"""Test file metrics functionality."""

from pathlib import Path

import pytest

from coder_mcp.analysis.file_metrics import FileMetricsCollector


class TestFileMetricsCollector:
    """Comprehensive test suite for FileMetricsCollector."""

    def test_collect_basic_metrics_simple_content(self):
        """Test basic metrics collection with simple content."""
        content = "line 1\nline 2\nline 3"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 3
        assert result["blank_lines"] == 0
        assert result["comment_lines"] == 0
        assert result["file_size_bytes"] == len(content.encode("utf-8"))

    def test_collect_basic_metrics_empty_content(self):
        """Test metrics collection with empty content."""
        content = ""
        file_path = Path("empty.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 0
        assert result["blank_lines"] == 0
        assert result["comment_lines"] == 0
        assert result["file_size_bytes"] == 0

    def test_collect_basic_metrics_with_blank_lines(self):
        """Test metrics collection with blank lines."""
        content = "line 1\n\n   \n\nline 2"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 5
        assert result["blank_lines"] == 3  # Empty line and whitespace-only lines
        assert result["comment_lines"] == 0

    def test_collect_basic_metrics_with_comments(self):
        """Test metrics collection with various comment styles."""
        content = "# Python comment\ncode line\n// JS comment\n/* CSS comment\n* Multiline comment"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 5
        assert result["blank_lines"] == 0
        assert result["comment_lines"] == 1  # Only lines starting with # are counted

    def test_collect_basic_metrics_mixed_content(self):
        """Test metrics collection with mixed content."""
        content = """# File header comment
import os

def function():
    # Inline comment
    pass


// Another comment style
/* Block comment start
"""
        file_path = Path("mixed.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 10
        assert result["blank_lines"] == 3
        assert result["comment_lines"] == 2  # Only # comments are counted

    def test_collect_basic_metrics_integration(self):
        """Integration test verifying all metrics work together correctly."""
        content = """# File header
import os
import sys

# Main function
def main():
    '''Main function docstring'''
    print("Hello, World!")  # Inline comment


    # Process data
    data = process_data()
    return data

// JavaScript-style comment
/* CSS-style comment
   continues here */
"""
        file_path = Path("integration_test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        # Verify all metrics are present and reasonable
        assert "lines_of_code" in result
        assert "blank_lines" in result
        assert "comment_lines" in result
        assert "file_size_bytes" in result

        # Verify specific counts based on actual implementation
        assert result["lines_of_code"] == 17  # Total lines including the newline at end
        assert result["blank_lines"] == 4
        assert result["comment_lines"] == 3  # Only # comments are counted
        assert result["file_size_bytes"] == len(content.encode("utf-8"))

    def test_collect_basic_metrics_performance(self):
        """Test performance with large content."""
        # Create large content
        large_content = "\n".join([f"line {i}" for i in range(1000)])
        large_content += "\n" + "\n".join([f"# comment {i}" for i in range(100)])

        file_path = Path("large_file.py")

        result = FileMetricsCollector.collect_basic_metrics(large_content, file_path)

        assert result["lines_of_code"] == 1100
        assert result["comment_lines"] == 100
        assert result["blank_lines"] == 0

    def test_pathlib_path_objects(self):
        """Test that methods work correctly with Path objects."""
        content = "# Test\ncode line"
        file_path = Path("test.py")

        # Ensure Path object is handled correctly
        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert isinstance(result, dict)
        assert all(
            key in result
            for key in ["lines_of_code", "blank_lines", "comment_lines", "file_size_bytes"]
        )

    @pytest.mark.parametrize(
        "content,expected_lines",
        [
            ("", 0),
            ("single line", 1),
            ("line 1\nline 2", 2),
            ("line 1\nline 2\n", 2),  # Splitlines doesn't count trailing empty
            ("line 1\nline 2\nline 3", 3),
        ],
    )
    def test_line_counting_edge_cases(self, content, expected_lines):
        """Parametrized test for various line counting scenarios."""
        file_path = Path("test.py")
        result = FileMetricsCollector.collect_basic_metrics(content, file_path)
        assert result["lines_of_code"] == expected_lines

    def test_comment_detection_python_style(self):
        """Test comment detection with Python-style comments only."""
        content = "# Comment 1\ncode\n# Comment 2\n  # Indented comment"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)
        assert result["comment_lines"] == 3  # Only # comments are counted

    def test_comment_detection_mixed_but_only_python_counted(self):
        """Test that only Python-style comments are counted."""
        content = "# Python comment\n// JS comment\n/* CSS comment\n* Continuation\ncode"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)
        assert result["comment_lines"] == 1  # Only # comment is counted

    def test_blank_line_detection_various_cases(self):
        """Test blank line detection with various whitespace scenarios."""
        content = "line1\n\n   \n\t\nline2"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)
        assert result["blank_lines"] == 3  # Empty, spaces, tabs

    def test_unicode_content_handling(self):
        """Test handling of unicode content."""
        content = "# Unicode comment: 🚀 émojis\ncode_line = 'test'"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 2
        assert result["comment_lines"] == 1
        assert result["file_size_bytes"] == len(content.encode("utf-8"))
        assert result["file_size_bytes"] > len(content)  # UTF-8 encoding is larger

    def test_whitespace_only_lines(self):
        """Test handling of whitespace-only lines."""
        content = "line1\n   \n\t\n \t \nline2"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 5
        assert result["blank_lines"] == 3  # All whitespace-only lines
        assert result["comment_lines"] == 0

    def test_comment_with_leading_whitespace(self):
        """Test comment detection with leading whitespace."""
        content = "   # Indented comment\n\t# Tabbed comment\ncode"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 3
        assert result["comment_lines"] == 2  # Both indented comments counted
        assert result["blank_lines"] == 0

    def test_edge_case_only_comments(self):
        """Test file with only comments."""
        content = "# Comment 1\n# Comment 2\n# Comment 3"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 3
        assert result["comment_lines"] == 3
        assert result["blank_lines"] == 0

    def test_edge_case_only_blank_lines(self):
        """Test file with only blank lines."""
        content = "\n\n   \n\t\n"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 4
        assert result["blank_lines"] == 4
        assert result["comment_lines"] == 0

    def test_long_lines_handling(self):
        """Test handling of very long lines."""
        long_line = "x" * 1000
        content = f"# Comment\n{long_line}\n# Another comment"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 3
        assert result["comment_lines"] == 2
        assert result["blank_lines"] == 0
        assert result["file_size_bytes"] == len(content.encode("utf-8"))

    def test_mixed_line_endings(self):
        """Test handling of mixed line endings."""
        content = "line1\nline2\rline3\r\nline4"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        # splitlines() handles mixed line endings correctly
        assert result["lines_of_code"] == 4
        assert result["blank_lines"] == 0
        assert result["comment_lines"] == 0

    def test_file_path_variations(self):
        """Test with different file path formats."""
        content = "# Test\ncode"

        # Test with different path formats
        paths = [
            Path("test.py"),
            Path("./test.py"),
            Path("/absolute/path/test.py"),
            Path("relative/path/test.py"),
        ]

        for path in paths:
            result = FileMetricsCollector.collect_basic_metrics(content, path)
            assert result["lines_of_code"] == 2
            assert result["comment_lines"] == 1

    def test_empty_string_edge_case(self):
        """Test completely empty string."""
        content = ""
        file_path = Path("empty.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 0
        assert result["blank_lines"] == 0
        assert result["comment_lines"] == 0
        assert result["file_size_bytes"] == 0

    def test_single_character_content(self):
        """Test single character content."""
        content = "x"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 1
        assert result["blank_lines"] == 0
        assert result["comment_lines"] == 0
        assert result["file_size_bytes"] == 1

    def test_newline_only_content(self):
        """Test content with only newlines."""
        content = "\n\n\n"
        file_path = Path("test.py")

        result = FileMetricsCollector.collect_basic_metrics(content, file_path)

        assert result["lines_of_code"] == 3
        assert result["blank_lines"] == 3
        assert result["comment_lines"] == 0
