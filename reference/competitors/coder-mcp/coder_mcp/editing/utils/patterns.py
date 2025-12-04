"""
Pattern utilities with caching for improved performance.
Provides cached regex compilation and pattern matching utilities.
"""

import re
from functools import lru_cache
from typing import Dict, List, Optional, Tuple


@lru_cache(maxsize=256)
def compile_pattern(pattern: str, flags: int = 0) -> re.Pattern:
    """
    Compile and cache regex patterns.

    Args:
        pattern: Regular expression pattern
        flags: Regex flags (e.g., re.IGNORECASE)

    Returns:
        Compiled regex pattern
    """
    return re.compile(pattern, flags)


@lru_cache(maxsize=512)
def cached_search(pattern: str, text: str, flags: int = 0) -> Optional[Tuple[int, int]]:
    """
    Cached regex search returning match positions.

    Args:
        pattern: Regex pattern to search for
        text: Text to search in
        flags: Regex flags

    Returns:
        Tuple of (start, end) positions if found, None otherwise
    """
    compiled = compile_pattern(pattern, flags)
    match = compiled.search(text)
    return (match.start(), match.end()) if match else None


@lru_cache(maxsize=512)
def cached_findall(pattern: str, text: str, flags: int = 0) -> List[str]:
    """
    Cached findall operation.

    Args:
        pattern: Regex pattern
        text: Text to search
        flags: Regex flags

    Returns:
        List of all matches
    """
    compiled = compile_pattern(pattern, flags)
    return compiled.findall(text)


class PatternMatcher:
    """Efficient pattern matcher with caching."""

    def __init__(self):
        """Initialize pattern matcher with common patterns."""
        self._initialize_common_patterns()

    def _initialize_common_patterns(self):
        """Pre-compile commonly used patterns."""
        self.common_patterns = {
            "function_def": compile_pattern(r"^(\s*)def\s+(\w+)\s*\(([^)]*)\):"),
            "class_def": compile_pattern(r"^(\s*)class\s+(\w+)"),
            "import": compile_pattern(r"^(?:from\s+\S+\s+)?import\s+.+"),
            "todo_comment": compile_pattern(r"#\s*TODO:?\s*(.+?)$", re.IGNORECASE),
            "docstring_start": compile_pattern(r'^\s*("""|\'\'\')'),
            "docstring_end": compile_pattern(r'("""|\'\'\')'),
            "variable_assignment": compile_pattern(r"(\w+)\s*=\s*(.+)"),
            "type_hint": compile_pattern(r":\s*([A-Za-z_]\w*(?:\[.+?\])?)"),
            "decorator": compile_pattern(r"^@\w+"),
            "whitespace_only": compile_pattern(r"^\s*$"),
            "comment_line": compile_pattern(r"^\s*#"),
            "print_statement": compile_pattern(r"print\s*\("),
            "logger_statement": compile_pattern(r"logger\.\w+\s*\("),
            "try_except": compile_pattern(r"^\s*try\s*:"),
            "if_statement": compile_pattern(r"^\s*if\s+.+:"),
            "for_loop": compile_pattern(r"^\s*for\s+.+:"),
            "while_loop": compile_pattern(r"^\s*while\s+.+:"),
        }

    def match_function_def(self, line: str) -> Optional[Dict[str, str]]:
        """
        Match function definition and extract components.

        Args:
            line: Line to match

        Returns:
            Dict with 'indent', 'name', 'params' if match, None otherwise
        """
        match = self.common_patterns["function_def"].match(line)
        if match:
            return {"indent": match.group(1), "name": match.group(2), "params": match.group(3)}
        return None

    def match_class_def(self, line: str) -> Optional[Dict[str, str]]:
        """
        Match class definition and extract components.

        Args:
            line: Line to match

        Returns:
            Dict with 'indent', 'name' if match, None otherwise
        """
        match = self.common_patterns["class_def"].match(line)
        if match:
            return {"indent": match.group(1), "name": match.group(2)}
        return None

    def find_todos(self, text: str) -> List[Tuple[int, str]]:
        """
        Find all TODO comments in text.

        Args:
            text: Text to search

        Returns:
            List of (line_number, todo_text) tuples
        """
        todos = []
        for i, line in enumerate(text.splitlines(), 1):
            match = self.common_patterns["todo_comment"].search(line)
            if match:
                todos.append((i, match.group(1)))
        return todos

    def is_whitespace_only(self, line: str) -> bool:
        """Check if line contains only whitespace."""
        return bool(self.common_patterns["whitespace_only"].match(line))

    def is_comment(self, line: str) -> bool:
        """Check if line is a comment."""
        return bool(self.common_patterns["comment_line"].match(line))

    def extract_indentation(self, line: str) -> str:
        """Extract leading whitespace from line."""
        match = re.match(r"^(\s*)", line)
        return match.group(1) if match else ""


# Global instance for convenience
pattern_matcher = PatternMatcher()


def clear_pattern_cache():
    """Clear all pattern caches (useful for testing or memory management)."""
    compile_pattern.cache_clear()
    cached_search.cache_clear()
    cached_findall.cache_clear()


def get_cache_info():
    """Get cache statistics for monitoring."""
    # Get cache info for all cached functions
    compile_info = compile_pattern.cache_info()
    search_info = cached_search.cache_info()  # noqa: E1123
    findall_info = cached_findall.cache_info()  # noqa: E1123

    return {
        "compile_pattern": compile_info,
        "cached_search": search_info,
        "cached_findall": findall_info,
    }
