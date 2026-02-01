"""Routers for the Discovery module."""
from app.routers.sessions import router as sessions_router
from app.routers.uploads import router as uploads_router

__all__ = ["sessions_router", "uploads_router"]
