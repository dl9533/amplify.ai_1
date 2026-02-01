"""Routers for the Discovery module."""
from app.routers.role_mappings import router as role_mappings_router
from app.routers.sessions import router as sessions_router
from app.routers.uploads import router as uploads_router

__all__ = ["role_mappings_router", "sessions_router", "uploads_router"]
