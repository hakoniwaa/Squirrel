"""
Session persistence for the editing system.
Provides save/load functionality for edit sessions.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.types import EditSession, EditStrategy, EditType, FileEdit


class SessionPersistence:
    """Handles saving and loading edit sessions to/from disk."""

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize session persistence.

        Args:
            storage_dir: Directory to store session files (default: ~/.coder_mcp/sessions)
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / ".coder_mcp" / "sessions"

        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, session: EditSession) -> bool:
        """
        Save a session to disk.

        Args:
            session: EditSession to save

        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = self.storage_dir / f"{session.session_id}.json"

            # Convert session to JSON-serializable format
            session_data = {
                "session_id": session.session_id,
                "files": session.files,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "history": self._serialize_history(session.history),
                "current_index": session.current_index,
                "metadata": {"saved_at": time.time(), "version": "1.0"},
            }

            # Write to file
            session_file.write_text(json.dumps(session_data, indent=2))
            return True

        except Exception as e:
            print(f"Error saving session {session.session_id}: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[EditSession]:
        """
        Load a session from disk.

        Args:
            session_id: ID of session to load

        Returns:
            EditSession if found and valid, None otherwise
        """
        try:
            session_file = self.storage_dir / f"{session_id}.json"

            if not session_file.exists():
                return None

            # Read and parse session data
            session_data = json.loads(session_file.read_text())

            # Reconstruct session
            session = EditSession(
                session_id=session_data["session_id"],
                files=session_data["files"],
                created_at=session_data["created_at"],
                last_activity=session_data["last_activity"],
                history=self._deserialize_history(session_data["history"]),
                current_index=session_data["current_index"],
            )

            return session

        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all saved sessions.

        Returns:
            List of session summaries
        """
        sessions = []

        for session_file in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(session_file.read_text())
                sessions.append(
                    {
                        "session_id": data["session_id"],
                        "created_at": data["created_at"],
                        "last_activity": data["last_activity"],
                        "files_count": len(data["files"]),
                        "history_length": len(data["history"]),
                        "saved_at": data["metadata"]["saved_at"],
                    }
                )
            except (json.JSONDecodeError, KeyError, OSError):
                continue

        # Sort by last activity (most recent first)
        sessions.sort(key=lambda x: x["last_activity"], reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a saved session.

        Args:
            session_id: ID of session to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                return True
            return False
        except (OSError, PermissionError):
            return False

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Remove sessions older than specified days.

        Args:
            days: Remove sessions older than this many days

        Returns:
            Number of sessions removed
        """
        removed = 0
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        for session_file in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(session_file.read_text())
                if data["last_activity"] < cutoff_time:
                    session_file.unlink()
                    removed += 1
            except (json.JSONDecodeError, KeyError, OSError):
                continue

        return removed

    def _serialize_history(self, history: List[Dict]) -> List[Dict]:
        """Serialize edit history for JSON storage."""
        serialized = []

        for entry in history:
            serialized_entry = {
                "timestamp": entry.get("timestamp", time.time()),
                "file_path": entry.get("file_path", ""),
                "description": entry.get("description", ""),
                "edits": [],
            }

            # Serialize FileEdit objects
            if "edits" in entry:
                for edit in entry["edits"]:
                    if isinstance(edit, FileEdit):
                        serialized_entry["edits"].append(
                            {
                                "type": edit.type.value,
                                "start_line": edit.start_line,
                                "end_line": edit.end_line,
                                "pattern": edit.pattern,
                                "replacement": edit.replacement,
                                "content": edit.content,
                                "target_line": edit.target_line,
                                "strategy": edit.strategy.value,
                            }
                        )
                    else:
                        serialized_entry["edits"].append(edit)

            serialized.append(serialized_entry)

        return serialized

    def _deserialize_history(self, history: List[Dict]) -> List[Dict]:
        """Deserialize edit history from JSON storage."""
        deserialized = []

        for entry in history:
            deserialized_entry = {
                "timestamp": entry.get("timestamp", time.time()),
                "file_path": entry.get("file_path", ""),
                "description": entry.get("description", ""),
                "edits": [],
            }

            # Deserialize FileEdit objects
            if "edits" in entry:
                for edit_data in entry["edits"]:
                    if isinstance(edit_data, dict) and "type" in edit_data:
                        try:
                            file_edit = FileEdit(
                                type=EditType(edit_data["type"]),
                                start_line=edit_data.get("start_line"),
                                end_line=edit_data.get("end_line"),
                                pattern=edit_data.get("pattern"),
                                replacement=edit_data.get("replacement"),
                                content=edit_data.get("content"),
                                target_line=edit_data.get("target_line"),
                                strategy=EditStrategy(edit_data.get("strategy", "line_based")),
                            )
                            deserialized_entry["edits"].append(file_edit)
                        except (ValueError, TypeError, KeyError):
                            # If deserialization fails, keep original data
                            deserialized_entry["edits"].append(edit_data)
                    else:
                        deserialized_entry["edits"].append(edit_data)

            deserialized.append(deserialized_entry)

        return deserialized

    def export_session(self, session_id: str, export_path: str) -> bool:
        """
        Export a session to a specific location.

        Args:
            session_id: ID of session to export
            export_path: Path to export to

        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                Path(export_path).write_text(session_file.read_text())
                return True
            return False
        except (OSError, PermissionError, json.JSONDecodeError):
            return False

    def import_session(self, import_path: str) -> Optional[str]:
        """
        Import a session from a file.

        Args:
            import_path: Path to import from

        Returns:
            Session ID if successful, None otherwise
        """
        try:
            data = json.loads(Path(import_path).read_text())
            session_id = data.get("session_id")

            if session_id and isinstance(session_id, str):
                session_file = self.storage_dir / f"{session_id}.json"
                session_file.write_text(json.dumps(data, indent=2))
                return str(session_id)

            return None
        except (json.JSONDecodeError, OSError, KeyError):
            return None
