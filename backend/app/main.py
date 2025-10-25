"""
Cloudvelous Chat Assistant - FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.utils.logging import configure_logging, add_request_id_middleware, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.

    This replaces the deprecated @app.on_event decorators with the
    modern lifespan context manager pattern.
    """
    # Configure logging
    configure_logging(log_level=settings.LOG_LEVEL, json_logs=settings.LOG_JSON)
    log = get_logger(__name__)

    # Startup
    log.info("🚀 Cloudvelous Chat Assistant starting...", version="0.3.0", phase="3")
    log.info("✅ Phase 0: Environment & Infrastructure - Complete")
    log.info("✅ Phase 1: Core Infrastructure - Complete")
    log.info("✅ Phase 2: Workflow Reasoning Capture - Complete")
    log.info("🚧 Phase 3: Admin Training Interface API - In Progress")
    log.info(f"Log level: {settings.LOG_LEVEL}, JSON logs: {settings.LOG_JSON}")
    log.info(f"CORS origins: {settings.CORS_ORIGINS}")

    yield  # Application runs here

    # Shutdown
    log.info("👋 Cloudvelous Chat Assistant shutting down...")


# Create FastAPI application with lifespan manager
app = FastAPI(
    title="Cloudvelous Chat Assistant",
    description="Intelligent chatbot powered by RAG with workflow learning and admin training interface",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure rate limiting to prevent DoS attacks
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add request ID middleware
app.middleware("http")(add_request_id_middleware)

# Configure CORS with environment-based origins
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"]
cors_methods = settings.CORS_ALLOW_METHODS.split(",")
cors_headers = settings.CORS_ALLOW_HEADERS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
    expose_headers=["X-Request-ID"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    log = get_logger(__name__)
    log.debug("Root endpoint accessed")
    return {
        "message": "Cloudvelous Chat Assistant API",
        "version": "0.3.0",
        "status": "Phase 3 In Progress - Admin Training Interface API",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    log = get_logger(__name__)
    log.debug("Health check endpoint accessed")
    return {
        "status": "healthy",
        "version": "0.3.0",
        "phase": "3",
    }


# Include routers
from app.routers.chat import router as chat_router
from app.routers.training import router as training_router
from app.routers.inspector import router as inspector_router
from app.routers.admin import router as admin_router
from app.routers.workflows import router as workflows_router

# Phase 2 routers
app.include_router(chat_router)
app.include_router(training_router)

# Phase 3 routers (Admin Training Interface)
app.include_router(inspector_router)
app.include_router(admin_router)
app.include_router(workflows_router)

# TODO: Add remaining routers in future phases
# app.include_router(questions.router)

