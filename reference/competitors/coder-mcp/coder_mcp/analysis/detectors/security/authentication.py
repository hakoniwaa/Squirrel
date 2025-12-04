"""
Authentication vulnerability detection - hardcoded passwords, insecure session management
"""

from pathlib import Path
from typing import Any, Dict, List

from .base import SecurityAnalysisUtils, SecurityContext
from .utils import create_security_issue


class AuthenticationVulnerabilityDetector:
    """
    Specialized detector for authentication-related security issues.

    Detects:
    - Hardcoded password comparisons
    - Plain text password handling
    - Insecure session management
    - Weak authentication patterns
    """

    def __init__(self, create_issue_func):
        """
        Initialize with issue creation callback.

        Args:
            create_issue_func: Function to create standardized security issues
        """
        self.auth_patterns = self._load_auth_patterns()
        self._create_issue = create_issue_func

    def _load_auth_patterns(self) -> List[Dict[str, Any]]:
        """Load comprehensive authentication vulnerability patterns"""
        return [
            self._create_hardcoded_password_pattern(),
            self._create_plaintext_password_pattern(),
            self._create_insecure_session_pattern(),
            self._create_weak_auth_pattern(),
            self._create_password_storage_pattern(),
        ]

    def _create_hardcoded_password_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting hardcoded password checks"""
        return {
            "pattern": r'password\s*==\s*["\'][^"\']+["\']',
            "type": "hardcoded_password_check",
            "severity": "high",
            "cwe_id": "CWE-798",
            "owasp_category": "A07:2021 – Identification and Authentication Failures",
            "description": "Hardcoded password in authentication check",
            "recommendation": (
                "Use secure password hashing (bcrypt, scrypt, Argon2) and compare hashes"
            ),
        }

    def _create_plaintext_password_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting plaintext password handling"""
        pattern = r"(if\s+.*password\s*==\s*input\s*\(|password\s*=\s*input\s*\([^)]*\)\s*$)"
        return {
            "pattern": pattern,
            "type": "plaintext_password_handling",
            "severity": "high",
            "cwe_id": "CWE-256",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Plain text password handling detected",
            "recommendation": (
                "Hash passwords immediately after input and never store in plain text"
            ),
        }

    def _create_insecure_session_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting insecure session management"""
        pattern = r'session\[["\'][^"\']*["\']]\s*=\s*(True|user_id|username)'
        recommendation = (
            "Use secure session tokens, implement session timeout, validate session integrity"
        )
        return {
            "pattern": pattern,
            "type": "insecure_session_management",
            "severity": "medium",
            "cwe_id": "CWE-384",
            "owasp_category": "A07:2021 – Identification and Authentication Failures",
            "description": "Potentially insecure session management",
            "recommendation": recommendation,
        }

    def _create_weak_auth_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting weak authentication mechanisms"""
        pattern = r"(auth\s*=\s*None|authenticate\s*=\s*False|login_required\s*=\s*False)"
        recommendation = (
            "Implement proper authentication checks and ensure all endpoints are protected"
        )
        return {
            "pattern": pattern,
            "type": "weak_authentication",
            "severity": "medium",
            "cwe_id": "CWE-287",
            "owasp_category": "A07:2021 – Identification and Authentication Failures",
            "description": "Weak or disabled authentication mechanism",
            "recommendation": recommendation,
        }

    def _create_password_storage_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting insecure password storage"""
        pattern = r'(password\s*=\s*["\'][^"\']*["\']|pwd\s*=\s*["\'][^"\']*["\'])'
        recommendation = (
            "Use secure password hashing libraries and never store passwords in plain text"
        )
        return {
            "pattern": pattern,
            "type": "insecure_password_storage",
            "severity": "high",
            "cwe_id": "CWE-256",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Potential insecure password storage",
            "recommendation": recommendation,
        }

    def detect_vulnerabilities(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Detect authentication-related security issues in code content.

        Args:
            content: Source code content to analyze
            lines: List of source code lines
            file_path: Path to the file being analyzed

        Returns:
            List of detected authentication issues
        """
        context = SecurityContext(content=content, lines=lines, file_path=file_path)
        issues = []

        for pattern_info in self.auth_patterns:
            issues.extend(self._detect_auth_pattern(context, pattern_info))

        return issues

    def _detect_auth_pattern(
        self, context: SecurityContext, pattern_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect authentication vulnerabilities for a specific pattern.

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

            issue = self._create_auth_issue_from_match(context, pattern_info, match)
            issues.append(issue)

        return issues

    def _should_skip_match(self, context: SecurityContext, match, issue_type: str) -> bool:
        """
        Determine if an authentication match should be skipped.

        Args:
            context: Security analysis context
            match: Regex match object
            issue_type: Type of authentication issue

        Returns:
            True if match should be skipped
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        line_content = SecurityAnalysisUtils.get_code_snippet(context.lines, line_number)

        # Skip commented code
        if SecurityAnalysisUtils.is_comment_line(line_content):
            return True

        # Skip obvious test/example patterns
        test_keywords = ["test", "example", "demo", "mock"]
        if any(keyword in line_content.lower() for keyword in test_keywords):
            return True

        # For test files, be more lenient with hardcoded credentials
        if SecurityAnalysisUtils.is_likely_test_file(context.file_path):
            if issue_type in ["hardcoded_password_check", "insecure_password_storage"]:
                return True

        return False

    def _create_auth_issue_from_match(
        self, context: SecurityContext, pattern_info: Dict[str, Any], match
    ) -> Dict[str, Any]:
        """
        Create an authentication issue from pattern match.

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
