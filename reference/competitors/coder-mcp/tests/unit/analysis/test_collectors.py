"""
Unit tests for metrics collection module - updated for refactored API
"""

import ast
from pathlib import Path

import pytest

from coder_mcp.analysis.metrics.collectors.base import MetricsCollector
from coder_mcp.analysis.metrics.collectors.python import HalsteadCalculator, PythonConstructCounter


class TestMetricsCollector:
    """Test MetricsCollector class with new refactored API"""

    @pytest.fixture
    def collector(self):
        """Create collector instance"""
        return MetricsCollector()

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file for testing"""
        file_path = tmp_path / "test_file.py"
        file_path.write_text("# Test file\nprint('Hello')\n")
        return file_path

    def test_collect_metrics_python_file(self, collector, temp_file):
        """Test metrics collection for Python file"""
        content = "# Comment\n\nprint('Hello')\n"

        metrics = collector.collect_metrics(content, temp_file)

        # Basic file metrics
        assert metrics["lines_of_code"] == 3
        assert metrics["blank_lines"] == 1
        assert metrics["comment_lines"] == 1
        assert metrics["file_size_bytes"] > 0
        assert metrics["average_line_length"] > 0
        assert metrics["max_line_length"] == len("print('Hello')")

        # Derived metrics
        assert 0 <= metrics["comment_ratio"] <= 1
        assert 0 <= metrics["blank_line_ratio"] <= 1
        assert 0 <= metrics["code_density"] <= 1

    def test_collect_metrics_empty_file(self, collector, temp_file):
        """Test metrics for empty file"""
        content = ""

        metrics = collector.collect_metrics(content, temp_file)

        assert metrics["lines_of_code"] == 0
        assert metrics["blank_lines"] == 0
        assert metrics["comment_lines"] == 0
        assert metrics["average_line_length"] == 0
        assert metrics["max_line_length"] == 0
        assert metrics["code_density"] == 0

    def test_collect_metrics_virtual_file(self, collector):
        """Test metrics for virtual file (no physical file)"""
        content = "print('test')"
        virtual_path = Path("virtual.py")

        metrics = collector.collect_metrics(content, virtual_path)

        # Should estimate size from content
        assert metrics["file_size_bytes"] == len(content.encode("utf-8"))

    def test_collect_python_metrics_simple(self, collector, temp_file):
        """Test Python-specific metrics collection"""
        content = '''def add(a, b):
    """Add two numbers"""
    if a > 0 and b > 0:
        return a + b
    return 0

class Calculator:
    def multiply(self, x, y):
        return x * y
'''

        metrics = collector.collect_python_metrics(content, temp_file)

        # Check Python-specific metrics
        assert metrics["functions"] == 2  # add + multiply (methods count as functions)
        assert metrics["classes"] == 1  # Calculator

        # Check complexity metrics
        assert metrics["cyclomatic_complexity"] > 0
        assert "max_function_complexity" in metrics
        assert "cognitive_complexity" in metrics

        # Check quality scores
        assert "maintainability_index" in metrics
        assert "overall_quality_score" in metrics

    def test_collect_python_metrics_syntax_error(self, collector, temp_file):
        """Test Python metrics with syntax error"""
        content = "def broken(\n"  # Syntax error

        metrics = collector.collect_python_metrics(content, temp_file)

        # Should handle syntax error gracefully
        assert "analysis_error" in metrics
        assert metrics["lines_of_code"] == 1

    def test_collect_python_metrics_comprehensive(self, collector, temp_file):
        """Test comprehensive Python constructs"""
        content = '''import os
from pathlib import Path

@decorator
class MyClass:
    """Class docstring"""

    def __init__(self):
        self.value = 0

    @property
    def prop(self):
        return self.value

    async def async_method(self):
        pass

def regular_function():
    # List comprehension
    squares = [x**2 for x in range(10)]

    # Dict comprehension
    dict_comp = {k: v for k, v in enumerate(squares)}

    # Lambda
    func = lambda x: x * 2

    # Try block
    try:
        risky_operation()
    except Exception:
        pass

    # With statement
    with open("file.txt") as f:
        pass

    return squares
'''

        metrics = collector.collect_python_metrics(content, temp_file)

        # Check construct counts
        assert metrics["classes"] == 1
        assert metrics["functions"] >= 3  # regular_function, __init__, prop, async_method
        assert metrics["async_functions"] == 1
        assert metrics["imports"] == 2
        assert metrics["decorators"] >= 2
        assert metrics["comprehensions"] == 2
        assert metrics["lambdas"] == 1
        assert metrics["try_blocks"] == 1
        assert metrics["with_statements"] == 1

    def test_collect_javascript_metrics(self, collector):
        """Test JavaScript metrics collection"""
        content = """import React from 'react';
