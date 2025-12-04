"""
Base metrics collector with refactored design

This module provides the main MetricsCollector class with improved error handling,
reduced complexity, and better separation of concerns.
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..complexity import calculate_complexity_metrics
from ..exceptions import MetricsCalculationError, ParseError
from ..protocols import BasicMetrics, MetricsCollectorProtocol
from ..quality import QualityMetricsCalculator
from .comment import CommentProcessor
from .coverage import CoverageEstimator
from .python import HalsteadCalculator, PythonConstructCounter
from .utils import add_derived_ratios

logger = logging.getLogger(__name__)


class FileConfiguration:
    """Configuration constants for file processing"""

    # Default encoding for file operations
    DEFAULT_ENCODING = "utf-8"

    # File extension mappings
    PYTHON_EXTENSIONS = (".py",)
    JS_EXTENSIONS = (".js", ".ts", ".jsx", ".tsx")

    # JavaScript complexity patterns for estimation
    JS_DECISION_PATTERNS = [
        r"\bif\s*\(",  # if statements
        r"\belse\s+if\b",  # else if
        r"\bwhile\s*\(",  # while loops
        r"\bfor\s*\(",  # for loops
        r"\bswitch\s*\(",  # switch statements
        r"\bcase\s+",  # case statements
        r"\bcatch\s*\(",  # catch blocks
        r"\?\s*.*\s*:",  # ternary operators
        r"\&\&",  # logical AND
        r"\|\|",  # logical OR
    ]

    # Base complexity constants
    BASE_COMPLEXITY = 1
    INDENT_DIVISOR = 2
    MAX_INDENT_DIVISOR = 4


class FileMetricsCalculator:
    """Handles basic file metrics calculation"""

    def __init__(self, comment_processor: CommentProcessor):
        self.comment_processor = comment_processor

    def calculate_basic_metrics(self, content: str, file_path: Path) -> BasicMetrics:
        """Calculate basic file metrics"""
        lines = content.splitlines()

        # Get file size safely
        file_size = self._get_file_size(content, file_path)

        # Calculate basic metrics
        metrics = BasicMetrics(
            {
                "lines_of_code": len(lines),
                "blank_lines": self._count_blank_lines(lines),
                "comment_lines": self.comment_processor.count_comment_lines(
                    lines, file_path.suffix
                ),
                "file_size_bytes": file_size,
                "average_line_length": self._calculate_average_line_length(lines),
                "max_line_length": max(len(line) for line in lines) if lines else 0,
                "comment_ratio": 0.0,
                "blank_line_ratio": 0.0,
                "code_density": 0.0,
            }
        )

        # Calculate derived ratios
        add_derived_ratios(dict(metrics))

        return metrics

    def _get_file_size(self, content: str, file_path: Path) -> int:
        """Get file size safely, handling virtual files"""
        try:
            return file_path.stat().st_size
        except (FileNotFoundError, OSError):
            # For test files or virtual files, estimate size from content
            return len(content.encode(FileConfiguration.DEFAULT_ENCODING))

    def _count_blank_lines(self, lines: List[str]) -> int:
        """Count blank lines in the file"""
        return sum(1 for line in lines if not line.strip())

    def _calculate_average_line_length(self, lines: List[str]) -> float:
        """Calculate average line length"""
        if not lines:
            return 0.0
        return sum(len(line) for line in lines) / len(lines)


class PythonAnalyzer:
    """Handles Python-specific analysis"""

    def __init__(self):
        self.construct_counter = PythonConstructCounter()
        self.halstead_calculator = HalsteadCalculator()

    def analyze_python_code(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze Python code and return comprehensive metrics"""
        try:
            tree = self._parse_python_ast(content, file_path)
            if tree is None:
                return {}

            metrics: Dict[str, Any] = {}
            self._collect_ast_metrics(tree, metrics)
            return metrics

        except SyntaxError as e:
            logger.warning("Syntax error in %s: %s", file_path, e)
            raise ParseError(f"Syntax error: {e}", str(file_path), e.lineno) from e
        except Exception as e:  # Defensive: catch all exceptions to ensure analysis doesn't crash
            logger.error("Error analyzing Python code in %s: %s", file_path, e)
            return {"analysis_error": str(e)}

    def _parse_python_ast(self, content: str, file_path: Path) -> Optional[ast.AST]:
        """Parse Python code to AST with proper error handling"""
        try:
            return ast.parse(content)
        except SyntaxError as e:
            logger.warning("Syntax error in %s: %s", file_path, e)
            raise ParseError(f"Syntax error: {e}", str(file_path), e.lineno) from e
        except Exception as e:  # Defensive: catch all exceptions to ensure parsing doesn't crash
            logger.error("Failed to parse %s: %s", file_path, e)
            raise ParseError(f"Parse error: {e}", str(file_path)) from e

    def _collect_ast_metrics(self, tree: ast.AST, metrics: Dict[str, Any]) -> None:
        """Collect metrics from AST analysis"""
        # Add Python construct counts
        python_metrics = self.construct_counter.count_constructs(tree)
        metrics.update(python_metrics)

        # Add complexity metrics
        complexity_metrics = calculate_complexity_metrics(tree)
        self._add_complexity_metrics(complexity_metrics, metrics)

        # Add Halstead metrics
        halstead_metrics = self.halstead_calculator.calculate_halstead_metrics(tree)
        metrics.update(halstead_metrics)

    def _add_complexity_metrics(
        self, complexity_metrics: Dict[str, Any], metrics: Dict[str, Any]
    ) -> None:
        """Add complexity metrics to the main metrics dictionary"""
        cyclomatic = complexity_metrics["cyclomatic"]
        cognitive = complexity_metrics["cognitive"]

        metrics.update(
            {
                "cyclomatic_complexity": cyclomatic["total_complexity"],
                "max_function_complexity": cyclomatic["max_function_complexity"],
                "average_function_complexity": cyclomatic["average_complexity"],
                "cognitive_complexity": cognitive["total_cognitive_complexity"],
                "combined_complexity_score": complexity_metrics["combined_score"],
            }
        )


