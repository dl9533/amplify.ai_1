"""Discovery upload repository for database operations.

Provides the DiscoveryUploadRepository for managing discovery upload
records including CRUD operations and session-specific queries.
"""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.discovery.models.session import DiscoveryUpload


class DiscoveryUploadRepository:
    """Repository for DiscoveryUpload CRUD and query operations.

    Provides async database operations for discovery uploads including:
    - Create new uploads with file metadata
    - Retrieve uploads by ID or session ID
    - Update column mappings and detected schema
    - Delete uploads
    - Get the most recent upload for a session
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def create(
        self,
        session_id: UUID,
        file_name: str,
        file_url: str,
        row_count: int,
        column_mappings: dict | None = None,
        detected_schema: dict | None = None,
    ) -> DiscoveryUpload:
        """Create a new discovery upload.

        Creates an upload record with file metadata and optional
        column mappings and detected schema.

        Args:
            session_id: UUID of the discovery session this upload belongs to.
            file_name: Name of the uploaded file.
            file_url: URL where the file is stored (e.g., S3 URL).
            row_count: Number of rows in the uploaded file.
            column_mappings: Optional dict mapping source columns to target fields.
            detected_schema: Optional dict describing the detected file schema.

        Returns:
            The created DiscoveryUpload instance.
        """
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
        """Retrieve a discovery upload by its ID.

        Args:
            upload_id: UUID of the upload to retrieve.

        Returns:
            DiscoveryUpload if found, None otherwise.
        """
        stmt = select(DiscoveryUpload).where(DiscoveryUpload.id == upload_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_session_id(self, session_id: UUID) -> list[DiscoveryUpload]:
        """Retrieve all uploads for a specific session.

        Args:
            session_id: UUID of the session whose uploads to retrieve.

        Returns:
            List of DiscoveryUpload instances for the session.
        """
        stmt = select(DiscoveryUpload).where(DiscoveryUpload.session_id == session_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_column_mappings(
        self,
        upload_id: UUID,
        column_mappings: dict,
    ) -> DiscoveryUpload | None:
        """Update the column mappings for an upload.

        Args:
            upload_id: UUID of the upload to update.
            column_mappings: New column mappings dict.

        Returns:
            Updated DiscoveryUpload if found, None otherwise.
        """
        upload = await self.get_by_id(upload_id)
        if upload is None:
            return None

        upload.column_mappings = column_mappings
        await self.session.commit()
        await self.session.refresh(upload)
        return upload

    async def update_detected_schema(
        self,
        upload_id: UUID,
        detected_schema: dict,
    ) -> DiscoveryUpload | None:
        """Update the detected schema for an upload.

        Args:
            upload_id: UUID of the upload to update.
            detected_schema: New detected schema dict.

        Returns:
            Updated DiscoveryUpload if found, None otherwise.
        """
        upload = await self.get_by_id(upload_id)
        if upload is None:
            return None

        upload.detected_schema = detected_schema
        await self.session.commit()
        await self.session.refresh(upload)
        return upload

    async def delete(self, upload_id: UUID) -> bool:
        """Delete a discovery upload by its ID.

        Args:
            upload_id: UUID of the upload to delete.

        Returns:
            True if the upload was deleted, False if not found.
        """
        upload = await self.get_by_id(upload_id)
        if upload is None:
            return False

        await self.session.delete(upload)
        await self.session.commit()
        return True

    async def get_latest_for_session(self, session_id: UUID) -> DiscoveryUpload | None:
        """Retrieve the most recent upload for a session.

        Orders by created_at descending and returns the first result.

        Args:
            session_id: UUID of the session whose latest upload to retrieve.

        Returns:
            Most recent DiscoveryUpload for the session if any exist, None otherwise.
        """
        stmt = (
            select(DiscoveryUpload)
            .where(DiscoveryUpload.session_id == session_id)
            .order_by(desc(DiscoveryUpload.created_at))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
