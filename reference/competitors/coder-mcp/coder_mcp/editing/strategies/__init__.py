"""
Enhanced file editing strategies.

This module provides different strategies for applying edits to files,
including AI-powered editing and pattern-based editing.
"""

from .ai_editor import AIFileEditor
from .pattern_based import apply_multiple_pattern_edits, apply_pattern_edit, validate_pattern

__all__ = [
    "AIFileEditor",
    "apply_pattern_edit",
    "apply_multiple_pattern_edits",
    "validate_pattern",
]
