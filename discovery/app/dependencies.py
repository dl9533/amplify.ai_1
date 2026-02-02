"""FastAPI dependency injection configuration."""
from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.base import async_session_maker
from app.repositories import (
    OnetRepository,
    SessionRepository,
    UploadRepository,
    RoleMappingRepository,
    AnalysisRepository,
)
from app.services.file_parser import FileParser
from app.services.s3_client import S3Client
from app.services.session_service import SessionService
from app.services.upload_service import UploadService


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


def get_s3_client() -> S3Client:
    """Get S3 client dependency."""
    settings = get_settings()
    return S3Client(
        endpoint_url=settings.s3_endpoint_url,
        bucket=settings.s3_bucket,
        access_key=settings.aws_access_key_id,
        secret_key=settings.aws_secret_access_key.get_secret_value() if settings.aws_secret_access_key else None,
        region=settings.aws_region,
    )


def get_file_parser() -> FileParser:
    """Get file parser dependency."""
    return FileParser()


def get_upload_service_dep(
    repository: UploadRepository,
    s3_client: S3Client,
    file_parser: FileParser,
) -> UploadService:
    """Get upload service dependency."""
    return UploadService(
        repository=repository,
        s3_client=s3_client,
        file_parser=file_parser,
    )
