"""
Utility modules for the enhanced file editing system.

This module provides various utilities for diff generation, backup management,
and other supporting functionality.
"""

from .backup import (
    BackupManager,
    cleanup_backups,
    create_backup,
    restore_from_backup,
)
from .diff import (
    apply_diff_to_content,
    count_changes,
    create_side_by_side_diff,
    diff_summary,
    generate_inline_diff,
    generate_unified_diff,
    parse_unified_diff,
)

__all__ = [
    # Diff utilities
    "generate_unified_diff",
    "generate_inline_diff",
    "parse_unified_diff",
    "count_changes",
    "apply_diff_to_content",
    "create_side_by_side_diff",
    "diff_summary",
    # Backup utilities
    "BackupManager",
    "create_backup",
    "restore_from_backup",
    "cleanup_backups",
]
