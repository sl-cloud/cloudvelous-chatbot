"""
Inspector service layer for session embedding inspection.

This service handles the business logic for inspecting training sessions,
comparing sessions, and analyzing embeddings and workflows.
"""

import asyncio
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models import (
    TrainingSession,
    EmbeddingLink,
    KnowledgeChunk,
    TrainingFeedback,
    WorkflowVector
)
from app.schemas.inspector import (
    InspectorSessionResponse,
    InspectorChunkDetail,
    RetrievalStatistics,
    WorkflowTraceVisualization,
    WorkflowTraceStep,
    SimilarWorkflowPreview,
    InspectorComparisonResponse,
    ChunkOverlapAnalysis,
)
from app.services import get_embedder
from app.utils.logging import get_logger
from app.exceptions import SessionNotFoundError, EmbeddingOperationError


class InspectorService:
    """Service layer for inspection operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.log = get_logger(__name__)
    
    async def inspect_session(self, session_id: int) -> InspectorSessionResponse:
        """
        Get complete embedding inspection details for a training session.
        
        Args:
            session_id: Training session ID to inspect
            
        Returns:
            Complete session inspection data
            
        Raises:
            SessionNotFoundError: If session not found
        """
        self.log.info(f"Inspecting session {session_id}", session_id=session_id)
        
        # Get training session
        session = self.db.query(TrainingSession).filter(
            TrainingSession.id == session_id
        ).first()
        
        if not session:
            self.log.warning(f"Session {session_id} not found", session_id=session_id)
            raise SessionNotFoundError(
                f"Training session not found",
                details={"session_id": session_id}
            )
        
        # Get feedback if exists
        feedback = self.db.query(TrainingFeedback).filter(
            TrainingFeedback.session_id == session_id
        ).first()
        
        # Get embedding links with chunk details
        links = self.db.query(EmbeddingLink, KnowledgeChunk).join(
            KnowledgeChunk,
            EmbeddingLink.chunk_id == KnowledgeChunk.id
        ).filter(
            EmbeddingLink.session_id == session_id
        ).order_by(
            EmbeddingLink.rank_position
        ).all()
        
        # Build retrieved chunks
        retrieved_chunks = self._build_chunk_details(links)
        
        # Calculate retrieval statistics
        retrieval_statistics = self._calculate_retrieval_stats(links)
        
        # Parse workflow trace
        workflow_trace = self._parse_workflow_trace(session)
        
        # Find similar workflows
        similar_workflows = self._find_similar_workflows(session)
        
        # Build visualization metadata
        visualization_metadata = {
            "has_workflow_trace": workflow_trace is not None,
            "has_similar_workflows": len(similar_workflows) > 0,
            "total_steps": len(workflow_trace.steps) if workflow_trace else 0,
            "embedding_model": "all-MiniLM-L6-v2",
            "embedding_dimension": 384
        }
        
        return InspectorSessionResponse(
            session_id=session.id,
            query=session.query,
            response=session.response,
            created_at=session.created_at,
            llm_provider=session.llm_provider,
            llm_model=session.llm_model,
            generation_time_ms=session.generation_time_ms,
            has_feedback=session.has_feedback,
            is_correct=session.is_correct,
            feedback_type=feedback.feedback_type if feedback else None,
            feedback_notes=feedback.notes if feedback else None,
            retrieved_chunks=retrieved_chunks,
            retrieval_statistics=retrieval_statistics,
            reasoning_chain=session.reasoning_chain,
            workflow_trace=workflow_trace,
            similar_workflows=similar_workflows if similar_workflows else None,
            visualization_metadata=visualization_metadata
        )
    
    def _build_chunk_details(self, links) -> list:
        """Build detailed chunk information from embedding links."""
        retrieved_chunks = []
        
        for link, chunk in links:
            content_preview = (
                chunk.content[:300] + "..." 
                if len(chunk.content) > 300 
                else chunk.content
            )
            
            retrieved_chunks.append(InspectorChunkDetail(
                chunk_id=chunk.id,
                repo_name=chunk.repo_name,
                file_path=chunk.file_path,
                section_title=chunk.section_title,
                content=chunk.content,
                content_preview=content_preview,
                embedding_dimension=384,
                similarity_score=link.similarity_score,
                rank_position=link.rank_position,
                was_useful=link.was_useful,
                accuracy_weight=chunk.accuracy_weight,
                weight_history=None
            ))
        
        return retrieved_chunks
    
    def _calculate_retrieval_stats(self, links) -> RetrievalStatistics:
        """Calculate retrieval statistics from embedding links."""
        if not links:
            return RetrievalStatistics(
                total_chunks_retrieved=0,
                avg_similarity_score=0.0,
                min_similarity_score=0.0,
                max_similarity_score=0.0,
                chunks_marked_useful=0,
                chunks_marked_not_useful=0,
                chunks_without_feedback=0
            )
        
        similarity_scores = [link.similarity_score for link, _ in links]
        useful_count = sum(1 for link, _ in links if link.was_useful == 1)
        not_useful_count = sum(1 for link, _ in links if link.was_useful == 0)
        no_feedback_count = sum(1 for link, _ in links if link.was_useful is None)
        
        return RetrievalStatistics(
            total_chunks_retrieved=len(links),
            avg_similarity_score=sum(similarity_scores) / len(similarity_scores),
            min_similarity_score=min(similarity_scores),
            max_similarity_score=max(similarity_scores),
            chunks_marked_useful=useful_count,
            chunks_marked_not_useful=not_useful_count,
            chunks_without_feedback=no_feedback_count
        )
    
    def _parse_workflow_trace(
        self,
        session: TrainingSession
    ) -> Optional[WorkflowTraceVisualization]:
        """Parse workflow trace from reasoning chain."""
        if not session.reasoning_chain:
            return None
        
        try:
            reasoning_chain = session.reasoning_chain
            steps = []
            
            if isinstance(reasoning_chain, dict) and "steps" in reasoning_chain:
                for step in reasoning_chain["steps"]:
                    steps.append(WorkflowTraceStep(
                        step_name=step.get("step_name", "unknown"),
                        duration_ms=step.get("duration_ms"),
                        metadata=step.get("metadata")
                    ))
            
            # Calculate timing breakdowns
            query_embedding_time = next(
                (s.duration_ms for s in steps if s.step_name == "query_embedding"),
                None
            )
            retrieval_time = next(
                (s.duration_ms for s in steps if s.step_name == "retrieval"),
                None
            )
            generation_time = next(
                (s.duration_ms for s in steps if s.step_name == "generation"),
                None
            )
            workflow_search_time = next(
                (s.duration_ms for s in steps if s.step_name == "workflow_search"),
                None
            )
            
            total_duration = sum(s.duration_ms for s in steps if s.duration_ms is not None)
            
            return WorkflowTraceVisualization(
                total_duration_ms=total_duration,
                steps=steps,
                query_embedding_time_ms=query_embedding_time,
                retrieval_time_ms=retrieval_time,
                generation_time_ms=generation_time,
                workflow_search_time_ms=workflow_search_time
            )
        except (KeyError, ValueError, TypeError) as e:
            self.log.warning(
                "Failed to parse workflow trace - using None",
                error=str(e),
                exc_info=True
            )
            return None
    
    def _find_similar_workflows(
        self,
        session: TrainingSession
    ) -> list:
        """Find similar workflows that influenced this session."""
        similar_workflows = []
        
        if not session.reasoning_chain or not isinstance(session.reasoning_chain, dict):
            return similar_workflows
        
        workflow_metadata = session.reasoning_chain.get("workflow_metadata", {})
        similar_workflow_ids = workflow_metadata.get("similar_workflows", [])
        
        if not similar_workflow_ids:
            return similar_workflows
        
        for wf_id in similar_workflow_ids[:5]:  # Limit to 5 for UI
            workflow_vector = self.db.query(WorkflowVector).filter(
                WorkflowVector.id == wf_id
            ).first()
            
            if not workflow_vector:
                continue
            
            orig_session = self.db.query(TrainingSession).filter(
                TrainingSession.id == workflow_vector.session_id
            ).first()
            
            if not orig_session:
                continue
            
            query_preview = (
                orig_session.query[:100] + "..." 
                if len(orig_session.query) > 100 
                else orig_session.query
            )
            
            similar_workflows.append(SimilarWorkflowPreview(
                workflow_id=workflow_vector.id,
                session_id=workflow_vector.session_id,
                similarity_score=workflow_metadata.get(
                    "similarity_scores", {}
                ).get(str(wf_id), 0.0),
                query_preview=query_preview,
                was_successful=workflow_vector.is_successful == 1,
                chunks_influenced=[]  # Would require tracking in Phase 4
            ))
        
        return similar_workflows
    
    async def compare_sessions(
        self,
        session_id_1: int,
        session_id_2: int,
        include_chunk_overlap: bool = True
    ) -> InspectorComparisonResponse:
        """
        Compare two training sessions side-by-side.
        
        Args:
            session_id_1: First session ID
            session_id_2: Second session ID
            include_chunk_overlap: Whether to analyze chunk overlap
            
        Returns:
            Comparison analysis of both sessions
        """
        self.log.info(
            f"Comparing sessions {session_id_1} and {session_id_2}",
            session_1=session_id_1,
            session_2=session_id_2
        )
        
        # Get both sessions
        session_1 = await self.inspect_session(session_id_1)
        session_2 = await self.inspect_session(session_id_2)
        
        # Calculate chunk overlap if requested
        chunk_overlap = None
        if include_chunk_overlap:
            chunk_overlap = self._analyze_chunk_overlap(session_1, session_2)
        
        # Calculate query similarity
        query_similarity = await self._calculate_query_similarity(
            session_1.query,
            session_2.query
        )
        
        # Build differences summary
        differences = self._build_differences_summary(session_1, session_2)
        
        return InspectorComparisonResponse(
            session_1=session_1,
            session_2=session_2,
            query_similarity=query_similarity,
            response_similarity=None,  # TODO: Implement in Phase 4
            chunk_overlap=chunk_overlap,
            differences=differences
        )
    
    def _analyze_chunk_overlap(
        self,
        session_1: InspectorSessionResponse,
        session_2: InspectorSessionResponse
    ) -> ChunkOverlapAnalysis:
        """Analyze chunk overlap between two sessions."""
        chunks_1 = set(c.chunk_id for c in session_1.retrieved_chunks)
        chunks_2 = set(c.chunk_id for c in session_2.retrieved_chunks)
        
        common = chunks_1.intersection(chunks_2)
        only_1 = chunks_1.difference(chunks_2)
        only_2 = chunks_2.difference(chunks_1)
        
        total_unique = len(chunks_1.union(chunks_2))
        overlap_pct = (len(common) / total_unique * 100) if total_unique > 0 else 0.0
        
        return ChunkOverlapAnalysis(
            common_chunks=list(common),
            only_in_session_1=list(only_1),
            only_in_session_2=list(only_2),
            overlap_percentage=round(overlap_pct, 2)
        )
    
    async def _calculate_query_similarity(
        self,
        query1: str,
        query2: str
    ) -> Optional[float]:
        """Calculate similarity between two queries using embeddings."""
        try:
            embedder = get_embedder()
            
            # Run blocking embedding operations in parallel
            query_1_emb, query_2_emb = await asyncio.gather(
                asyncio.to_thread(embedder.embed_text, query1),
                asyncio.to_thread(embedder.embed_text, query2)
            )
            
            query_similarity = await asyncio.to_thread(
                lambda: float(embedder.cosine_similarity(query_1_emb, query_2_emb))
            )
            
            return query_similarity
        except (ValueError, TypeError, RuntimeError) as e:
            # Embedding-specific errors
            self.log.warning(
                "Embedding operation failed during similarity calculation",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return None
        except Exception as e:
            # Unexpected errors
            self.log.error(
                "Unexpected error calculating query similarity",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return None
    
    def _build_differences_summary(
        self,
        session_1: InspectorSessionResponse,
        session_2: InspectorSessionResponse
    ) -> dict:
        """Build summary of differences between sessions."""
        return {
            "llm_provider_differs": session_1.llm_provider != session_2.llm_provider,
            "llm_model_differs": session_1.llm_model != session_2.llm_model,
            "correctness_differs": session_1.is_correct != session_2.is_correct,
            "generation_time_diff_ms": (
                (session_1.generation_time_ms or 0) - (session_2.generation_time_ms or 0)
            ),
            "chunks_retrieved_diff": (
                session_1.retrieval_statistics.total_chunks_retrieved -
                session_2.retrieval_statistics.total_chunks_retrieved
            ),
            "avg_similarity_diff": round(
                session_1.retrieval_statistics.avg_similarity_score -
                session_2.retrieval_statistics.avg_similarity_score,
                4
            )
        }

