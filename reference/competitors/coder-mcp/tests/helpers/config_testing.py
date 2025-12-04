"""
Configuration testing utilities for coder-mcp tests.

This module provides pre-built configurations, validation helpers, and setup utilities
to make configuration testing faster and more consistent.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Union
from unittest.mock import Mock

import pytest

from coder_mcp.core.config import ServerConfig
from coder_mcp.core.config.models import FeatureFlags, Limits, MCPConfiguration, ProviderConfig


class ConfigBuilder:
    """Builder for creating test configurations with common patterns."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset to default configuration."""
        self._workspace_root = Path("/test")
        self._providers = self._default_providers()
        self._provider_configs = self._default_provider_configs()
        self._limits = self._default_limits()
        self._features = self._default_features()
        self._server_name = "test-mcp-server"
        self._version = "1.0.0"
        self._env_vars = {}
        return self

    def _default_providers(self) -> Dict[str, Any]:
        """Default provider selection."""
        return {"embedding": "openai", "vector_store": "redis", "cache": "redis"}

    def _default_provider_configs(self) -> Dict[str, Any]:
        """Default provider detailed configurations."""
        return {
            "openai": {
                "api_key": "test-api-key",
                "model": "gpt-4",
                "base_url": "https://api.openai.com/v1",
            },
            "redis": {"host": "localhost", "port": 6379, "db": 0, "password": None},
        }

    def _default_limits(self) -> Dict[str, Any]:
        """Default limits configuration."""
        return {
            "max_file_size": 1048576,  # 1MB
            "max_files_to_index": 1000,
            "cache_ttl": 3600,
            "ai_max_requests_per_hour": None,
            "ai_max_tokens_per_request": None,
        }

    def _default_features(self) -> Dict[str, Any]:
        """Default features configuration."""
        return {
            "redis_enabled": True,
            "openai_enabled": True,
            "local_fallback": True,
            "ai_analysis_enabled": True,
            "ai_code_generation_enabled": True,
            "ai_debugging_enabled": True,
            "ai_refactoring_enabled": True,
        }

    def with_workspace(self, workspace_root: Union[str, Path]):
        """Set workspace root."""
        self._workspace_root = Path(workspace_root)
        return self

    def with_redis_disabled(self):
        """Disable Redis."""
        self._features["redis_enabled"] = False
        self._providers["vector_store"] = "local"
        self._providers["cache"] = "local"
        return self

    def with_openai_disabled(self):
        """Disable OpenAI."""
        self._features["openai_enabled"] = False
        return self

    def with_local_only(self):
        """Configure for local-only operation."""
        return self.with_redis_disabled().with_openai_disabled()

    def with_debug_mode(self):
        """Enable debug mode (enables all AI features)."""
        self._features["ai_analysis_enabled"] = True
        self._features["ai_code_generation_enabled"] = True
        self._features["ai_debugging_enabled"] = True
        self._features["ai_refactoring_enabled"] = True
        return self

    def with_performance_monitoring(self):
        """Enable performance monitoring (via AI analysis)."""
        self._features["ai_analysis_enabled"] = True
        return self

    def with_custom_limits(self, **limits):
        """Set custom limits."""
        self._limits.update(limits)
        return self

    def with_custom_provider(self, provider_name: str, config: Dict[str, Any]):
        """Add custom provider configuration."""
        self._provider_configs[provider_name] = config
        return self

    def with_env_vars(self, **env_vars):
        """Set environment variables for this config."""
        self._env_vars.update(env_vars)
        return self

    def build_server_config(self) -> ServerConfig:
        """Build ServerConfig object."""
        return ServerConfig(
            workspace_root=self._workspace_root,
            providers=ProviderConfig(**self._providers),
            limits=Limits(**self._limits),
            features=FeatureFlags(**self._features),
        )

    def build_mcp_config(self) -> MCPConfiguration:
        """Build MCPConfiguration object."""
        # Build ServerConfig first
        server_config = self.build_server_config()

        return MCPConfiguration(server=server_config, **self._provider_configs)

    def build_dict(self) -> Dict[str, Any]:
        """Build configuration as dictionary."""
        return {
            "server": {"name": self._server_name, "version": self._version},
            "workspace_root": str(self._workspace_root),
            "providers": self._providers,
            "limits": self._limits,
            "features": self._features,
            "provider_configs": self._provider_configs,
        }