class JavaScriptAnalyzer:
    """Handles JavaScript/TypeScript analysis using regex patterns"""

    def analyze_javascript_code(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript code using pattern matching"""
        js_metrics = self._count_javascript_constructs(content)
        js_metrics["cyclomatic_complexity"] = self._estimate_js_complexity(content)
        return js_metrics

    def _count_javascript_constructs(self, content: str) -> Dict[str, Any]:
        """Count JavaScript constructs using regex patterns"""
        patterns = {
            "functions": [
                r"function\s+\w+",
                r"const\s+\w+\s*=\s*function",
                r"let\s+\w+\s*=\s*function",
                r"var\s+\w+\s*=\s*function",
                r"const\s+\w+\s*=\s*\([^)]*\)\s*=>",
                r"let\s+\w+\s*=\s*\([^)]*\)\s*=>",
                r"var\s+\w+\s*=\s*\([^)]*\)\s*=>",
            ],
            "classes": [r"class\s+\w+"],
            "imports": [r"import\s+", r"require\s*\("],
            "exports": [r"export\s+", r"module\.exports"],
            "async_functions": [r"async\s+function", r"async\s+\([^)]*\)\s*=>"],
        }

        counts = {}
        for construct, pattern_list in patterns.items():
            count = 0
            for pattern in pattern_list:
                count += len(re.findall(pattern, content))
            counts[construct] = count

        return counts

    def _estimate_js_complexity(self, content: str) -> int:
        """Estimate cyclomatic complexity for JavaScript using regex patterns"""
        complexity = FileConfiguration.BASE_COMPLEXITY

        for pattern in FileConfiguration.JS_DECISION_PATTERNS:
            matches = re.findall(pattern, content)
            complexity += len(matches)

        return complexity


class GenericAnalyzer:
    """Handles analysis for generic file types"""

    def estimate_generic_complexity(self, content: str) -> int:
        """Estimate complexity for generic files based on indentation structure"""
        lines = content.splitlines()

        if not lines:
            return FileConfiguration.BASE_COMPLEXITY

        # Calculate indentation metrics
        indent_levels = self._calculate_indent_levels(lines)

        if not indent_levels:
            return FileConfiguration.BASE_COMPLEXITY

        avg_indent = sum(indent_levels) / len(indent_levels)
        max_indent = max(indent_levels)

        # Estimate complexity based on indentation patterns
        estimated_complexity = FileConfiguration.BASE_COMPLEXITY + int(
            avg_indent / FileConfiguration.INDENT_DIVISOR
            + max_indent / FileConfiguration.MAX_INDENT_DIVISOR
        )

        return max(FileConfiguration.BASE_COMPLEXITY, estimated_complexity)

    def _calculate_indent_levels(self, lines: List[str]) -> List[int]:
        """Calculate indentation levels for non-empty lines"""
        indent_levels = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                indent_levels.append(indent)
        return indent_levels


class MetricsCollector(MetricsCollectorProtocol):
    """Main metrics collection coordinator with improved design"""

    quality_calculator: QualityMetricsCalculator
    comment_processor: CommentProcessor
    coverage_estimator: CoverageEstimator
    file_calculator: FileMetricsCalculator
    python_analyzer: PythonAnalyzer
    js_analyzer: JavaScriptAnalyzer
    generic_analyzer: GenericAnalyzer

    def __init__(self) -> None:
        # Initialize specialized processors
        self.quality_calculator = QualityMetricsCalculator()
        self.comment_processor = CommentProcessor()
        self.coverage_estimator = CoverageEstimator()

        # Initialize analyzers
        self.file_calculator = FileMetricsCalculator(self.comment_processor)
        self.python_analyzer = PythonAnalyzer()
        self.js_analyzer = JavaScriptAnalyzer()
        self.generic_analyzer = GenericAnalyzer()

    def collect_metrics(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Collect appropriate metrics based on file type"""
        try:
            if file_path.suffix in FileConfiguration.PYTHON_EXTENSIONS:
                return self.collect_python_metrics(content, file_path)
            elif file_path.suffix in FileConfiguration.JS_EXTENSIONS:
                return self.collect_javascript_metrics(content, file_path)
            else:
                return self.collect_generic_metrics(content, file_path)
        except Exception as e:
            logger.error(
                "Error collecting metrics for %s: %s",
                file_path,
                e,
            )
            raise MetricsCalculationError(f"Failed to collect metrics: {e}") from e

    def collect_python_metrics(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Collect Python-specific metrics with improved error handling"""
        # Start with basic metrics
        metrics = dict(self.file_calculator.calculate_basic_metrics(content, file_path))

        # Add Python-specific analysis
        python_metrics = self.python_analyzer.analyze_python_code(content, file_path)
        metrics.update(python_metrics)

        # Add coverage and quality metrics
        self._add_coverage_and_quality(metrics, file_path, content)

        return metrics

    def collect_javascript_metrics(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Collect JavaScript-specific metrics"""
        # Start with basic metrics
        metrics = dict(self.file_calculator.calculate_basic_metrics(content, file_path))

        # Add JavaScript-specific analysis
        js_metrics = self.js_analyzer.analyze_javascript_code(content)
        metrics.update(js_metrics)

        # Add coverage and quality metrics
        self._add_coverage_and_quality(metrics, file_path, content)

        return metrics

    def collect_generic_metrics(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Collect generic metrics for any file type"""
        # Start with basic metrics
        metrics = dict(self.file_calculator.calculate_basic_metrics(content, file_path))

        # Estimate complexity based on structure
        metrics["cyclomatic_complexity"] = self.generic_analyzer.estimate_generic_complexity(
            content
        )

        # Add coverage and quality metrics
        self._add_coverage_and_quality(metrics, file_path, content)

        return metrics

    def _add_coverage_and_quality(
        self, metrics: Dict[str, Any], file_path: Path, content: str
    ) -> None:
        """Add coverage estimation and quality metrics"""
        try:
            # Estimate test coverage if not provided
            if "test_coverage" not in metrics:
                metrics["test_coverage"] = self.coverage_estimator.estimate_test_coverage(
                    file_path, content
                )

            # Calculate quality scores
            quality_scores = self.quality_calculator.calculate_quality_score(metrics)
            metrics.update(quality_scores)

        except Exception as e:
            logger.warning(
                "Error calculating coverage/quality for %s: %s",
                file_path,
                e,
            )
            # Set default values to prevent downstream errors
            metrics.setdefault("test_coverage", 0.0)
