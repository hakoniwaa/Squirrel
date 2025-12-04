"""
Generic code analyzer for files without specific language support.

This module provides baseline analysis capabilities for any text file, serving as
a fallback when language-specific analyzers are not available. It focuses on
universal code quality metrics and basic text analysis.

Classes:
    GenericAnalyzer: Universal code analyzer for unsupported file types
    GenericAnalysisError: Custom exception for generic analysis errors

Functions:
    is_text_file: Utility function to check if a file is likely a text file
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..analysis_result import AnalysisResult
from ..base_analyzer import AnalysisError, BaseAnalyzer
from ..metrics.collectors import MetricsCollector

# Constants
UNIVERSAL_EXTENSION = "*"  # Indicates support for all file types
DEFAULT_ENCODING = "utf-8"
ALTERNATIVE_ENCODINGS = ["latin-1", "cp1252", "ascii"]

# Line length thresholds
OPTIMAL_LINE_LENGTH = 80
ACCEPTABLE_LINE_LENGTH = 120
EXCESSIVE_LINE_LENGTH = 200

# File size thresholds (in lines)
SMALL_FILE_THRESHOLD = 100
MEDIUM_FILE_THRESHOLD = 500
LARGE_FILE_THRESHOLD = 1000
VERY_LARGE_FILE_THRESHOLD = 2000

# Comment patterns for various languages
COMMENT_PATTERNS = {
    "hash": "#",  # Python, Shell, Ruby, etc.
    "double_slash": "//",  # C++, Java, JavaScript, etc.
    "block_start": "/*",  # C, Java, CSS, etc.
    "block_line": "*",  # Block comment continuation
    "sql": "--",  # SQL
    "docstring_double": '"""',  # Python docstrings
    "docstring_single": "'''",  # Python docstrings
}

# Binary file indicators
BINARY_INDICATORS = {
    b"\x00",  # Null bytes
    b"\xff\xfe",  # UTF-16 LE BOM
    b"\xfe\xff",  # UTF-16 BE BOM
    b"\xef\xbb\xbf",  # UTF-8 BOM
}

logger = logging.getLogger(__name__)


class GenericAnalysisError(AnalysisError):
    """Custom exception for generic analysis errors."""

    def __init__(
        self,
        message: str,
        file_path: Optional[Path] = None,
        encoding_error: Optional[Exception] = None,
    ):
        super().__init__(message, file_path)
        self.encoding_error = encoding_error


