"""
Unit tests for authentication middleware.
"""

import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.middleware.auth import (
    create_access_token,
    verify_jwt_token,
    verify_api_key,
)
from app.config import settings


class TestJWTFunctions:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test creating a JWT access token."""
        data = {"sub": "admin", "role": "admin"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test creating a JWT token with custom expiry."""
        data = {"sub": "admin"}
        expires_delta = timedelta(hours=1)
        token = create_access_token(data, expires_delta)

        # Decode to verify expiry
        payload = jwt.decode(
            token,
            settings.ADMIN_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert "exp" in payload
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Should expire in approximately 1 hour
        time_diff = (exp_time - now).total_seconds()
        assert 3500 < time_diff < 3700  # Allow some margin

    def test_verify_valid_token(self):
        """Test verifying a valid JWT token."""
        data = {"sub": "admin", "role": "admin"}
        token = create_access_token(data)

        payload = verify_jwt_token(token)

        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"
        assert "exp" in payload

    def test_verify_expired_token(self):
        """Test that expired tokens are rejected."""
        data = {"sub": "admin"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data, expires_delta)

        # Should raise exception
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(token)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    def test_verify_invalid_token(self):
        """Test that invalid tokens are rejected."""
        invalid_token = "invalid.token.here"

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_jwt_token(invalid_token)

        assert exc_info.value.status_code == 401

    def test_verify_tampered_token(self):
        """Test that tampered tokens are rejected."""
        data = {"sub": "admin"}
        token = create_access_token(data)

        # Tamper with the token
        tampered_token = token[:-5] + "xxxxx"

        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            verify_jwt_token(tampered_token)


class TestAPIKeyVerification:
    """Test API key verification."""

    def test_verify_valid_api_key(self):
        """Test verifying a valid API key."""
        valid_key = settings.ADMIN_API_KEY
        assert verify_api_key(valid_key) is True

    def test_verify_invalid_api_key(self):
        """Test that invalid API keys are rejected."""
        invalid_key = "wrong_api_key_123"
        assert verify_api_key(invalid_key) is False

    def test_verify_empty_api_key(self):
        """Test that empty API keys are rejected."""
        assert verify_api_key("") is False


class TestTokenPayload:
    """Test token payload handling."""

    def test_token_contains_custom_claims(self):
        """Test that custom claims are preserved in token."""
        data = {
            "sub": "admin",
            "role": "admin",
            "permissions": ["read", "write"],
            "session_id": "123"
        }
        token = create_access_token(data)
        payload = verify_jwt_token(token)

        assert payload["sub"] == "admin"
        assert payload["role"] == "admin"
        assert payload["permissions"] == ["read", "write"]
        assert payload["session_id"] == "123"

    def test_token_expiry_field(self):
        """Test that expiry field is correctly set."""
        data = {"sub": "admin"}
        token = create_access_token(data)
        payload = verify_jwt_token(token)

        assert "exp" in payload
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Should expire in approximately 24 hours (default)
        time_diff = (exp_time - now).total_seconds()
        expected = settings.JWT_EXPIRATION_HOURS * 3600
        assert expected - 100 < time_diff < expected + 100  # Allow 100s margin
