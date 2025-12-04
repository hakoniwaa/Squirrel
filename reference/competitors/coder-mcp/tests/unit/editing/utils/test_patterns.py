"""
Unit tests for coder_mcp.editing.utils.patterns module.
Tests pattern compilation, caching, and pattern matching utilities.
"""

import re
from unittest.mock import patch

import pytest

from coder_mcp.editing.utils.patterns import (
    PatternMatcher,
    cached_findall,
    cached_search,
    compile_pattern,
)


class TestCompilePattern:
    """Test the compile_pattern function."""

    def test_basic_pattern_compilation(self):
        """Test basic pattern compilation."""
        pattern = compile_pattern(r"\d+")
        assert isinstance(pattern, re.Pattern)
        assert pattern.pattern == r"\d+"

    def test_pattern_with_flags(self):
        """Test pattern compilation with flags."""
        pattern = compile_pattern(r"hello", re.IGNORECASE)
        assert pattern.flags & re.IGNORECASE

        # Test that it matches case-insensitively
        assert pattern.match("HELLO") is not None
        assert pattern.match("hello") is not None

    def test_pattern_caching(self):
        """Test that patterns are cached."""
        # Call twice with same arguments
        pattern1 = compile_pattern(r"test")
        pattern2 = compile_pattern(r"test")

        # Should return the same object due to caching
        assert pattern1 is pattern2

    def test_cache_with_different_flags(self):
        """Test that patterns with different flags are cached separately."""
        pattern1 = compile_pattern(r"test", 0)
        pattern2 = compile_pattern(r"test", re.IGNORECASE)

        # Should be different objects
        assert pattern1 is not pattern2
        assert pattern1.flags != pattern2.flags

    @pytest.mark.parametrize(
        "pattern",
        [
            r"\d+",
            r"[a-zA-Z]+",
            r"^\s*def\s+\w+",
            r"(?P<name>\w+)=(?P<value>.+)",
        ],
    )
    def test_various_patterns(self, pattern):
        """Test compilation of various regex patterns."""
        compiled = compile_pattern(pattern)
        assert compiled.pattern == pattern


class TestCachedSearch:
    """Test the cached_search function."""

    def test_basic_search(self):
        """Test basic pattern search."""
        result = cached_search(r"\d+", "abc123def")
        assert result == (3, 6)

    def test_search_no_match(self):
        """Test search when pattern doesn't match."""
        result = cached_search(r"\d+", "abcdef")
        assert result is None

    def test_search_with_flags(self):
        """Test search with regex flags."""
        result = cached_search(r"HELLO", "hello world", re.IGNORECASE)
        assert result == (0, 5)

    def test_search_caching(self):
        """Test that search results are cached."""
        text = "test123"
        pattern = r"\d+"

        # Call twice with same arguments
        with patch("coder_mcp.editing.utils.patterns.compile_pattern") as mock_compile:
            mock_compile.return_value = re.compile(pattern)

            result1 = cached_search(pattern, text)
            result2 = cached_search(pattern, text)

            # compile_pattern should only be called once due to caching
            mock_compile.assert_called_once()
            assert result1 == result2

    @pytest.mark.parametrize(
        "pattern,text,expected",
        [
            (r"^hello", "hello world", (0, 5)),
            (r"world$", "hello world", (6, 11)),
            (r"\b\w{3}\b", "the cat sat", (0, 3)),
            (r"[aeiou]+", "beautiful", (1, 4)),  # Fixed: eau is 3 chars (1:4)
        ],
    )
    def test_various_searches(self, pattern, text, expected):
        """Test various search patterns."""
        result = cached_search(pattern, text)
        assert result == expected


class TestCachedFindall:
    """Test the cached_findall function."""

    def test_basic_findall(self):
        """Test basic findall operation."""
        result = cached_findall(r"\d+", "123 abc 456 def 789")
        assert result == ["123", "456", "789"]

    def test_findall_no_matches(self):
        """Test findall when no matches found."""
        result = cached_findall(r"\d+", "abc def ghi")
        assert result == []

    def test_findall_with_flags(self):
        """Test findall with regex flags."""
        result = cached_findall(r"[A-Z]+", "Hello WORLD", re.IGNORECASE)
        assert result == ["Hello", "WORLD"]

    def test_findall_caching(self):
        """Test that findall results are cached."""
        text = "a1 b2 c3"
        pattern = r"\w\d"

        # Clear cache first to ensure clean test
        cached_findall.cache_clear()

        # First call
        result1 = cached_findall(pattern, text)
        cache_info1 = cached_findall.cache_info()

        # Second call with same arguments
        result2 = cached_findall(pattern, text)
        cache_info2 = cached_findall.cache_info()

        assert result1 == result2
        assert cache_info2.hits == cache_info1.hits + 1

    @pytest.mark.parametrize(
        "pattern,text,expected",
        [
            (r"\w+", "hello world", ["hello", "world"]),
            (r"\d{2,}", "1 22 333 4444", ["22", "333", "4444"]),
            (r"[aeiou]", "hello", ["e", "o"]),
            (r"\b\w{4}\b", "this is a test case", ["this", "test", "case"]),
        ],
    )
    def test_various_findall(self, pattern, text, expected):
        """Test various findall patterns."""
        result = cached_findall(pattern, text)
        assert result == expected


