"""
Configuration manager for Memoriai
"""

import os
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from ..utils.exceptions import ConfigurationError
from .settings import MemoriSettings


class ConfigManager:
    """Central configuration manager for Memoriai"""

    _instance: Optional["ConfigManager"] = None
    _settings: MemoriSettings | None = None

    def __new__(cls) -> "ConfigManager":
        """Singleton pattern for configuration manager"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration manager"""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._config_sources = []
            self._load_default_config()

    def _load_default_config(self) -> None:
        """Load default configuration"""
        try:
            self._settings = MemoriSettings()
            self._config_sources.append("defaults")
            logger.debug("Loaded default configuration")
        except Exception as e:
            raise ConfigurationError(f"Failed to load default configuration: {e}")

    def load_from_env(self) -> None:
        """Load configuration from environment variables"""
        try:
            self._settings = MemoriSettings.from_env()
            self._config_sources.append("environment")
            logger.info("Configuration loaded from environment variables")
        except Exception as e:
            logger.warning(f"Failed to load configuration from environment: {e}")
            raise ConfigurationError(f"Environment configuration error: {e}")

    def load_from_file(self, config_path: str | Path) -> None:
        """Load configuration from file"""
        try:
            config_path = Path(config_path)
            self._settings = MemoriSettings.from_file(config_path)
            self._config_sources.append(str(config_path))
            logger.info(f"Configuration loaded from file: {config_path}")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {config_path}")
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from file {config_path}: {e}")
            raise ConfigurationError(f"File configuration error: {e}")

    def auto_load(self) -> None:
        """Automatically load configuration from multiple sources in priority order"""
        config_locations = [
            # Environment-specific paths
            os.getenv("MEMORI_CONFIG_PATH"),
            "memori.json",
            "memori.yaml",
            "memori.yml",
            "config/memori.json",
            "config/memori.yaml",
            "config/memori.yml",
            Path.home() / ".memori" / "config.json",
            Path.home() / ".memori" / "config.yaml",
            "/etc/memori/config.json",
            "/etc/memori/config.yaml",
        ]

        # Try to load from the first available config file
        for config_path in config_locations:
            if config_path and Path(config_path).exists():
                try:
                    self.load_from_file(config_path)
                    break
                except ConfigurationError:
                    continue

        # Override with environment variables if present
        if any(key.startswith("MEMORI_") for key in os.environ):
            try:
                env_settings = MemoriSettings.from_env()
                if self._settings:
                    # Merge environment settings with existing settings
                    self._merge_settings(env_settings)
                else:
                    self._settings = env_settings

                if "environment" not in self._config_sources:
                    self._config_sources.append("environment")

                logger.info("Environment variables merged into configuration")
            except Exception as e:
                logger.warning(f"Failed to merge environment configuration: {e}")

    def _merge_settings(self, new_settings: MemoriSettings) -> None:
        """Merge new settings with existing settings"""
        if self._settings is None:
            self._settings = new_settings
            return

        # Convert to dict, merge, and recreate
        current_dict = self._settings.dict()
        new_dict = new_settings.dict()

        # Deep merge dictionaries
        merged_dict = self._deep_merge_dicts(current_dict, new_dict)
        self._settings = MemoriSettings(**merged_dict)

    def _deep_merge_dicts(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge_dicts(result[key], value)
            else:
                result[key] = value

        return result

    def save_to_file(self, config_path: str | Path, format: str = "json") -> None:
        """Save current configuration to file"""
        if self._settings is None:
            raise ConfigurationError("No configuration loaded to save")

        try:
            self._settings.to_file(config_path, format)
            logger.info(f"Configuration saved to: {config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def get_settings(self) -> MemoriSettings:
        """Get current settings"""
        if self._settings is None:
            raise ConfigurationError("Configuration not loaded")
        return self._settings

    def update_setting(self, key_path: str, value: Any) -> None:
        """Update a specific setting using dot notation (e.g., 'database.pool_size')"""
        if self._settings is None:
            raise ConfigurationError("Configuration not loaded")

        try:
            # Convert to dict for easier manipulation
            settings_dict = self._settings.dict()

            # Navigate to the nested key
            keys = key_path.split(".")
            current = settings_dict

            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set the value
            current[keys[-1]] = value

            # Recreate settings object
            self._settings = MemoriSettings(**settings_dict)
            logger.debug(f"Updated setting {key_path} = {value}")

        except Exception as e:
            logger.error(f"Failed to update setting {key_path}: {e}")
            raise ConfigurationError(f"Setting update error: {e}")

    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """Get a specific setting using dot notation"""
        if self._settings is None:
            raise ConfigurationError("Configuration not loaded")

        try:
            # Navigate through the settings
            current = self._settings.dict()
            keys = key_path.split(".")

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default

            return current

        except Exception:
            return default

    def validate_configuration(self) -> bool:
        """Validate current configuration"""
        if self._settings is None:
            return False

        try:
            # Pydantic validation happens automatically during object creation
            # Additional custom validation can be added here

            # Validate database connection if possible
            db_url = self._settings.get_database_url()
            if not db_url:
                logger.error("Database connection string is required")
                return False

            # Validate API keys if conscious ingestion is enabled
            if (
                self._settings.agents.conscious_ingest
                and not self._settings.agents.openai_api_key
            ):
                logger.warning("OpenAI API key is required for conscious ingestion")

            logger.info("Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def get_config_info(self) -> dict[str, Any]:
        """Get information about current configuration"""
        return {
            "loaded": self._settings is not None,
            "sources": self._config_sources.copy(),
            "version": self._settings.version if self._settings else None,
            "debug_mode": self._settings.debug if self._settings else False,
            "is_production": (
                self._settings.is_production() if self._settings else False
            ),
        }

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self._settings = MemoriSettings()
        self._config_sources = ["defaults"]
        logger.info("Configuration reset to defaults")

    def setup_logging(self) -> None:
        """Setup logging based on current configuration"""
        if self._settings is None:
            raise ConfigurationError("Configuration not loaded")

        try:
            # Import here to avoid circular import
            from ..utils.logging import LoggingManager

            LoggingManager.setup_logging(
                self._settings.logging, verbose=self._settings.verbose
            )

            if self._settings.verbose:
                logger.info("Verbose logging enabled through ConfigManager")
        except Exception as e:
            logger.error(f"Failed to setup logging: {e}")
            raise ConfigurationError(f"Logging setup error: {e}")

    @classmethod
    def get_instance(cls) -> "ConfigManager":
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
