"""
Unit tests for coder_mcp.storage.search.metrics module.
Tests search metrics tracking and analytics.
"""

from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest

from coder_mcp.storage.search.metrics import SearchMetrics


class TestSearchMetrics:
    """Test the SearchMetrics class."""

    def test_initialization_without_redis(self):
        """Test SearchMetrics initialization without Redis client."""
        metrics = SearchMetrics()

        assert metrics.queries == []
        assert metrics.click_through_rate == {}
        assert metrics.query_times == []
        assert metrics.redis is None

    def test_initialization_with_redis(self):
        """Test SearchMetrics initialization with Redis client."""
        redis_client = Mock()
        metrics = SearchMetrics(redis_client)

        assert metrics.redis is redis_client

    @pytest.mark.asyncio
    async def test_log_search_without_redis(self):
        """Test logging search without Redis (should not crash)."""
        metrics = SearchMetrics()

        # Should complete without error
        await metrics.log_search(
            query="test query", results=[{"id": 1, "score": 0.8}], execution_time=0.123
        )

        # No state should change without Redis
        assert metrics.queries == []
        assert metrics.query_times == []

    @pytest.mark.asyncio
    async def test_log_search_with_redis(self):
        """Test logging search with Redis client."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        query = "test query"
        results = [{"id": 1, "score": 0.9}, {"id": 2, "score": 0.7}, {"id": 3, "score": 0.5}]
        execution_time = 0.456

        with patch("time.time", return_value=1234567890):
            await metrics.log_search(query, results, execution_time)

        # Verify Redis calls
        redis_client.zadd.assert_called_once_with("search:queries", {query: 1234567890})
        redis_client.hincrby.assert_called_once_with("search:stats", "total_queries", 1)
        redis_client.lpush.assert_any_call("search:times", execution_time)

        # Should also track quality
        avg_score = (0.9 + 0.7 + 0.5) / 3
        redis_client.lpush.assert_any_call("search:quality", avg_score)

    @pytest.mark.asyncio
    async def test_log_search_empty_results(self):
        """Test logging search with empty results."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        await metrics.log_search("test", [], 0.1)

        # Should still log query and time, but not quality
        redis_client.zadd.assert_called_once()
        redis_client.hincrby.assert_called_once()
        redis_client.lpush.assert_called_once_with("search:times", 0.1)

    @pytest.mark.asyncio
    async def test_log_search_results_without_scores(self):
        """Test logging search with results that have no scores."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        results = [{"id": 1}, {"id": 2, "score": 0.5}, {"id": 3}]  # No score  # No score

        await metrics.log_search("test", results, 0.1)

        # Average should handle missing scores as 0
        avg_score = (0.0 + 0.5 + 0.0) / 3
        redis_client.lpush.assert_any_call("search:quality", avg_score)

    @pytest.mark.asyncio
    async def test_get_analytics_without_redis(self):
        """Test getting analytics without Redis."""
        metrics = SearchMetrics()

        analytics = await metrics.get_analytics()

        assert analytics == {
            "total_queries": 0,
            "avg_latency": 0.0,
            "avg_quality": 0.0,
            "popular_queries": [],
            "cache_hit_rate": 0.0,
        }

    @pytest.mark.asyncio
    async def test_get_analytics_with_redis(self):
        """Test getting analytics with Redis client."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        # Mock Redis responses
        redis_client.hget.side_effect = [100, 50, 25]  # total_queries  # cache hits  # cache misses
        redis_client.lrange.side_effect = [
            [0.1, 0.2, 0.3],  # search times
            [0.8, 0.9, 0.7],  # search quality
        ]
        redis_client.zrevrange.return_value = ["query1", "query2", "query3"]

        analytics = await metrics.get_analytics()

        assert analytics["total_queries"] == 100
        assert analytics["avg_latency"] == np.mean([0.1, 0.2, 0.3])
        assert analytics["avg_quality"] == np.mean([0.8, 0.9, 0.7])
        assert analytics["popular_queries"] == ["query1", "query2", "query3"]
        assert analytics["cache_hit_rate"] == 50 / (50 + 25)  # 0.666...

    @pytest.mark.asyncio
    async def test_get_analytics_with_empty_redis_data(self):
        """Test getting analytics when Redis returns empty data."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        # Mock empty Redis responses
        redis_client.hget.side_effect = [None, None, None]
        redis_client.lrange.side_effect = [None, None]
        redis_client.zrevrange.return_value = []

        analytics = await metrics.get_analytics()

        assert analytics["total_queries"] == 0
        assert analytics["avg_latency"] == 0.0
        assert analytics["avg_quality"] == 0.0
        assert analytics["popular_queries"] == []
        assert analytics["cache_hit_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_calculate_cache_hit_rate_without_redis(self):
        """Test calculating cache hit rate without Redis."""
        metrics = SearchMetrics()

        hit_rate = await metrics._calculate_cache_hit_rate()
        assert hit_rate == 0.0

    @pytest.mark.asyncio
    async def test_calculate_cache_hit_rate_with_data(self):
        """Test calculating cache hit rate with data."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        # Mock cache stats
        redis_client.hget.side_effect = [75, 25]  # 75 hits, 25 misses

        hit_rate = await metrics._calculate_cache_hit_rate()
        assert hit_rate == 0.75

    @pytest.mark.asyncio
    async def test_calculate_cache_hit_rate_no_data(self):
        """Test calculating cache hit rate with no data."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        # Mock no cache stats
        redis_client.hget.side_effect = [0, 0]

        hit_rate = await metrics._calculate_cache_hit_rate()
        assert hit_rate == 0.0

    @pytest.mark.asyncio
    async def test_calculate_cache_hit_rate_error_handling(self):
        """Test cache hit rate calculation with Redis error."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        # Mock Redis error
        redis_client.hget.side_effect = Exception("Redis error")

        hit_rate = await metrics._calculate_cache_hit_rate()
        assert hit_rate == 0.0


