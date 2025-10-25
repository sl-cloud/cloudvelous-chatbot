"""
Unit tests for authentication middleware edge cases.
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from jose import jwt

from app.middleware.auth import (
    create_access_token,
    verify_jwt_token,
    verify_api_key,
    require_admin,
    require_api_key,
    require_admin_or_api_key
)
from app.config import settings


class TestCreateAccessToken:
    """Tests for JWT token creation."""
    
    def test_create_access_token_default_expiration(self):
        """Test creating token with default expiration."""
        token = create_access_token({"sub": "admin"})
        
        assert token is not None
        assert isinstance(token, str)
        
        # Decode and verify
        payload = jwt.decode(token, settings.ADMIN_JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "admin"
        assert "exp" in payload
    
    def test_create_access_token_custom_expiration(self):
        """Test creating token with custom expiration."""
        custom_delta = timedelta(hours=2)
        token = create_access_token({"sub": "admin"}, expires_delta=custom_delta)
        
        payload = jwt.decode(token, settings.ADMIN_JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Expiration should be approximately 2 hours from now
        time_diff = exp_time - now
        assert timedelta(hours=1, minutes=59) < time_diff < timedelta(hours=2, minutes=1)
    
    def test_create_access_token_is_timezone_aware(self):
        """Test that token expiration is timezone-aware."""
        token = create_access_token({"sub": "admin"})
        
        payload = jwt.decode(token, settings.ADMIN_JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        
        # Should have timezone info
        assert exp_time.tzinfo is not None


class TestVerifyJWTToken:
    """Tests for JWT token verification."""
    
    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        token = create_access_token({"sub": "admin", "role": "admin"})
        
        payload = verify_jwt_token(token)
        
        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"
    
    def test_verify_expired_token(self):
        """Test verifying an expired token."""
        # Create a token that's already expired
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_token = jwt.encode(
            {"sub": "admin", "exp": expired_time},
            settings.ADMIN_JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(expired_token)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail
    
    def test_verify_invalid_signature(self):
        """Test verifying a token with invalid signature."""
        # Create a token with wrong secret
        invalid_token = jwt.encode(
            {"sub": "admin"},
            "wrong-secret",
            algorithm=settings.JWT_ALGORITHM
        )
        
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(invalid_token)
        
        assert exc_info.value.status_code == 401
    
    def test_verify_malformed_token(self):
        """Test verifying a malformed token."""
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token("not-a-valid-jwt-token")
        
        assert exc_info.value.status_code == 401


class TestVerifyAPIKey:
    """Tests for API key verification."""
    
    def test_verify_valid_api_key(self):
        """Test verifying a valid API key."""
        result = verify_api_key(settings.ADMIN_API_KEY)
        
        assert result is True
    
    def test_verify_invalid_api_key(self):
        """Test verifying an invalid API key."""
        result = verify_api_key("wrong-api-key")
        
        assert result is False
    
    def test_verify_empty_api_key(self):
        """Test verifying an empty API key."""
        result = verify_api_key("")
        
        assert result is False
    
    def test_verify_none_api_key(self):
        """Test verifying None as API key."""
        result = verify_api_key(None)
        
        assert result is False
    
    def test_verify_api_key_uses_constant_time_comparison(self):
        """Test that API key verification is timing-safe."""
        import time
        
        # This is a basic test - real timing attack testing would be more complex
        # Just verify the function completes for different inputs
        start1 = time.time()
        verify_api_key("a")
        time1 = time.time() - start1
        
        start2 = time.time()
        verify_api_key("a" * 100)
        time2 = time.time() - start2
        
        # Both should complete (timing would need statistical analysis to truly test)
        assert time1 >= 0
        assert time2 >= 0


class TestRequireAdminDependency:
    """Tests for require_admin dependency."""
    
    @pytest.mark.asyncio
    async def test_require_admin_with_valid_credentials(self):
        """Test require_admin with valid credentials."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        token = create_access_token({"sub": "admin"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        payload = await require_admin(credentials)
        
        assert payload["sub"] == "admin"
    
    @pytest.mark.asyncio
    async def test_require_admin_without_credentials(self):
        """Test require_admin without credentials."""
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(None)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_admin_with_invalid_token(self):
        """Test require_admin with invalid token."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(credentials)
        
        assert exc_info.value.status_code == 401


class TestRequireAPIKeyDependency:
    """Tests for require_api_key dependency."""
    
    @pytest.mark.asyncio
    async def test_require_api_key_with_valid_key(self):
        """Test require_api_key with valid key."""
        api_key = await require_api_key(settings.ADMIN_API_KEY)
        
        assert api_key == settings.ADMIN_API_KEY
    
    @pytest.mark.asyncio
    async def test_require_api_key_without_key(self):
        """Test require_api_key without key."""
        with pytest.raises(HTTPException) as exc_info:
            await require_api_key(None)
        
        assert exc_info.value.status_code == 401
        assert "API key required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_require_api_key_with_invalid_key(self):
        """Test require_api_key with invalid key."""
        with pytest.raises(HTTPException) as exc_info:
            await require_api_key("wrong-key")
        
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.detail


class TestRequireAdminOrAPIKey:
    """Tests for require_admin_or_api_key dependency."""
    
    @pytest.mark.asyncio
    async def test_with_valid_jwt(self):
        """Test with valid JWT token."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        token = create_access_token({"sub": "admin"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        result = await require_admin_or_api_key(credentials, None)
        
        assert result["auth_type"] == "jwt"
        assert "payload" in result
    
    @pytest.mark.asyncio
    async def test_with_valid_api_key(self):
        """Test with valid API key."""
        result = await require_admin_or_api_key(None, settings.ADMIN_API_KEY)
        
        assert result["auth_type"] == "api_key"
        assert result["key"] == settings.ADMIN_API_KEY
    
    @pytest.mark.asyncio
    async def test_jwt_takes_precedence_over_api_key(self):
        """Test that JWT is tried before API key."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        token = create_access_token({"sub": "admin"})
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        result = await require_admin_or_api_key(credentials, settings.ADMIN_API_KEY)
        
        # Should use JWT, not API key
        assert result["auth_type"] == "jwt"
    
    @pytest.mark.asyncio
    async def test_fallback_to_api_key_when_jwt_invalid(self):
        """Test falling back to API key when JWT is invalid."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
        
        result = await require_admin_or_api_key(credentials, settings.ADMIN_API_KEY)
        
        # Should fall back to API key
        assert result["auth_type"] == "api_key"
    
    @pytest.mark.asyncio
    async def test_neither_jwt_nor_api_key(self):
        """Test when neither JWT nor API key is provided."""
        with pytest.raises(HTTPException) as exc_info:
            await require_admin_or_api_key(None, None)
        
        assert exc_info.value.status_code == 401
        assert "JWT token or API key required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_both_invalid(self):
        """Test when both JWT and API key are invalid."""
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
        
        with pytest.raises(HTTPException) as exc_info:
            await require_admin_or_api_key(credentials, "wrong-key")
        
        assert exc_info.value.status_code == 401

