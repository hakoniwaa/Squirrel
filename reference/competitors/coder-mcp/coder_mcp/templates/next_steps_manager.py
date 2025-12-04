#!/usr/bin/env python3
"""
Next Steps Manager
Provides feature-specific next steps and recommendations
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class NextStepsManager:
    """Manages feature-specific next steps and recommendations"""

    # Next steps configuration - easily extensible and language-aware
    FEATURE_NEXT_STEPS = {
        "class": [
            "Implement the class methods with actual logic",
            "Add proper validation and error handling",
            "Write comprehensive unit tests",
            "Add documentation for public methods",
        ],
        "function": [
            "Implement the function logic",
            "Add input validation",
            "Write unit tests",
            "Add proper documentation",
        ],
        "test": [
            "Replace TODO comments with actual test logic",
            "Add test data fixtures",
            "Configure test environment",
            "Add integration tests if needed",
        ],
        "api_endpoint": [
            "Implement the actual business logic",
            "Add proper database integration",
            "Write comprehensive tests",
            "Add proper authentication and authorization",
            "Update API documentation",
        ],
        "database_model": [
            "Add proper field validations",
            "Define relationships with other models",
            "Create database migration",
            "Add model to package imports",
            "Write model tests",
        ],
        "service_class": [
            "Implement business logic methods",
            "Add proper error handling",
            "Add database/external service integration",
            "Write comprehensive tests",
            "Add logging and monitoring",
        ],
        "react_component": [
            "Implement component logic and state management",
            "Add proper prop validation",
            "Write component tests",
            "Add accessibility features",
            "Add proper styling",
        ],
        "cli_command": [
            "Implement command logic",
            "Add proper argument validation",
            "Add error handling and user feedback",
            "Write command tests",
            "Add help documentation",
        ],
    }

    # Language-specific additional steps
    LANGUAGE_SPECIFIC_STEPS = {
        "python": [
            "Add type hints to improve code clarity",
            "Consider using dataclasses or Pydantic models",
            "Add logging using the standard logging module",
        ],
        "javascript": [
            "Consider using modern ES6+ features",
            "Add proper error boundaries (React)",
            "Consider adding TypeScript for better type safety",
        ],
        "typescript": [
            "Leverage TypeScript's type system for better safety",
            "Use interface and type definitions",
            "Consider using strict mode for better type checking",
        ],
    }

    # Default next steps for unknown feature types
    DEFAULT_NEXT_STEPS = [
        "Review and customize the generated code",
        "Add proper error handling",
        "Write tests",
        "Add documentation",
    ]

    def __init__(self) -> None:
        """Initialize next steps manager"""

    def get_next_steps(self, feature_type: str, language: str = "python") -> List[str]:
        """Get next steps for a specific feature type and language

        Args:
            feature_type: Type of feature that was generated
            language: Programming language used

        Returns:
            List of recommended next steps
        """
        # Get base steps for the feature type
        base_steps = self.FEATURE_NEXT_STEPS.get(feature_type, self.DEFAULT_NEXT_STEPS.copy())

        # Add language-specific steps
        language_steps = self.LANGUAGE_SPECIFIC_STEPS.get(language, [])

        # Combine and return unique steps
        all_steps = base_steps.copy()
        for step in language_steps:
            if step not in all_steps:
                all_steps.append(step)

        return all_steps

    def get_supported_features(self) -> List[str]:
        """Get list of supported feature types

        Returns:
            List of feature type names
        """
        return list(self.FEATURE_NEXT_STEPS.keys())

    def add_feature_steps(self, feature_type: str, steps: List[str]) -> None:
        """Add next steps for a new feature type

        Args:
            feature_type: Feature type name
            steps: List of next steps
        """
        self.FEATURE_NEXT_STEPS[feature_type] = steps

    def add_language_steps(self, language: str, steps: List[str]) -> None:
        """Add language-specific next steps

        Args:
            language: Programming language
            steps: List of language-specific steps
        """
        self.LANGUAGE_SPECIFIC_STEPS[language] = steps

    def update_feature_steps(self, feature_type: str, additional_steps: List[str]) -> None:
        """Update existing feature steps with additional ones

        Args:
            feature_type: Feature type to update
            additional_steps: Additional steps to add
        """
        if feature_type in self.FEATURE_NEXT_STEPS:
            existing_steps = self.FEATURE_NEXT_STEPS[feature_type]
            for step in additional_steps:
                if step not in existing_steps:
                    existing_steps.append(step)
        else:
            self.FEATURE_NEXT_STEPS[feature_type] = additional_steps

    def get_feature_info(self, feature_type: str) -> Dict[str, Any]:
        """Get information about a specific feature type

        Args:
            feature_type: Feature type to get info for

        Returns:
            Feature information dictionary
        """
        if feature_type not in self.FEATURE_NEXT_STEPS:
            return {
                "feature_type": feature_type,
                "supported": False,
                "available_features": self.get_supported_features(),
            }

        return {
            "feature_type": feature_type,
            "supported": True,
            "next_steps_count": len(self.FEATURE_NEXT_STEPS[feature_type]),
            "next_steps": self.FEATURE_NEXT_STEPS[feature_type].copy(),
        }

    def get_manager_info(self) -> Dict[str, Any]:
        """Get information about the next steps manager

        Returns:
            Manager information dictionary
        """
        return {
            "supported_features": self.get_supported_features(),
            "supported_languages": list(self.LANGUAGE_SPECIFIC_STEPS.keys()),
            "total_feature_types": len(self.FEATURE_NEXT_STEPS),
            "total_language_variants": len(self.LANGUAGE_SPECIFIC_STEPS),
        }
