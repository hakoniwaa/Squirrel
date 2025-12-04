#!/usr/bin/env python3
"""
Best Practices Manager
Handles application of language-specific best practices
"""

import inspect
import logging
from typing import Any, Dict, List, Optional

from .registry import TemplateRegistry

logger = logging.getLogger(__name__)


class BestPracticesManager:
    """Manages application of language-specific best practices"""

    PRACTICE_METHOD_MAP = {
        "testing": "setup_testing_framework",
        # Add more mappings as needed
    }

    # Best practices configuration - easily extensible
    PRACTICES_CONFIG = {
        "python": [
            "testing",
            "documentation",
            "error_handling",
            "logging",
            "type_hints",
            "linting",
        ],
        "javascript": ["testing", "documentation", "error_handling", "logging", "linting"],
        "typescript": ["testing", "documentation", "error_handling", "type_hints", "linting"],
    }

    # Practice-specific recommendations
    PRACTICE_RECOMMENDATIONS = {
        "testing": "Write tests for all public functions",
        "linting": "Run linters in CI/CD pipeline",
        "project_structure": "Follow standard project structure conventions",
        "documentation": "Document all public APIs with comprehensive docstrings",
        "error_handling": "Use custom exceptions for domain-specific errors",
        "logging": "Use structured logging (JSON format) for production",
        "type_hints": "Add type hints to all function signatures",
    }

    def __init__(self, registry: TemplateRegistry):
        """Initialize best practices manager

        Args:
            registry: Template registry for generator access
        """
        self.registry = registry

    async def apply_practices(
        self, language: str, practices: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Apply best practices for a specific language

        Args:
            language: Programming language
            practices: List of practices to apply (None for defaults)

        Returns:
            Results of applying best practices
        """
        # Get default practices if not specified
        if practices is None:
            practices = self.get_default_practices(language)

        # Get generator for language
        generator = self.registry.get_generator(language)
        if not generator:
            return self._create_error_result(language)

        # Initialize results
        applied_practices: List[str] = []
        files_created: List[str] = []
        recommendations: List[str] = []

        results: Dict[str, Any] = {
            "success": True,
            "applied": applied_practices,
            "files_created": files_created,
            "recommendations": recommendations,
            "language": language,
        }

        try:
            # Apply each practice
            for practice in practices:
                practice_result = await self._apply_single_practice(generator, practice, language)

                if practice_result["success"]:
                    applied_practices.append(practice)
                    files_created.extend(practice_result.get("files_created", []))

                    # Add practice-specific recommendation
                    recommendation = self.PRACTICE_RECOMMENDATIONS.get(practice)
                    if recommendation:
                        recommendations.append(recommendation)

        except (IOError, ValueError) as e:
            logger.error("Error applying best practices for %s: %s", language, e)
            results["success"] = False
            results["error"] = str(e)

        return results

    @staticmethod
    async def _apply_single_practice(generator, practice: str, language: str) -> Dict[str, Any]:
        """Apply a single best practice"""
        method_name = BestPracticesManager.PRACTICE_METHOD_MAP.get(
            practice, f"setup_{practice.replace('-', '_')}"
        )
        if hasattr(generator, method_name):
            try:
                method = getattr(generator, method_name)

                if inspect.iscoroutinefunction(method):
                    setup_result = await method()
                else:
                    setup_result = method()
                if isinstance(setup_result, dict):
                    return {
                        "success": setup_result.get("success", True),
                        "files_created": setup_result.get("files_created", []),
                    }
                else:
                    return {"success": True, "files_created": []}
            except (IOError, ValueError) as e:
                logger.warning("Failed to apply %s for %s: %s", practice, language, e)
                return {"success": False, "error": str(e)}
        return {"success": True, "files_created": []}

    def get_default_practices(self, language: str) -> List[str]:
        """Get default practices for a language

        Args:
            language: Programming language

        Returns:
            List of default practices
        """
        return self.PRACTICES_CONFIG.get(language, ["testing", "documentation", "error_handling"])

    def get_supported_practices(self, language: Optional[str] = None) -> List[str]:
        """Get supported practices for a language or all practices

        Args:
            language: Programming language (optional)

        Returns:
            List of supported practices
        """
        if language and language in self.PRACTICES_CONFIG:
            return self.PRACTICES_CONFIG[language].copy()

        # Return all unique practices across languages
        all_practices = set()
        for practices in self.PRACTICES_CONFIG.values():
            all_practices.update(practices)

        return list(all_practices)

    def is_practice_supported(self, language: str, practice: str) -> bool:
        """Check if a practice is supported for a language

        Args:
            language: Programming language
            practice: Practice to check

        Returns:
            True if supported, False otherwise
        """
        return practice in self.get_default_practices(language)

    def add_practice_config(self, language: str, practices: List[str]):
        """Add practice configuration for a new language

        Args:
            language: Programming language
            practices: List of supported practices
        """
        self.PRACTICES_CONFIG[language] = practices

    def _create_error_result(self, language: str) -> Dict[str, Any]:
        """Create error result for unsupported language

        Args:
            language: Programming language

        Returns:
            Error result dictionary
        """
        return {
            "success": False,
            "error": f"Unsupported language: {language}",
            "applied": [],
            "files_created": [],
            "available_languages": self.registry.list_languages(),
        }

    async def apply_best_practices(
        self, language: str, practices: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Apply language-specific best practices"""
        # This is an alias for apply_practices to maintain compatibility
        return await self.apply_practices(language, practices)
