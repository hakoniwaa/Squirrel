"""
Input validation and sanitization utilities for Memori
Provides security-focused validation for all database inputs
"""

import html
import json
import re
from datetime import datetime
from typing import Any

from loguru import logger

from .exceptions import ValidationError


class InputValidator:
    """Comprehensive input validation and sanitization"""

    # SQL injection patterns to detect and block
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(\b(OR|AND)\s+[\w\s]*=[\w\s]*)",
        r"(;|\|\||&&)",
        r"(\-\-|\#|/\*|\*/)",
        r"(\bxp_cmdshell\b|\bsp_executesql\b)",
        r"(\bINTO\s+OUTFILE\b|\bINTO\s+DUMPFILE\b)",
    ]

    # XSS patterns to detect and sanitize
    XSS_PATTERNS = [
        r"<\s*script[^>]*>.*?</\s*script\s*>",
        r"<\s*iframe[^>]*>.*?</\s*iframe\s*>",
        r"<\s*object[^>]*>.*?</\s*object\s*>",
        r"<\s*embed[^>]*>",
        r"javascript\s*:",
        r"on\w+\s*=",
    ]

    @classmethod
    def validate_and_sanitize_query(cls, query: str, max_length: int = 10000) -> str:
        """Validate and sanitize search query input"""
        if not isinstance(query, str | type(None)):
            raise ValidationError("Query must be a string or None")

        if query is None:
            return ""

        # Length validation
        if len(query) > max_length:
            raise ValidationError(f"Query too long (max {max_length} characters)")

        # Check for SQL injection patterns
        query_lower = query.lower()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                logger.warning(f"Potential SQL injection attempt blocked: {pattern}")
                raise ValidationError(
                    "Invalid query: contains potentially dangerous content"
                )

        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                logger.warning(f"Potential XSS attempt blocked: {pattern}")
                # Sanitize instead of blocking for XSS
                query = re.sub(pattern, "", query, flags=re.IGNORECASE)

        # HTML escape for additional safety
        sanitized_query = html.escape(query.strip())

        return sanitized_query

    @classmethod
    def validate_namespace(cls, namespace: str) -> str:
        """Validate and sanitize namespace"""
        if not isinstance(namespace, str):
            raise ValidationError("Namespace must be a string")

        # Namespace validation rules
        sanitized_namespace = namespace.strip()

        if not sanitized_namespace:
            sanitized_namespace = "default"

        # Only allow alphanumeric, underscore, hyphen
        if not re.match(r"^[a-zA-Z0-9_\-]+$", sanitized_namespace):
            raise ValidationError(
                "Namespace contains invalid characters (only alphanumeric, underscore, hyphen allowed)"
            )

        if len(sanitized_namespace) > 100:
            raise ValidationError("Namespace too long (max 100 characters)")

        return sanitized_namespace

    @classmethod
    def validate_category_filter(cls, category_filter: list[str] | None) -> list[str]:
        """Validate and sanitize category filter list"""
        if category_filter is None:
            return []

        if not isinstance(category_filter, list):
            raise ValidationError("Category filter must be a list or None")

        if len(category_filter) > 50:  # Reasonable limit
            raise ValidationError("Too many categories in filter (max 50)")

        sanitized_categories = []
        for category in category_filter:
            if not isinstance(category, str):
                continue  # Skip non-string categories

            sanitized_category = category.strip()
            if not sanitized_category:
                continue  # Skip empty categories

            # Validate category format
            if not re.match(r"^[a-zA-Z0-9_\-\s]+$", sanitized_category):
                logger.warning(f"Invalid category format: {sanitized_category}")
                continue  # Skip invalid categories

            if len(sanitized_category) > 100:
                sanitized_category = sanitized_category[:100]  # Truncate if too long

            sanitized_categories.append(sanitized_category)

        return sanitized_categories

    @classmethod
    def validate_limit(cls, limit: int | str) -> int:
        """Validate and sanitize limit parameter"""
        try:
            int_limit = int(limit)
        except (ValueError, TypeError):
            raise ValidationError("Limit must be a valid integer")

        # Enforce reasonable bounds
        if int_limit < 1:
            return 1
        elif int_limit > 1000:  # Maximum reasonable limit
            return 1000

        return int_limit

    @classmethod
    def validate_memory_id(cls, memory_id: str) -> str:
        """Validate memory ID format"""
        if not isinstance(memory_id, str):
            raise ValidationError("Memory ID must be a string")

        sanitized_id = memory_id.strip()

        if not sanitized_id:
            raise ValidationError("Memory ID cannot be empty")

        # UUID-like format validation
        if not re.match(r"^[a-fA-F0-9\-]{36}$", sanitized_id):
            # Also allow shorter alphanumeric IDs for flexibility
            if not re.match(r"^[a-zA-Z0-9_\-]+$", sanitized_id):
                raise ValidationError("Invalid memory ID format")

        if len(sanitized_id) > 100:
            raise ValidationError("Memory ID too long")

        return sanitized_id

    @classmethod
    def validate_json_field(cls, json_data: Any, field_name: str = "data") -> str:
        """Validate and sanitize JSON data"""
        if json_data is None:
            return "{}"

        try:
            if isinstance(json_data, str):
                # Validate it's proper JSON
                parsed_data = json.loads(json_data)
                # Re-serialize to ensure clean format
                clean_json = json.dumps(
                    parsed_data, ensure_ascii=True, separators=(",", ":")
                )
            else:
                # Serialize Python object to JSON
                clean_json = json.dumps(
                    json_data, ensure_ascii=True, separators=(",", ":")
                )

            # Size limit check (1MB for JSON data)
            if len(clean_json) > 1024 * 1024:
                raise ValidationError(f"{field_name} JSON too large (max 1MB)")

            return clean_json

        except (json.JSONDecodeError, TypeError) as e:
            raise ValidationError(f"Invalid JSON in {field_name}: {e}")

    @classmethod
    def validate_text_content(
        cls, content: str, field_name: str = "content", max_length: int = 100000
    ) -> str:
        """Validate and sanitize text content"""
        if not isinstance(content, str):
            raise ValidationError(f"{field_name} must be a string")

        # Length check
        if len(content) > max_length:
            raise ValidationError(
                f"{field_name} too long (max {max_length} characters)"
            )

        # XSS sanitization
        sanitized_content = content
        for pattern in cls.XSS_PATTERNS:
            sanitized_content = re.sub(
                pattern, "", sanitized_content, flags=re.IGNORECASE
            )

        # Basic HTML escaping for storage
        sanitized_content = html.escape(sanitized_content)

        return sanitized_content.strip()

    @classmethod
    def validate_timestamp(cls, timestamp: datetime | str | None) -> datetime:
        """Validate and normalize timestamp"""
        if timestamp is None:
            return datetime.now()

        if isinstance(timestamp, datetime):
            # Make timezone-naive for SQLite compatibility
            return timestamp.replace(tzinfo=None)

        if isinstance(timestamp, str):
            try:
                # Try to parse ISO format
                parsed_timestamp = datetime.fromisoformat(
                    timestamp.replace("Z", "+00:00")
                )
                return parsed_timestamp.replace(tzinfo=None)
            except ValueError:
                raise ValidationError("Invalid timestamp format (use ISO format)")

        raise ValidationError("Timestamp must be datetime object, ISO string, or None")

    @classmethod
    def validate_score(
        cls, score: float | int | str, field_name: str = "score"
    ) -> float:
        """Validate and normalize score values (0.0 to 1.0)"""
        try:
            float_score = float(score)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid number")

        # Clamp to valid range
        if float_score < 0.0:
            return 0.0
        elif float_score > 1.0:
            return 1.0

        return float_score

    @classmethod
    def validate_boolean_field(cls, value: Any, field_name: str = "field") -> bool:
        """Validate and convert boolean field"""
        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            return bool(value)

        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")

        return False  # Default to False for safety

    @classmethod
    def sanitize_sql_identifier(cls, identifier: str) -> str:
        """Sanitize SQL identifiers (table names, column names)"""
        if not isinstance(identifier, str):
            raise ValidationError("SQL identifier must be a string")

        # Remove dangerous characters and validate format
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "", identifier)

        if not sanitized or not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", sanitized):
            raise ValidationError("Invalid SQL identifier format")

        if len(sanitized) > 64:  # SQL standard limit
            raise ValidationError("SQL identifier too long")

        # Block reserved words (basic list)
        reserved_words = {
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "CREATE",
            "ALTER",
            "TABLE",
            "DATABASE",
            "INDEX",
            "VIEW",
            "TRIGGER",
            "PROCEDURE",
            "FUNCTION",
            "EXEC",
            "EXECUTE",
            "UNION",
            "WHERE",
            "FROM",
            "JOIN",
        }

        if sanitized.upper() in reserved_words:
            raise ValidationError(
                f"Cannot use reserved word as identifier: {sanitized}"
            )

        return sanitized


