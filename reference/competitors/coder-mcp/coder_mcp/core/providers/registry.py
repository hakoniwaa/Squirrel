#!/usr/bin/env python3
"""
Provider registry for MCP Server
Manages registration and discovery of provider types
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


@dataclass
class ProviderRegistration:
    """Information about a registered provider"""

    name: str
    provider_class: Type
    factory_method: Callable
    description: str
    requirements: List[str]
    supports_validation: bool = True

    def get_info(self) -> Dict[str, Any]:
        """Get provider registration information"""
        return {
            "name": self.name,
            "class": self.provider_class.__name__,
            "module": self.provider_class.__module__,
            "description": self.description,
            "requirements": self.requirements,
            "supports_validation": self.supports_validation,
        }


class ProviderCategory:
    """Category of providers (embedding, vector_store, cache)"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.providers: Dict[str, ProviderRegistration] = {}

    def register(self, registration: ProviderRegistration):
        """Register a provider in this category"""
        self.providers[registration.name] = registration
        logger.debug(f"Registered {registration.name} provider in {self.name} category")

    def get_provider(self, name: str) -> Optional[ProviderRegistration]:
        """Get provider registration by name"""
        return self.providers.get(name)

    def list_providers(self) -> List[str]:
        """List all provider names in this category"""
        return list(self.providers.keys())

    def get_info(self) -> Dict[str, Any]:
        """Get category information"""
        return {
            "name": self.name,
            "description": self.description,
            "provider_count": len(self.providers),
            "providers": {name: reg.get_info() for name, reg in self.providers.items()},
        }


