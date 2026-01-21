"""IPC method handlers."""

from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from sqrl.agents import LogCleaner, MemoryExtractor
from sqrl.models import ProcessEpisodeRequest, ProcessEpisodeResponse

log = structlog.get_logger()

Handler = Callable[[dict[str, Any]], Awaitable[Any]]


async def handle_process_episode(params: dict[str, Any]) -> dict[str, Any]:
    """IPC-001: process_episode handler."""
    # Parse request
    try:
        request = ProcessEpisodeRequest(**params)
    except Exception as e:
        raise ValueError(f"Invalid params: {e}") from e

    log.info(
        "process_episode_start",
        project_id=request.project_id,
        events_count=len(request.events),
    )

    # Stage 1: Log Cleaner
    cleaner = LogCleaner()
    cleaner_output = await cleaner.clean(request.project_id, request.events)

    if cleaner_output.skip:
        log.info(
            "episode_skipped",
            reason=cleaner_output.skip_reason,
        )
        return ProcessEpisodeResponse(
            skipped=True,
            skip_reason=cleaner_output.skip_reason,
        ).model_dump()

    # Stage 2: Memory Extractor
    extractor = MemoryExtractor()
    extractor_output = await extractor.extract(
        project_id=request.project_id,
        project_root=request.project_root,
        correction_context=cleaner_output.correction_context or "",
        existing_user_styles=request.existing_user_styles,
        existing_project_memories=request.existing_project_memories,
    )

    log.info(
        "process_episode_done",
        user_styles_count=len(extractor_output.user_styles),
        project_memories_count=len(extractor_output.project_memories),
    )

    return ProcessEpisodeResponse(
        skipped=False,
        user_styles=extractor_output.user_styles,
        project_memories=extractor_output.project_memories,
    ).model_dump()


def create_handlers() -> dict[str, Handler]:
    """Create all IPC handlers."""
    return {
        "process_episode": handle_process_episode,
    }
