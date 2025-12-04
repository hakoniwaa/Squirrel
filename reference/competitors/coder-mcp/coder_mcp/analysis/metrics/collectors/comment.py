"""
Comment processing and counting functionality

This module handles comment detection and counting for different file types,
including Python docstrings and JavaScript block comments.
"""

from typing import List

from ..protocols import CommentCounterProtocol
from .utils.docstring_state import BlockCommentState, DocstringState


class CommentConfiguration:
    """Configuration constants for comment processing"""

    # Minimum occurrences for same-line docstring detection
    MIN_DOCSTRING_OCCURRENCES = 2

    # Python file extensions
    PYTHON_EXTENSIONS = (".py",)

    # JavaScript/TypeScript extensions
    JS_EXTENSIONS = (".js", ".ts", ".jsx", ".tsx")

    # Generic comment prefixes
    GENERIC_COMMENT_PREFIXES = ("#", "//", "/*", "*", "--", "%")

    # Python docstring patterns
    PYTHON_DOCSTRING_PATTERNS = ['"""', "'''"]

    # JavaScript comment patterns
    JS_BLOCK_COMMENT_START = "/*"
    JS_BLOCK_COMMENT_END = "*/"
    JS_SINGLE_LINE_COMMENT = "//"


class PythonCommentCounter:
    """Specialized counter for Python comments and docstrings"""

    def __init__(self):
        self.state = DocstringState()

    def count(self, lines: List[str]) -> int:
        """Count Python comment lines including docstrings"""
        comment_count = 0
        self.state = DocstringState()  # Reset state

        for line in lines:
            stripped = line.strip()

            if self._is_single_line_comment(stripped):
                comment_count += 1
                continue

            comment_count += self._process_docstring_line(stripped)

        return int(comment_count)

    def _is_single_line_comment(self, stripped_line: str) -> bool:
        """Check if line is a single-line comment"""
        return bool(stripped_line.startswith("#"))

    def _process_docstring_line(self, stripped_line: str) -> int:
        """Process a line for docstring detection"""
        for delimiter in CommentConfiguration.PYTHON_DOCSTRING_PATTERNS:
            if delimiter in stripped_line:
                return int(self._handle_docstring_delimiter(stripped_line, delimiter))

        # No delimiter found, check if we're in a docstring
        return int(1 if self.state.in_docstring else 0)

    def _handle_docstring_delimiter(self, stripped_line: str, delimiter: str) -> int:
        """Handle docstring delimiter detection with reduced complexity"""
        delimiter_count = stripped_line.count(delimiter)

        if not self.state.in_docstring:
            return int(self._handle_docstring_start(stripped_line, delimiter, delimiter_count))
        elif self.state.is_matching_delimiter(delimiter):
            return int(self._handle_docstring_end(stripped_line, delimiter))
        else:
            # In docstring, different delimiter
            return 1

    def _handle_docstring_start(
        self, _stripped_line: str, delimiter: str, delimiter_count: int
    ) -> int:
        """Handle the start of a docstring"""
        self.state.start_docstring(delimiter)

        # Check if it ends on the same line
        if delimiter_count >= CommentConfiguration.MIN_DOCSTRING_OCCURRENCES:
            self.state.end_docstring()

        return 1

    def _handle_docstring_end(self, stripped_line: str, delimiter: str) -> int:
        """Handle the end of a docstring"""
        self.state.end_docstring()
        return int(0 if stripped_line.startswith(delimiter) else 1)


class JavaScriptCommentCounter:
    """Specialized counter for JavaScript/TypeScript comments"""

    def __init__(self):
        self.state = BlockCommentState()

    def count(self, lines: List[str]) -> int:
        """Count JavaScript/TypeScript comment lines"""
        comment_count = 0
        self.state = BlockCommentState()  # Reset state

        for line in lines:
            stripped = line.strip()
            comment_count += self._process_comment_line(stripped)

        return comment_count

    def _process_comment_line(self, stripped_line: str) -> int:
        """Process JavaScript comment line"""
        # Handle single-line comments
        if stripped_line.startswith(CommentConfiguration.JS_SINGLE_LINE_COMMENT):
            return 1

        # Handle block comments
        return self._process_block_comment(stripped_line)

    def _process_block_comment(self, stripped_line: str) -> int:
        """Process JavaScript block comment with reduced complexity"""
        config = CommentConfiguration

        if config.JS_BLOCK_COMMENT_START in stripped_line:
            if config.JS_BLOCK_COMMENT_END in stripped_line:
                # Single-line block comment
                return 1
            else:
                # Start of multi-line block comment
                self.state.start_block_comment()
                return 1
        elif self.state.in_block_comment:
            if config.JS_BLOCK_COMMENT_END in stripped_line:
                self.state.end_block_comment()
            return 1

        return 0


class GenericCommentCounter:
    """Generic comment counter for other file types"""

    def count(self, lines: List[str]) -> int:
        """Count comments in generic files"""
        comment_count = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(CommentConfiguration.GENERIC_COMMENT_PREFIXES):
                comment_count += 1

        return comment_count


class CommentProcessor(CommentCounterProtocol):
    """Main comment processing coordinator"""

    def __init__(self):
        self.python_counter = PythonCommentCounter()
        self.js_counter = JavaScriptCommentCounter()
        self.generic_counter = GenericCommentCounter()

    def count_comment_lines(self, lines: List[str], file_extension: str) -> int:
        """Count comment lines based on file type"""
        return int(self.count_comments(lines, file_extension))

    def count_comments(self, lines: List[str], file_extension: str) -> int:
        """Count comment lines based on file type (Protocol implementation)"""
        if file_extension in CommentConfiguration.PYTHON_EXTENSIONS:
            return int(self.python_counter.count(lines))
        elif file_extension in CommentConfiguration.JS_EXTENSIONS:
            return int(self.js_counter.count(lines))
        else:
            return int(self.generic_counter.count(lines))
