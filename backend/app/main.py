"""
Cloudvelous Chat Assistant - FastAPI Application Entry Point

This is a placeholder that will be fully implemented in Phase 1.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI application
app = FastAPI(
    title="Cloudvelous Chat Assistant",
    description="Intelligent chatbot powered by RAG with workflow learning",
    version="0.1.0",
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


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    print("🚀 Cloudvelous Chat Assistant starting...")
    print("✅ Phase 0: Environment & Infrastructure - Complete")
    print("✅ Phase 1: Core Infrastructure - Complete")
    print("✅ Phase 2: Workflow Reasoning Capture - Complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    print("👋 Cloudvelous Chat Assistant shutting down...")


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