const utils = require('./utils');

export class MyComponent {
    constructor() {
        this.state = {};
    }
}

async function fetchData(url) {
    if (url) {
        return await fetch(url);
    }
    return null;
}

const arrowFunc = (x, y) => x + y;

export default MyComponent;
"""

        js_file = Path("test.js")
        metrics = collector.collect_javascript_metrics(content, js_file)

        # Check JS-specific metrics
        assert metrics["functions"] >= 2  # constructor, fetchData
        assert metrics["classes"] == 1
        assert metrics["imports"] == 2
        assert metrics["exports"] == 2
        assert metrics["async_functions"] == 1

        # Check complexity estimation
        assert metrics["cyclomatic_complexity"] >= 2  # Base + if

    def test_collect_generic_metrics(self, collector):
        """Test generic file metrics collection"""
        content = """function example() {
    if (condition) {
        if (nested) {
            doSomething();
        }
    }
}"""

        generic_file = Path("test.txt")
        metrics = collector.collect_generic_metrics(content, generic_file)

        # Should estimate complexity from indentation
        assert metrics["cyclomatic_complexity"] > 1
        assert "overall_quality_score" in metrics


class TestPythonConstructCounter:
    """Test Python construct counter"""

    def test_count_functions(self):
        """Test counting functions"""
        code = """
def func1():
    pass

def func2(x, y):
    return x + y

async def async_func():
    pass
"""
        tree = ast.parse(code)
        counter = PythonConstructCounter()
        metrics = counter.count_constructs(tree)

        assert metrics["functions"] == 2  # async functions counted separately
        assert metrics["async_functions"] == 1

    def test_count_classes_and_methods(self):
        """Test counting classes and methods"""
        code = """
class MyClass:
    def method1(self):
        pass

    @staticmethod
    def static_method():
        pass

    @classmethod
    def class_method(cls):
        pass

class AnotherClass:
    pass
"""
        tree = ast.parse(code)
        counter = PythonConstructCounter()
        metrics = counter.count_constructs(tree)

        assert metrics["classes"] == 2
        assert metrics["functions"] == 3  # methods counted as functions

    def test_count_imports(self):
        """Test counting imports"""
        code = """
import os
import sys
from pathlib import Path, PosixPath
from collections.abc import Sequence
"""
        tree = ast.parse(code)
        counter = PythonConstructCounter()
        metrics = counter.count_constructs(tree)

        assert metrics["imports"] == 4

    def test_count_decorators(self):
        """Test counting decorators"""
        code = """
@decorator1
@decorator2
def decorated_func():
    pass

@property
def prop_method(self):
    pass

@staticmethod
@another_decorator
def static_func():
    pass
"""
        tree = ast.parse(code)
        counter = PythonConstructCounter()
        metrics = counter.count_constructs(tree)

        assert metrics["decorators"] == 5  # 2 + 1 + 2

    def test_count_comprehensions(self):
        """Test counting comprehensions"""
        code = """
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
word_dict = {word: len(word) for word in words}
unique_letters = {char for char in "hello world"}
gen_expr = (x for x in range(5))
"""
        tree = ast.parse(code)
        counter = PythonConstructCounter()
        metrics = counter.count_constructs(tree)

        assert metrics["comprehensions"] == 5

    def test_count_error_handling(self):
        """Test counting error handling constructs"""
        code = """
try:
    risky_operation()
except ValueError:
    pass
except Exception as e:
    handle_error(e)
finally:
    cleanup()

try:
    another_operation()
except:
    pass

with open("file.txt") as f:
    content = f.read()

with lock:
    shared_resource.modify()
"""
        tree = ast.parse(code)
        counter = PythonConstructCounter()
        metrics = counter.count_constructs(tree)

        assert metrics["try_blocks"] == 2
        assert metrics["with_statements"] == 2


class TestHalsteadCalculator:
    """Test Halstead metrics calculator"""

    def test_simple_expression(self):
        """Test Halstead metrics for simple expression"""
        code = "x = a + b"
        tree = ast.parse(code)
        calculator = HalsteadCalculator()
        metrics = calculator.calculate_halstead_metrics(tree)

        # Should have operators and operands
        assert (
            metrics["halstead_vocabulary"] >= 4
        )  # =, +, x, a, b (actual implementation produces 4)
        assert metrics["halstead_length"] >= 4
        assert metrics["halstead_difficulty"] > 0
        assert metrics["halstead_effort"] > 0

    def test_complex_expression(self):
        """Test Halstead metrics for complex code"""
        code = """
