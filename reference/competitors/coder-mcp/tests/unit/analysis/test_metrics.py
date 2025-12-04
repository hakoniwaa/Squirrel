"""Test metrics calculation modules."""

import os
import tempfile
from pathlib import Path

from coder_mcp.analysis.metrics.collectors.base import MetricsCollector
from coder_mcp.analysis.metrics.collectors.comment import CommentProcessor
from coder_mcp.analysis.metrics.collectors.coverage import CoverageEstimator
from coder_mcp.analysis.metrics.collectors.python import HalsteadCalculator, PythonConstructCounter


class TestMetricsCollector:
    """Test the main MetricsCollector"""

    def setup_method(self):
        """Set up test fixtures"""
        self.collector = MetricsCollector()
        self.test_file = Path("test_file.py")

    def test_init(self):
        """Test collector initialization"""
        assert self.collector.quality_calculator is not None
        assert self.collector.comment_processor is not None
        assert self.collector.coverage_estimator is not None
        assert self.collector.file_calculator is not None
        assert self.collector.python_analyzer is not None
        assert self.collector.js_analyzer is not None
        assert self.collector.generic_analyzer is not None

    def test_collect_python_metrics_simple(self):
        """Test Python metrics collection with simple code"""
        content = """
def test_function():
    '''A simple test function'''
    x = 1
    y = 2
    return x + y
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            test_file = Path(f.name)

        try:
            metrics = self.collector.collect_python_metrics(content, test_file)

            assert isinstance(metrics, dict)
            assert "lines_of_code" in metrics
            assert "functions" in metrics
            assert "cyclomatic_complexity" in metrics
            assert metrics["lines_of_code"] > 0
        finally:
            os.unlink(test_file)

    def test_collect_javascript_metrics(self):
        """Test JavaScript metrics collection"""
        content = """
function testFunction() {
    let x = 1;
    let y = 2;
    return x + y;
}

const arrowFunction = () => {
    console.log("Hello");
};
"""

        test_file = Path("test_file.js")
        metrics = self.collector.collect_javascript_metrics(content, test_file)

        assert isinstance(metrics, dict)
        assert "lines_of_code" in metrics
        assert "functions" in metrics
        assert "cyclomatic_complexity" in metrics

    def test_collect_generic_metrics(self):
        """Test generic metrics collection"""
        content = """
Some generic file content
with multiple lines
    and some indentation
        and deeper indentation
"""

        test_file = Path("test_file.txt")
        metrics = self.collector.collect_generic_metrics(content, test_file)

        assert isinstance(metrics, dict)
        assert "lines_of_code" in metrics
        assert "blank_lines" in metrics
        assert "cyclomatic_complexity" in metrics

    def test_collect_metrics_python_file(self):
        """Test metrics collection for Python file"""
        content = "def test(): pass"
        test_file = Path("test.py")

        metrics = self.collector.collect_metrics(content, test_file)
        assert isinstance(metrics, dict)
        assert "functions" in metrics

    def test_collect_metrics_javascript_file(self):
        """Test metrics collection for JavaScript file"""
        content = "function test() { return 1; }"
        test_file = Path("test.js")

        metrics = self.collector.collect_metrics(content, test_file)
        assert isinstance(metrics, dict)

    def test_collect_metrics_generic_file(self):
        """Test metrics collection for generic file"""
        content = "Some content"
        test_file = Path("test.txt")

        metrics = self.collector.collect_metrics(content, test_file)
        assert isinstance(metrics, dict)

    def test_collect_metrics_error_handling(self):
        """Test error handling in metrics collection"""
        # Test with content that might cause issues
        content = "invalid content that might break parsing"
        test_file = Path("test.py")

        # Should handle errors gracefully
        metrics = self.collector.collect_metrics(content, test_file)
        assert isinstance(metrics, dict)

    def test_python_syntax_error_handling(self):
        """Test handling of Python syntax errors"""
        content = """
