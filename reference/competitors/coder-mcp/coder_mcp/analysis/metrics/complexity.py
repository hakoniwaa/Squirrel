"""
Code complexity metrics calculation

This module calculates various complexity metrics including:
- Cyclomatic Complexity (McCabe Complexity)
- Cognitive Complexity
- Combined complexity scores
"""

import ast
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


# Constants for complexity calculations
class ComplexityConstants:
    """Constants used in complexity calculations"""

    # Base complexity for any function/method
    BASE_FUNCTION_COMPLEXITY = 1

    # Weight for boolean operations (each additional condition adds 1)
    BOOLEAN_OPERATION_WEIGHT = 1

    # Cognitive complexity increment per nesting level
    NESTING_LEVEL_INCREMENT = 1

    # Base cognitive complexity for control structures
    BASE_CONTROL_STRUCTURE_COMPLEXITY = 1

    # Weight for combining cyclomatic and cognitive complexity
    CYCLOMATIC_WEIGHT = 0.5
    COGNITIVE_WEIGHT = 0.5


class ComplexityCalculator(ABC):
    """Abstract base class for complexity calculators"""

    @abstractmethod
    def calculate(self, node: Any) -> Dict[str, Any]:
        """
        Calculate complexity metrics for a given node

        Args:
            node: AST node to analyze

        Returns:
            Dictionary containing complexity metrics
        """


class CyclomaticComplexityCalculator(ComplexityCalculator, ast.NodeVisitor):
    """
    Calculate cyclomatic complexity for Python AST nodes

    Cyclomatic complexity measures the number of linearly independent paths
    through a program's source code.
    """

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        """Reset the calculator for a new analysis"""
        self.complexity: int = 0
        self.current_complexity: int = 0
        self.max_complexity: int = 0
        self.function_complexities: Dict[str, int] = {}
        self.current_function: Optional[str] = None

    def calculate(self, node: ast.AST) -> Dict[str, Any]:
        """
        Calculate complexity metrics for an AST node

        Args:
            node: Python AST node to analyze

        Returns:
            Dictionary containing:
                - total_complexity: Total cyclomatic complexity
                - max_function_complexity: Highest complexity among functions
                - function_complexities: Map of function names to complexities
                - average_complexity: Average function complexity
        """
        self.reset()
        self.visit(node)

        return {
            "total_complexity": self.complexity,
            "max_function_complexity": self.max_complexity,
            "function_complexities": self.function_complexities.copy(),
            "average_complexity": self._calculate_average_complexity(),
        }

    def _calculate_average_complexity(self) -> float:
        """Calculate average complexity across all functions"""
        if not self.function_complexities:
            return 0.0

        total = sum(self.function_complexities.values())
        return total / len(self.function_complexities)

    def calculate_function_complexity(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> int:
        """
        Calculate cyclomatic complexity for a single function

        Args:
            node: Function definition node

        Returns:
            Cyclomatic complexity value
        """
        complexity = ComplexityConstants.BASE_FUNCTION_COMPLEXITY

        # Decision points that increase complexity
        decision_nodes = (
            ast.If,  # if statements
            ast.While,  # while loops
            ast.For,  # for loops
            ast.ExceptHandler,  # except clauses
            ast.ListComp,  # list comprehensions
            ast.DictComp,  # dict comprehensions
            ast.SetComp,  # set comprehensions
            ast.GeneratorExp,  # generator expressions
        )

        for child in ast.walk(node):
            if isinstance(child, decision_nodes):
                complexity += ComplexityConstants.BOOLEAN_OPERATION_WEIGHT
            elif isinstance(child, ast.BoolOp):
                # Each additional boolean operator adds complexity
                complexity += len(child.values) - ComplexityConstants.BOOLEAN_OPERATION_WEIGHT
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += ComplexityConstants.BOOLEAN_OPERATION_WEIGHT

        return complexity

    def _process_function(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], name: str
    ) -> None:
        """Process a function definition and update complexity metrics"""
        old_function = self.current_function
        self.current_function = name

        func_complexity = self.calculate_function_complexity(node)
        self.function_complexities[name] = func_complexity
        self.max_complexity = max(self.max_complexity, func_complexity)
        self.complexity += func_complexity

        self.current_function = old_function

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition and calculate its complexity"""
        self._process_function(node, node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition and calculate its complexity"""
        self._process_function(node, node.name)


