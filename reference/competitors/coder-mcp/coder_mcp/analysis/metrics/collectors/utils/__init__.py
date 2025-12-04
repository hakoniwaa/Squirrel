from typing import Any, Dict


def add_derived_ratios(metrics: Dict[str, Any]) -> None:
    """
    Add derived metrics based on basic metrics (comment_ratio, blank_line_ratio, code_density).
    """
    total_lines = metrics.get("lines_of_code", 0)
    comment_lines = metrics.get("comment_lines", 0)
    blank_lines = metrics.get("blank_lines", 0)
    if total_lines > 0:
        metrics["comment_ratio"] = comment_lines / total_lines
        metrics["blank_line_ratio"] = blank_lines / total_lines
        metrics["code_density"] = (total_lines - blank_lines - comment_lines) / total_lines
    else:
        metrics["comment_ratio"] = 0.0
        metrics["blank_line_ratio"] = 0.0
        metrics["code_density"] = 0.0
