"""
Python-specific code analyzer with comprehensive analysis capabilities.

This module provides specialized analysis for Python files, including syntax analysis,
code smell detection, complexity measurement, and quality scoring. It leverages
Python's AST module for accurate code parsing and analysis.

Classes:
    PythonAnalyzer: Comprehensive Python code analyzer
    PythonAnalysisError: Custom exception for Python analysis errors

Functions:
    is_python_file: Utility function to check if a file is a Python file
"""

import ast
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..analysis_result import AnalysisResult
from ..base_analyzer import AnalysisError, BaseAnalyzer
from ..detectors.code_smells import CodeSmellDetector
from ..metrics.collectors import MetricsCollector
from ..visitors.python_visitor import PythonSmellVisitor

# Constants
PYTHON_EXTENSIONS = [".py", ".pyw", ".pyi"]
DEFAULT_ENCODING = "utf-8"
ALTERNATIVE_ENCODINGS = ["latin-1", "cp1252"]

# Analysis type configurations
QUICK_ANALYSIS_SMELLS = ["long_functions", "complex_conditionals", "magic_numbers"]
DEEP_ANALYSIS_SMELLS = [
    "long_functions",
    "complex_conditionals",
    "magic_numbers",
    "duplicate_code",
    "god_classes",
    "dead_code",
    "long_parameter_list",
    "primitive_obsession",
    "feature_envy",
    "data_clumps",
]
SECURITY_ANALYSIS_SMELLS = [
    "long_functions",
    "complex_conditionals",
    "magic_numbers",
    "hardcoded_secrets",
    "sql_injection",
    "unsafe_input",
    "eval_usage",
    "pickle_usage",
    "unsafe_yaml",
    "weak_crypto",
]
PERFORMANCE_ANALYSIS_SMELLS = [
    "long_functions",
    "complex_conditionals",
    "magic_numbers",
    "inefficient_loops",
    "premature_optimization",
    "n_plus_one",
    "string_concatenation",
    "global_variables",
    "list_comprehension_abuse",
]

# Comment detection patterns
DOCSTRING_PATTERNS = ['"""', "'''"]
COMMENT_PREFIX = "#"

logger = logging.getLogger(__name__)


class PythonAnalysisError(AnalysisError):
    """Custom exception for Python analysis errors."""

    def __init__(
        self,
        message: str,
        file_path: Optional[Path] = None,
        syntax_error: Optional[SyntaxError] = None,
    ):
        super().__init__(message, file_path)
        self.syntax_error = syntax_error


