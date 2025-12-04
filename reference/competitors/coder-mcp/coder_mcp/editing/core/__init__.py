"""
Core editing module.

This module provides the fundamental building blocks for the enhanced
file editing system, including types, editors, and utilities.
"""

from .editor import EnhancedFileEditor
from .types import (
    ASTTransformation,
    BackupError,
    BackupInfo,
    EditApplicationError,
    EditConfig,
    EditDict,
    EditError,
    EditExample,
    EditList,
    EditResult,
    EditSession,
    EditStrategy,
    EditType,
    EditValidationError,
    FileEdit,
    FileEditMap,
    FileNotFoundError,
    MultiEditResult,
    PreviewResult,
    SessionNotFoundError,
)

__all__ = [
    # Enums
    "EditType",
    "EditStrategy",
    # Data classes
    "FileEdit",
    "EditResult",
    "EditSession",
    "EditConfig",
    "MultiEditResult",
    "ASTTransformation",
    "EditExample",
    "PreviewResult",
    "BackupInfo",
    # Exceptions
    "EditError",
    "EditValidationError",
    "EditApplicationError",
    "SessionNotFoundError",
    "FileNotFoundError",
    "BackupError",
    # Type aliases
    "EditList",
    "EditDict",
    "FileEditMap",
    # Editor classes
    "EnhancedFileEditor",
]
