#!/usr/bin/env python3
"""
Provider factory for MCP Server
Handles creation of provider instances based on configuration
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from coder_mcp.storage.providers import (
    CacheProvider,
    EmbeddingProvider,
    LocalEmbeddingProvider,
    MemoryVectorStore,
    OpenAIEmbeddingProvider,
    RedisCacheProvider,
    RedisVectorStore,
    VectorStoreProvider,
)

from ..config.models import MCPConfiguration

logger = logging.getLogger(__name__)


class BaseProviderFactory(ABC):
    """Abstract base class for provider factories"""

    def __init__(self, config: MCPConfiguration):
        self.config = config

    @abstractmethod
    def create(self) -> Any:
        """Create provider instance"""

    @abstractmethod
    def validate(self) -> bool:
        """Validate that provider can be created"""


class EmbeddingProviderFactory(BaseProviderFactory):
    """Factory for creating embedding providers"""

    def create(self) -> EmbeddingProvider:
        """Create embedding provider based on configuration"""
        provider_type = self.config.embedding_provider_type

        if provider_type == "openai":
            if not self.config.openai_api_key:
                logger.warning("OpenAI API key not found, falling back to local provider")
                return LocalEmbeddingProvider(dimensions=self.config.vector.dimension)

            return OpenAIEmbeddingProvider(
                api_key=self.config.openai_api_key, dimensions=self.config.vector.dimension
            )
        elif provider_type == "local":
            return LocalEmbeddingProvider(dimensions=self.config.vector.dimension)
        else:
            raise ValueError(f"Unknown embedding provider type: {provider_type}")

    def validate(self) -> bool:
        """Validate embedding provider can be created"""
        try:
            provider_type = self.config.embedding_provider_type

            if provider_type == "openai":
                if not self.config.openai_api_key:
                    logger.warning("OpenAI provider validation: No API key provided")
                    return False
                if len(self.config.openai_api_key) < 20:
                    logger.warning("OpenAI provider validation: API key seems too short")
                    return False
            elif provider_type == "local":
                # Local provider should always work
                return True
            else:
                logger.error(f"Unknown embedding provider type: {provider_type}")
                return False

            return True
        except Exception as e:
            logger.error(f"Embedding provider validation failed: {e}")
            return False


class VectorStoreProviderFactory(BaseProviderFactory):
    """Factory for creating vector store providers"""

    def __init__(self, config: MCPConfiguration, redis_client=None):
        super().__init__(config)
        self._redis_client = redis_client

    def create(self) -> VectorStoreProvider:
        """Create vector store provider based on configuration"""
        store_type = self.config.vector_store_type

        if store_type == "redis":
            redis_client = self._get_redis_client()
            if redis_client:
                return RedisVectorStore(
                    redis_client=redis_client,
                    index_name=self.config.vector.index_name,
                    prefix=self.config.vector.prefix,
                )
            else:
                logger.warning("Redis not available, falling back to memory vector store")

        return MemoryVectorStore()

    def validate(self) -> bool:
        """Validate vector store provider can be created"""
        try:
            store_type = self.config.vector_store_type

            if store_type == "redis":
                redis_client = self._get_redis_client()
                if not redis_client:
                    logger.warning("Vector store validation: Redis client not available")
                    return False

                # Test Redis connection
                try:
                    redis_client.ping()
                    return True
                except Exception as e:
                    logger.warning(f"Vector store validation: Redis ping failed: {e}")
                    return False
            elif store_type == "memory":
                # Memory store should always work
                return True
            else:
                logger.error(f"Unknown vector store type: {store_type}")
                return False
        except Exception as e:
            logger.error(f"Vector store validation failed: {e}")
            return False

    def _get_redis_client(self):
        """Get Redis client (shared with other factories)"""
        if self._redis_client:
            return self._redis_client

        try:
            import redis
            from redis import ConnectionPool

            pool = ConnectionPool(
                host=self.config.redis.host,
                port=self.config.redis.port,
                password=self.config.redis.password,
                decode_responses=self.config.redis.decode_responses,
                socket_timeout=self.config.redis.socket_timeout,
                socket_connect_timeout=self.config.redis.socket_connect_timeout,
                max_connections=self.config.redis.max_connections,
            )

            self._redis_client = redis.Redis(connection_pool=pool)
            self._redis_client.ping()  # Test connection

            logger.info(f"Connected to Redis at {self.config.redis.host}:{self.config.redis.port}")
            return self._redis_client

        except ImportError:
            logger.error("Redis package not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return None


class CacheProviderFactory(BaseProviderFactory):
    """Factory for creating cache providers"""

    def __init__(self, config: MCPConfiguration, redis_client=None):
        super().__init__(config)
        self._redis_client = redis_client

    def create(self) -> CacheProvider:
        """Create cache provider based on configuration"""
        cache_type = self.config.cache_provider_type

        if cache_type == "redis":
            redis_client = self._get_redis_client()
            if redis_client:
                return RedisCacheProvider(redis_client=redis_client)

        # Fallback to local cache
        return self._create_local_cache_provider()

    def validate(self) -> bool:
        """Validate cache provider can be created"""
        try:
            cache_type = self.config.cache_provider_type

            if cache_type == "redis":
                redis_client = self._get_redis_client()
                if not redis_client:
                    logger.warning("Cache provider validation: Redis client not available")
                    return False

                # Test Redis connection
                try:
                    redis_client.ping()
                    return True
                except Exception as e:
                    logger.warning(f"Cache provider validation: Redis ping failed: {e}")
                    return False
            elif cache_type == "memory":
                # Memory cache should always work
                return True
            else:
                logger.error(f"Unknown cache provider type: {cache_type}")
                return False
        except Exception as e:
            logger.error(f"Cache provider validation failed: {e}")
            return False

    def _get_redis_client(self):
        """Get Redis client (shared with vector store factory)"""
        if self._redis_client:
            return self._redis_client

        try:
            import redis
            from redis import ConnectionPool

            pool = ConnectionPool(
                host=self.config.redis.host,
                port=self.config.redis.port,
                password=self.config.redis.password,
                decode_responses=self.config.redis.decode_responses,
                socket_timeout=self.config.redis.socket_timeout,
                socket_connect_timeout=self.config.redis.socket_connect_timeout,
                max_connections=self.config.redis.max_connections,
            )

            self._redis_client = redis.Redis(connection_pool=pool)
            self._redis_client.ping()  # Test connection

            return self._redis_client

        except ImportError:
            logger.error("Redis package not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return None

    def _create_local_cache_provider(self) -> CacheProvider:
        """Create local cache provider"""
        from typing import Any

        from coder_mcp.utils.cache import ThreadSafeCache

        class LocalCacheProvider(CacheProvider):
            def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
                self.cache = ThreadSafeCache(max_size=max_size, default_ttl=default_ttl)

            async def get(self, key: str) -> Optional[Any]:
                return self.cache.get(key)

            async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
                self.cache.set(key, value, ttl)
                return True

            async def delete(self, key: str) -> bool:
                # ThreadSafeCache doesn't have delete, but we can set to None with 0 TTL
                self.cache.set(key, None, 0)
                return True

            async def clear(self) -> bool:
                self.cache.clear()
                return True

        return LocalCacheProvider(max_size=1000, default_ttl=self.config.storage.cache_ttl)


class ProviderFactory:
    """Main factory for creating all provider types"""

    def __init__(self, config: MCPConfiguration):
        self.config = config
        self._redis_client = None

        # Create specialized factories
        self.embedding_factory = EmbeddingProviderFactory(config)
        self.vector_store_factory = VectorStoreProviderFactory(config, self._redis_client)
        self.cache_factory = CacheProviderFactory(config, self._redis_client)

    def create_embedding_provider(self) -> EmbeddingProvider:
        """Create embedding provider"""
        return self.embedding_factory.create()

    def create_vector_store(self) -> VectorStoreProvider:
        """Create vector store provider"""
        return self.vector_store_factory.create()

    def create_cache_provider(self) -> CacheProvider:
        """Create cache provider"""
        return self.cache_factory.create()

    def validate_providers(self) -> dict:
        """Validate all providers can be created"""
        return {
            "embedding": self.embedding_factory.validate(),
            "vector_store": self.vector_store_factory.validate(),
            "cache": self.cache_factory.validate(),
            "redis": self._validate_redis_connection(),
        }

    def _validate_redis_connection(self) -> bool:
        """Validate Redis connection if required"""
        if self.config.is_redis_required():
            try:
                redis_client = self._get_redis_client()
                if redis_client:
                    redis_client.ping()
                    return True
                return False
            except Exception:
                return False
        return True  # Redis not required

    def _get_redis_client(self):
        """Get shared Redis client"""
        if self._redis_client:
            return self._redis_client

        try:
            import redis
            from redis import ConnectionPool

            pool = ConnectionPool(
                host=self.config.redis.host,
                port=self.config.redis.port,
                password=self.config.redis.password,
                decode_responses=self.config.redis.decode_responses,
                socket_timeout=self.config.redis.socket_timeout,
                socket_connect_timeout=self.config.redis.socket_connect_timeout,
                max_connections=self.config.redis.max_connections,
            )

            self._redis_client = redis.Redis(connection_pool=pool)

            # Share Redis client with other factories
            self.vector_store_factory._redis_client = self._redis_client
            self.cache_factory._redis_client = self._redis_client

            logger.info(f"Connected to Redis at {self.config.redis.host}:{self.config.redis.port}")
            return self._redis_client

        except ImportError:
            logger.error("Redis package not installed")
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return None