class PythonAnalyzer(BaseAnalyzer):
    """Comprehensive Python-specific code analyzer.

    This analyzer provides deep analysis of Python files including:
    - Syntax validation and AST parsing
    - Code smell detection using visitor patterns
    - Metrics collection (complexity, maintainability, etc.)
    - Security vulnerability detection
    - Performance issue identification

    Attributes:
        metrics_collector: Collects various code metrics
        smell_detector: Detects code smells and anti-patterns
    """

    def __init__(self, workspace_root: Path, validate_workspace: bool = True) -> None:
        """Initialize Python analyzer.

        Args:
            workspace_root: Root directory of the workspace
            validate_workspace: Whether to validate workspace exists (set False for testing)

        Raises:
            AnalysisError: If initialization fails
        """
        super().__init__(workspace_root, validate_workspace)

        try:
            self.metrics_collector = MetricsCollector()
            self.smell_detector = CodeSmellDetector()
        except Exception as e:
            raise AnalysisError(f"Failed to initialize Python analyzer: {e}") from e

    def get_file_extensions(self) -> List[str]:
        """Return supported Python file extensions.

        Returns:
            List of Python file extensions
        """
        return PYTHON_EXTENSIONS.copy()

    async def analyze_file(self, file_path: Path, analysis_type: str = "quick") -> Dict[str, Any]:
        """Analyze a Python file and return comprehensive results.

        This method performs complete analysis including syntax validation,
        metrics collection, code smell detection, and quality scoring.

        Args:
            file_path: Path to the Python file to analyze
            analysis_type: Type of analysis ("quick", "deep", "security", "performance")

        Returns:
            Dictionary containing comprehensive analysis results
        """
        # Validate inputs and prepare
        analysis_context = self._prepare_analysis(file_path, analysis_type)
        result = AnalysisResult(analysis_context["file_path"], self.workspace_root)

        try:
            # Read and validate file content
            content = self._read_file_content(analysis_context["file_path"])

            # Early exit for syntax errors
            if not self._validate_and_handle_syntax(content, analysis_context["file_path"], result):
                return self._finalize_result(result, analysis_context["analysis_type"])

            # Perform comprehensive analysis
            self._perform_comprehensive_analysis(content, analysis_context, result)

            # Log completion and return results
            self.log_analysis_complete(analysis_context["file_path"], result.quality_score)
            return self._finalize_result(result, analysis_context["analysis_type"])

        except Exception as e:
            self.logger.error(f"Python analysis failed for {analysis_context['file_path']}: {e}")
            return self._create_error_result(analysis_context["file_path"], str(e))

    def _prepare_analysis(self, file_path: Path, analysis_type: str) -> Dict[str, Any]:
        """Prepare analysis by validating inputs and setting up context.

        Args:
            file_path: Path to the file
            analysis_type: Type of analysis

        Returns:
            Analysis context dictionary
        """
        validated_analysis_type = self.validate_analysis_type(analysis_type)
        validated_file_path = self.validate_file_path(file_path)

        self.log_analysis_start(validated_file_path, validated_analysis_type)

        return {"file_path": validated_file_path, "analysis_type": validated_analysis_type}

    def _validate_and_handle_syntax(
        self, content: str, file_path: Path, result: AnalysisResult
    ) -> bool:
        """Validate syntax and handle syntax errors.

        Args:
            content: File content
            file_path: Path to the file
            result: Analysis result container

        Returns:
            True if syntax is valid, False if there are syntax errors
        """
        syntax_issues = self._validate_syntax(content, file_path)
        if syntax_issues:
            for issue in syntax_issues:
                result.add_issue(issue["description"])
            result.set_quality_score(2.0)  # Low score for syntax errors
            return False
        return True

    def _perform_comprehensive_analysis(
        self, content: str, analysis_context: Dict[str, Any], result: AnalysisResult
    ) -> None:
        """Perform the main comprehensive analysis.

        Args:
            content: File content
            analysis_context: Analysis context
            result: Analysis result container
        """
        # Collect comprehensive metrics
        metrics = self._collect_comprehensive_metrics(content, analysis_context["file_path"])
        result.set_metrics(metrics)

        # Detect code smells based on analysis type
        smell_types = self._get_smell_types_for_analysis(analysis_context["analysis_type"])
        smells = self._detect_comprehensive_smells(
            content, analysis_context["file_path"], smell_types
        )

        # Process detected issues and suggestions
        self._process_smells(result, smells)

        # Calculate quality score
        result.calculate_quality_score()

    def _read_file_content(self, file_path: Path) -> str:
        """Read file content with proper encoding handling.

        Args:
            file_path: Path to the file

        Returns:
            File content as string

        Raises:
            PythonAnalysisError: If file cannot be read
        """
        encodings_to_try = [DEFAULT_ENCODING] + ALTERNATIVE_ENCODINGS

        for encoding in encodings_to_try:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                self.logger.debug(f"Successfully read {file_path} with {encoding} encoding")
                return content
            except UnicodeDecodeError:
                continue
            except (OSError, IOError) as e:
                raise PythonAnalysisError(f"Cannot read file {file_path}: {e}", file_path) from e

        raise PythonAnalysisError(
            f"Cannot decode file {file_path} with any supported encoding", file_path
        )

    def _validate_syntax(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Validate Python syntax and return syntax errors.

        Args:
            content: Python source code
            file_path: Path to the file

        Returns:
            List of syntax error dictionaries
        """
        try:
            ast.parse(content)
            return []  # No syntax errors
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {file_path}: {e}")
            return [
                {
                    "type": "syntax_error",
                    "file": str(file_path.relative_to(self.workspace_root)),
                    "line": getattr(e, "lineno", 1),
                    "column": getattr(e, "offset", 0),
                    "severity": "critical",
                    "description": f"Syntax error: {e.msg}",
                    "suggestion": "Fix the syntax error to enable proper analysis",
                }
            ]
        except Exception as e:
            self.logger.error(f"Unexpected error parsing {file_path}: {e}")
            return [
                {
                    "type": "parse_error",
                    "file": str(file_path.relative_to(self.workspace_root)),
                    "line": 1,
                    "severity": "high",
                    "description": f"Failed to parse Python file: {e}",
                    "suggestion": "Check file encoding and syntax",
                }
            ]

    def _collect_comprehensive_metrics(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Collect comprehensive metrics for Python code.

        Args:
            content: Python source code
            file_path: Path to the file

        Returns:
            Dictionary of collected metrics
        """
        try:
            # Use the metrics collector for Python-specific metrics
            metrics = self.metrics_collector.collect_python_metrics(content, file_path)

            # Add additional Python-specific metrics
            additional_metrics = self._calculate_additional_metrics(content)
            metrics.update(additional_metrics)

            return metrics

        except Exception as e:
            self.logger.warning(f"Failed to collect metrics for {file_path}: {e}")
            # Return basic metrics as fallback
            return self._calculate_basic_metrics(content)

    def _calculate_additional_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate additional Python-specific metrics.

        Args:
            content: Python source code

        Returns:
            Dictionary of additional metrics
        """
        lines = content.splitlines()

        metrics = {
            "comment_lines": self._count_comment_lines(lines),
            "docstring_coverage": self._calculate_docstring_coverage(content),
            "import_complexity": self._calculate_import_complexity(content),
            "class_count": self._count_classes(content),
            "function_count": self._count_functions(content),
            "decorator_usage": self._count_decorators(content),
        }

        return metrics

    def _calculate_basic_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate basic metrics as fallback.

        Args:
            content: File content

        Returns:
            Dictionary of basic metrics
        """
        lines = content.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]

        return {
            "total_lines": len(lines),
            "code_lines": len(non_empty_lines),
            "comment_lines": self._count_comment_lines(lines),
            "blank_lines": len(lines) - len(non_empty_lines),
            "average_line_length": sum(len(line) for line in lines) / len(lines) if lines else 0,
        }

    def _detect_comprehensive_smells(
        self, content: str, file_path: Path, smell_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect code smells using multiple detection strategies.

        Args:
            content: Python source code
            file_path: Path to the file
            smell_types: Types of smells to detect

        Returns:
            List of detected code smells
        """
        all_smells = []

        try:
            # AST-based smell detection using visitor pattern
            ast_smells = self._detect_ast_smells(content, file_path, smell_types)
            all_smells.extend(ast_smells)

            # Pattern-based smell detection
            pattern_smells = self._detect_pattern_smells(content, file_path, smell_types)
            all_smells.extend(pattern_smells)

            # Remove duplicates while preserving order
            unique_smells = self._deduplicate_smells(all_smells)

            return unique_smells

        except Exception as e:
            self.logger.error(f"Comprehensive smell detection failed for {file_path}: {e}")
            return []

    def _detect_ast_smells(
        self, content: str, file_path: Path, smell_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect smells using AST visitor pattern.

        Args:
            content: Python source code
            file_path: Path to the file
            smell_types: Types of smells to detect

        Returns:
            List of AST-detected smells
        """
        try:
            tree = ast.parse(content)
            visitor = PythonSmellVisitor(file_path, self.workspace_root, smell_types)
            visitor.visit(tree)
            return visitor.get_smells()
        except Exception as e:
            self.logger.warning(f"AST smell detection failed for {file_path}: {e}")
            return []

    def _detect_pattern_smells(
        self, content: str, file_path: Path, smell_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect smells using pattern matching.

        Args:
            content: Python source code
            file_path: Path to the file
            smell_types: Types of smells to detect

        Returns:
            List of pattern-detected smells
        """
        try:
            return self.smell_detector.detect_code_smells(content, file_path, smell_types)
        except Exception as e:
            self.logger.warning(f"Pattern smell detection failed for {file_path}: {e}")
            return []

    def _deduplicate_smells(self, smells: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate smells while preserving order.

        Args:
            smells: List of detected smells

        Returns:
            List of unique smells
        """
        seen = set()
        unique_smells = []

        for smell in smells:
            # Create a unique identifier for each smell
            identifier = (
                smell.get("type", ""),
                smell.get("file", ""),
                smell.get("line", 0),
                smell.get("description", ""),
            )

            if identifier not in seen:
                seen.add(identifier)
                unique_smells.append(smell)

        return unique_smells

    def _process_smells(self, result: AnalysisResult, smells: List[Dict[str, Any]]) -> None:
        """Process detected smells and add them to the result.

        Args:
            result: Analysis result container
            smells: List of detected smells
        """
        for smell in smells:
            description = smell.get("description", "Unknown issue detected")
            result.add_issue(description)

            suggestion = smell.get("suggestion")
            if suggestion:
                result.add_suggestion(suggestion)

    def _get_smell_types_for_analysis(self, analysis_type: str) -> List[str]:
        """Get appropriate smell types based on analysis type.

        Args:
            analysis_type: Type of analysis to perform

        Returns:
            List of smell types to detect
        """
        smell_configs = {
            "quick": QUICK_ANALYSIS_SMELLS,
            "deep": DEEP_ANALYSIS_SMELLS,
            "security": SECURITY_ANALYSIS_SMELLS,
            "performance": PERFORMANCE_ANALYSIS_SMELLS,
        }

        return smell_configs.get(analysis_type, QUICK_ANALYSIS_SMELLS).copy()

    def _count_comment_lines(self, lines: List[str]) -> int:
        """Count Python comment lines including docstrings.

        Args:
            lines: List of file lines

        Returns:
            Number of comment lines
        """
        comment_count = 0
        docstring_state = self._initialize_docstring_state()

        for line in lines:
            stripped = line.strip()

            # Count regular comments first
            if self._is_regular_comment(stripped):
                comment_count += 1
                continue

            # Handle docstrings
            comment_count += self._process_docstring_line(stripped, docstring_state)

        return comment_count

    def _initialize_docstring_state(self) -> Dict[str, Any]:
        """Initialize state for docstring tracking.

        Returns:
            Dictionary containing docstring state
        """
        return {"in_docstring": False, "docstring_char": None}

    def _is_regular_comment(self, stripped_line: str) -> bool:
        """Check if a line is a regular comment.

        Args:
            stripped_line: Stripped line content

        Returns:
            True if line is a regular comment
        """
        return stripped_line.startswith(COMMENT_PREFIX)

    def _process_docstring_line(self, stripped_line: str, state: Dict[str, Any]) -> int:
        """Process a line for docstring detection.

        Args:
            stripped_line: Stripped line content
            state: Current docstring state

        Returns:
            Number of comment lines found (0 or 1)
        """
        # Handle lines inside existing docstrings
        if state["in_docstring"]:
            return self._handle_inside_docstring(stripped_line, state)

        # Check for new docstring starts
        return self._handle_potential_docstring_start(stripped_line, state)

    def _handle_inside_docstring(self, stripped_line: str, state: Dict[str, Any]) -> int:
        """Handle line that is inside a multi-line docstring.

        Args:
            stripped_line: Stripped line content
            state: Current docstring state

        Returns:
            Number of comment lines found (0 or 1)
        """
        # Check if this line ends the docstring
        for pattern in DOCSTRING_PATTERNS:
            if pattern in stripped_line and pattern == state["docstring_char"]:
                quote_count = stripped_line.count(pattern)
                if quote_count % 2 == 1:
                    # Odd number means we're ending the docstring
                    state["in_docstring"] = False
                    state["docstring_char"] = None
                    return 1  # This line is still part of the docstring

        # Line is inside docstring but doesn't end it
        return 1

    def _handle_potential_docstring_start(self, stripped_line: str, state: Dict[str, Any]) -> int:
        """Handle line that might start a new docstring.

        Args:
            stripped_line: Stripped line content
            state: Current docstring state

        Returns:
            Number of comment lines found (0 or 1)
        """
        for pattern in DOCSTRING_PATTERNS:
            if pattern in stripped_line:
                quote_count = stripped_line.count(pattern)

                if quote_count == 1:
                    # Starting a multi-line docstring
                    state["in_docstring"] = True
                    state["docstring_char"] = pattern
                    return 1
                elif quote_count >= 2 and quote_count % 2 == 0:
                    # Complete docstring on one line
                    return 1

        return 0

    def _calculate_docstring_coverage(self, content: str) -> float:
        """Calculate docstring coverage percentage.

        Args:
            content: Python source code

        Returns:
            Docstring coverage percentage (0-100)
        """
        try:
            tree = ast.parse(content)
            coverage_stats = self._collect_docstring_stats(tree)
            return self._compute_coverage_percentage(coverage_stats)

        except Exception:
            return 0.0

    def _collect_docstring_stats(self, tree: ast.AST) -> Dict[str, int]:
        """Collect statistics about docstring coverage.

        Args:
            tree: Parsed AST tree

        Returns:
            Dictionary with total_items and documented_items counts
        """
        stats = {"total_items": 0, "documented_items": 0}

        for node in ast.walk(tree):
            if self._is_documentable_node(node):
                stats["total_items"] += 1
                if self._has_docstring(node):
                    stats["documented_items"] += 1

        return stats

    def _is_documentable_node(self, node: ast.AST) -> bool:
        """Check if an AST node should have documentation.

        Args:
            node: AST node to check

        Returns:
            True if node should be documented
        """
        return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module))

    def _has_docstring(self, node: ast.AST) -> bool:
        """Check if an AST node has a docstring.

        Args:
            node: AST node to check

        Returns:
            True if node has a docstring
        """
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            return ast.get_docstring(node) is not None
        return False

    def _compute_coverage_percentage(self, stats: Dict[str, int]) -> float:
        """Compute coverage percentage from statistics.

        Args:
            stats: Dictionary with total and documented counts

        Returns:
            Coverage percentage (0-100)
        """
        if stats["total_items"] == 0:
            return 100.0  # No functions/classes to document

        return (stats["documented_items"] / stats["total_items"]) * 100.0

    def _calculate_import_complexity(self, content: str) -> int:
        """Calculate import complexity score.

        Args:
            content: Python source code

        Returns:
            Import complexity score
        """
        try:
            tree = ast.parse(content)
            complexity = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    complexity += len(node.names)
                elif isinstance(node, ast.ImportFrom):
                    complexity += len(node.names) if node.names else 1

            return complexity

        except Exception:
            return 0

    def _count_classes(self, content: str) -> int:
        """Count number of classes in the code.

        Args:
            content: Python source code

        Returns:
            Number of classes
        """
        try:
            tree = ast.parse(content)
            return len([node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)])
        except Exception:
            return 0

    def _count_functions(self, content: str) -> int:
        """Count number of functions in the code.

        Args:
            content: Python source code

        Returns:
            Number of functions
        """
        try:
            tree = ast.parse(content)
            return len(
                [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
            )
        except Exception:
            return 0

    def _count_decorators(self, content: str) -> int:
        """Count number of decorators used.

        Args:
            content: Python source code

        Returns:
            Number of decorators
        """
        try:
            tree = ast.parse(content)
            decorator_count = 0

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    decorator_count += len(node.decorator_list)

            return decorator_count

        except Exception:
            return 0

    def _finalize_result(self, result: AnalysisResult, analysis_type: str) -> Dict[str, Any]:
        """Finalize analysis result with additional metadata.

        Args:
            result: Analysis result container
            analysis_type: Type of analysis performed

        Returns:
            Finalized result dictionary
        """
        result_dict = result.to_dict()
        result_dict.update(
            {"analysis_type": analysis_type, "analyzer": "PythonAnalyzer", "language": "python"}
        )

        return result_dict

    def _create_error_result(self, file_path: Path, error_message: str) -> Dict[str, Any]:
        """Create error result for failed analysis.

        Args:
            file_path: Path to the file that failed analysis
            error_message: Error message

        Returns:
            Error result dictionary
        """
        try:
            relative_path = str(file_path.relative_to(self.workspace_root))
        except ValueError:
            relative_path = str(file_path)

        return {
            "file": relative_path,
            "error": error_message,
            "quality_score": 0,
            "analyzer": "PythonAnalyzer",
            "language": "python",
        }

    # Legacy method compatibility
    def detect_code_smells(
        self, content: str, file_path: Path, smell_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect code smells in Python code (legacy interface).

        This method maintains compatibility with the base class interface
        while leveraging the comprehensive smell detection capabilities.

        Args:
            content: Python source code
            file_path: Path to the file
            smell_types: List of smell types to detect

        Returns:
            List of detected code smells
        """
        return self._detect_comprehensive_smells(content, file_path, smell_types)


def is_python_file(file_path: Path) -> bool:
    """Check if a file is a Python file based on extension.

    Args:
        file_path: Path to check

    Returns:
        True if file is a Python file, False otherwise
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    return file_path.suffix.lower() in PYTHON_EXTENSIONS
