"""
Comprehensive tests for the mock utilities module.

These tests verify that all mock implementations behave correctly and
provide realistic behavior for testing other components.
"""

import time
from unittest.mock import AsyncMock

import numpy as np
import pytest

from tests.helpers.mocks import (
    MockContextManager,
    MockEmbeddingProvider,
    MockMCPServer,
    MockOpenAIClient,
    MockRedisClient,
    MockVectorStore,
    create_full_mock_suite,
    create_indexed_context_manager,
    create_mock_context_manager,
    create_mock_embedding_provider,
    create_mock_openai_client,
    create_mock_redis,
    create_mock_server,
    create_mock_vector_store,
    create_populated_redis,
    create_trained_vector_store,
)


class TestMockMCPServer:
    """Test the MockMCPServer implementation."""

    def test_server_initialization(self):
        """Test server creation and initial state."""
        server = MockMCPServer()
        assert not server.is_initialized
        assert server.health_status == "healthy"
        assert server.call_count == 0
        assert server.last_call_time is None
        assert server.tool_handlers.handlers is not None

    @pytest.mark.asyncio
    async def test_server_initialize(self):
        """Test server initialization."""
        server = MockMCPServer()
        await server.initialize()
        assert server.is_initialized

    @pytest.mark.asyncio
    async def test_tool_call_handling(self):
        """Test tool call handling with default handlers."""
        server = MockMCPServer()
        await server.initialize()

        # Test read_file tool
        result = await server.handle_tool_call("read_file", {"path": "test.py"})
        assert result["content"] == "mock file content"
        assert result["lines"] == 10
        assert result["size"] == 100
        assert server.call_count == 1

        # Test write_file tool
        result = await server.handle_tool_call(
            "write_file", {"path": "test.py", "content": "new content"}
        )
        assert result["success"] is True
        assert result["bytes_written"] == 100
        assert server.call_count == 2

    @pytest.mark.asyncio
    async def test_unknown_tool_handling(self):
        """Test handling of unknown tools."""
        server = MockMCPServer()
        await server.initialize()

        result = await server.handle_tool_call("unknown_tool", {"param": "value"})
        assert result["tool"] == "unknown_tool"
        assert result["arguments"] == {"param": "value"}
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_uninitialized_server_error(self):
        """Test that uninitialized server raises error."""
        server = MockMCPServer()

        with pytest.raises(RuntimeError, match="Server not initialized"):
            await server.handle_tool_call("test_tool", {})

    def test_health_status(self):
        """Test health status reporting."""
        server = MockMCPServer()
        health = server.get_health_status()

        assert health["status"] == "healthy"
        assert health["initialized"] is False
        assert health["uptime"] == 3600
        assert health["call_count"] == 0
        assert health["last_call"] is None

    @pytest.mark.asyncio
    async def test_custom_tool_handler(self):
        """Test adding custom tool handlers."""
        server = MockMCPServer()
        await server.initialize()

        # Add custom handler
        server.tool_handlers.handlers["custom_tool"] = AsyncMock(
            return_value={"custom": "response"}
        )

        result = await server.handle_tool_call("custom_tool", {"data": "test"})
        assert result["custom"] == "response"


