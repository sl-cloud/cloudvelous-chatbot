"""Root conftest.py to set up test environment before any imports."""

import sys
import types
from typing import Any, List

# Set up stub modules BEFORE any app imports
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
            def __init__(self, api_key: str = None) -> None:
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


# Run stub setup immediately when conftest is imported
_ensure_stub_modules()

