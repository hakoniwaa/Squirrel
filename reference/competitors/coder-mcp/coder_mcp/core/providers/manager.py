#!/usr/bin/env python3
"""
Provider manager for MCP Server
Manages provider lifecycle with lazy loading and caching
"""

import logging
import time
from collections import Counter
from enum import Enum
from typing import Any, Dict, Optional

from coder_mcp.storage.providers import CacheProvider, EmbeddingProvider, VectorStoreProvider

from ..config.models import MCPConfiguration
from .factory import ProviderFactory
from .registry import ProviderRegistry

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Provider status enumeration"""

    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DESTROYED = "destroyed"


class ProviderInfo:
    """Information about a provider instance"""

    def __init__(self, provider_type: str):
        self.provider_type = provider_type
        self.status = ProviderStatus.NOT_INITIALIZED
        self.instance = None
        self.error_message: Optional[str] = None
        self.creation_time = None
        self.access_count = 0
        self.last_access_time = None

    def set_ready(self, instance):
        """Mark provider as ready"""
        self.instance = instance
        self.status = ProviderStatus.READY
        self.error_message = None
        self.creation_time = time.time()

    def set_error(self, error_message: str):
        """Mark provider as having an error"""
        self.status = ProviderStatus.ERROR
        self.error_message = error_message
        self.instance = None

    def record_access(self):
        """Record an access to this provider"""
        self.access_count += 1
        self.last_access_time = time.time()

    def get_info(self) -> Dict[str, Any]:
        """Get provider information dictionary"""
        return {
            "type": self.provider_type,
            "status": self.status.value,
            "error_message": self.error_message,
            "creation_time": self.creation_time,
            "access_count": self.access_count,
            "last_access_time": self.last_access_time,
            "instance_type": type(self.instance).__name__ if self.instance else None,
        }


class ProviderManager:
    """Manage provider lifecycle with lazy loading and caching"""

    def __init__(self, config: MCPConfiguration):
        self.config = config
        self.registry = ProviderRegistry()
        self.factory = ProviderFactory(config)

        # Provider instances and metadata
        self._providers: Dict[str, ProviderInfo] = {}

        # Initialize provider info objects
        self._initialize_provider_info()

    def _initialize_provider_info(self):
        """Initialize provider info objects"""
        provider_types = ["embedding", "vector_store", "cache"]
        for provider_type in provider_types:
            self._providers[provider_type] = ProviderInfo(provider_type)

    def get_provider(self, provider_type: str) -> Any:
        """Get provider instance with lazy loading"""
        if provider_type not in self._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")

        provider_info = self._providers[provider_type]

        # Return existing instance if available
        if provider_info.status == ProviderStatus.READY:
            provider_info.record_access()
            return provider_info.instance

        # Return None if provider has an error
        if provider_info.status == ProviderStatus.ERROR:
            logger.warning("Provider %s has error: %s", provider_type, provider_info.error_message)
            return None

        # Create provider instance
        return self._create_provider(provider_type)

    def _create_provider(self, provider_type: str) -> Any:
        """Create provider instance"""
        provider_info = self._providers[provider_type]

        try:
            provider_info.status = ProviderStatus.INITIALIZING
            logger.info("Creating %s provider...", provider_type)

            # Create provider using factory
            instance: Any
            if provider_type == "embedding":
                instance = self.factory.create_embedding_provider()
            elif provider_type == "vector_store":
                instance = self.factory.create_vector_store()
            elif provider_type == "cache":
                instance = self.factory.create_cache_provider()
            else:
                raise ValueError(f"Unknown provider type: {provider_type}")

            provider_info.set_ready(instance)
            provider_info.record_access()

            logger.info("%s provider created: %s", provider_type, type(instance).__name__)
            return instance

        except (ValueError, ImportError, ConnectionError, RuntimeError) as e:
            error_msg = f"Failed to create {provider_type} provider: {e}"
            logger.error(error_msg)
            provider_info.set_error(error_msg)
            return None

    @property
    def embedding_provider(self) -> Optional[EmbeddingProvider]:
        """Get embedding provider (lazy loaded)"""
        provider = self.get_provider("embedding")
        return provider if provider is None or isinstance(provider, EmbeddingProvider) else None

    @property
    def vector_store(self) -> Optional[VectorStoreProvider]:
        """Get vector store (lazy loaded)"""
        provider = self.get_provider("vector_store")
        return provider if provider is None or isinstance(provider, VectorStoreProvider) else None

    @property
    def cache_provider(self) -> Optional[CacheProvider]:
        """Get cache provider (lazy loaded)"""
        provider = self.get_provider("cache")
        return provider if provider is None or isinstance(provider, CacheProvider) else None

    def validate_configuration(self) -> Dict[str, bool]:
        """Validate that all providers can be created"""
        logger.info("Validating provider configuration...")
        validation_results = self.factory.validate_providers()

        # Log validation results
        for provider_type, is_valid in validation_results.items():
            status = "✓ Valid" if is_valid else "✗ Invalid"
            logger.info("  %s: %s", provider_type, status)

        return validation_results

    def get_provider_status(self, provider_type: str) -> Dict[str, Any]:
        """Get status of specific provider"""
        if provider_type not in self._providers:
            return {"error": f"Unknown provider type: {provider_type}"}

        return self._providers[provider_type].get_info()

    def get_all_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        return {
            provider_type: provider_info.get_info()
            for provider_type, provider_info in self._providers.items()
        }

    def reset_provider(self, provider_type: str) -> bool:
        """Reset a specific provider (force recreation)"""
        if provider_type not in self._providers:
            logger.error("Unknown provider type: %s", provider_type)
            return False

        try:
            # Destroy existing instance if any
            provider_info = self._providers[provider_type]
            if provider_info.instance:
                self._destroy_provider_instance(provider_info.instance)

            # Reset provider info
            self._providers[provider_type] = ProviderInfo(provider_type)

            logger.info("Reset %s provider", provider_type)
            return True

        except (AttributeError, RuntimeError) as e:
            logger.error("Failed to reset %s provider: %s", provider_type, e)
            return False

    def reset_all_providers(self) -> bool:
        """Reset all providers"""
        success = True
        for provider_type in self._providers:
            if not self.reset_provider(provider_type):
                success = False
        return success

    def _destroy_provider_instance(self, instance):
        """Destroy a provider instance if it has cleanup methods"""
        try:
            # Check for common cleanup methods
            if hasattr(instance, "close"):
                instance.close()
            elif hasattr(instance, "cleanup"):
                instance.cleanup()
            elif hasattr(instance, "destroy"):
                instance.destroy()
        except (AttributeError, RuntimeError) as e:
            logger.warning("Error during provider cleanup: %s", e)

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of provider manager state"""
        provider_statuses = self.get_all_provider_status()

        # Count providers by status
        statuses = [str(provider_info["status"]) for provider_info in provider_statuses.values()]
        status_counts = dict(Counter(statuses))

        # Get configuration summary
        config_summary = self.config.get_summary()

        return {
            "configuration": config_summary,
            "providers": provider_statuses,
            "status_summary": status_counts,
            "total_access_count": sum(info["access_count"] for info in provider_statuses.values()),
            "validation": self.validate_configuration(),
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        health_status: Dict[str, Any] = {
            "overall_healthy": True,
            "providers": {},
            "timestamp": None,
        }

        health_status["timestamp"] = time.time()

        for provider_type in self._providers:
            provider_health = self._check_provider_health(provider_type)
            health_status["providers"][provider_type] = provider_health

            if not provider_health["healthy"]:
                health_status["overall_healthy"] = False

        return health_status

    def _check_provider_health(self, provider_type: str) -> Dict[str, Any]:
        """Check health of specific provider"""
        health_info = {"healthy": False, "status": "unknown", "error": None, "last_access": None}

        try:
            provider_info = self._providers[provider_type]
            health_info["status"] = provider_info.status.value
            health_info["last_access"] = provider_info.last_access_time

            if provider_info.status == ProviderStatus.READY:
                # Provider is ready and working
                health_info["healthy"] = True
            elif provider_info.status == ProviderStatus.NOT_INITIALIZED:
                # Provider is healthy but not yet accessed (lazy loading)
                health_info["healthy"] = True
                # Verify it can be created by testing factory validation
                validation_results = self.factory.validate_providers()
                if not validation_results.get(provider_type, False):
                    health_info["healthy"] = False
                    health_info["error"] = "Provider validation failed"
            elif provider_info.status == ProviderStatus.ERROR:
                health_info["error"] = provider_info.error_message
            elif provider_info.status == ProviderStatus.INITIALIZING:
                # Provider is currently being created, consider healthy
                health_info["healthy"] = True
            elif provider_info.status == ProviderStatus.DESTROYED:
                health_info["error"] = "Provider has been destroyed"

        except (KeyError, AttributeError) as e:
            health_info["error"] = str(e)

        return health_info

    def cleanup(self):
        """Cleanup all providers and resources"""
        logger.info("Cleaning up provider manager...")

        for provider_type, provider_info in self._providers.items():
            if provider_info.instance:
                try:
                    self._destroy_provider_instance(provider_info.instance)
                    provider_info.status = ProviderStatus.DESTROYED
                    logger.debug("Cleaned up %s provider", provider_type)
                except (AttributeError, RuntimeError) as e:
                    logger.warning("Error cleaning up %s provider: %s", provider_type, e)

        logger.info("Provider manager cleanup completed")