class TestPatternMatcher:
    """Test the PatternMatcher class."""

    @pytest.fixture
    def matcher(self):
        """Create a PatternMatcher instance."""
        return PatternMatcher()

    def test_initialization(self, matcher):
        """Test PatternMatcher initialization."""
        assert hasattr(matcher, "common_patterns")
        assert isinstance(matcher.common_patterns, dict)

        # Check some common patterns are present
        expected_patterns = [
            "function_def",
            "class_def",
            "import",
            "todo_comment",
            "docstring_start",
            "variable_assignment",
            "decorator",
        ]
        for pattern_name in expected_patterns:
            assert pattern_name in matcher.common_patterns
            assert isinstance(matcher.common_patterns[pattern_name], re.Pattern)

    def test_match_function_def(self, matcher):
        """Test matching function definitions."""
        # Standard function
        result = matcher.match_function_def("def hello():")
        assert result == {"indent": "", "name": "hello", "params": ""}

        # Function with parameters
        result = matcher.match_function_def("    def greet(name, age=18):")
        assert result == {"indent": "    ", "name": "greet", "params": "name, age=18"}

        # No match
        result = matcher.match_function_def("not a function")
        assert result is None

    def test_match_class_def(self, matcher):
        """Test matching class definitions."""
        # Simple class
        result = matcher.match_class_def("class MyClass:")
        assert result == {"indent": "", "name": "MyClass"}

        # Class with inheritance
        result = matcher.match_class_def("    class Child(Parent):")
        assert result == {"indent": "    ", "name": "Child"}

        # No match
        result = matcher.match_class_def("not a class")
        assert result is None

    def test_find_todos(self, matcher):
        """Test finding TODO comments."""
        code = """
# TODO: Fix this bug
# todo: add tests
# TODO Add documentation
# Not a todo
print("TODO: in string")  # TODO: another todo
        """

        todos = matcher.find_todos(code)
        assert len(todos) == 4
        # Check that todos is a list of tuples (line_num, todo_text)
        todo_texts = [t[1] for t in todos]
        assert "Fix this bug" in todo_texts
        assert "add tests" in todo_texts
        assert "Add documentation" in todo_texts
        assert "another todo" in todo_texts

    def test_extract_indentation(self, matcher):
        """Test extracting indentation."""
        assert matcher.extract_indentation("no indent") == ""
        assert matcher.extract_indentation("    four spaces") == "    "
        assert matcher.extract_indentation("\ttab") == "\t"
        assert matcher.extract_indentation("  \t  mixed") == "  \t  "
        assert matcher.extract_indentation("") == ""


class TestPatternPerformance:
    """Test performance-related aspects of pattern matching."""

    def test_cache_effectiveness(self):
        """Test that caching improves performance."""
        # Clear caches
        compile_pattern.cache_clear()
        cached_search.cache_clear()
        cached_findall.cache_clear()

        # Perform multiple operations
        for _ in range(100):
            compile_pattern(r"\d+")
            cached_search(r"\w+", "hello world")
            cached_findall(r"[aeiou]", "beautiful day")

        # Check cache statistics
        compile_info = compile_pattern.cache_info()
        search_info = cached_search.cache_info()
        findall_info = cached_findall.cache_info()

        # Should have high hit rates
        assert compile_info.hits > 90
        assert search_info.hits > 90
        assert findall_info.hits > 90

    def test_cache_size_limits(self):
        """Test that cache size limits are respected."""
        # Clear cache
        compile_pattern.cache_clear()

        # Fill cache beyond limit (maxsize=256)
        for i in range(300):
            compile_pattern(f"pattern_{i}")

        cache_info = compile_pattern.cache_info()
        assert cache_info.currsize <= 256
