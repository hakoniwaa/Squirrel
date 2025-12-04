"""
Authentication module for API endpoints
"""

from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token

    Args:
        credentials: HTTP Bearer token from request

    Returns:
        Dict containing user information

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # TODO: Implement actual JWT validation and user lookup
    # For now, return a mock user
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Mock user data - replace with actual user lookup
    return {
        "id": 1,
        "username": "example_user",
        "email": "user@example.com",
        "active": True,
    }
