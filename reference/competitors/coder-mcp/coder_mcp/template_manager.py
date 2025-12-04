#!/usr/bin/env python3
"""
Template Manager - High-Performance Orchestration Layer
Optimized template management using modular architecture
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import the modular template architecture
from .templates import TemplateRegistry
from .templates.best_practices_manager import BestPracticesManager
from .templates.language_detector import LanguageDetector
from .templates.next_steps_manager import NextStepsManager
from .templates.roadmap_generator import RoadmapGenerator

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    High-performance template manager using modular delegation architecture

    This class provides a clean interface while delegating complex operations
    to specialized components for optimal performance and maintainability.
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        """Initialize template manager with lazy-loaded components"""
        self.workspace_root = workspace_root or Path.cwd()

        # Core registry for template operations
        self.registry = TemplateRegistry(self.workspace_root)

        # Specialized components (lazy-loaded for performance)
        self._language_detector: Optional[LanguageDetector] = None
        self._best_practices_manager: Optional[BestPracticesManager] = None
        self._roadmap_generator: Optional[RoadmapGenerator] = None
        self._next_steps_manager: Optional[NextStepsManager] = None

        # Register generators
        self._register_generators()

    def _register_generators(self):
        """Register available generators with the registry"""
        from .templates import PythonGenerator

        self.registry.register_generator_class("python", PythonGenerator)
        logger.info(f"Registered generators for languages: {self.registry.list_languages()}")

    @property
    def language_detector(self) -> LanguageDetector:
        """Lazy-loaded language detector"""
        if self._language_detector is None:
            self._language_detector = LanguageDetector(self.workspace_root)
        return self._language_detector

    @property
    def best_practices_manager(self) -> BestPracticesManager:
        """Lazy-loaded best practices manager"""
        if self._best_practices_manager is None:
            self._best_practices_manager = BestPracticesManager(self.registry)
        return self._best_practices_manager

    @property
    def roadmap_generator(self) -> RoadmapGenerator:
        """Lazy-loaded roadmap generator"""
        if self._roadmap_generator is None:
            self._roadmap_generator = RoadmapGenerator()
        return self._roadmap_generator

    @property
    def next_steps_manager(self) -> NextStepsManager:
        """Lazy-loaded next steps manager"""
        if self._next_steps_manager is None:
            self._next_steps_manager = NextStepsManager()
        return self._next_steps_manager

    # Core delegation methods - maintain original interface

    def detect_language(self) -> str:
        """Detect the primary language of the project"""
        return self.language_detector.detect()

    def generate_code(
        self, language: str, feature_type: str, name: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate code using the template registry"""
        return self.registry.generate_code(language, feature_type, name, options)

    def validate_feature_request(self, language: str, feature_type: str) -> Dict[str, Any]:
        """Validate if a feature generation request is supported"""
        return self.registry.validate_feature_request(language, feature_type)

    async def apply_best_practices(
        self,
        language: str = "auto",
        practices: Optional[List[str]] = None,
        create_files: bool = True,
    ) -> Dict[str, Any]:
        """Apply language-specific best practices"""
        try:
            # Input validation
            if not language:
                raise ValueError("Language parameter is required")

            practices = practices or ["testing", "documentation", "error_handling", "logging"]

            result = await self.best_practices_manager.apply_best_practices(language, practices)

            if not result:
                logger.warning("Best practices application returned no results")
                return {"message": "No best practices applied"}

            return result

        except Exception as e:
            logger.error(f"Failed to apply best practices: {e}")
            return {"error": str(e)}

    async def scaffold_feature(
        self, feature_type: str, name: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate boilerplate code for a feature using the new template system"""
        options = options or {}
        language = options.get("language", self.detect_language())

        # Validate the request first
        validation = self.validate_feature_request(language, feature_type)
        if not validation["valid"]:
            return {
                "success": False,
                "error": f"Invalid feature request: {validation}",
                "files_created": [],
            }

        try:
            # Generate the code using the registry
            result = self.generate_code(language, feature_type, name, options)

            # Add next steps based on feature type
            if result.get("success"):
                result["next_steps"] = self.next_steps_manager.get_next_steps(
                    feature_type, language
                )

            return result

        except Exception as e:
            logger.error(f"Error scaffolding {feature_type}: {e}")
            return {"success": False, "error": str(e), "files_created": []}

    async def generate_improvement_roadmap(
        self,
        context: Dict[str, Any],
        focus_areas: Optional[List[str]] = None,
        time_frame: str = "short_term",
    ) -> Dict[str, Any]:
        """Generate improvement roadmap based on context"""
        try:
            # Input validation
            if not context:
                raise ValueError("Context parameter is required")
            if not time_frame:
                raise ValueError("Time frame parameter is required")

            focus_areas = focus_areas or ["quality", "performance", "security", "maintainability"]

            result = await self.roadmap_generator.generate_roadmap(context, focus_areas, time_frame)

            if not result:
                logger.warning("Roadmap generation returned no results")
                return {"message": "No roadmap generated"}

            return result

        except Exception as e:
            logger.error(f"Failed to generate improvement roadmap: {e}")
            return {"error": str(e)}

    # Information and compatibility methods

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return self.registry.list_languages()

    def get_supported_features(self, language: Optional[str] = None) -> List[str]:
        """Get list of supported feature types for a language"""
        if language:
            return self.registry.list_features(language)

        # Return all features across all languages
        all_features = set()
        for lang in self.get_supported_languages():
            all_features.update(self.registry.list_features(lang))
        return list(all_features)

    def get_supported_practices(self, language: Optional[str] = None) -> List[str]:
        """Get list of supported best practices"""
        return self.best_practices_manager.get_supported_practices(language)

    def get_registry_info(self) -> Dict[str, Any]:
        """Get information about the template registry"""
        return self.registry.get_registry_info()

    def cleanup(self):
        """Cleanup template manager resources"""
        if hasattr(self.registry, "cleanup"):
            self.registry.cleanup()
        logger.info("Template manager cleaned up")

    # Legacy compatibility properties (maintain original interface)
    @property
    def best_practices(self) -> Dict[str, List[str]]:
        """Legacy best practices mapping for backward compatibility"""
        return self.best_practices_manager.PRACTICES_CONFIG
