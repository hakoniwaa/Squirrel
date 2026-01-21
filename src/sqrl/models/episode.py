"""Models for episode processing requests."""

from pydantic import BaseModel


class EpisodeEvent(BaseModel):
    """Single event in an episode."""

    ts: str  # ISO 8601
    role: str  # user, assistant, tool_result, tool_error
    content_summary: str


class ExistingUserStyle(BaseModel):
    """Existing user style with ID."""

    id: str
    text: str


class ExistingProjectMemory(BaseModel):
    """Existing project memory with ID."""

    id: str
    category: str
    subcategory: str
    text: str


class ProcessEpisodeRequest(BaseModel):
    """IPC-001: process_episode request params."""

    project_id: str
    project_root: str
    events: list[EpisodeEvent]
    existing_user_styles: list[ExistingUserStyle]
    existing_project_memories: list[ExistingProjectMemory]
