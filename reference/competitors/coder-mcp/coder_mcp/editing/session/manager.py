"""
Session management for the enhanced file editing system.

This module provides the EditSessionManager class for managing editing sessions
with undo/redo functionality and transaction support.
"""

import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.editor import EnhancedFileEditor
from ..core.types import (
    EditConfig,
    EditResult,
    EditSession,
    FileEdit,
    SessionNotFoundError,
)
from ..utils.backup import BackupManager
from .persistence import SessionPersistence


class EditSessionManager:
    """
    Manages editing sessions with history and undo/redo functionality.

    Provides session-based editing with transaction support, allowing
    for complex multi-step edits with rollback capabilities.
    """

    def __init__(self, config: Optional[EditConfig] = None, workspace_root: Optional[str] = None):
        """
        Initialize the session manager.

        Args:
            config: Optional configuration for editing operations
            workspace_root: Optional workspace root path (for backward compatibility)
        """
        self.config = config or EditConfig()
        self.workspace_root = workspace_root
        self.sessions: Dict[str, EditSession] = {}
        self.editor = EnhancedFileEditor(config)
        self.backup_manager = BackupManager(
            self.config.backup_location, self.config.backup_retention_days
        )
        self.persistence = SessionPersistence()

        # Load existing sessions from disk
        self._load_persisted_sessions()

    def _load_persisted_sessions(self) -> None:
        """Load persisted sessions from disk."""
        try:
            # Get list of session summaries
            session_summaries = self.persistence.list_sessions()

            # Load each session individually
            for summary in session_summaries:
                session_id = summary["session_id"]
                session = self.persistence.load_session(session_id)
                if session:
                    self.sessions[session_id] = session
        except Exception:
            # If loading fails, start with empty sessions
            pass

    def create_session(self, files: List[str], session_id: Optional[str] = None) -> EditSession:
        """
        Create a new editing session.

        Args:
            files: List of files that may be edited in this session
            session_id: Optional session ID (generated if not provided)

        Returns:
            EditSession object
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        # Validate only existing files, but allow empty list
        valid_files = []
        for file_path in files:
            if Path(file_path).exists():
                valid_files.append(file_path)
            # Don't raise error for non-existent files, just skip them
        session = EditSession(
            session_id=session_id,
            files=valid_files,
            created_at=time.time(),
            last_activity=time.time(),
            history=[],
            current_index=-1,
        )

        self.sessions[session_id] = session

        # Save session to disk
        self.persistence.save_session(session)
        return session

    def get_session(self, session_id: str) -> EditSession:
        """
        Get an existing session.

        Args:
            session_id: ID of the session to retrieve

        Returns:
            EditSession object

        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session not found: {session_id}")

        session = self.sessions[session_id]
        session.update_activity()
        return session

    def add_file_to_session(self, session_id: str, file_path: str) -> bool:
        """
        Add a file to an existing session.

        Args:
            session_id: Session identifier
            file_path: Path to file to add

        Returns:
            True if file was added successfully
        """
        session = self.sessions.get(session_id)
        if not session:
            return False

        # Resolve the file path
        from ..tools import resolve_file_path

        resolved_path = resolve_file_path(file_path)

        if resolved_path not in session.files:
            session.files.append(resolved_path)
            session.update_activity()

        return True

    def apply_edit(
        self,
        session_id: str,
        file_path: str,
        edits: List[FileEdit],
        description: Optional[str] = None,
    ) -> EditResult:
        """
        Apply an edit within a session.

        Args:
            session_id: ID of the session
            file_path: Path to the file to edit
            edits: List of edit operations
            description: Optional description of the edit

        Returns:
            EditResult with session state information
        """
        session = self.get_session(session_id)

        # Resolve the file path
        from ..tools import resolve_file_path

        resolved_path = resolve_file_path(file_path)

        # Auto-add file to session if not present
        if resolved_path not in session.files:
            self.add_file_to_session(session_id, file_path)

        # Create backup before edit
        backup_info = self.backup_manager.create_backup(resolved_path)

        # Apply the edit
        result = self.editor.edit_file(resolved_path, edits, create_backup=False)

        if result.success:
            # Clear any future history (we're creating a new branch)
            session.history = session.history[: session.current_index + 1]

            # Add to history
            history_entry = {
                "timestamp": time.time(),
                "file_path": resolved_path,
                "edits": [self._edit_to_dict(edit) for edit in edits],
                "description": description or f"Edit {file_path}",
                "backup_path": backup_info.backup_path,
                "result": {
                    "success": result.success,
                    "changes_made": result.changes_made,
                    "diff": result.diff,
                },
            }

            session.history.append(history_entry)
            session.current_index += 1
            session.update_activity()

            # Add session info to result
            result.warnings = result.warnings or []
            result.warnings.append(f"Session: {session_id}, History: {len(session.history)}")

        return result

    def undo(self, session_id: str) -> EditResult:
        """
        Undo the last edit in a session.

        Args:
            session_id: ID of the session

        Returns:
            EditResult indicating success or failure
        """
        session = self.get_session(session_id)

        if session.current_index < 0:
            return EditResult(success=False, changes_made=0, diff="", error="Nothing to undo")

        # Get the edit to undo
        edit_entry = session.history[session.current_index]
        backup_path = edit_entry["backup_path"]
        file_path = edit_entry["file_path"]

        try:
            # Read current content
            current_content = Path(file_path).read_text()

            # Restore from backup
            backup_info = None
            for backup in self.backup_manager.list_backups(file_path):
                if backup.backup_path == backup_path:
                    backup_info = backup
                    break

            if not backup_info:
                return EditResult(
                    success=False, changes_made=0, diff="", error="Backup not found for undo"
                )

            # Restore the backup
            self.backup_manager.restore_backup(backup_info)

            # Read restored content
            restored_content = Path(file_path).read_text()

            # Generate diff
            from ..utils.diff import generate_unified_diff

            diff = generate_unified_diff(current_content, restored_content, file_path)

            # Update session state
            session.current_index -= 1
            session.update_activity()

            return EditResult(success=True, changes_made=1, diff=diff, backup_path=backup_path)

        except Exception as e:
            return EditResult(
                success=False, changes_made=0, diff="", error=f"Undo failed: {str(e)}"
            )

    def redo(self, session_id: str) -> EditResult:
        """
        Redo an undone edit in a session.

        Args:
            session_id: ID of the session

        Returns:
            EditResult indicating success or failure
        """
        session = self.get_session(session_id)

        if session.current_index >= len(session.history) - 1:
            return EditResult(success=False, changes_made=0, diff="", error="Nothing to redo")

        # Move to next edit
        session.current_index += 1
        edit_entry = session.history[session.current_index]

        # Reconstruct and apply the edit
        file_path = edit_entry["file_path"]
        edits = [self._dict_to_edit(edit_dict) for edit_dict in edit_entry["edits"]]

        # Apply the edit
        result = self.editor.edit_file(file_path, edits, create_backup=False)

        if result.success:
            session.update_activity()
        else:
            # Revert index if edit failed
            session.current_index -= 1

        return result

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about a session.

        Args:
            session_id: ID of the session

        Returns:
            Dictionary with session information
        """
        session = self.get_session(session_id)

        return {
            "session_id": session.session_id,
            "files": session.files,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "history_length": len(session.history),
            "current_index": session.current_index,
            "can_undo": session.current_index >= 0,
            "can_redo": session.current_index < len(session.history) - 1,
            "recent_edits": [
                {
                    "timestamp": entry["timestamp"],
                    "file_path": entry["file_path"],
                    "description": entry["description"],
                }
                for entry in session.history[-5:]  # Last 5 edits
            ],
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active sessions.

        Returns:
            List of session information dictionaries
        """
        return [
            {
                "session_id": session.session_id,
                "files": session.files,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "history_length": len(session.history),
            }
            for session in self.sessions.values()
        ]

    def close_session(self, session_id: str) -> bool:
        """
        Close and remove a session.

        Args:
            session_id: ID of the session to close

        Returns:
            True if session was closed, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old inactive sessions.

        Args:
            max_age_hours: Maximum age in hours for keeping sessions

        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = time.time() - (max_age_hours * 3600)
        old_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if session.last_activity < cutoff_time
        ]

        for session_id in old_sessions:
            del self.sessions[session_id]

        return len(old_sessions)

    def _edit_to_dict(self, edit: FileEdit) -> Dict[str, Any]:
        """
        Convert FileEdit to dictionary for serialization.

        Args:
            edit: FileEdit object

        Returns:
            Dictionary representation
        """
        return {
            "type": edit.type.value,
            "start_line": edit.start_line,
            "end_line": edit.end_line,
            "pattern": edit.pattern,
            "replacement": edit.replacement,
            "content": edit.content,
            "target_line": edit.target_line,
            "strategy": edit.strategy.value,
        }

    def _dict_to_edit(self, edit_dict: Dict[str, Any]) -> FileEdit:
        """
        Convert dictionary to FileEdit object.

        Args:
            edit_dict: Dictionary representation

        Returns:
            FileEdit object
        """
        from ..core.types import EditStrategy, EditType

        return FileEdit(
            type=EditType(edit_dict["type"]),
            start_line=edit_dict.get("start_line"),
            end_line=edit_dict.get("end_line"),
            pattern=edit_dict.get("pattern"),
            replacement=edit_dict.get("replacement"),
            content=edit_dict.get("content"),
            target_line=edit_dict.get("target_line"),
            strategy=EditStrategy(edit_dict.get("strategy", "line_based")),
        )