class DatabaseInputValidator:
    """Database-specific input validation"""

    @classmethod
    def validate_insert_params(
        cls, table: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate parameters for database insert operations"""
        sanitized_params = {}

        # Validate table name
        InputValidator.sanitize_sql_identifier(table)

        for key, value in params.items():
            # Validate column names
            sanitized_key = InputValidator.sanitize_sql_identifier(key)

            # Type-specific validation
            if key.endswith("_id"):
                if value is not None:
                    sanitized_params[sanitized_key] = InputValidator.validate_memory_id(
                        str(value)
                    )
                else:
                    sanitized_params[sanitized_key] = None
            elif key == "namespace":
                sanitized_params[sanitized_key] = InputValidator.validate_namespace(
                    str(value)
                )
            elif key.endswith("_score"):
                sanitized_params[sanitized_key] = InputValidator.validate_score(
                    value, key
                )
            elif key.endswith("_at") or key == "timestamp":
                sanitized_params[sanitized_key] = InputValidator.validate_timestamp(
                    value
                )
            elif key.endswith("_json") or key == "metadata":
                sanitized_params[sanitized_key] = InputValidator.validate_json_field(
                    value, key
                )
            elif isinstance(value, bool) or key.startswith("is_"):
                sanitized_params[sanitized_key] = InputValidator.validate_boolean_field(
                    value, key
                )
            elif isinstance(value, str):
                sanitized_params[sanitized_key] = InputValidator.validate_text_content(
                    value, key, max_length=50000
                )
            else:
                # Pass through numeric and other safe types
                sanitized_params[sanitized_key] = value

        return sanitized_params

    @classmethod
    def validate_search_params(
        cls,
        query: str,
        namespace: str,
        category_filter: list[str] | None,
        limit: int,
    ) -> dict[str, Any]:
        """Validate all search parameters together"""
        return {
            "query": InputValidator.validate_and_sanitize_query(query),
            "namespace": InputValidator.validate_namespace(namespace),
            "category_filter": InputValidator.validate_category_filter(category_filter),
            "limit": InputValidator.validate_limit(limit),
        }