class GenericAnalyzer(BaseAnalyzer):
    """Universal code analyzer for unsupported file types.

    This analyzer provides baseline analysis for any text file, focusing on:
    - Basic text metrics (lines, length, etc.)
    - Universal code quality issues (line length, whitespace, etc.)
    - File structure analysis
    - Encoding and format validation

    It serves as a fallback when specific language analyzers are not available
    and provides consistent analysis capabilities across all file types.

    Attributes:
        metrics_collector: Collects basic text and code metrics
    """

    def __init__(self, workspace_root: Path, validate_workspace: bool = True) -> None:
        """Initialize generic analyzer.

        Args:
            workspace_root: Root directory of the workspace
            validate_workspace: Whether to validate workspace exists (set False for testing)

        Raises:
            AnalysisError: If initialization fails
        """
        super().__init__(workspace_root, validate_workspace)

        try:
            self.metrics_collector = MetricsCollector()
        except (OSError, IOError, ValueError) as e:
            raise AnalysisError(f"Failed to initialize generic analyzer: {e}") from e

    def get_file_extensions(self) -> List[str]:
        """Return supported file extensions (all files as fallback).

        Returns:
            List containing universal extension indicator
        """
        return [UNIVERSAL_EXTENSION]

    async def analyze_file(self, file_path: Path, analysis_type: str = "quick") -> Dict[str, Any]:
        """Analyze a generic file and return comprehensive results.

        This method performs universal text analysis that can be applied to any
        file type, providing basic quality metrics and common issues detection.

        Args:
            file_path: Path to the file to analyze
            analysis_type: Type of analysis ("quick", "deep", "security", "performance")

        Returns:
            Dictionary containing comprehensive analysis results
        """
        # Validate inputs
        analysis_type = self.validate_analysis_type(analysis_type)
        file_path = self.validate_file_path(file_path)

        # Log analysis start
        self.log_analysis_start(file_path, analysis_type)

        # Create result container
        result = AnalysisResult(file_path, self.workspace_root)

        try:
            # Check if file is likely binary
            if self._is_likely_binary_file(file_path):
                return self._create_binary_file_result(file_path, analysis_type)

            # Read and validate file content
            content = self._read_file_content(file_path)

            # Collect comprehensive metrics
            metrics = self._collect_comprehensive_metrics(content, file_path)
            result.set_metrics(metrics)

            # Detect universal code issues
            issues = self._detect_universal_issues(content, file_path, analysis_type)

            # Process detected issues
            self._process_issues(result, issues)

            # Calculate quality score
            result.calculate_quality_score()

            # Log completion
            self.log_analysis_complete(file_path, result.quality_score)

            return self._finalize_result(result, analysis_type)

        except (OSError, ValueError, UnicodeDecodeError) as e:
            self.logger.error("Generic analysis failed for %s: %s", file_path, e)
            return self._create_error_result(file_path, str(e))

    def _is_likely_binary_file(self, file_path: Path) -> bool:
        """Check if file is likely a binary file.

        Args:
            file_path: Path to check

        Returns:
            True if file appears to be binary
        """
        try:
            # Check file extension first
            binary_extensions = {
                ".exe",
                ".dll",
                ".so",
                ".dylib",
                ".bin",
                ".obj",
                ".o",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".ico",
                ".svg",
                ".mp3",
                ".mp4",
                ".avi",
                ".mov",
                ".wav",
                ".pdf",
                ".zip",
                ".tar",
                ".gz",
                ".rar",
                ".7z",
                ".db",
                ".sqlite",
            }

            if file_path.suffix.lower() in binary_extensions:
                return True

            # Sample first few bytes
            with open(file_path, "rb") as f:
                sample = f.read(512)  # Read first 512 bytes

            # Check for binary indicators
            for indicator in BINARY_INDICATORS:
                if indicator in sample:
                    return True

            # Check for high ratio of non-printable characters
            printable_count = sum(1 for byte in sample if 32 <= byte <= 126 or byte in (9, 10, 13))
            if len(sample) > 0:
                printable_ratio = printable_count / len(sample)
                return printable_ratio < 0.7  # Less than 70% printable

            return False

        except (OSError, IOError, ValueError) as e:
            self.logger.warning("Could not determine if %s is binary: %s", file_path, e)
            return False

    def _read_file_content(self, file_path: Path) -> str:
        """Read file content with robust encoding handling.

        Args:
            file_path: Path to the file

        Returns:
            File content as string

        Raises:
            GenericAnalysisError: If file cannot be read
        """
        encodings_to_try = [DEFAULT_ENCODING] + ALTERNATIVE_ENCODINGS

        for encoding in encodings_to_try:
            try:
                with open(file_path, "r", encoding=encoding, errors="replace") as f:
                    content = f.read()
                self.logger.debug("Successfully read %s with %s encoding", file_path, encoding)
                return content
            except UnicodeDecodeError:
                continue
            except (OSError, IOError) as e:
                raise GenericAnalysisError(f"Cannot read file {file_path}: {e}", file_path) from e

        raise GenericAnalysisError(
            f"Cannot decode file {file_path} with any supported encoding", file_path
        )

    def _collect_comprehensive_metrics(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Collect comprehensive metrics for generic files.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            Dictionary of collected metrics
        """
        try:
            # Use the metrics collector for basic metrics
            metrics = self.metrics_collector.collect_generic_metrics(content, file_path)

            # Add additional universal metrics
            additional_metrics = self._calculate_additional_metrics(content)
            metrics.update(additional_metrics)

            return metrics

        except (ValueError, TypeError) as e:
            self.logger.warning("Failed to collect metrics for %s: %s", file_path, e)
            # Return basic metrics as fallback
            return self._calculate_basic_metrics(content)

    def _calculate_additional_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate additional universal metrics.

        Args:
            content: File content

        Returns:
            Dictionary of additional metrics
        """
        lines = content.splitlines()

        metrics = {
            "comment_lines": self._count_comment_lines(lines),
            "whitespace_issues": self._count_whitespace_issues(lines),
            "line_ending_consistency": self._check_line_ending_consistency(content),
            "character_distribution": self._analyze_character_distribution(content),
            "file_size_category": self._categorize_file_size(len(lines)),
            "indentation_analysis": self._analyze_indentation(lines),
        }

        return metrics

    def _calculate_basic_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate basic metrics as fallback.

        Args:
            content: File content

        Returns:
            Dictionary of basic metrics
        """
        lines = content.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]

        return {
            "total_lines": len(lines),
            "code_lines": len(non_empty_lines),
            "blank_lines": len(lines) - len(non_empty_lines),
            "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
            "max_line_length": max(len(line) for line in lines) if lines else 0,
            "total_characters": len(content),
        }

    def _detect_universal_issues(
        self, content: str, file_path: Path, analysis_type: str
    ) -> List[Dict[str, Any]]:
        """Detect universal code quality issues.

        Args:
            content: File content
            file_path: Path to the file
            analysis_type: Type of analysis

        Returns:
            List of detected issues
        """
        issues = []
        lines = content.splitlines()

        # Always check basic issues
        issues.extend(self._detect_long_lines(lines, file_path))
        issues.extend(self._detect_trailing_whitespace(lines, file_path))

        # Additional checks based on analysis type
        if analysis_type in ["deep", "security", "performance"]:
            issues.extend(self._detect_mixed_line_endings(content, file_path))
            issues.extend(self._detect_large_files(lines, file_path))
            issues.extend(self._detect_encoding_issues(content, file_path))

        if analysis_type in ["deep", "performance"]:
            issues.extend(self._detect_inefficient_patterns(lines, file_path))

        return issues

    def _detect_long_lines(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Detect lines that exceed reasonable length thresholds.

        Args:
            lines: File lines
            file_path: Path to the file

        Returns:
            List of long line issues
        """
        issues = []

        for i, line in enumerate(lines):
            line_length = len(line)

            if line_length > EXCESSIVE_LINE_LENGTH:
                severity = "high"
                suggestion = (
                    f"Break this extremely long line ({line_length} chars) into multiple lines"
                )
            elif line_length > ACCEPTABLE_LINE_LENGTH:
                severity = "medium"
                suggestion = (
                    f"Consider breaking this long line ({line_length} chars) for better readability"
                )
            elif line_length > OPTIMAL_LINE_LENGTH:
                severity = "low"
                suggestion = f"Line is {line_length} characters (optimal: {OPTIMAL_LINE_LENGTH})"
            else:
                continue

            issues.append(
                {
                    "type": "long_lines",
                    "file": str(file_path.relative_to(self.workspace_root)),
                    "line": i + 1,
                    "severity": severity,
                    "description": f"Line is {line_length} characters long",
                    "suggestion": suggestion,
                }
            )

        return issues

    def _detect_trailing_whitespace(
        self, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """Detect lines with trailing whitespace.

        Args:
            lines: File lines
            file_path: Path to the file

        Returns:
            List of trailing whitespace issues
        """
        issues = []

        for i, line in enumerate(lines):
            if line != line.rstrip():
                issues.append(
                    {
                        "type": "trailing_whitespace",
                        "file": str(file_path.relative_to(self.workspace_root)),
                        "line": i + 1,
                        "severity": "low",
                        "description": "Line has trailing whitespace",
                        "suggestion": "Remove trailing whitespace to maintain clean formatting",
                    }
                )

        return issues

    def _detect_mixed_line_endings(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect mixed line endings in file.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            List of line ending issues
        """
        issues = []

        has_crlf = "\r\n" in content
        has_lf = "\n" in content and "\r\n" not in content.replace("\r\n", "")
        has_cr = "\r" in content and "\r\n" not in content

        line_ending_types = sum([has_crlf, has_lf, has_cr])

        if line_ending_types > 1:
            endings = []
            if has_crlf:
                endings.append("CRLF (\\r\\n)")
            if has_lf:
                endings.append("LF (\\n)")
            if has_cr:
                endings.append("CR (\\r)")

            issues.append(
                {
                    "type": "mixed_line_endings",
                    "file": str(file_path.relative_to(self.workspace_root)),
                    "line": 1,
                    "severity": "medium",
                    "description": f"File has mixed line endings: {', '.join(endings)}",
                    "suggestion": "Use consistent line endings throughout the file",
                }
            )

        return issues

    def _detect_large_files(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Detect files that may be too large for maintainability.

        Args:
            lines: File lines
            file_path: Path to the file

        Returns:
            List of file size issues
        """
        issues: List[Dict[str, Any]] = []
        line_count = len(lines)

        if line_count > VERY_LARGE_FILE_THRESHOLD:
            severity = "high"
            suggestion = (
                f"File is very large ({line_count} lines). Consider splitting into smaller modules"
            )
        elif line_count > LARGE_FILE_THRESHOLD:
            severity = "medium"
            suggestion = (
                "File is large (" + str(line_count) + " lines). "
                "Consider refactoring for better maintainability"
            )
        else:
            return issues

        issues.append(
            {
                "type": "large_files",
                "file": str(file_path.relative_to(self.workspace_root)),
                "line": 1,
                "severity": severity,
                "description": f"File is {line_count} lines long",
                "suggestion": suggestion,
            }
        )

        return issues

    def _detect_encoding_issues(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect potential encoding issues.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            List of encoding issues
        """
        issues: List[Dict[str, Any]] = []

        # Check for replacement characters (indicating encoding issues)
        if "\ufffd" in content:
            issues.append(
                {
                    "type": "encoding_issues",
                    "file": str(file_path.relative_to(self.workspace_root)),
                    "line": 1,
                    "severity": "medium",
                    "description": (
                        "File contains replacement characters, " "indicating encoding issues"
                    ),
                    "suggestion": "Check file encoding and convert to UTF-8 if necessary",
                }
            )

        # Check for unusual byte order marks
        if content.startswith("\ufeff"):
            issues.append(
                {
                    "type": "encoding_issues",
                    "file": str(file_path.relative_to(self.workspace_root)),
                    "line": 1,
                    "severity": "low",
                    "description": "File starts with byte order mark (BOM)",
                    "suggestion": "Consider removing BOM for better compatibility",
                }
            )

        return issues

    def _detect_inefficient_patterns(
        self, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """Detect potentially inefficient patterns in text files.

        Args:
            lines: File lines
            file_path: Path to the file

        Returns:
            List of inefficiency issues
        """
        issues = []

        # Check for excessive blank lines
        consecutive_blank = 0
        for i, line in enumerate(lines):
            if not line.strip():
                consecutive_blank += 1
            else:
                if consecutive_blank > 3:
                    issues.append(
                        {
                            "type": "excessive_blank_lines",
                            "file": str(file_path.relative_to(self.workspace_root)),
                            "line": i - consecutive_blank + 1,
                            "severity": "low",
                            "description": f"{consecutive_blank} consecutive blank lines",
                            "suggestion": "Reduce excessive blank lines for better readability",
                        }
                    )
                consecutive_blank = 0

        return issues

    def _count_comment_lines(self, lines: List[str]) -> int:
        """Count comment lines using universal patterns.

        Args:
            lines: File lines

        Returns:
            Number of comment lines
        """
        comment_count = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check against common comment patterns
            for pattern in COMMENT_PATTERNS.values():
                if stripped.startswith(pattern):
                    comment_count += 1
                    break

        return comment_count

    def _count_whitespace_issues(self, lines: List[str]) -> int:
        """Count various whitespace-related issues.

        Args:
            lines: File lines

        Returns:
            Number of whitespace issues
        """
        issue_count = 0

        for line in lines:
            # Trailing whitespace
            if line != line.rstrip():
                issue_count += 1
            # Tabs mixed with spaces (basic detection)
            if "\t" in line and "    " in line:
                issue_count += 1

        return issue_count

    def _check_line_ending_consistency(self, content: str) -> str:
        """Check line ending consistency.

        Args:
            content: File content

        Returns:
            Line ending consistency status
        """
        has_crlf = "\r\n" in content
        has_lf = "\n" in content and "\r\n" not in content.replace("\r\n", "")
        has_cr = "\r" in content and "\r\n" not in content

        ending_types = sum([has_crlf, has_lf, has_cr])

        if ending_types == 0:
            return "none"
        if ending_types == 1:
            if has_crlf:
                return "crlf"
            if has_lf:
                return "lf"
            return "cr"
        return "mixed"

    def _analyze_character_distribution(self, content: str) -> Dict[str, float]:
        """Analyze character distribution in the file.

        Args:
            content: File content

        Returns:
            Character distribution statistics
        """
        if not content:
            return {}

        total_chars = len(content)
        alphanumeric = sum(1 for c in content if c.isalnum())
        whitespace = sum(1 for c in content if c.isspace())
        punctuation = sum(1 for c in content if not c.isalnum() and not c.isspace())

        return {
            "alphanumeric_ratio": alphanumeric / total_chars * 100,
            "whitespace_ratio": whitespace / total_chars * 100,
            "punctuation_ratio": punctuation / total_chars * 100,
        }

    def _categorize_file_size(self, line_count: int) -> str:
        """Categorize file size based on line count.

        Args:
            line_count: Number of lines in file

        Returns:
            Size category string
        """
        if line_count < SMALL_FILE_THRESHOLD:
            return "small"
        if line_count < MEDIUM_FILE_THRESHOLD:
            return "medium"
        if line_count < LARGE_FILE_THRESHOLD:
            return "large"
        if line_count < VERY_LARGE_FILE_THRESHOLD:
            return "very_large"
        return "huge"

    def _analyze_indentation(self, lines: List[str]) -> Dict[str, Any]:
        """Analyze indentation patterns in the file.

        Args:
            lines: File lines

        Returns:
            Indentation analysis results
        """
        spaces_count = 0
        tabs_count = 0
        mixed_count = 0

        for line in lines:
            if not line.strip():
                continue

            leading_spaces = len(line) - len(line.lstrip(" "))
            leading_tabs = len(line) - len(line.lstrip("\t"))

            if leading_tabs > 0 and leading_spaces > 0:
                mixed_count += 1
            elif leading_tabs > 0:
                tabs_count += 1
            elif leading_spaces > 0:
                spaces_count += 1

        return {
            "spaces_count": spaces_count,
            "tabs_count": tabs_count,
            "mixed_count": mixed_count,
            "consistency": "consistent" if mixed_count == 0 else "mixed",
            "primary_style": (
                "spaces" if spaces_count > tabs_count else "tabs" if tabs_count > 0 else "none"
            ),
        }

    def _process_issues(self, result: AnalysisResult, issues: List[Dict[str, Any]]) -> None:
        """Process detected issues and add them to the result.

        Args:
            result: Analysis result container
            issues: List of detected issues
        """
        for issue in issues:
            description = issue.get("description", "Unknown issue detected")
            result.add_issue(description)

            suggestion = issue.get("suggestion")
            if suggestion:
                result.add_suggestion(suggestion)

    def _create_binary_file_result(self, file_path: Path, analysis_type: str) -> Dict[str, Any]:
        """Create result for binary files.

        Args:
            file_path: Path to the binary file
            analysis_type: Type of analysis

        Returns:
            Result dictionary for binary file
        """
        try:
            relative_path = str(file_path.relative_to(self.workspace_root))
        except ValueError:
            relative_path = str(file_path)

        return {
            "file": relative_path,
            "analysis_type": analysis_type,
            "analyzer": "GenericAnalyzer",
            "file_type": "binary",
            "quality_score": 5,  # Neutral score for binary files
            "issues": ["File appears to be binary - no text analysis performed"],
            "suggestions": ["Exclude binary files from code analysis"],
            "metrics": {
                "file_size": file_path.stat().st_size if file_path.exists() else 0,
                "is_binary": True,
            },
            "timestamp": "",
        }

    def _finalize_result(self, result: AnalysisResult, analysis_type: str) -> Dict[str, Any]:
        """Finalize analysis result with additional metadata.

        Args:
            result: Analysis result container
            analysis_type: Type of analysis performed

        Returns:
            Finalized result dictionary
        """
        result_dict = result.to_dict()
        result_dict.update(
            {"analysis_type": analysis_type, "analyzer": "GenericAnalyzer", "file_type": "text"}
        )

        return result_dict

    def _create_error_result(self, file_path: Path, error_message: str) -> Dict[str, Any]:
        """Create error result for failed analysis.

        Args:
            file_path: Path to the file that failed analysis
            error_message: Error message

        Returns:
            Error result dictionary
        """
        try:
            relative_path = str(file_path.relative_to(self.workspace_root))
        except ValueError:
            relative_path = str(file_path)

        return {
            "file": relative_path,
            "error": error_message,
            "quality_score": 0,
            "analyzer": "GenericAnalyzer",
            "file_type": "unknown",
        }

    # Legacy method compatibility
    def detect_code_smells(
        self, content: str, file_path: Path, smell_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect code smells in generic files (legacy interface).

        This method maintains compatibility with the base class interface.

        Args:
            content: File content
            file_path: Path to the file
            smell_types: List of smell types to detect (mapped to universal issues)

        Returns:
            List of detected issues
        """
        # Map smell types to universal analysis
        analysis_type = "deep" if len(smell_types) > 3 else "quick"
        return self._detect_universal_issues(content, file_path, analysis_type)


def is_text_file(file_path: Path, sample_size: int = 512) -> bool:
    """Check if a file is likely a text file.

    Args:
        file_path: Path to check
        sample_size: Number of bytes to sample for analysis

    Returns:
        True if file appears to be text, False otherwise
    """
    try:
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        if not file_path.exists() or not file_path.is_file():
            return False

        # Check for known binary extensions
        binary_extensions = {
            ".exe",
            ".dll",
            ".so",
            ".dylib",
            ".bin",
            ".obj",
            ".o",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".ico",
            ".mp3",
            ".mp4",
            ".avi",
            ".mov",
            ".wav",
            ".pdf",
        }

        if file_path.suffix.lower() in binary_extensions:
            return False

        # Sample file content
        with open(file_path, "rb") as f:
            sample = f.read(sample_size)

        if not sample:
            return True  # Empty files are considered text

        # Check for binary indicators
        for indicator in BINARY_INDICATORS:
            if indicator in sample:
                return False

        # Check ratio of printable characters
        printable_count = sum(1 for byte in sample if 32 <= byte <= 126 or byte in (9, 10, 13))
        printable_ratio = printable_count / len(sample)

        return printable_ratio >= 0.7  # At least 70% printable characters

    except (OSError, IOError, ValueError):
        return False  # Assume binary if we can't determine
