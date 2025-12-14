"""Tests for embeddings module (IPC-002)."""

from unittest.mock import MagicMock, patch

import pytest

from sqrl.embeddings import (
    ERROR_EMBEDDING_FAILED,
    ERROR_EMPTY_TEXT,
    EmbeddingConfig,
    EmbeddingError,
    bytes_to_embedding,
    embed_text,
    embed_text_sync,
    embedding_to_bytes,
    make_embedding_getter,
)


class TestEmbeddingConfig:
    """Test configuration handling."""

    def test_default_config(self):
        """Default config uses text-embedding-3-small."""
        config = EmbeddingConfig()
        assert config.model == "text-embedding-3-small"
        assert config.dimensions == 1536

    def test_config_from_env(self, monkeypatch):
        """Config can be loaded from environment."""
        monkeypatch.setenv("SQRL_EMBEDDING_MODEL", "custom-model")
        monkeypatch.setenv("SQRL_EMBEDDING_DIMS", "768")

        config = EmbeddingConfig.from_env()
        assert config.model == "custom-model"
        assert config.dimensions == 768


class TestEmbeddingConversion:
    """Test byte conversion for SQLite storage."""

    def test_embedding_to_bytes(self):
        """Convert embedding list to bytes."""
        embedding = [1.0, -0.5, 0.25, 0.0]
        result = embedding_to_bytes(embedding)

        # 4 floats * 4 bytes = 16 bytes
        assert len(result) == 16
        assert isinstance(result, bytes)

    def test_bytes_to_embedding(self):
        """Convert bytes back to embedding list."""
        original = [1.0, -0.5, 0.25, 0.0]
        packed = embedding_to_bytes(original)
        restored = bytes_to_embedding(packed)

        assert len(restored) == len(original)
        for a, b in zip(original, restored):
            assert abs(a - b) < 1e-6

    def test_roundtrip_large_embedding(self):
        """Roundtrip works for 1536-dim embeddings."""
        import random

        original = [random.uniform(-1, 1) for _ in range(1536)]
        packed = embedding_to_bytes(original)
        restored = bytes_to_embedding(packed)

        assert len(restored) == 1536
        for a, b in zip(original, restored):
            assert abs(a - b) < 1e-6


class TestEmptyTextError:
    """Test error handling for empty text (IPC-002 -32040)."""

    @pytest.mark.asyncio
    async def test_async_empty_text_raises(self):
        """Async embed_text raises on empty string."""
        with pytest.raises(EmbeddingError) as exc_info:
            await embed_text("")

        assert exc_info.value.code == ERROR_EMPTY_TEXT
        assert "Empty text" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_async_whitespace_only_raises(self):
        """Async embed_text raises on whitespace-only string."""
        with pytest.raises(EmbeddingError) as exc_info:
            await embed_text("   \n\t  ")

        assert exc_info.value.code == ERROR_EMPTY_TEXT

    def test_sync_empty_text_raises(self):
        """Sync embed_text_sync raises on empty string."""
        with pytest.raises(EmbeddingError) as exc_info:
            embed_text_sync("")

        assert exc_info.value.code == ERROR_EMPTY_TEXT


class TestEmbeddingWithMock:
    """Test embedding generation with mocked LiteLLM."""

    @pytest.mark.asyncio
    async def test_async_embed_success(self):
        """Async embed_text returns embedding on success."""
        mock_embedding = [0.1] * 1536
        mock_response = MagicMock()
        mock_response.data = [{"embedding": mock_embedding}]

        with patch("sqrl.embeddings.litellm.aembedding") as mock_aembedding:
            mock_aembedding.return_value = mock_response

            result = await embed_text("test text")

            assert result == mock_embedding
            mock_aembedding.assert_called_once()

    def test_sync_embed_success(self):
        """Sync embed_text_sync returns embedding on success."""
        mock_embedding = [0.2] * 1536
        mock_response = MagicMock()
        mock_response.data = [{"embedding": mock_embedding}]

        with patch("sqrl.embeddings.litellm.embedding") as mock_embedding_fn:
            mock_embedding_fn.return_value = mock_response

            result = embed_text_sync("test text")

            assert result == mock_embedding
            mock_embedding_fn.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_api_error(self):
        """Async embed_text raises EmbeddingError on API failure."""
        with patch("sqrl.embeddings.litellm.aembedding") as mock_aembedding:
            mock_aembedding.side_effect = Exception("API rate limited")

            with pytest.raises(EmbeddingError) as exc_info:
                await embed_text("test text")

            assert exc_info.value.code == ERROR_EMBEDDING_FAILED
            assert "API rate limited" in exc_info.value.message

    def test_sync_api_error(self):
        """Sync embed_text_sync raises EmbeddingError on API failure."""
        with patch("sqrl.embeddings.litellm.embedding") as mock_embedding_fn:
            mock_embedding_fn.side_effect = Exception("Network error")

            with pytest.raises(EmbeddingError) as exc_info:
                embed_text_sync("test text")

            assert exc_info.value.code == ERROR_EMBEDDING_FAILED
            assert "Network error" in exc_info.value.message


class TestEmbeddingGetter:
    """Test the embedding getter for commit_memory_ops."""

    def test_make_embedding_getter_returns_bytes(self):
        """Getter function returns bytes for DB storage."""
        mock_embedding = [0.5] * 10
        mock_response = MagicMock()
        mock_response.data = [{"embedding": mock_embedding}]

        with patch("sqrl.embeddings.litellm.embedding") as mock_embedding_fn:
            mock_embedding_fn.return_value = mock_response

            getter = make_embedding_getter()
            result = getter("test text")

            assert isinstance(result, bytes)
            # 10 floats * 4 bytes = 40 bytes
            assert len(result) == 40

            # Verify it can be converted back
            restored = bytes_to_embedding(result)
            assert restored == mock_embedding

    def test_getter_uses_custom_config(self):
        """Getter respects custom config."""
        mock_embedding = [0.3] * 768
        mock_response = MagicMock()
        mock_response.data = [{"embedding": mock_embedding}]

        custom_config = EmbeddingConfig(model="custom-model", dimensions=768)

        with patch("sqrl.embeddings.litellm.embedding") as mock_embedding_fn:
            mock_embedding_fn.return_value = mock_response

            getter = make_embedding_getter(custom_config)
            _ = getter("test")

            mock_embedding_fn.assert_called_once()
            call_args = mock_embedding_fn.call_args
            assert call_args.kwargs["model"] == "custom-model"