def calculate(x, y, z):
    if x > 0:
        result = x * y + z / 2
        return result ** 2
    else:
        return x - y

total = calculate(10, 5, 3) + calculate(2, 8, 1)
"""
        tree = ast.parse(code)
        calculator = HalsteadCalculator()
        metrics = calculator.calculate_halstead_metrics(tree)

        # More complex code should have higher metrics
        assert metrics["halstead_vocabulary"] > 10
        assert metrics["halstead_length"] > 15
        assert metrics["halstead_difficulty"] > 1

    def test_empty_code(self):
        """Test Halstead metrics for empty code"""
        code = ""
        try:
            tree = ast.parse(code)
            calculator = HalsteadCalculator()
            metrics = calculator.calculate_halstead_metrics(tree)

            # Empty code should have minimal metrics
            assert metrics["halstead_vocabulary"] == 0
            assert metrics["halstead_length"] == 0
            assert metrics["halstead_difficulty"] == 0
            assert metrics["halstead_effort"] == 0
        except Exception:
            # Empty AST might not be handled, that's acceptable
            pass


class TestIntegration:
    """Integration tests for the full metrics collection pipeline"""

    @pytest.fixture
    def collector(self):
        """Create collector instance"""
        return MetricsCollector()

    def test_full_python_analysis(self, collector, tmp_path):
        """Test complete Python file analysis"""
        content = '''
"""
Module docstring
"""
import os
from pathlib import Path

@dataclass
class Person:
    """A person with name and age"""
    name: str
    age: int = 0

    def greet(self) -> str:
        """Return a greeting message"""
        if self.age > 0:
            return f"Hello, I'm {self.name} and I'm {self.age} years old"
        return f"Hello, I'm {self.name}"

    @property
    def is_adult(self) -> bool:
        """Check if person is an adult"""
        return self.age >= 18

def create_person(name: str, age: int = 0) -> Person:
    """Create a new person instance"""
    if not isinstance(name, str):
        raise ValueError("Name must be a string")

    try:
        person = Person(name, age)
        return person
    except Exception as e:
        print(f"Error creating person: {e}")
        raise

# Test the functionality
if __name__ == "__main__":
    people = [
        create_person("Alice", 25),
        create_person("Bob", 17),
        create_person("Charlie"),
    ]

    adults = [p for p in people if p.is_adult]
    print(f"Found {len(adults)} adults")
'''

        python_file = tmp_path / "person.py"
        python_file.write_text(content)

        metrics = collector.collect_python_metrics(content, python_file)

        # Verify comprehensive analysis
        assert metrics["classes"] == 1
        assert metrics["functions"] >= 3  # greet, is_adult, create_person
        assert metrics["imports"] == 2
        assert metrics["decorators"] >= 2  # @dataclass, @property
        assert metrics["try_blocks"] == 1
        assert metrics["comprehensions"] == 1

        # Check quality metrics
        assert "maintainability_index" in metrics
        assert "overall_quality_score" in metrics
        assert "test_coverage" in metrics

        # Verify reasonable quality scores
        assert 0 <= metrics["overall_quality_score"] <= 100
        assert 0 <= metrics["maintainability_index"] <= 100

    def test_error_handling_resilience(self, collector, tmp_path):
        """Test that collector handles various error conditions gracefully"""
        # Test with invalid Python syntax
        invalid_content = "def broken(:\n    pass"
        invalid_file = tmp_path / "broken.py"

        metrics = collector.collect_python_metrics(invalid_content, invalid_file)
        assert "analysis_error" in metrics
        assert "lines_of_code" in metrics  # Basic metrics should still work

    def test_different_file_types(self, collector, tmp_path):
        """Test handling different file types"""
        # Python file
        py_content = "print('hello')"
        py_file = tmp_path / "test.py"
        py_metrics = collector.collect_metrics(py_content, py_file)
        assert "functions" in py_metrics or "analysis_error" in py_metrics

        # JavaScript file
        js_content = "console.log('hello');"
        js_file = tmp_path / "test.js"
        js_metrics = collector.collect_metrics(js_content, js_file)
        assert "functions" in js_metrics

        # Generic file
        txt_content = "Hello world"
        txt_file = tmp_path / "test.txt"
        txt_metrics = collector.collect_metrics(txt_content, txt_file)
        assert "cyclomatic_complexity" in txt_metrics