class ProviderRegistry:
    """Central registry for managing provider types and categories"""

    def __init__(self):
        self.categories: Dict[str, ProviderCategory] = {}
        self._initialize_default_categories()
        self._register_built_in_providers()

    def _initialize_default_categories(self):
        """Initialize default provider categories"""
        self.categories["embedding"] = ProviderCategory(
            "embedding", "Text embedding providers for vector generation"
        )
        self.categories["vector_store"] = ProviderCategory(
            "vector_store", "Vector storage and retrieval providers"
        )
        self.categories["cache"] = ProviderCategory(
            "cache", "Caching providers for performance optimization"
        )

    def _register_built_in_providers(self):
        """Register built-in provider types"""
        try:
            from coder_mcp.storage.providers import (
                LocalEmbeddingProvider,
                MemoryVectorStore,
                OpenAIEmbeddingProvider,
                RedisCacheProvider,
                RedisVectorStore,
            )

            # Register embedding providers
            self.register_provider(
                "embedding",
                ProviderRegistration(
                    name="openai",
                    provider_class=OpenAIEmbeddingProvider,
                    factory_method=self._create_openai_embedding,
                    description="OpenAI text-embedding models",
                    requirements=["openai", "OPENAI_API_KEY"],
                ),
            )

            self.register_provider(
                "embedding",
                ProviderRegistration(
                    name="local",
                    provider_class=LocalEmbeddingProvider,
                    factory_method=self._create_local_embedding,
                    description="Local sentence-transformer models",
                    requirements=["sentence-transformers", "torch"],
                ),
            )

            # Register vector store providers
            self.register_provider(
                "vector_store",
                ProviderRegistration(
                    name="redis",
                    provider_class=RedisVectorStore,
                    factory_method=self._create_redis_vector_store,
                    description="Redis vector search with RediSearch",
                    requirements=["redis", "redis-connection"],
                ),
            )

            self.register_provider(
                "vector_store",
                ProviderRegistration(
                    name="memory",
                    provider_class=MemoryVectorStore,
                    factory_method=self._create_memory_vector_store,
                    description="In-memory vector storage",
                    requirements=[],
                ),
            )

            # Register cache providers
            self.register_provider(
                "cache",
                ProviderRegistration(
                    name="redis",
                    provider_class=RedisCacheProvider,
                    factory_method=self._create_redis_cache,
                    description="Redis-based caching",
                    requirements=["redis", "redis-connection"],
                ),
            )

            logger.info("Built-in providers registered successfully")

        except ImportError as e:
            logger.warning(f"Could not register some built-in providers: {e}")

    def register_provider(self, category: str, registration: ProviderRegistration):
        """Register a provider in a category"""
        if category not in self.categories:
            raise ValueError(f"Unknown provider category: {category}")

        self.categories[category].register(registration)
        logger.info(f"Registered provider: {category}.{registration.name}")

    def get_provider_registration(self, category: str, name: str) -> Optional[ProviderRegistration]:
        """Get provider registration"""
        if category not in self.categories:
            return None
        return self.categories[category].get_provider(name)

    def list_categories(self) -> List[str]:
        """List all provider categories"""
        return list(self.categories.keys())

    def list_providers(self, category: str) -> List[str]:
        """List providers in a category"""
        if category not in self.categories:
            return []
        return self.categories[category].list_providers()

    def get_category_info(self, category: str) -> Optional[Dict[str, Any]]:
        """Get information about a category"""
        if category not in self.categories:
            return None
        return self.categories[category].get_info()

    def get_all_info(self) -> Dict[str, Any]:
        """Get complete registry information"""
        return {
            "categories": {name: category.get_info() for name, category in self.categories.items()},
            "total_categories": len(self.categories),
            "total_providers": sum(
                len(category.providers) for category in self.categories.values()
            ),
        }

    def _add_missing(self, validation_result: Dict[str, Any], requirement: str) -> None:
        if not isinstance(validation_result["missing"], list):
            validation_result["missing"] = []
        validation_result["missing"].append(requirement)
        validation_result["valid"] = False

    def validate_provider_requirements(self, category: str, name: str) -> Dict[str, Any]:
        """Validate provider requirements"""
        registration = self.get_provider_registration(category, name)
        if not registration:
            return {"valid": False, "error": "Provider not found"}

        validation_result: Dict[str, Any] = {
            "valid": True,
            "requirements": (
                list(registration.requirements)
                if isinstance(registration.requirements, list)
                else []
            ),
            "missing": [],
            "errors": [],
        }

        for requirement in registration.requirements:
            if requirement.startswith("OPENAI_API_KEY"):
                # Check environment variable
                import os

                if not os.getenv("OPENAI_API_KEY"):
                    self._add_missing(validation_result, requirement)
            elif requirement == "redis-connection":
                # Check Redis connection
                try:
                    pass

                    # This would need actual Redis config to test
                    # For now, just check if redis package is available
                except ImportError:
                    self._add_missing(validation_result, "redis")
            else:
                # Check Python package
                try:
                    __import__(requirement)
                except ImportError:
                    self._add_missing(validation_result, requirement)

        return validation_result

    def create_provider(self, category: str, name: str, config: Any) -> Any:
        """Create provider instance using registered factory"""
        registration = self.get_provider_registration(category, name)
        if not registration:
            raise ValueError(f"Provider {category}.{name} not registered")

        try:
            return registration.factory_method(config)
        except Exception as e:
            logger.error(f"Failed to create provider {category}.{name}: {e}")
            raise

    # Built-in factory methods
    def _create_openai_embedding(self, config):
        """Factory method for OpenAI embedding provider"""
        from coder_mcp.storage.providers import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(
            api_key=config.openai_api_key, dimensions=config.vector.dimension
        )

    def _create_local_embedding(self, config):
        """Factory method for local embedding provider"""
        from coder_mcp.storage.providers import LocalEmbeddingProvider

        return LocalEmbeddingProvider(dimensions=config.vector.dimension)

    def _create_redis_vector_store(self, config):
        """Factory method for Redis vector store"""

        # This would need Redis client
        raise NotImplementedError("Redis vector store creation requires Redis client")

    def _create_memory_vector_store(self, config):
        """Factory method for memory vector store"""
        from coder_mcp.storage.providers import MemoryVectorStore

        return MemoryVectorStore()

    def _create_redis_cache(self, config):
        """Factory method for Redis cache provider"""

        # This would need Redis client
        raise NotImplementedError("Redis cache creation requires Redis client")

    def discover_providers(self) -> Dict[str, List[str]]:
        """Discover available providers by category"""
        discovered = {}
        for category_name, category in self.categories.items():
            available_providers = []
            for provider_name in category.list_providers():
                validation = self.validate_provider_requirements(category_name, provider_name)
                if validation["valid"]:
                    available_providers.append(provider_name)
            discovered[category_name] = available_providers
        return discovered

    def get_recommended_providers(self, config: Any) -> Dict[str, str]:
        """Get recommended providers based on configuration"""
        recommendations = {}

        # Recommend embedding provider
        if hasattr(config, "openai_api_key") and config.openai_api_key:
            recommendations["embedding"] = "openai"
        else:
            recommendations["embedding"] = "local"

        # Recommend vector store
        if hasattr(config, "redis") and hasattr(config.redis, "password") and config.redis.password:
            recommendations["vector_store"] = "redis"
        else:
            recommendations["vector_store"] = "memory"

        # Recommend cache provider
        if hasattr(config, "redis") and hasattr(config.redis, "password") and config.redis.password:
            recommendations["cache"] = "redis"
        else:
            recommendations["cache"] = "memory"

        return recommendations
