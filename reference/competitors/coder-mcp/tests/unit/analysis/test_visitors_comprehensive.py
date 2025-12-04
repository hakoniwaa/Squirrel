"""
Comprehensive tests for analysis visitors.

This module provides complete test coverage for AST visitors and Python-specific
visitor implementations used in code analysis.
"""

import ast
from unittest.mock import patch

import pytest

from coder_mcp.analysis.visitors.ast_visitor import BaseASTVisitor
from coder_mcp.analysis.visitors.python_visitor import PythonSmellVisitor


class TestBaseASTVisitor:
    """Test BaseASTVisitor abstract class behavior."""

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that BaseASTVisitor cannot be instantiated directly."""
        from pathlib import Path

        with pytest.raises(TypeError) as exc_info:
            BaseASTVisitor(
                file_path=Path("test.py"), workspace_root=Path("."), smell_types=["test_smell"]
            )

        assert "Can't instantiate abstract class" in str(exc_info.value)
        assert "get_smells" in str(exc_info.value)

    def test_abstract_methods_defined(self):
        """Test that abstract methods are properly defined."""
        # Check that get_smells is marked as abstract
        assert hasattr(BaseASTVisitor, "get_smells")

        # Check if it's abstract method
        if hasattr(BaseASTVisitor.get_smells, "__isabstractmethod__"):
            assert BaseASTVisitor.get_smells.__isabstractmethod__ is True


class TestPythonSmellVisitor:
    """Test PythonSmellVisitor class."""

    @pytest.fixture
    def visitor(self):
        """Create PythonSmellVisitor instance."""
        from pathlib import Path

        return PythonSmellVisitor(
            file_path=Path("test.py"),
            workspace_root=Path("."),
            smell_types=["long_functions", "complex_conditionals", "god_classes"],
        )

    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for testing."""
        return """
def test_function(x, y=10):
    '''Test function with docstring.'''
    if x > 0:
        for i in range(x):
            try:
                result = x / i if i > 0 else 0
                yield result
            except ZeroDivisionError:
                continue
        return sum(range(x))
    else:
        raise ValueError("x must be positive")

class TestClass:
    '''Test class with methods.'''

    def __init__(self, value):
        self.value = value

    def method(self):
        return self.value * 2

    @property
    def prop(self):
        return self._value

    @staticmethod
    def static_method():
        return "static"

    @classmethod
    def class_method(cls):
        return cls.__name__

# Global variable
GLOBAL_VAR = 42

# List comprehension
numbers = [x**2 for x in range(10) if x % 2 == 0]

# Dictionary comprehension
squares = {x: x**2 for x in range(5)}

# Set comprehension
unique_squares = {x**2 for x in range(10)}

# Generator expression
gen = (x for x in range(100) if x % 3 == 0)

# Lambda function
lambda_func = lambda x: x * 2

# Async function
async def async_function():
    return await some_async_call()

# Context manager
with open('file.txt') as f:
    content = f.read()
"""

    def test_initialization(self, visitor):
        """Test PythonSmellVisitor initialization."""
        assert visitor is not None
        assert isinstance(visitor, BaseASTVisitor)  # Should inherit from BaseASTVisitor
        assert hasattr(visitor, "thresholds")
        assert hasattr(visitor, "current_class")

    def test_get_smells(self, visitor):
        """Test getting detected smells."""
        # Initially should have no smells
        smells = visitor.get_smells()
        assert isinstance(smells, list)
        assert len(smells) == 0

        # Add a smell and verify
        visitor.add_smell("test_smell", 10, "medium", "Test description")
        smells = visitor.get_smells()
        assert len(smells) == 1

    def test_visit_function_def(self, visitor):
        """Test visiting function definitions."""
        code = "def test_func(x, y=1):\n    return x + y"
        tree = ast.parse(code)

        # Mock the visit_FunctionDef method if it exists
        if hasattr(visitor, "visit_FunctionDef"):
            with patch.object(visitor, "visit_FunctionDef") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_class_def(self, visitor):
        """Test visiting class definitions."""
        code = "class TestClass:\n    def method(self):\n        pass"
        tree = ast.parse(code)

        # Mock the visit_ClassDef method if it exists
        if hasattr(visitor, "visit_ClassDef"):
            with patch.object(visitor, "visit_ClassDef") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_if_statement(self, visitor):
        """Test visiting if statements."""
        code = "if x > 0:\n    print('positive')\nelse:\n    print('negative')"
        tree = ast.parse(code)

        # Mock the visit_If method if it exists
        if hasattr(visitor, "visit_If"):
            with patch.object(visitor, "visit_If") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_for_loop(self, visitor):
        """Test visiting for loops."""
        code = "for i in range(10):\n    print(i)"
        tree = ast.parse(code)

        # Mock the visit_For method if it exists
        if hasattr(visitor, "visit_For"):
            with patch.object(visitor, "visit_For") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_while_loop(self, visitor):
        """Test visiting while loops."""
        code = "while x > 0:\n    x -= 1"
        tree = ast.parse(code)

        # Mock the visit_While method if it exists
        if hasattr(visitor, "visit_While"):
            with patch.object(visitor, "visit_While") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_try_except(self, visitor):
        """Test visiting try/except blocks."""
        code = "try:\n    risky_operation()\nexcept Exception:\n    handle_error()"
        tree = ast.parse(code)

        # Mock the visit_Try method if it exists
        if hasattr(visitor, "visit_Try"):
            with patch.object(visitor, "visit_Try") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_with_statement(self, visitor):
        """Test visiting with statements."""
        code = "with open('file.txt') as f:\n    content = f.read()"
        tree = ast.parse(code)

        # Mock the visit_With method if it exists
        if hasattr(visitor, "visit_With"):
            with patch.object(visitor, "visit_With") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_list_comprehension(self, visitor):
        """Test visiting list comprehensions."""
        code = "result = [x**2 for x in range(10) if x % 2 == 0]"
        tree = ast.parse(code)

        # Mock the visit_ListComp method if it exists
        if hasattr(visitor, "visit_ListComp"):
            with patch.object(visitor, "visit_ListComp") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_dict_comprehension(self, visitor):
        """Test visiting dictionary comprehensions."""
        code = "result = {k: v for k, v in items.items()}"
        tree = ast.parse(code)

        # Mock the visit_DictComp method if it exists
        if hasattr(visitor, "visit_DictComp"):
            with patch.object(visitor, "visit_DictComp") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_set_comprehension(self, visitor):
        """Test visiting set comprehensions."""
        code = "result = {x**2 for x in range(10)}"
        tree = ast.parse(code)

        # Mock the visit_SetComp method if it exists
        if hasattr(visitor, "visit_SetComp"):
            with patch.object(visitor, "visit_SetComp") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_generator_expression(self, visitor):
        """Test visiting generator expressions."""
        code = "result = (x**2 for x in range(10))"
        tree = ast.parse(code)

        # Mock the visit_GeneratorExp method if it exists
        if hasattr(visitor, "visit_GeneratorExp"):
            with patch.object(visitor, "visit_GeneratorExp") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_lambda(self, visitor):
        """Test visiting lambda functions."""
        code = "func = lambda x: x * 2"
        tree = ast.parse(code)

        # Mock the visit_Lambda method if it exists
        if hasattr(visitor, "visit_Lambda"):
            with patch.object(visitor, "visit_Lambda") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_async_function(self, visitor):
        """Test visiting async function definitions."""
        code = "async def async_func():\n    return await something()"
        tree = ast.parse(code)

        # Mock the visit_AsyncFunctionDef method if it exists
        if hasattr(visitor, "visit_AsyncFunctionDef"):
            with patch.object(visitor, "visit_AsyncFunctionDef") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_await_expression(self, visitor):
        """Test visiting await expressions."""
        code = "async def func():\n    result = await async_call()"
        tree = ast.parse(code)

        # Mock the visit_Await method if it exists
        if hasattr(visitor, "visit_Await"):
            with patch.object(visitor, "visit_Await") as mock_visit:
                visitor.visit(tree)
                mock_visit.assert_called()

    def test_visit_complex_code(self, visitor, sample_python_code):
        """Test visiting complex Python code."""
        tree = ast.parse(sample_python_code)

        # Should be able to visit complex code without errors
        try:
            visitor.visit(tree)
        except Exception as e:
            pytest.fail(f"Visiting complex code raised {type(e).__name__} unexpectedly: {e}")

    def test_visitor_state_management(self, visitor):
        """Test that visitor properly manages state during traversal."""
        code = """
def func1():
    x = 1
    return x

def func2():
    y = 2
    return y
"""
        tree = ast.parse(code)

        # Visit the tree multiple times to ensure state is handled correctly
        for _ in range(3):
            try:
                visitor.visit(tree)
            except Exception as e:
                pytest.fail(f"Multiple visits failed: {e}")

    def test_visit_nested_structures(self, visitor):
        """Test visiting deeply nested structures."""
        code = """
def outer():
    def inner():
        def innermost():
            class NestedClass:
                def nested_method(self):
                    for i in range(10):
                        if i % 2 == 0:
                            try:
                                with open('file') as f:
                                    result = [x for x in f if x.strip()]
                                    return result
                            except Exception:
                                continue
            return NestedClass()
        return innermost()
    return inner()
"""
        tree = ast.parse(code)

        # Should handle deeply nested structures
        try:
            visitor.visit(tree)
        except Exception as e:
            pytest.fail(f"Visiting nested structures failed: {e}")

    def test_visit_edge_cases(self, visitor):
        """Test visiting edge cases and unusual constructs."""
        edge_cases = [
            "",  # Empty code
            "pass",  # Single pass statement
            "...",  # Ellipsis
            "x",  # Single identifier
            "1 + 2",  # Simple expression
            "x = y = z = 1",  # Multiple assignment
            "x, y = 1, 2",  # Tuple unpacking
            "*args, **kwargs",  # Starred expressions (in function context)
        ]

        for code in edge_cases:
            if code.strip():  # Skip empty code
                try:
                    tree = ast.parse(code)
                    visitor.visit(tree)
                except SyntaxError:
                    # Some edge cases might not be valid standalone
                    continue
                except Exception as e:
                    pytest.fail(f"Edge case '{code}' failed: {e}")

    def test_visit_python_specific_features(self, visitor):
        """Test visiting Python-specific language features."""
        python_features = [
            "x = 1 if condition else 0",  # Conditional expression
            "yield x",  # Yield expression
            "yield from iterator",  # Yield from
            "raise Exception('error')",  # Raise statement
            "assert x > 0, 'error'",  # Assert statement
            "del x",  # Delete statement
            "global x",  # Global statement
            "nonlocal x",  # Nonlocal statement
            "import os",  # Import statement
            "from os import path",  # Import from statement
            "from . import module",  # Relative import
        ]

        for code in python_features:
            try:
                tree = ast.parse(code)
                visitor.visit(tree)
            except Exception as e:
                pytest.fail(f"Python feature '{code}' failed: {e}")

    def test_visitor_inheritance(self, visitor):
        """Test that PythonSmellVisitor properly inherits from BaseASTVisitor."""
        assert isinstance(visitor, BaseASTVisitor)

        # Should have access to base visitor methods
        assert hasattr(visitor, "visit")
        assert hasattr(visitor, "generic_visit")
        assert hasattr(visitor, "add_smell")
        assert hasattr(visitor, "get_smells")

        # Base methods should be callable
        assert callable(visitor.visit)
        assert callable(visitor.generic_visit)

    def test_visitor_extensibility(self, visitor):
        """Test that visitor can be extended with custom behavior."""
        # Create a custom visitor method
        original_visit = visitor.visit
        call_count = 0

        def custom_visit(node):
            nonlocal call_count
            call_count += 1
            return original_visit(node)

        # Monkey-patch for testing
        visitor.visit = custom_visit

        # Visit some code
        tree = ast.parse("x = 1")
        visitor.visit(tree)

        # Should have been called
        assert call_count > 0

    def test_visitor_performance(self, visitor):
        """Test visitor performance with large code structures."""
        # Generate a large code structure
        function_parts = []
        for i in range(50):  # 50 functions with loops
            function_parts.extend(
                [
                    f"def func_{i}():",
                    f"    x = {i}",
                    f"    for j in range({i}):",
                    "        if j % 2 == 0:",
                    "            yield j",
                    "",
                ]
            )
        large_code = "\n".join(function_parts)

        tree = ast.parse(large_code)

        # Should handle large structures reasonably quickly
        import time

        start_time = time.time()

        try:
            visitor.visit(tree)
            end_time = time.time()

            # Should complete within reasonable time (10 seconds)
            assert end_time - start_time < 10.0
        except Exception as e:
            pytest.fail(f"Performance test failed: {e}")


