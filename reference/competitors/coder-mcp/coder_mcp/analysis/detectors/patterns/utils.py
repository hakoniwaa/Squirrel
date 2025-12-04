"""
Shared utilities for pattern detectors.
"""

import logging
import re
from typing import Any, Dict, List, Optional


def get_code_snippet(lines: Optional[List[str]], line_number: int, context_lines: int = 2) -> str:
    """Get a code snippet around the specified line number with null safety."""
    if not lines:
        return "No content available"
    try:
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        snippet_lines = lines[start:end]
        return "\n".join(f"{i + start + 1:4}: {line}" for i, line in enumerate(snippet_lines))
    except Exception as e:
        logging.getLogger(__name__).debug(f"Failed to get code snippet: {e}")
        return "Snippet unavailable"


def create_pattern_issue_from_match(
    context,
    pattern_name: str,
    pattern_type: str,
    pattern_config: Any,
    match: re.Match,
    confidence: float,
    get_line_number,
    get_code_snippet,
) -> Dict[str, Any]:
    """
    Create a standardized pattern issue dictionary for pattern detectors.
    Args:
        context: DetectionContext
        pattern_name: Name of the matched pattern
        pattern_type: Type of pattern (e.g., 'anti_pattern', 'structural_issue')
        pattern_config: Pattern configuration (dict or PatternConfig)
        match: Regex match object
        confidence: Confidence score
        get_line_number: function to get line number from match
        get_code_snippet: function to get code snippet from lines/line number
    Returns:
        Issue dictionary compatible with the analysis system
    """
    # Handle both dict and PatternConfig types
    if hasattr(pattern_config, "description"):
        description = pattern_config.description
        suggestion = pattern_config.suggestion
        severity = getattr(pattern_config, "severity", "info")
    else:
        description = pattern_config.get(
            "description", f"{pattern_type.replace('_', ' ').title()} '{pattern_name}' detected"
        )
        suggestion = pattern_config.get(
            "suggestion", "Consider refactoring to improve code quality"
        )
        severity = pattern_config.get("severity", "info")

    # Calculate line number from match
    line_number = get_line_number(context.content, match)

    # Get code snippet around the match with null safety
    if context.lines:
        code_snippet = get_code_snippet(context.lines, line_number, 2)
    else:
        code_snippet = "No content available"

    return {
        "type": pattern_type,
        "pattern_name": pattern_name,
        "severity": severity,
        "file": getattr(context, "relative_path", str(getattr(context, "file_path", ""))),
        "line": line_number,
        "description": description,
        "suggestion": suggestion,
        "confidence": confidence,
        "code_snippet": code_snippet,
        "match_text": match.group(0) if match.group(0) else "",
    }
