"""
Shared test fixtures for ingestion tests.

Provides reusable mock objects and test data for GitHub client testing.
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_github_client():
    """
    Provides a fully mocked GitHub client.

    Yields:
        Mock: Mocked PyGithub client instance
    """
    with patch("scripts.ingestion.github_client.Github") as mock_github:
        mock_client = Mock()
        mock_github.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_rate_limit():
    """
    Provides a mock rate limit response.

    Returns:
        Mock: Mock rate limit object with core attributes
    """
    mock_core = Mock()
    mock_core.limit = 5000
    mock_core.remaining = 4500
    mock_core.reset = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    mock_rate_limit = Mock()
    mock_rate_limit.core = mock_core
    return mock_rate_limit


@pytest.fixture
def mock_user():
    """
    Provides a mock GitHub user.

    Returns:
        Mock: Mock user object with login attribute
    """
    mock = Mock()
    mock.login = "testuser"
    return mock


@pytest.fixture
def mock_repository():
    """
    Provides a mock GitHub repository.

    Returns:
        Mock: Mock repository object with full_name attribute
    """
    mock = Mock()
    mock.full_name = "cloudvelous/aws-sdk"
    mock.name = "aws-sdk"
    mock.owner.login = "cloudvelous"
    return mock

