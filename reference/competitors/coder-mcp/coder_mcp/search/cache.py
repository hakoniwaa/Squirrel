import hashlib
import pickle
from typing import Awaitable, Callable, List

from coder_mcp.context.search.cache import LRUCache


class SearchCache:
    """Multi-level caching for search operations"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_cache = LRUCache(maxsize=1000)
        self.embedding_cache = LRUCache(maxsize=5000)

    async def get_or_compute_embedding(
        self, text: str, compute_func: Callable[[str], Awaitable[List[float]]]
    ) -> List[float]:
        """Cache embeddings to avoid recomputation"""

        # Generate cache key
        cache_key = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()

        # Check local cache first
        if cache_key in self.embedding_cache:
            return self.embedding_cache.get(cache_key)  # type: ignore

        # Check Redis
        cached = await self.redis.get(f"emb:{cache_key}")
        if cached:
            # Note: pickle is used here for performance with embeddings (numpy arrays)
            # This is safe as we control the data source (our own cache)
            embedding: List[float] = pickle.loads(cached)  # nosec B301
            self.embedding_cache.set(cache_key, embedding)
            return embedding

        # Compute and cache
        embedding = await compute_func(text)

        # Store in both caches
        self.embedding_cache.set(cache_key, embedding)
        await self.redis.setex(f"emb:{cache_key}", 3600, pickle.dumps(embedding))  # 1 hour TTL

        return embedding
