"""
Analysis result container and data model.

This module provides a robust data container for analysis results with validation,
error handling, and consistent data structure management.

Classes:
    AnalysisResult: Comprehensive data container for analysis results
    AnalysisResultError: Custom exception for result-related errors
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .quality_scoring import QualityScoreCalculator

# Constants
DEFAULT_QUALITY_SCORE = 0
MIN_QUALITY_SCORE = 0
MAX_QUALITY_SCORE = 10
HIGH_QUALITY_THRESHOLD = 8.0


class AnalysisResultError(Exception):
    """Custom exception for analysis result errors."""

    def __init__(self, message: str, result_file: Optional[str] = None):
        super().__init__(message)
        self.result_file = result_file


class AnalysisResult:
    """Comprehensive data container for analysis results.

    This class provides a structured way to store and manage analysis results
    with validation, error handling, and consistent data access patterns.

    Attributes:
        relative_path: Relative path to the analyzed file
        issues: List of detected issues
        suggestions: List of improvement suggestions
        metrics: Dictionary of collected metrics
        quality_score: Numerical quality score (0-10)
        timestamp: ISO timestamp of analysis
    """

    def __init__(self, file_path: Union[str, Path], workspace_root: Union[str, Path]) -> None:
        """Initialize analysis result container.

        Args:
            file_path: Path to the analyzed file
            workspace_root: Root directory of the workspace

        Raises:
            AnalysisResultError: If paths are invalid
        """
        try:
            file_path = Path(file_path)
            workspace_root = Path(workspace_root)

            # Calculate relative path safely
            try:
                self.relative_path = str(file_path.relative_to(workspace_root))
            except ValueError:
                # File is outside workspace, use absolute path
                self.relative_path = str(file_path.resolve())

        except (OSError, ValueError) as e:
            raise AnalysisResultError(f"Invalid file path configuration: {e}") from e

        # Initialize collections
        self._issues: List[str] = []
        self._suggestions: List[str] = []
        self._metrics: Dict[str, Any] = {}
        self._quality_score: float = DEFAULT_QUALITY_SCORE
        self._timestamp: str = datetime.now().isoformat()

    @property
    def issues(self) -> List[str]:
        """Get list of issues (read-only)."""
        return self._issues.copy()

    @property
    def suggestions(self) -> List[str]:
        """Get list of suggestions (read-only)."""
        return self._suggestions.copy()

    @property
    def metrics(self) -> Dict[str, Any]:
        """Get metrics dictionary (read-only)."""
        return self._metrics.copy()

    @property
    def quality_score(self) -> float:
        """Get quality score (read-only)."""
        return self._quality_score

    @property
    def timestamp(self) -> str:
        """Get timestamp (read-only)."""
        return self._timestamp

    def add_issue(self, issue: str) -> None:
        """Add an issue to the result.

        Args:
            issue: Description of the issue

        Raises:
            AnalysisResultError: If issue is invalid
        """
        if not isinstance(issue, str):
            raise AnalysisResultError(f"Issue must be a string, got {type(issue)}")

        issue = issue.strip()
        if not issue:
            return  # Skip empty issues

        if issue not in self._issues:  # Avoid duplicates
            self._issues.append(issue)

    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion to the result.

        Args:
            suggestion: Improvement suggestion

        Raises:
            AnalysisResultError: If suggestion is invalid
        """
        if not isinstance(suggestion, str):
            raise AnalysisResultError(f"Suggestion must be a string, got {type(suggestion)}")

        suggestion = suggestion.strip()
        if not suggestion:
            return  # Skip empty suggestions

        if suggestion not in self._suggestions:  # Avoid duplicates
            self._suggestions.append(suggestion)

    def add_multiple_issues(self, issues: List[str]) -> None:
        """Add multiple issues at once.

        Args:
            issues: List of issue descriptions

        Raises:
            AnalysisResultError: If issues list is invalid
        """
        if not isinstance(issues, list):
            raise AnalysisResultError(f"Issues must be a list, got {type(issues)}")

        for issue in issues:
            self.add_issue(issue)

    def add_multiple_suggestions(self, suggestions: List[str]) -> None:
        """Add multiple suggestions at once.

        Args:
            suggestions: List of improvement suggestions

        Raises:
            AnalysisResultError: If suggestions list is invalid
        """
        if not isinstance(suggestions, list):
            raise AnalysisResultError(f"Suggestions must be a list, got {type(suggestions)}")

        for suggestion in suggestions:
            self.add_suggestion(suggestion)

    def set_metrics(self, metrics: Dict[str, Any]) -> None:
        """Set metrics dictionary.

        Args:
            metrics: Dictionary of metrics data

        Raises:
            AnalysisResultError: If metrics is invalid
        """
        if not isinstance(metrics, dict):
            raise AnalysisResultError(f"Metrics must be a dictionary, got {type(metrics)}")

        # Validate metric values
        for key, value in metrics.items():
            if not isinstance(key, str):
                raise AnalysisResultError(f"Metric key must be string, got {type(key)}")
            if not self._is_valid_metric_value(value):
                raise AnalysisResultError(f"Invalid metric value for '{key}': {value}")

        self._metrics = metrics.copy()

    def update_metrics(self, additional_metrics: Dict[str, Any]) -> None:
        """Update metrics with additional data.

        Args:
            additional_metrics: Additional metrics to merge

        Raises:
            AnalysisResultError: If additional_metrics is invalid
        """
        if not isinstance(additional_metrics, dict):
            raise AnalysisResultError(
                f"Additional metrics must be a dictionary, got {type(additional_metrics)}"
            )

        for key, value in additional_metrics.items():
            if not isinstance(key, str):
                raise AnalysisResultError(f"Metric key must be string, got {type(key)}")
            if not self._is_valid_metric_value(value):
                raise AnalysisResultError(f"Invalid metric value for '{key}': {value}")

        self._metrics.update(additional_metrics)

    def calculate_quality_score(self) -> None:
        """Calculate and set the quality score based on metrics and issues."""
        # Try comprehensive metrics first
        if self._metrics:
            score = QualityScoreCalculator.calculate_from_comprehensive_metrics(self._metrics)
            if score is not None:
                self._quality_score = self._clamp_score(score)
                return

        # Fallback to issue-based scoring
        score = QualityScoreCalculator.calculate_from_issues(len(self._issues))
        self._quality_score = self._clamp_score(score)

    def set_quality_score(self, score: Union[int, float]) -> None:
        """Manually set quality score.

        Args:
            score: Quality score (0-10)

        Raises:
            AnalysisResultError: If score is invalid
        """
        if not isinstance(score, (int, float)):
            raise AnalysisResultError(f"Quality score must be numeric, got {type(score)}")

        self._quality_score = self._clamp_score(score)

    def clear_issues(self) -> None:
        """Clear all issues."""
        self._issues.clear()

    def clear_suggestions(self) -> None:
        """Clear all suggestions."""
        self._suggestions.clear()

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self._metrics.clear()

    def reset(self) -> None:
        """Reset all data to initial state."""
        self.clear_issues()
        self.clear_suggestions()
        self.clear_metrics()
        self._quality_score = DEFAULT_QUALITY_SCORE
        self._timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary containing all result data
        """
        return {
            "file": self.relative_path,
            "quality_score": self._quality_score,
            "issues": self._issues.copy(),
            "suggestions": self._suggestions.copy(),
            "metrics": self._metrics.copy(),
            "timestamp": self._timestamp,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary with key information only.

        Returns:
            Dictionary containing summary information
        """
        return {
            "file": self.relative_path,
            "quality_score": self._quality_score,
            "issue_count": len(self._issues),
            "suggestion_count": len(self._suggestions),
            "timestamp": self._timestamp,
        }

    def has_issues(self) -> bool:
        """Check if result has any issues.

        Returns:
            True if there are issues, False otherwise
        """
        return len(self._issues) > 0

    def has_suggestions(self) -> bool:
        """Check if result has any suggestions.

        Returns:
            True if there are suggestions, False otherwise
        """
        return len(self._suggestions) > 0

    def has_metrics(self) -> bool:
        """Check if result has any metrics.

        Returns:
            True if there are metrics, False otherwise
        """
        return len(self._metrics) > 0

    def is_high_quality(self, threshold: float = HIGH_QUALITY_THRESHOLD) -> bool:
        """Check if result indicates high quality code.

        Args:
            threshold: Quality score threshold (default: 8.0)

        Returns:
            True if quality score is above threshold
        """
        return self._quality_score >= threshold

    def _is_valid_metric_value(self, value: Any) -> bool:
        """Check if a value is valid for metrics.

        Args:
            value: Value to validate

        Returns:
            True if value is valid
        """
        return isinstance(value, (int, float, str, bool, list, dict)) or value is None

    def _clamp_score(self, score: Union[int, float]) -> float:
        """Clamp score to valid range.

        Args:
            score: Score to clamp

        Returns:
            Clamped score
        """
        return max(MIN_QUALITY_SCORE, min(MAX_QUALITY_SCORE, float(score)))

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"AnalysisResult(file='{self.relative_path}', "
            f"score={self._quality_score}, "
            f"issues={len(self._issues)})"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Analysis of {self.relative_path}: {self._quality_score}/10 "
            f"(issues: {len(self._issues)})"
        )
