"""
Core editor implementation for the enhanced file editing system.

This module provides the main EnhancedFileEditor class that supports
from .errors import (
    EditError,
    FileNotFoundError as EditFileNotFoundError,
    FilePermissionError,
    SyntaxValidationError,
    EditValidationError,
    PatternNotFoundError,
    FileSizeError,
    BackupError
)
multiple editing strategies including line-based, pattern-based, and AST-based editing.
"""

import ast
import re
from pathlib import Path
from typing import List, Optional, Tuple

from ..utils.backup import BackupManager
from ..utils.diff import generate_unified_diff
from .types import (
    EditConfig,
    EditError,
    EditResult,
    EditStrategy,
    EditType,
    EditValidationError,
    FileEdit,
    FileNotFoundError,
)


class EnhancedFileEditor:
    """
    Main file editor with multiple editing strategies.

    Supports line-based, pattern-based, and AST-based editing operations
    with comprehensive backup and validation features.
    """

    def __init__(self, config: Optional[EditConfig] = None):
        """
        Initialize the enhanced file editor.

        Args:
            config: Optional configuration for editing operations
        """
        self.config = config or EditConfig()
        self.backup_manager = BackupManager(
            self.config.backup_location, self.config.backup_retention_days
        )

    def edit_file(
        self,
        file_path: str,
        edits: List[FileEdit],
        preview: bool = False,
        create_backup: Optional[bool] = None,
    ) -> EditResult:
        """
        Apply edits to a file using various strategies.

        Args:
            file_path: Path to the file to edit
            edits: List of edit operations to apply
            preview: If True, show changes without applying
            create_backup: If True, create backup before editing

        Returns:
            EditResult with operation details
        """
        try:
            # Validate inputs
            if not edits:
                return EditResult(success=False, changes_made=0, diff="", error="No edits provided")

            # Validate file exists
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Check file size
            file_size = file_path_obj.stat().st_size
            max_size = self.config.max_file_size_mb * 1024 * 1024
            if file_size > max_size:
                raise EditError(f"File too large: {file_size} bytes > {max_size} bytes")

            # Read original content
            original_content = file_path_obj.read_text()

            # Validate edits
            for edit in edits:
                self._validate_edit(edit, original_content)

            # Apply edits
            modified_content, changes_made = self._apply_edits(original_content, edits)

            # Generate diff
            diff = generate_unified_diff(original_content, modified_content, file_path)

            # Handle backup and finalization
            return self._finalize_edit(
                file_path_obj,
                original_content,
                modified_content,
                changes_made,
                diff,
                preview,
                create_backup,
            )

        except Exception as e:
            return EditResult(success=False, changes_made=0, diff="", error=str(e))

    def _finalize_edit(
        self,
        file_path_obj: Path,
        original_content: str,
        modified_content: str,
        changes_made: int,
        diff: str,
        preview: bool,
        create_backup: Optional[bool],
    ) -> EditResult:
        """Finalize edit by creating backup and applying changes."""
        # Create backup if requested
        backup_path = None
        if create_backup or (create_backup is None and self.config.create_backups):
            if not preview:
                backup_info = self.backup_manager.create_backup(
                    str(file_path_obj), original_content
                )
                backup_path = backup_info.backup_path

        # Preview or apply changes
        if preview:
            return EditResult(
                success=True, changes_made=changes_made, diff=diff, preview=modified_content
            )
        else:
            # Validate syntax if enabled
            if self.config.validate_syntax:
                self._validate_syntax(modified_content, str(file_path_obj))

            # Write modified content
            file_path_obj.write_text(modified_content)

            return EditResult(
                success=True, changes_made=changes_made, diff=diff, backup_path=backup_path
            )

    def _validate_edit(self, edit: FileEdit, content: str) -> None:
        """
        Validate a single edit operation.

        Args:
            edit: Edit operation to validate
            content: File content to validate against

        Raises:
            EditValidationError: If edit is invalid
        """
        lines = content.splitlines()

        if edit.type == EditType.REPLACE:
            self._validate_replace_edit(edit, lines)
        elif edit.type == EditType.INSERT:
            self._validate_insert_edit(edit, lines)
        elif edit.type == EditType.DELETE:
            self._validate_delete_edit(edit, lines)
        elif edit.type == EditType.MOVE:
            self._validate_move_edit(edit, lines)

    def _validate_replace_edit(self, edit: FileEdit, lines: List[str]) -> None:
        """Validate a replace edit operation."""
        if edit.start_line is not None:
            if edit.start_line < 1 or edit.start_line > len(lines):
                raise EditValidationError(f"Invalid start_line: {edit.start_line}")
            if edit.end_line is not None:
                if edit.end_line < edit.start_line or edit.end_line > len(lines):
                    raise EditValidationError(f"Invalid end_line: {edit.end_line}")
        elif edit.pattern is not None:
            try:
                re.compile(edit.pattern)
            except re.error as e:
                raise EditValidationError(f"Invalid regex pattern: {e}")
        else:
            raise EditValidationError("REPLACE edit requires start_line or pattern")

    def _validate_insert_edit(self, edit: FileEdit, lines: List[str]) -> None:
        """Validate an insert edit operation."""
        if edit.target_line is None or edit.content is None:
            raise EditValidationError("INSERT edit requires target_line and content")
        if edit.target_line < 1 or edit.target_line > len(lines) + 1:
            raise EditValidationError(f"Invalid target_line: {edit.target_line}")

    def _validate_delete_edit(self, edit: FileEdit, lines: List[str]) -> None:
        """Validate a delete edit operation."""
        if edit.start_line is not None:
            if edit.start_line < 1 or edit.start_line > len(lines):
                raise EditValidationError(f"Invalid start_line: {edit.start_line}")
            if edit.end_line is not None:
                if edit.end_line < edit.start_line or edit.end_line > len(lines):
                    raise EditValidationError(f"Invalid end_line: {edit.end_line}")
        elif edit.pattern is not None:
            try:
                re.compile(edit.pattern)
            except re.error as e:
                raise EditValidationError(f"Invalid regex pattern: {e}")
        else:
            raise EditValidationError("DELETE edit requires start_line or pattern")

    def _validate_move_edit(self, edit: FileEdit, lines: List[str]) -> None:
        """Validate a move edit operation."""
        if edit.start_line is None or edit.target_line is None:
            raise EditValidationError("MOVE edit requires start_line and target_line")
        if edit.start_line < 1 or edit.start_line > len(lines):
            raise EditValidationError(f"Invalid start_line: {edit.start_line}")
        if edit.target_line < 1 or edit.target_line > len(lines) + 1:
            raise EditValidationError(f"Invalid target_line: {edit.target_line}")

    def _apply_edits(self, content: str, edits: List[FileEdit]) -> Tuple[str, int]:
        """
        Apply a list of edits to content.

        Args:
            content: Original content
            edits: List of edits to apply

        Returns:
            Tuple of (modified_content, changes_made)
        """
        lines = content.splitlines(keepends=True)
        total_changes = 0

        # Sort edits by line number (reverse order for line-based edits)
        line_edits = [e for e in edits if e.start_line is not None or e.target_line is not None]
        pattern_edits = [e for e in edits if e.pattern is not None]

        line_edits.sort(key=lambda x: x.start_line or x.target_line or 0, reverse=True)

        # Apply line-based edits first (in reverse order)
        for edit in line_edits:
            if edit.strategy == EditStrategy.LINE_BASED or (
                edit.strategy == EditStrategy.PATTERN_BASED and edit.pattern is None
            ):
                lines, changes = self._apply_line_based_edit(lines, edit)
                total_changes += changes

        # Apply pattern-based edits
        content_str = "".join(lines)
        for edit in pattern_edits:
            if edit.strategy == EditStrategy.PATTERN_BASED or (
                edit.type == EditType.REPLACE and edit.pattern
            ):
                # Use pattern-based strategy
                from ..strategies.pattern_based import apply_pattern_edit

                content_str, changes = apply_pattern_edit(content_str, edit)
                total_changes += changes
            else:
                # Fallback to original pattern-based edit
                content_str, changes = self._apply_pattern_based_edit(content_str, edit)
                total_changes += changes

        return content_str, total_changes

    def _apply_line_based_edit(self, lines: List[str], edit: FileEdit) -> Tuple[List[str], int]:
        """
        Apply a line-based edit operation.

        Args:
            lines: List of file lines
            edit: Edit operation to apply

        Returns:
            Tuple of (modified_lines, changes_made)
        """
        if edit.type == EditType.REPLACE:
            return self._apply_replace_edit(lines, edit)
        elif edit.type == EditType.INSERT:
            return self._apply_insert_edit(lines, edit)
        elif edit.type == EditType.DELETE:
            return self._apply_delete_edit(lines, edit)
        elif edit.type == EditType.MOVE:
            return self._apply_move_edit(lines, edit)

        return lines, 0

    def _apply_replace_edit(self, lines: List[str], edit: FileEdit) -> Tuple[List[str], int]:
        """Apply a replace edit operation."""
        if edit.start_line is None:
            return lines, 0

        start = edit.start_line - 1
        end = (edit.end_line or edit.start_line) - 1

        if 0 <= start < len(lines):
            # Get the content to insert
            if edit.content is not None:
                # Ensure content ends with newline
                content = edit.content
                if not content.endswith("\n") and end < len(lines) - 1:
                    content += "\n"

                new_lines = content.splitlines(keepends=True)
                # Replace the lines
                lines[start : end + 1] = new_lines
                return lines, 1
            elif edit.replacement is not None:
                # Single line replacement
                if start < len(lines):
                    lines[start] = edit.replacement
                    if not lines[start].endswith("\n") and start < len(lines) - 1:
                        lines[start] += "\n"
                    return lines, 1
            else:
                # Delete the lines if no replacement content
                del lines[start : end + 1]
                return lines, 1

        return lines, 0

    def _apply_insert_edit(self, lines: List[str], edit: FileEdit) -> Tuple[List[str], int]:
        """Apply an insert edit operation."""
        if edit.target_line is None or edit.content is None:
            return lines, 0

        # Convert to 0-based index
        insert_pos = edit.target_line - 1

        # Ensure content ends with newline if not present
        content = edit.content
        if not content.endswith("\n"):
            content += "\n"

        # Insert at the correct position
        if 0 <= insert_pos <= len(lines):
            # Split content into lines while preserving newlines
            new_lines = content.splitlines(keepends=True)
            # Insert the new lines
            lines[insert_pos:insert_pos] = new_lines
            return lines, len(new_lines)

        return lines, 0

    def _apply_delete_edit(self, lines: List[str], edit: FileEdit) -> Tuple[List[str], int]:
        """Apply a delete edit operation."""
        if edit.start_line is None:
            return lines, 0

        start = edit.start_line - 1
        end = (edit.end_line or edit.start_line) - 1

        if 0 <= start < len(lines):
            count = min(end + 1, len(lines)) - start
            del lines[start : min(end + 1, len(lines))]
            return lines, count

        return lines, 0

    def _apply_move_edit(self, lines: List[str], edit: FileEdit) -> Tuple[List[str], int]:
        """Apply a move edit operation."""
        if edit.start_line is None or edit.target_line is None:
            return lines, 0

        start = edit.start_line - 1
        end = (edit.end_line or edit.start_line) - 1
        target = edit.target_line - 1

        if 0 <= start < len(lines):
            moving_lines = lines[start : end + 1]
            del lines[start : end + 1]
            if target > start:
                target -= end - start + 1
            lines[target:target] = moving_lines
            return lines, len(moving_lines)

        return lines, 0

    def _apply_pattern_based_edit(self, content: str, edit: FileEdit) -> Tuple[str, int]:
        """
        Apply a pattern-based edit operation.

        Args:
            content: File content
            edit: Edit operation to apply

        Returns:
            Tuple of (modified_content, changes_made)
        """
        changes = 0

        if edit.type == EditType.REPLACE and edit.pattern:
            pattern = re.compile(edit.pattern, re.MULTILINE)
            replacement = edit.replacement or ""

            # Count matches before replacement
            matches = pattern.findall(content)
            changes = len(matches)

            # Apply replacement
            content = pattern.sub(replacement, content)

        elif edit.type == EditType.DELETE and edit.pattern:
            pattern = re.compile(edit.pattern, re.MULTILINE)

            # Count matches before deletion
            matches = pattern.findall(content)
            changes = len(matches)

            # Delete matches
            content = pattern.sub("", content)

        return content, changes

    def _validate_syntax(self, content: str, file_path: str) -> None:
        """
        Validate syntax of modified content.

        Args:
            content: Modified content to validate
            file_path: Path to the file (for determining language)

        Raises:
            EditValidationError: If syntax is invalid
        """
        file_path_obj = Path(file_path)

        # Python syntax validation
        if file_path_obj.suffix == ".py":
            try:
                ast.parse(content)
            except SyntaxError as e:
                raise EditValidationError(f"Python syntax error: {e}")

        # Add more syntax validators for other languages as needed

    def preview_edit(self, file_path: str, edits: List[FileEdit]) -> EditResult:
        """
        Preview edits without applying them.

        Args:
            file_path: Path to the file to edit
            edits: List of edit operations

        Returns:
            EditResult with preview information
        """
        return self.edit_file(file_path, edits, preview=True)

    def undo_last_edit(self, file_path: str) -> EditResult:
        """
        Undo the last edit by restoring from the most recent backup.

        Args:
            file_path: Path to the file to restore

        Returns:
            EditResult indicating success or failure
        """
        try:
            backups = self.backup_manager.list_backups(file_path)
            if not backups:
                return EditResult(
                    success=False, changes_made=0, diff="", error="No backups found for file"
                )

            # Get the most recent backup
            latest_backup = backups[0]

            # Read current content
            current_content = Path(file_path).read_text()

            # Restore from backup
            self.backup_manager.restore_backup(latest_backup)

            # Read restored content
            restored_content = Path(file_path).read_text()

            # Generate diff
            diff = generate_unified_diff(current_content, restored_content, file_path)

            return EditResult(
                success=True, changes_made=1, diff=diff, backup_path=latest_backup.backup_path
            )

        except Exception as e:
            return EditResult(success=False, changes_made=0, diff="", error=str(e))
