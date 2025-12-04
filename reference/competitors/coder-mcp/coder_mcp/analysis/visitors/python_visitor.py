"""
Python AST visitor for code smell detection
"""

import ast
from pathlib import Path
from typing import Any, Dict, List

from .ast_visitor import BaseASTVisitor


class PythonSmellVisitor(BaseASTVisitor):
    """AST visitor for detecting Python code smells"""

    def __init__(self, file_path: Path, workspace_root: Path, smell_types: List[str]):
        super().__init__(file_path, workspace_root, smell_types)
        self.current_class = None
        self.class_lines = 0

        # Code smell thresholds
        self.thresholds = {
            "long_functions": 50,
            "complex_conditionals": 5,
            "god_classes": 300,
            "long_parameter_list": 5,
        }

    def get_smells(self) -> List[Dict[str, Any]]:
        """Get all detected code smells"""
        return self.smells.copy()

    def visit_FunctionDef(self, node):
        """Check function-related smells"""
        # Long functions
        if self.should_check_smell("long_functions"):
            func_lines = (
                (node.end_lineno - node.lineno)
                if (hasattr(node, "end_lineno") and node.end_lineno is not None)
                else 0
            )
            threshold = self.thresholds["long_functions"]

            if func_lines > threshold:
                self.add_smell(
                    "long_functions",
                    node.lineno,
                    "medium",
                    f"Function '{node.name}' is {func_lines} lines long (threshold: {threshold})",
                    "Consider breaking this function into smaller, more focused functions",
                )

        # Long parameter list
        if self.should_check_smell("long_parameter_list"):
            param_count = len(node.args.args)
            threshold = self.thresholds["long_parameter_list"]

            if param_count > threshold:
                self.add_smell(
                    "long_parameter_list",
                    node.lineno,
                    "medium",
                    f"Function '{node.name}' has {param_count} parameters (threshold: {threshold})",
                    "Consider using a configuration object or breaking down the function",
                )

        # Complex conditionals
        if self.should_check_smell("complex_conditionals"):
            complexity = self._calculate_complexity(node)
            threshold = self.thresholds["complex_conditionals"]

            if complexity > threshold:
                self.add_smell(
                    "complex_conditionals",
                    node.lineno,
                    "medium",
                    f"Function '{node.name}' has cyclomatic complexity of {complexity} "
                    f"(threshold: {threshold})",
                    "Simplify conditional logic using early returns or extract complex conditions",
                )

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Handle async functions same as regular functions"""
        # Long functions
        if self.should_check_smell("long_functions"):
            func_lines = (
                (node.end_lineno - node.lineno)
                if (hasattr(node, "end_lineno") and node.end_lineno is not None)
                else 0
            )
            threshold = self.thresholds["long_functions"]

            if func_lines > threshold:
                self.add_smell(
                    "long_functions",
                    node.lineno,
                    "medium",
                    f"Function '{node.name}' is {func_lines} lines long (threshold: {threshold})",
                    "Consider breaking this function into smaller, more focused functions",
                )

        # Long parameter list
        if self.should_check_smell("long_parameter_list"):
            param_count = len(node.args.args)
            threshold = self.thresholds["long_parameter_list"]

            if param_count > threshold:
                self.add_smell(
                    "long_parameter_list",
                    node.lineno,
                    "medium",
                    f"Function '{node.name}' has {param_count} parameters (threshold: {threshold})",
                    "Consider using a configuration object or breaking down the function",
                )

        # Complex conditionals
        if self.should_check_smell("complex_conditionals"):
            complexity = self._calculate_complexity(node)
            threshold = self.thresholds["complex_conditionals"]

            if complexity > threshold:
                self.add_smell(
                    "complex_conditionals",
                    node.lineno,
                    "medium",
                    f"Function '{node.name}' has cyclomatic complexity of {complexity} "
                    f"(threshold: {threshold})",
                    "Simplify conditional logic using early returns or extract complex conditions",
                )

        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Check class-related smells"""
        self.current_class = node.name
        self.class_lines = (
            (node.end_lineno - node.lineno)
            if (hasattr(node, "end_lineno") and node.end_lineno is not None)
            else 0
        )

        # God classes
        if self.should_check_smell("god_classes"):
            threshold = self.thresholds["god_classes"]

            if self.class_lines > threshold:
                self.add_smell(
                    "god_classes",
                    node.lineno,
                    "high",
                    f"Class '{node.name}' is {self.class_lines} lines long "
                    f"(threshold: {threshold})",
                    "Consider splitting this class using Single Responsibility Principle",
                )

        self.generic_visit(node)
        self.current_class = None

    def visit_Num(self, node):
        """Check for magic numbers (Python < 3.8)"""
        if self.should_check_smell("magic_numbers"):
            # Ignore common numbers
            if hasattr(node, "n") and node.n not in [0, 1, -1, 2, 10, 100]:
                line_num = getattr(node, "lineno", 0)
                if line_num > 0:
                    self.add_smell(
                        "magic_numbers",
                        line_num,
                        "low",
                        f"Magic number {node.n} found",
                        "Extract this to a named constant",
                    )

        self.generic_visit(node)

    def visit_Constant(self, node):
        """Check for magic numbers (Python >= 3.8)"""
        if self.should_check_smell("magic_numbers"):
            # Check if it's a numeric constant
            if isinstance(node.value, (int, float)) and node.value not in [0, 1, -1, 2, 10, 100]:
                line_num = getattr(node, "lineno", 0)
                if line_num > 0:
                    self.add_smell(
                        "magic_numbers",
                        line_num,
                        "low",
                        f"Magic number {node.value} found",
                        "Extract this to a named constant",
                    )

        self.generic_visit(node)

    def visit_Global(self, node):
        """Check for excessive global variable usage"""
        if self.should_check_smell("global_variables"):
            for name in node.names:
                self.add_smell(
                    "global_variables",
                    node.lineno,
                    "medium",
                    f"Global variable '{name}' used",
                    "Consider using class attributes or passing variables as parameters",
                )

        self.generic_visit(node)

    def visit_Import(self, node):
        """Check import-related smells"""
        if self.should_check_smell("unused_imports"):
            # This would require more complex analysis to detect truly unused imports
            # For now, just record the import
            pass

        self.generic_visit(node)

    def visit_Call(self, node):
        """Check for dangerous function calls"""
        if self.should_check_smell("eval_usage"):
            if (hasattr(node.func, "id") and getattr(node.func, "id", None) == "eval") or (
                hasattr(node.func, "attr") and getattr(node.func, "attr", None) == "eval"
            ):
                self.add_smell(
                    "eval_usage",
                    node.lineno,
                    "high",
                    "Usage of eval() function detected",
                    "Avoid eval() - use safer alternatives like ast.literal_eval() for data",
                )

        # Check for exec usage
        if self.should_check_smell("exec_usage"):
            if (hasattr(node.func, "id") and getattr(node.func, "id", None) == "exec") or (
                hasattr(node.func, "attr") and getattr(node.func, "attr", None) == "exec"
            ):
                self.add_smell(
                    "exec_usage",
                    node.lineno,
                    "high",
                    "Usage of exec() function detected",
                    "Avoid exec() - use safer alternatives",
                )

        self.generic_visit(node)

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1

        return complexity

    def visit_Try(self, node):
        """Check try-except related smells"""
        if self.should_check_smell("bare_except"):
            for handler in node.handlers:
                if handler.type is None:
                    self.add_smell(
                        "bare_except",
                        handler.lineno,
                        "medium",
                        "Bare except clause found",
                        "Specify the exception type or use 'except Exception:' instead",
                    )

        if self.should_check_smell("too_many_except"):
            if len(node.handlers) > 3:
                self.add_smell(
                    "too_many_except",
                    node.lineno,
                    "medium",
                    f"Too many except clauses ({len(node.handlers)})",
                    "Consider refactoring to reduce the number of exception types",
                )

        self.generic_visit(node)

    def visit_With(self, node):
        """Check with statement usage"""
        # Could add checks for proper resource management
        self.generic_visit(node)
