"""
Event chunking for Memory Writer.

Splits raw events into chunks for LLM processing.
Chunk size and overlap are configurable (TBD via testing).
"""

from dataclasses import dataclass
from typing import Iterator, Optional

from sqrl.parsers.base import Event


@dataclass
class ChunkConfig:
    """Configuration for event chunking."""

    chunk_size: int = 100  # TBD via testing
    overlap: int = 10  # TBD via testing


@dataclass
class EventChunk:
    """A chunk of events for Memory Writer processing."""

    events: list[Event]
    chunk_index: int
    is_first: bool
    is_last: bool
    # Indices relative to original event list
    start_offset: int
    end_offset: int


def chunk_events(
    events: list[Event],
    config: Optional[ChunkConfig] = None,
) -> Iterator[EventChunk]:
    """
    Split events into overlapping chunks for Memory Writer.

    Yields EventChunk objects with:
    - events: List of Event objects for this chunk
    - chunk_index: 0-based chunk number
    - is_first/is_last: Boundary markers
    - start_offset/end_offset: Position in original list

    The overlap ensures context continuity across chunks.
    Memory Writer uses carry_state for semantic continuity.
    """
    if config is None:
        config = ChunkConfig()

    if not events:
        return

    total = len(events)
    chunk_index = 0
    start = 0

    while start < total:
        end = min(start + config.chunk_size, total)
        chunk_events_list = events[start:end]

        yield EventChunk(
            events=chunk_events_list,
            chunk_index=chunk_index,
            is_first=(chunk_index == 0),
            is_last=(end >= total),
            start_offset=start,
            end_offset=end,
        )

        # Move start forward, accounting for overlap
        # But don't overlap if this is the last chunk
        if end >= total:
            break

        start = end - config.overlap
        chunk_index += 1


def events_to_json(events: list[Event]) -> list[dict]:
    """
    Convert events to JSON format for Memory Writer input.

    Adds idx field for episode boundary referencing.
    """
    return [
        {
            "idx": idx,
            "ts": e.ts.isoformat(),
            "role": e.role.value,
            "kind": e.kind.value,
            "summary": e.summary,
            "tool_name": e.tool_name,
            "file": e.file,
            "is_error": e.is_error,
        }
        for idx, e in enumerate(events)
    ]
