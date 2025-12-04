"""
Base classes and interfaces for code analysis detectors.

This module provides the foundational architecture for all code analysis detectors,
including pattern-based, rule-based, and statistical detectors. It emphasizes
clean abstractions, proper error handling, and extensibility.

Classes:
    BaseDetector: Abstract base class for all detectors
    BasePatternDetector: Pattern-based detection implementation
    BaseRuleDetector: Rule-based detection implementation
    BaseStatisticalDetector: Statistical analysis implementation
    DetectionContext: Context container for detection operations
    DetectionUtils: Utility functions for common detection tasks

Exceptions:
    DetectorError: Base exception for detector errors
    PatternNotFoundError: Pattern configuration missing
    InvalidContextError: Invalid detection context
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, TypedDict, Union


# Type definitions for better type safety
class IssueDict(TypedDict):
    """Type definition for issue dictionaries."""

    type: str
    severity: str
    file: str
    line: int
    description: str
    suggestion: str


class PatternDict(TypedDict, total=False):
    """Type definition for pattern dictionaries."""

    pattern_name: str
    pattern_type: str
    file: str
    start_line: int
    end_line: int
    confidence: float
    description: str
    suggestion: str
    severity: str


class SecurityIssueDict(TypedDict, total=False):
    """Type definition for security issue dictionaries."""

    type: str
    severity: str
    file: str
    line: int
    description: str
    suggestion: str
    cwe_id: Optional[str]
    owasp_category: Optional[str]
    code_snippet: str


# Constants
DEFAULT_CONFIDENCE_THRESHOLD = 0.4
MAX_CODE_SNIPPET_LINES = 5
DEFAULT_CONTEXT_LINES = 2

# Severity levels
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

# Confidence thresholds
CONFIDENCE_HIGH = 0.8
CONFIDENCE_MEDIUM = 0.6
CONFIDENCE_LOW = 0.4


# Custom exceptions
class DetectorError(Exception):
    """Base exception for detector errors."""

    def __init__(
        self, message: str, detector_name: Optional[str] = None, cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.detector_name = detector_name
        self.cause = cause


class PatternNotFoundError(DetectorError):
    """Raised when pattern configuration is missing."""


class InvalidContextError(DetectorError):
    """Raised when detection context is invalid."""


@dataclass
class DetectionContext:
    """Context container for detection operations.

    This class encapsulates all the information needed for detection operations,
    providing a clean interface and validation.

    Attributes:
        content: File content to analyze
        lines: Content split into lines
        file_path: Path to the file being analyzed
    """

    content: str
    file_path: Path
    lines: Optional[List[str]] = None

    def __post_init__(self) -> None:
        """Initialize derived attributes after construction."""
        if self.lines is None:
            self.lines = self.content.splitlines()

        # Validate content
        if not isinstance(self.content, str):
            raise InvalidContextError("Content must be a string")
        if not isinstance(self.file_path, Path):
            raise InvalidContextError("File path must be a Path object")

    @property
    def relative_path(self) -> str:
        """Get relative path string for reporting."""
        try:
            return str(self.file_path.relative_to(Path.cwd()))
        except ValueError:
            return str(self.file_path)

    @property
    def line_count(self) -> int:
        """Get total number of lines."""
        return len(self.lines) if self.lines else 0

    def get_line(self, line_number: int) -> str:
        """Get specific line by number (1-indexed).

        Args:
            line_number: Line number (1-indexed)

        Returns:
            Line content or empty string if invalid
        """
        if not self.lines or line_number < 1 or line_number > len(self.lines):
            return ""
        return self.lines[line_number - 1]

    def get_lines_around(
        self, line_number: int, context_lines: int = DEFAULT_CONTEXT_LINES
    ) -> List[str]:
        """Get lines around a specific line number.

        Args:
            line_number: Center line number (1-indexed)
            context_lines: Number of context lines on each side

        Returns:
            List of lines including context
        """
        if not self.lines:
            return []

        start = max(0, line_number - context_lines - 1)
        end = min(len(self.lines), line_number + context_lines)

        return self.lines[start:end]


@dataclass
class PatternConfig:
    """Configuration for pattern detection.

    This class encapsulates pattern detection configuration with validation.
    """

    indicators: List[str]
    description: str
    suggestion: str
    severity: str = SEVERITY_MEDIUM
    line_threshold: Optional[int] = None
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD

    def __post_init__(self) -> None:
        """Validate configuration after construction."""
        if not self.indicators:
            raise PatternNotFoundError("Indicators list cannot be empty")
        if not self.description:
            raise PatternNotFoundError("Description is required")
        if not self.suggestion:
            raise PatternNotFoundError("Suggestion is required")
        if self.severity not in [SEVERITY_LOW, SEVERITY_MEDIUM, SEVERITY_HIGH, SEVERITY_CRITICAL]:
            raise PatternNotFoundError(f"Invalid severity: {self.severity}")
        if not 0 <= self.confidence_threshold <= 1:
            raise PatternNotFoundError(
                f"Confidence threshold must be 0-1: {self.confidence_threshold}"
            )


class DetectionStrategy(Protocol):
    """Protocol for detection strategies."""

    def detect(self, context: DetectionContext) -> List[Dict[str, Any]]:
        """Detect issues in the given context."""
        ...


class BaseDetector(ABC):
    """Abstract base class for all detectors.

    This class provides the common interface and functionality for all detector
    implementations, with proper error handling and logging.
    """

    def __init__(self) -> None:
        """Initialize the detector."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._patterns: Dict[str, Any] = {}
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """Initialize patterns safely with error handling."""
        try:
            self._patterns = self._load_patterns()
        except Exception as e:
            self.logger.error(f"Failed to load patterns for {self.__class__.__name__}: {e}")
            self._patterns = {}

    @abstractmethod
    def _load_patterns(self) -> Dict[str, Any]:
        """Load detection patterns/rules.

        Returns:
            Dictionary of patterns/rules
        """

    @abstractmethod
    def detect(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect issues in the given content.

        Args:
            content: File content to analyze
            file_path: Path to the file

        Returns:
            List of detected issues
        """

    def create_context(self, content: str, file_path: Path) -> DetectionContext:
        """Create detection context with validation.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            Validated detection context

        Raises:
            InvalidContextError: If context is invalid
        """
        try:
            return DetectionContext(content=content, file_path=file_path)
        except Exception as e:
            raise InvalidContextError(f"Failed to create detection context: {e}") from e

    def validate_context(self, context: DetectionContext) -> None:
        """Validate detection context.

        Args:
            context: Context to validate

        Raises:
            InvalidContextError: If context is invalid
        """
        if not context.content or not context.content.strip():
            raise InvalidContextError("Content is empty or invalid")

        if not context.file_path:
            raise InvalidContextError("File path is required")

        if not context.file_path.exists():
            self.logger.warning(f"File does not exist: {context.file_path}")


class BasePatternDetector(BaseDetector):
    """Base class for pattern-based detectors.

    This class implements pattern matching logic with confidence scoring
    and proper error handling.
    """

    def __init__(self) -> None:
        """Initialize pattern detector."""
        super().__init__()
        self._confidence_thresholds = {
            "high": CONFIDENCE_HIGH,
            "medium": CONFIDENCE_MEDIUM,
            "low": CONFIDENCE_LOW,
        }

    def detect(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect patterns in content.

        Args:
            content: File content to analyze
            file_path: Path to the file

        Returns:
            List of detected pattern matches
        """
        try:
            context = self.create_context(content, file_path)
            self.validate_context(context)

            return self._detect_patterns(context)

        except Exception as e:
            self.logger.error(f"Pattern detection failed for {file_path}: {e}")
            return []

    def _detect_patterns(self, context: DetectionContext) -> List[Dict[str, Any]]:
        """Detect all patterns in the context.

        Args:
            context: Detection context

        Returns:
            List of pattern matches
        """
        results = []

        for pattern_name, pattern_config in self._patterns.items():
            try:
                matches = self._find_pattern_matches(context, pattern_name, pattern_config)
                results.extend(matches)
            except Exception as e:
                self.logger.warning(f"Error detecting pattern {pattern_name}: {e}")
                continue

        return results

    def _find_pattern_matches(
        self, context: DetectionContext, pattern_name: str, pattern_config: PatternConfig
    ) -> List[Dict[str, Any]]:
        """Find matches for a specific pattern.

        Args:
            context: Detection context
            pattern_name: Name of the pattern
            pattern_config: Pattern configuration

        Returns:
            List of pattern matches
        """
        matches = []

        for indicator in pattern_config.indicators:
            try:
                pattern_matches = self._search_pattern(context.content, indicator)

                for match in pattern_matches:
                    confidence = self._calculate_confidence(match, pattern_config)

                    if confidence >= pattern_config.confidence_threshold:
                        issue = self._create_issue_from_match(
                            context, pattern_name, pattern_config, match, confidence
                        )
                        matches.append(issue)

            except re.error as e:
                self.logger.warning(f"Invalid regex pattern '{indicator}': {e}")
                continue
            except Exception as e:
                self.logger.warning(f"Error searching pattern '{indicator}': {e}")
                continue

        return matches

    def _search_pattern(self, content: str, pattern: str) -> List[re.Match]:
        """Search for pattern in content safely.

        Args:
            content: Content to search
            pattern: Regex pattern

        Returns:
            List of regex matches
        """
        try:
            return list(re.finditer(pattern, content, re.MULTILINE))
        except re.error:
            # If regex fails, try as literal string
            escaped_pattern = re.escape(pattern)
            return list(re.finditer(escaped_pattern, content, re.MULTILINE))

    def _calculate_confidence(self, match: re.Match, pattern_config: PatternConfig) -> float:
        """Calculate confidence for a pattern match.

        Args:
            match: Regex match object
            pattern_config: Pattern configuration

        Returns:
            Confidence score (0.0-1.0)
        """
        # Base implementation - can be enhanced in subclasses
        return self._confidence_thresholds["medium"]

    @abstractmethod
    def _create_issue_from_match(
        self,
        context: DetectionContext,
        pattern_name: str,
        pattern_config: PatternConfig,
        match: re.Match,
        confidence: float,
    ) -> Dict[str, Any]:
        """Create issue dictionary from pattern match.

        Args:
            context: Detection context
            pattern_name: Name of the matched pattern
            pattern_config: Pattern configuration
            match: Regex match object
            confidence: Confidence score

        Returns:
            Issue dictionary
        """


class BaseRuleDetector(BaseDetector):
    """Base class for rule-based detectors.

    This class implements rule-based detection with proper error handling
    and rule management.
    """

    def __init__(self) -> None:
        """Initialize rule detector."""
        super().__init__()
        self._rules: Dict[str, Any] = {}
        self._initialize_rules()

    def _initialize_rules(self) -> None:
        """Initialize rules safely."""
        try:
            self._rules = self._load_rules()
        except Exception as e:
            self.logger.error(f"Failed to load rules for {self.__class__.__name__}: {e}")
            self._rules = {}

    @abstractmethod
    def _load_rules(self) -> Dict[str, Any]:
        """Load detection rules.

        Returns:
            Dictionary of rules
        """

    def detect(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect rule violations in content.

        Args:
            content: File content to analyze
            file_path: Path to the file

        Returns:
            List of rule violations
        """
        try:
            context = self.create_context(content, file_path)
            self.validate_context(context)

            return self._check_all_rules(context)

        except Exception as e:
            self.logger.error(f"Rule detection failed for {file_path}: {e}")
            return []

    def _check_all_rules(self, context: DetectionContext) -> List[Dict[str, Any]]:
        """Check all rules against the context.

        Args:
            context: Detection context

        Returns:
            List of rule violations
        """
        results = []

        for rule_name, rule_config in self._rules.items():
            try:
                violations = self._check_rule(context, rule_name, rule_config)
                results.extend(violations)
            except Exception as e:
                self.logger.warning(f"Error checking rule {rule_name}: {e}")
                continue

        return results

    @abstractmethod
    def _check_rule(
        self, context: DetectionContext, rule_name: str, rule_config: Any
    ) -> List[Dict[str, Any]]:
        """Check rule against context.

        Args:
            context: Detection context
            rule_name: Name of the rule
            rule_config: Rule configuration

        Returns:
            List of rule violations
        """


class BaseStatisticalDetector(BaseDetector):
    """Base class for statistical analysis detectors.

    This class implements statistical analysis patterns with proper
    threshold management and metric calculation.
    """

    def __init__(self) -> None:
        """Initialize statistical detector."""
        super().__init__()
        self._thresholds: Dict[str, Union[int, float]] = {}
        self._initialize_thresholds()

    def _initialize_thresholds(self) -> None:
        """Initialize thresholds safely."""
        try:
            self._thresholds = self._get_thresholds()
        except Exception as e:
            self.logger.error(f"Failed to load thresholds for {self.__class__.__name__}: {e}")
            self._thresholds = {}

    @abstractmethod
    def _get_thresholds(self) -> Dict[str, Union[int, float]]:
        """Get statistical thresholds.

        Returns:
            Dictionary of thresholds
        """

    def detect(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Detect statistical anomalies in content.

        Args:
            content: File content to analyze
            file_path: Path to the file

        Returns:
            List of statistical issues
        """
        try:
            context = self.create_context(content, file_path)
            self.validate_context(context)

            metrics = self._calculate_metrics(context)
            return self._analyze_metrics(context, metrics)

        except Exception as e:
            self.logger.error(f"Statistical detection failed for {file_path}: {e}")
            return []

    @abstractmethod
    def _calculate_metrics(self, context: DetectionContext) -> Dict[str, Union[int, float]]:
        """Calculate metrics for the content.

        Args:
            context: Detection context

        Returns:
            Dictionary of calculated metrics
        """

    @abstractmethod
    def _analyze_metrics(
        self, context: DetectionContext, metrics: Dict[str, Union[int, float]]
    ) -> List[Dict[str, Any]]:
        """Analyze metrics and return issues.

        Args:
            context: Detection context
            metrics: Calculated metrics

        Returns:
            List of statistical issues
        """


class DetectionUtils:
    """Utility functions for detection operations.

    This class provides common utility functions used across different
    detector implementations.
    """

    @staticmethod
    def get_line_number_from_match(content: str, match: re.Match) -> int:
        """Get line number from regex match.

        Args:
            content: Original content
            match: Regex match object

        Returns:
            1-indexed line number
        """
        if not match:
            return 1
        return content[: match.start()].count("\n") + 1

    @staticmethod
    def get_code_snippet(
        lines: List[str], line_number: int, context_lines: int = DEFAULT_CONTEXT_LINES
    ) -> str:
        """Get code snippet around line number.

        Args:
            lines: List of file lines
            line_number: Target line number (1-indexed)
            context_lines: Number of context lines to include

        Returns:
            Code snippet as string
        """
        if not lines or line_number < 1:
            return ""

        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)

        snippet_lines = lines[start:end]
        return "\n".join(snippet_lines)

    @staticmethod
    def is_comment_line(line: str) -> bool:
        """Check if line is a comment.

        Args:
            line: Line to check

        Returns:
            True if line is a comment
        """
        stripped = line.strip()
        if not stripped:
            return False

        comment_prefixes = ["#", "//", "/*", "*", '"""', "'''"]
        return any(stripped.startswith(prefix) for prefix in comment_prefixes)

    @staticmethod
    def normalize_code(code: str) -> str:
        """Normalize code for comparison.

        Args:
            code: Code to normalize

        Returns:
            Normalized code string
        """
        lines = code.splitlines()
        normalized_lines = []

        for line in lines:
            normalized = line.strip()
            if normalized and not DetectionUtils.is_comment_line(normalized):
                # Normalize whitespace
                normalized = " ".join(normalized.split())
                normalized_lines.append(normalized)

        return "\n".join(normalized_lines)

    @staticmethod
    def calculate_indentation_level(line: str, indent_size: int = 4) -> int:
        """Calculate indentation level of a line.

        Args:
            line: Line to analyze
            indent_size: Size of one indentation level

        Returns:
            Indentation level
        """
        if not line or not line.strip():
            return 0
        return (len(line) - len(line.lstrip())) // indent_size

    @staticmethod
    def extract_function_lines(lines: List[str], start_idx: int) -> List[str]:
        """Extract lines belonging to a function.

        Args:
            lines: All file lines
            start_idx: Starting line index (0-indexed)

        Returns:
            Lines belonging to the function
        """
        return DetectionUtils._extract_block_lines(lines, start_idx, "function")

    @staticmethod
    def extract_class_lines(lines: List[str], start_idx: int) -> List[str]:
        """Extract lines belonging to a class.

        Args:
            lines: All file lines
            start_idx: Starting line index (0-indexed)

        Returns:
            Lines belonging to the class
        """
        return DetectionUtils._extract_block_lines(lines, start_idx, "class")

    @staticmethod
    def _extract_block_lines(lines: List[str], start_idx: int, block_type: str) -> List[str]:
        """Extract lines belonging to a code block.

        Args:
            lines: All file lines
            start_idx: Starting line index (0-indexed)
            block_type: Type of block (for logging)

        Returns:
            Lines belonging to the block
        """
        if not lines or start_idx >= len(lines) or start_idx < 0:
            return []

        block_lines = []
        base_indent = None

        for i in range(start_idx, len(lines)):
            line = lines[i]

            # Always include empty lines
            if not line.strip():
                block_lines.append(line)
                continue

            current_indent = len(line) - len(line.lstrip())

            # Set base indentation from first non-empty line
            if base_indent is None:
                base_indent = current_indent
                block_lines.append(line)
                continue

            # If we encounter a line with less or equal indentation that's not a comment,
            # we've reached the end of the block
            if current_indent <= base_indent and not DetectionUtils.is_comment_line(line.strip()):
                break

            block_lines.append(line)

        return block_lines
