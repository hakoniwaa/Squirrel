"""
Session management module for the enhanced file editing system.

This module provides session-based editing capabilities with undo/redo
functionality and transaction support.
"""

from .manager import EditSessionManager

__all__ = [
    "EditSessionManager",
]
