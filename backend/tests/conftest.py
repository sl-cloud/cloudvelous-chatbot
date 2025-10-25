"""
Pytest configuration and shared fixtures.

This module provides test infrastructure including:
- Stub modules for heavy dependencies (pgvector, sentence-transformers, etc.)
- Database fixtures (in-memory SQLite)
- API client fixtures (FastAPI TestClient)
- Stub database session for unit tests
- Sample data fixtures
"""

from __future__ import annotations

import os
import sys
import types
from typing import Any, Dict, Generator, List, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Disable rate limiting for all tests BEFORE any app imports
os.environ["RATE_LIMITING_ENABLED"] = "false"


def _ensure_stub_modules() -> None:
    """Register lightweight stubs for heavy optional dependencies."""
    if "sentence_transformers" not in sys.modules:
        module = types.ModuleType("sentence_transformers")

        class _DummySentenceTransformer:
            def __init__(self, model_name: str) -> None:
                self.model_name = model_name
                self._dimension = 8

            def get_sentence_embedding_dimension(self) -> int:
                return self._dimension

            def _encode_one(self, text: str) -> List[float]:
                base = hash(text) % 100
                return [(base + i) / 100.0 for i in range(self._dimension)]

            def encode(self, texts: Any, convert_to_numpy: bool = True) -> Any:
                if isinstance(texts, str):
                    vector = self._encode_one(texts)
                    return vector
                vectors = [self._encode_one(text) for text in texts]
                return vectors

        module.SentenceTransformer = _DummySentenceTransformer  # type: ignore[attr-defined]
        sys.modules["sentence_transformers"] = module

    if "pgvector" not in sys.modules:
        pgvector_module = types.ModuleType("pgvector")
        sqlalchemy_module = types.ModuleType("pgvector.sqlalchemy")

        from sqlalchemy.types import PickleType, TypeDecorator
        from sqlalchemy import func

        class _DummyVectorComparator:
            """Comparator that provides cosine_distance for testing."""
            
            def __init__(self, column):
                self.column = column
            
            def cosine_distance(self, other):
                """Return a dummy expression for cosine distance."""
                # Return a simple constant for testing
                return func.random()  # Placeholder that works with SQLAlchemy
        
        class _DummyVector(TypeDecorator):  # pragma: no cover - trivial wrapper
            """Fallback vector type storing data via PickleType."""

            impl = PickleType
            cache_ok = True
            
            class comparator_factory(_DummyVectorComparator):
                """Factory for creating comparator instances."""
                pass

            def process_bind_param(self, value: Any, dialect: Any) -> Any:
                return value

            def process_result_value(self, value: Any, dialect: Any) -> Any:
                return value

        sqlalchemy_module.Vector = _DummyVector  # type: ignore[attr-defined]
        pgvector_module.sqlalchemy = sqlalchemy_module  # type: ignore[attr-defined]

        sys.modules["pgvector"] = pgvector_module
        sys.modules["pgvector.sqlalchemy"] = sqlalchemy_module

    if "openai" not in sys.modules:
        openai_module = types.ModuleType("openai")

        class _DummyChatCompletions:
            def create(self, **kwargs: Any) -> Any:
                return types.SimpleNamespace(
                    choices=[
                        types.SimpleNamespace(
                            message=types.SimpleNamespace(content="stubbed response")
                        )
                    ]
                )

        class _DummyChat:
            def __init__(self) -> None:
                self.completions = _DummyChatCompletions()

        class _DummyOpenAI:
            def __init__(self, api_key: Optional[str] = None) -> None:
                self.api_key = api_key
                self.chat = _DummyChat()

        openai_module.OpenAI = _DummyOpenAI  # type: ignore[attr-defined]
        sys.modules["openai"] = openai_module

    if "google" not in sys.modules:
        google_module = types.ModuleType("google")
        sys.modules["google"] = google_module

    if "google.generativeai" not in sys.modules:
        genai_module = types.ModuleType("google.generativeai")
        genai_types_module = types.ModuleType("google.generativeai.types")

        class _DummyGenerationConfig:
            def __init__(self, **kwargs: Any) -> None:
                self.kwargs = kwargs

        def _configure(**kwargs: Any) -> None:  # pragma: no cover - simple setter
            genai_module._config = kwargs

        class _DummyGenerativeModel:
            def __init__(self, model: str) -> None:
                self.model = model

            def generate_content(self, prompt: str, generation_config: Any = None) -> Any:
                return types.SimpleNamespace(text=f"stubbed {self.model} response")

        genai_module.configure = _configure  # type: ignore[attr-defined]
        genai_module.GenerativeModel = _DummyGenerativeModel  # type: ignore[attr-defined]
        genai_module.types = genai_types_module  # type: ignore[attr-defined]
        genai_types_module.GenerationConfig = _DummyGenerationConfig  # type: ignore[attr-defined]

        sys.modules["google.generativeai"] = genai_module
        sys.modules["google.generativeai.types"] = genai_types_module


