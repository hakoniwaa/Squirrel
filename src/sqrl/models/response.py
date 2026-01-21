"""Models for IPC responses."""

from typing import Optional

from pydantic import BaseModel

from sqrl.models.extraction import ProjectMemoryOp, UserStyleOp


class ProcessEpisodeResponse(BaseModel):
    """IPC-001: process_episode response."""

    skipped: bool
    skip_reason: Optional[str] = None
    user_styles: list[UserStyleOp] = []
    project_memories: list[ProjectMemoryOp] = []
