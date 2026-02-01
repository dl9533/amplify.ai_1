"""FastAPI dependency injection configuration."""
from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import async_session_maker
from app.repositories import (
    OnetRepository,
    SessionRepository,
    UploadRepository,
    RoleMappingRepository,
    AnalysisRepository,
)
from app.services.session_service import SessionService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


def get_onet_repository(db: AsyncSession) -> OnetRepository:
    """Get O*NET repository dependency."""
    return OnetRepository(db)


def get_session_repository(db: AsyncSession) -> SessionRepository:
    """Get session repository dependency."""
    return SessionRepository(db)


def get_upload_repository(db: AsyncSession) -> UploadRepository:
    """Get upload repository dependency."""
    return UploadRepository(db)


def get_role_mapping_repository(db: AsyncSession) -> RoleMappingRepository:
    """Get role mapping repository dependency."""
    return RoleMappingRepository(db)


def get_analysis_repository(db: AsyncSession) -> AnalysisRepository:
    """Get analysis repository dependency."""
    return AnalysisRepository(db)


def get_session_service_dep(
    repository: SessionRepository,
    user_id: UUID | None = None,
) -> SessionService:
    """Get session service dependency.

    Note: In production, user_id would be extracted from JWT token
    via an auth dependency.
    """
    return SessionService(repository=repository, user_id=user_id)
