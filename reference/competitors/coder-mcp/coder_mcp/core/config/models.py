#!/usr/bin/env python3
"""
Configuration models for MCP Server
Dataclasses representing different configuration sections
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    """Redis configuration"""

    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    decode_responses: bool = False
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    max_connections: int = 50

    def __post_init__(self) -> None:
        """Validate Redis configuration after initialization"""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid Redis port: {self.port}")
        if self.max_connections < 1:
            raise ValueError(f"Invalid max_connections: {self.max_connections}")
        if self.socket_timeout < 0:
            raise ValueError(f"Invalid socket_timeout: {self.socket_timeout}")

    @property
    def connection_url(self) -> str:
        """Get Redis connection URL"""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}"

    def is_local(self) -> bool:
        """Check if Redis is configured for local development"""
        return self.host in ["localhost", "127.0.0.1"] and not self.password


@dataclass
class VectorConfig:
    """Vector search configuration"""

    index_name: str = "mcp_vectors"
    dimension: int = 3072
    distance_metric: str = "COSINE"
    algorithm: str = "FLAT"
    prefix: str = "mcp:doc:"

    def __post_init__(self) -> None:
        """Validate vector configuration"""
        if self.dimension < 1:
            raise ValueError(f"Invalid vector dimension: {self.dimension}")
        if self.distance_metric not in ["COSINE", "IP", "L2"]:
            raise ValueError(f"Invalid distance metric: {self.distance_metric}")
        if self.algorithm not in ["FLAT", "HNSW"]:
            raise ValueError(f"Invalid algorithm: {self.algorithm}")
        if not self.index_name:
            raise ValueError("Index name cannot be empty")


@dataclass
class StorageConfig:
    """Storage configuration"""

    context_dir: str = ".mcp"
    cache_ttl: int = 86400  # 24 hours
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    max_files_to_index: int = 1000

    def __post_init__(self) -> None:
        """Validate storage configuration"""
        if self.cache_ttl < 0:
            raise ValueError(f"Invalid cache_ttl: {self.cache_ttl}")
        if self.max_file_size < 1:
            raise ValueError(f"Invalid max_file_size: {self.max_file_size}")
        if self.max_files_to_index < 1:
            raise ValueError(f"Invalid max_files_to_index: {self.max_files_to_index}")


@dataclass
class OpenAIConfig:
    """OpenAI configuration with enhanced AI capabilities"""

    # Core configuration
    api_key: Optional[str] = None
    enabled: bool = True

    # Embedding configuration
    embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 3072

    # AI model configuration
    reasoning_model: str = "gpt-4o"
    code_model: str = "gpt-4o"
    analysis_model: str = "gpt-4o"

    # Performance configuration
    max_concurrent_requests: int = 10
    request_timeout: int = 60

    # Feature flags
    enable_cache: bool = True
    enable_streaming: bool = True
    cache_ttl: int = 3600  # 1 hour

    # Cost control
    max_requests_per_hour: int = 100
    max_tokens_per_request: int = 4096

    # Model parameters
    temperature: float = 0.2
    top_p: float = 0.95

    def __post_init__(self) -> None:
        """Validate OpenAI configuration"""
        if self.embedding_dimension < 1:
            raise ValueError(f"Invalid embedding dimension: {self.embedding_dimension}")
        if self.max_concurrent_requests < 1 or self.max_concurrent_requests > 50:
            raise ValueError(f"Invalid max concurrent requests: {self.max_concurrent_requests}")
        if self.request_timeout < 10 or self.request_timeout > 300:
            raise ValueError(f"Invalid request timeout: {self.request_timeout}")
        if self.max_tokens_per_request < 100 or self.max_tokens_per_request > 32768:
            raise ValueError(f"Invalid max tokens per request: {self.max_tokens_per_request}")
        if self.temperature < 0.0 or self.temperature > 2.0:
            raise ValueError(f"Invalid temperature: {self.temperature}")
        if self.top_p < 0.0 or self.top_p > 1.0:
            raise ValueError(f"Invalid top_p: {self.top_p}")

        # Validate model names (allow future models)
        known_embedding_models = [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002",
        ]
        known_ai_models = [
            "gpt-4-turbo-preview",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
            "o3",  # Future model
            "o3-mini",  # Future model
        ]

        if self.embedding_model not in known_embedding_models:
            logger.warning(f"Using unknown embedding model: {self.embedding_model}")

        for model_name in [self.reasoning_model, self.code_model, self.analysis_model]:
            if model_name not in known_ai_models:
                logger.warning(f"Using unknown/future AI model: {model_name}")


@dataclass
class ServerMeta:
    """Metadata about the running MCP server."""

    name: str = "coder-mcp-server"
    version: str = "1.0.0"


@dataclass
class ProviderConfig:
    """Which concrete providers/back‑ends to use for the core subsystems."""

    embedding: str = "openai"
    vector_store: str = "redis"
    cache: str = "redis"


@dataclass
class FeatureFlags:
    """Toggle optional capabilities at runtime."""

    redis_enabled: bool = True
    openai_enabled: bool = True
    local_fallback: bool = True
    # New AI feature flags
    ai_analysis_enabled: bool = True
    ai_code_generation_enabled: bool = True
    ai_debugging_enabled: bool = True
    ai_refactoring_enabled: bool = True


@dataclass
class Limits:
    """Hard limits to protect resources."""

    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    max_files_to_index: int = 1000
    cache_ttl: int = 3600  # seconds
    # New AI-related limits (these override OpenAIConfig defaults if set)
    ai_max_requests_per_hour: Optional[int] = None
    ai_max_tokens_per_request: Optional[int] = None


@dataclass
class ServerConfig:
    """
    Top‑level server configuration expected by the test suite
    (mirrors structure used in tests/conftest.py).
    """

    server: ServerMeta = field(default_factory=ServerMeta)
    providers: ProviderConfig = field(default_factory=ProviderConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    limits: Limits = field(default_factory=Limits)
    workspace_root: Path = field(default_factory=lambda: Path.cwd())

    # --- compatibility helpers for existing code ---------------------------------

    @property
    def name(self) -> str:
        """Expose `server.name` at the first level so legacy code still works."""
        return self.server.name

    @property
    def version(self) -> str:
        """Expose `server.version` at the first level so legacy code still works."""
        return self.server.version


@dataclass
class MCPConfiguration:
    """Main MCP configuration"""

    redis: RedisConfig = field(default_factory=RedisConfig)
    vector: VectorConfig = field(default_factory=VectorConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)  # New OpenAI config

    # Provider settings
    embedding_provider_type: str = "openai"  # "openai" or "local"
    vector_store_type: str = "redis"  # "redis" or "memory"
    cache_provider_type: str = "redis"  # "redis" or "memory"

    # API keys (loaded from environment)
    openai_api_key: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate main configuration"""
        # Validate provider types
        valid_embedding_providers = ["openai", "local"]
        if self.embedding_provider_type not in valid_embedding_providers:
            raise ValueError(f"Invalid embedding provider: {self.embedding_provider_type}")

        valid_vector_stores = ["redis", "memory"]
        if self.vector_store_type not in valid_vector_stores:
            raise ValueError(f"Invalid vector store type: {self.vector_store_type}")

        valid_cache_providers = ["redis", "memory"]
        if self.cache_provider_type not in valid_cache_providers:
            raise ValueError(f"Invalid cache provider type: {self.cache_provider_type}")

        # Validate OpenAI configuration
        if self.embedding_provider_type == "openai" and not self.openai_api_key:
            logger.warning("OpenAI embedding provider selected but no API key provided")

        # Apply server limits to OpenAI config if specified
        if self.server.limits.ai_max_requests_per_hour is not None:
            self.openai.max_requests_per_hour = self.server.limits.ai_max_requests_per_hour
        if self.server.limits.ai_max_tokens_per_request is not None:
            self.openai.max_tokens_per_request = self.server.limits.ai_max_tokens_per_request

        # Sync API key
        if self.openai_api_key and not self.openai.api_key:
            self.openai.api_key = self.openai_api_key

    def get_summary(self) -> dict[str, dict[str, object]]:
        """Get configuration summary for logging/debugging"""
        return {
            "server": {
                "name": self.server.server.name,
                "version": self.server.server.version,
            },
            "providers": {
                "embedding": self.server.providers.embedding,
                "vector_store": self.server.providers.vector_store,
                "cache": self.server.providers.cache,
            },
            "features": {
                "redis_enabled": self.server.features.redis_enabled,
                "openai_enabled": self.server.features.openai_enabled,
                "local_fallback": self.server.features.local_fallback,
                "ai_analysis": self.server.features.ai_analysis_enabled,
                "ai_generation": self.server.features.ai_code_generation_enabled,
            },
            "limits": {
                "max_file_size": self.server.limits.max_file_size,
                "max_files_to_index": self.server.limits.max_files_to_index,
                "cache_ttl": self.server.limits.cache_ttl,
                "ai_requests_per_hour": self.openai.max_requests_per_hour,
                "ai_tokens_per_request": self.openai.max_tokens_per_request,
            },
            "ai_models": {
                "embedding": self.openai.embedding_model,
                "reasoning": self.openai.reasoning_model,
                "code": self.openai.code_model,
                "analysis": self.openai.analysis_model,
            },
        }

    def is_redis_required(self) -> bool:
        """Check if Redis is required for current configuration"""
        return self.vector_store_type == "redis" or self.cache_provider_type == "redis"

    def is_openai_required(self) -> bool:
        """Check if OpenAI is required for current configuration"""
        return self.embedding_provider_type == "openai" or self.is_ai_enabled()

    def is_ai_enabled(self) -> bool:
        """Check if AI features are enabled"""
        return (
            self.server.features.openai_enabled
            and self.openai.enabled
            and self.openai.api_key is not None
            and any(
                [
                    self.server.features.ai_analysis_enabled,
                    self.server.features.ai_code_generation_enabled,
                    self.server.features.ai_debugging_enabled,
                    self.server.features.ai_refactoring_enabled,
                ]
            )
        )

    def get_ai_limits(self) -> dict[str, object]:
        """Get AI-related limits and controls"""
        return {
            "max_requests_per_hour": self.openai.max_requests_per_hour,
            "max_tokens_per_request": self.openai.max_tokens_per_request,
            "max_concurrent_requests": self.openai.max_concurrent_requests,
            "cache_enabled": self.openai.enable_cache,
            "cache_ttl": self.openai.cache_ttl,
            "streaming_enabled": self.openai.enable_streaming,
        }

    def get_provider_config(self, provider: str) -> dict[str, object]:
        """Get configuration for a specific provider"""
        if provider == "redis":
            return {
                "host": self.redis.host,
                "port": self.redis.port,
                "password": self.redis.password,
                "decode_responses": self.redis.decode_responses,
                "socket_timeout": self.redis.socket_timeout,
                "socket_connect_timeout": self.redis.socket_connect_timeout,
                "retry_on_timeout": self.redis.retry_on_timeout,
                "max_connections": self.redis.max_connections,
            }
        elif provider == "openai":
            return {
                "api_key": self.openai.api_key,
                "enabled": self.openai.enabled,
                "embedding_model": self.openai.embedding_model,
                "embedding_dimension": self.openai.embedding_dimension,
                "reasoning_model": self.openai.reasoning_model,
                "code_model": self.openai.code_model,
                "analysis_model": self.openai.analysis_model,
                "max_concurrent_requests": self.openai.max_concurrent_requests,
                "request_timeout": self.openai.request_timeout,
                "enable_cache": self.openai.enable_cache,
                "enable_streaming": self.openai.enable_streaming,
                "cache_ttl": self.openai.cache_ttl,
                "max_requests_per_hour": self.openai.max_requests_per_hour,
                "max_tokens_per_request": self.openai.max_tokens_per_request,
                "temperature": self.openai.temperature,
                "top_p": self.openai.top_p,
            }
        elif provider == "vector":
            return {
                "index_name": self.vector.index_name,
                "dimension": self.vector.dimension,
                "distance_metric": self.vector.distance_metric,
                "algorithm": self.vector.algorithm,
                "prefix": self.vector.prefix,
            }
        else:
            return {}
