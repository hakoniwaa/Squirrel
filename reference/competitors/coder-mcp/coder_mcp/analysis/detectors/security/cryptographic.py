"""
Cryptographic vulnerability detection - weak algorithms, hardcoded keys, SSL/TLS issues
"""

from pathlib import Path
from typing import Any, Dict, List

from ..constants import SecurityThresholds
from .base import SecurityAnalysisUtils, SecurityContext, VulnerabilityPattern
from .utils import create_security_issue


class CryptographicVulnerabilityDetector:
    """
    Specialized detector for cryptographic vulnerabilities.

    Detects:
    - Weak cryptographic algorithms
    - Hardcoded cryptographic keys
    - Weak SSL/TLS configurations
    - Insecure random number generation
    """

    # Configuration constants
    MIN_TOKEN_LENGTH = SecurityThresholds.MIN_TOKEN_LENGTH
    MIN_SECRET_LENGTH = SecurityThresholds.MIN_SECRET_LENGTH

    def __init__(self, create_issue_func):
        """
        Initialize with issue creation callback.

        Args:
            create_issue_func: Function to create standardized security issues
        """
        self.crypto_patterns = self._load_crypto_patterns()
        self._create_issue = create_issue_func

    def _load_crypto_patterns(self) -> Dict[str, VulnerabilityPattern]:
        """Load comprehensive cryptographic security patterns"""
        return {
            "weak_crypto": self._create_weak_crypto_pattern(),
            "hardcoded_crypto_key": self._create_hardcoded_crypto_pattern(),
            "weak_ssl": self._create_weak_ssl_pattern(),
            "weak_random": self._create_weak_random_pattern(),
        }

    def _create_weak_crypto_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting weak cryptographic algorithms"""
        return VulnerabilityPattern(
            patterns=[
                # Weak hash algorithms
                r"hashlib\.md5\s*\(",
                r"hashlib\.sha1\s*\(",
                r"Crypto\.Hash\.MD5",
                r"Crypto\.Hash\.SHA1",
                r"cryptography\.hazmat\.primitives\.hashes\.MD5",
                r"cryptography\.hazmat\.primitives\.hashes\.SHA1",
                # Weak encryption algorithms
                r"Crypto\.Cipher\.DES",
                r"Crypto\.Cipher\.ARC4",  # RC4
                r"cryptography\.hazmat\.primitives\.ciphers\.algorithms\.TripleDES",
                # Deprecated SSL/TLS versions
                r"ssl\.PROTOCOL_SSLv[23]",
                r"ssl\.PROTOCOL_TLS",  # Generic TLS (potentially weak)
            ],
            severity="medium",
            cwe_id="CWE-327",
            owasp_category="A02:2021 – Cryptographic Failures",
            description="Use of weak or deprecated cryptographic algorithm",
            recommendation=(
                "Use SHA-256 or stronger hashing algorithms, AES-256 for encryption, "
                "TLS 1.2+ for transport"
            ),
        )

    def _create_hardcoded_crypto_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting hardcoded cryptographic keys"""
        return VulnerabilityPattern(
            patterns=[
                # Hardcoded AES keys
                r'AES\.new\s*\(\s*["\'][^"\']{16,}["\']',
                r'cryptography\.fernet\.Fernet\s*\(\s*["\'][^"\']{32,}["\']',
                # Generic hardcoded keys
                rf'(?i)(key|secret)\s*=\s*["\'][A-Za-z0-9+/]{{{self.MIN_TOKEN_LENGTH},}}["\']',
                rf'(?i)(encrypt|decrypt).*["\'][A-Za-z0-9+/]{{{self.MIN_TOKEN_LENGTH},}}["\']',
                # Hardcoded initialization vectors
                r'(?i)iv\s*=\s*["\'][A-Za-z0-9+/]{16,}["\']',
                # Hardcoded salts (less critical but still bad practice)
                r'(?i)salt\s*=\s*["\'][A-Za-z0-9+/]{8,}["\']',
            ],
            severity="critical",
            cwe_id="CWE-798",
            owasp_category="A02:2021 – Cryptographic Failures",
            description="Hardcoded cryptographic key or secret detected",
            recommendation=(
                "Store keys securely using environment variables, key management systems, "
                "or secure vaults"
            ),
        )

    def _create_weak_ssl_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting weak SSL/TLS configurations"""
        return VulnerabilityPattern(
            patterns=[
                # Disabled certificate verification
                r"verify_mode\s*=\s*ssl\.CERT_NONE",
                r"check_hostname\s*=\s*False",
                r"verify=False",  # requests library
                # Weak SSL protocols
                r"ssl\.PROTOCOL_SSLv[23]",
                r"ssl\.PROTOCOL_TLSv1\b",  # TLS 1.0 is weak
                # Insecure cipher suites
                r"ssl\.OP_NO_SSLv[23]",  # Good but check context
                r"DEFAULT:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5",  # Cipher string check
            ],
            severity="high",
            cwe_id="CWE-326",
            owasp_category="A02:2021 – Cryptographic Failures",
            description="Weak SSL/TLS configuration detected",
            recommendation=(
                "Use TLS 1.2+ with strong cipher suites, enable certificate verification"
            ),
        )

    def _create_weak_random_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting weak random number generation"""
        return VulnerabilityPattern(
            patterns=[
                # Weak random functions for security contexts
                r"random\.random\s*\(",
                r"random\.randint\s*\(",
                r"random\.choice\s*\(",
                r"random\.uniform\s*\(",
                # Math.random in other contexts
                r"Math\.random\s*\(",  # JavaScript
                # Time-based seeds (predictable)
                r"random\.seed\s*\(\s*time\.",
                r"srand\s*\(\s*time\s*\(",  # C-style
            ],
            severity="medium",
            cwe_id="CWE-338",
            owasp_category="A02:2021 – Cryptographic Failures",
            description="Use of cryptographically weak random number generator",
            recommendation=(
                "Use secrets module or cryptographically secure random number generators"
            ),
        )

    def detect_vulnerabilities(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Detect cryptographic security issues in code content.

        Args:
            content: Source code content to analyze
            lines: List of source code lines
            file_path: Path to the file being analyzed

        Returns:
            List of detected cryptographic issues
        """
        context = SecurityContext(content=content, lines=lines, file_path=file_path)
        issues = []

        for crypto_type, pattern_config in self.crypto_patterns.items():
            issues.extend(
                self._detect_pattern_vulnerabilities(context, crypto_type, pattern_config)
            )

        return issues

    def _detect_pattern_vulnerabilities(
        self, context: SecurityContext, crypto_type: str, pattern_config: VulnerabilityPattern
    ) -> List[Dict[str, Any]]:
        """
        Detect cryptographic vulnerabilities for specific patterns.

        Args:
            context: Security analysis context
            crypto_type: Type of cryptographic issue
            pattern_config: Pattern configuration for detection

        Returns:
            List of detected issues for this pattern type
        """
        issues = []

        for pattern in pattern_config.patterns:
            matches = SecurityAnalysisUtils.find_pattern_matches(context.content, pattern)

            for match in matches:
                if self._should_skip_match(context, match, crypto_type):
                    continue

                issue = self._create_issue_from_match(context, crypto_type, pattern_config, match)
                issues.append(issue)

        return issues

    def _should_skip_match(self, context: SecurityContext, match, crypto_type: str) -> bool:
        """
        Determine if a cryptographic match should be skipped.

        Args:
            context: Security analysis context
            match: Regex match object
            crypto_type: Type of cryptographic issue

        Returns:
            True if match should be skipped
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        line_content = SecurityAnalysisUtils.get_code_snippet(context.lines, line_number)

        # Skip commented code
        if SecurityAnalysisUtils.is_comment_line(line_content):
            return True

        # For hardcoded keys, check if it might be a test fixture
        if crypto_type == "hardcoded_crypto_key":
            if SecurityAnalysisUtils.is_likely_test_file(context.file_path):
                # Still report but lower severity could be applied elsewhere
                return False

            # Skip obvious test patterns or examples
            if any(
                keyword in line_content.lower()
                for keyword in ["test", "example", "demo", "fixture"]
            ):
                return True

        return False

    def _create_issue_from_match(
        self,
        context: SecurityContext,
        crypto_type: str,
        pattern_config: VulnerabilityPattern,
        match,
    ) -> Dict[str, Any]:
        """
        Create a cryptographic security issue from pattern match.

        Args:
            context: Security analysis context
            crypto_type: Type of cryptographic issue
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
                    "issue_type": crypto_type,
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
