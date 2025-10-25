"""
Tests for GitHub client wrapper.

These tests verify authentication, connection, and repository access.
Some tests require a valid GITHUB_TOKEN to run against the real API.
"""

import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from github import GithubException, RateLimitExceededException

from scripts.ingestion.github_client import (
    GitHubAuthenticationError,
    GitHubClient,
    GitHubClientError,
    GitHubRateLimitError,
)


class TestGitHubClientInitialization:
    """Test GitHub client initialization and authentication."""

    def test_init_with_token(self) -> None:
        """Test initialization with explicit token."""
        token = "ghp_test_token_123"
        client = GitHubClient(token=token)
        assert client._token_prefix == "ghp_tes..."
        assert client.client is not None
        assert client.timeout == 10  # default
        assert client.max_retries == 3  # default

    def test_init_with_custom_params(self) -> None:
        """Test initialization with custom timeout and retries."""
        client = GitHubClient(token="ghp_test", timeout=20, max_retries=5)
        assert client.timeout == 20
        assert client.max_retries == 5

    def test_init_with_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test initialization using GITHUB_TOKEN environment variable."""
        test_token = "ghp_env_token_456"
        monkeypatch.setenv("GITHUB_TOKEN", test_token)

        client = GitHubClient()
        assert client._token_prefix == "ghp_env..."

    def test_init_without_token_raises_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that initialization fails without a token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        with pytest.raises(GitHubAuthenticationError) as exc_info:
            GitHubClient()

        assert "GitHub token not provided" in str(exc_info.value)

    def test_repr_masks_token(self) -> None:
        """Test that __repr__ masks the token."""
        client = GitHubClient(token="ghp_secret_token_12345")
        repr_str = repr(client)
        assert "ghp_sec..." in repr_str
        assert "secret_token" not in repr_str
        assert "timeout=10" in repr_str
        assert "max_retries=3" in repr_str


class TestGitHubClientContextManager:
    """Test context manager functionality."""

    @patch("scripts.ingestion.github_client.Github")
    def test_context_manager_enter_exit(self, mock_github: Mock) -> None:
        """Test that context manager properly opens and closes."""
        mock_client = Mock()
        mock_github.return_value = mock_client

        with GitHubClient(token="test_token") as client:
            assert isinstance(client, GitHubClient)
            assert client.client is not None

        # Verify close was called
        mock_client.close.assert_called_once()

    @patch("scripts.ingestion.github_client.Github")
    def test_context_manager_with_exception(self, mock_github: Mock) -> None:
        """Test that context manager closes even if exception occurs."""
        mock_client = Mock()
        mock_github.return_value = mock_client

        with pytest.raises(ValueError):
            with GitHubClient(token="test_token"):
                raise ValueError("Test exception")

        # Verify close was still called
        mock_client.close.assert_called_once()


class TestGitHubClientConnection:
    """Test connection verification and authentication."""

    def test_verify_connection_success(
        self, mock_github_client: Mock, mock_rate_limit: Mock, mock_user: Mock
    ) -> None:
        """Test successful connection verification."""
        mock_github_client.get_user.return_value = mock_user
        mock_github_client.get_rate_limit.return_value = mock_rate_limit

        client = GitHubClient(token="test_token")
        result = client.verify_connection()

        assert result is True
        mock_github_client.get_user.assert_called_once()
        mock_github_client.get_rate_limit.assert_called_once()

    def test_verify_connection_auth_failure(
        self, mock_github_client: Mock
    ) -> None:
        """Test connection verification with authentication failure."""
        mock_github_client.get_user.side_effect = GithubException(
            status=401,
            data={"message": "Bad credentials"},
            headers={},
        )

        client = GitHubClient(token="invalid_token")

        with pytest.raises(GitHubAuthenticationError) as exc_info:
            client.verify_connection()

        assert "Authentication failed" in str(exc_info.value)
        assert "Bad credentials" in str(exc_info.value)

    def test_verify_connection_with_non_dict_data(
        self, mock_github_client: Mock
    ) -> None:
        """Test error handling when exception data is not a dict."""
        mock_github_client.get_user.side_effect = GithubException(
            status=500,
            data="Internal Server Error",  # String instead of dict
            headers={},
        )

        client = GitHubClient(token="test_token")

        with pytest.raises(GitHubClientError) as exc_info:
            client.verify_connection()

        assert "GitHub API error" in str(exc_info.value)


class TestGitHubClientRepositoryAccess:
    """Test repository access methods."""

    def test_get_repository_success(
        self, mock_github_client: Mock, mock_repository: Mock
    ) -> None:
        """Test successful repository retrieval."""
        mock_github_client.get_repo.return_value = mock_repository

        client = GitHubClient(token="test_token")
        repo = client.get_repository("cloudvelous/aws-sdk")

        assert repo.full_name == "cloudvelous/aws-sdk"
        mock_github_client.get_repo.assert_called_once_with("cloudvelous/aws-sdk")

    def test_get_repository_not_found(self, mock_github_client: Mock) -> None:
        """Test repository retrieval when repo doesn't exist."""
        mock_github_client.get_repo.side_effect = GithubException(
            status=404,
            data={"message": "Not Found"},
            headers={},
        )

        client = GitHubClient(token="test_token")

        with pytest.raises(GitHubClientError) as exc_info:
            client.get_repository("nonexistent/repo")

        assert "not found or access denied" in str(exc_info.value)

    def test_get_repository_rate_limit(
        self, mock_github_client: Mock, mock_rate_limit: Mock
    ) -> None:
        """Test repository retrieval when rate limit is exceeded."""
        mock_github_client.get_repo.side_effect = RateLimitExceededException(
            status=403,
            data={"message": "Rate limit exceeded"},
            headers={},
        )
        mock_github_client.get_rate_limit.return_value = mock_rate_limit

        client = GitHubClient(token="test_token")

        with pytest.raises(GitHubRateLimitError) as exc_info:
            client.get_repository("cloudvelous/aws-sdk")

        assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "",
            "   ",
            "no-slash",
            "/missing-owner",
            "owner/",
            "owner/repo/extra",
            "owner//repo",
        ],
    )
    def test_get_repository_invalid_format(
        self, mock_github_client: Mock, invalid_name: str
    ) -> None:
        """Test repository retrieval with invalid repository name formats."""
        mock_github_client.get_repo.side_effect = GithubException(
            status=404,
            data={"message": "Not Found"},
            headers={},
        )

        client = GitHubClient(token="test_token")

        with pytest.raises(GitHubClientError):
            client.get_repository(invalid_name)

    def test_get_repository_with_retries_disabled(
        self, mock_github_client: Mock, mock_repository: Mock
    ) -> None:
        """Test repository access with retries disabled."""
        mock_github_client.get_repo.return_value = mock_repository

        client = GitHubClient(token="test_token", max_retries=0)
        repo = client.get_repository("cloudvelous/aws-sdk")

        assert repo.full_name == "cloudvelous/aws-sdk"

    def test_get_repository_generic_error(
        self, mock_github_client: Mock
    ) -> None:
        """Test repository retrieval with generic GitHub error."""
        mock_github_client.get_repo.side_effect = GithubException(
            status=500,
            data={"message": "Internal Server Error"},
            headers={},
        )

        client = GitHubClient(token="test_token")

        with pytest.raises(GitHubClientError) as exc_info:
            client.get_repository("cloudvelous/aws-sdk")

        assert "Error accessing repository" in str(exc_info.value)
        assert "Internal Server Error" in str(exc_info.value)


