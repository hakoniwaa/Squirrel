"""Models for LLM extraction outputs."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class CleanerOutput(BaseModel):
    """PROMPT-001: Log Cleaner output."""

    skip: bool
    skip_reason: Optional[str] = None
    correction_context: Optional[str] = None


class MemoryOperation(str, Enum):
    """Memory operation type."""

    ADD = "ADD"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class UserStyleOp(BaseModel):
    """User style operation."""

    op: MemoryOperation
    text: Optional[str] = None  # For ADD/UPDATE
    target_id: Optional[str] = None  # For UPDATE/DELETE


class ProjectMemoryOp(BaseModel):
    """Project memory operation."""

    op: MemoryOperation
    category: Optional[str] = None  # For ADD
    subcategory: Optional[str] = "main"  # For ADD
    text: Optional[str] = None  # For ADD/UPDATE
    target_id: Optional[str] = None  # For UPDATE/DELETE


class ExtractorOutput(BaseModel):
    """PROMPT-002: Memory Extractor output."""

    user_styles: list[UserStyleOp] = []
    project_memories: list[ProjectMemoryOp] = []
    skip_reason: Optional[str] = None
