"""
Injection vulnerability detection - SQL, command, and path traversal attacks
"""

from pathlib import Path
from typing import Any, Dict, List

from .base import SecurityAnalysisUtils, SecurityContext, VulnerabilityPattern
from .utils import create_security_issue


class InjectionVulnerabilityDetector:
    """
    Specialized detector for injection vulnerabilities.

    Detects:
    - SQL injection vulnerabilities
    - Command injection vulnerabilities
    - Path traversal vulnerabilities
    """

    def __init__(self, create_issue_func):
        """
        Initialize with issue creation callback.

        Args:
            create_issue_func: Function to create standardized security issues
        """
        self.vulnerability_patterns = self._load_vulnerability_patterns()
        self._create_issue = create_issue_func

    def _load_vulnerability_patterns(self) -> Dict[str, VulnerabilityPattern]:
        """Load vulnerability detection patterns with comprehensive coverage"""
        return {
            "sql_injection": self._create_sql_injection_pattern(),
            "command_injection": self._create_command_injection_pattern(),
            "path_traversal": self._create_path_traversal_pattern(),
        }

    def _create_sql_injection_pattern(self) -> VulnerabilityPattern:
        """Create comprehensive SQL injection vulnerability pattern"""
        return VulnerabilityPattern(
            patterns=[
                # String formatting patterns
                r'\.execute\s*\(\s*["\'].*%.*["\']',
                r'\.execute\s*\(\s*["\'].*\{.*\}.*["\']',
                # String concatenation patterns
                r"\.execute\s*\(\s*.*\+.*\)",
                r"coder\.execute\s*\([^)]*\+[^)]*\)",
                # Format method usage
                r"coder\.execute\s*\([^)]*\.format\s*\(",
                r"\.execute\s*\([^)]*\.format\s*\(",
                # f-string patterns (potentially unsafe)
                r'\.execute\s*\(\s*f["\'].*\{[^}]*\}.*["\']',
            ],
            severity="high",
            cwe_id="CWE-89",
            owasp_category="A03:2021 – Injection",
            description="Potential SQL injection vulnerability detected",
            recommendation="Use parameterized queries or prepared statements with bound parameters",
        )

    def _create_command_injection_pattern(self) -> VulnerabilityPattern:
        """Create comprehensive command injection vulnerability pattern"""
        return VulnerabilityPattern(
            patterns=[
                # os.system patterns
                r"os\.system\s*\([^)]*\+[^)]*\)",
                r"os\.system\s*\([^)]*\.format\s*\(",
                r'os\.system\s*\(\s*f["\'].*\{[^}]*\}.*["\']',
                # subprocess patterns
                r"subprocess\.(call|run|Popen)\s*\([^)]*\+[^)]*\)",
                r"subprocess\.(call|run|Popen)\s*\([^)]*\.format\s*\(",
                r'subprocess\.(call|run|Popen)\s*\(\s*f["\'].*\{[^}]*\}.*["\']',
                # os.popen patterns
                r"os\.popen\s*\([^)]*\+[^)]*\)",
                r"os\.popen\s*\([^)]*\.format\s*\(",
                # eval with user input
                r"eval\s*\([^)]*input\s*\(",
                r"exec\s*\([^)]*input\s*\(",
            ],
            severity="critical",
            cwe_id="CWE-78",
            owasp_category="A03:2021 – Injection",
            description="Potential command injection vulnerability detected",
            recommendation=(
                "Validate and sanitize all input, use parameterized commands, " "avoid shell=True"
            ),
        )

    def _create_path_traversal_pattern(self) -> VulnerabilityPattern:
        """Create comprehensive path traversal vulnerability pattern"""
        return VulnerabilityPattern(
            patterns=[
                # File operations with path traversal
                r'open\s*\([^)]*\+[^)]*["\']\.\.\/["\']',
                r"open\s*\([^)]*\.\.\/[^)]*\)",
                # Unsafe path joining
                r"os\.path\.join\s*\([^)]*\+[^)]*\)",
                r"pathlib\.Path\s*\([^)]*\+[^)]*\)",
                # Directory traversal patterns
                r'["\'][^"\']*\.\.[\/\\][^"\']*["\']',
                r"\.\.\/\.\.\/",  # Multiple traversal attempts
                r"\.\.[\/\\]\.\.[\/\\]",
                # File operations with user input
                r"open\s*\([^)]*input\s*\([^)]*\)[^)]*\)",
            ],
            severity="high",
            cwe_id="CWE-22",
            owasp_category="A01:2021 – Broken Access Control",
            description="Potential path traversal vulnerability detected",
            recommendation=(
                "Validate file paths, use Path.resolve(), restrict access to allowed " "directories"
            ),
        )

    def detect_vulnerabilities(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Detect injection vulnerabilities in code content.

        Args:
            content: Source code content to analyze
            lines: List of source code lines
            file_path: Path to the file being analyzed

        Returns:
            List of detected vulnerability issues
        """
        context = SecurityContext(content=content, lines=lines, file_path=file_path)
        issues = []

        for vuln_type, pattern_config in self.vulnerability_patterns.items():
            issues.extend(self._detect_pattern_vulnerabilities(context, vuln_type, pattern_config))

        return issues

    def _detect_pattern_vulnerabilities(
        self, context: SecurityContext, vuln_type: str, pattern_config: VulnerabilityPattern
    ) -> List[Dict[str, Any]]:
        """
        Detect vulnerabilities for a specific pattern configuration.

        Args:
            context: Security analysis context
            vuln_type: Type of vulnerability being detected
            pattern_config: Pattern configuration for detection

        Returns:
            List of detected issues for this pattern
        """
        issues = []

        for pattern in pattern_config.patterns:
            matches = SecurityAnalysisUtils.find_pattern_matches(context.content, pattern)

            for match in matches:
                if self._should_skip_match(context, match):
                    continue

                issue = self._create_issue_from_match(context, vuln_type, pattern_config, match)
                issues.append(issue)

        return issues

    def _should_skip_match(self, context: SecurityContext, match) -> bool:
        """
        Determine if a match should be skipped (e.g., in comments or test files).

        Args:
            context: Security analysis context
            match: Regex match object

        Returns:
            True if match should be skipped
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        line_content = SecurityAnalysisUtils.get_code_snippet(context.lines, line_number)

        # Skip commented code
        if SecurityAnalysisUtils.is_comment_line(line_content):
            return True

        # Be less strict in test files (but still report critical issues)
        if SecurityAnalysisUtils.is_likely_test_file(context.file_path):
            return False  # Still report but could be filtered later

        return False

    def _create_issue_from_match(
        self, context: SecurityContext, vuln_type: str, pattern_config: VulnerabilityPattern, match
    ) -> Dict[str, Any]:
        """
        Create a security issue from a pattern match.

        Args:
            context: Security analysis context
            vuln_type: Type of vulnerability
            pattern_config: Pattern configuration
            match: Regex match object

        Returns:
            Standardized security issue dictionary
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        code_snippet = SecurityAnalysisUtils.get_code_snippet(
            context.lines, line_number, context_lines=1
        )
        from typing import Any, Dict, cast

        return cast(
            Dict[str, Any],
            create_security_issue(
                {
                    "issue_type": vuln_type,
                    "severity": pattern_config.severity,
                    "file_path": context.file_path,
                    "line_number": line_number,
                    "description": pattern_config.description,
                    "recommendation": pattern_config.recommendation,
                    "cwe_id": pattern_config.cwe_id,
                    "owasp_category": pattern_config.owasp_category,
                    "code_snippet": code_snippet,
                }
            ),
        )
