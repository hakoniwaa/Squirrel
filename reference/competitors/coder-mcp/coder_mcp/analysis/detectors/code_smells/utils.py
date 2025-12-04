"""
Utility functions for code smell detection
"""

from typing import Dict

from ..base import DetectionContext


def create_code_smell_issue(
    issue_type: str,
    context: DetectionContext,
    line: int,
    description: str,
    suggestion: str,
    severity: str,
) -> Dict:
    """Create a standardized code smell issue dictionary."""
    return {
        "type": issue_type,
        "file": context.relative_path,
        "line": line,
        "severity": severity,
        "description": description,
        "suggestion": suggestion,
    }
