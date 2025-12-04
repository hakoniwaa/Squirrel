"""
Quality code smell detection - focuses on code quality issues
"""

import re
from typing import Any, Dict, List

from ..base import BaseRuleDetector, DetectionContext
from ..constants import CodeQualityThresholds, RegexPatterns, SecurityThresholds, SeverityLevels
from .utils import create_code_smell_issue


class QualitySmellDetector(BaseRuleDetector):
    """Detect quality code smells like magic numbers, dead code, naming issues"""

    def _load_patterns(self) -> Dict[str, Any]:
        """Load quality analysis patterns - not used for rule-based detector"""
        return {}

    def _load_rules(self) -> Dict[str, Any]:
        """Load quality smell detection rules"""
        return {
            "magic_numbers": {
                "threshold": CodeQualityThresholds.MAGIC_NUMBER_DIGITS,
                "severity": SeverityLevels.LOW,
                "description": "Magic number detected",
                "suggestion": ("Extract magic number to a named constant for better readability"),
            },
            "dead_code": {
                "threshold": 0,
                "severity": SeverityLevels.LOW,
                "description": "Potentially unreachable code detected",
                "suggestion": "Remove unreachable code or restructure the logic",
            },
            "inconsistent_naming": {
                "threshold": 0,
                "severity": SeverityLevels.LOW,
                "description": "Mixed naming conventions detected",
                "suggestion": (
                    "Use consistent naming convention throughout the codebase "
                    "(preferably snake_case for Python)"
                ),
            },
            "hardcoded_secrets": {
                "threshold": SecurityThresholds.MIN_SECRET_LENGTH,
                "severity": SeverityLevels.HIGH,
                "description": "Potential hardcoded secret detected",
                "suggestion": (
                    "Use environment variables or secure configuration files "
                    "for sensitive information"
                ),
            },
            "todo_comments": {
                "threshold": 0,
                "severity": SeverityLevels.INFO,
                "description": "TODO comment found",
                "suggestion": "Consider creating a ticket to track this work item",
            },
        }

    def _check_rule(
        self, context: DetectionContext, rule_name: str, rule_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check quality rules against context"""
        if rule_name == "magic_numbers":
            return self._detect_magic_numbers(context, rule_config)
        elif rule_name == "dead_code":
            return self._detect_dead_code(context, rule_config)
        elif rule_name == "inconsistent_naming":
            return self._detect_inconsistent_naming(context, rule_config)
        elif rule_name == "hardcoded_secrets":
            return self._detect_hardcoded_secrets(context, rule_config)
        elif rule_name == "todo_comments":
            return self._detect_todo_comments(context, rule_config)

        return []

    def _detect_magic_numbers(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect magic numbers in code"""
        issues: List[Dict[str, Any]] = []
        acceptable_numbers = {"0", "1", "2", "10", "100", "1000"}

        # Guard against None context.lines
        if not context.lines:
            return issues

        for i, line in enumerate(context.lines):
            if self._is_comment_or_string_line(line):
                continue

            # Use centralized regex pattern
            matches = re.findall(RegexPatterns.MAGIC_NUMBER, line)
            for match in matches:
                if match not in acceptable_numbers and len(match) >= config["threshold"]:
                    suggestion = (
                        f"Extract magic number '{match}' to a named constant "
                        f"for better readability"
                    )
                    issues.append(
                        create_code_smell_issue(
                            "magic_numbers",
                            context,
                            i + 1,
                            f"Magic number '{match}' found",
                            suggestion,
                            config["severity"],
                        )
                    )

        return issues

    def _detect_dead_code(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect potentially dead code (unreachable or unused)"""
        issues: List[Dict[str, Any]] = []

        # Guard against None context.lines
        if not context.lines:
            return issues

        for i, line in enumerate(context.lines):
            if re.search(r"^\s*return\b", line.strip()):
                # Check for code after return statement
                for j in range(i + 1, len(context.lines)):
                    next_line = context.lines[j].strip()
                    if not next_line or next_line.startswith("#"):
                        continue

                    # If we find a new function/class/control structure, stop
                    control_structures = r"^\s*(def|class|if|elif|else|except|finally|with)"
                    if re.match(control_structures, next_line):
                        break

                    issues.append(
                        create_code_smell_issue(
                            "dead_code",
                            context,
                            j + 1,
                            "Potentially unreachable code after return statement",
                            config["suggestion"],
                            config["severity"],
                        )
                    )
                    break

        return issues

    def _detect_inconsistent_naming(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect inconsistent naming conventions"""
        issues: List[Dict[str, Any]] = []

        # Use centralized regex patterns
        snake_case_matches = re.findall(RegexPatterns.SNAKE_CASE, context.content)
        camel_case_matches = re.findall(RegexPatterns.CAMEL_CASE, context.content)

        # Only flag if there are significant amounts of both
        min_threshold = 5
        if len(snake_case_matches) > min_threshold and len(camel_case_matches) > min_threshold:
            description = (
                f"Mixed naming conventions: {len(snake_case_matches)} snake_case, "
                f"{len(camel_case_matches)} camelCase"
            )
            issues.append(
                create_code_smell_issue(
                    "inconsistent_naming",
                    context,
                    1,
                    description,
                    config["suggestion"],
                    config["severity"],
                )
            )

        return issues

    def _detect_hardcoded_secrets(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect hardcoded secrets and sensitive information"""
        issues: List[Dict[str, Any]] = []
        min_secret_length = config["threshold"]

        # Guard against None context.lines
        if not context.lines:
            return issues

        secret_patterns = [
            (RegexPatterns.PASSWORD_PATTERN, "hardcoded password"),
            (RegexPatterns.API_KEY_PATTERN, "hardcoded API key"),
            (rf'secret\s*=\s*["\'][^"\']{{{min_secret_length * 2},}}["\']', "hardcoded secret"),
            (
                rf'token\s*=\s*["\'][^"\']{{{SecurityThresholds.MIN_TOKEN_LENGTH},}}["\']',
                "hardcoded token",
            ),
        ]

        for i, line in enumerate(context.lines):
            for pattern, description in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        create_code_smell_issue(
                            "hardcoded_secrets",
                            context,
                            i + 1,
                            f"Potential {description} detected",
                            config["suggestion"],
                            config["severity"],
                        )
                    )

        return issues

    def _detect_todo_comments(
        self, context: DetectionContext, config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect TODO, FIXME, and HACK comments"""
        issues: List[Dict[str, Any]] = []
        todo_patterns = [r"#\s*TODO", r"#\s*FIXME", r"#\s*HACK", r"#\s*XXX", r"#\s*BUG"]

        # Guard against None context.lines
        if not context.lines:
            return issues

        for i, line in enumerate(context.lines):
            for pattern in todo_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    todo_type = match.group().strip("#").strip()
                    issues.append(
                        create_code_smell_issue(
                            "todo_comments",
                            context,
                            i + 1,
                            f"{todo_type} comment found: {line.strip()}",
                            config["suggestion"],
                            config["severity"],
                        )
                    )
                    break  # Only report one TODO per line

        return issues

    def _is_comment_or_string_line(self, line: str) -> bool:
        """Check if line is primarily a comment or string literal"""
        stripped = line.strip()
        return (
            stripped.startswith("#")
            or stripped.startswith('"""')
            or stripped.startswith("'''")
            or stripped.startswith('"')
            or stripped.startswith("'")
        )

    def _create_issue(
        self,
        issue_type: str,
        context: DetectionContext,
        line: int,
        description: str,
        suggestion: str,
        severity: str,
    ) -> Dict[str, Any]:
        """Create a standardized code smell issue"""
        return {}