_ensure_stub_modules()


@pytest.fixture(scope="session")
def memory_db_engine():
    """Provide a shared in-memory SQLite engine for tests."""
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()


@pytest.fixture
def test_db(memory_db_engine) -> Generator[Session, None, None]:
    """
    Provide an isolated SQLAlchemy session bound to the in-memory engine.

    Tests can choose to create/drop tables as needed.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=memory_db_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def api_client() -> Generator[TestClient, None, None]:
    """Create a FastAPI TestClient for integration tests."""
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_embedding() -> List[float]:
    """Provide a deterministic sample embedding vector."""
    return [round((i + 1) * 0.1, 2) for i in range(8)]


class StubDBSession:
    """
    Lightweight stub mimicking the subset of SQLAlchemy session API used in tests.
    """

    def __init__(self) -> None:
        self.added: List[Any] = []
        self.flushed: bool = False
        self.committed: bool = False
        self._queries: Dict[Any, List[Any]] = {}

    def add(self, obj: Any) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = len(self.added) + 1
        self.added.append(obj)

    def flush(self) -> None:
        self.flushed = True

    def commit(self) -> None:
        self.committed = True

    def refresh(self, obj: Any) -> None:  # pragma: no cover - no-op
        return

    def rollback(self) -> None:  # pragma: no cover - no-op
        return
    
    def begin_nested(self) -> "StubNestedTransaction":
        """Begin a nested transaction (savepoint)."""
        return StubNestedTransaction()

    # Helpers for configuring query behaviour in tests
    def add_query_result(self, model: Any, results: List[Any]) -> None:
        self._queries[model] = results

    def query(self, *models: Any) -> "StubQuery":
        """
        Query for one or more models.
        
        For single model: db.query(User)
        For joins: db.add_query_result((User, Profile), results)
        
        Args:
            models: One or more model classes to query
            
        Returns:
            StubQuery instance with configured results
        """
        query_key = models[0] if len(models) == 1 else models
        return StubQuery(self._queries.get(query_key, []))


class StubNestedTransaction:
    """Stub for nested transaction (savepoint) support."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False
    
    def commit(self) -> None:  # pragma: no cover - no-op
        pass
    
    def rollback(self) -> None:  # pragma: no cover - no-op
        pass


class StubQuery:
    """Simple iterable stub used for query chaining in tests."""

    def __init__(self, results: List[Any]) -> None:
        self._results = results
        self._filters: List[Any] = []

    def filter(self, *args: Any, **kwargs: Any) -> "StubQuery":
        return self

    def join(self, *args: Any, **kwargs: Any) -> "StubQuery":
        return self

    def first(self) -> Optional[Any]:
        return self._results[0] if self._results else None

    def all(self) -> List[Any]:
        return self._results

    def limit(self, *_args: Any, **_kwargs: Any) -> "StubQuery":
        return self

    def order_by(self, *_args: Any, **_kwargs: Any) -> "StubQuery":
        return self

    def count(self) -> int:
        return len(self._results)

    def group_by(self, *_args: Any, **_kwargs: Any) -> "StubQuery":
        return self

    def having(self, *_args: Any, **_kwargs: Any) -> "StubQuery":
        return self

    def outerjoin(self, *_args: Any, **_kwargs: Any) -> "StubQuery":
        return self

    def offset(self, *_args: Any, **_kwargs: Any) -> "StubQuery":
        return self

    def scalar(self) -> Any:
        """Return first element of first row or None."""
        return self._results[0] if self._results else 0

    def distinct(self, *_args: Any, **_kwargs: Any) -> "StubQuery":
        return self

    def one_or_none(self) -> Optional[Any]:
        """Return exactly one result or None."""
        return self._results[0] if self._results else None

    def one(self) -> Any:
        """Return exactly one result or raise."""
        if not self._results:
            raise Exception("No row found")
        if len(self._results) > 1:
            raise Exception("Multiple rows found")
        return self._results[0]

