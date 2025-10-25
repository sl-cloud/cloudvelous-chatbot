"""
GitHub API client wrapper for repository data ingestion.

This module provides a simple interface to the GitHub API using PyGithub,
with built-in authentication and rate limit handling.
"""

import logging
import os
from datetime import datetime
from typing import Optional, TypedDict

from github import Auth, Github, GithubException, RateLimitExceededException
from github.Repository import Repository
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)


class RateLimitInfo(TypedDict):
    """Rate limit information from GitHub API."""

    limit: int
    remaining: int
    reset: datetime


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""


class GitHubAuthenticationError(GitHubClientError):
    """Raised when authentication fails."""


class GitHubRateLimitError(GitHubClientError):
    """Raised when rate limit is exceeded."""


class GitHubClient:
    """
    Wrapper for GitHub API access with authentication and error handling.

    This client handles:
    - Authentication using personal access token
    - Connection verification
    - Rate limit checking
    - Repository access
    - Automatic retry with exponential backoff (optional)
    - Request timeouts

    Attributes:
        client: The authenticated PyGithub client instance
        max_retries: Maximum number of retry attempts for transient failures
        timeout: Request timeout in seconds

    Example:
        >>> with GitHubClient(token="ghp_xxxx") as client:
        ...     client.verify_connection()
        ...     repo = client.get_repository("owner/repo")
    """

    def __init__(
        self,
        token: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize GitHub client with authentication.

        Args:
            token: GitHub personal access token. If not provided,
                   reads from GITHUB_TOKEN environment variable.
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum retry attempts for transient failures (default: 3)

        Raises:
            GitHubAuthenticationError: If no token is provided or found.
        """
        _raw_token = token or os.getenv("GITHUB_TOKEN")

        if not _raw_token:
            raise GitHubAuthenticationError(
                "GitHub token not provided. Set GITHUB_TOKEN environment variable "
                "or pass token to constructor."
            )

        # Authenticate using the token
        auth = Auth.Token(_raw_token)
        self.client = Github(auth=auth, timeout=timeout)
        self.max_retries = max_retries
        self.timeout = timeout

        # Store masked token for logging/debugging (never log full token)
        self._token_prefix = (
            _raw_token[:7] + "..." if len(_raw_token) > 7 else "***"
        )

        logger.info(
            "GitHub client initialized",
            extra={
                "token_prefix": self._token_prefix,
                "timeout": timeout,
                "max_retries": max_retries,
            },
        )

    def __repr__(self) -> str:
        """Return string representation with masked token."""
        return (
            f"GitHubClient(token={self._token_prefix}, "
            f"timeout={self.timeout}, max_retries={self.max_retries})"
        )

    def __enter__(self) -> "GitHubClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes connection."""
        self.close()

    @staticmethod
    def _get_error_message(exc: GithubException) -> str:
        """
        Extract error message from GitHub exception safely.

        Args:
            exc: GitHub exception to extract message from

        Returns:
            Error message string
        """
        if isinstance(exc.data, dict):
            return exc.data.get("message", str(exc))
        return str(exc)

    def verify_connection(self) -> bool:
        """
        Verify that the GitHub connection and authentication are working.

        Returns:
            True if connection is successful

        Raises:
            GitHubAuthenticationError: If authentication fails
            GitHubClientError: If connection fails for other reasons

        Example:
            >>> client = GitHubClient()
            >>> client.verify_connection()
            True
        """
        try:
            # Try to get authenticated user info
            user = self.client.get_user()
            username = user.login
            logger.info(
                "GitHub authentication successful",
                extra={"github_user": username, "action": "auth_verify"},
            )

            # Check rate limit
            rate_limit = self.client.get_rate_limit()
            core = rate_limit.core
            logger.info(
                "GitHub rate limit check",
                extra={
                    "remaining": core.remaining,
                    "limit": core.limit,
                    "reset_at": core.reset.isoformat() if core.reset else None,
                },
            )

            return True

        except GithubException as exc:
            if exc.status == 401:
                message = self._get_error_message(exc)
                raise GitHubAuthenticationError(
                    f"Authentication failed: {message}"
                ) from exc
            raise GitHubClientError(
                f"GitHub API error: {self._get_error_message(exc)}"
            ) from exc

    def _get_repository_impl(self, repo_full_name: str) -> Repository:
        """
        Internal implementation of get_repository without retry decorator.

        This allows the retry logic to be applied only when max_retries > 0.
        """
        try:
            logger.info(
                "Fetching GitHub repository",
                extra={"repository": repo_full_name, "action": "repo_fetch"},
            )
            repo = self.client.get_repo(repo_full_name)
            logger.info(
                "Successfully loaded repository",
                extra={
                    "repository": repo.full_name,
                    "action": "repo_fetch_success",
                },
            )
            return repo

        except RateLimitExceededException as exc:
            rate_limit = self.client.get_rate_limit()
            raise GitHubRateLimitError(
                f"Rate limit exceeded. Resets at {rate_limit.core.reset}"
            ) from exc

        except GithubException as exc:
            if exc.status == 404:
                raise GitHubClientError(
                    f"Repository '{repo_full_name}' not found or access denied"
                ) from exc
            raise GitHubClientError(
                f"Error accessing repository: {self._get_error_message(exc)}"
            ) from exc

    def get_repository(self, repo_full_name: str) -> Repository:
        """
        Get a repository by its full name (owner/repo).

        Args:
            repo_full_name: Repository identifier in format "owner/repo"
                            e.g., "cloudvelous/aws-sdk"

        Returns:
            Repository object from PyGithub

        Raises:
            GitHubClientError: If repository not found or access denied
            GitHubRateLimitError: If rate limit is exceeded

        Example:
            >>> client = GitHubClient()
            >>> repo = client.get_repository("cloudvelous/aws-sdk")
            >>> print(repo.full_name)
            cloudvelous/aws-sdk
        """
        if self.max_retries > 0:
            # Apply retry logic for transient failures
            retrying_get = retry(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential_jitter(max=10),
                retry=retry_if_exception_type(GitHubClientError),
                reraise=True,
            )(self._get_repository_impl)
            return retrying_get(repo_full_name)
        else:
            return self._get_repository_impl(repo_full_name)

    def check_rate_limit(self) -> RateLimitInfo:
        """
        Check current API rate limit status.

        Returns:
            RateLimitInfo dictionary with:
                - limit: Total requests allowed per hour
                - remaining: Requests remaining
                - reset: When limit resets (datetime)

        Example:
            >>> client = GitHubClient()
            >>> limits = client.check_rate_limit()
            >>> print(f"Remaining: {limits['remaining']}")
        """
        rate_limit = self.client.get_rate_limit()
        core = rate_limit.core

        return RateLimitInfo(
            limit=core.limit,
            remaining=core.remaining,
            reset=core.reset,
        )

    def close(self) -> None:
        """
        Close the GitHub client connection.

        Should be called when done using the client to clean up resources.
        Best used via context manager (with statement).
        """
        try:
            self.client.close()
            logger.info("GitHub client connection closed")
        except (AttributeError, Exception):
            # Already closed or never initialized
            pass

