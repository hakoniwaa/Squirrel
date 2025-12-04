"""
Insecure function detection - dangerous functions that pose security risks
"""

from pathlib import Path
from typing import Any, Dict, List, cast

from .base import SecurityAnalysisUtils, SecurityContext, VulnerabilityPattern
from .utils import create_security_issue


class InsecureFunctionDetector:
    """
    Specialized detector for usage of insecure functions.

    Detects:
    - Dangerous eval/exec functions
    - Insecure deserialization (pickle)
    - Weak random number generation
    - Unsafe YAML loading
    - Deprecated or dangerous APIs
    """

    def __init__(self, create_issue_func):
        """
        Initialize with issue creation callback.

        Args:
            create_issue_func: Function to create standardized security issues
        """
        self.insecure_functions = self._load_insecure_functions()
        self._create_issue = create_issue_func

    def _load_insecure_functions(self) -> Dict[str, VulnerabilityPattern]:
        """Load comprehensive patterns for insecure function usage"""
        return {
            "dangerous_eval": self._create_dangerous_eval_pattern(),
            "insecure_pickle": self._create_insecure_pickle_pattern(),
            "weak_random": self._create_weak_random_pattern(),
            "unsafe_yaml": self._create_unsafe_yaml_pattern(),
            "dangerous_imports": self._create_dangerous_imports_pattern(),
            "unsafe_temp_files": self._create_unsafe_temp_files_pattern(),
        }

    def _create_dangerous_eval_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting dangerous eval/exec functions"""
        return VulnerabilityPattern(
            patterns=[
                r"\beval\s*\(",
                r"\bexec\s*\(",
                r'compile\s*\([^)]*["\'].*["\'].*["\']exec["\']',  # compile with exec mode
                r"__import__\s*\(",  # Dynamic imports can be dangerous
            ],
            severity="high",
            cwe_id="CWE-95",
            owasp_category="A03:2021 – Injection",
            description="Use of dangerous code execution functions",
            recommendation=(
                "Avoid eval/exec, use ast.literal_eval() for data parsing, "
                "validate dynamic imports"
            ),
        )

    def _create_insecure_pickle_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting insecure pickle usage"""
        return VulnerabilityPattern(
            patterns=[
                r"pickle\.loads?\s*\(",
                r"cPickle\.loads?\s*\(",
                r"_pickle\.loads?\s*\(",
                r"dill\.loads?\s*\(",  # dill is also unsafe
                r"cloudpickle\.loads?\s*\(",  # cloudpickle unsafe too
            ],
            severity="high",
            cwe_id="CWE-502",
            owasp_category="A08:2021 – Software and Data Integrity Failures",
            description="Insecure deserialization with pickle or similar libraries",
            recommendation=(
                "Use JSON or other safe serialization formats, validate data before "
                "deserialization"
            ),
        )

    def _create_weak_random_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting weak random number generation"""
        return VulnerabilityPattern(
            patterns=[
                r"random\.random\s*\(",
                r"random\.randint\s*\(",
                r"random\.choice\s*\(",
                r"random\.uniform\s*\(",
                r"random\.sample\s*\(",
                r"numpy\.random\.",  # NumPy random is also not cryptographically secure
            ],
            severity="medium",
            cwe_id="CWE-338",
            owasp_category="A02:2021 – Cryptographic Failures",
            description="Use of cryptographically weak random number generator",
            recommendation=(
                "Use secrets module for cryptographic purposes, "
                "os.urandom() for secure random bytes"
            ),
        )

    def _create_unsafe_yaml_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting unsafe YAML loading"""
        return VulnerabilityPattern(
            patterns=[
                r"yaml\.load\s*\([^)]*\)(?!\s*,\s*Loader\s*=)",  # yaml.load without safe loader
                r"yaml\.unsafe_load\s*\(",
                r"yaml\.load\s*\([^)]*,\s*Loader\s*=\s*yaml\.Loader\)",  # Explicitly unsafe loader
                r"yaml\.load\s*\([^)]*,\s*Loader\s*=\s*yaml\.UnsafeLoader\)",
            ],
            severity="high",
            cwe_id="CWE-502",
            owasp_category="A08:2021 – Software and Data Integrity Failures",
            description="Unsafe YAML loading that allows arbitrary code execution",
            recommendation="Use yaml.safe_load() or yaml.load() with SafeLoader",
        )

    def _create_dangerous_imports_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting potentially dangerous imports"""
        return VulnerabilityPattern(
            patterns=[
                r"from\s+.*\s+import\s+\*",  # Wildcard imports
                r"importlib\.import_module\s*\([^)]*input",  # Dynamic imports with user input
                r"__import__\s*\([^)]*input",  # __import__ with user input
            ],
            severity="low",
            cwe_id="CWE-470",
            owasp_category="A06:2021 – Vulnerable and Outdated Components",
            description="Potentially dangerous import patterns",
            recommendation="Use explicit imports, validate module names before dynamic imports",
        )

    def _create_unsafe_temp_files_pattern(self) -> VulnerabilityPattern:
        """Create pattern for detecting unsafe temporary file usage"""
        return VulnerabilityPattern(
            patterns=[
                r"tempfile\.mktemp\s*\(",  # Deprecated and unsafe
                r"tempfile\.tempdir\s*=",  # Setting global temp directory
                r'tmp_path\s*=\s*["\']\/tmp\/',  # Hardcoded temp paths
            ],
            severity="medium",
            cwe_id="CWE-377",
            owasp_category="A01:2021 – Broken Access Control",
            description="Unsafe temporary file handling",
            recommendation=(
                "Use tempfile.NamedTemporaryFile() or tempfile.mkstemp() with proper permissions"
            ),
        )

    def detect_vulnerabilities(
        self, content: str, lines: List[str], file_path: Path
    ) -> List[Dict[str, Any]]:
        """
        Detect usage of insecure functions in code content.

        Args:
            content: Source code content to analyze
            lines: List of source code lines
            file_path: Path to the file being analyzed

        Returns:
            List of detected insecure function usage issues
        """
        context = SecurityContext(content=content, lines=lines, file_path=file_path)
        issues = []

        for func_type, pattern_config in self.insecure_functions.items():
            issues.extend(self._detect_pattern_vulnerabilities(context, func_type, pattern_config))

        return issues

    def _detect_pattern_vulnerabilities(
        self, context: SecurityContext, func_type: str, pattern_config: VulnerabilityPattern
    ) -> List[Dict[str, Any]]:
        """
        Detect vulnerabilities for insecure function patterns.

        Args:
            context: Security analysis context
            func_type: Type of insecure function
            pattern_config: Pattern configuration for detection

        Returns:
            List of detected issues for this function type
        """
        issues = []

        for pattern in pattern_config.patterns:
            matches = SecurityAnalysisUtils.find_pattern_matches(context.content, pattern)

            for match in matches:
                if self._should_skip_match(context, match, func_type):
                    continue

                issue = self._create_issue_from_match(context, func_type, pattern_config, match)
                issues.append(issue)

        return issues

    def _should_skip_match(self, context: SecurityContext, match, func_type: str) -> bool:
        """
        Determine if an insecure function match should be skipped.

        Args:
            context: Security analysis context
            match: Regex match object
            func_type: Type of insecure function

        Returns:
            True if match should be skipped
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        line_content = SecurityAnalysisUtils.get_code_snippet(context.lines, line_number)

        # Skip commented code
        if SecurityAnalysisUtils.is_comment_line(line_content):
            return True

        # Special handling for different function types
        if func_type == "weak_random":
            # Allow weak random in test files or for non-security purposes
            if SecurityAnalysisUtils.is_likely_test_file(context.file_path):
                return True
            if any(
                keyword in line_content.lower()
                for keyword in ["test", "demo", "example", "shuffle"]
            ):
                return True

        elif func_type == "dangerous_imports":
            # Allow wildcard imports in __init__.py files
            if context.file_path.name == "__init__.py":
                return True

        elif func_type == "insecure_pickle":
            # Be more lenient in test files but still report
            if SecurityAnalysisUtils.is_likely_test_file(context.file_path):
                return False  # Still report but could be filtered later

        return False

    def _create_issue_from_match(
        self, context: SecurityContext, func_type: str, pattern_config: VulnerabilityPattern, match
    ) -> Dict[str, Any]:
        """
        Create a security issue from pattern match.

        Args:
            context: Security analysis context
            func_type: Type of insecure function
            pattern_config: Pattern configuration
            match: Regex match object

        Returns:
            Standardized security issue dictionary
        """
        line_number = SecurityAnalysisUtils.get_line_number_from_match(context.content, match)
        code_snippet = SecurityAnalysisUtils.get_code_snippet(
            context.lines, line_number, context_lines=1
        )

        return cast(
            Dict[str, Any],
            create_security_issue(
                {
                    "issue_type": func_type,
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