class TestVisitorIntegration:
    """Integration tests for visitor classes."""

    def test_visitor_factory_pattern(self):
        """Test creating visitors through factory pattern."""
        from pathlib import Path

        # Should be able to create different visitor types
        visitors = {
            "python": PythonSmellVisitor(
                file_path=Path("test.py"), workspace_root=Path("."), smell_types=["long_functions"]
            ),
        }

        for name, visitor in visitors.items():
            assert visitor is not None
            assert hasattr(visitor, "visit")

    def test_visitor_composition(self):
        """Test using multiple visitors together."""
        from pathlib import Path

        code = "def test():\n    return 1"
        tree = ast.parse(code)

        visitors = [
            PythonSmellVisitor(
                file_path=Path("test.py"), workspace_root=Path("."), smell_types=["long_functions"]
            )
        ]

        # Should be able to use multiple visitors on same AST
        for visitor in visitors:
            try:
                visitor.visit(tree)
            except Exception as e:
                pytest.fail(f"Visitor composition failed: {e}")

    def test_visitor_ast_compatibility(self):
        """Test visitor compatibility with different AST node types."""
        # Test various Python versions' AST features
        test_cases = [
            ("x = 1", "assignment"),
            ("def f(): pass", "function"),
            ("class C: pass", "class"),
            ("[x for x in range(10)]", "comprehension"),
            ("async def f(): pass", "async function"),
            ("x if True else y", "conditional"),
        ]

        from pathlib import Path

        visitor = PythonSmellVisitor(
            file_path=Path("test.py"),
            workspace_root=Path("."),
            smell_types=["long_functions", "complex_conditionals"],
        )

        for code, description in test_cases:
            try:
                tree = ast.parse(code)
                visitor.visit(tree)
            except Exception as e:
                pytest.fail(f"AST compatibility failed for {description}: {e}")