class TestGitHubClientRateLimit:
    """Test rate limit checking functionality."""

    def test_check_rate_limit(
        self, mock_github_client: Mock, mock_rate_limit: Mock
    ) -> None:
        """Test rate limit status check."""
        mock_github_client.get_rate_limit.return_value = mock_rate_limit

        client = GitHubClient(token="test_token")
        limits = client.check_rate_limit()

        assert limits["limit"] == 5000
        assert limits["remaining"] == 4500
        assert isinstance(limits["reset"], datetime)
        assert limits["reset"].tzinfo == timezone.utc

    def test_check_rate_limit_returns_typed_dict(
        self, mock_github_client: Mock, mock_rate_limit: Mock
    ) -> None:
        """Test that check_rate_limit returns proper TypedDict structure."""
        mock_github_client.get_rate_limit.return_value = mock_rate_limit

        client = GitHubClient(token="test_token")
        limits = client.check_rate_limit()

        # Verify all expected keys are present
        assert "limit" in limits
        assert "remaining" in limits
        assert "reset" in limits

        # Verify types
        assert isinstance(limits["limit"], int)
        assert isinstance(limits["remaining"], int)
        assert isinstance(limits["reset"], datetime)


class TestGitHubClientResourceManagement:
    """Test resource cleanup and connection management."""

    def test_close_success(self, mock_github_client: Mock) -> None:
        """Test successful connection close."""
        client = GitHubClient(token="test_token")
        client.close()

        mock_github_client.close.assert_called_once()

    def test_close_with_no_client(self, mock_github_client: Mock) -> None:
        """Test close when client doesn't have close method."""
        mock_github_client.close.side_effect = AttributeError("no close")

        client = GitHubClient(token="test_token")
        # Should not raise exception
        client.close()

    def test_close_with_exception(self, mock_github_client: Mock) -> None:
        """Test close when an exception occurs."""
        mock_github_client.close.side_effect = Exception("Connection error")

        client = GitHubClient(token="test_token")
        # Should not raise exception
        client.close()


class TestGitHubClientEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_short_token(self) -> None:
        """Test initialization with very short token."""
        client = GitHubClient(token="abc")
        assert client._token_prefix == "***"

    def test_get_repository_with_special_characters(
        self, mock_github_client: Mock, mock_repository: Mock
    ) -> None:
        """Test repository name with special characters."""
        mock_repository.full_name = "org-name/repo.name"
        mock_github_client.get_repo.return_value = mock_repository

        client = GitHubClient(token="test_token")
        repo = client.get_repository("org-name/repo.name")

        assert repo.full_name == "org-name/repo.name"

    def test_rate_limit_with_zero_remaining(
        self, mock_github_client: Mock, mock_rate_limit: Mock
    ) -> None:
        """Test rate limit check when no requests remaining."""
        mock_rate_limit.core.remaining = 0
        mock_github_client.get_rate_limit.return_value = mock_rate_limit

        client = GitHubClient(token="test_token")
        limits = client.check_rate_limit()

        assert limits["remaining"] == 0


# Integration tests (require real GITHUB_TOKEN)
@pytest.mark.integration
class TestGitHubClientIntegration:
    """
    Integration tests that require a real GitHub token.

    Run with: pytest -m integration
    Requires: GITHUB_TOKEN environment variable
    """

    @pytest.fixture
    def real_client(self) -> GitHubClient:
        """Fixture that creates a real GitHub client."""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            pytest.skip("GITHUB_TOKEN not set")
        return GitHubClient(token=token)

    def test_real_connection(self, real_client: GitHubClient) -> None:
        """Test connection with real GitHub API."""
        result = real_client.verify_connection()
        assert result is True

    def test_real_rate_limit_check(self, real_client: GitHubClient) -> None:
        """Test rate limit check with real API."""
        limits = real_client.check_rate_limit()
        assert "limit" in limits
        assert "remaining" in limits
        assert "reset" in limits
        assert limits["remaining"] >= 0
        assert limits["limit"] > 0
        assert isinstance(limits["reset"], datetime)

    def test_real_context_manager(self, real_client: GitHubClient) -> None:
        """Test context manager with real client."""
        token = os.getenv("GITHUB_TOKEN")
        with GitHubClient(token=token) as client:
            result = client.verify_connection()
            assert result is True
