#!/usr/bin/env python3
"""
Input Validation and Security Functions
Extracted from the original server for modularity
"""

import logging
import re
from functools import wraps
from typing import Any, Dict, Optional

from .exceptions import ResourceLimitError, SecurityError, ValidationError

logger = logging.getLogger(__name__)


def validate_string_input(
    value: Any, name: str, max_length: int = 50000, allow_empty: bool = False
) -> str:
    """Validate string input with length and type checks"""
    if not isinstance(value, str):
        raise ValidationError(
            f"{name} must be a string",
            context={"value_type": type(value).__name__, "parameter": name},
        )

    if not allow_empty and not value.strip():
        raise ValidationError(f"{name} cannot be empty", context={"parameter": name})

    if len(value) > max_length:
        raise ValidationError(
            f"{name} too long (max: {max_length} characters)",
            context={"length": len(value), "max_length": max_length, "parameter": name},
        )

    return value.strip()


def validate_dict_input(value: Any, name: str) -> Dict[str, Any]:
    """Validate dictionary input"""
    if not isinstance(value, dict):
        raise ValidationError(
            f"{name} must be a dictionary",
            context={"value_type": type(value).__name__, "parameter": name},
        )
    return value


def validate_regex_pattern(pattern: str) -> re.Pattern:
    """Validate and compile regex pattern safely"""
    if not isinstance(pattern, str):
        raise ValidationError(
            "Pattern must be a string", context={"pattern_type": type(pattern).__name__}
        )

    if len(pattern) > 1000:
        raise ValidationError(
            "Pattern too long", context={"pattern_length": len(pattern), "max_length": 1000}
        )

    # Only check for the most obvious catastrophic backtracking patterns
    # We're being conservative to avoid blocking valid patterns
    extremely_dangerous_patterns = [
        r"\(\w+\)\*\w*\(\w+\)\*",  # Multiple nested quantifiers - very specific
        r"\(\w+\)\+\w*\(\w+\)\+",  # Multiple nested quantifiers with + - very specific
    ]

    for dangerous in extremely_dangerous_patterns:
        try:
            if re.search(dangerous, pattern):
                raise SecurityError(
                    "Potentially dangerous regex pattern detected",
                    context={"pattern": pattern[:100], "dangerous_pattern": dangerous},
                )
        except re.error:
            # If our danger detection pattern itself fails, just skip it
            continue

    try:
        compiled = re.compile(pattern)
        # Test with empty string to catch some issues early
        compiled.search("")
        return compiled
    except re.error as e:
        raise ValidationError(
            f"Invalid regex pattern: {str(e)}",
            context={"pattern": pattern[:100], "original_error": str(e)},
        )


def sanitize_path_input(path: str) -> str:
    """Sanitize path input by removing dangerous characters"""
    if "\x00" in path:
        raise SecurityError("Null bytes not allowed in paths", context={"path": path[:100]})

    # Check for other dangerous control characters (except tab, newline, carriage return)
    if any(ord(c) < 32 for c in path if c not in "\t\n\r"):
        raise SecurityError("Invalid control characters in path", context={"path": path[:100]})

    return path


def validate_file_size(size: int, max_size: int, file_path: str = "unknown") -> None:
    """Validate file size against limits"""
    if size > max_size:
        raise ResourceLimitError(
            f"File too large: {size} bytes (max: {max_size})",
            context={"file_path": file_path, "file_size": size, "max_size": max_size},
        )


def validate_tool_args(required_fields: list, optional_fields: Optional[list] = None):
    """Decorator to validate tool arguments"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract args from the function call
            if len(args) > 1:
                tool_args = args[1]
            else:
                tool_args = kwargs.get("args", {})

            # Validate that arguments are a dictionary
            validate_dict_input(tool_args, "arguments")

            # Check required fields
            for field in required_fields:
                if field not in tool_args:
                    raise ValidationError(
                        f"Missing required parameter: {field}",
                        context={
                            "required_fields": required_fields,
                            "provided": list(tool_args.keys()),
                        },
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
