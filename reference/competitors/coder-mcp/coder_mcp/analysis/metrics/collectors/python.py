"""
Python-specific code analysis and metrics collection

This module handles Python AST analysis for construct counting and
Halstead complexity metrics calculation.
"""

import ast
import math
from typing import Dict, Set

from ..protocols import HalsteadMetrics, PythonMetrics


class ASTVisitorBase(ast.NodeVisitor):
    """Shared base for AST visitors to avoid duplicate visit_* logic."""

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self._handle_comprehension()
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self._handle_comprehension()
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self._handle_comprehension()
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self._handle_comprehension()
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self._handle_lambda()
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self._handle_try()
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self._handle_with()
        self.generic_visit(node)

    # These methods should be implemented by subclasses
    def _handle_comprehension(self):
        pass

    def _handle_lambda(self):
        pass

    def _handle_try(self):
        pass

    def _handle_with(self):
        pass


class PythonConstructCounter(ASTVisitorBase):
    """Count Python language constructs using AST analysis"""

    def __init__(self):
        self._reset_counters()
        self.in_class = False

    def _reset_counters(self) -> None:
        """Reset all counters for a new analysis"""
        self.counts = {
            "functions": 0,
            "async_functions": 0,
            "classes": 0,
            "methods": 0,
            "imports": 0,
            "decorators": 0,
            "comprehensions": 0,
            "lambdas": 0,
            "try_blocks": 0,
            "with_statements": 0,
        }

    def count_constructs(self, tree: ast.AST) -> PythonMetrics:
        """
        Count Python constructs in an AST

        Args:
            tree: Python AST to analyze

        Returns:
            PythonMetrics dictionary with construct counts
        """
        self._reset_counters()
        self.visit(tree)
        return PythonMetrics(
            functions=self.counts["functions"],
            async_functions=self.counts["async_functions"],
            classes=self.counts["classes"],
            methods=self.counts["methods"],
            imports=self.counts["imports"],
            decorators=self.counts["decorators"],
            comprehensions=self.counts["comprehensions"],
            lambdas=self.counts["lambdas"],
            try_blocks=self.counts["try_blocks"],
            with_statements=self.counts["with_statements"],
        )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition"""
        # Count all functions (including methods) in the functions count
        self.counts["functions"] += 1

        if self.in_class:
            self.counts["methods"] += 1

        self._count_decorators(node.decorator_list)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition"""
        # Count async functions separately from regular functions
        self.counts["async_functions"] += 1

        if self.in_class:
            self.counts["methods"] += 1

        self._count_decorators(node.decorator_list)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition"""
        self.counts["classes"] += 1
        self._count_decorators(node.decorator_list)

        # Track class context for method counting
        old_in_class = self.in_class
        self.in_class = True
        self.generic_visit(node)
        self.in_class = old_in_class

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement"""
        self.counts["imports"] += 1
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from-import statement"""
        self.counts["imports"] += 1
        self.generic_visit(node)

    def _count_decorators(self, decorator_list: list) -> None:
        """Count decorators in a decorator list"""
        self.counts["decorators"] += len(decorator_list)

    def get_metrics(self) -> PythonMetrics:
        """Get the collected metrics (for backward compatibility)"""
        counts = self.counts.copy()
        return PythonMetrics(
            functions=counts["functions"],
            async_functions=counts["async_functions"],
            classes=counts["classes"],
            methods=counts["methods"],
            imports=counts["imports"],
            decorators=counts["decorators"],
            comprehensions=counts["comprehensions"],
            lambdas=counts["lambdas"],
            try_blocks=counts["try_blocks"],
            with_statements=counts["with_statements"],
        )

    def _handle_comprehension(self):
        self.counts["comprehensions"] += 1

    def _handle_lambda(self):
        self.counts["lambdas"] += 1

    def _handle_try(self):
        self.counts["try_blocks"] += 1

    def _handle_with(self):
        self.counts["with_statements"] += 1


class HalsteadConstants:
    """Constants for Halstead metrics calculation"""

    # Minimum values to avoid mathematical errors
    MIN_VALUE = 1

    # Default values when no data is available
    DEFAULT_VOCABULARY = 2  # At least operators and operands exist

    # Mathematical constants
    LOG_BASE = 2


class HalsteadCalculator(ASTVisitorBase):
    """Calculate Halstead complexity metrics from Python AST"""

    def __init__(self):
        self._reset_collections()

    def _reset_collections(self) -> None:
        """Reset collections for a new analysis"""
        self.operators: Set[str] = set()
        self.operands: Set[str] = set()
        self.operator_count = 0
        self.operand_count = 0

    def calculate_halstead_metrics(self, tree: ast.AST) -> HalsteadMetrics:
        """
        Calculate Halstead complexity metrics for an AST

        Args:
            tree: Python AST to analyze

        Returns:
            HalsteadMetrics dictionary with all metrics
        """
        self._reset_collections()
        self.visit(tree)
        return self._compute_metrics()

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """Visit binary operation"""
        operator_name = type(node.op).__name__
        self.operators.add(operator_name)
        self.operator_count += 1
        self.generic_visit(node)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        """Visit unary operation"""
        operator_name = type(node.op).__name__
        self.operators.add(operator_name)
        self.operator_count += 1
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        """Visit comparison operation"""
        for op in node.ops:
            operator_name = type(op).__name__
            self.operators.add(operator_name)
            self.operator_count += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Visit boolean operation"""
        operator_name = type(node.op).__name__
        self.operators.add(operator_name)
        self.operator_count += 1
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Visit augmented assignment"""
        operator_name = type(node.op).__name__
        self.operators.add(operator_name)
        self.operator_count += 1
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name node (variable, function name, etc.)"""
        self.operands.add(node.id)
        self.operand_count += 1
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        """Visit constant node (literal values)"""
        # Use string representation for consistent hashing
        operand_value = str(node.value)
        self.operands.add(operand_value)
        self.operand_count += 1
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access (obj.attr)"""
        self.operands.add(node.attr)
        self.operand_count += 1
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition"""
        self.operands.add(node.name)
        self.operand_count += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition"""
        self.operands.add(node.name)
        self.operand_count += 1
        self.generic_visit(node)

    def _compute_metrics(self) -> HalsteadMetrics:
        """Calculate and return Halstead metrics"""
        # Distinct counts
        n1 = len(self.operators)  # Distinct operators
        n2 = len(self.operands)  # Distinct operands

        # Total counts
        N1 = self.operator_count  # Total operators
        N2 = self.operand_count  # Total operands

        # Handle edge cases
        n1 = max(n1, HalsteadConstants.MIN_VALUE)
        n2 = max(n2, HalsteadConstants.MIN_VALUE)

        # Calculate metrics
        program_length = N1 + N2
        vocabulary = n1 + n2

        if vocabulary > HalsteadConstants.MIN_VALUE:
            volume = program_length * math.log2(vocabulary)
            difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
            effort = difficulty * volume
        else:
            volume = difficulty = effort = 0

        return HalsteadMetrics(
            halstead_length=program_length,
            halstead_vocabulary=vocabulary,
            halstead_volume=volume,
            halstead_difficulty=difficulty,
            halstead_effort=effort,
        )

    def get_metrics(self) -> Dict[str, float]:
        """Get the collected metrics (for backward compatibility)"""
        metrics = self._compute_metrics()
        return {
            "halstead_length": float(metrics["halstead_length"]),
            "halstead_vocabulary": float(metrics["halstead_vocabulary"]),
            "halstead_volume": float(metrics["halstead_volume"]),
            "halstead_difficulty": float(metrics["halstead_difficulty"]),
            "halstead_effort": float(metrics["halstead_effort"]),
        }

    def _handle_comprehension(self):
        # No-op for Halstead metrics
        pass

    def _handle_lambda(self):
        # No-op for Halstead metrics
        pass

    def _handle_try(self):
        # No-op for Halstead metrics
        pass

    def _handle_with(self):
        # No-op for Halstead metrics
        pass
