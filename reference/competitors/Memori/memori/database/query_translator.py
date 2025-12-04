"""
Cross-database query parameter translator for Memori v2.0

This module provides database-agnostic parameter translation to handle
differences between SQLite, PostgreSQL, and MySQL, particularly for
boolean values and other database-specific syntax.
"""

from typing import Any

from loguru import logger


class QueryParameterTranslator:
    """
    Translates query parameters to be compatible with different database engines.

    Handles cross-database compatibility issues like:
    - Boolean values (SQLite: 0/1, PostgreSQL: TRUE/FALSE, MySQL: 0/1)
    - Date/time formats
    - Case sensitivity
    - Data type constraints
    """

    def __init__(self, database_type: str):
        """
        Initialize translator for specific database type.

        Args:
            database_type: Database engine name ('sqlite', 'postgresql', 'mysql')
        """
        self.database_type = database_type.lower()
        logger.debug(f"QueryParameterTranslator initialized for {self.database_type}")

    def translate_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Translate parameters to be compatible with the target database.

        Args:
            parameters: Dictionary of query parameters

        Returns:
            Dictionary with translated parameters
        """
        if not parameters:
            return parameters

        translated = {}

        for key, value in parameters.items():
            translated[key] = self._translate_value(value, key)

        return translated

    def _translate_value(self, value: Any, parameter_name: str = None) -> Any:
        """Translate a single parameter value based on database type."""

        # Handle boolean values
        if isinstance(value, bool):
            return self._translate_boolean(value)

        # Handle integer boolean representations (0, 1)
        if isinstance(value, int) and value in (0, 1):
            # Check if this looks like a boolean context based on parameter name
            if self._is_likely_boolean_context(value, parameter_name):
                return self._translate_boolean(bool(value))

        # Handle None values
        if value is None:
            return None

        # Handle lists/arrays
        if isinstance(value, list | tuple):
            return [self._translate_value(item) for item in value]

        # Handle dictionaries
        if isinstance(value, dict):
            return {k: self._translate_value(v, k) for k, v in value.items()}

        # Return other values unchanged
        return value

    def _translate_boolean(self, value: bool) -> bool | int:
        """
        Translate boolean values for database compatibility.

        Args:
            value: Boolean value to translate

        Returns:
            Database-appropriate boolean representation
        """
        if self.database_type == "postgresql":
            # PostgreSQL uses TRUE/FALSE
            return value  # SQLAlchemy handles the TRUE/FALSE conversion

        elif self.database_type in ("sqlite", "mysql"):
            # SQLite and MySQL use 0/1 for booleans
            return int(value)

        else:
            # Default: return as-is and let SQLAlchemy handle it
            logger.warning(
                f"Unknown database type {self.database_type}, using default boolean handling"
            )
            return value

    def _is_likely_boolean_context(
        self, value: int, parameter_name: str = None
    ) -> bool:
        """
        Heuristic to determine if an integer (0 or 1) is meant to be a boolean.

        This is used to detect integer parameters that should be treated as booleans
        for cross-database compatibility.

        Args:
            value: Integer value (should be 0 or 1)
            parameter_name: Name of the parameter (for context)

        Returns:
            True if this looks like a boolean context
        """
        # Must be 0 or 1 to be considered
        if value not in (0, 1):
            return False

        # Use parameter name patterns to identify boolean fields
        if parameter_name:
            boolean_patterns = [
                "active",
                "enabled",
                "disabled",
                "processed",
                "eligible",
                "is_",
                "has_",
                "can_",
                "should_",
                "allow_",
                "visible",
                "hidden",
                "conscious_processed",
                "processed_for_duplicates",
                "promotion_eligible",
                "is_user_context",
                "is_preference",
                "is_skill_knowledge",
                "is_current_project",
                "is_permanent_context",
            ]

            param_lower = parameter_name.lower()
            for pattern in boolean_patterns:
                if pattern in param_lower:
                    return True

        # Default to treating 0/1 as potential booleans if no parameter name context
        return True

    def translate_query_with_parameters(
        self, query: str, parameters: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """
        Translate both query and parameters for database compatibility.

        Currently focuses on parameter translation, but could be extended
        to handle query syntax differences if needed.

        Args:
            query: SQL query string
            parameters: Query parameters

        Returns:
            Tuple of (translated_query, translated_parameters)
        """
        # For now, we only translate parameters
        # Query translation could be added here if needed for other compatibility issues
        translated_params = self.translate_parameters(parameters)

        return query, translated_params

    def get_boolean_true(self) -> bool | int:
        """Get database-appropriate TRUE value."""
        return self._translate_boolean(True)

    def get_boolean_false(self) -> bool | int:
        """Get database-appropriate FALSE value."""
        return self._translate_boolean(False)


# Convenience functions for common boolean translations
def get_db_boolean(value: bool, database_type: str) -> bool | int:
    """
    Get database-appropriate boolean value.

    Args:
        value: Boolean value
        database_type: Database engine name

    Returns:
        Database-appropriate boolean representation
    """
    translator = QueryParameterTranslator(database_type)
    return translator._translate_boolean(value)


def translate_query_params(
    parameters: dict[str, Any], database_type: str
) -> dict[str, Any]:
    """
    Convenience function to translate query parameters.

    Args:
        parameters: Query parameters
        database_type: Database engine name

    Returns:
        Translated parameters
    """
    translator = QueryParameterTranslator(database_type)
    return translator.translate_parameters(parameters)
