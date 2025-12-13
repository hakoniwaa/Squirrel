"""
Base parser interface and data models for episode extraction.

All log parsers must implement BaseParser to produce Episodes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class EventKind(str, Enum):
    MESSAGE = "message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class Frustration(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not_run"


@dataclass
class Event:
    """Single event in an episode timeline."""

    ts: datetime
    role: Role
    kind: EventKind
    summary: str
    tool_name: Optional[str] = None
    file: Optional[str] = None
    raw_snippet: Optional[str] = None
    is_error: bool = False


@dataclass
class EpisodeStats:
    """Aggregated stats for an episode."""

    error_count: int = 0
    retry_loops: int = 0
    tests_final_status: Optional[TestStatus] = None
    user_frustration: Frustration = Frustration.NONE


@dataclass
class Episode:
    """
    Compressed episode ready for Memory Writer.

    Matches events_json schema in SCHEMA-004.
    """

    session_id: str
    project_id: str
    start_ts: datetime
    end_ts: datetime
    events: list[Event] = field(default_factory=list)
    stats: EpisodeStats = field(default_factory=EpisodeStats)

    def to_events_json(self) -> dict:
        """Convert to events_json format for storage."""
        return {
            "events": [
                {
                    "ts": e.ts.isoformat(),
                    "role": e.role.value,
                    "kind": e.kind.value,
                    "tool_name": e.tool_name,
                    "file": e.file,
                    "summary": e.summary,
                    "raw_snippet": e.raw_snippet,
                }
                for e in self.events
            ],
            "stats": {
                "error_count": self.stats.error_count,
                "retry_loops": self.stats.retry_loops,
                "tests_final_status": (
                    self.stats.tests_final_status.value
                    if self.stats.tests_final_status
                    else None
                ),
                "user_frustration": self.stats.user_frustration.value,
            },
        }


class BaseParser(ABC):
    """Base class for log parsers."""

    @abstractmethod
    def get_sessions(self, project_path: Optional[Path] = None) -> list[Path]:
        """Find all session log files for a project."""
        ...

    @abstractmethod
    def parse_session(self, session_path: Path) -> list[Episode]:
        """Parse a session file into episodes."""
        ...

    def parse_all(self, project_path: Optional[Path] = None) -> list[Episode]:
        """Parse all sessions for a project."""
        episodes = []
        for session_path in self.get_sessions(project_path):
            episodes.extend(self.parse_session(session_path))
        return episodes
