#!/usr/bin/env python3
"""
Configuration loader for MCP Server
Handles loading configuration from various sources
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from dotenv import load_dotenv

from .defaults import DefaultConfigProvider
from .models import (
    FeatureFlags,
    Limits,
    MCPConfiguration,
    OpenAIConfig,
    ProviderConfig,
    RedisConfig,
    ServerConfig,
    ServerMeta,
    StorageConfig,
    VectorConfig,
)

logger = logging.getLogger(__name__)


class ConfigurationSource(ABC):
    """Abstract base class for configuration sources"""

    @abstractmethod
    def load(self, env_file: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from this source"""

    @abstractmethod
    def get_priority(self) -> int:
        """Get priority (lower = higher priority)"""


class EnvironmentSource(ConfigurationSource):
    """Load configuration from environment variables"""

    def load(self, env_file: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config: Dict[str, Any] = {}

        # Load each configuration section
        config.update(self._load_redis_config())
        config.update(self._load_vector_config())
        config.update(self._load_storage_config())
        config.update(self._load_provider_config())
        config.update(self._load_openai_core_config())
        config.update(self._load_openai_performance_config())
        config.update(self._load_openai_feature_config())
        config.update(self._load_openai_cost_config())
        config.update(self._load_openai_model_config())
        config.update(self._load_ai_feature_config())

        return config

    def _load_redis_config(self) -> Dict[str, Any]:
        """Load Redis configuration from environment"""
        config: Dict[str, Any] = {}

        if os.getenv("REDIS_HOST"):
            config["REDIS_HOST"] = os.getenv("REDIS_HOST")
        if redis_port := os.getenv("REDIS_PORT"):
            config["REDIS_PORT"] = int(redis_port)
        if os.getenv("REDIS_PASSWORD"):
            config["REDIS_PASSWORD"] = os.getenv("REDIS_PASSWORD")
        if redis_max_conn := os.getenv("REDIS_MAX_CONNECTIONS"):
            config["REDIS_MAX_CONNECTIONS"] = int(redis_max_conn)

        return config

    def _load_vector_config(self) -> Dict[str, Any]:
        """Load Vector configuration from environment"""
        config: Dict[str, Any] = {}

        if os.getenv("REDIS_VECTOR_INDEX"):
            config["REDIS_VECTOR_INDEX"] = os.getenv("REDIS_VECTOR_INDEX")
        if embedding_dim := os.getenv("EMBEDDING_DIMENSION"):
            config["EMBEDDING_DIMENSION"] = int(embedding_dim)
        if os.getenv("VECTOR_PREFIX"):
            config["VECTOR_PREFIX"] = os.getenv("VECTOR_PREFIX")

        return config

    def _load_storage_config(self) -> Dict[str, Any]:
        """Load Storage configuration from environment"""
        config: Dict[str, Any] = {}

        if os.getenv("MCP_CONTEXT_DIR"):
            config["MCP_CONTEXT_DIR"] = os.getenv("MCP_CONTEXT_DIR")
        if context_ttl := os.getenv("MCP_CONTEXT_TTL"):
            config["MCP_CONTEXT_TTL"] = int(context_ttl)
        if max_file_size := os.getenv("MCP_MAX_FILE_SIZE"):
            config["MCP_MAX_FILE_SIZE"] = int(max_file_size)
        if max_files := os.getenv("MCP_MAX_FILES_TO_INDEX"):
            config["MCP_MAX_FILES_TO_INDEX"] = int(max_files)

        return config

    def _load_provider_config(self) -> Dict[str, Any]:
        """Load Provider configuration from environment"""
        config: Dict[str, Any] = {}

        if os.getenv("MCP_EMBEDDING_PROVIDER"):
            config["MCP_EMBEDDING_PROVIDER"] = os.getenv("MCP_EMBEDDING_PROVIDER")
        if os.getenv("MCP_VECTOR_STORE"):
            config["MCP_VECTOR_STORE"] = os.getenv("MCP_VECTOR_STORE")
        if os.getenv("MCP_CACHE_PROVIDER"):
            config["MCP_CACHE_PROVIDER"] = os.getenv("MCP_CACHE_PROVIDER")

        return config

    def _load_openai_core_config(self) -> Dict[str, Any]:
        """Load OpenAI core configuration from environment"""
        config: Dict[str, Any] = {}

        if os.getenv("OPENAI_API_KEY"):
            config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        if os.getenv("OPENAI_ENABLED"):
            config["OPENAI_ENABLED"] = os.getenv("OPENAI_ENABLED", "true").lower() == "true"
        if os.getenv("OPENAI_EMBEDDING_MODEL"):
            config["OPENAI_EMBEDDING_MODEL"] = os.getenv("OPENAI_EMBEDDING_MODEL")
        if embedding_dim := os.getenv("OPENAI_EMBEDDING_DIMENSION"):
            config["OPENAI_EMBEDDING_DIMENSION"] = int(embedding_dim)
        if os.getenv("OPENAI_REASONING_MODEL"):
            config["OPENAI_REASONING_MODEL"] = os.getenv("OPENAI_REASONING_MODEL")
        if os.getenv("OPENAI_CODE_MODEL"):
            config["OPENAI_CODE_MODEL"] = os.getenv("OPENAI_CODE_MODEL")
        if os.getenv("OPENAI_ANALYSIS_MODEL"):
            config["OPENAI_ANALYSIS_MODEL"] = os.getenv("OPENAI_ANALYSIS_MODEL")

        return config

    def _load_openai_performance_config(self) -> Dict[str, Any]:
        """Load OpenAI performance settings from environment"""
        config: Dict[str, Any] = {}

        if max_concurrent := os.getenv("AI_MAX_CONCURRENT_REQUESTS"):
            config["OPENAI_MAX_CONCURRENT_REQUESTS"] = int(max_concurrent)
        if timeout := os.getenv("OPENAI_REQUEST_TIMEOUT"):
            config["OPENAI_REQUEST_TIMEOUT"] = int(timeout)

        return config

    def _load_openai_feature_config(self) -> Dict[str, Any]:
        """Load OpenAI feature flags from environment"""
        config: Dict[str, Any] = {}

        if os.getenv("ENABLE_AI_CACHE"):
            config["ENABLE_AI_CACHE"] = os.getenv("ENABLE_AI_CACHE", "true").lower() == "true"
        if os.getenv("ENABLE_AI_STREAMING"):
            config["ENABLE_AI_STREAMING"] = (
                os.getenv("ENABLE_AI_STREAMING", "true").lower() == "true"
            )
        if cache_ttl := os.getenv("AI_CACHE_TTL"):
            config["AI_CACHE_TTL"] = int(cache_ttl)

        return config

    def _load_openai_cost_config(self) -> Dict[str, Any]:
        """Load OpenAI cost controls from environment"""
        config: Dict[str, Any] = {}

        if max_requests := os.getenv("AI_MAX_REQUESTS_PER_HOUR"):
            config["AI_MAX_REQUESTS_PER_HOUR"] = int(max_requests)
        if max_tokens := os.getenv("AI_MAX_TOKENS_PER_REQUEST"):
            config["AI_MAX_TOKENS_PER_REQUEST"] = int(max_tokens)

        return config

    def _load_openai_model_config(self) -> Dict[str, Any]:
        """Load OpenAI model parameters from environment"""
        config: Dict[str, Any] = {}

        if temperature := os.getenv("OPENAI_TEMPERATURE"):
            config["OPENAI_TEMPERATURE"] = float(temperature)
        if top_p := os.getenv("OPENAI_TOP_P"):
            config["OPENAI_TOP_P"] = float(top_p)

        return config

    def _load_ai_feature_config(self) -> Dict[str, Any]:
        """Load AI feature flags from environment"""
        config: Dict[str, Any] = {}

        if os.getenv("ENABLE_AI_ANALYSIS"):
            config["ENABLE_AI_ANALYSIS"] = os.getenv("ENABLE_AI_ANALYSIS", "true").lower() == "true"
        if os.getenv("ENABLE_AI_CODE_GENERATION"):
            config["ENABLE_AI_CODE_GENERATION"] = (
                os.getenv("ENABLE_AI_CODE_GENERATION", "true").lower() == "true"
            )
        if os.getenv("ENABLE_AI_DEBUGGING"):
            config["ENABLE_AI_DEBUGGING"] = (
                os.getenv("ENABLE_AI_DEBUGGING", "true").lower() == "true"
            )
        if os.getenv("ENABLE_AI_REFACTORING"):
            config["ENABLE_AI_REFACTORING"] = (
                os.getenv("ENABLE_AI_REFACTORING", "true").lower() == "true"
            )

        return config

    def get_priority(self) -> int:
        """Environment variables have highest priority"""
        return 1


class FileSource(ConfigurationSource):
    """Load configuration from .env files"""

    def load(self, env_file: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from .env file"""
        config: Dict[str, Any] = {}

        # Determine which file to load
        env_files_to_try = []

        if env_file:
            env_files_to_try.append(env_file)
        else:
            # Try multiple locations
            env_files_to_try.extend(
                [
                    Path.cwd() / ".env.mcp",
                    Path.cwd() / ".env",
                    Path.home() / ".config" / "mcp" / ".env",
                ]
            )

        # Load from first file that exists
        loaded_file = None
        for file_path in env_files_to_try:
            if file_path.exists():
                logger.info(f"Loading configuration from {file_path}")
                load_dotenv(file_path, override=False)
                loaded_file = file_path
                break

        if not loaded_file:
            logger.debug("No .env file found, using defaults only")
            return config

        # Now load the same way as EnvironmentSource
        env_source = EnvironmentSource()
        return env_source.load()

    def get_priority(self) -> int:
        """File source has medium priority"""
        return 2


class DefaultSource(ConfigurationSource):
    """Load configuration from defaults"""

    def __init__(self):
        self.defaults_provider = DefaultConfigProvider()

    def load(self, env_file: Optional[Path] = None) -> Dict[str, Any]:
        """Load default configuration"""
        return cast(Dict[str, Any], self.defaults_provider.get_defaults())

    def get_priority(self) -> int:
        """Default source has lowest priority"""
        return 3


class ConfigurationLoader:
    """Load configuration from multiple sources with priority"""

    def __init__(self):
        self.sources: List[ConfigurationSource] = [
            EnvironmentSource(),
            FileSource(),
            DefaultSource(),
        ]
        # Sort by priority (lower number = higher priority)
        self.sources.sort(key=lambda s: s.get_priority(), reverse=True)

    def load(self, env_file: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from all sources and merge"""
        merged_config: Dict[str, Any] = {}

        # Load in reverse priority order (lowest priority first)
        # This way higher priority sources override lower ones
        for source in self.sources:
            try:
                source_config = source.load(env_file)
                merged_config.update(source_config)
                logger.debug(
                    f"Loaded {len(source_config)} settings from {source.__class__.__name__}"
                )
            except Exception as e:
                logger.warning(f"Failed to load from {source.__class__.__name__}: {e}")

        return merged_config

    def load_complete_configuration(self, env_file: Optional[Path] = None) -> MCPConfiguration:
        """Load and build complete configuration object"""
        # Load raw configuration
        config_dict = self.load(env_file)

        # Build configuration object
        return self._build_config_from_dict(config_dict)

    def _build_config_from_dict(self, config_dict: Dict[str, Any]) -> MCPConfiguration:
        """Build configuration object from dictionary"""
        # Build Redis config
        redis_config = RedisConfig(
            host=config_dict.get("REDIS_HOST", "localhost"),
            port=config_dict.get("REDIS_PORT", 6379),
            password=config_dict.get("REDIS_PASSWORD"),
            max_connections=config_dict.get("REDIS_MAX_CONNECTIONS", 50),
        )

        # Build Vector config
        vector_config = VectorConfig(
            index_name=config_dict.get("REDIS_VECTOR_INDEX", "mcp_vectors"),
            dimension=config_dict.get("EMBEDDING_DIMENSION", 3072),
            prefix=config_dict.get("VECTOR_PREFIX", "mcp:doc:"),
        )

        # Build Storage config
        storage_config = StorageConfig(
            context_dir=config_dict.get("MCP_CONTEXT_DIR", ".mcp"),
            cache_ttl=config_dict.get("MCP_CONTEXT_TTL", 86400),
            max_file_size=config_dict.get("MCP_MAX_FILE_SIZE", 10 * 1024 * 1024),
            max_files_to_index=config_dict.get("MCP_MAX_FILES_TO_INDEX", 1000),
        )

        # Build OpenAI config
        openai_config = OpenAIConfig(
            api_key=config_dict.get("OPENAI_API_KEY"),
            enabled=config_dict.get("OPENAI_ENABLED", True),
            embedding_model=config_dict.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
            embedding_dimension=config_dict.get("OPENAI_EMBEDDING_DIMENSION", 3072),
            reasoning_model=config_dict.get("OPENAI_REASONING_MODEL", "o1-preview"),
            code_model=config_dict.get("OPENAI_CODE_MODEL", "gpt-4o"),
            analysis_model=config_dict.get("OPENAI_ANALYSIS_MODEL", "gpt-4o"),
            max_concurrent_requests=config_dict.get("OPENAI_MAX_CONCURRENT_REQUESTS", 10),
            request_timeout=config_dict.get("OPENAI_REQUEST_TIMEOUT", 60),
            enable_cache=config_dict.get("ENABLE_AI_CACHE", True),
            enable_streaming=config_dict.get("ENABLE_AI_STREAMING", True),
            cache_ttl=config_dict.get("AI_CACHE_TTL", 3600),
            max_requests_per_hour=config_dict.get("AI_MAX_REQUESTS_PER_HOUR", 100),
            max_tokens_per_request=config_dict.get("AI_MAX_TOKENS_PER_REQUEST", 4096),
            temperature=config_dict.get("OPENAI_TEMPERATURE", 0.2),
            top_p=config_dict.get("OPENAI_TOP_P", 0.95),
        )

        # Build Server config with nested components
        server_meta = ServerMeta(
            name=config_dict.get("MCP_SERVER_NAME", "coder-mcp-enhanced"),
            version=config_dict.get("MCP_SERVER_VERSION", "5.0.0"),
        )

        provider_config = ProviderConfig(
            embedding=config_dict.get("MCP_EMBEDDING_PROVIDER", "local"),
            vector_store=config_dict.get("MCP_VECTOR_STORE", "memory"),
            cache=config_dict.get("MCP_CACHE_PROVIDER", "memory"),
        )

        feature_flags = FeatureFlags(
            redis_enabled=True,  # Default to enabled
            openai_enabled=config_dict.get("OPENAI_API_KEY") is not None,
            local_fallback=True,
            ai_analysis_enabled=config_dict.get("ENABLE_AI_ANALYSIS", True),
            ai_code_generation_enabled=config_dict.get("ENABLE_AI_CODE_GENERATION", True),
            ai_debugging_enabled=config_dict.get("ENABLE_AI_DEBUGGING", True),
            ai_refactoring_enabled=config_dict.get("ENABLE_AI_REFACTORING", True),
        )

        limits = Limits(
            max_file_size=config_dict.get("MCP_MAX_FILE_SIZE", 10 * 1024 * 1024),
            max_files_to_index=config_dict.get("MCP_MAX_FILES_TO_INDEX", 1000),
            cache_ttl=config_dict.get("MCP_CONTEXT_TTL", 3600),
            ai_max_requests_per_hour=config_dict.get("AI_MAX_REQUESTS_PER_HOUR"),
            ai_max_tokens_per_request=config_dict.get("AI_MAX_TOKENS_PER_REQUEST"),
        )

        server_config = ServerConfig(
            server=server_meta,
            providers=provider_config,
            features=feature_flags,
            limits=limits,
            workspace_root=Path.cwd(),
        )

        # Build main configuration
        return MCPConfiguration(
            redis=redis_config,
            vector=vector_config,
            storage=storage_config,
            server=server_config,
            openai=openai_config,
            embedding_provider_type=config_dict.get("MCP_EMBEDDING_PROVIDER", "local"),
            vector_store_type=config_dict.get("MCP_VECTOR_STORE", "memory"),
            cache_provider_type=config_dict.get("MCP_CACHE_PROVIDER", "memory"),
            openai_api_key=config_dict.get("OPENAI_API_KEY"),
        )

    def add_source(self, source: ConfigurationSource):
        """Add a custom configuration source"""
        self.sources.append(source)
        self.sources.sort(key=lambda s: s.get_priority(), reverse=True)

    def remove_source(self, source_type: type):
        """Remove a configuration source by type"""
        self.sources = [s for s in self.sources if not isinstance(s, source_type)]

    def get_sources(self) -> List[ConfigurationSource]:
        """Get list of configuration sources"""
        return self.sources.copy()

    def validate_environment(self, env_file: Optional[Path] = None) -> Dict[str, Any]:
        """Validate that required environment variables are set"""
        config_dict = self.load(env_file)
        missing = []
        warnings = []

        # Check for required variables based on configuration
        if config_dict.get("MCP_EMBEDDING_PROVIDER") == "openai":
            if not config_dict.get("OPENAI_API_KEY"):
                missing.append("OPENAI_API_KEY (required for OpenAI embedding provider)")

        # Check for AI features
        ai_features = [
            config_dict.get("ENABLE_AI_ANALYSIS", True),
            config_dict.get("ENABLE_AI_CODE_GENERATION", True),
            config_dict.get("ENABLE_AI_DEBUGGING", True),
            config_dict.get("ENABLE_AI_REFACTORING", True),
        ]

        if any(ai_features) and not config_dict.get("OPENAI_API_KEY"):
            missing.append("OPENAI_API_KEY (required for AI features)")

        # Check for Redis configuration
        if (
            config_dict.get("MCP_VECTOR_STORE") == "redis"
            or config_dict.get("MCP_CACHE_PROVIDER") == "redis"
        ):
            redis_host = config_dict.get("REDIS_HOST", "localhost")
            if redis_host not in ["localhost", "127.0.0.1"] and not config_dict.get(
                "REDIS_PASSWORD"
            ):
                warnings.append("REDIS_PASSWORD (recommended for remote Redis connections)")

        return {
            "valid": len(missing) == 0,
            "missing": missing,
            "warnings": warnings,
            "loaded_count": len(config_dict),
        }

    def export_configuration(self, env_file: Optional[Path] = None) -> str:
        """Export current configuration as .env format"""
        config_dict = self.load(env_file)
        lines = ["# MCP Server Configuration", "# Generated by ConfigurationLoader", ""]

        # Group by category
        categories = {
            "Redis": lambda k: k.startswith("REDIS_"),
            "Vector": lambda k: k in ["REDIS_VECTOR_INDEX", "EMBEDDING_DIMENSION", "VECTOR_PREFIX"],
            "Storage": lambda k: k.startswith("MCP_") and any(x in k for x in ["CONTEXT", "FILE"]),
            "Server": lambda k: k.startswith("MCP_")
            and not any(x in k for x in ["EMBEDDING_PROVIDER", "VECTOR_STORE", "CACHE_PROVIDER"]),
            "Providers": lambda k: k
            in ["MCP_EMBEDDING_PROVIDER", "MCP_VECTOR_STORE", "MCP_CACHE_PROVIDER"],
            "OpenAI Core": lambda k: k.startswith("OPENAI_")
            and not any(x in k for x in ["MAX", "TIMEOUT", "TEMPERATURE", "TOP_P"]),
            "OpenAI Performance": lambda k: k
            in [
                "OPENAI_MAX_CONCURRENT_REQUESTS",
                "OPENAI_REQUEST_TIMEOUT",
                "AI_MAX_CONCURRENT_REQUESTS",
            ],
            "OpenAI Features": lambda k: k
            in ["ENABLE_AI_CACHE", "ENABLE_AI_STREAMING", "AI_CACHE_TTL"],
            "OpenAI Cost Control": lambda k: k.startswith("AI_MAX_"),
            "OpenAI Parameters": lambda k: k in ["OPENAI_TEMPERATURE", "OPENAI_TOP_P"],
            "AI Features": lambda k: k.startswith("ENABLE_AI_")
            and k
            not in [
                "ENABLE_AI_CACHE",
                "ENABLE_AI_STREAMING",
            ],
        }

        for category, filter_func in categories.items():
            category_keys = [k for k in sorted(config_dict.keys()) if filter_func(k)]
            if category_keys:
                lines.append(f"# {category}")
                for key in category_keys:
                    value = config_dict[key]
                    if value is None:
                        lines.append(f"# {key}=")
                    elif isinstance(value, bool):
                        lines.append(f"{key}={str(value).lower()}")
                    elif isinstance(value, str) and " " in value:
                        lines.append(f'{key}="{value}"')
                    else:
                        lines.append(f"{key}={value}")
                lines.append("")

        return "\n".join(lines)
