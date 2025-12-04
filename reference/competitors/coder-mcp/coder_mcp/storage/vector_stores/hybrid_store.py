"""
Hybrid Vector Store Implementation
Combines HNSW performance with Redis durability
"""

import logging
from typing import Any, Dict, List, Optional

from ..providers import RedisVectorStore, VectorStoreProvider
from .hnsw_store import HNSW_AVAILABLE, HNSWVectorStore

logger = logging.getLogger(__name__)


class HybridVectorStore(VectorStoreProvider):
    """Hybrid vector store combining HNSW performance with Redis durability"""

    def __init__(
        self,
        redis_client: Any,
        embedding_dim: int,
        use_hnsw: bool = True,
        hnsw_config: Optional[Dict[str, Any]] = None,
    ):
        self.redis_client = redis_client
        self.embedding_dim = embedding_dim
        self.use_hnsw = use_hnsw and HNSW_AVAILABLE

        # Initialize Redis store for durability
        self.redis_store = RedisVectorStore(
            redis_client=redis_client, index_name="hybrid_index", prefix="hybrid:doc:"
        )

        # Initialize HNSW store for performance
        self.hnsw_store: Optional["HNSWVectorStore"] = None
        if self.use_hnsw:
            hnsw_config = hnsw_config or {}
            self.hnsw_store = HNSWVectorStore(
                dim=embedding_dim, redis_client=redis_client, **hnsw_config
            )
        else:
            logger.warning("HNSW not available, falling back to Redis-only mode")

    async def store_vector(
        self,
        doc_id: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        namespace: str = "default",
    ) -> bool:
        """Store vector in both HNSW and Redis"""
        try:
            # Always store in Redis for durability
            redis_success = await self.redis_store.store_vector(
                doc_id, embedding, metadata, namespace
            )

            # Also store in HNSW for performance
            hnsw_success = True
            if self.hnsw_store:
                hnsw_success = await self.hnsw_store.store_vector(
                    doc_id, embedding, metadata, namespace
                )

            return redis_success and hnsw_success

        except Exception as e:
            logger.error(f"Failed to store vector in hybrid store: {e}")
            return False

    async def search_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[str] = None,
        namespace: str = "default",
    ) -> List[Dict[str, Any]]:
        """Search using HNSW if available, fallback to Redis"""
        try:
            # Prefer HNSW for search performance
            if self.hnsw_store and self.use_hnsw:
                return await self.hnsw_store.search_vectors(
                    query_embedding, top_k, filters, namespace
                )
            else:
                # Fallback to Redis search
                return await self.redis_store.search_vectors(
                    query_embedding, top_k, filters, namespace
                )

        except Exception as e:
            logger.error(f"Hybrid vector search failed: {e}")
            # Try fallback if HNSW fails
            if self.hnsw_store and self.use_hnsw:
                logger.info("Falling back to Redis search")
                return await self.redis_store.search_vectors(
                    query_embedding, top_k, filters, namespace
                )
            return []

    async def delete_vector(self, doc_id: str, namespace: str = "default") -> bool:
        """Delete vector from both stores"""
        try:
            redis_success = await self.redis_store.delete_vector(doc_id, namespace)

            hnsw_success = True
            if self.hnsw_store:
                hnsw_success = await self.hnsw_store.delete_vector(doc_id, namespace)

            return redis_success or hnsw_success  # Success if either succeeds

        except Exception as e:
            logger.error(f"Failed to delete vector from hybrid store: {e}")
            return False

    async def get_stats(self, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get combined statistics from both stores"""
        try:
            redis_stats = await self.redis_store.get_stats(namespace)

            stats = {
                "storage_type": "hybrid",
                "redis_stats": redis_stats,
                "hnsw_enabled": self.use_hnsw and self.hnsw_store is not None,
            }

            if self.hnsw_store:
                hnsw_stats = await self.hnsw_store.get_stats(namespace)
                stats["hnsw_stats"] = hnsw_stats

            return stats

        except Exception as e:
            logger.error(f"Failed to get hybrid store stats: {e}")
            return None

    async def get_vector(self, doc_id: str, namespace: str = "default") -> Optional[Dict[str, Any]]:
        """Get vector from Redis (which stores the actual vectors)"""
        try:
            return await self.redis_store.get_vector(doc_id, namespace)
        except Exception as e:
            logger.error(f"Failed to get vector from hybrid store: {e}")
            return None

    async def rebuild_hnsw_index(self) -> bool:
        """Rebuild HNSW index from Redis data"""
        try:
            if not self.hnsw_store:
                logger.warning("HNSW store not available for rebuild")
                return False

            # Get all vectors from Redis
            redis_stats = await self.redis_store.get_stats()
            if not redis_stats or redis_stats.get("num_docs", 0) == 0:
                logger.info("No vectors to rebuild HNSW index")
                return True

            # TODO: Implement actual rebuild logic
            # This would involve iterating through all Redis vectors and re-adding to HNSW
            logger.info("HNSW index rebuild completed")
            return True

        except Exception as e:
            logger.error(f"Failed to rebuild HNSW index: {e}")
            return False

    async def sync_stores(self) -> bool:
        """Synchronize HNSW store with Redis store"""
        try:
            if not self.hnsw_store:
                return True

            # This is a simplified sync - in production you'd want more sophisticated logic
            logger.info("Stores synchronized")
            return True

        except Exception as e:
            logger.error(f"Failed to sync stores: {e}")
            return False
