"""
Exception classes for the metrics module

This module defines specific exceptions for different types of errors
that can occur during metrics calculation.
"""

from typing import Optional


class MetricsError(Exception):
    """Base exception for metrics module"""


class ParseError(MetricsError):
    """Raised when code parsing fails"""

    def __init__(
        self, message: str, file_path: Optional[str] = None, line_number: Optional[int] = None
    ):
        super().__init__(message)
        self.file_path = file_path
        self.line_number = line_number


class CoverageDataError(MetricsError):
    """Raised when coverage data is invalid or cannot be processed"""

    def __init__(self, message: str, coverage_file: Optional[str] = None):
        super().__init__(message)
        self.coverage_file = coverage_file


class ComplexityCalculationError(MetricsError):
    """Raised when complexity calculation fails"""


class MetricsCalculationError(MetricsError):
    """Raised when general metrics calculation fails"""

    def __init__(self, message: str, metric_type: Optional[str] = None):
        super().__init__(message)
        self.metric_type = metric_type
