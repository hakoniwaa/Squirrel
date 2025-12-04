"""
Diff utilities for the enhanced file editing system.

This module provides functions for generating, parsing, and applying
unified diffs between file versions.
"""

import difflib
from typing import Dict, List, Optional, Tuple


def generate_unified_diff(
    original: str,
    modified: str,
    filename: str,
    original_timestamp: Optional[str] = None,
    modified_timestamp: Optional[str] = None,
    context_lines: int = 3,
) -> str:
    """
    Generate a unified diff between original and modified content.

    Args:
        original: Original file content
        modified: Modified file content
        filename: Name of the file being diffed
        original_timestamp: Timestamp for original file
        modified_timestamp: Timestamp for modified file
        context_lines: Number of context lines to include

    Returns:
        Unified diff string
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    fromfile = f"a/{filename}"
    tofile = f"b/{filename}"

    if original_timestamp:
        fromfile += f"\t{original_timestamp}"
    if modified_timestamp:
        tofile += f"\t{modified_timestamp}"

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=fromfile,
        tofile=tofile,
        lineterm="",
        n=context_lines,
    )

    return "".join(diff)


def generate_inline_diff(original: str, modified: str, filename: str) -> str:
    """
    Generate an inline diff showing changes within lines.

    Args:
        original: Original file content
        modified: Modified file content
        filename: Name of the file being diffed

    Returns:
        Inline diff string
    """
    original_lines = original.splitlines()
    modified_lines = modified.splitlines()

    result = [f"=== {filename} ==="]

    # Use SequenceMatcher to find differences
    matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        result.extend(_format_diff_section(tag, original_lines, modified_lines, i1, i2, j1, j2))

    return "\n".join(result)


def _format_diff_section(
    tag: str,
    original_lines: List[str],
    modified_lines: List[str],
    i1: int,
    i2: int,
    j1: int,
    j2: int,
) -> List[str]:
    """Format a section of the diff based on the operation tag."""
    result = []

    if tag == "equal":
        for line in original_lines[i1:i2]:
            result.append(f"  {line}")
    elif tag == "delete":
        for line in original_lines[i1:i2]:
            result.append(f"- {line}")
    elif tag == "insert":
        for line in modified_lines[j1:j2]:
            result.append(f"+ {line}")
    elif tag == "replace":
        for line in original_lines[i1:i2]:
            result.append(f"- {line}")
        for line in modified_lines[j1:j2]:
            result.append(f"+ {line}")

    return result


def parse_unified_diff(diff_content: str) -> List[Tuple[str, str, List[str]]]:
    """
    Parse a unified diff and extract file changes.

    Args:
        diff_content: Unified diff content

    Returns:
        List of (original_file, modified_file, changes) tuples
    """
    changes = []
    current_file = None
    current_changes: List[str] = []

    for line in diff_content.splitlines():
        if line.startswith("---"):
            # Start of a new file diff
            if current_file:
                changes.append(current_file + (current_changes,))
            original_file = line[4:].split("\t")[0]
            current_changes = []
        elif line.startswith("+++"):
            modified_file = line[4:].split("\t")[0]
            current_file = (original_file, modified_file)
        elif line.startswith("@@"):
            # Hunk header
            current_changes.append(line)
        elif line.startswith((" ", "+", "-")):
            # Diff line
            current_changes.append(line)

    # Add the last file
    if current_file:
        changes.append(current_file + (current_changes,))

    return changes


def count_changes(diff_content: str) -> Dict[str, int]:
    """
    Count additions and deletions in a unified diff.

    Args:
        diff_content: Unified diff content

    Returns:
        Dictionary with 'additions' and 'deletions' counts
    """
    additions = 0
    deletions = 0

    for line in diff_content.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    return {"additions": additions, "deletions": deletions}


def apply_diff_to_content(original: str, diff_content: str) -> str:
    """
    Apply a unified diff to original content.

    Args:
        original: Original file content
        diff_content: Unified diff to apply

    Returns:
        Modified content after applying diff

    Raises:
        ValueError: If diff cannot be applied
    """
    # This is a simplified implementation
    # In a production system, you'd want to use a more robust diff library
    original_lines = original.splitlines()
    result_lines = original_lines.copy()

    changes = parse_unified_diff(diff_content)

    for _, _, diff_lines in changes:
        line_offset = 0

        for diff_line in diff_lines:
            if diff_line.startswith("@@"):
                # Parse hunk header to get line numbers
                parts = diff_line.split()
                if len(parts) >= 2:
                    old_range = parts[1][1:]  # Remove the '-'
                    if "," in old_range:
                        old_start = int(old_range.split(",")[0]) - 1
                    else:
                        old_start = int(old_range) - 1

                    current_line = old_start + line_offset

            elif diff_line.startswith("-"):
                # Deletion
                if current_line < len(result_lines):
                    del result_lines[current_line]
                    line_offset -= 1

            elif diff_line.startswith("+"):
                # Addition
                new_content = diff_line[1:]  # Remove the '+'
                result_lines.insert(current_line, new_content)
                current_line += 1
                line_offset += 1

            elif diff_line.startswith(" "):
                # Context line
                current_line += 1

    return "\n".join(result_lines)


def create_side_by_side_diff(original: str, modified: str, filename: str, width: int = 80) -> str:
    """
    Create a side-by-side diff view.

    Args:
        original: Original file content
        modified: Modified file content
        filename: Name of the file being diffed
        width: Width of each column

    Returns:
        Side-by-side diff string
    """
    original_lines = original.splitlines()
    modified_lines = modified.splitlines()

    result = [f"=== {filename} ==="]
    result.append("=" * (width * 2 + 3))
    result.append(f"{'Original':<{width}} | {'Modified':<{width}}")
    result.append("=" * (width * 2 + 3))

    # Use SequenceMatcher to align lines
    matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for i, line in enumerate(original_lines[i1:i2]):
                result.append(f"{line:<{width}} | {line:<{width}}")
        elif tag == "delete":
            for line in original_lines[i1:i2]:
                result.append(f"{line:<{width}} | {'<deleted>':<{width}}")
        elif tag == "insert":
            for line in modified_lines[j1:j2]:
                result.append(f"{'<added>':<{width}} | {line:<{width}}")
        elif tag == "replace":
            # Handle replacements
            orig_chunk = original_lines[i1:i2]
            mod_chunk = modified_lines[j1:j2]

            max_len = max(len(orig_chunk), len(mod_chunk))
            for i in range(max_len):
                orig_line = orig_chunk[i] if i < len(orig_chunk) else "<deleted>"
                mod_line = mod_chunk[i] if i < len(mod_chunk) else "<added>"
                result.append(f"{orig_line:<{width}} | {mod_line:<{width}}")

    return "\n".join(result)


def diff_summary(diff_content: str) -> str:
    """
    Generate a summary of changes in a diff.

    Args:
        diff_content: Unified diff content

    Returns:
        Summary string
    """
    change_counts = count_changes(diff_content)
    additions = change_counts["additions"]
    deletions = change_counts["deletions"]
    changes = parse_unified_diff(diff_content)

    if not changes:
        return "No changes"

    files_changed = len(changes)

    summary = f"{files_changed} file{'s' if files_changed != 1 else ''} changed"

    if additions > 0:
        summary += f", {additions} insertion{'s' if additions != 1 else ''}"

    if deletions > 0:
        summary += f", {deletions} deletion{'s' if deletions != 1 else ''}"

    return summary
