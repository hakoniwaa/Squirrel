"""
Structural pattern detection - identifies structural code issues and patterns
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BasePatternDetector, DetectionContext, DetectionUtils
from ..constants import (
    CodeQualityThresholds,
    ConfidenceLevels,
    PatternDetectionConfig,
    SeverityLevels,
)
from . import utils

logger = logging.getLogger(__name__)


class StructuralPatternDetector(BasePatternDetector):
    """Detect structural patterns and issues in code"""

    def __init__(self, config: Optional[PatternDetectionConfig] = None):
        """Initialize structural pattern detector"""
        super().__init__()
        self.config = config or PatternDetectionConfig()

    def _load_patterns(self) -> Dict[str, Any]:
        """Load structural pattern detection configurations"""
        return {
            "naming_conventions": self._create_naming_pattern(),
            "deep_nesting": self._create_deep_nesting_pattern(),
            "long_methods": self._create_long_method_pattern(),
            "large_classes": self._create_large_class_pattern(),
            "complex_expressions": self._create_complex_expression_pattern(),
            "code_duplication": self._create_code_duplication_pattern(),
            "method_chaining": self._create_method_chaining_pattern(),
            "cyclomatic_complexity": self._create_cyclomatic_complexity_pattern(),
        }

    def _create_naming_pattern(self) -> Dict[str, Any]:
        """Create naming convention pattern configuration"""
        return {
            "indicators": [
                r"\b[a-z]+_[a-z_]+\b",  # snake_case
                r"\b[a-z][a-zA-Z]*[A-Z][a-zA-Z]*\b",  # camelCase
                r"\b[A-Z][A-Z_]+\b",  # CONSTANTS
                r"\bclass\s+([A-Z][a-zA-Z]*)\b",  # PascalCase classes
            ],
            "description": "Naming convention analysis",
            "suggestion": "Use consistent naming conventions throughout the codebase",
            "severity": SeverityLevels.LOW,
            "threshold": PatternDetectionConfig.NAMING_CONVENTION_THRESHOLD,
        }

    def _create_deep_nesting_pattern(self) -> Dict[str, Any]:
        """Create deep nesting pattern configuration"""
        return {
            "indicators": [
                r"^\s{16,}\w+",  # 4+ levels of indentation (assuming 4 spaces)
                r"if.*:.*if.*:.*if.*:",  # Nested if statements
                r"for.*:.*for.*:.*for.*:",  # Nested loops
                r"try.*:.*try.*:",  # Nested try blocks
            ],
            "description": "Deep nesting detected - code structure is too complex",
            "suggestion": (
                "Consider extracting nested code into separate methods or using early returns"
            ),
            "severity": SeverityLevels.MEDIUM,
            "threshold": CodeQualityThresholds.NESTING_DEPTH,
        }

    def _create_long_method_pattern(self) -> Dict[str, Any]:
        """Create long method pattern configuration"""
        return {
            "indicators": [
                r"def\s+\w+\(",
                r"^\s+\w+",  # Indented lines (method content)
            ],
            "description": "Long method detected - method is too complex",
            "suggestion": "Break down long methods into smaller, focused methods",
            "severity": SeverityLevels.MEDIUM,
            "line_threshold": CodeQualityThresholds.FUNCTION_LENGTH,
        }

    def _create_large_class_pattern(self) -> Dict[str, Any]:
        """Create large class pattern configuration"""
        return {
            "indicators": [
                r"class\s+\w+",
                r"def\s+\w+\(",  # Methods in class
                r"self\.\w+",  # Instance variables
            ],
            "description": "Large class detected - class has too many responsibilities",
            "suggestion": "Break down large classes into smaller, focused classes",
            "severity": SeverityLevels.HIGH,
            "line_threshold": CodeQualityThresholds.CLASS_SIZE,
        }

    def _create_complex_expression_pattern(self) -> Dict[str, Any]:
        """Create complex expression pattern configuration"""
        return {
            "indicators": [
                r"\([^)]*\([^)]*\([^)]*\)",  # Triple nested parentheses
                r"\w+\.\w+\.\w+\.\w+\.",  # Long method chains
                r"[&|]{2}.*[&|]{2}.*[&|]{2}",  # Complex boolean expressions
                r"\+.*\+.*\+.*\+",  # Long concatenations
            ],
            "description": "Complex expressions detected - expressions are hard to understand",
            "suggestion": "Break down complex expressions into intermediate variables",
            "severity": SeverityLevels.LOW,
        }

    def _create_code_duplication_pattern(self) -> Dict[str, Any]:
        """Create code duplication pattern configuration"""
        return {
            "indicators": [
                r"def\s+(\w+).*:\s*.*def\s+\1",  # Duplicate method names (simplified)
                r"class\s+(\w+).*:\s*.*class\s+\1",  # Duplicate class names
                r"(\w{10,}).*\1",  # Repeated long strings/identifiers
            ],
            "description": "Potential code duplication detected",
            "suggestion": "Extract common code into reusable functions or modules",
            "severity": SeverityLevels.MEDIUM,
        }

    def _create_method_chaining_pattern(self) -> Dict[str, Any]:
        """Create method chaining pattern configuration"""
        return {
            "indicators": [
                r"\w+\.\w+\.\w+\.\w+\.\w+",  # Long method chains
                r"\..*\..*\..*\.",  # Dot notation chains
            ],
            "description": "Long method chaining detected",
            "suggestion": "Consider breaking method chains or using intermediate variables",
            "severity": SeverityLevels.LOW,
        }

    def _create_cyclomatic_complexity_pattern(self) -> Dict[str, Any]:
        """Create cyclomatic complexity pattern configuration"""
        return {
            "indicators": [
                r"\bif\b",
                r"\belif\b",
                r"\bwhile\b",
                r"\bfor\b",
                r"\band\b",
                r"\bor\b",
                r"\btry\b",
                r"\bexcept\b",
            ],
            "description": "High cyclomatic complexity detected",
            "suggestion": "Reduce complexity by extracting methods or simplifying logic",
            "severity": SeverityLevels.MEDIUM,
            "complexity_threshold": CodeQualityThresholds.CYCLOMATIC_COMPLEXITY,
        }

    def detect_patterns(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """Detect structural patterns in code"""
        patterns = []

        for pattern_name, pattern_config in self._patterns.items():
            context = DetectionContext(content=content, lines=lines, file_path=file_path)

            matches = self._find_structural_patterns(context, pattern_name, pattern_config)
            patterns.extend(matches)

        return patterns

    def _find_structural_patterns(
        self, context: DetectionContext, pattern_name: str, pattern_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find structural pattern matches with special handling"""
        if pattern_name == "naming_conventions":
            return self._detect_naming_violations(context, pattern_config)
        elif pattern_name == "deep_nesting":
            return self._detect_deep_nesting(context, pattern_config)
        elif pattern_name == "long_methods":
            return self._detect_long_methods(context, pattern_config)
        elif pattern_name == "large_classes":
            return self._detect_large_classes(context, pattern_config)
        elif pattern_name == "cyclomatic_complexity":
            return self._detect_cyclomatic_complexity(context, pattern_config)
        else:
            return self._find_generic_patterns(context, pattern_name, pattern_config)

    def _detect_naming_violations(
        self, context: DetectionContext, pattern_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect naming convention violations"""
        patterns: List[Dict[str, Any]] = []

        snake_case_count = len(re.findall(r"\b[a-z]+_[a-z_]+\b", context.content))
        camel_case_count = len(re.findall(r"\b[a-z][a-zA-Z]*[A-Z][a-zA-Z]*\b", context.content))

        threshold = pattern_config.get("threshold", 5)

        if snake_case_count > threshold and camel_case_count > threshold:
            patterns.append(
                self._create_pattern_result(
                    context,
                    "mixed_naming_conventions",
                    "structural_issue",
                    {
                        "indicator_matches": snake_case_count + camel_case_count,
                        "matched_lines": [1],
                    },
                    pattern_config,
                    ConfidenceLevels.MEDIUM,
                )
            )

        return patterns

    def _detect_deep_nesting(
        self, context: DetectionContext, pattern_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect deeply nested code structures"""
        patterns: List[Dict[str, Any]] = []
        threshold = pattern_config.get("threshold", CodeQualityThresholds.NESTING_DEPTH)

        # Guard against None context.lines
        if not context.lines:
            return patterns

        for i, line in enumerate(context.lines):
            indent_level = (len(line) - len(line.lstrip())) // 4  # Assuming 4-space indents

            if indent_level > threshold:
                patterns.append(
                    self._create_pattern_result(
                        context,
                        "deep_nesting",
                        "structural_issue",
                        {"indicator_matches": 1, "matched_lines": [i + 1]},
                        pattern_config,
                        ConfidenceLevels.HIGH,
                    )
                )

        return patterns

    def _detect_long_methods(
        self, context: DetectionContext, pattern_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect long methods"""
        patterns: List[Dict[str, Any]] = []
        threshold = pattern_config.get("line_threshold", CodeQualityThresholds.FUNCTION_LENGTH)

        # Guard against None context.lines
        if not context.lines:
            return patterns

        method_pattern = re.compile(r"^\s*def\s+(\w+)\s*\(", re.MULTILINE)

        for match in method_pattern.finditer(context.content):
            method_name = match.group(1)
            start_line = context.content[: match.start()].count("\n") + 1

            method_lines = DetectionUtils.extract_function_lines(context.lines, start_line - 1)

            if method_lines and len(method_lines) > threshold:
                description = f'Long method "{method_name}" detected ({len(method_lines)} lines)'
                patterns.append(
                    self._create_pattern_result(
                        context,
                        "long_method",
                        "structural_issue",
                        {"indicator_matches": len(method_lines), "matched_lines": [start_line]},
                        {
                            **pattern_config,
                            "description": description,
                        },
                        ConfidenceLevels.HIGH,
                    )
                )

        return patterns

    def _detect_large_classes(
        self, context: DetectionContext, pattern_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect large classes"""
        patterns: List[Dict[str, Any]] = []
        threshold = pattern_config.get("line_threshold", CodeQualityThresholds.CLASS_SIZE)

        # Guard against None context.lines
        if not context.lines:
            return patterns

        class_pattern = re.compile(r"^\s*class\s+(\w+)", re.MULTILINE)

        for match in class_pattern.finditer(context.content):
            class_name = match.group(1)
            start_line = context.content[: match.start()].count("\n") + 1

            class_lines = DetectionUtils.extract_class_lines(context.lines, start_line - 1)

            if class_lines and len(class_lines) > threshold:
                description = f'Large class "{class_name}" detected ({len(class_lines)} lines)'
                patterns.append(
                    self._create_pattern_result(
                        context,
                        "large_class",
                        "structural_issue",
                        {"indicator_matches": len(class_lines), "matched_lines": [start_line]},
                        {
                            **pattern_config,
                            "description": description,
                        },
                        ConfidenceLevels.HIGH,
                    )
                )

        return patterns

    def _detect_cyclomatic_complexity(
        self, context: DetectionContext, pattern_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect high cyclomatic complexity"""
        patterns: List[Dict[str, Any]] = []
        threshold = pattern_config.get(
            "complexity_threshold", CodeQualityThresholds.CYCLOMATIC_COMPLEXITY
        )

        # Guard against None context.lines
        if not context.lines:
            return patterns

        # Simple cyclomatic complexity calculation
        complexity_indicators = pattern_config["indicators"]

        method_pattern = re.compile(r"^\s*def\s+(\w+)\s*\(", re.MULTILINE)

        for match in method_pattern.finditer(context.content):
            method_name = match.group(1)
            start_line = context.content[: match.start()].count("\n")
            method_lines = DetectionUtils.extract_function_lines(context.lines, start_line)

            if not method_lines:
                continue

            method_content = "\n".join(method_lines)

            complexity = 1  # Base complexity
            for indicator in complexity_indicators:
                complexity += len(re.findall(indicator, method_content))

            if complexity > threshold:
                description = (
                    f'High cyclomatic complexity in "{method_name}" (complexity: {complexity})'
                )
                patterns.append(
                    self._create_pattern_result(
                        context,
                        "high_cyclomatic_complexity",
                        "structural_issue",
                        {"indicator_matches": complexity, "matched_lines": [start_line + 1]},
                        {
                            **pattern_config,
                            "description": description,
                        },
                        ConfidenceLevels.HIGH,
                    )
                )

        return patterns

    def _find_generic_patterns(
        self, context: DetectionContext, pattern_name: str, pattern_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find generic structural patterns"""
        matches = []
        indicators = pattern_config["indicators"]

        match_data = self._collect_indicator_matches(context.content, indicators)

        if match_data["indicator_matches"] > 0:
            confidence = self._calculate_structural_confidence(match_data, indicators)

            if confidence >= ConfidenceLevels.LOW:
                pattern_dict = self._create_pattern_result(
                    context,
                    pattern_name,
                    "structural_issue",
                    match_data,
                    pattern_config,
                    confidence,
                )
                matches.append(pattern_dict)

        return matches

    def _collect_indicator_matches(self, content: str, indicators: List[str]) -> Dict[str, Any]:
        """Collect matches for all indicators"""
        indicator_matches = 0
        matched_lines = []

        for indicator in indicators:
            pattern_matches = list(re.finditer(indicator, content, re.MULTILINE))
            indicator_matches += len(pattern_matches)

            for match in pattern_matches:
                line_num = content[: match.start()].count("\n") + 1
                matched_lines.append(line_num)

        return {"indicator_matches": indicator_matches, "matched_lines": matched_lines}

    def _calculate_structural_confidence(
        self, match_data: Dict[str, Any], indicators: List[str]
    ) -> float:
        """Calculate confidence score for structural pattern match"""
        indicator_matches = int(match_data["indicator_matches"])
        return min(indicator_matches / len(indicators), 1.0)

    def _create_pattern_result(
        self,
        context: DetectionContext,
        pattern_name: str,
        pattern_type: str,
        match_data: Dict[str, Any],
        pattern_config: Dict[str, Any],
        confidence: float,
    ) -> Dict[str, Any]:
        """Create pattern result from context and match data"""
        matched_lines = match_data["matched_lines"]
        start_line = min(matched_lines) if matched_lines else 1
        end_line = (
            max(matched_lines) if matched_lines else (len(context.lines) if context.lines else 1)
        )

        try:
            relative_path = str(context.file_path.relative_to(Path.cwd()))
        except ValueError:
            relative_path = str(context.file_path)

        return {
            "pattern_name": pattern_name,
            "pattern_type": pattern_type,
            "file": relative_path,
            "start_line": start_line,
            "end_line": end_line,
            "confidence": confidence,
            "description": pattern_config["description"],
            "suggestion": pattern_config["suggestion"],
            "severity": pattern_config.get(
                "severity", self._get_pattern_severity(pattern_type, confidence)
            ),
            "matches_found": match_data["indicator_matches"],
        }

    def _get_pattern_severity(self, _: str, confidence: float) -> str:
        """Determine severity based on pattern type and confidence"""
        if confidence >= ConfidenceLevels.HIGH:
            return SeverityLevels.MEDIUM
        elif confidence >= ConfidenceLevels.MEDIUM:
            return SeverityLevels.LOW
        else:
            return SeverityLevels.LOW

    def _create_issue_from_match(
        self,
        context: DetectionContext,
        pattern_name: str,
        pattern_config: Any,
        match: re.Match,
        confidence: float,
    ) -> Dict[str, Any]:
        """Create issue dictionary from pattern match.

        Args:
            context: Detection context
            pattern_name: Name of the matched pattern
            pattern_config: Pattern configuration (dict or PatternConfig)
            match: Regex match object
            confidence: Confidence score

        Returns:
            Issue dictionary compatible with the analysis system
        """
        # Method removed; use utils.create_pattern_issue_from_match instead
        return {}

    def _detect_package_structure(self, tree: ast.AST, lines: List[str]) -> List[Dict[str, Any]]:
        """Detect good package/module structure patterns"""
        patterns = []

        # Handle None lines parameter
        if lines is None:
            return patterns

        # Analyze imports and module structure
        import_count = 0
        has_main_guard = False

        for _, line in enumerate(lines):
            if line.strip().startswith(("import ", "from ")):
                import_count += 1
            elif 'if __name__ == "__main__"' in line:
                has_main_guard = True

        # Check for well-structured modules
        for node in ast.walk(tree):
            if isinstance(node, ast.Module):
                # Analyze module structure
                has_docstring = ast.get_docstring(node) is not None

                if has_docstring and import_count > 0:
                    snippet = utils.get_code_snippet(lines, 1, 5) if lines else "N/A"

                    patterns.append(
                        {
                            "type": "well_structured_module",
                            "confidence": 0.8,
                            "line": 1,
                            "details": {
                                "has_docstring": has_docstring,
                                "import_count": import_count,
                                "has_main_guard": has_main_guard,
                                "snippet": snippet,
                            },
                        }
                    )

        return patterns

    def _extract_function_lines(
        self, lines: List[str], func_node: ast.FunctionDef
    ) -> Optional[List[str]]:
        """Extract lines that belong to a function with null safety"""
        if not lines:
            return None

        try:
            start_line = func_node.lineno - 1  # Convert to 0-based indexing

            # Find the end of the function
            end_line = len(lines)
            func_indent = self._get_indentation_level(lines[start_line])

            for i in range(start_line + 1, len(lines)):
                line_indent = self._get_indentation_level(lines[i])
                if line_indent <= func_indent and lines[i].strip():
                    end_line = i
                    break

            return lines[start_line:end_line]
        except (IndexError, AttributeError, ValueError) as e:
            logger.debug("Failed to extract function lines: %s", e)
            return None

    def _extract_class_lines(
        self, lines: List[str], class_node: ast.ClassDef
    ) -> Optional[List[str]]:
        """Extract lines that belong to a class with null safety"""
        if not lines:
            return None

        try:
            start_line = class_node.lineno - 1  # Convert to 0-based indexing

            # Find the end of the class
            end_line = len(lines)
            class_indent = self._get_indentation_level(lines[start_line])

            for i in range(start_line + 1, len(lines)):
                line_indent = self._get_indentation_level(lines[i])
                if line_indent <= class_indent and lines[i].strip():
                    # Check if this is another top-level definition
                    stripped = lines[i].strip()
                    if stripped.startswith(("class ", "def ", "async def ")):
                        end_line = i
                        break

            return lines[start_line:end_line]
        except (IndexError, AttributeError, ValueError) as e:
            logger.debug("Failed to extract class lines: %s", e)
            return None

    def _get_indentation_level(self, line: str) -> int:
        """Get the indentation level of a line"""
        return len(line) - len(line.lstrip())

    def _get_code_snippet(self, lines: List[str], line_number: int, context_lines: int = 2) -> str:
        """Get a code snippet around the specified line number with null safety"""
        # Method removed; use utils.get_code_snippet instead
        return ""
