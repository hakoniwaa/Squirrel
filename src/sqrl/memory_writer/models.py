"""Pydantic models for Memory Writer input/output."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OpType(str, Enum):
    """Memory operation types."""

    ADD = "ADD"
    UPDATE = "UPDATE"
    DEPRECATE = "DEPRECATE"


class Scope(str, Enum):
    """Memory scope."""

    GLOBAL = "global"
    PROJECT = "project"
    REPO_PATH = "repo_path"


class OwnerType(str, Enum):
    """Memory owner type."""

    USER = "user"
    TEAM = "team"
    ORG = "org"


class MemoryKind(str, Enum):
    """Memory kind/category."""

    PREFERENCE = "preference"
    INVARIANT = "invariant"
    PATTERN = "pattern"
    GUARD = "guard"
    NOTE = "note"


class MemoryTier(str, Enum):
    """Memory tier/priority."""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EMERGENCY = "emergency"


class EvidenceSource(str, Enum):
    """Source of evidence for a memory."""

    FAILURE_THEN_SUCCESS = "failure_then_success"
    USER_CORRECTION = "user_correction"
    EXPLICIT_STATEMENT = "explicit_statement"
    PATTERN_OBSERVED = "pattern_observed"
    GUARD_TRIGGERED = "guard_triggered"


class Frustration(str, Enum):
    """User frustration level."""

    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class EpisodeBoundary(BaseModel):
    """Detected episode boundary within a chunk."""

    start_idx: int = Field(description="Start index in events array")
    end_idx: int = Field(description="End index in events array")
    label: str = Field(description="Semantic label for the episode")


class Evidence(BaseModel):
    """Evidence for a memory operation."""

    source: EvidenceSource
    frustration: Frustration = Frustration.NONE


class MemoryOp(BaseModel):
    """A memory operation from Memory Writer."""

    op: OpType
    target_memory_id: Optional[str] = Field(
        default=None, description="Required for UPDATE/DEPRECATE"
    )
    episode_idx: int = Field(description="Index into episodes array")
    scope: Scope
    owner_type: OwnerType
    owner_id: str
    kind: MemoryKind
    tier: MemoryTier = MemoryTier.SHORT_TERM
    polarity: int = Field(default=1, ge=-1, le=1)
    key: Optional[str] = None
    text: str = Field(description="Human-readable memory text")
    ttl_days: Optional[int] = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: Evidence


class MemoryWriterOutput(BaseModel):
    """Complete output from Memory Writer."""

    episodes: list[EpisodeBoundary] = Field(default_factory=list)
    memories: list[MemoryOp] = Field(default_factory=list)
    discard_reason: Optional[str] = None
    carry_state: Optional[str] = None
