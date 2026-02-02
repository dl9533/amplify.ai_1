# discovery/app/services/upload_service.py
"""Upload service for managing file uploads in discovery sessions."""
from typing import Any
from uuid import UUID

from app.repositories.upload_repository import UploadRepository
from app.services.s3_client import S3Client
from app.services.file_parser import FileParser


class UploadService:
    """Upload service backed by S3 storage and database."""

    def __init__(
        self,
        repository: UploadRepository,
        s3_client: S3Client | None = None,
        file_parser: FileParser | None = None,
    ) -> None:
        self.repository = repository
        self.s3_client = s3_client
        self.file_parser = file_parser or FileParser()

    async def process_upload(
        self,
        session_id: UUID,
        file_name: str,
        content: bytes,
    ) -> dict[str, Any]:
        """Process an uploaded file.

        Args:
            session_id: The session ID.
            file_name: Original filename.
            content: File content as bytes.

        Returns:
            Dict with upload metadata.
        """
        # Parse file to detect schema
        parse_result = self.file_parser.parse(content, file_name)

        # Upload to S3 if client available
        file_url = ""
        if self.s3_client:
            s3_result = await self.s3_client.upload_file(
                key=f"sessions/{session_id}/{file_name}",
                content=content,
                content_type=self._get_content_type(file_name),
            )
            file_url = s3_result["url"]

        # Create database record
        upload = await self.repository.create(
            session_id=session_id,
            file_name=file_name,
            file_url=file_url,
            row_count=parse_result["row_count"],
            column_mappings=None,
            detected_schema=parse_result["detected_schema"],
        )

        return {
            "id": str(upload.id),
            "file_name": upload.file_name,
            "row_count": upload.row_count,
            "detected_schema": parse_result["detected_schema"],
            "column_suggestions": parse_result.get("column_suggestions", {}),
            "preview": parse_result.get("preview", []),
            "created_at": upload.created_at.isoformat(),
        }

    async def get_by_session_id(self, session_id: UUID) -> list[dict[str, Any]]:
        """Get all uploads for a session."""
        uploads = await self.repository.get_for_session(session_id)
        return [
            {
                "id": str(u.id),
                "file_name": u.file_name,
                "row_count": u.row_count,
                "detected_schema": u.detected_schema,
                "column_mappings": u.column_mappings,
                "created_at": u.created_at.isoformat(),
            }
            for u in uploads
        ]

    async def update_column_mappings(
        self,
        upload_id: UUID,
        mappings: dict[str, str | None],
    ) -> dict[str, Any] | None:
        """Update column mappings for an upload."""
        upload = await self.repository.update_mappings(upload_id, mappings)
        if not upload:
            return None
        return {
            "id": str(upload.id),
            "file_name": upload.file_name,
            "column_mappings": upload.column_mappings,
        }

    async def get_file_content(self, upload_id: UUID) -> bytes | None:
        """Get file content from S3."""
        upload = await self.repository.get_by_id(upload_id)
        if not upload or not self.s3_client:
            return None

        key = f"sessions/{upload.session_id}/{upload.file_name}"
        return await self.s3_client.download_file(key)

    def _get_content_type(self, filename: str) -> str:
        """Get MIME type from filename."""
        ext = filename.lower().split(".")[-1]
        types = {
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xls": "application/vnd.ms-excel",
        }
        return types.get(ext, "application/octet-stream")


def get_upload_service() -> UploadService:
    """Dependency placeholder - will be replaced with DI."""
    raise NotImplementedError("Use dependency injection")
