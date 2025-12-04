#!/usr/bin/env python3
"""
Template Registry
Central registry for managing generators, templates, and builders
"""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .generators.base import BaseGenerator
from .template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """Central registry for managing templates and generators"""

    def __init__(self, workspace_root: Path, template_dirs: Optional[List[Path]] = None):
        """
        Initialize template registry

        Args:
            workspace_root: Root directory of the workspace
            template_dirs: Additional template directories to search
        """
        self.workspace_root = workspace_root
        self.template_engine = TemplateEngine(template_dirs or [])
        self._generators: Dict[str, BaseGenerator] = {}
        self._generator_classes: Dict[str, Type[BaseGenerator]] = {}

        # Setup default template directories
        self._setup_default_template_dirs()

    def _setup_default_template_dirs(self):
        """Setup default template search directories"""
        # Add workspace template directories
        workspace_templates = self.workspace_root / "templates"
        if workspace_templates.exists():
            self.template_engine.add_template_dir(workspace_templates)

        # Add package template directories
        package_templates = Path(__file__).parent / "files"
        if package_templates.exists():
            self.template_engine.add_template_dir(package_templates)

    def register_generator_class(self, language: str, generator_class: Type[BaseGenerator]):
        """
        Register a generator class for a language

        Args:
            language: Language name (e.g., 'python', 'javascript')
            generator_class: Generator class to register
        """
        self._generator_classes[language] = generator_class
        logger.info("Registered generator class for language: %s", language)

    def get_generator(self, language: str) -> Optional[BaseGenerator]:
        """
        Get or create a generator for a language

        Args:
            language: Language name

        Returns:
            Generator instance or None if not found
        """
        # Return cached generator if available
        if language in self._generators:
            return self._generators[language]

        # Create new generator if class is registered
        if language in self._generator_classes:
            generator_class = self._generator_classes[language]
            generator = generator_class(self.template_engine, self.workspace_root)
            self._generators[language] = generator
            logger.info(f"Created generator instance for language: {language}")
            return generator

        logger.warning(f"No generator found for language: {language}")
        return None

    def list_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self._generator_classes.keys())

    def list_features(self, language: str) -> List[str]:
        """
        Get list of supported features for a language

        Args:
            language: Language name

        Returns:
            List of supported feature types
        """
        generator = self.get_generator(language)
        return generator.get_supported_features() if generator else []

    def generate_code(
        self, language: str, feature_type: str, name: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate code for a specific language and feature

        Args:
            language: Programming language
            feature_type: Type of feature to generate
            name: Name for the generated feature
            options: Additional generation options

        Returns:
            Generation result dictionary
        """
        generator = self.get_generator(language)
        if not generator:
            return {
                "success": False,
                "error": f"No generator available for language: {language}",
                "supported_languages": self.list_languages(),
            }

        return generator.generate(feature_type, name, options or {})

    def discover_generators(self, package_name: str = "coder_mcp.templates.generators"):
        """
        Auto-discover generator classes in a package

        Args:
            package_name: Python package to search for generators
        """
        try:
            # Import the package
            package = importlib.import_module(package_name)

            # Iterate through all modules in the package
            for _, module_name, _ in pkgutil.iter_modules(package.__path__, package_name + "."):
                try:
                    module = importlib.import_module(module_name)

                    # Look for generator classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)

                        # Check if it's a generator class
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseGenerator)
                            and attr is not BaseGenerator
                        ):

                            # Get language name from the generator
                            try:
                                # Create temporary instance to get language name
                                temp_generator = attr(self.template_engine, self.workspace_root)
                                language = temp_generator.get_language_name()
                                self.register_generator_class(language, attr)
                                logger.info(
                                    "Auto-discovered generator: %s for %s", attr_name, language
                                )
                            except (
                                Exception
                            ) as e:  # noqa: BLE001  # Catch-all for generator registration errors
                                logger.warning("Failed to auto-register %s: %s", attr_name, e)

                except ImportError as e:
                    logger.warning("Failed to import module %s: %s", module_name, e)

        except ImportError as e:
            logger.warning("Failed to discover generators in %s: %s", package_name, e)

    def register_template(self, name: str, content: str):
        """Register an inline template"""
        self.template_engine.register_inline_template(name, content)

    def add_template_dir(self, template_dir: Path):
        """Add a new template directory"""
        self.template_engine.add_template_dir(template_dir)

    def get_registry_info(self) -> Dict[str, Any]:
        """Get information about the registry"""
        generators_info = {}
        for language, generator in self._generators.items():
            generators_info[language] = generator.get_generator_info()

        return {
            "workspace_root": str(self.workspace_root),
            "template_dirs": [str(d) for d in self.template_engine.template_dirs],
            "supported_languages": self.list_languages(),
            "available_templates": self.template_engine.list_templates(),
            "generators": generators_info,
            "total_generator_classes": len(self._generator_classes),
            "total_active_generators": len(self._generators),
        }

    def validate_feature_request(self, language: str, feature_type: str) -> Dict[str, Any]:
        """
        Validate if a feature generation request is supported

        Args:
            language: Programming language
            feature_type: Type of feature to generate

        Returns:
            Validation result with details
        """
        result = {
            "valid": False,
            "language_supported": language in self._generator_classes,
            "feature_supported": False,
            "available_languages": self.list_languages(),
            "available_features": [],
        }

        if result["language_supported"]:
            available_features = self.list_features(language)
            result["available_features"] = available_features
            result["feature_supported"] = feature_type in available_features
            result["valid"] = result["feature_supported"]

        return result

    def get_feature_info(self, language: str, feature_type: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific feature

        Args:
            language: Programming language
            feature_type: Type of feature

        Returns:
            Feature information dictionary
        """
        generator = self.get_generator(language)
        if not generator:
            return {"error": f"No generator for language: {language}"}

        builder = generator.get_builder(feature_type)
        if not builder:
            return {"error": f"No builder for feature: {feature_type}"}

        return {
            "language": language,
            "feature_type": feature_type,
            "builder_class": builder.__class__.__name__,
            "available": True,
        }

    def cleanup(self):
        """Cleanup resources"""
        self._generators.clear()
        logger.info("Template registry cleaned up")
