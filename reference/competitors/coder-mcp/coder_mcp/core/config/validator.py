#!/usr/bin/env python3
"""
Configuration validator for MCP Server
Handles complex validation logic for configuration
"""

import logging
import re
from typing import Any, Callable, Dict, List, Tuple

from .models import (
    MCPConfiguration,
    OpenAIConfig,
    RedisConfig,
    ServerConfig,
    StorageConfig,
    VectorConfig,
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Configuration validation error"""


class ConfigurationValidator:
    """Validates MCP configuration with detailed error reporting"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate(self, config: MCPConfiguration) -> bool:
        """Validate complete configuration"""
        self.errors.clear()
        self.warnings.clear()

        # Validate individual components
        self._validate_redis_config(config.redis)
        self._validate_vector_config(config.vector)
        self._validate_storage_config(config.storage)
        self._validate_server_config(config.server)
        self._validate_openai_config(config.openai)
        self._validate_provider_configuration(config)
        self._validate_ai_provider_configuration(config)
        self._validate_cross_component_consistency(config)

        # Log results
        if self.errors:
            for error in self.errors:
                logger.error("Configuration validation error: %s", error)
            return False

        if self.warnings:
            for warning in self.warnings:
                logger.warning("Configuration validation warning: %s", warning)

        logger.info("Configuration validation passed")
        return True

    def _validate_redis_config(self, config: RedisConfig):
        """Validate Redis configuration"""
        # Port validation
        if not 1 <= config.port <= 65535:
            self.errors.append(f"Invalid Redis port: {config.port}")

        # Host validation
        if not config.host or not isinstance(config.host, str):
            self.errors.append("Redis host cannot be empty")
        elif not self._is_valid_hostname(config.host):
            self.warnings.append(f"Redis host may be invalid: {config.host}")

        # Connection limits
        if config.max_connections < 1:
            self.errors.append(f"Redis max_connections must be positive: {config.max_connections}")
        elif config.max_connections > 1000:
            self.warnings.append(f"Very high Redis max_connections: {config.max_connections}")

        # Timeout validation
        if config.socket_timeout < 0:
            self.errors.append(f"Redis socket_timeout cannot be negative: {config.socket_timeout}")
        if config.socket_connect_timeout < 0:
            self.errors.append(
                f"Redis socket_connect_timeout cannot be negative: {config.socket_connect_timeout}"
            )

        # Security warnings
        if config.host not in ["localhost", "127.0.0.1"] and not config.password:
            self.warnings.append("Remote Redis connection without password is insecure")

    def _validate_vector_config(self, config: VectorConfig):
        """Validate vector configuration"""
        # Index name validation
        if not config.index_name:
            self.errors.append("Vector index name cannot be empty")
        elif not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", config.index_name):
            self.warnings.append(f"Vector index name may be invalid: {config.index_name}")

        # Dimension validation
        if config.dimension < 1:
            self.errors.append(f"Vector dimension must be positive: {config.dimension}")
        elif config.dimension > 4096:
            self.warnings.append(f"Very high vector dimension: {config.dimension}")

        # Distance metric validation
        valid_metrics = ["COSINE", "IP", "L2"]
        if config.distance_metric not in valid_metrics:
            self.errors.append(
                f"Invalid distance metric: {config.distance_metric}. Must be one of {valid_metrics}"
            )

        # Algorithm validation
        valid_algorithms = ["FLAT", "HNSW"]
        if config.algorithm not in valid_algorithms:
            self.errors.append(
                f"Invalid algorithm: {config.algorithm}. Must be one of {valid_algorithms}"
            )

        # Prefix validation
        if not config.prefix:
            self.warnings.append("Empty vector prefix may cause key collisions")

    def _validate_storage_config(self, config: StorageConfig):
        """Validate storage configuration"""
        # Context directory validation
        if not config.context_dir:
            self.errors.append("Context directory cannot be empty")

        # TTL validation
        if config.cache_ttl < 0:
            self.errors.append(f"Cache TTL cannot be negative: {config.cache_ttl}")
        elif config.cache_ttl == 0:
            self.warnings.append("Cache TTL of 0 means no caching")
        elif config.cache_ttl > 604800:  # 1 week
            self.warnings.append(f"Very long cache TTL: {config.cache_ttl} seconds")

        # File size validation
        if config.max_file_size < 1:
            self.errors.append(f"Max file size must be positive: {config.max_file_size}")
        elif config.max_file_size > 100 * 1024 * 1024:  # 100MB
            self.warnings.append(
                f"Very large max file size: {config.max_file_size / (1024 * 1024):.1f}MB"
            )

        # File count validation
        if config.max_files_to_index < 1:
            self.errors.append(f"Max files to index must be positive: {config.max_files_to_index}")
        elif config.max_files_to_index > 10000:
            self.warnings.append(f"Very high max files to index: {config.max_files_to_index}")

    def _validate_server_config(self, config: ServerConfig):
        """Validate server configuration"""
        # Name validation
        if not config.server.name:
            self.errors.append("Server name cannot be empty")

        # Version validation
        if not config.server.version:
            self.errors.append("Server version cannot be empty")
        elif not re.match(r"^\d+\.\d+\.\d+", config.server.version):
            self.warnings.append(f"Server version format may be invalid: {config.server.version}")

        # Workspace validation
        if not config.workspace_root:
            self.errors.append("Workspace root cannot be empty")
        elif not config.workspace_root.exists():
            self.errors.append(f"Workspace root does not exist: {config.workspace_root}")
        elif not config.workspace_root.is_dir():
            self.errors.append(f"Workspace root is not a directory: {config.workspace_root}")

        # Limits validation
        if config.limits.max_file_size < 1:
            self.errors.append(
                f"Server max file size must be positive: {config.limits.max_file_size}"
            )
        if config.limits.max_files_to_index < 1:
            self.errors.append(
                f"Server max files to index must be positive: {config.limits.max_files_to_index}"
            )
        if config.limits.cache_ttl < 0:
            self.errors.append(f"Server cache TTL cannot be negative: {config.limits.cache_ttl}")

    def _validate_openai_config(self, config: OpenAIConfig):
        """Validate OpenAI configuration"""
        self._validate_openai_api_key(config)
        self._validate_openai_models(config)
        self._validate_openai_dimension(config)
        self._validate_openai_performance(config)
        self._validate_openai_cost(config)
        self._validate_openai_cache(config)

    def _validate_openai_api_key(self, config: OpenAIConfig):
        if config.enabled and not config.api_key:
            self.warnings.append("OpenAI enabled but no API key provided")

    def _validate_openai_models(self, config: OpenAIConfig):
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
        if config.embedding_model not in known_embedding_models:
            self.warnings.append(f"Unknown embedding model: {config.embedding_model}")
        for model_attr in ["reasoning_model", "code_model", "analysis_model"]:
            model_name = getattr(config, model_attr)
            if model_name not in known_ai_models:
                self.warnings.append(f"Unknown/future AI model for {model_attr}: {model_name}")

    def _validate_openai_dimension(self, config: OpenAIConfig):
        if config.embedding_dimension < 1:
            self.errors.append(f"Invalid embedding dimension: {config.embedding_dimension}")
        elif config.embedding_dimension > 4096:
            self.warnings.append(f"Very high embedding dimension: {config.embedding_dimension}")

    def _validate_openai_performance(self, config: OpenAIConfig):
        if config.max_concurrent_requests < 1:
            self.errors.append(
                f"Max concurrent requests must be positive: {config.max_concurrent_requests}"
            )
        elif config.max_concurrent_requests > 50:
            self.warnings.append(
                f"Very high max concurrent requests: {config.max_concurrent_requests}"
            )
        if config.request_timeout < 10:
            self.errors.append(f"Request timeout too low: {config.request_timeout}")
        elif config.request_timeout > 300:
            self.warnings.append(f"Very high request timeout: {config.request_timeout}")
        if config.max_tokens_per_request < 100:
            self.errors.append(f"Max tokens per request too low: {config.max_tokens_per_request}")
        elif config.max_tokens_per_request > 32768:
            self.warnings.append(
                f"Very high max tokens per request: {config.max_tokens_per_request}"
            )
        if config.temperature < 0.0 or config.temperature > 2.0:
            self.errors.append(f"Invalid temperature: {config.temperature} (must be 0.0-2.0)")
        if config.top_p < 0.0 or config.top_p > 1.0:
            self.errors.append(f"Invalid top_p: {config.top_p} (must be 0.0-1.0)")

    def _validate_openai_cost(self, config: OpenAIConfig):
        if config.max_requests_per_hour == 0:
            self.warnings.append("No rate limit set for AI requests - this could be expensive")
        elif config.max_requests_per_hour > 1000:
            self.warnings.append(f"Very high AI request limit: {config.max_requests_per_hour}/hour")

    def _validate_openai_cache(self, config: OpenAIConfig):
        if config.cache_ttl < 0:
            self.errors.append(f"AI cache TTL cannot be negative: {config.cache_ttl}")
        elif config.cache_ttl > 86400:  # 24 hours
            self.warnings.append(f"Very long AI cache TTL: {config.cache_ttl} seconds")

    def _validate_provider_configuration(self, config: MCPConfiguration):
        """Validate provider configuration consistency"""
        # Embedding provider
        valid_embedding_providers = ["openai", "local"]
        if config.embedding_provider_type not in valid_embedding_providers:
            self.errors.append(
                f"Invalid embedding provider: {config.embedding_provider_type}. "
                f"Must be one of {valid_embedding_providers}"
            )

        # Vector store
        valid_vector_stores = ["redis", "memory"]
        if config.vector_store_type not in valid_vector_stores:
            self.errors.append(
                f"Invalid vector store: {config.vector_store_type}. "
                f"Must be one of {valid_vector_stores}"
            )

        # Cache provider
        valid_cache_providers = ["redis", "memory"]
        if config.cache_provider_type not in valid_cache_providers:
            self.errors.append(
                f"Invalid cache provider: {config.cache_provider_type}. "
                f"Must be one of {valid_cache_providers}"
            )

        # Check OpenAI requirements
        if config.embedding_provider_type == "openai" and not config.openai_api_key:
            self.errors.append("OpenAI embedding provider selected but no API key provided")

        # Check Redis requirements
        if config.vector_store_type == "redis" or config.cache_provider_type == "redis":
            if not config.server.features.redis_enabled:
                self.errors.append("Redis providers selected but Redis is disabled")

    def _validate_ai_provider_configuration(self, config: MCPConfiguration):
        self._check_ai_features_enabled(config)
        self._check_embedding_provider_consistency(config)
        self._check_vector_dimension_consistency(config)
        self._check_feature_flag_consistency(config)
        self._check_ai_limits_consistency(config)

    def _check_ai_features_enabled(self, config: MCPConfiguration):
        ai_features_enabled = any(
            [
                config.server.features.ai_analysis_enabled,
                config.server.features.ai_code_generation_enabled,
                config.server.features.ai_debugging_enabled,
                config.server.features.ai_refactoring_enabled,
            ]
        )
        if ai_features_enabled and not config.openai.enabled:
            self.warnings.append("AI features enabled but OpenAI is disabled")
        if ai_features_enabled and not config.openai.api_key:
            self.errors.append("AI features enabled but no OpenAI API key provided")

    def _check_embedding_provider_consistency(self, config: MCPConfiguration):
        if config.embedding_provider_type == "openai":
            if not config.openai.enabled:
                self.errors.append("OpenAI embedding provider selected but OpenAI is disabled")
            if not config.openai.api_key:
                self.errors.append("OpenAI embedding provider selected but no API key provided")

    def _check_vector_dimension_consistency(self, config: MCPConfiguration):
        if config.embedding_provider_type == "openai":
            expected_dim = config.openai.embedding_dimension
            if config.vector.dimension != expected_dim:
                self.warnings.append(
                    f"Vector dimension ({config.vector.dimension}) doesn't match "
                    f"OpenAI embedding dimension ({expected_dim})"
                )

    def _check_feature_flag_consistency(self, config: MCPConfiguration):
        if config.server.features.openai_enabled:
            if not config.openai.enabled:
                self.warnings.append("Server OpenAI feature enabled but OpenAI config is disabled")

    def _check_ai_limits_consistency(self, config: MCPConfiguration):
        if config.server.limits.ai_max_requests_per_hour is not None:
            if config.server.limits.ai_max_requests_per_hour != config.openai.max_requests_per_hour:
                self.warnings.append(
                    f"Server AI request limit ({config.server.limits.ai_max_requests_per_hour}) "
                    f"doesn't match OpenAI config ({config.openai.max_requests_per_hour})"
                )
        if config.server.limits.ai_max_tokens_per_request is not None:
            if (
                config.server.limits.ai_max_tokens_per_request
                != config.openai.max_tokens_per_request
            ):
                self.warnings.append(
                    f"Server AI token limit ({config.server.limits.ai_max_tokens_per_request}) "
                    f"doesn't match OpenAI config ({config.openai.max_tokens_per_request})"
                )

    def _validate_cross_component_consistency(self, config: MCPConfiguration):
        """Validate consistency across configuration components"""
        # Vector dimension consistency
        if config.embedding_provider_type == "openai":
            if config.vector.dimension != config.openai.embedding_dimension:
                self.errors.append(
                    f"Vector dimension ({config.vector.dimension}) must match "
                    f"OpenAI embedding dimension ({config.openai.embedding_dimension})"
                )

        # Storage limits consistency
        if config.storage.max_file_size != config.server.limits.max_file_size:
            self.warnings.append(
                f"Storage max file size ({config.storage.max_file_size}) "
                f"differs from server limit ({config.server.limits.max_file_size})"
            )

        if config.storage.max_files_to_index != config.server.limits.max_files_to_index:
            self.warnings.append(
                f"Storage max files ({config.storage.max_files_to_index}) "
                f"differs from server limit ({config.server.limits.max_files_to_index})"
            )

        # Cache TTL consistency
        if config.storage.cache_ttl != config.server.limits.cache_ttl:
            self.warnings.append(
                f"Storage cache TTL ({config.storage.cache_ttl}) "
                f"differs from server limit ({config.server.limits.cache_ttl})"
            )

        # Provider availability
        if config.vector_store_type == "redis" and not config.server.features.redis_enabled:
            self.errors.append("Redis vector store selected but Redis is disabled")

        if config.cache_provider_type == "redis" and not config.server.features.redis_enabled:
            self.errors.append("Redis cache provider selected but Redis is disabled")

        if config.embedding_provider_type == "openai" and not config.server.features.openai_enabled:
            self.errors.append("OpenAI embedding provider selected but OpenAI is disabled")

    def _is_valid_hostname(self, hostname: str) -> bool:
        """Check if hostname is valid"""
        if hostname in ["localhost", "127.0.0.1"]:
            return True

        # Basic hostname validation
        if len(hostname) > 253:
            return False

        # Check each label
        labels = hostname.split(".")
        for label in labels:
            if not label or len(label) > 63:
                return False
            if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", label):
                return False

        return True

    def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation report"""
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy(),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }

    def validate_single_component(self, component: str, config: Any) -> bool:
        """Validate a single configuration component"""
        self.errors.clear()
        self.warnings.clear()

        validators: Dict[str, Callable[[Any], None]] = {
            "redis": self._validate_redis_config,
            "vector": self._validate_vector_config,
            "storage": self._validate_storage_config,
            "server": self._validate_server_config,
            "openai": self._validate_openai_config,
        }

        if component not in validators:
            self.errors.append(f"Unknown component: {component}")
            return False

        validators[component](config)
        return len(self.errors) == 0

    def suggest_fixes(self) -> List[Tuple[str, str]]:
        """Suggest fixes for validation errors"""
        fixes = []

        for error in self.errors:
            if "port" in error and "Invalid" in error:
                fixes.append((error, "Use a port number between 1 and 65535"))
            elif "API key" in error:
                fixes.append((error, "Set the OPENAI_API_KEY environment variable"))
            elif "dimension" in error and "must match" in error:
                fixes.append((error, "Ensure vector dimension matches embedding model dimension"))
            elif "does not exist" in error:
                fixes.append((error, "Create the directory or update the path"))
            elif "Redis" in error and "disabled" in error:
                fixes.append((error, "Enable Redis in server features or use memory providers"))

        return fixes

    def validate_environment_completeness(self, env_dict: Dict[str, Any]) -> List[str]:
        """Check if all required environment variables are set"""
        missing = []

        # Required when OpenAI features are enabled
        if env_dict.get("MCP_EMBEDDING_PROVIDER") == "openai" or any(
            env_dict.get(f"ENABLE_AI_{feature}", False)
            for feature in ["ANALYSIS", "CODE_GENERATION", "DEBUGGING", "REFACTORING"]
        ):
            if not env_dict.get("OPENAI_API_KEY"):
                missing.append("OPENAI_API_KEY")

        # Required when Redis is used
        if (
            env_dict.get("MCP_VECTOR_STORE") == "redis"
            or env_dict.get("MCP_CACHE_PROVIDER") == "redis"
        ):
            # Redis host and port have defaults, but password might be needed
            redis_host = env_dict.get("REDIS_HOST", "localhost")
            if redis_host not in ["localhost", "127.0.0.1"] and not env_dict.get("REDIS_PASSWORD"):
                missing.append("REDIS_PASSWORD (recommended for remote Redis)")

        return missing
