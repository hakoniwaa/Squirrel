"""
JavaScript-specific code analyzer
"""

import re
from pathlib import Path
from typing import Any, Dict, List

from ..analysis_result import AnalysisResult
from ..base_analyzer import BaseAnalyzer
from ..detectors.code_smells import CodeSmellDetector
from ..metrics.collectors import MetricsCollector


class JavaScriptAnalyzer(BaseAnalyzer):
    """JavaScript-specific code analyzer"""

    def __init__(self, workspace_root: Path, validate_workspace: bool = True):
        super().__init__(workspace_root, validate_workspace)
        self.metrics_collector = MetricsCollector()
        self.smell_detector = CodeSmellDetector()

    def get_file_extensions(self) -> List[str]:
        """Return supported JavaScript file extensions"""
        return [".js", ".jsx", ".mjs", ".cjs"]

    async def analyze_file(self, file_path: Path, analysis_type: str = "quick") -> Dict[str, Any]:
        """Analyze a JavaScript file and return comprehensive results"""
        result = AnalysisResult(file_path, self.workspace_root)

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Collect metrics
            metrics = self.metrics_collector.collect_javascript_metrics(content, file_path)
            result.set_metrics(metrics)

            # Detect code smells based on analysis type
            smell_types = self._get_smell_types_for_analysis(analysis_type)
            smells = self.detect_code_smells(content, file_path, smell_types)

            # Add issues and suggestions from smells
            for smell in smells:
                result.add_issue(smell.get("description", ""))
                if "suggestion" in smell:
                    result.add_suggestion(smell["suggestion"])

            # Calculate quality score
            result.calculate_quality_score()

            # Add analysis type to result
            result_dict = result.to_dict()
            result_dict["analysis_type"] = analysis_type

            return result_dict

        except FileNotFoundError:
            return {
                "file": str(file_path.relative_to(self.workspace_root)),
                "error": f"File not found: {file_path}",
                "quality_score": 0,
            }
        except UnicodeDecodeError:
            return {
                "file": str(file_path.relative_to(self.workspace_root)),
                "error": "File is not text or has encoding issues",
                "quality_score": 0,
            }
        except (OSError, ValueError, TypeError) as e:
            self.logger.error("Error analyzing JavaScript file %s: %s", file_path, e)
            return {
                "file": str(file_path.relative_to(self.workspace_root)),
                "error": str(e),
                "quality_score": 0,
            }

    def detect_code_smells(
        self, content: str, file_path: Path, smell_types: List[str]
    ) -> List[Dict[str, Any]]:
        """Detect code smells in JavaScript code using regex patterns"""
        smells = []
        lines = content.splitlines()

        if "long_functions" in smell_types:
            smells.extend(self._detect_long_functions(lines, file_path))

        if "complex_conditionals" in smell_types:
            smells.extend(self._detect_complex_conditionals(lines, file_path))

        if "magic_numbers" in smell_types:
            smells.extend(self._detect_magic_numbers(lines, file_path))

        if "duplicate_code" in smell_types:
            smells.extend(self._detect_duplicate_code(lines, file_path))

        if "console_logs" in smell_types:
            smells.extend(self._detect_console_logs(lines, file_path))

        if "var_usage" in smell_types:
            smells.extend(self._detect_var_usage(lines, file_path))

        if "callback_hell" in smell_types:
            smells.extend(self._detect_callback_hell(lines, file_path))

        return smells

    def _detect_long_functions(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Detect long functions in JavaScript"""
        smells = []
        function_patterns = [
            r"function\s+(\w+)",
            r"const\s+(\w+)\s*=\s*function",
            r"let\s+(\w+)\s*=\s*function",
            r"var\s+(\w+)\s*=\s*function",
            r"const\s+(\w+)\s*=\s*\([^)]*\)\s*=>",
            r"(\w+)\s*:\s*function",
            r"async\s+function\s+(\w+)",
        ]

        in_function = False
        function_start = 0
        function_name = ""
        brace_count = 0

        for i, line in enumerate(lines):
            line.strip()

            # Check for function start
            if not in_function:
                for pattern in function_patterns:
                    match = re.search(pattern, line)
                    if match:
                        in_function = True
                        function_start = i
                        function_name = match.group(1) if match.groups() else "anonymous"
                        brace_count = 0
                        break

            if in_function:
                # Count braces to track function end
                brace_count += line.count("{") - line.count("}")

                # Function ends when braces are balanced
                if brace_count <= 0 and "{" in lines[function_start : i + 1]:
                    function_length = i - function_start + 1
                    if function_length > 50:  # Threshold for long function
                        smells.append(
                            {
                                "type": "long_functions",
                                "file": str(file_path.relative_to(self.workspace_root)),
                                "line": function_start + 1,
                                "severity": "medium",
                                "description": (
                                    f"Function '{function_name}' is {function_length} lines long"
                                ),
                                "suggestion": (
                                    "Consider breaking this function into smaller, more focused "
                                    "functions"
                                ),
                            }
                        )
                    in_function = False

        return smells

    def _detect_complex_conditionals(
        self, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """Detect complex conditional statements"""
        smells = []

        for i, line in enumerate(lines):
            # Count logical operators in conditional statements
            if re.search(r"\b(if|while|for)\s*\(", line):
                logical_ops = len(re.findall(r"(\&\&|\|\||!)", line))
                if logical_ops > 3:  # Threshold for complex conditional
                    smells.append(
                        {
                            "type": "complex_conditionals",
                            "file": str(file_path.relative_to(self.workspace_root)),
                            "line": i + 1,
                            "severity": "medium",
                            "description": (
                                f"Complex conditional with {logical_ops} logical operators"
                            ),
                            "suggestion": (
                                "Simplify conditional logic using early returns or extract complex "
                                "conditions into variables"
                            ),
                        }
                    )

        return smells

    def _detect_magic_numbers(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Detect magic numbers in JavaScript code"""
        smells = []

        # Pattern to find numeric literals (excluding common values)
        number_pattern = r"\b(?<![\w.])((?!0|1|2|10|100|1000)\d+(?:\.\d+)?)\b(?![\w.])"

        for i, line in enumerate(lines):
            # Skip comments and strings
            if re.match(r"^\s*(//|/\*|\*)", line.strip()):
                continue

            matches = re.finditer(number_pattern, line)
            for match in matches:
                number = match.group(0)
                if float(number) not in [0, 1, -1, 2, 10, 100]:
                    smells.append(
                        {
                            "type": "magic_numbers",
                            "file": str(file_path.relative_to(self.workspace_root)),
                            "line": i + 1,
                            "severity": "low",
                            "description": f"Magic number {number} found",
                            "suggestion": "Extract this to a named constant",
                        }
                    )

        return smells

    def _detect_duplicate_code(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Detect potential duplicate code blocks"""
        smells = []

        # Simple duplicate detection: look for identical consecutive lines
        consecutive_count = 1
        prev_line = ""

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and stripped == prev_line and len(stripped) > 20:
                consecutive_count += 1
            else:
                if consecutive_count >= 3:
                    smells.append(
                        {
                            "type": "duplicate_code",
                            "file": str(file_path.relative_to(self.workspace_root)),
                            "line": i - consecutive_count + 1,
                            "severity": "medium",
                            "description": f"Found {consecutive_count} consecutive identical lines",
                            "suggestion": "Extract duplicate code into a function or loop",
                        }
                    )
                consecutive_count = 1
                prev_line = stripped

        return smells

    def _detect_console_logs(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Detect console.log statements that should be removed in production"""
        smells = []

        for i, line in enumerate(lines):
            if re.search(r"\bconsole\.(log|debug|info|warn|error)", line):
                smells.append(
                    {
                        "type": "console_logs",
                        "file": str(file_path.relative_to(self.workspace_root)),
                        "line": i + 1,
                        "severity": "low",
                        "description": "Console log statement found",
                        "suggestion": (
                            "Remove console logs before production or use a proper logging library"
                        ),
                    }
                )

        return smells

    def _detect_var_usage(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Detect usage of 'var' keyword which should be replaced with 'let' or 'const'"""
        smells = []

        for i, line in enumerate(lines):
            if re.search(r"\bvar\s+\w+", line):
                smells.append(
                    {
                        "type": "var_usage",
                        "file": str(file_path.relative_to(self.workspace_root)),
                        "line": i + 1,
                        "severity": "low",
                        "description": "Usage of 'var' keyword found",
                        "suggestion": "Use 'let' or 'const' instead of 'var' for better scoping",
                    }
                )

        return smells

    def _detect_callback_hell(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Detect deeply nested callbacks"""
        smells = []

        nesting_level = 0
        max_nesting = 0
        callback_line = 0

        for i, line in enumerate(lines):
            # Look for callback patterns
            if re.search(r"function\s*\([^)]*\)\s*{|=>\s*{|\.\w+\s*\([^)]*function", line):
                if nesting_level == 0:
                    callback_line = i
                nesting_level += 1
                max_nesting = max(max_nesting, nesting_level)

            # Count braces to track nesting
            nesting_level += line.count("{") - line.count("}")
            nesting_level = max(0, nesting_level)

            if nesting_level == 0 and max_nesting > 3:
                smells.append(
                    {
                        "type": "callback_hell",
                        "file": str(file_path.relative_to(self.workspace_root)),
                        "line": callback_line + 1,
                        "severity": "high",
                        "description": f"Deeply nested callbacks (depth: {max_nesting})",
                        "suggestion": (
                            "Refactor using Promises, async/await, or break into separate functions"
                        ),
                    }
                )
                max_nesting = 0

        return smells

    def _get_smell_types_for_analysis(self, analysis_type: str) -> List[str]:
        """Get appropriate smell types based on analysis type"""
        base_smells = ["long_functions", "complex_conditionals", "magic_numbers", "console_logs"]

        if analysis_type == "quick":
            return base_smells
        elif analysis_type == "deep":
            return base_smells + [
                "duplicate_code",
                "var_usage",
                "callback_hell",
                "unused_variables",
                "missing_semicolons",
            ]
        elif analysis_type == "security":
            return base_smells + [
                "eval_usage",
                "innerHTML_usage",
                "unsafe_regex",
                "prototype_pollution",
            ]
        elif analysis_type == "performance":
            return base_smells + [
                "inefficient_loops",
                "memory_leaks",
                "dom_manipulation",
                "sync_operations",
            ]
        else:
            return base_smells


def is_javascript_file(file_path: Path) -> bool:
    """Check if a file is a JavaScript file"""
    return file_path.suffix.lower() in [".js", ".jsx", ".mjs", ".cjs"]
