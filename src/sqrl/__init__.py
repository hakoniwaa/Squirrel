"""Squirrel - Local-first memory system for AI coding tools."""

__version__ = "0.1.0"

from sqrl.chunking import ChunkConfig, EventChunk, chunk_events, events_to_json
from sqrl.ingest import IngestPipeline, IngestResult
from sqrl.memory_writer import MemoryWriter, MemoryWriterConfig, MemoryWriterOutput
from sqrl.retrieval import MemoryStore, RetrievalResult, Retriever

__all__ = [
    "ChunkConfig",
    "EventChunk",
    "chunk_events",
    "events_to_json",
    "IngestPipeline",
    "IngestResult",
    "MemoryStore",
    "MemoryWriter",
    "MemoryWriterConfig",
    "MemoryWriterOutput",
    "RetrievalResult",
    "Retriever",
]
