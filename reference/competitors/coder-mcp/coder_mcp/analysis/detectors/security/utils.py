"""
Utility functions for security issue detection
"""

from pathlib import Path
from typing import Any, Dict


def create_security_issue(issue_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a standardized security issue dictionary from configuration.

    This is the central point for issue creation, ensuring consistent formatting
    across all specialized detectors.

    Args:
        issue_config: Configuration dictionary with issue details

    Returns:
        Standardized security issue dictionary
    """
    # Severity level constants
    MEDIUM = "medium"
    LOW = "low"

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
            "severity": issue_config.get("severity", MEDIUM),
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
            "severity": LOW,
            "file": "unknown",
            "line": 0,
            "description": "Error during security analysis",
            "suggestion": "Review code manually for security issues",
            "cwe_id": None,
            "owasp_category": None,
            "code_snippet": "",
        }
