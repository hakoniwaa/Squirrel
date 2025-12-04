"""
Multi-Level Search Cache
Caching system for embeddings and search results to improve performance
"""

import asyncio
import hashlib
import logging
import pickle
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU cache implementation"""

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self.cache: Dict[str, Any] = {}
        self.access_order: List[str] = []

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set item in cache"""
        if key in self.cache:
            # Update existing item
            self.access_order.remove(key)
        elif len(self.cache) >= self.maxsize:
            # Remove least recently used item
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]

        self.cache[key] = value
        self.access_order.append(key)

    def __contains__(self, key: str) -> bool:
        return key in self.cache

    def clear(self) -> None:
        """Clear all items from cache"""
        self.cache.clear()
        self.access_order.clear()

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)


class SearchCache:
    """Multi-level caching for search operations"""

    def __init__(self, redis_client: Optional[Any] = None):
        self.redis_client = redis_client

        # Local caches
        self.local_cache = LRUCache(maxsize=1000)
        self.embedding_cache = LRUCache(maxsize=5000)
        self.query_cache = LRUCache(maxsize=2000)

        # Cache TTLs (in seconds)
        self.embedding_ttl = 3600  # 1 hour
        self.search_ttl = 600  # 10 minutes
        self.query_ttl = 1800  # 30 minutes

        # Cache statistics
        self.stats = {
            "embedding_hits": 0,
            "embedding_misses": 0,
            "search_hits": 0,
            "search_misses": 0,
            "query_hits": 0,
            "query_misses": 0,
        }

    async def get_or_compute_embedding(
        self, text: str, model: str, compute_func: Callable[[], List[float]]
    ) -> Optional[List[float]]:
        """Get embedding from cache or compute and cache it"""
        cache_key = (
            f"embedding:{model}:{hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()}"
        )

        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    cached_result = pickle.loads(cached_data)  # nosec B301
                    if isinstance(cached_result, list) and all(
                        isinstance(x, float) for x in cached_result
                    ):
                        return cached_result
                    # If cached result is not the expected type, continue to compute
            except Exception as e:
                logger.warning(f"Failed to get embedding from cache: {e}")

        # Compute embedding
        try:
            embedding = compute_func()
            if isinstance(embedding, list) and all(isinstance(x, float) for x in embedding):
                # Cache the result
                if self.redis_client:
                    await self.redis_client.setex(
                        cache_key, self.embedding_ttl, pickle.dumps(embedding)  # nosec B301
                    )
                return embedding
        except Exception as e:
            logger.error(f"Failed to compute embedding: {e}")

        return None

    async def get_or_compute_batch_embeddings(
        self, texts: List[str], model: str, compute_func: Callable[[], List[List[float]]]
    ) -> List[List[float]]:
        """Get batch embeddings from cache or compute and cache them"""
        cached_embeddings, missing_indices = await self._check_cached_embeddings(texts, model)

        if missing_indices:
            await self._compute_and_cache_missing_embeddings(
                texts, model, missing_indices, cached_embeddings, compute_func
            )

        return self._build_final_embeddings(cached_embeddings)

    async def _check_cached_embeddings(
        self, texts: List[str], model: str
    ) -> tuple[List[Optional[List[float]]], List[int]]:
        """Check cache for embeddings and return cached results and missing indices"""
        cached_embeddings: List[Optional[List[float]]] = []
        missing_indices: List[int] = []

        for i, text in enumerate(texts):
            cache_key = (
                f"embedding:{model}:{hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()}"
            )

            if self.redis_client:
                try:
                    cached_data = await self.redis_client.get(cache_key)
                    if cached_data:
                        cached_result = pickle.loads(cached_data)  # nosec B301
                        if isinstance(cached_result, list) and all(
                            isinstance(x, float) for x in cached_result
                        ):
                            cached_embeddings.append(cached_result)
                            continue
                except Exception as e:
                    logger.warning(f"Failed to get embedding from cache: {e}")

            cached_embeddings.append(None)
            missing_indices.append(i)

        return cached_embeddings, missing_indices

    async def _compute_and_cache_missing_embeddings(
        self,
        texts: List[str],
        model: str,
        missing_indices: List[int],
        cached_embeddings: List[Optional[List[float]]],
        compute_func: Callable[[], List[List[float]]],
    ) -> None:
        """Compute missing embeddings and cache them"""
        try:
            computed_embeddings = compute_func()
            if not isinstance(computed_embeddings, list):
                logger.error("Computed embeddings is not a list")
                return

            for i, embedding in enumerate(computed_embeddings):
                if i < len(missing_indices):
                    original_index = missing_indices[i]
                    if (
                        original_index < len(texts)
                        and isinstance(embedding, list)
                        and all(isinstance(x, float) for x in embedding)
                    ):
                        text_hash = hashlib.md5(
                            texts[original_index].encode(), usedforsecurity=False
                        ).hexdigest()
                        cache_key = f"embedding:{model}:{text_hash}"

                        if self.redis_client:
                            await self.redis_client.setex(
                                cache_key, self.embedding_ttl, pickle.dumps(embedding)  # nosec B301
                            )
                        cached_embeddings[original_index] = embedding
        except Exception as e:
            logger.error(f"Failed to compute batch embeddings: {e}")

    def _build_final_embeddings(
        self, cached_embeddings: List[Optional[List[float]]]
    ) -> List[List[float]]:
        """Build final result, replacing None values with empty lists"""
        return [cached_emb if cached_emb is not None else [] for cached_emb in cached_embeddings]

    async def get_or_compute_search_results(
        self, query: str, search_type: str, compute_func: Callable[[], List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Get search results from cache or compute and cache them"""
        cache_key = (
            f"search:{search_type}:{hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()}"
        )

        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    cached_result = pickle.loads(cached_data)  # nosec B301
                    if isinstance(cached_result, list):
                        return cached_result
            except Exception as e:
                logger.warning(f"Failed to get search results from cache: {e}")

        # Compute search results
        try:
            results = compute_func()
            if isinstance(results, list):
                # Cache the result
                if self.redis_client:
                    await self.redis_client.setex(
                        cache_key, self.search_ttl, pickle.dumps(results)  # nosec B301
                    )
                return results
        except Exception as e:
            logger.error(f"Failed to compute search results: {e}")

        return []

    async def get_or_compute_query_processing(
        self, query: str, compute_func: Callable[[], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get query processing results from cache or compute and cache them"""
        cache_key = (
            f"query_processing:{hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()}"
        )

        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    cached_result = pickle.loads(cached_data)  # nosec B301
                    if isinstance(cached_result, dict):
                        return cached_result
            except Exception as e:
                logger.warning(f"Failed to get query processing from cache: {e}")

        # Compute query processing
        try:
            result = compute_func()
            if isinstance(result, dict):
                # Cache the result
                if self.redis_client:
                    await self.redis_client.setex(
                        cache_key, self.query_ttl, pickle.dumps(result)  # nosec B301
                    )
                return result
        except Exception as e:
            logger.error(f"Failed to compute query processing: {e}")

        return {}

    async def invalidate_embedding(self, text: str, context_type: str = "default") -> None:
        """Invalidate cached embedding"""
        cache_key = self._generate_embedding_key(text, context_type)

        # Remove from local cache
        if cache_key in self.embedding_cache:
            self.embedding_cache.cache.pop(cache_key, None)
            if cache_key in self.embedding_cache.access_order:
                self.embedding_cache.access_order.remove(cache_key)

        # Remove from Redis
        if self.redis_client:
            await self._delete_from_redis(f"emb:{cache_key}")

    async def invalidate_search_pattern(self, pattern: str) -> None:
        """Invalidate cached search results matching a pattern"""
        if self.redis_client:
            # Get all search cache keys
            keys = await self._get_keys_pattern(f"search:*{pattern}*")
            if keys:
                await self._delete_from_redis(*keys)

        # Clear local cache (simple approach)
        self.local_cache.clear()

    async def clear_all_caches(self) -> None:
        """Clear all caches"""
        self.local_cache.clear()
        self.embedding_cache.clear()
        self.query_cache.clear()

        if self.redis_client:
            # Clear Redis caches
            patterns = ["emb:*", "search:*", "query:*"]
            for pattern in patterns:
                keys = await self._get_keys_pattern(pattern)
                if keys:
                    await self._delete_from_redis(*keys)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_embedding_requests = self.stats["embedding_hits"] + self.stats["embedding_misses"]
        total_search_requests = self.stats["search_hits"] + self.stats["search_misses"]
        total_query_requests = self.stats["query_hits"] + self.stats["query_misses"]

        return {
            "embedding_cache": {
                "hits": self.stats["embedding_hits"],
                "misses": self.stats["embedding_misses"],
                "hit_rate": self.stats["embedding_hits"] / max(1, total_embedding_requests),
                "size": self.embedding_cache.size(),
                "max_size": self.embedding_cache.maxsize,
            },
            "search_cache": {
                "hits": self.stats["search_hits"],
                "misses": self.stats["search_misses"],
                "hit_rate": self.stats["search_hits"] / max(1, total_search_requests),
                "size": self.local_cache.size(),
                "max_size": self.local_cache.maxsize,
            },
            "query_cache": {
                "hits": self.stats["query_hits"],
                "misses": self.stats["query_misses"],
                "hit_rate": self.stats["query_hits"] / max(1, total_query_requests),
                "size": self.query_cache.size(),
                "max_size": self.query_cache.maxsize,
            },
            "redis_enabled": self.redis_client is not None,
        }

    def _generate_embedding_key(self, text: str, context_type: str) -> str:
        """Generate cache key for embedding"""
        content = f"{context_type}:{text}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def _generate_search_key(self, query: str, params: Dict[str, Any]) -> str:
        """Generate cache key for search"""
        # Create a stable string representation of parameters
        param_str = str(sorted(params.items()))
        content = f"{query}:{param_str}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    def _generate_query_key(self, query: str) -> str:
        """Generate cache key for query processing"""
        return hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()

    async def _get_from_redis(self, key: str) -> Optional[bytes]:
        """Get value from Redis"""
        try:
            if not self.redis_client:
                return None

            # Use asyncio to run Redis operation
            return await asyncio.get_event_loop().run_in_executor(None, self.redis_client.get, key)
        except Exception as e:
            logger.error(f"Failed to get from Redis: {e}")
            return None

    async def _set_in_redis(self, key: str, value: bytes, ttl: int) -> None:
        """Set value in Redis with TTL"""
        try:
            if not self.redis_client:
                return

            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.setex, key, ttl, value
            )
        except Exception as e:
            logger.error(f"Failed to set in Redis: {e}")

    async def _delete_from_redis(self, *keys: str) -> None:
        """Delete keys from Redis"""
        try:
            if not self.redis_client or not keys:
                return

            await asyncio.get_event_loop().run_in_executor(None, self.redis_client.delete, *keys)
        except Exception as e:
            logger.error(f"Failed to delete from Redis: {e}")

    async def _get_keys_pattern(self, pattern: str) -> List[str]:
        """Get keys matching pattern from Redis"""
        try:
            if not self.redis_client:
                return []

            keys = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.keys, pattern
            )
            return [key.decode() if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            logger.error(f"Failed to get keys from Redis: {e}")
            return []


class BatchProcessor:
    """Process multiple queries efficiently"""

    def __init__(self, cache: SearchCache, max_concurrency: int = 10):
        self.cache = cache
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)

    async def batch_search(
        self,
        queries: List[str],
        search_func: Callable[[str, int], Any],
        search_params: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
    ) -> List[List[Dict[str, Any]]]:
        """Process multiple queries in parallel"""

        search_params = search_params or {}

        async def process_single_query(query: str) -> List[Dict[str, Any]]:
            async with self.semaphore:
                return await self.cache.get_or_compute_search_results(
                    query, "default", lambda: search_func(query, top_k)
                )

        # Execute searches in parallel
        tasks = [process_single_query(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results: List[List[Dict[str, Any]]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Query '{queries[i]}' failed: {result}")
                processed_results.append([])
            elif isinstance(result, list):
                processed_results.append(result)
            else:
                processed_results.append([])

        return processed_results

    async def batch_embeddings(
        self, texts: List[str], embedding_func: Callable[[str], Any], context_type: str = "default"
    ) -> List[Optional[List[float]]]:
        """Process multiple embeddings in parallel"""

        async def process_single_embedding(text: str) -> Optional[List[float]]:
            async with self.semaphore:
                return await self.cache.get_or_compute_embedding(
                    text, "default", lambda: embedding_func(text)
                )

        # Execute embedding creation in parallel
        tasks = [process_single_embedding(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        processed_results: List[Optional[List[float]]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Embedding for text '{texts[i][:50]}...' failed: {result}")
                processed_results.append(None)
            elif isinstance(result, list) or result is None:
                processed_results.append(result)
            else:
                processed_results.append(None)

        return processed_results
