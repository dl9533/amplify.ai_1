"""Main FastAPI application for the Discovery module."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware.error_handler import add_exception_handlers
from app.middleware.session_save import AutoSaveMiddleware
from app.routers import (
    activities_router,
    analysis_router,
    chat_router,
    exports_router,
    handoff_router,
    roadmap_router,
    role_mappings_router,
    sessions_router,
    uploads_router,
)

logger = logging.getLogger(__name__)

# Global middleware instance for dependency injection
_auto_save_middleware: AutoSaveMiddleware | None = None


def get_auto_save_middleware() -> AutoSaveMiddleware | None:
    """Get the auto-save middleware instance."""
    return _auto_save_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Handles startup and shutdown events, including flushing
    pending session saves on shutdown.
    """
    global _auto_save_middleware

    # Startup: Initialize auto-save middleware
    # Note: In production, SessionService would be properly initialized with DB session
    # For now, we initialize with a placeholder that can be replaced via dependency injection
    logger.info("Starting Discovery API")
    yield

    # Shutdown: Flush any pending session saves
    if _auto_save_middleware is not None:
        try:
            count = await _auto_save_middleware.flush_pending_saves()
            if count > 0:
                logger.info(f"Flushed {count} pending session saves on shutdown")
        except Exception as e:
            logger.error(f"Error flushing pending saves on shutdown: {e}")
    logger.info("Shutting down Discovery API")


app = FastAPI(
    title="Discovery API",
    description="Opportunity Discovery module for AI agent identification",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - configured from environment
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_methods_list,
    allow_headers=settings.cors_headers_list,
)

# Register exception handlers
add_exception_handlers(app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Register all routers
app.include_router(sessions_router)
app.include_router(uploads_router)
app.include_router(role_mappings_router)
app.include_router(activities_router)
app.include_router(analysis_router)
app.include_router(roadmap_router)
app.include_router(chat_router)
app.include_router(exports_router)
app.include_router(handoff_router)
