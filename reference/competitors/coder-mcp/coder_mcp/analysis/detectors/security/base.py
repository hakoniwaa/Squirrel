"""
Base classes and utilities for security detection - shared across all security detectors
"""

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class SecurityIssue:
    """Represents a detected security issue with comprehensive metadata"""

    issue_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    file_path: str
    line_number: int
    description: str
    recommendation: str
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID
    owasp_category: Optional[str] = None
    code_snippet: str = ""


@dataclass
class VulnerabilityPattern:
    """Configuration for vulnerability detection patterns with metadata"""

    patterns: List[str]
    severity: str
    description: str
    recommendation: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


@dataclass
class SecurityContext:
    """Immutable context for security analysis operations"""

    content: str
    lines: List[str]
    file_path: Path


class SecurityAnalysisUtils:
    """Centralized utilities for security analysis operations"""

    @staticmethod
    def find_pattern_matches(content: str, pattern: str) -> List[re.Match]:
        """
        Find all regex matches for a pattern in content.

        Args:
            content: The source code content to search
            pattern: The regex pattern to find

        Returns:
            List of regex match objects
        """
        try:
            return list(re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE))
        except Exception:
            # Log regex errors but don't fail the entire analysis
            return []

    @staticmethod
    def get_line_number_from_match(content: str, match: re.Match) -> int:
        """
        Calculate line number from a regex match position.

        Args:
            content: The source code content
            match: The regex match object

        Returns:
            Line number (1-indexed)
        """
        return content[: match.start()].count("\n") + 1

    @staticmethod
    def get_code_snippet(lines: List[str], line_number: int, context_lines: int = 0) -> str:
        """
        Extract code snippet with optional context lines.

        Args:
            lines: List of source code lines
            line_number: Target line number (1-indexed)
            context_lines: Number of context lines before and after

        Returns:
            Code snippet string
        """
        if line_number <= 0 or line_number > len(lines):
            return ""

        start_line = max(1, line_number - context_lines)
        end_line = min(len(lines), line_number + context_lines)

        snippet_lines = lines[start_line - 1 : end_line]
        return "\n".join(snippet_lines).strip()

    @staticmethod
    def is_comment_line(line: str) -> bool:
        """
        Check if a line is a comment (should be ignored in analysis).

        Args:
            line: Source code line to check

        Returns:
            True if line is a comment
        """
        stripped = line.strip()
        return stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*")

    @staticmethod
    def calculate_entropy(text: str) -> float:
        """
        Calculate Shannon entropy of text (useful for secret detection).

        Args:
            text: Text to analyze

        Returns:
            Entropy value (higher = more random/likely secret)
        """
        if not text:
            return 0.0

        # Calculate character frequency
        char_counts: dict[str, int] = {}
        for char in text:
            char_counts[char] = char_counts.get(char, 0) + 1

        # Calculate entropy
        entropy = 0.0
        text_length = len(text)

        for count in char_counts.values():
            probability = count / text_length
            if probability > 0:
                entropy -= probability * math.log2(probability)

        return entropy

    @staticmethod
    def is_likely_test_file(file_path: Path) -> bool:
        """
        Determine if file is likely a test file (may have different security standards).

        Args:
            file_path: Path to analyze

        Returns:
            True if appears to be a test file
        """
        path_str = str(file_path).lower()
        test_indicators = ["test_", "_test", "tests/", "/test/", "spec_", "_spec"]
        return any(indicator in path_str for indicator in test_indicators)
