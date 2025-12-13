"""Squirrel - Local-first memory system for AI coding tools."""

__version__ = "0.1.0"

from sqrl.chunking import ChunkConfig, EventChunk, chunk_events, events_to_json

__all__ = ["ChunkConfig", "EventChunk", "chunk_events", "events_to_json"]
