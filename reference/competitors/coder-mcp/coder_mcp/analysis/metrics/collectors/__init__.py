"""
Metrics collectors package

This package provides specialized collectors for different aspects of code metrics:
- Comment processing and counting
- Test coverage estimation
- Python-specific construct analysis
- Base metrics collection functionality
"""

from .base import MetricsCollector
from .comment import BlockCommentState, CommentProcessor, DocstringState
from .coverage import CoverageEstimator, CoverageScorer, FilePathMatcher
from .python import HalsteadCalculator, PythonConstructCounter

__all__ = [
    "MetricsCollector",
    "CommentProcessor",
    "DocstringState",
    "BlockCommentState",
    "CoverageEstimator",
    "CoverageScorer",
    "FilePathMatcher",
    "PythonConstructCounter",
    "HalsteadCalculator",
]
