"""
Enhanced error types for the editing system.
Provides specific exception classes for better error handling.
"""

from typing import Any, Dict, Optional


class EditError(Exception):
    """Base exception for all editing errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize edit error with message and optional details.

        Args:
            message: Error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.details = details or {}
        self.error_type = self.__class__.__name__


class FileNotFoundError(EditError):
    """Raised when a file to edit is not found."""

    def __init__(self, file_path: str):
        super().__init__(f"File not found: {file_path}", {"file_path": file_path})


class FilePermissionError(EditError):
    """Raised when there are permission issues with a file."""

    def __init__(self, file_path: str, operation: str):
        super().__init__(
            f"Permission denied for {operation} on: {file_path}",
            {"file_path": file_path, "operation": operation},
        )


class SyntaxValidationError(EditError):
    """Raised when edited code has syntax errors."""

    def __init__(self, file_path: str, line: int, column: int, error_msg: str):
        super().__init__(
            f"Syntax error in {file_path} at line {line}, column {column}: {error_msg}",
            {"file_path": file_path, "line": line, "column": column, "syntax_error": error_msg},
        )


class EditValidationError(EditError):
    """Raised when an edit operation is invalid."""

    def __init__(self, edit_type: str, reason: str, **kwargs):
        super().__init__(
            f"Invalid {edit_type} edit: {reason}",
            {"edit_type": edit_type, "reason": reason, **kwargs},
        )


class ConcurrentEditError(EditError):
    """Raised when concurrent edits conflict."""

    def __init__(self, file_path: str, conflict_details: Dict[str, Any]):
        super().__init__(
            f"Concurrent edit conflict in {file_path}",
            {"file_path": file_path, "conflicts": conflict_details},
        )


class PatternNotFoundError(EditError):
    """Raised when a pattern to replace is not found."""

    def __init__(self, pattern: str, file_path: str):
        super().__init__(
            f"Pattern '{pattern}' not found in {file_path}",
            {"pattern": pattern, "file_path": file_path},
        )


class FileSizeError(EditError):
    """Raised when a file is too large to edit."""

    def __init__(self, file_path: str, size_mb: float, max_size_mb: float):
        super().__init__(
            f"File {file_path} is too large ({size_mb:.1f}MB). Maximum size is {max_size_mb}MB",
            {"file_path": file_path, "size_mb": size_mb, "max_size_mb": max_size_mb},
        )


class BackupError(EditError):
    """Raised when backup operations fail."""

    def __init__(self, message: str):
        super().__init__(message)


class SessionError(EditError):
    """Base class for session-related errors."""

    pass


class SessionNotFoundError(SessionError):
    """Raised when a session ID is not found."""

    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}", {"session_id": session_id})


class SessionExpiredError(SessionError):
    """Raised when a session has expired."""

    def __init__(self, session_id: str, expired_at: float):
        super().__init__(
            f"Session {session_id} has expired",
            {"session_id": session_id, "expired_at": expired_at},
        )


class UndoError(EditError):
    """Raised when undo operation fails."""

    def __init__(self, reason: str, session_id: Optional[str] = None):
        super().__init__(f"Undo failed: {reason}", {"reason": reason, "session_id": session_id})


class RedoError(EditError):
    """Raised when redo operation fails."""

    def __init__(self, reason: str, session_id: Optional[str] = None):
        super().__init__(f"Redo failed: {reason}", {"reason": reason, "session_id": session_id})
