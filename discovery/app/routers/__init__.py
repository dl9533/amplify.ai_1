"""Routers for the Discovery module."""
from app.routers.activities import router as activities_router
from app.routers.admin import router as admin_router
from app.routers.analysis import router as analysis_router
from app.routers.chat import router as chat_router
from app.routers.exports import router as exports_router
from app.routers.handoff import router as handoff_router
from app.routers.roadmap import router as roadmap_router
from app.routers.role_mappings import router as role_mappings_router
from app.routers.sessions import router as sessions_router
from app.routers.uploads import router as uploads_router

__all__ = [
    "activities_router",
    "admin_router",
    "analysis_router",
    "chat_router",
    "exports_router",
    "handoff_router",
    "roadmap_router",
    "role_mappings_router",
    "sessions_router",
    "uploads_router",
]
