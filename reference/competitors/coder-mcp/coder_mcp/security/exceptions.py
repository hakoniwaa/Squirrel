#!/usr/bin/env python3
"""
Security Exception Classes for MCP Server
Standardized error handling with structured context
"""

import logging
from functools import wraps
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)


def handle_exceptions(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Decorator to standardize exception handling for tool methods"""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except MCPServerError as e:
            # Log structured error
            logger.error(f"MCP Server Error in {func.__name__}: {e.to_dict()}")
            return f"Error: {e.message}"
        except Exception as e:
            # Convert unexpected errors to MCPServerError
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            server_error = MCPServerError(
                message=f"Internal server error: {str(e)[:200]}",
                error_code="INTERNAL_ERROR",
                context={"function": func.__name__, "original_error": str(e)},
            )
            return f"Error: {server_error.message}"

    return wrapper


class MCPServerError(Exception):
    """Base exception for MCP Server errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.context = context or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for structured logging"""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
        }


class SecurityError(MCPServerError):
    """Security-related errors (path traversal, unauthorized access, etc.)"""


class ValidationError(MCPServerError):
    """Input validation errors"""


class FileOperationError(MCPServerError):
    """File system operation errors"""


class RedisOperationError(MCPServerError):
    """Redis operation errors"""


class ConfigurationError(MCPServerError):
    """Configuration and setup errors"""


class ResourceLimitError(MCPServerError):
    """Resource limit exceeded errors"""


class SearchError(MCPServerError):
    """Search operation errors"""


class TemplateError(MCPServerError):
    """Template generation and rendering errors"""


class AnalysisError(MCPServerError):
    """Code analysis errors"""


class APIError(MCPServerError):
    """API operation errors (OpenAI, external services)"""


class RateLimitError(MCPServerError):
    """Rate limiting errors"""


class ProcessingError(MCPServerError):
    """Data processing errors"""


class ToolError(MCPServerError):
    """Tool execution errors"""
