#!/usr/bin/env python3
"""Initialize the database by creating all tables."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.models.base import Base

# Import all models to ensure they're registered with Base
from app.models import (  # noqa: F401
    onet_occupation,
    onet_work_activities,
    onet_task,
    onet_skills,
    discovery_session,
    discovery_upload,
    discovery_role_mapping,
    discovery_activity_selection,
    discovery_analysis,
    agentification_candidate,
    agent_memory,
)


async def init_db():
    """Create all database tables."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=True)

    print(f"Connecting to: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")

    async with engine.begin() as conn:
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