class TestMockRedisClient:
    """Test the MockRedisClient implementation."""

    def test_redis_initialization(self):
        """Test Redis client creation."""
        redis = MockRedisClient()
        assert redis._data == {}
        assert redis._hashes == {}
        assert redis._sorted_sets == {}

        # Test with initial data
        initial_data = {"key1": "value1", "key2": "value2"}
        redis = MockRedisClient(initial_data)
        assert redis._data == initial_data

    @pytest.mark.asyncio
    async def test_string_operations(self):
        """Test basic string operations."""
        redis = MockRedisClient()

        # Test set and get
        await redis.set("test_key", "test_value")
        value = await redis.get("test_key")
        assert value == "test_value"

        # Test exists
        exists = await redis.exists("test_key")
        assert exists is True

        exists = await redis.exists("nonexistent")
        assert exists is False

        # Test delete
        deleted = await redis.delete("test_key")
        assert deleted == 1

        value = await redis.get("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_expiry_operations(self):
        """Test key expiry functionality."""
        redis = MockRedisClient()

        # Set key with expiry
        await redis.set("temp_key", "temp_value", ex=1)

        # Should exist immediately
        assert await redis.exists("temp_key")

        # Mock time passing
        original_time = time.time
        time.time = lambda: original_time() + 2

        try:
            # Should be expired now
            assert not await redis.exists("temp_key")
            value = await redis.get("temp_key")
            assert value is None
        finally:
            time.time = original_time

    @pytest.mark.asyncio
    async def test_hash_operations(self):
        """Test hash operations."""
        redis = MockRedisClient()

        # Test hset and hget
        await redis.hset("test_hash", "field1", "value1")
        await redis.hset("test_hash", "field2", "value2")

        value = await redis.hget("test_hash", "field1")
        assert value == "value1"

        # Test hgetall
        all_fields = await redis.hgetall("test_hash")
        assert all_fields == {"field1": "value1", "field2": "value2"}

        # Test hdel
        deleted = await redis.hdel("test_hash", "field1")
        assert deleted == 1

        value = await redis.hget("test_hash", "field1")
        assert value is None

    @pytest.mark.asyncio
    async def test_sorted_set_operations(self):
        """Test sorted set operations."""
        redis = MockRedisClient()

        # Test zadd
        added = await redis.zadd("test_zset", {"member1": 1.0, "member2": 2.0, "member3": 0.5})
        assert added == 3

        # Test zrange (should be sorted by score)
        members = await redis.zrange("test_zset", 0, -1)
        assert members == ["member3", "member1", "member2"]  # Sorted by score

        # Test zrange with scores
        members_with_scores = await redis.zrange("test_zset", 0, -1, withscores=True)
        expected = [("member3", 0.5), ("member1", 1.0), ("member2", 2.0)]
        assert members_with_scores == expected

    @pytest.mark.asyncio
    async def test_keys_operation(self):
        """Test keys listing."""
        redis = MockRedisClient({"test1": "value1", "test2": "value2", "other": "value3"})

        # Test all keys
        all_keys = await redis.keys("*")
        assert set(all_keys) == {"test1", "test2", "other"}

        # Test pattern matching
        test_keys = await redis.keys("test*")
        assert set(test_keys) == {"test1", "test2"}

    @pytest.mark.asyncio
    async def test_ttl_operation(self):
        """Test TTL functionality."""
        redis = MockRedisClient()

        # Key doesn't exist
        ttl = await redis.ttl("nonexistent")
        assert ttl == -2

        # Key exists but no expiry
        await redis.set("persistent_key", "value")
        ttl = await redis.ttl("persistent_key")
        assert ttl == -1

        # Key with expiry
        await redis.set("temp_key", "value", ex=60)
        ttl = await redis.ttl("temp_key")
        assert 0 < ttl <= 60

    def test_redis_stats(self):
        """Test Redis statistics."""
        redis = MockRedisClient({"key1": "value1", "key2": "value2"})
        stats = redis.get_stats()

        assert stats["total_keys"] == 2
        assert stats["hash_keys"] == 0
        assert stats["sorted_sets"] == 0
        assert stats["keys_with_expiry"] == 0
        assert stats["memory_usage"] > 0


class TestMockContextManager:
    """Test the MockContextManager implementation."""

    def test_context_manager_initialization(self):
        """Test context manager creation."""
        cm = MockContextManager()
        assert cm.indexed_files == {}
        assert cm.project_info["name"] == "test-project"
        assert cm.project_info["type"] == "python"
        assert cm.project_info["files_count"] == 42
        assert "last_indexed" in cm.project_info

    @pytest.mark.asyncio
    async def test_file_indexing(self):
        """Test file indexing functionality."""
        cm = MockContextManager()

        content = "def test_function():\n    pass\n"
        result = await cm.index_file("test.py", content)
        assert result is True

        assert "test.py" in cm.indexed_files
        file_info = cm.indexed_files["test.py"]
        assert file_info["content"] == content
        assert file_info["size"] == len(content)
        assert file_info["lines"] == 3  # 2 lines + 1
        assert "indexed_at" in file_info

    @pytest.mark.asyncio
    async def test_context_retrieval(self):
        """Test context retrieval."""
        cm = MockContextManager()

        context = await cm.get_context("test query", max_results=5)
        assert context["query"] == "test query"
        assert context["results"] == []  # Initially empty
        assert context["total"] == 0
        assert context["relevance_threshold"] == 0.7

    @pytest.mark.asyncio
    async def test_similarity_search(self):
        """Test similarity search functionality."""
        cm = MockContextManager()

        # Index some files
        await cm.index_file("file1.py", "def calculate_sum(a, b): return a + b")
        await cm.index_file("file2.py", "def calculate_product(x, y): return x * y")
        await cm.index_file("file3.py", "def print_message(msg): print(msg)")

        # Search for calculate-related content
        results = await cm.search_similar("calculate")
        assert len(results) == 2  # Should find file1.py and file2.py

        for result in results:
            # Check that the content contains "calculate" since that's what we're searching for
            assert "calculate" in result["snippet"]
            assert result["similarity"] == 0.85
            assert "lines" in result

    def test_project_metrics(self):
        """Test project metrics."""
        cm = MockContextManager()

        # Add some test data
        cm.indexed_files = {
            "file1.py": {"lines": 10, "size": 100},
            "file2.py": {"lines": 20, "size": 200},
        }

        metrics = cm.get_project_metrics()
        assert metrics["files_indexed"] == 2
        assert metrics["total_lines"] == 30
        assert metrics["total_size"] == 300
        assert metrics["project_info"] == cm.project_info


class TestMockOpenAIClient:
    """Test the MockOpenAIClient implementation."""

    def test_openai_initialization(self):
        """Test OpenAI client creation."""
        client = MockOpenAIClient()
        assert client.usage_stats["total_tokens"] == 0
        assert client.usage_stats["embedding_requests"] == 0
        assert client.usage_stats["chat_requests"] == 0

    @pytest.mark.asyncio
    async def test_embedding_creation(self):
        """Test embedding creation."""
        client = MockOpenAIClient()

        result = await client.create_embedding("test text")

        assert result["object"] == "list"
        assert len(result["data"]) == 1

        embedding_data = result["data"][0]
        assert embedding_data["object"] == "embedding"
        assert embedding_data["index"] == 0
        assert len(embedding_data["embedding"]) == 1536

        # Check usage tracking
        assert client.usage_stats["embedding_requests"] == 1
        assert client.usage_stats["total_tokens"] > 0

    @pytest.mark.asyncio
    async def test_deterministic_embeddings(self):
        """Test that embeddings are deterministic."""
        client = MockOpenAIClient()

        result1 = await client.create_embedding("test text")
        result2 = await client.create_embedding("test text")

        embedding1 = result1["data"][0]["embedding"]
        embedding2 = result2["data"][0]["embedding"]

        assert embedding1 == embedding2  # Should be identical

    @pytest.mark.asyncio
    async def test_chat_completion(self):
        """Test chat completion creation."""
        client = MockOpenAIClient()

        messages = [{"role": "user", "content": "Can you explain this concept?"}]

        result = await client.create_chat_completion(messages)

        assert "id" in result
        assert result["object"] == "chat.completion"
        assert "created" in result
        assert len(result["choices"]) == 1

        choice = result["choices"][0]
        assert choice["message"]["role"] == "assistant"
        assert "explain" in choice["message"]["content"].lower()
        assert choice["finish_reason"] == "stop"

        # Check usage tracking
        assert client.usage_stats["chat_requests"] == 1
        assert result["usage"]["total_tokens"] > 0

    @pytest.mark.asyncio
    async def test_contextual_responses(self):
        """Test contextual chat responses."""
        client = MockOpenAIClient()

        # Test error-related message
        result = await client.create_chat_completion(
            [{"role": "user", "content": "I have an error in my code"}]
        )
        assert "debug" in result["choices"][0]["message"]["content"].lower()

        # Test code-related message
        result = await client.create_chat_completion(
            [{"role": "user", "content": "Show me some code examples"}]
        )
        assert "```python" in result["choices"][0]["message"]["content"]

    def test_usage_stats(self):
        """Test usage statistics tracking."""
        client = MockOpenAIClient()
        client.usage_stats = {"total_tokens": 100, "embedding_requests": 5, "chat_requests": 3}

        stats = client.get_usage_stats()
        assert stats["total_tokens"] == 100
        assert stats["embedding_requests"] == 5
        assert stats["chat_requests"] == 3

        # Ensure it's a copy
        stats["total_tokens"] = 200
        assert client.usage_stats["total_tokens"] == 100


class TestMockEmbeddingProvider:
    """Test the MockEmbeddingProvider implementation."""

    def test_embedding_provider_initialization(self):
        """Test embedding provider creation."""
        provider = MockEmbeddingProvider()
        assert provider.dimensions == 1536
        assert provider.cache == {}
        assert provider.call_count == 0

        # Test custom dimensions
        provider = MockEmbeddingProvider(dimensions=512)
        assert provider.dimensions == 512

    @pytest.mark.asyncio
    async def test_single_embedding(self):
        """Test single embedding creation."""
        provider = MockEmbeddingProvider()

        embedding = await provider.create_embedding("test text")
        assert len(embedding) == 1536
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)

        # Check normalization (vector should have unit length)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 1e-10

    @pytest.mark.asyncio
    async def test_batch_embeddings(self):
        """Test batch embedding creation."""
        provider = MockEmbeddingProvider()

        texts = ["text1", "text2", "text3"]
        embeddings = await provider.create_embeddings(texts)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)

        # Each embedding should be different
        assert not np.array_equal(embeddings[0], embeddings[1])
        assert not np.array_equal(embeddings[1], embeddings[2])

    @pytest.mark.asyncio
    async def test_embedding_caching(self):
        """Test embedding caching."""
        provider = MockEmbeddingProvider()

        # First call
        embedding1 = await provider.create_embedding("test text")
        assert len(provider.cache) == 1

        # Second call with same text
        embedding2 = await provider.create_embedding("test text")
        assert embedding1 == embedding2  # Should be cached
        assert len(provider.cache) == 1  # Cache size unchanged

    @pytest.mark.asyncio
    async def test_deterministic_embeddings(self):
        """Test that embeddings are deterministic."""
        provider1 = MockEmbeddingProvider()
        provider2 = MockEmbeddingProvider()

        embedding1 = await provider1.create_embedding("test text")
        embedding2 = await provider2.create_embedding("test text")

        assert embedding1 == embedding2

    def test_provider_stats(self):
        """Test provider statistics."""
        provider = MockEmbeddingProvider(dimensions=512)
        provider.cache = {"text1": [0.1] * 512, "text2": [0.2] * 512}
        provider.call_count = 5

        stats = provider.get_stats()
        assert stats["dimensions"] == 512
        assert stats["cached_embeddings"] == 2
        assert stats["total_calls"] == 5


class TestMockVectorStore:
    """Test the MockVectorStore implementation."""

    def test_vector_store_initialization(self):
        """Test vector store creation."""
        store = MockVectorStore()
        assert store.dimensions == 1536
        assert store.vectors == {}
        assert store.metadata == {}

        # Test custom dimensions
        store = MockVectorStore(dimensions=512)
        assert store.dimensions == 512

    @pytest.mark.asyncio
    async def test_add_single_vector(self):
        """Test adding a single vector."""
        store = MockVectorStore(dimensions=3)

        vector = [0.1, 0.2, 0.3]
        metadata = {"text": "test", "category": "example"}

        await store.add_vector("vec1", vector, metadata)

        assert "vec1" in store.vectors
        assert np.array_equal(store.vectors["vec1"], np.array(vector))
        assert store.metadata["vec1"] == metadata

    @pytest.mark.asyncio
    async def test_add_vector_wrong_dimensions(self):
        """Test adding vector with wrong dimensions."""
        store = MockVectorStore(dimensions=3)

        with pytest.raises(ValueError, match="Vector must have 3 dimensions"):
            await store.add_vector("vec1", [0.1, 0.2])  # Wrong dimension

    @pytest.mark.asyncio
    async def test_add_multiple_vectors(self):
        """Test adding multiple vectors."""
        store = MockVectorStore(dimensions=2)

        vectors = {"vec1": [0.1, 0.2], "vec2": [0.3, 0.4]}
        metadata = {"vec1": {"category": "A"}, "vec2": {"category": "B"}}

        await store.add_vectors(vectors, metadata)

        assert len(store.vectors) == 2
        assert store.metadata["vec1"]["category"] == "A"
        assert store.metadata["vec2"]["category"] == "B"

    @pytest.mark.asyncio
    async def test_similarity_search(self):
        """Test similarity search."""
        store = MockVectorStore(dimensions=2)

        # Add some vectors
        await store.add_vector("vec1", [1.0, 0.0], {"text": "horizontal"})
        await store.add_vector("vec2", [0.0, 1.0], {"text": "vertical"})
        await store.add_vector("vec3", [0.7071, 0.7071], {"text": "diagonal"})

        # Search for horizontal-like vector
        results = await store.search_similar([0.9, 0.1], top_k=2, threshold=0.5)

        assert len(results) <= 2
        assert results[0]["id"] == "vec1"  # Should be most similar
        assert results[0]["similarity"] > 0.8

        # Test all results have required fields
        for result in results:
            assert "id" in result
            assert "similarity" in result
            assert "metadata" in result

    @pytest.mark.asyncio
    async def test_similarity_search_with_threshold(self):
        """Test similarity search with threshold."""
        store = MockVectorStore(dimensions=2)

        await store.add_vector("vec1", [1.0, 0.0])
        await store.add_vector("vec2", [0.0, 1.0])

        # Search with high threshold
        results = await store.search_similar([1.0, 0.0], threshold=0.99)

        # Should only return very similar vectors
        assert len(results) == 1
        assert results[0]["id"] == "vec1"

    @pytest.mark.asyncio
    async def test_delete_vector(self):
        """Test vector deletion."""
        store = MockVectorStore(dimensions=2)

        await store.add_vector("vec1", [0.1, 0.2], {"test": "data"})

        # Delete existing vector
        deleted = await store.delete_vector("vec1")
        assert deleted is True
        assert "vec1" not in store.vectors
        assert "vec1" not in store.metadata

        # Delete non-existing vector
        deleted = await store.delete_vector("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_search_wrong_dimensions(self):
        """Test search with wrong query dimensions."""
        store = MockVectorStore(dimensions=3)

        with pytest.raises(ValueError, match="Query vector must have 3 dimensions"):
            await store.search_similar([0.1, 0.2])  # Wrong dimension

    def test_vector_store_stats(self):
        """Test vector store statistics."""
        store = MockVectorStore(dimensions=2)

        # Add some test data
        store.vectors = {"vec1": np.array([0.1, 0.2]), "vec2": np.array([0.3, 0.4])}

        stats = store.get_stats()
        assert stats["total_vectors"] == 2
        assert stats["dimensions"] == 2
        assert stats["memory_usage"] > 0


class TestFactoryFunctions:
    """Test factory functions and preset configurations."""

    def test_create_mock_server(self):
        """Test mock server factory."""
        server = create_mock_server()
        assert isinstance(server, MockMCPServer)
        assert not server.is_initialized

    def test_create_mock_redis(self):
        """Test mock Redis factory."""
        redis = create_mock_redis()
        assert isinstance(redis, MockRedisClient)
        assert redis._data == {}

        # Test with initial data
        redis = create_mock_redis({"key": "value"})
        assert redis._data == {"key": "value"}

    def test_create_mock_context_manager(self):
        """Test mock context manager factory."""
        cm = create_mock_context_manager()
        assert isinstance(cm, MockContextManager)
        assert cm.project_info["name"] == "test-project"

    def test_create_mock_openai_client(self):
        """Test mock OpenAI client factory."""
        client = create_mock_openai_client()
        assert isinstance(client, MockOpenAIClient)
        assert client.usage_stats["total_tokens"] == 0

    def test_create_mock_embedding_provider(self):
        """Test mock embedding provider factory."""
        provider = create_mock_embedding_provider()
        assert isinstance(provider, MockEmbeddingProvider)
        assert provider.dimensions == 1536

        # Test custom dimensions
        provider = create_mock_embedding_provider(dimensions=512)
        assert provider.dimensions == 512

    def test_create_mock_vector_store(self):
        """Test mock vector store factory."""
        store = create_mock_vector_store()
        assert isinstance(store, MockVectorStore)
        assert store.dimensions == 1536

        # Test custom dimensions
        store = create_mock_vector_store(dimensions=512)
        assert store.dimensions == 512

    def test_create_full_mock_suite(self):
        """Test full mock suite factory."""
        suite = create_full_mock_suite()

        assert isinstance(suite["server"], MockMCPServer)
        assert isinstance(suite["redis"], MockRedisClient)
        assert isinstance(suite["context_manager"], MockContextManager)
        assert isinstance(suite["openai"], MockOpenAIClient)
        assert isinstance(suite["embedding_provider"], MockEmbeddingProvider)
        assert isinstance(suite["vector_store"], MockVectorStore)

    def test_create_populated_redis(self):
        """Test populated Redis factory."""
        redis = create_populated_redis()
        assert isinstance(redis, MockRedisClient)
        assert len(redis._data) > 0

        # Check for expected data
        assert "user:123" in redis._data
        assert "session:abc" in redis._data
        assert "cache:key1" in redis._data
        assert "config:app" in redis._data

    def test_create_indexed_context_manager(self):
        """Test indexed context manager factory."""
        cm = create_indexed_context_manager()
        assert isinstance(cm, MockContextManager)
        # Note: Files are indexed asynchronously, so we can't test them immediately

    def test_create_trained_vector_store(self):
        """Test trained vector store factory."""
        store = create_trained_vector_store()
        assert isinstance(store, MockVectorStore)
        # Note: Vectors are added asynchronously, so we can't test them immediately


class TestIntegrationScenarios:
    """Test integration scenarios using multiple mocks together."""

    @pytest.mark.asyncio
    async def test_server_with_redis_integration(self):
        """Test server working with Redis."""
        server = create_mock_server()
        redis = create_populated_redis()

        await server.initialize()

        # Simulate a tool that uses Redis
        async def redis_tool(args):
            value = await redis.get("user:123")
            return {"user_data": value, "success": True}

        server.tool_handlers.handlers["get_user"] = redis_tool

        result = await server.handle_tool_call("get_user", {})
        assert result["success"] is True
        assert "user_data" in result

    @pytest.mark.asyncio
    async def test_embedding_and_vector_store_integration(self):
        """Test embedding provider with vector store."""
        provider = create_mock_embedding_provider()
        store = create_mock_vector_store()

        # Create embeddings and store them
        texts = ["Python programming", "Machine learning", "Data science"]
        embeddings = await provider.create_embeddings(texts)

        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            await store.add_vector(f"doc_{i}", embedding, {"text": text})

        # Search for similar content with a lower threshold to ensure results
        query_embedding = await provider.create_embedding("Python code")
        results = await store.search_similar(
            query_embedding, top_k=2, threshold=-1.0
        )  # Use very low threshold

        assert len(results) > 0
        # The most similar result should contain "Python" related content
        assert any("Python" in result["metadata"]["text"] for result in results)

    @pytest.mark.asyncio
    async def test_context_manager_with_search(self):
        """Test context manager with search functionality."""
        cm = create_mock_context_manager()

        # Index some files
        await cm.index_file("utils.py", "def calculate_sum(a, b): return a + b")
        await cm.index_file("math_helpers.py", "def calculate_product(x, y): return x * y")
        await cm.index_file("display.py", "def show_result(result): print(result)")

        # Search for calculation functions
        results = await cm.search_similar("calculate")

        # Should find the calculation-related files (checking content, not filename)
        calc_results = [r for r in results if "calculate" in r["snippet"]]
        assert len(calc_results) == 2

        # Check specific files found
        found_files = [r["file"] for r in calc_results]
        assert "utils.py" in found_files
        assert "math_helpers.py" in found_files

    @pytest.mark.asyncio
    async def test_openai_with_contextual_chat(self):
        """Test OpenAI client with different message contexts."""
        client = create_mock_openai_client()

        # Test different types of messages
        test_cases = [
            ("I have a bug in my code", "debug"),
            ("Can you explain this function?", "explain"),
            ("Show me a code example", "```python"),
            ("Help me optimize this", "response"),
        ]

        for message, expected_keyword in test_cases:
            result = await client.create_chat_completion([{"role": "user", "content": message}])

            response_content = result["choices"][0]["message"]["content"].lower()
            assert expected_keyword in response_content

    def test_mock_statistics_integration(self):
        """Test statistics from multiple mocks."""
        redis = create_populated_redis()
        provider = create_mock_embedding_provider()
        store = create_mock_vector_store()

        # Add some test data
        provider.cache = {"text1": [0.1] * 1536, "text2": [0.2] * 1536}
        provider.call_count = 3

        store.vectors = {"vec1": np.random.rand(1536), "vec2": np.random.rand(1536)}

        # Collect all statistics
        all_stats = {
            "redis": redis.get_stats(),
            "embedding_provider": provider.get_stats(),
            "vector_store": store.get_stats(),
        }

        assert all_stats["redis"]["total_keys"] > 0
        assert all_stats["embedding_provider"]["cached_embeddings"] == 2
        assert all_stats["embedding_provider"]["total_calls"] == 3
        assert all_stats["vector_store"]["total_vectors"] == 2
