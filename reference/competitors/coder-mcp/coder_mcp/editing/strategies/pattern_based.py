"""
Pattern-based editing strategy for the enhanced file editing system.

This module provides pattern-based editing capabilities with proper regex handling
and fallback to literal string replacement when regex compilation fails.
"""

import re
from typing import List, Tuple

from ..core.types import EditType, FileEdit


def _try_regex_replacement(
    content: str, pattern: str, replacement: str, edit_type: EditType
) -> Tuple[str, int]:
    """Try regex-based replacement with the given pattern."""
    try:
        compiled_pattern = re.compile(pattern, re.MULTILINE)
        if edit_type == EditType.REPLACE:
            return compiled_pattern.subn(replacement, content)
        elif edit_type == EditType.DELETE:
            return compiled_pattern.subn("", content)
    except re.error:
        pass
    return content, 0


def _try_literal_replacement(
    content: str, pattern: str, replacement: str, edit_type: EditType
) -> Tuple[str, int]:
    """Try literal string replacement."""
    if edit_type == EditType.REPLACE:
        count = content.count(pattern)
        return content.replace(pattern, replacement), count
    elif edit_type == EditType.DELETE:
        count = content.count(pattern)
        return content.replace(pattern, ""), count
    return content, 0


def apply_pattern_edit(content: str, edit: FileEdit) -> Tuple[str, int]:
    """
    Apply pattern-based edit with proper regex handling.

    Args:
        content: Original file content
        edit: FileEdit object with pattern and replacement

    Returns:
        Tuple of (modified_content, changes_count)
    """
    if not edit.pattern:
        return content, 0

    replacement = edit.replacement if edit.replacement is not None else edit.content or ""

    # Try escaped pattern first (for literal matching)
    escaped_pattern = re.escape(edit.pattern)
    modified_content, count = _try_regex_replacement(
        content, escaped_pattern, replacement, edit.type
    )
    if count > 0:
        return modified_content, count

    # Try original pattern as regex
    modified_content, count = _try_regex_replacement(content, edit.pattern, replacement, edit.type)
    if count > 0:
        return modified_content, count

    # Fall back to literal replacement
    return _try_literal_replacement(content, edit.pattern, replacement, edit.type)


def apply_multiple_pattern_edits(content: str, edits: List[FileEdit]) -> Tuple[str, int]:
    """
    Apply multiple pattern-based edits to content.

    Args:
        content: Original file content
        edits: List of FileEdit objects with patterns

    Returns:
        Tuple of (modified_content, total_changes_count)
    """
    total_changes = 0
    modified_content = content

    for edit in edits:
        if edit.pattern:
            modified_content, changes = apply_pattern_edit(modified_content, edit)
            total_changes += changes

    return modified_content, total_changes


def validate_pattern(pattern: str) -> bool:
    """
    Validate if a pattern is a valid regex.

    Args:
        pattern: Pattern string to validate

    Returns:
        True if pattern is valid regex, False otherwise
    """
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False
