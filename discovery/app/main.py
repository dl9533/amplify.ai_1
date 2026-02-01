"""Main FastAPI application for the Discovery module."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

app = FastAPI(
    title="Discovery API",
    description="Opportunity Discovery module for AI agent identification",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
