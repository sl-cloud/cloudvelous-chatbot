"""Tests for application configuration settings."""

import os

import pytest

from app.config import Settings


def test_settings_defaults_are_loaded(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should expose defined default values when no env overrides are set."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)  # Ignore local .env for deterministic test

    assert settings.DATABASE_URL.startswith("postgresql://")
    assert settings.WORKFLOW_EMBEDDING_ENABLED is True
    assert settings.TOP_K_RETRIEVAL == 5


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables should override defaults."""
    monkeypatch.setenv("API_PORT", "9001")
    monkeypatch.setenv("WORKFLOW_EMBEDDING_ENABLED", "false")

    settings = Settings(_env_file=None)

    assert settings.API_PORT == 9001
    assert settings.WORKFLOW_EMBEDDING_ENABLED is False

