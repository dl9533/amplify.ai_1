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
    ActivitySelectionRepository,
    CandidateRepository,
)
from app.services.file_parser import FileParser
from app.services.s3_client import S3Client
from app.services.session_service import SessionService
from app.services.upload_service import UploadService
from app.services.role_mapping_service import RoleMappingService
from app.services.activity_service import ActivityService
from app.services.analysis_service import AnalysisService
from app.services.roadmap_service import RoadmapService
from app.services.chat_service import ChatService


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


def get_activity_selection_repository(db: AsyncSession) -> ActivitySelectionRepository:
    """Get activity selection repository dependency."""
    return ActivitySelectionRepository(db)


def get_candidate_repository(db: AsyncSession) -> CandidateRepository:
    """Get candidate repository dependency."""
    return CandidateRepository(db)


def get_role_mapping_service_dep(
    repository: RoleMappingRepository,
    onet_repository: OnetRepository,
) -> RoleMappingService:
    """Get role mapping service dependency."""
    return RoleMappingService(
        repository=repository,
        onet_repository=onet_repository,
    )


def get_activity_service_dep(
    repository: ActivitySelectionRepository,
    onet_repository: OnetRepository,
) -> ActivityService:
    """Get activity service dependency."""
    return ActivityService(
        repository=repository,
        onet_repository=onet_repository,
    )


def get_analysis_service_dep(
    repository: AnalysisRepository,
    onet_repository: OnetRepository,
) -> AnalysisService:
    """Get analysis service dependency."""
    return AnalysisService(
        repository=repository,
        onet_repository=onet_repository,
    )


def get_roadmap_service_dep(
    repository: CandidateRepository,
    analysis_repository: AnalysisRepository,
) -> RoadmapService:
    """Get roadmap service dependency."""
    return RoadmapService(
        repository=repository,
        analysis_repository=analysis_repository,
    )


def get_chat_service_dep(
    session_repository: SessionRepository,
) -> ChatService:
    """Get chat service dependency."""
    return ChatService(
        session_repository=session_repository,
    )
