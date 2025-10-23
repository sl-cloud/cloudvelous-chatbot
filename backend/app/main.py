"""
Cloudvelous Chat Assistant - FastAPI Application Entry Point

This is a placeholder that will be fully implemented in Phase 1.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.
    
    This replaces the deprecated @app.on_event decorators with the
    modern lifespan context manager pattern.
    """
    # Startup
    print("🚀 Cloudvelous Chat Assistant starting...")
    print("✅ Phase 0: Environment & Infrastructure - Complete")
    print("✅ Phase 1: Core Infrastructure - Complete")
    print("✅ Phase 2: Workflow Reasoning Capture - Complete")
    
    yield  # Application runs here
    
    # Shutdown
    print("👋 Cloudvelous Chat Assistant shutting down...")


# Create FastAPI application with lifespan manager
app = FastAPI(
    title="Cloudvelous Chat Assistant",
    description="Intelligent chatbot powered by RAG with workflow learning",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Cloudvelous Chat Assistant API",
        "version": "0.2.0",
        "status": "Phase 2 Complete - Workflow Reasoning Capture Ready",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


# Include routers
from app.routers.chat import router as chat_router
from app.routers.training import router as training_router

app.include_router(chat_router)
app.include_router(training_router)

# TODO: Add remaining routers in future phases
# app.include_router(questions.router)
# app.include_router(workflows.router)
# app.include_router(admin.router)
# app.include_router(inspector.router)

