"""
Chat router for /api/ask endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.models import get_db, TrainingSession, EmbeddingLink
from app.schemas.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services import (
    get_embedder,
    get_retriever,
    get_workflow_learner,
    WorkflowTracer,
    GeneratorService
)
from app.llm import get_llm_provider
from app.config import settings


router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question and get an AI-generated answer.
    
    This endpoint implements the complete RAG pipeline with workflow tracing:
    1. Embed the query
    2. Find similar past workflows (if available)
    3. Retrieve relevant knowledge chunks
    4. Generate answer using LLM
    5. Store complete workflow trace for training
    
    Args:
        request: Chat request with question
        db: Database session
        
    Returns:
        ChatResponse with answer and optional workflow trace
    """
    try:
        # Initialize workflow tracer (Phase 2.1)
        tracer = WorkflowTracer(request.question)
        
        # Get services
        embedder = get_embedder()
        retriever = get_retriever()
        workflow_learner = get_workflow_learner()
        llm_provider = get_llm_provider()
        generator = GeneratorService(llm_provider)
        
        # Step 1: Embed the query
        step_start = tracer.start_step("query_embedding")
        query_embedding = embedder.embed_text(request.question)
        tracer.end_step("query_embedding", step_start, {
            "embedding_dimension": len(query_embedding)
        })
        
        # Step 2: Find similar past workflows
        boost_chunk_ids = []
        if settings.WORKFLOW_EMBEDDING_ENABLED:
            step_start = tracer.start_step("workflow_search")
            similar_workflows = workflow_learner.find_similar_workflows(
                db=db,
                query_embedding=query_embedding,
                top_k=3,
                min_similarity=0.7,
                successful_only=True
            )
            tracer.end_step("workflow_search", step_start, {
                "similar_workflows_found": len(similar_workflows)
            })
            
            # Get chunk IDs to boost from similar workflows
            if similar_workflows:
                boost_chunk_ids = workflow_learner.get_successful_chunk_ids(
                    db=db,
                    workflow_vectors=similar_workflows
                )
        
        # Step 3: Retrieve relevant knowledge chunks
        step_start = tracer.start_step("retrieval")
        retrieval_results = retriever.retrieve_by_embedding(
            db=db,
            query_embedding=query_embedding,
            top_k=settings.TOP_K_RETRIEVAL,
            boost_chunk_ids=boost_chunk_ids if boost_chunk_ids else None,
            boost_factor=settings.WORKFLOW_BOOST_FACTOR if boost_chunk_ids else None
        )
        tracer.end_step("retrieval", step_start, {
            "chunks_retrieved": len(retrieval_results),
            "boosted_chunks": len(boost_chunk_ids) if boost_chunk_ids else 0
        })
        
        # Add retrieved chunks to tracer
        for result in retrieval_results:
            tracer.add_retrieved_chunk(
                chunk_id=result.chunk.id,
                repo_name=result.chunk.repo_name,
                file_path=result.chunk.file_path,
                section_title=result.chunk.section_title,
                content=result.chunk.content,
                similarity_score=result.similarity_score,
                rank_position=result.rank_position,
                accuracy_weight=result.chunk.accuracy_weight
            )
        
        # Step 4: Generate answer using LLM
        step_start = tracer.start_step("generation")
        tracer.set_llm_info(
            provider=generator.get_provider_name(),
            model=generator.get_model_name()
        )
        
        answer = generator.generate_answer(
            query=request.question,
            retrieval_results=retrieval_results,
            temperature=0.7,
            max_tokens=1000
        )
        tracer.end_step("generation", step_start, {
            "answer_length": len(answer)
        })
        
        # Step 5: Store training session with complete workflow trace
        reasoning_chain = tracer.build_reasoning_chain()
        
        # Build retrieved chunks JSON
        retrieved_chunks_json = [
            {
                "chunk_id": result.chunk.id,
                "repo_name": result.chunk.repo_name,
                "file_path": result.chunk.file_path,
                "similarity_score": result.similarity_score,
                "rank_position": result.rank_position
            }
            for result in retrieval_results
        ]
        
        # Create training session
        training_session = TrainingSession(
            query=request.question,
            response=answer,
            reasoning_chain=reasoning_chain.model_dump(),
            retrieved_chunks=retrieved_chunks_json,
            workflow_context=None,  # Can be extended with repo relationships
            llm_provider=generator.get_provider_name(),
            llm_model=generator.get_model_name(),
            generation_time_ms=reasoning_chain.total_time_ms,
            has_feedback=0,
            is_correct=None
        )
        
        db.add(training_session)
        db.flush()  # Get the ID
        
        # Create embedding links for tracking
        for result in retrieval_results:
            link = EmbeddingLink(
                session_id=training_session.id,
                chunk_id=result.chunk.id,
                similarity_score=result.similarity_score,
                rank_position=result.rank_position,
                was_useful=None  # Will be set by feedback
            )
            db.add(link)
        
        db.commit()
        db.refresh(training_session)
        
        # Extract source information
        sources = list(set([
            f"{result.chunk.repo_name}/{result.chunk.file_path}"
            for result in retrieval_results
        ]))
        
        # Build response
        response = ChatResponse(
            answer=answer,
            session_id=training_session.id,
            sources=sources
        )
        
        # Include reasoning chain if requested
        if request.include_trace:
            response.reasoning_chain = reasoning_chain
        
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )

