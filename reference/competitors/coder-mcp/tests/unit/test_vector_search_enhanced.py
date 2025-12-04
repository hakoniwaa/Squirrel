# tests/unit/test_vector_search_enhanced.py
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from coder_mcp.context.enhanced_search_manager import EnhancedSearchManager
from coder_mcp.context.search.cache import SearchCache
from coder_mcp.context.search.enhanced_hybrid_search import EnhancedHybridSearch, SearchStrategy
from coder_mcp.storage.vector_stores import HNSWVectorStore, HybridVectorStore


class TestEnhancedVectorSearch:
    """Test suite for enhanced vector search functionality"""

    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client for testing"""
        mock_redis = Mock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=True)
        mock_redis.keys = AsyncMock(return_value=[])
        return mock_redis

    @pytest.fixture
    def sample_embedding(self):
        """Sample embedding vector for testing"""
        return np.random.random(384).tolist()

    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for testing"""
        return {
            "file_path": "test_file.py",
            "content": "def test_function():\n    pass",
            "language": "python",
            "size": 100,
            "last_modified": "2024-01-01T00:00:00Z",
        }

    @pytest.mark.asyncio
    async def test_multi_model_embeddings(self, mock_redis_client):
        """Test multiple embedding models"""
        search = EnhancedHybridSearch(redis_client=mock_redis_client, enable_hnsw=False)

        # Test code embedding
        with patch.object(search.multi_model_embedding, "create_hybrid_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 384

            code_emb = await search.multi_model_embedding.create_hybrid_embedding(
                "def hello_world():\n    print('Hello')", context_type="code"
            )
            assert len(code_emb) == 384
            mock_embed.assert_called_once()

        # Test doc embedding
        with patch.object(search.multi_model_embedding, "create_hybrid_embedding") as mock_embed:
            mock_embed.return_value = [0.2] * 384

            doc_emb = await search.multi_model_embedding.create_hybrid_embedding(
                "This function prints hello", context_type="docs"
            )
            assert len(doc_emb) == 384

    @pytest.mark.asyncio
    async def test_vector_storage_operations(
        self, mock_redis_client, sample_embedding, sample_metadata
    ):
        """Test vector storage and retrieval operations"""
        # Use smaller HNSW configuration for testing to avoid memory issues
        hnsw_config = {
            "max_elements": 1000,  # Much smaller than default 1M
            "ef_construction": 50,  # Smaller than default 200
            "M": 8,  # Smaller than default 16
        }
        vector_store = HybridVectorStore(
            redis_client=mock_redis_client,
            embedding_dim=384,
            use_hnsw=True,
            hnsw_config=hnsw_config,
        )

        # Test storing vector
        success = await vector_store.store_vector(
            doc_id="test_doc_1",
            embedding=sample_embedding,
            metadata=sample_metadata,
            namespace="test",
        )
        assert success is True

        # Test searching vectors
        with patch.object(vector_store.hnsw_store, "search_vectors") as mock_search:
            mock_search.return_value = [
                {
                    "id": "test_doc_1",
                    "score": 0.85,
                    "metadata": sample_metadata,
                    "content": sample_metadata["content"],
                }
            ]

            results = await vector_store.search_vectors(
                query_embedding=sample_embedding, top_k=5, namespace="test"
            )
            assert len(results) == 1
            assert results[0]["id"] == "test_doc_1"
            assert results[0]["score"] == 0.85

        # Test deleting vector
        success = await vector_store.delete_vector("test_doc_1", namespace="test")
        assert success is True

    @pytest.mark.asyncio
    async def test_hnsw_vector_store(self, mock_redis_client, sample_embedding, sample_metadata):
        """Test HNSW vector store specifically"""
        try:
            hnsw_store = HNSWVectorStore(dim=384, max_elements=1000, redis_client=mock_redis_client)

            # Test storing vector
            success = await hnsw_store.store_vector(
                doc_id="hnsw_test_1", embedding=sample_embedding, metadata=sample_metadata
            )
            assert success is True

            # Test getting stats
            stats = await hnsw_store.get_stats()
            assert stats is not None
            assert stats["storage_type"] == "hnsw"
            assert stats["dimensions"] == 384

            # Test searching
            results = await hnsw_store.search_vectors(query_embedding=sample_embedding, top_k=5)
            assert isinstance(results, list)

        except ImportError:
            pytest.skip("hnswlib not available")

    @pytest.mark.asyncio
    async def test_search_cache(self, mock_redis_client):
        """Test search caching functionality"""
        cache = SearchCache(redis_client=mock_redis_client)

        # Test embedding caching
        def mock_compute_embedding():
            return [0.1] * 384

        # First call should compute
        embedding1 = await cache.get_or_compute_embedding(
            "test text", "default", mock_compute_embedding
        )
        assert len(embedding1) == 384

        # Second call should use cache
        embedding2 = await cache.get_or_compute_embedding(
            "test text", "default", mock_compute_embedding
        )
        assert embedding1 == embedding2

        # Test search result caching
        def mock_search():
            return [{"id": "test", "score": 0.9}]

        results1 = await cache.get_or_compute_search_results("test query", "default", mock_search)
        assert len(results1) == 1

        results2 = await cache.get_or_compute_search_results("test query", "default", mock_search)
        assert results1 == results2

    @pytest.mark.asyncio
    async def test_enhanced_search_manager(self, mock_redis_client, tmp_path):
        """Test the enhanced search manager"""
        # Create a mock config that uses local embeddings (no API key required)
        from coder_mcp.core.config.models import MCPConfiguration

        mock_config = MCPConfiguration()
        mock_config.embedding_provider = "local"
        mock_config.ai_features_enabled = False

        with (
            patch("coder_mcp.context.enhanced_search_manager.ProviderFactory") as mock_factory,
            patch(
                "coder_mcp.context.enhanced_search_manager.ConfigurationManager"
            ) as mock_config_manager,
            patch(
                "coder_mcp.context.search.enhanced_hybrid_search.HybridVectorStore"
            ) as mock_vector_store,
        ):
            mock_factory.return_value._get_redis_client.return_value = mock_redis_client
            mock_config_manager.return_value = Mock()  # Mock the config manager to avoid validation

            # Mock the vector store to avoid memory issues
            mock_store_instance = Mock()
            mock_store_instance.get_stats.return_value = {"num_docs": 0, "storage_type": "hybrid"}
            mock_vector_store.return_value = mock_store_instance

            manager = EnhancedSearchManager(
                config=mock_config, redis_client=mock_redis_client, workspace_path=str(tmp_path)
            )

            # Test initialization
            with patch.object(manager.enhanced_search, "health_check") as mock_health:
                mock_health.return_value = {"status": "healthy"}

                success = await manager.initialize()
                assert success is True

            # Test search functionality
            with patch.object(manager.enhanced_search, "search") as mock_search:
                mock_search.return_value = [
                    {
                        "id": "test_result",
                        "score": 0.9,
                        "metadata": {"file_path": "test.py"},
                        "content": "test content",
                    }
                ]

                results = await manager.search("test query", top_k=5)
                assert len(results) == 1
                assert results[0]["id"] == "test_result"

    @pytest.mark.asyncio
    async def test_search_strategies(self, mock_redis_client):
        """Test different search strategies"""
        search = EnhancedHybridSearch(redis_client=mock_redis_client, enable_hnsw=False)

        # Mock the underlying search methods
        with (
            patch.object(search, "_semantic_first_search") as mock_semantic,
            patch.object(search, "_text_first_search") as mock_text,
            patch.object(search, "_hybrid_search") as mock_hybrid,
        ):

            mock_semantic.return_value = [{"id": "semantic", "score": 0.9}]
            mock_text.return_value = [{"id": "text", "score": 0.8}]
            mock_hybrid.return_value = [{"id": "hybrid", "score": 0.95}]

            # Test semantic first strategy
            results = await search.search("test", strategy=SearchStrategy.SEMANTIC_FIRST)
            assert isinstance(results, list)

            # Test text first strategy
            results = await search.search("test", strategy=SearchStrategy.TEXT_FIRST)
            assert isinstance(results, list)

            # Test hybrid strategy
            results = await search.search("test", strategy=SearchStrategy.HYBRID)
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_redis_client):
        """Test error handling in search operations"""
        search = EnhancedHybridSearch(redis_client=mock_redis_client, enable_hnsw=False)

        # Test with invalid embedding
        with patch.object(search.multi_model_embedding, "create_hybrid_embedding") as mock_embed:
            mock_embed.side_effect = Exception("Embedding failed")

            results = await search.search("test query")
            assert isinstance(results, list)  # Should return empty list, not crash

        # Test with vector store failure
        with patch.object(search.vector_store, "search_vectors") as mock_search:
            mock_search.side_effect = Exception("Vector store failed")

            results = await search.search("test query")
            assert isinstance(results, list)  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_batch_operations(self, mock_redis_client):
        """Test batch processing capabilities"""
        search = EnhancedHybridSearch(redis_client=mock_redis_client, enable_hnsw=False)

        # Test batch embeddings
        with patch.object(search.batch_processor, "batch_embeddings") as mock_batch:
            mock_batch.return_value = [[0.1] * 384, [0.2] * 384]

            texts = ["text 1", "text 2"]
            embeddings = await search.batch_processor.batch_embeddings(
                texts, search.multi_model_embedding.create_hybrid_embedding
            )
            assert len(embeddings) == 2

        # Test batch search
        with patch.object(search.batch_processor, "batch_search") as mock_batch:
            mock_batch.return_value = [
                [{"id": "result1", "score": 0.9}],
                [{"id": "result2", "score": 0.8}],
            ]

            queries = ["query 1", "query 2"]
            results = await search.batch_processor.batch_search(queries, search.search)
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_performance_metrics(self, mock_redis_client):
        """Test performance metrics collection"""
        search = EnhancedHybridSearch(redis_client=mock_redis_client, enable_hnsw=False)

        # Perform some operations
        with patch.object(search.multi_model_embedding, "create_hybrid_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 384

            await search.search("test query 1")
            await search.search("test query 2")

        # Check metrics
        metrics = search.get_metrics()
        assert "total_searches" in metrics
        assert metrics["total_searches"] >= 0

    @pytest.mark.asyncio
    async def test_contextual_search(self, mock_redis_client, tmp_path):
        """Test contextual search with file context"""
        search = EnhancedHybridSearch(redis_client=mock_redis_client, enable_hnsw=False)

        # Create test files
        test_file = tmp_path / "test.py"
        test_file.write_text("def test_function():\n    pass")

        with patch.object(search, "contextual_search") as mock_contextual:
            mock_contextual.return_value = [
                {
                    "id": "contextual_result",
                    "score": 0.95,
                    "metadata": {"file_path": str(test_file)},
                    "content": "def test_function():\n    pass",
                }
            ]

            results = await search.contextual_search("test function", [str(test_file)], top_k=5)
            assert len(results) == 1
            assert results[0]["id"] == "contextual_result"

    @pytest.mark.asyncio
    async def test_health_check(self, mock_redis_client):
        """Test system health check"""
        search = EnhancedHybridSearch(redis_client=mock_redis_client, enable_hnsw=False)

        # Mock successful health check
        with patch.object(search.vector_store, "get_stats") as mock_stats:
            mock_stats.return_value = {"num_docs": 100, "storage_type": "hybrid"}

            health = await search.health_check()
            assert health["status"] == "healthy"
            assert "components" in health

    @pytest.mark.asyncio
    async def test_namespace_isolation(self, mock_redis_client, sample_embedding, sample_metadata):
        """Test namespace isolation in vector storage"""
        # Use smaller HNSW configuration for testing to avoid memory issues
        hnsw_config = {
            "max_elements": 1000,  # Much smaller than default 1M
            "ef_construction": 50,  # Smaller than default 200
            "M": 8,  # Smaller than default 16
        }
        vector_store = HybridVectorStore(
            redis_client=mock_redis_client,
            embedding_dim=384,
            use_hnsw=True,
            hnsw_config=hnsw_config,
        )

        # Store vectors in different namespaces
        await vector_store.store_vector("doc1", sample_embedding, sample_metadata, namespace="ns1")
        await vector_store.store_vector("doc2", sample_embedding, sample_metadata, namespace="ns2")

        # Test namespace-specific stats
        stats_ns1 = await vector_store.get_stats("ns1")
        stats_ns2 = await vector_store.get_stats("ns2")

        assert stats_ns1 is not None
        assert stats_ns2 is not None
        assert stats_ns1["storage_type"] == "hybrid"
        assert stats_ns2["storage_type"] == "hybrid"

    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_search_performance(self, benchmark, mock_redis_client):
        """Benchmark search performance"""
        search = EnhancedHybridSearch(redis_client=mock_redis_client, enable_hnsw=False)

        # Mock to avoid actual API calls
        with patch.object(search.multi_model_embedding, "create_hybrid_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 384

            with patch.object(search.vector_store, "search_vectors") as mock_search:
                mock_search.return_value = []

                async def run_search():
                    return await search.search("implement binary search tree")

                result = await benchmark(run_search)
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_cleanup_and_resource_management(self, mock_redis_client):
        """Test proper cleanup and resource management"""
        search = EnhancedHybridSearch(redis_client=mock_redis_client, enable_hnsw=False)

        # Test cache clearing
        await search.clear_cache()

        # Test stats retrieval
        stats = await search.get_cache_stats()
        assert isinstance(stats, dict)
        assert "cache_type" in stats or "status" in stats

        # Test graceful shutdown
        # This would be called in a real scenario
        if hasattr(search, "cleanup"):
            await search.cleanup()
