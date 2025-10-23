"""Pytest configuration and fixtures."""
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# from app.main import app
# from app.models.database import Base
# from app.config import Settings


@pytest.fixture(scope="session")
def test_db() -> Generator[Session, None, None]:
    """Create a test database session."""
    # Create test database
    engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Create a test client."""
    # with TestClient(app) as test_client:
    #     yield test_client
    pass


@pytest.fixture
def sample_embedding():
    """Provide a sample embedding vector for testing."""
    import numpy as np
    return np.random.rand(384).tolist()  # Matches all-MiniLM-L6-v2 dimensions

