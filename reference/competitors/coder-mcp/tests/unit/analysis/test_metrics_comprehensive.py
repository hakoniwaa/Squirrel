"""Comprehensive tests for metrics module."""

import ast
from unittest.mock import Mock

import pytest

from coder_mcp.analysis.metrics.complexity import (
    CognitiveComplexityCalculator,
    ComplexityConstants,
    CyclomaticComplexityCalculator,
    calculate_complexity_metrics,
)
from coder_mcp.analysis.metrics.factory import MetricsCollectorBuilder, MetricsCollectorFactory


class TestMetricsCollectorFactory:
    """Test MetricsCollectorFactory class."""

    def test_create_for_file_python(self, tmp_path):
        """Test creating collector for Python file."""
        python_file = tmp_path / "test.py"
        python_file.write_text("print('hello')")

        collector = MetricsCollectorFactory.create_for_file(python_file)

        assert collector is not None

    def test_create_python_collector(self):
        """Test creating Python-specific collector."""
        collector = MetricsCollectorFactory.create_python_collector()

        assert collector is not None

    def test_get_file_type_python(self, tmp_path):
        """Test file type detection for Python."""
        python_file = tmp_path / "test.py"
        file_type = MetricsCollectorFactory.get_file_type(python_file)
        assert file_type == "python"

    def test_get_file_type_javascript(self, tmp_path):
        """Test file type detection for JavaScript."""
        js_file = tmp_path / "test.js"
        file_type = MetricsCollectorFactory.get_file_type(js_file)
        assert file_type == "javascript"

    def test_get_file_type_generic(self, tmp_path):
        """Test file type detection for generic."""
        generic_file = tmp_path / "test.txt"
        file_type = MetricsCollectorFactory.get_file_type(generic_file)
        assert file_type == "generic"


class TestMetricsCollectorBuilder:
    """Test MetricsCollectorBuilder class."""

    @pytest.fixture
    def builder(self):
        """Create MetricsCollectorBuilder instance."""
        return MetricsCollectorBuilder()

    def test_initialization(self, builder):
        """Test builder initialization."""
        assert builder._custom_quality_calculator is None
        assert builder._custom_comment_processor is None
        assert builder._custom_coverage_estimator is None

    def test_with_quality_calculator(self, builder):
        """Test setting custom quality calculator."""
        mock_calculator = Mock()

        result = builder.with_quality_calculator(mock_calculator)

        assert result is builder  # Fluent interface
        assert builder._custom_quality_calculator is mock_calculator

    def test_build_default(self, builder):
        """Test building with default configuration."""
        collector = builder.build()

        assert collector is not None


class TestCyclomaticComplexityCalculator:
    """Test CyclomaticComplexityCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create CyclomaticComplexityCalculator instance."""
        return CyclomaticComplexityCalculator()

    def test_initialization(self, calculator):
        """Test calculator initialization."""
        assert calculator.complexity == 0
        assert calculator.current_complexity == 0
        assert calculator.max_complexity == 0
        assert calculator.function_complexities == {}
        assert calculator.current_function is None

    def test_simple_function_complexity(self, calculator):
        """Test complexity calculation for simple function."""
        code = """
def simple_function(x):
    return x * 2
"""
        tree = ast.parse(code)
        result = calculator.calculate(tree)

        assert result["total_complexity"] == 1  # Base complexity
        assert result["max_function_complexity"] == 1
        assert "simple_function" in result["function_complexities"]
        assert result["function_complexities"]["simple_function"] == 1
        assert result["average_complexity"] == 1.0

    def test_empty_code(self, calculator):
        """Test complexity calculation for empty code."""
        code = ""
        tree = ast.parse(code)
        result = calculator.calculate(tree)

        assert result["total_complexity"] == 0
        assert result["max_function_complexity"] == 0
        assert result["function_complexities"] == {}
        assert result["average_complexity"] == 0.0


class TestCognitiveComplexityCalculator:
    """Test CognitiveComplexityCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create CognitiveComplexityCalculator instance."""
        return CognitiveComplexityCalculator()

    def test_initialization(self, calculator):
        """Test calculator initialization."""
        assert calculator.cognitive_complexity == 0
        assert calculator.nesting_level == 0
        assert calculator.current_function is None
        assert calculator.function_complexities == {}

    def test_simple_function_cognitive_complexity(self, calculator):
        """Test cognitive complexity for simple function."""
        code = """
def simple_function(x):
    return x * 2
"""
        tree = ast.parse(code)
        result = calculator.calculate(tree)

        assert result["total_cognitive_complexity"] == 0  # No control structures
        assert result["function_complexities"]["simple_function"] == 0
        assert result["average_cognitive_complexity"] == 0.0


class TestComplexityConstants:
    """Test ComplexityConstants class."""

    def test_constants_defined(self):
        """Test that all required constants are defined."""
        assert hasattr(ComplexityConstants, "BASE_FUNCTION_COMPLEXITY")
        assert hasattr(ComplexityConstants, "BOOLEAN_OPERATION_WEIGHT")
        assert hasattr(ComplexityConstants, "NESTING_LEVEL_INCREMENT")
        assert hasattr(ComplexityConstants, "BASE_CONTROL_STRUCTURE_COMPLEXITY")
        assert hasattr(ComplexityConstants, "CYCLOMATIC_WEIGHT")
        assert hasattr(ComplexityConstants, "COGNITIVE_WEIGHT")

    def test_constants_values(self):
        """Test constant values are reasonable."""
        assert ComplexityConstants.BASE_FUNCTION_COMPLEXITY == 1
        assert ComplexityConstants.BOOLEAN_OPERATION_WEIGHT == 1
        assert ComplexityConstants.NESTING_LEVEL_INCREMENT == 1
        assert ComplexityConstants.BASE_CONTROL_STRUCTURE_COMPLEXITY == 1
        assert ComplexityConstants.CYCLOMATIC_WEIGHT == 0.5
        assert ComplexityConstants.COGNITIVE_WEIGHT == 0.5


class TestCalculateComplexityMetrics:
    """Test calculate_complexity_metrics function."""

    def test_simple_function_metrics(self):
        """Test complexity metrics for simple function."""
        code = """
def simple_function(x):
    return x * 2
"""
        tree = ast.parse(code)
        result = calculate_complexity_metrics(tree)

        assert "cyclomatic" in result
        assert "cognitive" in result
        assert "combined_score" in result

        assert result["cyclomatic"]["total_complexity"] == 1
        assert result["cognitive"]["total_cognitive_complexity"] == 0
        assert result["combined_score"] == 0.5  # 1 * 0.5 + 0 * 0.5

    def test_empty_code_metrics(self):
        """Test complexity metrics for empty code."""
        code = ""
        tree = ast.parse(code)
        result = calculate_complexity_metrics(tree)

        assert result["cyclomatic"]["total_complexity"] == 0
        assert result["cognitive"]["total_cognitive_complexity"] == 0
        assert result["combined_score"] == 0.0
