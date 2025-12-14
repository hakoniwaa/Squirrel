"""Squirrel - Local-first memory system for AI coding tools."""

__version__ = "0.1.0"

from sqrl.chunking import ChunkConfig, EventChunk, chunk_events, events_to_json
from sqrl.embeddings import (
    EmbeddingConfig,
    EmbeddingError,
    bytes_to_embedding,
    embed_text,
    embed_text_sync,
    embedding_to_bytes,
    make_embedding_getter,
)
from sqrl.ingest import IngestPipeline, IngestResult
from sqrl.memory_writer import MemoryWriter, MemoryWriterConfig, MemoryWriterOutput
from sqrl.retrieval import MemoryStore, RetrievalResult, Retriever

__all__ = [
    "ChunkConfig",
    "EventChunk",
    "chunk_events",
    "events_to_json",
    # Embeddings (IPC-002)
    "EmbeddingConfig",
    "EmbeddingError",
    "embed_text",
    "embed_text_sync",
    "embedding_to_bytes",
    "bytes_to_embedding",
    "make_embedding_getter",
    # Ingest
    "IngestPipeline",
    "IngestResult",
    # Memory Writer
    "MemoryWriter",
    "MemoryWriterConfig",
    "MemoryWriterOutput",
    # Retrieval
    "MemoryStore",
    "RetrievalResult",
    "Retriever",
]