def incomplete_function(
    # Missing closing parenthesis and body
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            test_file = Path(f.name)

        try:
            metrics = self.collector.collect_python_metrics(content, test_file)

            # Should handle syntax error gracefully
            assert isinstance(metrics, dict)
            assert "analysis_error" in metrics or "syntax_error" in metrics
        finally:
            os.unlink(test_file)

    def test_virtual_file_handling(self):
        """Test handling of virtual/non-existent files"""
        content = "def test(): pass"
        test_file = Path("/virtual/test.py")  # Non-existent path

        metrics = self.collector.collect_python_metrics(content, test_file)
        assert isinstance(metrics, dict)
        assert "file_size_bytes" in metrics


class TestCommentProcessor:
    """Test the CommentProcessor"""

    def setup_method(self):
        """Set up test fixtures"""
        self.processor = CommentProcessor()

    def test_count_python_comments(self):
        """Test Python comment counting"""
        lines = [
            "def test():",
            "    '''Docstring'''",
            "    # Single line comment",
            "    x = 1  # Inline comment",
            "    '''",
            "    Multi-line",
            "    string",
            "    '''",
            "    return x",
        ]

        count = self.processor.count_comment_lines(lines, ".py")
        assert count > 0

    def test_count_javascript_comments(self):
        """Test JavaScript comment counting"""
        lines = [
            "function test() {",
            "    // Single line comment",
            "    let x = 1; // Inline comment",
            "    /*",
            "    Multi-line",
            "    comment",
            "    */",
            "    return x;",
            "}",
        ]

        count = self.processor.count_comment_lines(lines, ".js")
        assert count > 0

    def test_count_generic_comments(self):
        """Test generic comment counting"""
        lines = ["Some content", "# This looks like a comment", "// This too", "Regular content"]

        count = self.processor.count_comment_lines(lines, ".txt")
        assert count >= 0


class TestCoverageEstimator:
    """Test the CoverageEstimator"""

    def setup_method(self):
        """Set up test fixtures"""
        self.estimator = CoverageEstimator()

    def test_estimate_test_coverage_test_file(self):
        """Test coverage estimation for test files"""
        test_file = Path("test_something.py")
        content = """
def test_function():
    assert True

def test_another():
    assert False
"""

        coverage = self.estimator.estimate_test_coverage(test_file, content)
        assert isinstance(coverage, (int, float))
        assert 0 <= coverage <= 100

    def test_estimate_test_coverage_regular_file(self):
        """Test coverage estimation for regular files"""
        regular_file = Path("module.py")
        content = """
def function():
    return True

def another_function():
    return False
"""

        coverage = self.estimator.estimate_test_coverage(regular_file, content)
        assert isinstance(coverage, (int, float))
        assert 0 <= coverage <= 100


class TestPythonConstructCounter:
    """Test the PythonConstructCounter"""

    def setup_method(self):
        """Set up test fixtures"""
        self.counter = PythonConstructCounter()

    def test_count_functions(self):
        """Test function counting"""
        content = """
def function1():
    pass

def function2():
    def nested_function():
        pass
    return nested_function

async def async_function():
    pass
"""

        import ast

        tree = ast.parse(content)
        metrics = self.counter.count_constructs(tree)

        assert "functions" in metrics
        assert metrics["functions"] >= 2  # At least function1 and function2

    def test_count_classes(self):
        """Test class counting"""
        content = """
class Class1:
    pass

class Class2:
    class NestedClass:
        pass
"""

        import ast

        tree = ast.parse(content)
        metrics = self.counter.count_constructs(tree)

        assert "classes" in metrics
        assert metrics["classes"] >= 2

    def test_count_imports(self):
        """Test import counting"""
        content = """
import os
import sys
from pathlib import Path
from collections import defaultdict, Counter
"""

        import ast

        tree = ast.parse(content)
        metrics = self.counter.count_constructs(tree)

        assert "imports" in metrics
        assert metrics["imports"] >= 4


class TestHalsteadCalculator:
    """Test the HalsteadCalculator"""

    def setup_method(self):
        """Set up test fixtures"""
        self.calculator = HalsteadCalculator()

    def test_simple_calculation(self):
        """Test Halstead metrics calculation"""
        content = """
def add(a, b):
    return a + b

result = add(1, 2)
"""

        import ast

        tree = ast.parse(content)
        metrics = self.calculator.calculate_halstead_metrics(tree)

        assert "halstead_vocabulary" in metrics
        assert "halstead_length" in metrics
        assert "halstead_volume" in metrics
        assert "halstead_difficulty" in metrics
        assert "halstead_effort" in metrics

    def test_empty_code(self):
        """Test Halstead metrics with empty code"""
        content = ""

        import ast

        tree = ast.parse(content)
        metrics = self.calculator.calculate_halstead_metrics(tree)

        # Should handle empty code gracefully
        assert isinstance(metrics, dict)


class TestMetricsIntegration:
    """Integration tests for the complete metrics system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.collector = MetricsCollector()

    def test_comprehensive_python_analysis(self):
        """Test comprehensive Python file analysis"""
        content = """
'''
A comprehensive test module
'''

import os
import sys
from pathlib import Path

class Calculator:
    '''A simple calculator class'''

    def __init__(self):
        self.history = []

    def add(self, a, b):
        '''Add two numbers'''
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result

    def multiply(self, a, b):
        '''Multiply two numbers'''
        if a == 0 or b == 0:
            return 0
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

def main():
    '''Main function'''
    calc = Calculator()

    # Some calculations
    x = calc.add(5, 3)
    y = calc.multiply(x, 2)

    print(f"Results: {x}, {y}")
    return x, y

if __name__ == "__main__":
    main()
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()
            test_file = Path(f.name)

        try:
            metrics = self.collector.collect_metrics(content, test_file)

            # Verify comprehensive metrics
            assert isinstance(metrics, dict)

            # Basic metrics
            assert "lines_of_code" in metrics
            assert "blank_lines" in metrics
            assert "comment_lines" in metrics
            assert "file_size_bytes" in metrics

            # Python-specific metrics
            assert "functions" in metrics
            assert "classes" in metrics
            assert "imports" in metrics
            assert "cyclomatic_complexity" in metrics

            # Halstead metrics
            assert "halstead_vocabulary" in metrics
            assert "halstead_length" in metrics

            # Quality metrics
            assert "test_coverage" in metrics

            # Verify reasonable values
            assert metrics["lines_of_code"] > 30  # Reasonable line count
            assert metrics["functions"] >= 1  # At least one function detected
            assert metrics["classes"] >= 1  # Calculator
            assert metrics["imports"] >= 3  # os, sys, pathlib

        finally:
            os.unlink(test_file)

    def test_error_resilience(self):
        """Test that the system is resilient to various error conditions"""
        # Test with problematic content
        problematic_content = [
            "",  # Empty content
            "   \n  \n  ",  # Whitespace only
            "def incomplete(",  # Syntax error
            "🚀" * 1000,  # Unicode content
        ]

        for content in problematic_content:
            test_file = Path("test.py")
            metrics = self.collector.collect_metrics(content, test_file)
            assert isinstance(metrics, dict)

    def test_different_file_types(self):
        """Test metrics collection for different file types"""
        files_and_content = [
            (Path("test.py"), "def test(): pass"),
            (Path("test.js"), "function test() { return 1; }"),
            (Path("test.ts"), "function test(): number { return 1; }"),
            (Path("test.txt"), "Some text content"),
            (Path("test.md"), "# Markdown content"),
            (Path("test"), "File without extension"),
        ]

        for file_path, content in files_and_content:
            metrics = self.collector.collect_metrics(content, file_path)
            assert isinstance(metrics, dict)
            assert "lines_of_code" in metrics
            assert "blank_lines" in metrics

    def test_performance_with_large_files(self):
        """Test performance with larger files"""
        # Generate a large Python file
        functions = []
        for i in range(100):
            functions.append(
                f"""
def function_{i}():
    '''Function number {i}'''
    x = {i}
    y = x * 2
    if x > 50:
        return y + 10
    else:
        return y - 10
"""
            )

        content = "\n".join(functions)
        test_file = Path("large_test.py")

        # Should handle large files without issues
        metrics = self.collector.collect_metrics(content, test_file)
        assert isinstance(metrics, dict)
        assert metrics["functions"] >= 100
        assert metrics["lines_of_code"] > 500
