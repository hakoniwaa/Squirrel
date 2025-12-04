"""
Metrics calculation module for code analysis

This module provides comprehensive code metrics calculation including:
- Cyclomatic and cognitive complexity
- Code quality metrics and scores
- Test coverage analysis
- Halstead complexity metrics
- Python construct analysis
- Comment processing
"""

# Specialized processors (for advanced usage)
# Main collectors and calculators
from .collectors import (
    CommentProcessor,
    CoverageEstimator,
    HalsteadCalculator,
    MetricsCollector,
    PythonConstructCounter,
)
from .complexity import ComplexityCalculator, CyclomaticComplexityCalculator

# Exceptions
from .exceptions import CoverageDataError, MetricsError, ParseError

# Type definitions and protocols
from .protocols import (
    BasicMetrics,
    HalsteadMetrics,
    MetricsCollectorProtocol,
    PythonMetrics,
    QualityMetrics,
)
from .quality import QualityMetricsCalculator

__all__ = [
    # Main classes
    "MetricsCollector",
    "ComplexityCalculator",
    "CyclomaticComplexityCalculator",
    "QualityMetricsCalculator",
    # Specialized processors
    "CommentProcessor",
    "CoverageEstimator",
    "PythonConstructCounter",
    "HalsteadCalculator",
    # Protocols and types
    "MetricsCollectorProtocol",
    "BasicMetrics",
    "PythonMetrics",
    "HalsteadMetrics",
    "QualityMetrics",
    # Exceptions
    "MetricsError",
    "ParseError",
    "CoverageDataError",
]

# Version info
__version__ = "2.0.0"  # Major version bump due to breaking changes
