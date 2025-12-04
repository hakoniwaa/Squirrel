"""
Network security vulnerability detection - SSL/TLS issues, insecure communications
"""

from pathlib import Path
from typing import Any, Dict, List

from .base import SecurityAnalysisUtils, SecurityContext
from .utils import create_security_issue


class NetworkSecurityDetector:
    """
    Specialized detector for network security issues.

    Detects:
    - Disabled SSL/TLS certificate verification
    - Insecure network configurations
    - Unencrypted communications
    - Weak SSL/TLS settings
    """

    def __init__(self, create_issue_func):
        """
        Initialize with issue creation callback.

        Args:
            create_issue_func: Function to create standardized security issues
        """
        self.network_patterns = self._load_network_patterns()
        self._create_issue = create_issue_func

    def _load_network_patterns(self) -> List[Dict[str, Any]]:
        """Load comprehensive network security patterns"""
        return [
            self._create_disabled_ssl_pattern(),
            self._create_disabled_ssl_requests_pattern(),
            self._create_bind_all_interfaces_pattern(),
            self._create_insecure_protocols_pattern(),
            self._create_weak_ssl_context_pattern(),
            self._create_unencrypted_connections_pattern(),
        ]

    def _create_disabled_ssl_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting disabled SSL verification in urllib"""
        urllib_pattern = r"urllib\.request\.urlopen\s*\([^)]*verify=False"
        ssl_recommendation = (
            "Enable SSL certificate verification to prevent man-in-the-middle attacks"
        )
        return {
            "pattern": urllib_pattern,
            "type": "disabled_ssl_verification",
            "severity": "high",
            "cwe_id": "CWE-295",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Disabled SSL certificate verification in urllib",
            "recommendation": ssl_recommendation,
        }

    def _create_disabled_ssl_requests_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting disabled SSL verification in requests library"""
        requests_pattern = (
            r"requests\.(get|post|put|delete|patch|head|options)\s*\([^)]*verify=False"
        )
        requests_recommendation = (
            "Enable SSL certificate verification or use proper certificate bundle"
        )
        return {
            "pattern": requests_pattern,
            "type": "disabled_ssl_verification_requests",
            "severity": "high",
            "cwe_id": "CWE-295",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Disabled SSL certificate verification in requests library",
            "recommendation": requests_recommendation,
        }

    def _create_bind_all_interfaces_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting services bound to all network interfaces"""
        bind_pattern = (
            r'(socket\.socket\s*\([^)]*\)\.bind\s*\(\s*\(["\']0\.0\.0\.0["\']|'
            r'\.bind\s*\(\s*["\']0\.0\.0\.0["\']|host\s*=\s*["\']0\.0\.0\.0["\'])'
        )
        bind_recommendation = (
            "Bind to specific interfaces when possible, use firewalls for access control"
        )
        return {
            "pattern": bind_pattern,
            "type": "bind_all_interfaces",
            "severity": "medium",
            "cwe_id": "CWE-200",
            "owasp_category": "A01:2021 – Broken Access Control",
            "description": "Service bound to all network interfaces (0.0.0.0)",
            "recommendation": bind_recommendation,
        }

    def _create_insecure_protocols_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting insecure network protocols"""
        return {
            "pattern": r"(http://|ftp://|telnet://|ldap://(?!localhost))",
            "type": "insecure_protocol_usage",
            "severity": "medium",
            "cwe_id": "CWE-319",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Use of insecure network protocol",
            "recommendation": "Use encrypted protocols (https://, sftp://, ssh://, ldaps://)",
        }

    def _create_weak_ssl_context_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting weak SSL context configurations"""
        ssl_context_pattern = (
            r"(ssl\.create_default_context\([^)]*check_hostname=False|"
            r"ssl\.SSLContext\([^)]*\)\.check_hostname\s*=\s*False|"
            r"ssl\._create_unverified_context)"
        )
        ssl_context_recommendation = "Use secure SSL context with hostname verification enabled"
        return {
            "pattern": ssl_context_pattern,
            "type": "weak_ssl_context",
            "severity": "high",
            "cwe_id": "CWE-295",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Weak SSL context configuration",
            "recommendation": ssl_context_recommendation,
        }

    def _create_unencrypted_connections_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting potentially unencrypted database connections"""
        return {
            "pattern": r"(mysql://|postgresql://|mongodb://(?!.*ssl=true))",
            "type": "unencrypted_database_connection",
            "severity": "medium",
            "cwe_id": "CWE-319",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Potentially unencrypted database connection",
            "recommendation": "Use encrypted database connections with SSL/TLS",
        }

    def detect_vulnerabilities(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Detect network security issues in code content.

        Args:
            content: Source code content to analyze
            lines: List of source code lines
            file_path: Path to the file being analyzed

        Returns:
            List of detected network security issues
        """
        context = SecurityContext(content=content, lines=lines, file_path=file_path)
        issues = []

        for pattern_info in self.network_patterns:
            issues.extend(self._detect_network_pattern(context, pattern_info))

        return issues

    def _detect_network_pattern(
        self, context: SecurityContext, pattern_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect network security vulnerabilities for a specific pattern.

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

            issue = self._create_network_issue_from_match(context, pattern_info, match)
            issues.append(issue)

        return issues

    def _should_skip_match(self, context: SecurityContext, match, issue_type: str) -> bool:
        """
        Determine if a network security match should be skipped.

        Args:
            context: Security analysis context
            match: Regex match object
            issue_type: Type of network security issue

        Returns:
            True if match should be skipped
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        line_content = SecurityAnalysisUtils.get_code_snippet(context.lines, line_number)

        # Skip commented code
        if SecurityAnalysisUtils.is_comment_line(line_content):
            return True

        # Skip obvious test/development patterns
        if any(keyword in line_content.lower() for keyword in ["test", "dev", "debug", "local"]):
            return True

        # For localhost/development contexts, be more lenient
        if "localhost" in line_content.lower() or "127.0.0.1" in line_content:
            if issue_type in ["insecure_protocol_usage", "bind_all_interfaces"]:
                return True

        # Skip in test files for certain issues
        if SecurityAnalysisUtils.is_likely_test_file(context.file_path):
            if issue_type in ["disabled_ssl_verification", "disabled_ssl_verification_requests"]:
                return True  # Test files often disable SSL for testing

        return False

    def _create_network_issue_from_match(
        self, context: SecurityContext, pattern_info: Dict[str, Any], match
    ) -> Dict[str, Any]:
        """
        Create a network security issue from pattern match.

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
