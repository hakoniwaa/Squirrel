"""
Complexity code smell detection - focuses on complexity-related issues
"""

import re
from typing import Any, Dict, List

from ..base import BaseRuleDetector, DetectionContext, DetectionUtils
from ..constants import CodeQualityThresholds, RegexPatterns, SeverityLevels
from .utils import create_code_smell_issue


class ComplexitySmellDetector(BaseRuleDetector):
    """Detect complexity-related code smells like complex conditionals, parameter lists"""

    def _load_patterns(self) -> Dict[str, Any]:
        """Load complexity analysis patterns - not used for rule-based detector"""
        return {}

    def _load_rules(self) -> Dict[str, Any]:
        """Load complexity smell detection rules"""
        return {
            "complex_conditionals": {
                "threshold": CodeQualityThresholds.CONDITIONAL_COMPLEXITY,
                "severity": SeverityLevels.MEDIUM,
                "description": "Complex conditional statement detected",
                "suggestion": (
                    "Consider breaking complex conditions into smaller, named boolean variables"
                ),
            },
            "long_parameter_list": {
                "threshold": CodeQualityThresholds.PARAMETER_COUNT,
                "severity": SeverityLevels.MEDIUM,
                "description": "Function has too many parameters",
                "suggestion": (
                    "Consider using a parameter object or breaking function into smaller functions"
                ),
            },
            "primitive_obsession": {
                "threshold": CodeQualityThresholds.PRIMITIVE_OBSESSION_COUNT,
                "severity": SeverityLevels.MEDIUM,
                "description": "Excessive use of primitive types detected",
                "suggestion": (
                    "Consider creating domain-specific classes instead of using primitive types"
                ),
            },
            "high_cyclomatic_complexity": {
                "threshold": CodeQualityThresholds.CYCLOMATIC_COMPLEXITY,
                "severity": SeverityLevels.HIGH,
                "description": "High cyclomatic complexity detected",
                "suggestion": "Break down complex method into smaller, simpler methods",
            },
            "excessive_method_calls": {
                "threshold": CodeQualityThresholds.FEATURE_ENVY_CALLS,
                "severity": SeverityLevels.MEDIUM,
                "description": "Method makes too many calls to external objects (Feature Envy)",
                "suggestion": "Consider moving this logic closer to the data it uses",
            },
        }

    def _check_rule(
        self, context: DetectionContext, rule_name: str, rule_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check complexity rules against context"""
        if rule_name == "complex_conditionals":
            return self._detect_complex_conditionals(context, rule_config)
        elif rule_name == "long_parameter_list":
            return self._detect_long_parameter_lists(context, rule_config)
        elif rule_name == "primitive_obsession":
            return self._detect_primitive_obsession(context, rule_config)
        elif rule_name == "high_cyclomatic_complexity":
            return self._detect_high_cyclomatic_complexity(context, rule_config)
        elif rule_name == "excessive_method_calls":
            return self._detect_excessive_method_calls(context, rule_config)

        return []

    def _detect_complex_conditionals(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect overly complex conditional statements"""
        issues: List[Dict[str, Any]] = []
        threshold = config["threshold"]

        # Guard against None context.lines
        if not context.lines:
            return issues

        for i, line in enumerate(context.lines):
            # Skip comments and empty lines
            if not line.strip() or line.strip().startswith("#"):
                continue

            # Check for if statements with multiple logical operators
            if re.search(r"\bif\b", line):
                logical_ops = len(re.findall(r"\b(and|or|&&|\|\|)\b", line))

                # Also check for nested parentheses indicating complexity
                paren_depth = self._calculate_parentheses_depth(line)

                complexity_score = logical_ops + (paren_depth // 2)

                if complexity_score >= threshold:
                    issues.append(
                        create_code_smell_issue(
                            "complex_conditionals",
                            context,
                            i + 1,
                            (
                                f"Complex conditional with {logical_ops} logical operators "
                                f"and nesting depth {paren_depth}"
                            ),
                            config["suggestion"],
                            config["severity"],
                        )
                    )

        return issues

    def _detect_long_parameter_lists(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect functions with too many parameters"""
        issues: List[Dict[str, Any]] = []
        threshold = config["threshold"]

        # Use centralized regex pattern
        func_pattern = re.compile(RegexPatterns.FUNCTION_DEF, re.MULTILINE)

        for match in func_pattern.finditer(context.content):
            func_name = match.group(2)
            line_start = match.start()

            # Find the complete function signature (may span multiple lines)
            signature = self._extract_function_signature(context.content, line_start)

            params = self._parse_parameters(signature)

            if len(params) > threshold:
                line_num = context.content[:line_start].count("\n") + 1
                issues.append(
                    create_code_smell_issue(
                        "long_parameter_list",
                        context,
                        line_num,
                        (
                            f"Function '{func_name}' has {len(params)} parameters "
                            f"(threshold: {threshold})"
                        ),
                        (
                            f"Consider using a parameter object or breaking '{func_name}' "
                            "into smaller functions"
                        ),
                        config["severity"],
                    )
                )

        return issues

    def _detect_primitive_obsession(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect excessive use of primitive types"""
        issues: List[Dict[str, Any]] = []
        threshold = config["threshold"]

        # Guard against None context.lines
        if not context.lines:
            return issues

        primitive_patterns = [r"\bstr\(", r"\bint\(", r"\bfloat\(", r"\bbool\("]

        for i, line in enumerate(context.lines):
            if line.strip().startswith("#"):
                continue

            primitive_count = sum(len(re.findall(pattern, line)) for pattern in primitive_patterns)

            if primitive_count >= threshold:
                issues.append(
                    create_code_smell_issue(
                        "primitive_obsession",
                        context,
                        i + 1,
                        f"Excessive use of primitive types ({primitive_count} conversions)",
                        config["suggestion"],
                        config["severity"],
                    )
                )

        return issues

    def _detect_high_cyclomatic_complexity(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect functions with high cyclomatic complexity"""
        issues: List[Dict[str, Any]] = []
        threshold = config["threshold"]

        # Guard against None context.lines
        if not context.lines:
            return issues

        func_pattern = re.compile(RegexPatterns.FUNCTION_DEF, re.MULTILINE)

        for match in func_pattern.finditer(context.content):
            func_name = match.group(2)
            func_start = context.content[: match.start()].count("\n")

            func_lines = DetectionUtils.extract_function_lines(context.lines, func_start)

            # Guard against None return from extract_function_lines
            if not func_lines:
                continue

            complexity = self._calculate_cyclomatic_complexity(func_lines)

            if complexity > threshold:
                issues.append(
                    create_code_smell_issue(
                        "high_cyclomatic_complexity",
                        context,
                        func_start + 1,
                        (
                            f"Function '{func_name}' has cyclomatic complexity of {complexity} "
                            f"(threshold: {threshold})"
                        ),
                        config["suggestion"],
                        config["severity"],
                    )
                )

        return issues

    def _detect_excessive_method_calls(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect methods with too many external method calls (Feature Envy)"""
        issues: List[Dict[str, Any]] = []
        threshold = config["threshold"]

        # Guard against None context.lines
        if not context.lines:
            return issues

        func_pattern = re.compile(RegexPatterns.FUNCTION_DEF, re.MULTILINE)

        for match in func_pattern.finditer(context.content):
            func_name = match.group(2)
            func_start = context.content[: match.start()].count("\n")

            func_lines = DetectionUtils.extract_function_lines(context.lines, func_start)

            # Guard against None return from extract_function_lines
            if not func_lines:
                continue

            external_calls = self._count_external_method_calls(func_lines)

            if external_calls > threshold:
                issues.append(
                    create_code_smell_issue(
                        "excessive_method_calls",
                        context,
                        func_start + 1,
                        (
                            f"Function '{func_name}' makes {external_calls} external method calls "
                            f"(threshold: {threshold})"
                        ),
                        config["suggestion"],
                        config["severity"],
                    )
                )

        return issues

    def _calculate_parentheses_depth(self, line: str) -> int:
        """Calculate maximum nesting depth of parentheses in a line"""
        depth = 0
        max_depth = 0

        for char in line:
            if char == "(":
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == ")":
                depth = max(0, depth - 1)

        return max_depth

    def _extract_function_signature(self, content: str, start_pos: int) -> str:
        """Extract complete function signature (may span multiple lines)"""
        # Find the opening parenthesis
        paren_start = content.find("(", start_pos)
        if paren_start == -1:
            return ""

        # Find the matching closing parenthesis
        paren_count = 0
        pos = paren_start

        while pos < len(content):
            if content[pos] == "(":
                paren_count += 1
            elif content[pos] == ")":
                paren_count -= 1
                if paren_count == 0:
                    return content[paren_start : pos + 1]
            pos += 1

        return ""

    def _parse_parameters(self, signature: str) -> List[str]:
        """Parse parameters from function signature"""
        if not signature:
            return []

        # Remove parentheses and split by comma
        params_str = signature.strip("()")
        if not params_str.strip():
            return []

        # Simple parameter splitting (could be improved for complex cases)
        params = [param.strip() for param in params_str.split(",") if param.strip()]

        # Filter out 'self' and 'cls'
        params = [p for p in params if not p.startswith(("self", "cls"))]

        return params

    def _calculate_cyclomatic_complexity(self, func_lines: List[str]) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity

        complexity_keywords = [
            r"\bif\b",
            r"\belif\b",
            r"\belse\b",
            r"\bfor\b",
            r"\bwhile\b",
            r"\btry\b",
            r"\bexcept\b",
            r"\bfinally\b",
            r"\band\b",
            r"\bor\b",
            r"\?.*:",  # Ternary operator
        ]

        for line in func_lines:
            line = line.strip()
            if line.startswith("#"):
                continue

            for keyword in complexity_keywords:
                complexity += len(re.findall(keyword, line))

        return complexity

    def _count_external_method_calls(self, func_lines: List[str]) -> int:
        """Count external method calls in function lines"""
        external_calls = 0

        for line in func_lines:
            if line.strip().startswith("#"):
                continue

            # Count patterns like object.method() but not self.method()
            method_calls = re.findall(r"(\w+)\.(\w+)\s*\(", line)
            for obj, _ in method_calls:
                if obj not in ["self", "cls", "super"]:
                    external_calls += 1

        return external_calls
