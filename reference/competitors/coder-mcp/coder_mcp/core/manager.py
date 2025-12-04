#!/usr/bin/env python3
"""
Simplified Configuration Manager for MCP Server
Uses modular config and provider components
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, cast

from ..security.exceptions import ConfigurationError
from .config import ConfigurationLoader, ConfigurationValidator, MCPConfiguration
from .providers import ProviderManager

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Simplified configuration manager using modular components"""

    def __init__(self, config: Optional[MCPConfiguration] = None, env_file: Optional[Path] = None):
        """Initialize configuration manager

        Args:
            config: Pre-built configuration object
            env_file: Path to environment file to load
        """
        # Load or use provided configuration
        if config:
            self.config = config
            logger.info("Using provided configuration")
        else:
            self.config = self._load_configuration(env_file)

        # Initialize modular components
        self.validator = ConfigurationValidator()
        self.provider_manager = ProviderManager(self.config)

        # Validate configuration
        self._validate_configuration()

        logger.info("Configuration manager initialized for %s", self.config.server.name)

    def _load_configuration(self, env_file: Optional[Path] = None) -> MCPConfiguration:
        """Load configuration using the configuration loader"""
        try:
            loader = ConfigurationLoader()
            config = loader.load_complete_configuration(env_file)
            logger.info("Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error("Failed to load configuration: %s", e)
            raise ConfigurationError(f"Configuration loading failed: {e}") from e

    def _validate_configuration(self):
        """Validate the loaded configuration"""
        try:
            is_valid = self.validator.validate(self.config)
            if not is_valid:
                validation_report = self.validator.get_validation_report()
                error_summary = "; ".join(validation_report["errors"])
                raise ConfigurationError(f"Configuration validation failed: {error_summary}")

            # Log validation warnings
            validation_report = self.validator.get_validation_report()
            if validation_report["warnings"]:
                logger.warning(
                    "Configuration warnings: %d issues found", len(validation_report["warnings"])
                )

        except ConfigurationError:
            raise
        except Exception as e:
            logger.error("Configuration validation error: %s", e)
            raise ConfigurationError(f"Configuration validation failed: {e}")

    # Provider access properties (delegated to provider manager)
    @property
    def embedding_provider(self):
        """Get embedding provider (lazy loaded)"""
        return self.provider_manager.embedding_provider

    @property
    def vector_store(self):
        """Get vector store (lazy loaded)"""
        return self.provider_manager.vector_store

    @property
    def cache_provider(self):
        """Get cache provider (lazy loaded)"""
        return self.provider_manager.cache_provider

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider

        Args:
            provider: Provider name (redis, openai, vector, etc.)

        Returns:
            Dictionary of provider configuration
        """
        return self.config.get_provider_config(provider)

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate complete configuration including providers"""
        # Validate configuration models
        config_validation = self.validator.validate(self.config)

        # Validate providers
        provider_validation = self.provider_manager.validate_configuration()

        # Check AI configuration if enabled
        ai_validation = True
        if self.config.is_ai_enabled():
            ai_validation = self.config.openai.api_key is not None
            if not ai_validation:
                logger.warning("AI features enabled but OpenAI API key is missing")

        # Combine results
        all_valid = config_validation and all(provider_validation.values()) and ai_validation

        return {
            "configuration": config_validation,
            "providers": provider_validation,
            "ai_enabled": self.config.is_ai_enabled(),
            "ai_configured": ai_validation,
            "overall": all_valid,
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive configuration and provider summary"""
        config_summary = self.config.get_summary()
        provider_summary = self.provider_manager.get_summary()
        validation_report = self.validator.get_validation_report()

        # Add AI configuration summary if enabled
        if self.config.is_ai_enabled():
            config_summary["ai_configuration"] = {
                "enabled": True,
                "models": config_summary.get("ai_models", {}),
                "limits": self.config.get_ai_limits(),
                "features": {
                    "analysis": self.config.server.features.ai_analysis_enabled,
                    "generation": self.config.server.features.ai_code_generation_enabled,
                    "debugging": self.config.server.features.ai_debugging_enabled,
                    "refactoring": self.config.server.features.ai_refactoring_enabled,
                },
            }

        return {
            "configuration": config_summary,
            "providers": provider_summary["providers"],
            "validation": {
                "valid": validation_report["valid"],
                "errors": validation_report["errors"],
                "warnings": validation_report["warnings"],
            },
            "health": self.health_check(),
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            provider_health = self.provider_manager.health_check()
            config_valid = self.validator.validate(self.config)

            # Check AI health if enabled
            ai_health = {"healthy": True, "message": "AI not enabled"}
            if self.config.is_ai_enabled():
                ai_health = {
                    "healthy": bool(self.config.openai.api_key),
                    "message": "AI configured" if self.config.openai.api_key else "Missing API key",
                    "models": {
                        "embedding": self.config.openai.embedding_model,
                        "reasoning": self.config.openai.reasoning_model,
                        "code": self.config.openai.code_model,
                    },
                }

            return {
                "overall_healthy": provider_health["overall_healthy"]
                and config_valid
                and ai_health["healthy"],
                "configuration_valid": config_valid,
                "providers": provider_health["providers"],
                "ai": ai_health,
                "timestamp": provider_health["timestamp"],
            }
        except (ConnectionError, TimeoutError, ValueError) as e:
            logger.error("Health check failed: %s", e)
            return {"overall_healthy": False, "error": str(e), "timestamp": None}
        except Exception as e:  # Catch-all for unexpected errors
            logger.error("Health check failed: %s", e)
            return {"overall_healthy": False, "error": str(e), "timestamp": None}

    def reload_configuration(self, env_file: Optional[Path] = None) -> bool:
        """Reload configuration from environment"""
        try:
            logger.info("Reloading configuration...")

            # Load new configuration
            new_config = self._load_configuration(env_file)

            # Validate new configuration
            temp_validator = ConfigurationValidator()
            if not temp_validator.validate(new_config):
                validation_report = temp_validator.get_validation_report()
                error_summary = "; ".join(validation_report["errors"])
                logger.error("New configuration is invalid: %s", error_summary)
                return False

            # Update configuration
            self.config = new_config
            self.validator = temp_validator

            # Reset providers (they will be recreated with new config)
            self.provider_manager = ProviderManager(self.config)

            logger.info("Configuration reloaded successfully")
            return True

        except (OSError, ValueError, ConfigurationError) as e:
            logger.error("Failed to reload configuration: %s", e)
            return False
        except Exception as e:  # Catch-all for unexpected errors
            logger.error("Failed to reload configuration: %s", e)
            return False

    def reset_providers(self) -> bool:
        """Reset all providers (force recreation)"""
        try:
            return self.provider_manager.reset_all_providers()
        except (OSError, ValueError, ConfigurationError) as e:
            logger.error("Failed to reset providers: %s", e)
            return False
        except Exception as e:  # Catch-all for unexpected errors
            logger.error("Failed to reset providers: %s", e)
            return False

    def get_provider_status(self, provider_type: str) -> Dict[str, Any]:
        """Get status of specific provider"""
        # Handle OpenAI provider status
        if provider_type == "openai":
            return {
                "enabled": self.config.openai.enabled,
                "configured": bool(self.config.openai.api_key),
                "models": {
                    "embedding": self.config.openai.embedding_model,
                    "reasoning": self.config.openai.reasoning_model,
                    "code": self.config.openai.code_model,
                    "analysis": self.config.openai.analysis_model,
                },
                "limits": self.config.get_ai_limits(),
            }

        return self.provider_manager.get_provider_status(provider_type)

    def get_all_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        provider_status = self.provider_manager.get_all_provider_status()

        # Add OpenAI status
        if self.config.server.features.openai_enabled:
            provider_status["openai"] = self.get_provider_status("openai")

        return provider_status

    def get_configuration_for_logging(self) -> Dict[str, Any]:
        """Get configuration summary suitable for logging (no secrets)"""
        summary = self.get_summary()

        # Remove sensitive information
        config_section = summary.get("configuration", {})
        if isinstance(config_section, dict):
            config_section = cast(Dict[str, Any], config_section)
            if "openai_api_key" in config_section:
                if config_section["openai_api_key"]:
                    config_section["openai_api_key"] = "***REDACTED***"

            # Redact OpenAI API key in provider config
            ai_config = config_section.get("ai_configuration")
            if isinstance(ai_config, dict):
                ai_config = cast(Dict[str, Any], ai_config)
                if "api_key" in ai_config:
                    ai_config["api_key"] = "***REDACTED***"

        return summary

    def export_configuration(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        config_dict = {
            "server": {
                "name": self.config.server.name,
                "version": self.config.server.version,
                "features": {
                    "redis_enabled": self.config.server.features.redis_enabled,
                    "openai_enabled": self.config.server.features.openai_enabled,
                    "local_fallback": self.config.server.features.local_fallback,
                    "ai_analysis_enabled": self.config.server.features.ai_analysis_enabled,
                    "ai_code_generation_enabled": (
                        self.config.server.features.ai_code_generation_enabled
                    ),
                    "ai_debugging_enabled": self.config.server.features.ai_debugging_enabled,
                    "ai_refactoring_enabled": self.config.server.features.ai_refactoring_enabled,
                },
            },
            "redis": {
                "host": self.config.redis.host,
                "port": self.config.redis.port,
                "max_connections": self.config.redis.max_connections,
                "socket_timeout": self.config.redis.socket_timeout,
                "socket_connect_timeout": self.config.redis.socket_connect_timeout,
            },
            "vector": {
                "index_name": self.config.vector.index_name,
                "dimension": self.config.vector.dimension,
                "distance_metric": self.config.vector.distance_metric,
                "algorithm": self.config.vector.algorithm,
                "prefix": self.config.vector.prefix,
            },
            "storage": {
                "context_dir": self.config.storage.context_dir,
                "cache_ttl": self.config.storage.cache_ttl,
                "max_file_size": self.config.storage.max_file_size,
                "max_files_to_index": self.config.storage.max_files_to_index,
            },
            "providers": {
                "embedding_provider_type": self.config.embedding_provider_type,
                "vector_store_type": self.config.vector_store_type,
                "cache_provider_type": self.config.cache_provider_type,
            },
            "openai": {
                "enabled": self.config.openai.enabled,
                "embedding_model": self.config.openai.embedding_model,
                "embedding_dimension": self.config.openai.embedding_dimension,
                "reasoning_model": self.config.openai.reasoning_model,
                "code_model": self.config.openai.code_model,
                "analysis_model": self.config.openai.analysis_model,
                "max_concurrent_requests": self.config.openai.max_concurrent_requests,
                "request_timeout": self.config.openai.request_timeout,
                "enable_cache": self.config.openai.enable_cache,
                "enable_streaming": self.config.openai.enable_streaming,
                "cache_ttl": self.config.openai.cache_ttl,
                "max_requests_per_hour": self.config.openai.max_requests_per_hour,
                "max_tokens_per_request": self.config.openai.max_tokens_per_request,
                "temperature": self.config.openai.temperature,
                "top_p": self.config.openai.top_p,
            },
        }

        # Include secrets if requested
        if include_secrets:
            if self.config.redis.password:
                redis_section = cast(Dict[str, Any], config_dict["redis"])
                redis_section["password"] = self.config.redis.password
            if self.config.openai_api_key or self.config.openai.api_key:
                api_key = self.config.openai.api_key or self.config.openai_api_key
                openai_section = cast(Dict[str, Any], config_dict["openai"])
                openai_section["api_key"] = api_key

        return config_dict

    def cleanup(self):
        """Cleanup configuration manager and providers"""
        try:
            logger.info("Cleaning up configuration manager...")
            if hasattr(self, "provider_manager"):
                self.provider_manager.cleanup()
            logger.info("Configuration manager cleanup completed")
        except Exception as e:  # Broad except is intentional for cleanup
            logger.warning("Error during configuration manager cleanup: %s", e)

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


# Convenience function for creating configuration manager
def create_configuration_manager(env_file: Optional[Path] = None) -> ConfigurationManager:
    """Create and initialize configuration manager

    Args:
        env_file: Optional path to environment file

    Returns:
        Initialized configuration manager
    """
    try:
        return ConfigurationManager(env_file=env_file)
    except Exception as e:
        logger.error("Failed to create configuration manager: %s", e)
        raise ConfigurationError(f"Configuration loading failed: {e}") from e