class TestSearchMetricsIntegration:
    """Test SearchMetrics integration scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_searches_tracking(self):
        """Test tracking multiple searches."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        # Log multiple searches
        searches = [
            ("python tutorial", [{"score": 0.9}, {"score": 0.8}], 0.1),
            ("async programming", [{"score": 0.7}, {"score": 0.6}, {"score": 0.5}], 0.2),
            ("redis cache", [{"score": 0.95}], 0.05),
        ]

        for query, results, execution_time in searches:
            await metrics.log_search(query, results, execution_time)

        # Verify all searches were logged
        assert redis_client.zadd.call_count == 3
        assert redis_client.hincrby.call_count == 3
        assert redis_client.lpush.call_count == 6  # 3 times + 3 quality

    @pytest.mark.asyncio
    async def test_analytics_data_types(self):
        """Test that analytics returns correct data types."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        # Set up realistic mock data
        redis_client.hget.side_effect = ["42", "100", "50"]  # String numbers
        redis_client.lrange.side_effect = [
            ["0.123", "0.456", "0.789"],  # String floats
            ["0.8", "0.85", "0.9"],
        ]
        redis_client.zrevrange.return_value = ["query1", "query2"]

        analytics = await metrics.get_analytics()

        # Check data types
        assert isinstance(analytics["total_queries"], (int, str))
        assert isinstance(analytics["avg_latency"], float)
        assert isinstance(analytics["avg_quality"], float)
        assert isinstance(analytics["popular_queries"], list)
        assert isinstance(analytics["cache_hit_rate"], float)

    @pytest.mark.asyncio
    async def test_concurrent_log_operations(self):
        """Test concurrent logging operations."""
        redis_client = AsyncMock()
        metrics = SearchMetrics(redis_client)

        # Simulate concurrent searches
        import asyncio

        async def log_search(i):
            await metrics.log_search(f"query_{i}", [{"score": 0.5 + i * 0.1}], 0.1 + i * 0.01)

        # Run multiple searches concurrently
        await asyncio.gather(*[log_search(i) for i in range(5)])

        # All operations should complete
        assert redis_client.zadd.call_count == 5
        assert redis_client.hincrby.call_count == 5
