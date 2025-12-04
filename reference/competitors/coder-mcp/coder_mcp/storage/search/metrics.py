import time
from typing import Any, Dict, List, Optional

import numpy as np


class SearchMetrics:
    """Track search quality and performance"""

    def __init__(self, redis_client: Optional[Any] = None):
        self.queries: List[str] = []
        self.click_through_rate: Dict[str, float] = {}
        self.query_times: List[float] = []
        self.redis = redis_client

    async def log_search(
        self, query: str, results: List[Dict[str, Any]], execution_time: float
    ) -> None:
        """Log search execution"""

        if self.redis:
            await self.redis.zadd("search:queries", {query: time.time()})
            await self.redis.hincrby("search:stats", "total_queries", 1)
            await self.redis.lpush("search:times", execution_time)

            # Track result quality
            if results:
                avg_score = sum(r.get("score", 0.0) for r in results) / len(results)
                await self.redis.lpush("search:quality", avg_score)

    async def get_analytics(self) -> Dict[str, Any]:
        """Get search analytics"""

        if not self.redis:
            return {
                "total_queries": 0,
                "avg_latency": 0.0,
                "avg_quality": 0.0,
                "popular_queries": [],
                "cache_hit_rate": 0.0,
            }

        # Get raw data from Redis
        total_queries = await self.redis.hget("search:stats", "total_queries") or 0
        times_raw = await self.redis.lrange("search:times", 0, 100) or []
        quality_raw = await self.redis.lrange("search:quality", 0, 100) or []
        popular_queries = await self.redis.zrevrange("search:queries", 0, 10)

        # Convert string data to numeric types
        try:
            total_queries = int(total_queries) if total_queries else 0
        except (ValueError, TypeError):
            total_queries = 0

        # Convert times to floats
        times = []
        for t in times_raw:
            try:
                times.append(float(t))
            except (ValueError, TypeError):
                continue

        # Convert quality scores to floats
        quality_scores = []
        for q in quality_raw:
            try:
                quality_scores.append(float(q))
            except (ValueError, TypeError):
                continue

        return {
            "total_queries": total_queries,
            "avg_latency": np.mean(times) if times else 0.0,
            "avg_quality": np.mean(quality_scores) if quality_scores else 0.0,
            "popular_queries": popular_queries,
            "cache_hit_rate": await self._calculate_cache_hit_rate(),
        }

    async def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if not self.redis:
            return 0.0

        try:
            hits = await self.redis.hget("cache:stats", "hits") or 0
            misses = await self.redis.hget("cache:stats", "misses") or 0
            total = int(hits) + int(misses)
            return float(hits) / total if total > 0 else 0.0
        except Exception:
            return 0.0
