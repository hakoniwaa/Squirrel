"""
Secret and credential detection - hardcoded secrets, API keys, passwords
"""

import re
from pathlib import Path
from typing import Any, Dict, List

from ..constants import SecurityThresholds
from .base import SecurityAnalysisUtils, SecurityContext
from .utils import create_security_issue


class SecretDetector:
    """
    Specialized detector for hardcoded secrets and credentials.

    Detects:
    - Hardcoded passwords and API keys
    - Base64-encoded secrets
    - High-entropy strings that may be secrets
    - Common secret patterns in various formats
    """

    # Configuration constants from centralized config
    MIN_SECRET_LENGTH = SecurityThresholds.MIN_SECRET_LENGTH
    MIN_TOKEN_LENGTH = SecurityThresholds.MIN_TOKEN_LENGTH
    MIN_BASE64_LENGTH = SecurityThresholds.MIN_BASE64_LENGTH
    MIN_ENTROPY_THRESHOLD = SecurityThresholds.MIN_ENTROPY_THRESHOLD

    def __init__(self, create_issue_func):
        """
        Initialize with issue creation callback.

        Args:
            create_issue_func: Function to create standardized security issues
        """
        self.secret_patterns = self._load_secret_patterns()
        self._create_issue = create_issue_func

    def _load_secret_patterns(self) -> List[Dict[str, Any]]:
        """Load comprehensive secret detection patterns"""
        return [
            self._create_hardcoded_password_pattern(),
            self._create_hardcoded_api_key_pattern(),
            self._create_hardcoded_secret_key_pattern(),
            self._create_base64_secret_pattern(),
            self._create_jwt_pattern(),
            self._create_connection_string_pattern(),
            self._create_private_key_pattern(),
        ]

    def _create_hardcoded_password_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting hardcoded passwords"""
        return {
            "pattern": (
                rf'(?i)(password|pwd|pass|passwd)\s*[=:]\s*["\']'
                rf'[^"\']{{{self.MIN_SECRET_LENGTH},}}["\']'
            ),  # pragma: allowlist secret
            "type": "hardcoded_password",
            "severity": "high",
            "cwe_id": "CWE-798",
            "owasp_category": "A07:2021 – Identification and Authentication Failures",
            "description": "Hardcoded password detected",
            "recommendation": (
                "Store passwords securely using environment variables "
                "or secure configuration management"
            ),
        }

    def _create_hardcoded_api_key_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting hardcoded API keys"""
        return {
            "pattern": (
                rf'(?i)(api[_-]?key|apikey|access[_-]?key|auth[_-]?token)\s*[=:]\s*["\']'
                rf'[A-Za-z0-9]{{{self.MIN_TOKEN_LENGTH},}}["\']'
            ),  # pragma: allowlist secret
            "type": "hardcoded_api_key",
            "severity": "high",
            "cwe_id": "CWE-798",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Hardcoded API key or access token detected",
            "recommendation": (
                "Store API keys in environment variables or secure configuration systems"
            ),
        }

    def _create_hardcoded_secret_key_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting hardcoded secret keys"""
        return {
            "pattern": (
                rf'(?i)(secret[_-]?key|secretkey|private[_-]?key|encryption[_-]?key)\s*[=:]\s*["\']'
                rf'[A-Za-z0-9+/]{{{self.MIN_SECRET_LENGTH * 2},}}["\']'
            ),  # pragma: allowlist secret
            "type": "hardcoded_secret_key",
            "severity": "critical",
            "cwe_id": "CWE-798",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Hardcoded secret or encryption key detected",
            "recommendation": "Use secure key management systems (AWS KMS, Azure Key Vault, etc.)",
        }

    def _create_base64_secret_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting base64-encoded secrets"""
        return {
            "pattern": rf'["\'][A-Za-z0-9+/]{{{self.MIN_BASE64_LENGTH},}}={{0,2}}["\']',
            "type": "potential_base64_secret",
            "severity": "medium",
            "cwe_id": "CWE-798",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Potential base64-encoded secret detected",
            "recommendation": "Verify if this is a secret and store securely if confirmed",
        }

    def _create_jwt_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting JWT tokens"""
        return {
            "pattern": r'["\']eyJ[A-Za-z0-9+/]+=*\.[A-Za-z0-9+/]+=*\.[A-Za-z0-9+/]+=*["\']',
            "type": "hardcoded_jwt_token",
            "severity": "high",
            "cwe_id": "CWE-798",
            "owasp_category": "A07:2021 – Identification and Authentication Failures",
            "description": "Hardcoded JWT token detected",
            "recommendation": "Generate JWT tokens dynamically and store signing keys securely",
        }

    def _create_connection_string_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting database connection strings"""
        return {
            "pattern": (
                r'(?i)(connection[_-]?string|conn[_-]?str|database[_-]?url)\s*[=:]\s*["\']'
                r'[^"\']*password[^"\']*["\']'
            ),  # pragma: allowlist secret
            "type": "hardcoded_connection_string",
            "severity": "high",
            "cwe_id": "CWE-798",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Database connection string with embedded credentials",
            "recommendation": (
                "Use connection strings without embedded credentials, store credentials separately"
            ),
        }

    def _create_private_key_pattern(self) -> Dict[str, Any]:
        """Create pattern for detecting private keys"""
        return {
            "pattern": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
            "type": "hardcoded_private_key",
            "severity": "critical",
            "cwe_id": "CWE-798",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "description": "Private key found in source code",
            "recommendation": (
                "Store private keys in secure key management systems, never in source code"
            ),
        }

    def detect_vulnerabilities(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Detect hardcoded secrets and credentials in code content.

        Args:
            content: Source code content to analyze
            lines: List of source code lines
            file_path: Path to the file being analyzed

        Returns:
            List of detected secret issues
        """
        context = SecurityContext(content=content, lines=lines, file_path=file_path)
        issues = []

        for pattern_info in self.secret_patterns:
            issues.extend(self._detect_secret_pattern(context, pattern_info))

        # Add entropy-based detection for high-entropy strings
        issues.extend(self._detect_high_entropy_secrets(context))

        return issues

    def _detect_secret_pattern(
        self, context: SecurityContext, pattern_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect secrets for a specific pattern.

        Args:
            context: Security analysis context
            pattern_info: Pattern configuration dictionary

        Returns:
            List of detected issues for this pattern
        """
        issues = []
        matches = list(re.finditer(pattern_info["pattern"], context.content, re.MULTILINE))

        for match in matches:
            if self._should_skip_match(context, match, pattern_info["type"]):
                continue

            issue = self._create_secret_issue_from_match(context, pattern_info, match)
            issues.append(issue)

        return issues

    def _detect_high_entropy_secrets(self, context: SecurityContext) -> List[Dict[str, Any]]:
        """
        Detect potential secrets using entropy analysis.

        Args:
            context: Security analysis context

        Returns:
            List of high-entropy string issues
        """
        issues = []

        # Pattern for quoted strings that might be secrets
        string_pattern = r'["\']([A-Za-z0-9+/=]{16,})["\']'
        matches = re.finditer(string_pattern, context.content)

        for match in matches:
            secret_value = match.group(1)
            entropy = SecurityAnalysisUtils.calculate_entropy(secret_value)

            if entropy > self.MIN_ENTROPY_THRESHOLD and len(secret_value) >= self.MIN_TOKEN_LENGTH:
                if not self._should_skip_entropy_match(context, match, secret_value):
                    issue = self._create_entropy_issue(context, match, entropy, secret_value)
                    issues.append(issue)

        return issues

    def _should_skip_match(self, context: SecurityContext, match, secret_type: str) -> bool:
        """
        Determine if a secret match should be skipped.

        Args:
            context: Security analysis context
            match: Regex match object
            secret_type: Type of secret being detected

        Returns:
            True if match should be skipped
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        line_content = SecurityAnalysisUtils.get_code_snippet(context.lines, line_number)

        # Skip commented code
        if SecurityAnalysisUtils.is_comment_line(line_content):
            return True

        # Skip obvious test patterns, examples, or placeholders
        skip_patterns = [
            "test",
            "example",
            "demo",
            "placeholder",
            "xxx",
            "yyy",
            "zzz",
            "fake",
            "mock",
            "dummy",
            "sample",
            "<your",
            "your_",
            "replace",
        ]

        line_lower = line_content.lower()
        if any(pattern in line_lower for pattern in skip_patterns):
            return True

        # For base64 patterns, be more strict
        if secret_type == "potential_base64_secret":  # pragma: allowlist secret
            # Skip if it looks like a hash or has repeating patterns
            match_text = match.group(0).strip("'\"")
            if self._is_likely_hash_or_constant(match_text):
                return True

        # Be more lenient in test files
        if SecurityAnalysisUtils.is_likely_test_file(context.file_path):
            return True

        return False

    def _should_skip_entropy_match(
        self, context: SecurityContext, match, secret_value: str
    ) -> bool:
        """
        Determine if a high-entropy match should be skipped.

        Args:
            context: Security analysis context
            match: Regex match object
            secret_value: The potential secret string

        Returns:
            True if match should be skipped
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        line_content = SecurityAnalysisUtils.get_code_snippet(context.lines, line_number)

        # Skip if it's likely a hash or constant
        if self._is_likely_hash_or_constant(secret_value):
            return True

        # Skip very short strings
        if len(secret_value) < self.MIN_TOKEN_LENGTH:
            return True

        # Skip in test files
        if SecurityAnalysisUtils.is_likely_test_file(context.file_path):
            return True

        # Skip if in comments
        if SecurityAnalysisUtils.is_comment_line(line_content):
            return True

        return False

    def _is_likely_hash_or_constant(self, text: str) -> bool:
        """
        Check if a string is likely a hash digest or constant rather than a secret.

        Args:
            text: String to analyze

        Returns:
            True if likely a hash or constant
        """
        # Common hash lengths
        hash_lengths = {32, 40, 56, 64, 96, 128}
        if len(text) in hash_lengths and all(c in "0123456789abcdefABCDEF" for c in text):
            return True

        # Repeating patterns
        if len(set(text)) < 4:  # Very low character diversity
            return True

        # All same character type
        if text.isdigit() or text.isalpha():
            return True

        return False

    def _create_secret_issue_from_match(
        self, context: SecurityContext, pattern_info: Dict[str, Any], match
    ) -> Dict[str, Any]:
        """
        Create a secret detection issue from pattern match.

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
        return create_security_issue(issue_data)

    def _create_entropy_issue(
        self,
        context: SecurityContext,
        match,
        entropy: float,
        secret_value: str,  # pylint: disable=unused-argument
    ) -> Dict[str, Any]:
        """
        Create a high-entropy secret issue.

        Args:
            context: Security analysis context
            match: Regex match object
            entropy: Calculated entropy value
            secret_value: The potential secret string

        Returns:
            Standardized security issue dictionary
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        code_snippet = SecurityAnalysisUtils.get_code_snippet(
            context.lines, line_number, context_lines=1
        )

        issue_data = {
            "issue_type": "high_entropy_secret",
            "severity": "medium",
            "file_path": context.file_path,
            "line_number": line_number,
            "description": (
                f"High-entropy string detected (entropy: {entropy:.2f}) - possible secret"
            ),
            "recommendation": (
                "Review string for sensitive content, store securely if confirmed as secret"
            ),
            "cwe_id": "CWE-798",
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "code_snippet": code_snippet,
        }
        return create_security_issue(issue_data)
