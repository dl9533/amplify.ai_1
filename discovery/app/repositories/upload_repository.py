"""Discovery upload repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_upload import DiscoveryUpload


class UploadRepository:
    """Repository for discovery upload operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        session_id: UUID,
        file_name: str,
        file_url: str,
        row_count: int | None = None,
        column_mappings: dict | None = None,
        detected_schema: dict | None = None,
    ) -> DiscoveryUpload:
        """Create a new upload record."""
        upload = DiscoveryUpload(
            session_id=session_id,
            file_name=file_name,
            file_url=file_url,
            row_count=row_count,
            column_mappings=column_mappings,
            detected_schema=detected_schema,
        )
        self.session.add(upload)
        await self.session.commit()
        await self.session.refresh(upload)
        return upload

    async def get_by_id(self, upload_id: UUID) -> DiscoveryUpload | None:
        """Get upload by ID."""
        stmt = select(DiscoveryUpload).where(DiscoveryUpload.id == upload_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_session(
        self,
        session_id: UUID,
    ) -> Sequence[DiscoveryUpload]:
        """Get all uploads for a session."""
        stmt = (
            select(DiscoveryUpload)
            .where(DiscoveryUpload.session_id == session_id)
            .order_by(DiscoveryUpload.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_mappings(
        self,
        upload_id: UUID,
        column_mappings: dict,
    ) -> DiscoveryUpload | None:
        """Update column mappings for an upload."""
        upload = await self.get_by_id(upload_id)
        if upload:
            upload.column_mappings = column_mappings
            await self.session.commit()
            await self.session.refresh(upload)
        return upload
