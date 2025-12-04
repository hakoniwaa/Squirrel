#!/usr/bin/env python3
"""
Default configuration provider for MCP Server
Provides fallback values for configuration
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DefaultConfigProvider:
    """Provides default configuration values"""

    def __init__(self) -> None:
        self._defaults = self._build_defaults()

    def _build_defaults(self) -> Dict[str, Any]:
        """Build the default configuration dictionary"""
        return {
            # Redis configuration defaults
            "REDIS_HOST": "localhost",
            "REDIS_PORT": 6379,
            "REDIS_PASSWORD": None,
            "REDIS_MAX_CONNECTIONS": 50,
            # Vector configuration defaults
            "REDIS_VECTOR_INDEX": "mcp_vectors",
            "EMBEDDING_DIMENSION": 3072,
            "VECTOR_PREFIX": "mcp:doc:",
            # Storage configuration defaults
            "MCP_CONTEXT_DIR": ".mcp",
            "MCP_CONTEXT_TTL": 86400,  # 24 hours
            "MCP_MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
            "MCP_MAX_FILES_TO_INDEX": 1000,
            # Server configuration defaults
            "MCP_SERVER_NAME": "coder-mcp-enhanced",
            "MCP_SERVER_VERSION": "5.0.0",
            "MCP_MAX_CONCURRENT_OPS": 10,
            "MCP_REQUEST_TIMEOUT": 60,
            # Provider defaults
            "MCP_EMBEDDING_PROVIDER": "local",
            "MCP_VECTOR_STORE": "memory",
            "MCP_CACHE_PROVIDER": "memory",
            # OpenAI configuration defaults
            "OPENAI_API_KEY": None,
            "OPENAI_ENABLED": True,
            "OPENAI_EMBEDDING_MODEL": "text-embedding-3-large",
            "OPENAI_EMBEDDING_DIMENSION": 3072,
            "OPENAI_REASONING_MODEL": "o3",
            "OPENAI_CODE_MODEL": "o3",
            "OPENAI_ANALYSIS_MODEL": "o3",
            # OpenAI performance defaults
            "OPENAI_MAX_CONCURRENT_REQUESTS": 10,
            "OPENAI_REQUEST_TIMEOUT": 60,
            # OpenAI feature flags
            "ENABLE_AI_CACHE": True,
            "ENABLE_AI_STREAMING": True,
            "AI_CACHE_TTL": 3600,  # 1 hour
            # OpenAI cost controls
            "AI_MAX_REQUESTS_PER_HOUR": 100,
            "AI_MAX_TOKENS_PER_REQUEST": 4096,
            # OpenAI model parameters
            "OPENAI_TEMPERATURE": 0.2,
            "OPENAI_TOP_P": 0.95,
            # AI feature flags
            "ENABLE_AI_ANALYSIS": True,
            "ENABLE_AI_CODE_GENERATION": True,
            "ENABLE_AI_DEBUGGING": True,
            "ENABLE_AI_REFACTORING": True,
        }

    def get_defaults(self) -> Dict[str, Any]:
        """Get all default configuration values"""
        return self._defaults.copy()

    def get_redis_defaults(self) -> Dict[str, Any]:
        """Get Redis-specific defaults"""
        return {k: v for k, v in self._defaults.items() if k.startswith("REDIS_")}

    def get_vector_defaults(self) -> Dict[str, Any]:
        """Get vector configuration defaults"""
        return {
            "REDIS_VECTOR_INDEX": self._defaults["REDIS_VECTOR_INDEX"],
            "EMBEDDING_DIMENSION": self._defaults["EMBEDDING_DIMENSION"],
            "VECTOR_PREFIX": self._defaults["VECTOR_PREFIX"],
        }

    def get_storage_defaults(self) -> Dict[str, Any]:
        """Get storage configuration defaults"""
        return {
            k: v
            for k, v in self._defaults.items()
            if k.startswith("MCP_")
            and any(
                storage_key in k
                for storage_key in [
                    "CONTEXT_DIR",
                    "CONTEXT_TTL",
                    "MAX_FILE_SIZE",
                    "MAX_FILES_TO_INDEX",
                ]
            )
        }

    def get_server_defaults(self) -> Dict[str, Any]:
        """Get server configuration defaults"""
        return {
            "MCP_SERVER_NAME": self._defaults["MCP_SERVER_NAME"],
            "MCP_SERVER_VERSION": self._defaults["MCP_SERVER_VERSION"],
            "MCP_MAX_CONCURRENT_OPS": self._defaults["MCP_MAX_CONCURRENT_OPS"],
            "MCP_REQUEST_TIMEOUT": self._defaults["MCP_REQUEST_TIMEOUT"],
        }

    def get_provider_defaults(self) -> Dict[str, Any]:
        """Get provider configuration defaults"""
        return {
            "MCP_EMBEDDING_PROVIDER": self._defaults["MCP_EMBEDDING_PROVIDER"],
            "MCP_VECTOR_STORE": self._defaults["MCP_VECTOR_STORE"],
            "MCP_CACHE_PROVIDER": self._defaults["MCP_CACHE_PROVIDER"],
        }

    def get_openai_defaults(self) -> Dict[str, Any]:
        """Get OpenAI configuration defaults"""
        return {
            k: v
            for k, v in self._defaults.items()
            if k.startswith("OPENAI_") or k.startswith("AI_") or k.startswith("ENABLE_AI_")
        }

    def get_ai_feature_defaults(self) -> Dict[str, Any]:
        """Get AI feature flag defaults"""
        return {k: v for k, v in self._defaults.items() if k.startswith("ENABLE_AI_")}

    def merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge provided configuration with defaults"""
        merged = self._defaults.copy()
        merged.update(config)
        return merged

    def get_default(self, key: str, fallback: Any = None) -> Any:
        """Get a single default value"""
        return self._defaults.get(key, fallback)

    def set_default(self, key: str, value: Any) -> None:
        """Set a default value (useful for testing)"""
        self._defaults[key] = value

    def reset_defaults(self) -> None:
        """Reset defaults to original values"""
        self._defaults = self._build_defaults()

    def get_required_keys(self) -> List[str]:
        """Get list of configuration keys that are required (no default)"""
        # Currently only API keys are truly required when their features are enabled
        # pragma: allowlist secret
        return []

    def get_optional_keys(self) -> List[str]:
        """Get list of configuration keys that have defaults"""
        return list(self._defaults.keys())

    def validate_key(self, key: str) -> bool:
        """Check if a configuration key is recognized"""
        return key in self._defaults

    def get_key_description(self, key: str) -> str:
        """Get description for a configuration key"""
        descriptions = {
            # Redis
            "REDIS_HOST": "Redis server hostname",
            "REDIS_PORT": "Redis server port",
            "REDIS_PASSWORD": "Redis authentication password",  # pragma: allowlist secret
            "REDIS_MAX_CONNECTIONS": "Maximum Redis connections",
            # Vector
            "REDIS_VECTOR_INDEX": "Redis vector index name",
            "EMBEDDING_DIMENSION": "Embedding vector dimension",
            "VECTOR_PREFIX": "Redis key prefix for vectors",
            # Storage
            "MCP_CONTEXT_DIR": "Directory for context storage",
            "MCP_CONTEXT_TTL": "Context cache TTL in seconds",
            "MCP_MAX_FILE_SIZE": "Maximum file size in bytes",
            "MCP_MAX_FILES_TO_INDEX": "Maximum number of files to index",
            # Server
            "MCP_SERVER_NAME": "Server name identifier",
            "MCP_SERVER_VERSION": "Server version",
            "MCP_MAX_CONCURRENT_OPS": "Maximum concurrent operations",
            "MCP_REQUEST_TIMEOUT": "Request timeout in seconds",
            # Providers
            "MCP_EMBEDDING_PROVIDER": "Embedding provider type",
            "MCP_VECTOR_STORE": "Vector store type",
            "MCP_CACHE_PROVIDER": "Cache provider type",
            # OpenAI Core
            "OPENAI_API_KEY": "OpenAI API key",  # pragma: allowlist secret
            "OPENAI_ENABLED": "Enable OpenAI features",
            "OPENAI_EMBEDDING_MODEL": "OpenAI embedding model",
            "OPENAI_EMBEDDING_DIMENSION": "OpenAI embedding dimension",
            "OPENAI_REASONING_MODEL": "OpenAI reasoning model (o3)",
            "OPENAI_CODE_MODEL": "OpenAI code generation model",
            "OPENAI_ANALYSIS_MODEL": "OpenAI analysis model",
            # OpenAI Performance
            "OPENAI_MAX_CONCURRENT_REQUESTS": "Max concurrent OpenAI requests",
            "OPENAI_REQUEST_TIMEOUT": "OpenAI request timeout",
            # OpenAI Features
            "ENABLE_AI_CACHE": "Enable AI response caching",
            "ENABLE_AI_STREAMING": "Enable streaming AI responses",
            "AI_CACHE_TTL": "AI cache TTL in seconds",
            # OpenAI Cost Control
            "AI_MAX_REQUESTS_PER_HOUR": "Max AI requests per hour",
            "AI_MAX_TOKENS_PER_REQUEST": "Max tokens per AI request",
            # OpenAI Parameters
            "OPENAI_TEMPERATURE": "AI response temperature",
            "OPENAI_TOP_P": "AI response top-p sampling",
            # AI Features
            "ENABLE_AI_ANALYSIS": "Enable AI code analysis",
            "ENABLE_AI_CODE_GENERATION": "Enable AI code generation",
            "ENABLE_AI_DEBUGGING": "Enable AI debugging assistance",
            "ENABLE_AI_REFACTORING": "Enable AI refactoring",
        }
        return descriptions.get(key, f"Configuration for {key}")

    def export_defaults(self) -> str:
        """Export defaults as environment variable format"""
        lines = ["# MCP Server Default Configuration"]
        lines.append("# Generated from DefaultConfigProvider")
        lines.append("")

        # Group by category
        categories = {
            "Redis": lambda k: k.startswith("REDIS_"),
            "Vector": lambda k: k in ["REDIS_VECTOR_INDEX", "EMBEDDING_DIMENSION", "VECTOR_PREFIX"],
            "Storage": lambda k: k.startswith("MCP_") and any(x in k for x in ["CONTEXT", "FILE"]),
            "Server": lambda k: k.startswith("MCP_")
            and k not in ["MCP_EMBEDDING_PROVIDER", "MCP_VECTOR_STORE", "MCP_CACHE_PROVIDER"],
            "Providers": lambda k: k
            in ["MCP_EMBEDDING_PROVIDER", "MCP_VECTOR_STORE", "MCP_CACHE_PROVIDER"],
            "OpenAI Core": lambda k: k.startswith("OPENAI_")
            and not any(x in k for x in ["MAX", "TIMEOUT", "TEMPERATURE", "TOP_P"]),
            "OpenAI Performance": lambda k: k
            in ["OPENAI_MAX_CONCURRENT_REQUESTS", "OPENAI_REQUEST_TIMEOUT"],
            "OpenAI Features": lambda k: k
            in ["ENABLE_AI_CACHE", "ENABLE_AI_STREAMING", "AI_CACHE_TTL"],
            "OpenAI Cost Control": lambda k: k.startswith("AI_MAX_"),
            "OpenAI Parameters": lambda k: k in ["OPENAI_TEMPERATURE", "OPENAI_TOP_P"],
            "AI Features": lambda k: k.startswith("ENABLE_AI_")
            and k not in ["ENABLE_AI_CACHE", "ENABLE_AI_STREAMING"],
        }

        for category, filter_func in categories.items():
            category_keys = [k for k in self._defaults.keys() if filter_func(k)]
            if category_keys:
                lines.append(f"# {category}")
                for key in sorted(category_keys):
                    value = self._defaults[key]
                    desc = self.get_key_description(key)
                    lines.append(f"# {desc}")
                    if value is None:
                        lines.append(f"# {key}=")
                    elif isinstance(value, bool):
                        lines.append(f"{key}={str(value).lower()}")
                    else:
                        lines.append(f"{key}={value}")
                lines.append("")

        return "\n".join(lines)
