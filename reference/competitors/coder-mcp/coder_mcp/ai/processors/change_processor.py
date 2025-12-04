#!/usr/bin/env python3
"""
Code Change Processing
Handles extraction of code changes and diff processing
"""

import logging
import re
from typing import List

from .base import CodeChange

logger = logging.getLogger(__name__)


class ChangeExtractor:
    """Extract code changes from AI responses"""

    def extract_code_changes(self, response: str) -> List[CodeChange]:
        """Extract suggested code changes from response"""
        changes = []

        # Look for patterns like "Change X to Y" or "Replace X with Y"
        change_pattern = (
            r"(?:Change|Replace|Modify|Update)\s+(.+?)\s+(?:to|with)\s+(.+?)(?:\.|,|\n)"
        )
        matches = re.finditer(change_pattern, response, re.IGNORECASE)

        for match in matches:
            original = match.group(1).strip()
            new = match.group(2).strip()

            # Extract code if present
            original_code = self._extract_code_from_text(original)
            new_code = self._extract_code_from_text(new)

            if original_code or new_code:
                changes.append(
                    CodeChange(
                        file_path="",  # Would need to be determined from context
                        change_type="modify",
                        original_code=original_code,
                        new_code=new_code or new,
                        description=match.group(0),
                    )
                )

        return changes

    def _extract_code_from_text(self, text: str) -> str:
        """Extract code from text that might contain code"""
        # Look for code patterns
        code_pattern = r"`([^`]+)`"
        match = re.search(code_pattern, text)
        if match:
            return match.group(1)

        # Look for code-like patterns (contains brackets, operators, etc.)
        if any(char in text for char in ["(", ")", "{", "}", "[", "]", "=", "->", "=>"]):
            return text.strip()

        return text


def _start_new_file(line: str) -> dict:
    return {"old_file": line[4:], "new_file": None, "hunks": []}


def _set_new_file_name(current_file: dict, line: str) -> None:
    current_file["new_file"] = line[4:]


def _start_new_hunk(line: str) -> dict | None:
    hunk_match = re.match(r"@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@", line)
    if hunk_match:
        return {
            "old_start": int(hunk_match.group(1)),
            "old_count": int(hunk_match.group(2)) if hunk_match.group(2) else 1,
            "new_start": int(hunk_match.group(3)),
            "new_count": int(hunk_match.group(4)) if hunk_match.group(4) else 1,
            "lines": [],
        }
    return None


def _append_line_to_hunk(current_hunk: dict, line: str) -> None:
    if isinstance(current_hunk.get("lines"), list):
        current_hunk["lines"].append(line)


def _finalize_file_and_hunk(
    current_file: dict | None, current_hunk: dict | None, files: list[dict]
) -> None:
    if current_file is not None:
        if isinstance(current_file, dict) and current_hunk is not None:
            hunks = current_file.get("hunks")
            if isinstance(hunks, list):
                hunks.append(current_hunk)
        files.append(current_file)


class DiffProcessor:
    """Process git diffs and code changes"""

    @staticmethod
    def parse_diff(diff_text: str) -> List[dict]:
        """Parse unified diff format"""
        files: List[dict] = []
        current_file: dict | None = None
        current_hunk: dict | None = None

        lines = diff_text.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]
            if line.startswith("--- "):
                current_file, files = DiffProcessor._handle_file_start(current_file, files, line)
                current_hunk = None
            elif line.startswith("+++ "):
                DiffProcessor._handle_file_name(current_file, line)
            elif line.startswith("@@"):
                current_file, current_hunk = DiffProcessor._handle_hunk_start(
                    current_file, current_hunk, line
                )
            elif current_hunk is not None and DiffProcessor._is_hunk_line(line):
                _append_line_to_hunk(current_hunk, line)
            i += 1

        _finalize_file_and_hunk(current_file, current_hunk, files)
        return files

    @staticmethod
    def _handle_file_start(
        current_file: dict | None, files: list[dict], line: str
    ) -> tuple[dict, list[dict]]:
        if current_file is not None:
            files.append(current_file)
        return _start_new_file(line), files

    @staticmethod
    def _handle_file_name(current_file: dict | None, line: str) -> None:
        if current_file is not None:
            _set_new_file_name(current_file, line)

    @staticmethod
    def _handle_hunk_start(
        current_file: dict | None, current_hunk: dict | None, line: str
    ) -> tuple[dict | None, dict | None]:
        if isinstance(current_file, dict) and current_hunk is not None:
            hunks = current_file.get("hunks")
            if isinstance(hunks, list):
                hunks.append(current_hunk)
        current_hunk = _start_new_hunk(line)
        return current_file, current_hunk

    @staticmethod
    def _is_hunk_line(line: str) -> bool:
        return (
            line.startswith(" ")
            or line.startswith("+")
            or line.startswith("-")
            or line.startswith("\\")
        )

    @staticmethod
    def generate_patch(changes: List[CodeChange]) -> str:
        """Generate a unified diff patch from code changes"""
        patch_lines = []

        for change in changes:
            # File header
            patch_lines.append(f"--- a/{change.file_path}")
            patch_lines.append(f"+++ b/{change.file_path}")

            # Simple hunk (this is a basic implementation)
            old_lines = change.original_code.split("\n") if change.original_code else []
            new_lines = change.new_code.split("\n") if change.new_code else []

            start_line = change.line_start or 1
            old_count = len(old_lines)
            new_count = len(new_lines)

            # Hunk header
            patch_lines.append(f"@@ -{start_line},{old_count} +{start_line},{new_count} @@")

            # Remove old lines
            for line in old_lines:
                patch_lines.append(f"-{line}")

            # Add new lines
            for line in new_lines:
                patch_lines.append(f"+{line}")

        return "\n".join(patch_lines)