class CognitiveComplexityCalculator(ComplexityCalculator, ast.NodeVisitor):
    """
    Calculate cognitive complexity for Python AST nodes

    Cognitive complexity measures how difficult it is to understand the code,
    taking into account nesting levels and control flow structures.
    """

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        """Reset the calculator for a new analysis"""
        self.cognitive_complexity: int = 0
        self.nesting_level: int = 0
        self.current_function: Optional[str] = None
        self.function_complexities: Dict[str, int] = {}

    def calculate(self, node: ast.AST) -> Dict[str, Any]:
        """
        Calculate cognitive complexity metrics for an AST node

        Args:
            node: Python AST node to analyze

        Returns:
            Dictionary containing:
                - total_cognitive_complexity: Total cognitive complexity
                - function_complexities: Map of function names to complexities
                - average_cognitive_complexity: Average function complexity
        """
        self.reset()
        self.visit(node)

        return {
            "total_cognitive_complexity": self.cognitive_complexity,
            "function_complexities": self.function_complexities.copy(),
            "average_cognitive_complexity": self._calculate_average_complexity(),
        }

    def _calculate_average_complexity(self) -> float:
        """Calculate average cognitive complexity across all functions"""
        if not self.function_complexities:
            return 0.0

        total = sum(self.function_complexities.values())
        return total / len(self.function_complexities)

    def _process_function(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], name: str
    ) -> None:
        """Process a function and calculate its cognitive complexity"""
        # Save current state
        old_function = self.current_function
        old_complexity = self.cognitive_complexity
        old_nesting = self.nesting_level

        # Reset for function analysis
        self.current_function = name
        self.cognitive_complexity = 0
        self.nesting_level = 0

        # Visit function body
        for child in node.body:
            self.visit(child)

        # Store function complexity
        self.function_complexities[name] = self.cognitive_complexity

        # Restore state and add function complexity to total
        func_complexity = self.cognitive_complexity
        self.current_function = old_function
        self.cognitive_complexity = old_complexity + func_complexity
        self.nesting_level = old_nesting

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition and calculate its cognitive complexity"""
        self._process_function(node, node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition and calculate its cognitive complexity"""
        self._process_function(node, node.name)

    def _process_control_structure(
        self, node: ast.AST, body: List[ast.stmt], orelse: Optional[List[ast.stmt]] = None
    ) -> None:
        """Process a control structure and update complexity"""
        # Add base complexity plus nesting penalty
        self.cognitive_complexity += (
            ComplexityConstants.BASE_CONTROL_STRUCTURE_COMPLEXITY
            + self.nesting_level * ComplexityConstants.NESTING_LEVEL_INCREMENT
        )

        # Process body with increased nesting
        self.nesting_level += 1
        for child in body:
            self.visit(child)
        self.nesting_level -= 1

        # Process else clause if present
        if orelse:
            self._process_else_clause(orelse)

    def _process_else_clause(self, orelse: List[ast.stmt]) -> None:
        """Process else/elif clauses"""
        if len(orelse) == 1 and isinstance(orelse[0], ast.If):
            # elif case - add complexity but don't increase nesting
            self.cognitive_complexity += ComplexityConstants.BASE_CONTROL_STRUCTURE_COMPLEXITY
        else:
            # else case
            self.cognitive_complexity += ComplexityConstants.BASE_CONTROL_STRUCTURE_COMPLEXITY

        self.nesting_level += 1
        for child in orelse:
            self.visit(child)
        self.nesting_level -= 1

    def visit_If(self, node: ast.If) -> None:
        """Visit if statement and add cognitive complexity"""
        self._process_control_structure(node, node.body, node.orelse)

    def visit_While(self, node: ast.While) -> None:
        """Visit while loop and add cognitive complexity"""
        self._process_control_structure(node, node.body, node.orelse)

    def visit_For(self, node: ast.For) -> None:
        """Visit for loop and add cognitive complexity"""
        self._process_control_structure(node, node.body, node.orelse)

    def visit_Try(self, node: ast.Try) -> None:
        """Visit try statement and add cognitive complexity"""
        # Try block
        self.cognitive_complexity += (
            ComplexityConstants.BASE_CONTROL_STRUCTURE_COMPLEXITY
            + self.nesting_level * ComplexityConstants.NESTING_LEVEL_INCREMENT
        )

        self.nesting_level += 1
        for child in node.body:
            self.visit(child)
        self.nesting_level -= 1

        # Except clauses
        for handler in node.handlers:
            self.cognitive_complexity += ComplexityConstants.BASE_CONTROL_STRUCTURE_COMPLEXITY
            self.nesting_level += 1
            for child in handler.body:
                self.visit(child)
            self.nesting_level -= 1

        # Else and finally clauses
        for child in node.orelse + node.finalbody:
            self.visit(child)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        """Visit boolean operation and add cognitive complexity"""
        # Each additional boolean operator adds complexity
        self.cognitive_complexity += len(node.values) - ComplexityConstants.BOOLEAN_OPERATION_WEIGHT
        for child in node.values:
            self.visit(child)


def calculate_complexity_metrics(node: ast.AST) -> Dict[str, Any]:
    """
    Calculate all complexity metrics for an AST node

    Args:
        node: Python AST node to analyze

    Returns:
        Dictionary containing:
            - cyclomatic: Cyclomatic complexity metrics
            - cognitive: Cognitive complexity metrics
            - combined_score: Weighted combination of both metrics
    """
    cyclomatic_calc = CyclomaticComplexityCalculator()
    cognitive_calc = CognitiveComplexityCalculator()

    cyclomatic_metrics = cyclomatic_calc.calculate(node)
    cognitive_metrics = cognitive_calc.calculate(node)

    # Calculate combined score using configurable weights
    combined_score = (
        cyclomatic_metrics["total_complexity"] * ComplexityConstants.CYCLOMATIC_WEIGHT
        + cognitive_metrics["total_cognitive_complexity"] * ComplexityConstants.COGNITIVE_WEIGHT
    )

    return {
        "cyclomatic": cyclomatic_metrics,
        "cognitive": cognitive_metrics,
        "combined_score": combined_score,
    }