class ConfigScenarios:
    """Pre-built configuration scenarios for common test cases."""

    @staticmethod
    def minimal_config() -> ServerConfig:
        """Minimal configuration for basic testing."""
        return ConfigBuilder().with_local_only().build_server_config()

    @staticmethod
    def full_featured_config() -> ServerConfig:
        """Full-featured configuration with all providers enabled."""
        return ConfigBuilder().with_debug_mode().with_performance_monitoring().build_server_config()

    @staticmethod
    def redis_only_config() -> ServerConfig:
        """Configuration with only Redis enabled."""
        return ConfigBuilder().with_openai_disabled().build_server_config()

    @staticmethod
    def openai_only_config() -> ServerConfig:
        """Configuration with only OpenAI enabled."""
        return ConfigBuilder().with_redis_disabled().build_server_config()

    @staticmethod
    def high_performance_config() -> ServerConfig:
        """Configuration optimized for performance."""
        return (
            ConfigBuilder()
            .with_custom_limits(
                max_files_to_index=10000, cache_ttl=7200, ai_max_requests_per_hour=1000
            )
            .with_performance_monitoring()
            .build_server_config()
        )

    @staticmethod
    def development_config(workspace: Path) -> ServerConfig:
        """Configuration for development/testing."""
        return (
            ConfigBuilder()
            .with_workspace(workspace)
            .with_debug_mode()
            .with_custom_limits(max_file_size=10485760)  # 10MB for dev
            .build_server_config()
        )

    @staticmethod
    def secure_config() -> ServerConfig:
        """Configuration with security-focused settings."""
        return (
            ConfigBuilder()
            .with_custom_limits(
                max_file_size=524288, max_files_to_index=100, ai_max_requests_per_hour=50  # 512KB
            )
            .build_server_config()
        )


class ConfigValidator:
    """Validation utilities for configuration testing."""

    @staticmethod
    def validate_config_structure(config: Dict[str, Any]) -> List[str]:
        """Validate configuration structure and return any errors."""
        errors = []

        # Check required sections
        required_sections = ["providers", "limits", "features"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")

        # Validate providers
        if "providers" in config:
            providers = config["providers"]
            if "embedding" not in providers:
                errors.append("Missing embedding provider")
            if "vector_store" not in providers:
                errors.append("Missing vector_store provider")

        # Validate limits
        if "limits" in config:
            limits = config["limits"]
            required_limits = ["max_file_size", "max_files_to_index", "cache_ttl"]
            for limit in required_limits:
                if limit not in limits:
                    errors.append(f"Missing limit: {limit}")
                elif not isinstance(limits[limit], (int, float)):
                    errors.append(f"Limit {limit} must be numeric")

        return errors

    @staticmethod
    def validate_provider_config(provider_name: str, config: Dict[str, Any]) -> List[str]:
        """Validate specific provider configuration."""
        errors = []

        if provider_name == "openai":
            if "api_key" not in config:
                errors.append("OpenAI provider missing api_key")
            if "model" not in config:
                errors.append("OpenAI provider missing model")

        elif provider_name == "redis":
            if "host" not in config:
                errors.append("Redis provider missing host")
            if "port" not in config:
                errors.append("Redis provider missing port")
            elif not isinstance(config["port"], int):
                errors.append("Redis port must be integer")

        return errors

    @staticmethod
    def assert_config_valid(config: Union[Dict[str, Any], ServerConfig]):
        """Assert configuration is valid."""
        if isinstance(config, ServerConfig):
            # ServerConfig should be valid by construction
            assert config.workspace_root is not None
            assert config.providers is not None
            assert config.limits is not None
            assert config.features is not None
        else:
            errors = ConfigValidator.validate_config_structure(config)
            assert not errors, f"Configuration validation errors: {errors}"


class ConfigEnvironment:
    """Manage environment variables for configuration testing."""

    def __init__(self):
        self.original_env = {}
        self.temp_files = []

    def set_env_var(self, key: str, value: str):
        """Set environment variable, saving original value."""
        if key not in self.original_env:
            self.original_env[key] = os.environ.get(key)
        os.environ[key] = value

    def set_openai_env(self, api_key: str = "test-key", model: str = "gpt-4"):
        """Set OpenAI environment variables."""
        self.set_env_var("OPENAI_API_KEY", api_key)
        self.set_env_var("OPENAI_MODEL", model)

    def set_redis_env(self, host: str = "localhost", port: int = 6379, password: str = None):
        """Set Redis environment variables."""
        self.set_env_var("REDIS_HOST", host)
        self.set_env_var("REDIS_PORT", str(port))
        if password:
            self.set_env_var("REDIS_PASSWORD", password)

    def create_temp_config_file(self, config: Dict[str, Any]) -> Path:
        """Create temporary configuration file."""

        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)

        json.dump(config, temp_file, indent=2)
        temp_file.close()

        temp_path = Path(temp_file.name)
        self.temp_files.append(temp_path)
        return temp_path

    def cleanup(self):
        """Restore original environment and clean up temp files."""
        # Restore environment variables
        for key, original_value in self.original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

        # Clean up temporary files
        for temp_file in self.temp_files:
            if temp_file.exists():
                temp_file.unlink()

        self.original_env.clear()
        self.temp_files.clear()


