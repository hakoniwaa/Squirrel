"""
Input validation vulnerability detection - unsafe input handling and conversion
"""

from pathlib import Path
from typing import Any, Dict, List

from .base import SecurityAnalysisUtils, SecurityContext
from .utils import create_security_issue


class InputValidationVulnerabilityDetector:
    """
    Specialized detector for input validation security issues.

    Detects:
    - Unsafe input conversion without validation
    - Unvalidated file operations with user input
    - Format string injection vulnerabilities
    - Missing input sanitization
    """

    def __init__(self, create_issue_func):
        """
        Initialize with issue creation callback.

        Args:
            create_issue_func: Function to create standardized security issues
        """
        self.validation_patterns = self._load_validation_patterns()
        self._create_issue = create_issue_func

    def _load_validation_patterns(self) -> List[Dict[str, Any]]:
        """Load comprehensive input validation vulnerability patterns"""
        return [
            self._create_unsafe_input_pattern(),
            self._create_unsafe_file_pattern(),
            self._create_format_injection_pattern(),
            self._create_unsafe_deserialization_pattern(),
            self._create_xss_pattern(),
        ]

    def _create_unsafe_input_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting unsafe input conversion"""
        unsafe_input_pattern = r"(int|float|eval)\s*\(\s*input\s*\([^)]*\)\s*\)"
        recommendation_text = (
            "Validate input before conversion, use try-except blocks, "
            "implement input sanitization"
        )
        return {
            "pattern": unsafe_input_pattern,
            "type": "unsafe_input_conversion",
            "severity": "medium",
            "cwe_id": "CWE-20",
            "owasp_category": "A03:2021 – Injection",
            "description": "Unsafe conversion of user input without validation",
            "recommendation": recommendation_text,
        }

    def _create_unsafe_file_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting unsafe file operations with user input"""
        unsafe_file_pattern = r"open\s*\(\s*input\s*\([^)]*\)[^)]*\)"
        file_recommendation = (
            "Validate and sanitize file paths, restrict access to allowed directories"
        )
        return {
            "pattern": unsafe_file_pattern,
            "type": "unsafe_file_operation",
            "severity": "high",
            "cwe_id": "CWE-22",
            "owasp_category": "A01:2021 – Broken Access Control",
            "description": "File operation with unvalidated user input",
            "recommendation": file_recommendation,
        }

    def _create_format_injection_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting format string injection"""
        format_pattern = (
            r'(\.format\s*\([^)]*input\s*\(|%\s*input\s*\(|f["\'].*\{[^}]*input[^}]*\})'
        )
        format_recommendation = (
            "Validate input before formatting, use safe string templating methods"
        )
        return {
            "pattern": format_pattern,
            "type": "format_string_injection",
            "severity": "medium",
            "cwe_id": "CWE-134",
            "owasp_category": "A03:2021 – Injection",
            "description": "Potential format string injection vulnerability",
            "recommendation": format_recommendation,
        }

    def _create_unsafe_deserialization_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting unsafe deserialization with user input"""
        deserialization_pattern = (
            r"(pickle\.loads?\s*\(.*input|json\.loads\s*\(.*input|eval\s*\(.*input)"
        )
        deserialization_recommendation = (
            "Validate input before deserialization, use safe deserialization methods"
        )
        return {
            "pattern": deserialization_pattern,
            "type": "unsafe_deserialization",
            "severity": "high",
            "cwe_id": "CWE-502",
            "owasp_category": "A08:2021 – Software and Data Integrity Failures",
            "description": "Unsafe deserialization of user input",
            "recommendation": deserialization_recommendation,
        }

    def _create_xss_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting potential XSS vulnerabilities"""
        xss_pattern = r"(render_template.*request\.|\.innerHTML\s*=|document\.write\s*\()"
        xss_recommendation = (
            "Sanitize user input, use proper output encoding, implement CSP headers"
        )
        return {
            "pattern": xss_pattern,
            "type": "potential_xss",
            "severity": "medium",
            "cwe_id": "CWE-79",
            "owasp_category": "A03:2021 – Injection",
            "description": "Potential cross-site scripting (XSS) vulnerability",
            "recommendation": xss_recommendation,
        }

    def detect_vulnerabilities(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Detect input validation security issues in code content.

        Args:
            content: Source code content to analyze
            lines: List of source code lines
            file_path: Path to the file being analyzed

        Returns:
            List of detected input validation issues
        """
        context = SecurityContext(content=content, lines=lines, file_path=file_path)
        issues = []

        for pattern_info in self.validation_patterns:
            issues.extend(self._detect_validation_pattern(context, pattern_info))

        return issues

    def _detect_validation_pattern(
        self, context: SecurityContext, pattern_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect input validation vulnerabilities for a specific pattern.

        Args:
            context: Security analysis context
            pattern_info: Pattern configuration dictionary

        Returns:
            List of detected issues for this pattern
        """
        issues = []
        matches = SecurityAnalysisUtils.find_pattern_matches(
            context.content, pattern_info["pattern"]
        )

        for match in matches:
            if self._should_skip_match(context, match, pattern_info["type"]):
                continue

            issue = self._create_validation_issue_from_match(context, pattern_info, match)
            issues.append(issue)

        return issues

    def _should_skip_match(self, context: SecurityContext, match, _: str) -> bool:
        """
        Determine if an input validation match should be skipped.

        Args:
            context: Security analysis context
            match: Regex match object
            issue_type: Type of input validation issue

        Returns:
            True if match should be skipped
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        line_content = SecurityAnalysisUtils.get_code_snippet(context.lines, line_number)

        # Skip commented code
        if SecurityAnalysisUtils.is_comment_line(line_content):
            return True

        # Check for existing validation in surrounding lines
        if self._has_nearby_validation(context.lines, line_number):
            return True

        # Skip obvious test patterns
        if any(keyword in line_content.lower() for keyword in ["test", "example", "demo"]):
            return True

        return False

    def _has_nearby_validation(
        self, lines: List[str], line_number: int, context_range: int = 3
    ) -> bool:
        """
        Check if there's validation logic near the suspicious line.

        Args:
            lines: List of source code lines
            line_number: Target line number (1-indexed)
            context_range: Number of lines to check before and after

        Returns:
            True if validation patterns are found nearby
        """
        start_line = max(0, line_number - context_range - 1)
        end_line = min(len(lines), line_number + context_range)

        context_lines = lines[start_line:end_line]
        context_text = "\n".join(context_lines).lower()

        validation_indicators = [
            "try:",
            "except",
            "raise",
            "assert",
            "if not",
            "validate",
            "sanitize",
            "check",
            "isinstance",
            "hasattr",
            "len(",
        ]

        return any(indicator in context_text for indicator in validation_indicators)

    def _create_validation_issue_from_match(
        self, context: SecurityContext, pattern_info: Dict[str, Any], match
    ) -> Dict[str, Any]:
        """
        Create an input validation issue from pattern match.

        Args:
            context: Security analysis context
            pattern_info: Pattern configuration dictionary
            match: Regex match object

        Returns:
            Standardized security issue dictionary
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        code_snippet = SecurityAnalysisUtils.get_code_snippet(
            context.lines, line_number, context_lines=1
        )

        issue_data = {
            "issue_type": pattern_info["type"],
            "severity": pattern_info["severity"],
            "file_path": context.file_path,
            "line_number": line_number,
            "description": pattern_info["description"],
            "recommendation": pattern_info["recommendation"],
            "cwe_id": pattern_info.get("cwe_id"),
            "owasp_category": pattern_info.get("owasp_category"),
            "code_snippet": code_snippet,
        }
        result: Dict[str, Any] = create_security_issue(issue_data)
        return result
