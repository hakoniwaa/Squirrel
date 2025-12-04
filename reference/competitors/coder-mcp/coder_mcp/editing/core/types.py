"""
Core types for the enhanced file editing system.

This module defines the fundamental data structures used throughout
the editing system, including edit operations, results, and configurations.
"""

import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class EditType(Enum):
    """Types of edit operations supported by the system."""

    REPLACE = "replace"
    INSERT = "insert"
    DELETE = "delete"
    MOVE = "move"
    PATTERN_BASED = "pattern_based"


class EditStrategy(Enum):
    """Strategy for applying edits."""

    LINE_BASED = "line_based"
    PATTERN_BASED = "pattern_based"
    AST_BASED = "ast_based"
    AI_BASED = "ai_based"


@dataclass
class FileEdit:
    """Represents a single edit operation on a file."""

    type: EditType
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    pattern: Optional[str] = None
    replacement: Optional[str] = None
    content: Optional[str] = None
    new_content: Optional[str] = None
    target_line: Optional[int] = None  # for move operations
    strategy: EditStrategy = EditStrategy.LINE_BASED

    def __post_init__(self):
        """Validate the edit operation."""
        if self.type == EditType.REPLACE:
            if not (self.start_line or self.pattern):
                raise ValueError("REPLACE edit requires either start_line or pattern")
        elif self.type == EditType.INSERT:
            if not (self.target_line and self.content):
                raise ValueError("INSERT edit requires target_line and content")
        elif self.type == EditType.DELETE:
            if not (self.start_line or self.pattern):
                raise ValueError("DELETE edit requires either start_line or pattern")
        elif self.type == EditType.MOVE:
            if not (self.start_line and self.target_line):
                raise ValueError("MOVE edit requires start_line and target_line")


@dataclass
class EditResult:
    """Result of an edit operation."""

    success: bool
    changes_made: int
    diff: str
    message: Optional[str] = None
    backup_path: Optional[str] = None
    error: Optional[str] = None
    preview: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class EditSession:
    """Represents an editing session with history."""

    session_id: str
    files: List[str]
    created_at: float
    last_activity: float
    history: List[Dict[str, Any]] = field(default_factory=list)
    current_index: int = -1

    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = time.time()


@dataclass
class EditConfig:
    """Configuration for editing operations."""

    backup_enabled: bool = True
    backup_location: str = str(Path(tempfile.gettempdir()) / "coder_mcp_backups")
    backup_retention_days: int = 7
    max_file_size_mb: int = 10
    preserve_formatting: bool = True
    validate_syntax: bool = True
    atomic_operations: bool = True
    parallel_edits: bool = True
    cache_ast: bool = True

    # AI settings
    ai_model: str = "gpt-4"
    ai_temperature: float = 0.2
    ai_max_retries: int = 3

    # Safety settings
    create_backups: bool = True
    preview_by_default: bool = False


@dataclass
class MultiEditResult:
    """Result of multi-file editing operations."""

    success: bool
    results: Dict[str, EditResult]
    total_changes: int
    failed_files: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    transaction_id: Optional[str] = None


@dataclass
class ASTTransformation:
    """Represents an AST-based transformation."""

    node_type: str
    transformation_type: str
    target_name: Optional[str] = None
    new_name: Optional[str] = None
    new_content: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EditExample:
    """Example for AI-powered editing."""

    instruction: str
    before: str
    after: str
    explanation: str


@dataclass
class PreviewResult:
    """Result of previewing an edit."""

    original_content: str
    modified_content: str
    diff: str
    changes_count: int
    warnings: List[str] = field(default_factory=list)


@dataclass
class BackupInfo:
    """Information about a file backup."""

    original_path: str
    backup_path: str
    timestamp: float
    size: int
    checksum: str


class EditError(Exception):
    """Base exception for editing operations."""

    pass


class EditValidationError(EditError):
    """Raised when edit validation fails."""

    pass


class EditApplicationError(EditError):
    """Raised when applying an edit fails."""

    pass


class SessionNotFoundError(EditError):
    """Raised when an edit session is not found."""

    pass


class FileNotFoundError(EditError):
    """Raised when a file to edit is not found."""

    pass


class BackupError(EditError):
    """Raised when backup operations fail."""

    pass


# Type aliases for convenience
EditList = List[FileEdit]
EditDict = Dict[str, Any]
FileEditMap = Dict[str, EditList]
