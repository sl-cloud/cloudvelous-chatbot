"""
Authentication middleware and dependencies for admin endpoints.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import JWTError, jwt

from app.config import settings
from app.utils.logging import get_logger


# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with timezone-aware expiration.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.ADMIN_JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.ADMIN_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise credentials_exception


def verify_api_key(api_key: str) -> bool:
    """
    Verify an API key against the configured admin key using constant-time comparison.

    This prevents timing attacks where an attacker could determine the correct
    key character-by-character by measuring response times.

    Args:
        api_key: API key to verify

    Returns:
        True if valid, False otherwise
    """
    if not api_key or not settings.ADMIN_API_KEY:
        return False
    return secrets.compare_digest(api_key, settings.ADMIN_API_KEY)


async def require_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> dict:
    """
    FastAPI dependency that requires a valid JWT token.

    Use this on endpoints that require admin authentication via JWT.

    Args:
        credentials: HTTP Bearer credentials

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If credentials are missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_jwt_token(credentials.credentials)


async def require_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> str:
    """
    FastAPI dependency that requires a valid API key.

    Use this on endpoints that require admin authentication via API key.

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The validated API key

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


async def require_admin_or_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header)
) -> dict:
    """
    FastAPI dependency that accepts either JWT token or API key.

    Use this on endpoints that can be accessed via either authentication method.

    Args:
        credentials: HTTP Bearer credentials
        api_key: API key from X-API-Key header

    Returns:
        Dict with auth_type and payload/key

    Raises:
        HTTPException: If neither authentication method is valid
    """
    log = get_logger(__name__)
    
    # Try JWT first
    if credentials:
        try:
            payload = verify_jwt_token(credentials.credentials)
            return {"auth_type": "jwt", "payload": payload}
        except HTTPException as e:
            # Log JWT verification failure for security monitoring
            log.warning(
                "JWT authentication failed",
                error=e.detail,
                status_code=e.status_code,
                has_api_key_fallback=bool(api_key)
            )

    # Try API key
    if api_key:
        if verify_api_key(api_key):
            return {"auth_type": "api_key", "key": api_key}
        else:
            log.warning(
                "API key authentication failed",
                has_jwt_fallback=bool(credentials)
            )

    # Neither worked - log final authentication failure
    log.warning(
        "Authentication failed - neither JWT nor API key valid",
        has_jwt=bool(credentials),
        has_api_key=bool(api_key)
    )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Valid JWT token or API key required",
        headers={"WWW-Authenticate": "Bearer, ApiKey"},
    )
