"""
Protocol definitions and type annotations for the metrics module

This module provides protocol definitions for better type safety and
TypedDict definitions for structured return types.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, TypedDict


class MetricsCollectorProtocol(Protocol):
    """Protocol for metrics collectors"""

    def collect_metrics(self, content: str, file_path: Path) -> Dict[str, Any]:
        pass


class CommentCounterProtocol(Protocol):
    """Protocol for comment counters"""

    def count_comments(self, lines: List[str], file_extension: str) -> int:
        pass


class CoverageEstimatorProtocol(Protocol):
    """Protocol for coverage estimators"""

    def estimate_test_coverage(self, file_path: Path, content: str) -> float:
        pass


class ComplexityCalculatorProtocol(Protocol):
    """Protocol for complexity calculators"""

    def calculate_complexity(self, content: str) -> int:
        pass


# TypedDict definitions for structured metrics
class BasicMetrics(TypedDict):
    """Basic file metrics"""

    lines_of_code: int
    blank_lines: int
    comment_lines: int
    file_size_bytes: int
    average_line_length: float
    max_line_length: int
    comment_ratio: float
    blank_line_ratio: float
    code_density: float


class PythonMetrics(TypedDict):
    """Python-specific metrics"""

    functions: int
    async_functions: int
    classes: int
    methods: int
    imports: int
    decorators: int
    comprehensions: int
    lambdas: int
    try_blocks: int
    with_statements: int


class ComplexityMetrics(TypedDict):
    """Complexity metrics"""

    cyclomatic_complexity: int
    max_function_complexity: int
    average_function_complexity: float
    cognitive_complexity: int
    combined_complexity_score: float


class HalsteadMetrics(TypedDict):
    """Halstead complexity metrics"""

    halstead_length: int
    halstead_vocabulary: int
    halstead_volume: float
    halstead_difficulty: float
    halstead_effort: float


class QualityMetrics(TypedDict):
    """Quality assessment metrics"""

    maintainability_index: float
    maintainability_rating: str
    technical_debt_ratio: float
    technical_debt_rating: str
    test_coverage: float
    test_coverage_impact: str
    duplication_percentage: float
    duplication_impact: str
    overall_quality_score: float
    overall_quality_rating: str


class ComprehensiveMetrics(TypedDict):
    """Complete metrics combining all aspects"""

    basic: BasicMetrics
    python: Optional[PythonMetrics]
    complexity: ComplexityMetrics
    halstead: Optional[HalsteadMetrics]
    quality: QualityMetrics
