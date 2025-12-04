"""
Structural code smell detection - focuses on code structure issues
"""

import re
from typing import Any, Dict, List

from ..base import BaseRuleDetector, DetectionContext, DetectionUtils
from ..constants import CodeQualityThresholds, SeverityLevels
from .utils import create_code_smell_issue


class StructuralSmellDetector(BaseRuleDetector):
    """Detect structural code smells like long functions, large classes, deep nesting"""

    def _load_patterns(self) -> Dict[str, Any]:
        """Load structural analysis patterns - not used for rule-based detector"""
        return {}

    def _load_rules(self) -> Dict[str, Any]:
        """Load structural smell detection rules"""
        return {
            "long_functions": {
                "threshold": CodeQualityThresholds.FUNCTION_LENGTH,
                "severity": SeverityLevels.MEDIUM,
                "description": "Function exceeds recommended length",
                "suggestion": "Consider breaking down into smaller, more focused functions",
            },
            "god_classes": {
                "threshold": CodeQualityThresholds.CLASS_SIZE,
                "severity": SeverityLevels.HIGH,
                "description": "Class is too large (God Object anti-pattern)",
                "suggestion": (
                    "Break down large class into smaller, focused classes using "
                    "Single Responsibility Principle"
                ),
            },
            "deep_nesting": {
                "threshold": CodeQualityThresholds.NESTING_DEPTH,
                "severity": SeverityLevels.MEDIUM,
                "description": "Deep nesting detected",
                "suggestion": (
                    "Consider extracting nested logic into separate methods or using early returns"
                ),
            },
            "long_lines": {
                "threshold": CodeQualityThresholds.LINE_LENGTH,
                "severity": SeverityLevels.LOW,
                "description": "Line exceeds recommended length",
                "suggestion": "Break long lines for better readability",
            },
            "inconsistent_indentation": {
                "threshold": 0,
                "severity": SeverityLevels.LOW,
                "description": "Inconsistent indentation detected",
                "suggestion": "Use consistent indentation throughout the file (preferably spaces)",
            },
        }

    def _check_rule(
        self, context: DetectionContext, rule_name: str, rule_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check structural rules against context"""
        if rule_name == "long_functions":
            return self._detect_long_functions(context, rule_config)
        elif rule_name == "god_classes":
            return self._detect_god_classes(context, rule_config)
        elif rule_name == "deep_nesting":
            return self._detect_deep_nesting(context, rule_config)
        elif rule_name == "long_lines":
            return self._detect_long_lines(context, rule_config)
        elif rule_name == "inconsistent_indentation":
            return self._detect_inconsistent_indentation(context, rule_config)

        return []

    def _detect_long_functions(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect functions that are too long"""
        issues: List[Dict[str, Any]] = []
        threshold = config["threshold"]

        # Guard against None context.lines
        if not context.lines:
            return issues

        function_pattern = re.compile(r"^\s*(def|function|async\s+def)\s+(\w+)", re.MULTILINE)

        for match in function_pattern.finditer(context.content):
            func_start = context.content[: match.start()].count("\n")
            func_name = match.group(2)

            func_lines = DetectionUtils.extract_function_lines(context.lines, func_start)

            # Guard against None return from extract_function_lines
            if not func_lines:
                continue

            if len(func_lines) > threshold:
                issues.append(
                    create_code_smell_issue(
                        "long_functions",
                        context,
                        func_start + 1,
                        (
                            f"Function '{func_name}' is {len(func_lines)} lines long "
                            f"(threshold: {threshold})"
                        ),
                        config["suggestion"],
                        config["severity"],
                    )
                )

        return issues

    def _detect_god_classes(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect classes that are too large (God Object anti-pattern)"""
        issues: List[Dict[str, Any]] = []
        threshold = config["threshold"]

        # Guard against None context.lines
        if not context.lines:
            return issues

        class_pattern = re.compile(r"^class\s+(\w+)", re.MULTILINE)

        for match in class_pattern.finditer(context.content):
            class_start = context.content[: match.start()].count("\n")
            class_name = match.group(1)

            class_lines = DetectionUtils.extract_class_lines(context.lines, class_start)

            # Guard against None return from extract_class_lines
            if not class_lines:
                continue

            if len(class_lines) > threshold:
                issues.append(
                    create_code_smell_issue(
                        "god_classes",
                        context,
                        class_start + 1,
                        (
                            f"Class '{class_name}' is {len(class_lines)} lines long "
                            f"(threshold: {threshold})"
                        ),
                        config["suggestion"],
                        config["severity"],
                    )
                )

        return issues

    def _detect_deep_nesting(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect deeply nested code blocks"""
        issues: List[Dict[str, Any]] = []
        threshold = config["threshold"]
        indent_size = 4  # Standard Python indentation

        # Guard against None context.lines
        if not context.lines:
            return issues

        for i, line in enumerate(context.lines):
            if not line.strip():
                continue

            indent_level = DetectionUtils.calculate_indentation_level(line, indent_size)

            if indent_level > threshold:
                issues.append(
                    create_code_smell_issue(
                        "deep_nesting",
                        context,
                        i + 1,
                        f"Deep nesting detected (level {indent_level}, threshold: {threshold})",
                        config["suggestion"],
                        config["severity"],
                    )
                )

        return issues

    def _detect_long_lines(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect lines that are too long"""
        issues: List[Dict[str, Any]] = []
        threshold = config["threshold"]

        # Guard against None context.lines
        if not context.lines:
            return issues

        for i, line in enumerate(context.lines):
            if len(line) > threshold:
                issues.append(
                    create_code_smell_issue(
                        "long_lines",
                        context,
                        i + 1,
                        f"Line too long ({len(line)} characters, threshold: {threshold})",
                        config["suggestion"],
                        config["severity"],
                    )
                )

        return issues

    def _detect_inconsistent_indentation(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect inconsistent indentation"""
        issues: List[Dict[str, Any]] = []
        indent_patterns = set()

        # Guard against None context.lines
        if not context.lines:
            return issues

        for line in context.lines:
            if line.strip():  # Skip empty lines
                leading_space = len(line) - len(line.lstrip())
                if leading_space > 0:
                    indent_char = "tab" if line[0] == "\t" else "space"
                    indent_patterns.add(indent_char)

        if len(indent_patterns) > 1:
            issues.append(
                create_code_smell_issue(
                    "inconsistent_indentation",
                    context,
                    1,
                    f"Inconsistent indentation: using both {' and '.join(indent_patterns)}",
                    config["suggestion"],
                    config["severity"],
                )
            )

        return issues
