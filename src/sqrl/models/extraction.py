"""Models for LLM extraction outputs."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ScannerOutput(BaseModel):
    """PROMPT-001: User Scanner output.

    Returns indices of messages with behavioral patterns worth extracting.
    """

    has_patterns: bool
    indices: list[int] = []


class MemoryOperation(str, Enum):
    """Memory operation type."""

    ADD = "ADD"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class UserStyleOp(BaseModel):
    """User style operation with confidence score."""

    op: MemoryOperation
    text: Optional[str] = None  # For ADD/UPDATE
    target_id: Optional[str] = None  # For UPDATE/DELETE
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class ProjectMemoryOp(BaseModel):
    """Project memory operation with confidence score."""

    op: MemoryOperation
    category: Optional[str] = None  # For ADD
    subcategory: Optional[str] = "main"  # For ADD
    text: Optional[str] = None  # For ADD/UPDATE
    target_id: Optional[str] = None  # For UPDATE/DELETE
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


# Confidence threshold for storing memories (no user review in v1)
CONFIDENCE_THRESHOLD = 0.8


class ExtractorOutput(BaseModel):
    """PROMPT-002: Memory Extractor output."""

    user_styles: list[UserStyleOp] = []
    project_memories: list[ProjectMemoryOp] = []
    skip_reason: Optional[str] = None

    def filter_by_confidence(self, threshold: float = CONFIDENCE_THRESHOLD) -> "ExtractorOutput":
        """Return a new ExtractorOutput with only high-confidence memories."""
        return ExtractorOutput(
            user_styles=[s for s in self.user_styles if s.confidence >= threshold],
            project_memories=[m for m in self.project_memories if m.confidence >= threshold],
            skip_reason=self.skip_reason,
        )
