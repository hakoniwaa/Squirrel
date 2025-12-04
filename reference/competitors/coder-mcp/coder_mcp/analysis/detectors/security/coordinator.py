"""
Security issue detection coordinator - orchestrates all specialized security detectors
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .authentication import AuthenticationVulnerabilityDetector
from .cryptographic import CryptographicVulnerabilityDetector
from .injection import InjectionVulnerabilityDetector
from .input_validation import InputValidationVulnerabilityDetector
from .insecure_functions import InsecureFunctionDetector
from .network import NetworkSecurityDetector
from .secrets import SecretDetector


class SecurityIssueDetector:
    """
    Main coordinator for security issue detection.

    Orchestrates specialized detectors and provides unified interface for security analysis.
    Follows the coordinator pattern for clean separation of concerns.
    """

    # Severity level constants
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    # Analysis configuration
    DEFAULT_MAX_ISSUES_PER_TYPE = 100
    DEFAULT_ENABLE_ALL_DETECTORS = True

    def __init__(self, max_issues_per_type: Optional[int] = None):
        """
        Initialize the security coordinator with specialized detectors.

        Args:
            max_issues_per_type: Maximum number of issues to report per type
                (prevents overwhelming output)
        """
        self.max_issues_per_type = max_issues_per_type or self.DEFAULT_MAX_ISSUES_PER_TYPE

        # Initialize specialized detectors with issue creation callback
        self.injection_detector = InjectionVulnerabilityDetector(self._create_security_issue)
        self.crypto_detector = CryptographicVulnerabilityDetector(self._create_security_issue)
        self.auth_detector = AuthenticationVulnerabilityDetector(self._create_security_issue)
        self.input_detector = InputValidationVulnerabilityDetector(self._create_security_issue)
        self.function_detector = InsecureFunctionDetector(self._create_security_issue)
        self.secret_detector = SecretDetector(self._create_security_issue)
        self.network_detector = NetworkSecurityDetector(self._create_security_issue)

    def detect_security_issues(
        self, content: str, file_path: Path, enabled_detectors: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Detect security vulnerabilities and issues in code content.

        Args:
            content: Source code content to analyze
            file_path: Path to the file being analyzed
            enabled_detectors: List of detector names to enable (None = all enabled)

        Returns:
            List of detected security issues with comprehensive metadata
        """
        if not content or not content.strip():
            return []

        lines = content.splitlines()
        all_issues = []

        # Define detector mapping for selective execution
        detector_map = {
            "injection": self.injection_detector,
            "cryptographic": self.crypto_detector,
            "authentication": self.auth_detector,
            "input_validation": self.input_detector,
            "insecure_functions": self.function_detector,
            "secrets": self.secret_detector,
            "network": self.network_detector,
        }

        # Determine which detectors to run
        detectors_to_run = self._get_enabled_detectors(detector_map, enabled_detectors)

        # Execute each enabled detector
        for detector_name, detector in detectors_to_run.items():
            try:
                detector_issues = detector.detect_vulnerabilities(content, lines, file_path)

                # Apply rate limiting per detector type
                if len(detector_issues) > self.max_issues_per_type:
                    detector_issues = detector_issues[: self.max_issues_per_type]

                all_issues.extend(detector_issues)

            except Exception:
                # Log error but don't fail entire analysis
                # In production, this would use proper logging
                continue

        # Sort issues by severity and line number
        return self._sort_and_deduplicate_issues(all_issues)

    def _get_enabled_detectors(
        self, detector_map: Dict[str, Any], enabled_detectors: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Get the subset of detectors that should be executed.

        Args:
            detector_map: All available detectors
            enabled_detectors: List of enabled detector names (None = all)

        Returns:
            Dictionary of enabled detectors
        """
        if enabled_detectors is None:
            return detector_map

        return {
            name: detector for name, detector in detector_map.items() if name in enabled_detectors
        }

    def _sort_and_deduplicate_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort issues by severity and deduplicate similar issues.

        Args:
            issues: List of security issues

        Returns:
            Sorted and deduplicated list of issues
        """
        if not issues:
            return []

        # Define severity order for sorting
        severity_order = {self.CRITICAL: 0, self.HIGH: 1, self.MEDIUM: 2, self.LOW: 3}

        # Sort by severity (highest first), then by line number
        sorted_issues = sorted(
            issues,
            key=lambda x: (severity_order.get(x.get("severity", self.LOW), 4), x.get("line", 0)),
        )

        # Simple deduplication based on type, file, and line
        seen = set()
        deduplicated = []

        for issue in sorted_issues:
            key = (issue.get("type"), issue.get("file"), issue.get("line"))
            if key not in seen:
                seen.add(key)
                deduplicated.append(issue)

        return deduplicated

    def _create_security_issue(self, issue_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a standardized security issue dictionary from configuration.

        This is the central point for issue creation, ensuring consistent formatting
        across all specialized detectors.

        Args:
            issue_config: Configuration dictionary with issue details

        Returns:
            Standardized security issue dictionary
        """
        try:
            # Handle file path conversion
            file_path = issue_config.get("file_path")
            if isinstance(file_path, Path):
                try:
                    file_str = str(file_path.relative_to(Path.cwd()))
                except (ValueError, AttributeError):
                    file_str = str(file_path)
            else:
                file_str = str(file_path) if file_path else "unknown"

            return {
                "type": issue_config.get("issue_type", "unknown"),
                "severity": issue_config.get("severity", self.MEDIUM),
                "file": file_str,
                "line": issue_config.get("line_number", 0),
                "description": issue_config.get("description", "Security issue detected"),
                "suggestion": issue_config.get(
                    "recommendation", "Review code for security implications"
                ),
                "cwe_id": issue_config.get("cwe_id"),
                "owasp_category": issue_config.get("owasp_category"),
                "code_snippet": issue_config.get("code_snippet", "").strip(),
            }

        except Exception:
            # Fallback issue creation in case of errors
            return {
                "type": "security_analysis_error",
                "severity": self.LOW,
                "file": "unknown",
                "line": 0,
                "description": "Error during security analysis",
                "suggestion": "Review code manually for security issues",
                "cwe_id": None,
                "owasp_category": None,
                "code_snippet": "",
            }

    def get_security_statistics(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive statistics about detected security issues.

        Args:
            issues: List of security issues

        Returns:
            Dictionary with detailed statistics
        """
        if not issues:
            return self._get_empty_statistics()

        # Count issues by severity
        severity_counts = self._count_by_severity(issues)

        # Find most common CWE
        most_common_cwe = self._find_most_common_cwe(issues)

        # Get unique OWASP categories
        owasp_categories = self._get_unique_owasp_categories(issues)

        # Count affected files
        affected_files = len(set(issue.get("file", "unknown") for issue in issues))

        # Get issue type distribution
        type_distribution = self._get_type_distribution(issues)

        return {
            "total_issues": len(issues),
            "critical_issues": severity_counts["critical"],
            "high_issues": severity_counts["high"],
            "medium_issues": severity_counts["medium"],
            "low_issues": severity_counts["low"],
            "most_common_cwe": most_common_cwe,
            "files_affected": affected_files,
            "owasp_categories": owasp_categories,
            "type_distribution": type_distribution,
            "security_score": self._calculate_security_score(severity_counts, len(issues)),
        }

    def _get_empty_statistics(self) -> Dict[str, Any]:
        """Get statistics structure for empty results"""
        return {
            "total_issues": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "most_common_cwe": None,
            "files_affected": 0,
            "owasp_categories": [],
            "type_distribution": {},
            "security_score": 100,  # Perfect score for no issues
        }

    def _count_by_severity(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by severity level"""
        return {
            "critical": sum(1 for i in issues if i.get("severity") == self.CRITICAL),
            "high": sum(1 for i in issues if i.get("severity") == self.HIGH),
            "medium": sum(1 for i in issues if i.get("severity") == self.MEDIUM),
            "low": sum(1 for i in issues if i.get("severity") == self.LOW),
        }

    def _find_most_common_cwe(self, issues: List[Dict[str, Any]]) -> Optional[str]:
        """Find the most frequently occurring CWE ID"""
        cwe_counts: Dict[str, int] = {}
        for issue in issues:
            cwe_id = issue.get("cwe_id")
            if cwe_id:
                cwe_counts[cwe_id] = cwe_counts.get(cwe_id, 0) + 1

        return max(cwe_counts.items(), key=lambda x: x[1])[0] if cwe_counts else None

    def _get_unique_owasp_categories(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Get list of unique OWASP categories"""
        categories = set()
        for issue in issues:
            category = issue.get("owasp_category")
            if category:
                categories.add(category)
        return sorted(list(categories))

    def _get_type_distribution(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of issue types"""
        type_counts: Dict[str, int] = {}
        for issue in issues:
            issue_type = issue.get("type", "unknown")
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        return type_counts

    def _calculate_security_score(
        self, severity_counts: Dict[str, int], total_issues: int
    ) -> float:
        """
        Calculate a security score based on issue severity distribution.

        Args:
            severity_counts: Dictionary of severity counts
            total_issues: Total number of issues

        Returns:
            Security score from 0-100 (higher is better)
        """
        if total_issues == 0:
            return 100.0

        # Weight factors for different severities (higher weight = more penalty)
        weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}

        # Calculate weighted penalty
        weighted_penalty = sum(
            severity_counts[severity] * weight for severity, weight in weights.items()
        )

        # Normalize to 0-100 scale (arbitrary scaling factor)
        max_possible_penalty = total_issues * weights["critical"]
        score = max(0, 100 - (weighted_penalty / max_possible_penalty * 100))

        return round(score, 1)