class ConfigMocker:
    """Mock configuration components for testing."""

    @staticmethod
    def mock_config_loader(config_data: Dict[str, Any] = None):
        """Mock configuration loader."""
        config_data = config_data or ConfigBuilder().build_dict()

        mock_loader = Mock()
        mock_loader.load_config.return_value = config_data
        mock_loader.validate_config.return_value = True
        mock_loader.get_config_path.return_value = Path("/test/config.json")

        return mock_loader

    @staticmethod
    def mock_config_validator(is_valid: bool = True, errors: List[str] = None):
        """Mock configuration validator."""
        mock_validator = Mock()
        mock_validator.validate.return_value = is_valid
        mock_validator.get_errors.return_value = errors or []
        mock_validator.get_warnings.return_value = []

        return mock_validator

    @staticmethod
    def mock_provider_factory(providers: Dict[str, Any] = None):
        """Mock provider factory."""
        providers = providers or {"redis": Mock(), "openai": Mock()}

        mock_factory = Mock()
        mock_factory.create_provider.side_effect = lambda name: providers.get(name)
        mock_factory.get_available_providers.return_value = list(providers.keys())

        return mock_factory


class ConfigTestFixtures:
    """Pre-configured test fixtures for common scenarios."""

    @staticmethod
    def workspace_fixture(tmp_path: Path) -> Path:
        """Create a test workspace with basic structure."""
        workspace = tmp_path / "test_workspace"
        workspace.mkdir()

        # Create basic project structure
        (workspace / "src").mkdir()
        (workspace / "tests").mkdir()
        (workspace / ".mcp").mkdir()

        # Create sample files
        (workspace / "README.md").write_text("# Test Project")
        (workspace / "src" / "__init__.py").write_text("")
        (workspace / "src" / "main.py").write_text("print('Hello, World!')")

        return workspace

    @staticmethod
    def config_file_fixture(tmp_path: Path, config: Dict[str, Any] = None) -> Path:
        """Create a temporary configuration file."""

        config = config or ConfigBuilder().build_dict()
        config_file = tmp_path / "config.json"

        config_file.write_text(json.dumps(config, indent=2))
        return config_file


# Pytest fixtures


@pytest.fixture
def config_builder():
    """Provide config builder instance."""
    return ConfigBuilder()


@pytest.fixture
def config_environment():
    """Provide config environment manager with automatic cleanup."""
    env = ConfigEnvironment()
    yield env
    env.cleanup()


@pytest.fixture
def minimal_config():
    """Provide minimal configuration."""
    return ConfigScenarios.minimal_config()


@pytest.fixture
def full_config():
    """Provide full-featured configuration."""
    return ConfigScenarios.full_featured_config()


@pytest.fixture
def test_workspace(tmp_path):
    """Provide test workspace with basic structure."""
    return ConfigTestFixtures.workspace_fixture(tmp_path)


@pytest.fixture
def config_file(tmp_path):
    """Provide temporary config file."""
    return ConfigTestFixtures.config_file_fixture(tmp_path)


# Convenience functions
def create_test_config(**overrides) -> ServerConfig:
    """Quick configuration creation with overrides."""
    builder = ConfigBuilder()

    for key, value in overrides.items():
        if key == "workspace":
            builder.with_workspace(value)
        elif key == "redis_disabled":
            if value:
                builder.with_redis_disabled()
        elif key == "openai_disabled":
            if value:
                builder.with_openai_disabled()
        elif key == "debug":
            if value:
                builder.with_debug_mode()

    return builder.build_server_config()


def mock_config_manager(config: ServerConfig = None):
    """Create a mock configuration manager."""
    config = config or ConfigScenarios.minimal_config()

    mock_manager = Mock()
    mock_manager.config = config
    mock_manager.get_config.return_value = config
    mock_manager.is_valid.return_value = True
    mock_manager.get_errors.return_value = []
    mock_manager.health_check.return_value = {"status": "healthy"}

    return mock_manager
