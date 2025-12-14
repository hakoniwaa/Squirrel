"""
Embeddings module for Squirrel (IPC-002).

Handles text embedding generation for memory storage and retrieval.
Uses LiteLLM for provider-agnostic embeddings.
"""

import os
import struct
from dataclasses import dataclass
from typing import Optional

import litellm


class EmbeddingError(Exception):
    """Error during embedding generation."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


# Error codes per IPC-002 spec
ERROR_EMPTY_TEXT = -32040
ERROR_EMBEDDING_FAILED = -32041


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation.

    Attributes:
        model: Embedding model to use (default: text-embedding-3-small)
        dimensions: Expected embedding dimensions (default: 1536)
    """

    model: str = "text-embedding-3-small"
    dimensions: int = 1536

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Create config from environment variables."""
        return cls(
            model=os.getenv("SQRL_EMBEDDING_MODEL", "text-embedding-3-small"),
            dimensions=int(os.getenv("SQRL_EMBEDDING_DIMS", "1536")),
        )


async def embed_text(
    text: str,
    config: Optional[EmbeddingConfig] = None,
) -> list[float]:
    """
    Generate embedding for text (IPC-002).

    Args:
        text: Text to embed (must not be empty)
        config: Optional embedding config

    Returns:
        1536-dim float32 vector

    Raises:
        EmbeddingError: With code -32040 if text empty, -32041 if API fails
    """
    if not text or not text.strip():
        raise EmbeddingError(ERROR_EMPTY_TEXT, "Empty text")

    cfg = config or EmbeddingConfig.from_env()

    try:
        response = await litellm.aembedding(
            model=cfg.model,
            input=text,
        )
        return response.data[0]["embedding"]
    except Exception as e:
        raise EmbeddingError(ERROR_EMBEDDING_FAILED, f"Embedding error: {e}") from e


def embed_text_sync(
    text: str,
    config: Optional[EmbeddingConfig] = None,
) -> list[float]:
    """
    Synchronous version of embed_text (IPC-002).

    Args:
        text: Text to embed (must not be empty)
        config: Optional embedding config

    Returns:
        1536-dim float32 vector

    Raises:
        EmbeddingError: With code -32040 if text empty, -32041 if API fails
    """
    if not text or not text.strip():
        raise EmbeddingError(ERROR_EMPTY_TEXT, "Empty text")

    cfg = config or EmbeddingConfig.from_env()

    try:
        response = litellm.embedding(
            model=cfg.model,
            input=text,
        )
        return response.data[0]["embedding"]
    except Exception as e:
        raise EmbeddingError(ERROR_EMBEDDING_FAILED, f"Embedding error: {e}") from e


def embedding_to_bytes(embedding: list[float]) -> bytes:
    """
    Convert embedding list to bytes for SQLite storage.

    Uses little-endian float32 format for sqlite-vec compatibility.

    Args:
        embedding: List of float values

    Returns:
        Packed bytes (4 bytes per float)
    """
    return struct.pack(f"<{len(embedding)}f", *embedding)


def bytes_to_embedding(data: bytes) -> list[float]:
    """
    Convert bytes back to embedding list.

    Args:
        data: Packed bytes from embedding_to_bytes

    Returns:
        List of float values
    """
    count = len(data) // 4  # 4 bytes per float32
    return list(struct.unpack(f"<{count}f", data))


def make_embedding_getter(
    config: Optional[EmbeddingConfig] = None,
) -> callable:
    """
    Create an embedding getter function for commit_memory_ops.

    Returns a sync function that takes text and returns bytes.

    Args:
        config: Optional embedding config

    Returns:
        Function: (text: str) -> bytes
    """
    cfg = config or EmbeddingConfig.from_env()

    def get_embedding(text: str) -> bytes:
        embedding = embed_text_sync(text, cfg)
        return embedding_to_bytes(embedding)

    return get_embedding
