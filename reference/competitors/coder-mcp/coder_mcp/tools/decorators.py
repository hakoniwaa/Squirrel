#!/usr/bin/env python3
"""
Decorators for tool registration and validation
"""

import json
import logging
from functools import wraps
from typing import Any, Callable, Dict

from ..security.validators import validate_dict_input

logger = logging.getLogger(__name__)


def tool(name: str, description: str, schema: Dict):
    """Decorator for registering tools with metadata"""

    def decorator(func: Callable) -> Callable:
        setattr(
            func, "_tool_metadata", {"name": name, "description": description, "schema": schema}
        )
        return func

    return decorator


def validate_args(schema: Dict):
    """Decorator for argument validation against schema"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, args: Dict[str, Any]):
            # Validate arguments against the provided schema
            try:
                validate_against_schema(args, schema)
            except Exception as e:
                return f"Validation error: {str(e)}"

            return await func(self, args)

        return wrapper

    return decorator


def validate_against_schema(data: Dict[str, Any], schema: Dict):
    """Simple schema validation for tool arguments"""
    # Basic validation - can be enhanced with jsonschema library
    validate_dict_input(data, "tool arguments")

    if "required" in schema:
        for required_field in schema["required"]:
            if required_field not in data:
                raise ValueError(f"Missing required field: {required_field}")

    if "properties" in schema:
        for field_name, field_schema in schema["properties"].items():
            if field_name in data:
                field_value = data[field_name]
                _validate_field_type(field_name, field_value, field_schema)
                _validate_field_enum(field_name, field_value, field_schema)


def _validate_field_type(field_name: str, field_value: Any, field_schema: Dict) -> None:
    field_type = field_schema.get("type")
    if field_type == "string" and not isinstance(field_value, str):
        raise ValueError(f"Field '{field_name}' must be a string")
    elif field_type == "boolean" and not isinstance(field_value, bool):
        raise ValueError(f"Field '{field_name}' must be a boolean")
    elif field_type == "integer" and not isinstance(field_value, int):
        raise ValueError(f"Field '{field_name}' must be an integer")
    elif field_type == "number" and not isinstance(field_value, (int, float)):
        raise ValueError(f"Field '{field_name}' must be a number")
    elif field_type == "array" and not isinstance(field_value, list):
        raise ValueError(f"Field '{field_name}' must be an array")
    elif field_type == "object" and not isinstance(field_value, dict):
        raise ValueError(f"Field '{field_name}' must be an object")


def _validate_field_enum(field_name: str, field_value: Any, field_schema: Dict) -> None:
    if "enum" in field_schema:
        if field_value not in field_schema["enum"]:
            raise ValueError(f"Field '{field_name}' must be one of: {field_schema['enum']}")


def rate_limit(calls_per_minute: int = 60):
    """Decorator for rate limiting tool calls"""

    def decorator(func: Callable) -> Callable:
        # Simple rate limiting implementation
        # In a real implementation, you'd use a proper rate limiter
        @wraps(func)
        async def wrapper(self, args: Dict[str, Any]):
            # Rate limiting logic would go here
            # For now, just pass through
            return await func(self, args)

        return wrapper

    return decorator


def cache_result(ttl_seconds: int = 300):
    """Decorator for caching tool results"""

    def decorator(func: Callable) -> Callable:
        # Simple caching implementation
        # In a real implementation, you'd use a proper cache
        cache = {}

        @wraps(func)
        async def wrapper(self, args: Dict[str, Any]):
            # Create cache key from function name and args
            cache_key = f"{func.__name__}:{json.dumps(args, sort_keys=True)}"

            # Check if result is cached and not expired
            if cache_key in cache:
                # For simplicity, not implementing TTL expiration here
                # In production, you'd check timestamp and TTL
                pass

            # Execute function and cache result
            result = await func(self, args)
            cache[cache_key] = result
            return result

        return wrapper

    return decorator


def log_tool_call(func: Callable) -> Callable:
    """Decorator for logging tool calls"""

    @wraps(func)
    async def wrapper(self, args: Dict[str, Any]):
        tool_name = func.__name__
        # Log the tool call
        logger.debug(f"Tool called: {tool_name} with args: {args}")

        try:
            result = await func(self, args)
            logger.debug(f"Tool {tool_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {str(e)}")
            raise

    return wrapper
