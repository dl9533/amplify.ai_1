"""Discovery API - Main Application Entry Point.

FastAPI application for O*NET-powered opportunity discovery service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from discovery import __version__
from discovery.routes import health_router

app = FastAPI(
    title="Discovery API",
    description="O*NET-powered opportunity discovery service",
    version=__version__,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "Discovery API", "version": __version__}
