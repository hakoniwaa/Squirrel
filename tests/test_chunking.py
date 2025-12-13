"""Tests for event chunking."""

from datetime import datetime

import pytest

from sqrl.chunking import ChunkConfig, chunk_events, events_to_json
from sqrl.parsers.base import Event, EventKind, Role


def make_events(n: int) -> list[Event]:
    """Create n test events."""
    return [
        Event(
            ts=datetime(2024, 1, 1, 12, i % 60, i // 60),
            role=Role.USER if i % 2 == 0 else Role.ASSISTANT,
            kind=EventKind.MESSAGE,
            summary=f"Event {i}",
        )
        for i in range(n)
    ]


def test_chunk_empty_events():
    """Empty events should yield no chunks."""
    chunks = list(chunk_events([]))
    assert chunks == []


def test_chunk_small_events():
    """Events smaller than chunk_size should yield one chunk."""
    events = make_events(5)
    config = ChunkConfig(chunk_size=10, overlap=2)
    chunks = list(chunk_events(events, config))

    assert len(chunks) == 1
    assert chunks[0].is_first is True
    assert chunks[0].is_last is True
    assert len(chunks[0].events) == 5
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset == 5


def test_chunk_exact_size():
    """Events equal to chunk_size should yield one chunk."""
    events = make_events(10)
    config = ChunkConfig(chunk_size=10, overlap=2)
    chunks = list(chunk_events(events, config))

    assert len(chunks) == 1
    assert len(chunks[0].events) == 10


def test_chunk_overlap():
    """Multiple chunks should have correct overlap."""
    events = make_events(25)
    config = ChunkConfig(chunk_size=10, overlap=3)
    chunks = list(chunk_events(events, config))

    # With 25 events, chunk_size=10, overlap=3:
    # Chunk 0: events 0-9 (10 events)
    # Chunk 1: events 7-16 (10 events, starts at 10-3=7)
    # Chunk 2: events 14-23 (10 events, starts at 17-3=14)
    # Chunk 3: events 21-24 (4 events, starts at 24-3=21)
    assert len(chunks) == 4

    # First chunk
    assert chunks[0].is_first is True
    assert chunks[0].is_last is False
    assert chunks[0].start_offset == 0
    assert chunks[0].end_offset == 10

    # Middle chunks
    assert chunks[1].is_first is False
    assert chunks[1].is_last is False
    assert chunks[1].start_offset == 7

    # Last chunk
    assert chunks[-1].is_first is False
    assert chunks[-1].is_last is True
    assert chunks[-1].end_offset == 25


def test_chunk_indices():
    """Chunk indices should be sequential."""
    events = make_events(30)
    config = ChunkConfig(chunk_size=10, overlap=2)
    chunks = list(chunk_events(events, config))

    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i


def test_events_to_json():
    """Event JSON conversion should include idx field."""
    events = make_events(3)
    json_events = events_to_json(events)

    assert len(json_events) == 3
    for i, je in enumerate(json_events):
        assert je["idx"] == i
        assert "ts" in je
        assert "role" in je
        assert "kind" in je
        assert "summary" in je


def test_events_to_json_error_flag():
    """Event JSON should include is_error flag."""
    events = [
        Event(
            ts=datetime.now(),
            role=Role.TOOL,
            kind=EventKind.TOOL_RESULT,
            summary="Error occurred",
            is_error=True,
        )
    ]
    json_events = events_to_json(events)

    assert json_events[0]["is_error"] is True
