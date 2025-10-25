"""
Services initialization.
"""

from app.services.embedder import EmbeddingService, get_embedder
from app.services.retriever import RetrieverService, RetrievalResult, get_retriever
from app.services.generator import GeneratorService
from app.services.workflow_tracer import WorkflowTracer
from app.services.workflow_learner import WorkflowLearner, get_workflow_learner

# Protocol definitions for type checking and testing
from app.services.protocols import (
    EmbedderProtocol,
    RetrieverProtocol,
    GeneratorProtocol,
    WorkflowTracerProtocol,
    WorkflowLearnerProtocol,
    AdminServiceProtocol,
    InspectorServiceProtocol,
)

__all__ = [
    # Concrete implementations
    "EmbeddingService",
    "get_embedder",
    "RetrieverService",
    "RetrievalResult",
    "get_retriever",
    "GeneratorService",
    "WorkflowTracer",
    "WorkflowLearner",
    "get_workflow_learner",
    # Protocol definitions
    "EmbedderProtocol",
    "RetrieverProtocol",
    "GeneratorProtocol",
    "WorkflowTracerProtocol",
    "WorkflowLearnerProtocol",
    "AdminServiceProtocol",
    "InspectorServiceProtocol",
]
