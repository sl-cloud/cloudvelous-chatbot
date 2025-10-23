"""Tests for database connection and session management."""

from __future__ import annotations

from app.models.database import get_db


def test_get_db_yields_session() -> None:
    """get_db should yield a database session."""
    # This test verifies the generator pattern works
    gen = get_db()
    
    # Get the session
    try:
        session = next(gen)
        assert session is not None
    finally:
        # Clean up the generator
        try:
            next(gen)
        except StopIteration:
            pass  # Expected

