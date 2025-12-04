"""
Anti-pattern detection - identifies problematic code patterns to avoid
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..base import BasePatternDetector, DetectionContext, DetectionUtils
from ..constants import (
    CodeQualityThresholds,
    ConfidenceLevels,
    PatternDetectionConfig,
    SeverityLevels,
)
from . import utils

logger = logging.getLogger(__name__)


class AntiPatternDetector(BasePatternDetector):
    """Detect anti-patterns and problematic code structures"""

    def __init__(self, config: Optional[PatternDetectionConfig] = None):
        """Initialize with pattern configuration"""
        super().__init__()
        self.config = config or PatternDetectionConfig()

    def _load_patterns(self) -> Dict[str, Any]:
        """Load anti-pattern detection configurations"""
        return {
            "god_object": self._create_god_object_pattern(),
            "spaghetti_code": self._create_spaghetti_code_pattern(),
            "magic_numbers": self._create_magic_numbers_pattern(),
            "long_method": self._create_long_method_pattern(),
            "data_class": self._create_data_class_pattern(),
            "feature_envy": self._create_feature_envy_pattern(),
            "primitive_obsession": self._create_primitive_obsession_pattern(),
            "dead_code": self._create_dead_code_pattern(),
        }

    def _create_god_object_pattern(self) -> Dict[str, Any]:
        """Create god object anti-pattern configuration"""
        return {
            "indicators": [r"class\s+\w+.*:", r"def\s+\w+\(", r"self\.\w+\s*="],
            "description": "God Object anti-pattern - class is too large",
            "suggestion": "Break down large class into smaller, focused classes",
            "severity": SeverityLevels.HIGH,
            "line_threshold": CodeQualityThresholds.CLASS_SIZE,
        }

    def _create_spaghetti_code_pattern(self) -> Dict[str, Any]:
        """Create spaghetti code anti-pattern configuration"""
        return {
            "indicators": [r"goto\s+\w+", r"break\s+\w+", r"continue\s+\w+"],
            "description": "Spaghetti code anti-pattern detected",
            "suggestion": "Restructure code to improve readability and maintainability",
            "severity": SeverityLevels.MEDIUM,
        }

    def _create_magic_numbers_pattern(self) -> Dict[str, Any]:
        """Create magic numbers anti-pattern configuration"""
        return {
            "indicators": [rf"\b\d{{{CodeQualityThresholds.MAGIC_NUMBER_DIGITS},}}\b"],
            "description": "Magic numbers detected",
            "suggestion": "Replace magic numbers with named constants",
            "severity": SeverityLevels.LOW,
        }

    def _create_long_method_pattern(self) -> Dict[str, Any]:
        """Create long method anti-pattern configuration"""
        return {
            "indicators": [r"def\s+\w+\("],
            "description": "Long method anti-pattern detected",
            "suggestion": "Break down long methods into smaller, focused methods",
            "severity": SeverityLevels.MEDIUM,
            "line_threshold": CodeQualityThresholds.FUNCTION_LENGTH,
        }

    def _create_data_class_pattern(self) -> Dict[str, Any]:
        """Create data class anti-pattern configuration"""
        return {
            "indicators": [r"def\s+get_\w+\(", r"def\s+set_\w+\(", r"@property"],
            "description": "Data class anti-pattern - class with only getters/setters",
            "suggestion": "Add meaningful behavior or use dataclasses for simple containers",
            "severity": SeverityLevels.LOW,
        }

    def _create_feature_envy_pattern(self) -> Dict[str, Any]:
        """Create feature envy anti-pattern configuration"""
        return {
            "indicators": [r"other\.\w+", r"obj\.\w+\(\)", r"self\.\w+\.\w+\.\w+"],
            "description": "Feature envy - method uses another class more than its own",
            "suggestion": "Move method to the class it envies or reduce coupling",
            "severity": SeverityLevels.MEDIUM,
        }

    def _create_primitive_obsession_pattern(self) -> Dict[str, Any]:
        """Create primitive obsession anti-pattern configuration"""
        return {
            "indicators": [r"str\(", r"int\(", r"float\(", r"bool\("],
            "description": "Primitive obsession - overuse of primitive types",
            "suggestion": "Consider creating domain-specific classes",
            "severity": SeverityLevels.LOW,
        }

    def _create_dead_code_pattern(self) -> Dict[str, Any]:
        """Create dead code anti-pattern configuration"""
        return {
            "indicators": [r"#\s*TODO:.*remove", r"if\s+False\s*:", r"pass\s*#.*unused"],
            "description": "Dead code detected - unused or unreachable code",
            "suggestion": "Remove dead code to improve maintainability",
            "severity": SeverityLevels.LOW,
        }

    def detect_patterns(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """Detect anti-patterns in code"""
        patterns = []

        for pattern_name, pattern_config in self._patterns.items():
            context = DetectionContext(content=content, lines=lines, file_path=file_path)

            matches = self._find_anti_pattern_matches(context, pattern_name, pattern_config)
            patterns.extend(matches)

        return patterns

    def _find_anti_pattern_matches(
        self, context: DetectionContext, pattern_name: str, pattern_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find matches for anti-patterns with special handling"""
        matches = []
        indicators = pattern_config["indicators"]

        match_data = self._collect_indicator_matches(context.content, indicators)

        if match_data["indicator_matches"] > 0:
            confidence = self._calculate_anti_pattern_confidence(
                context, pattern_name, pattern_config, match_data
            )

            if confidence >= ConfidenceLevels.LOW:
                pattern_dict = self._create_pattern_result(
                    context, pattern_name, "anti_pattern", match_data, pattern_config, confidence
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

    def _calculate_anti_pattern_confidence(
        self,
        context: DetectionContext,
        pattern_name: str,
        pattern_config: Dict[str, Any],
        match_data: Dict[str, Any],
    ) -> float:
        """Calculate confidence for anti-pattern matches"""
        confidence = float(
            min(match_data["indicator_matches"] / len(pattern_config["indicators"]), 1.0)
        )
        confidence = float(
            max(confidence, ConfidenceLevels.MEDIUM)
        )  # Anti-patterns get medium baseline

        # Check for line threshold if specified
        line_threshold = pattern_config.get("line_threshold")
        if line_threshold is not None:
            confidence = self._check_line_threshold_patterns(
                context, pattern_name, line_threshold, confidence
            )

        return confidence

    def _check_line_threshold_patterns(
        self, context: DetectionContext, pattern_name: str, threshold: int, base_confidence: float
    ) -> float:
        """Check patterns that depend on line count thresholds"""
        if pattern_name == "god_object":
            return self._check_god_object_threshold(context, threshold, base_confidence)
        elif pattern_name == "long_method":
            return self._check_long_method_threshold(context, threshold, base_confidence)

        return base_confidence

    def _check_god_object_threshold(
        self, context: DetectionContext, threshold: int, base_confidence: float
    ) -> float:
        """Check god object pattern against line threshold"""
        if context.lines is None:
            return base_confidence

        class_pattern = re.compile(r"^\s*class\s+\w+", re.MULTILINE)
        for match in class_pattern.finditer(context.content):
            start_line = context.content[: match.start()].count("\n")
            class_lines = DetectionUtils.extract_class_lines(context.lines, start_line)
            if len(class_lines) > threshold:
                return ConfidenceLevels.HIGH
        return base_confidence

    def _check_long_method_threshold(
        self, context: DetectionContext, threshold: int, base_confidence: float
    ) -> float:
        """Check long method pattern against line threshold"""
        if context.lines is None:
            return base_confidence

        method_pattern = re.compile(r"^\s*def\s+\w+\s*\(", re.MULTILINE)
        for match in method_pattern.finditer(context.content):
            start_line = context.content[: match.start()].count("\n")
            method_lines = DetectionUtils.extract_function_lines(context.lines, start_line)
            if len(method_lines) > threshold:
                return ConfidenceLevels.HIGH
        return base_confidence

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

    def _get_pattern_severity(self, pattern_type: str, confidence: float) -> str:
        """Determine severity based on pattern type and confidence"""
        if confidence >= ConfidenceLevels.HIGH:
            return SeverityLevels.HIGH
        elif confidence >= ConfidenceLevels.MEDIUM:
            return SeverityLevels.MEDIUM
        else:
            return SeverityLevels.LOW

    def _create_issue_from_match(
        self,
        context: DetectionContext,
        pattern_name: str,
        pattern_config: Any,
        match: re.Match,
        confidence: float,
    ):
        # Method removed; use utils.create_pattern_issue_from_match instead
        return {}

    def _detect_large_classes(self, tree: ast.AST, lines: List[str]) -> List[Dict[str, Any]]:
        """Detect classes that are too large"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Handle None lines parameter
                if lines is None:
                    continue

                class_lines = self._extract_class_lines(lines, node)
                if class_lines is None:
                    continue

                class_size = len(class_lines)
                # Use a reasonable default if the config doesn't have the attribute
                max_class_lines = getattr(self.config, "MAX_CLASS_LINES", 100)
                if class_size > max_class_lines:
                    issues.append(
                        {
                            "type": "large_class",
                            "severity": "warning",
                            "message": f"Class '{node.name}' is too large ({class_size} lines)",
                            "line": node.lineno,
                            "details": {
                                "class_name": node.name,
                                "line_count": class_size,
                                "max_allowed": max_class_lines,
                            },
                        }
                    )
        return issues

    def _detect_long_methods(self, tree: ast.AST, lines: List[str]) -> List[Dict[str, Any]]:
        """Detect methods that are too long"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Handle None lines parameter
                if lines is None:
                    continue

                method_lines = self._extract_function_lines(lines, node)
                if method_lines is None:
                    continue

                method_size = len(method_lines)
                # Use a reasonable default if the config doesn't have the attribute
                max_method_lines = getattr(self.config, "MAX_METHOD_LINES", 30)
                if method_size > max_method_lines:
                    issues.append(
                        {
                            "type": "long_method",
                            "severity": "warning",
                            "message": f"Method '{node.name}' is too long ({method_size} lines)",
                            "line": node.lineno,
                            "details": {
                                "method_name": node.name,
                                "line_count": method_size,
                                "max_allowed": max_method_lines,
                            },
                        }
                    )
        return issues

    def _detect_complex_conditionals(self, tree: ast.AST, lines: List[str]) -> List[Dict[str, Any]]:
        """Detect overly complex conditional statements"""
        issues = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While)):
                # Handle None lines parameter
                if lines is None:
                    continue

                complexity = self._calculate_conditional_complexity(node)
                max_complexity = getattr(self.config, "MAX_CONDITIONAL_COMPLEXITY", 5)
                if complexity > max_complexity:
                    # Get code snippet safely
                    snippet = utils.get_code_snippet(lines, node.lineno, 3) if lines else "N/A"

                    issues.append(
                        {
                            "type": "complex_conditional",
                            "severity": "warning",
                            "message": (
                                f"Conditional statement is too complex "
                                f"(complexity: {complexity})"
                            ),
                            "line": node.lineno,
                            "details": {
                                "complexity": complexity,
                                "max_allowed": max_complexity,
                                "snippet": snippet,
                            },
                        }
                    )
        return issues

    def _calculate_conditional_complexity(self, node: ast.AST) -> int:
        """Calculate complexity of a conditional statement"""
        complexity = 1  # Base complexity

        # Count logical operators (and, or)
        for child in ast.walk(node):
            if isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.Compare):
                # Multiple comparisons add complexity
                complexity += len(child.ops)

        return complexity

    def _extract_class_lines(
        self, lines: List[str], class_node: ast.ClassDef
    ) -> Optional[List[str]]:
        """Extract lines that belong to a class"""
        if not lines:
            return None

        try:
            start_line = class_node.lineno - 1  # Convert to 0-based indexing

            # Find the end of the class by looking for the next class/function
            # at the same indentation level
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
        except Exception as e:
            logger.debug(f"Failed to extract class lines: {e}")
            return None

    def _extract_function_lines(
        self, lines: List[str], func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> Optional[List[str]]:
        """Extract lines that belong to a function"""
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
        except Exception as e:
            logger.debug(f"Failed to extract function lines: {e}")
            return None

    def _get_indentation_level(self, line: str) -> int:
        """Get the indentation level of a line"""
        return len(line) - len(line.lstrip())

    def _get_code_snippet(self, lines: List[str], line_number: int, context_lines: int = 2) -> str:
        # Method removed; use utils.get_code_snippet instead
        return ""
