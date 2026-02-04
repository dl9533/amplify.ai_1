# discovery/app/services/upload_service.py
"""Upload service for managing file uploads in discovery sessions."""
import logging
import re
from pathlib import Path
from typing import Any
from uuid import UUID

from app.exceptions import ValidationException
from app.repositories.upload_repository import UploadRepository
from app.services.s3_client import S3Client
from app.services.file_parser import FileParser

logger = logging.getLogger(__name__)

# Default max upload size in bytes (50MB)
DEFAULT_MAX_UPLOAD_SIZE = 50 * 1024 * 1024


class UploadService:
    """Upload service backed by S3 storage and database."""

    def __init__(
        self,
        repository: UploadRepository,
        s3_client: S3Client | None = None,
        file_parser: FileParser | None = None,
        max_upload_size: int = DEFAULT_MAX_UPLOAD_SIZE,
    ) -> None:
        self.repository = repository
        self.s3_client = s3_client
        self.file_parser = file_parser or FileParser()
        self.max_upload_size = max_upload_size

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

        Raises:
            ValidationException: If file is too large or filename is invalid.
        """
        # Validate file size
        if len(content) > self.max_upload_size:
            max_mb = self.max_upload_size / (1024 * 1024)
            raise ValidationException(
                f"File size exceeds maximum allowed size of {max_mb:.0f}MB",
                details={"max_size_mb": max_mb, "actual_size_mb": len(content) / (1024 * 1024)},
            )

        # Sanitize filename to prevent path traversal
        safe_file_name = self._sanitize_filename(file_name)
        logger.debug("Processing upload: original='%s', sanitized='%s'", file_name, safe_file_name)

        # Parse file to detect schema
        parse_result = self.file_parser.parse(content, safe_file_name)

        # Upload to S3 if client available
        file_url = ""
        if self.s3_client:
            # Use sanitized filename in S3 key
            s3_key = f"sessions/{session_id}/{safe_file_name}"
            s3_result = await self.s3_client.upload_file(
                key=s3_key,
                content=content,
                content_type=self._get_content_type(safe_file_name),
            )
            file_url = s3_result["url"]

        # Create database record (store original filename for display)
        upload = await self.repository.create(
            session_id=session_id,
            file_name=safe_file_name,
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
        ext = Path(filename).suffix.lower().lstrip(".")
        types = {
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "xls": "application/vnd.ms-excel",
        }
        return types.get(ext, "application/octet-stream")

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal and other attacks.

        Args:
            filename: Original filename from user.

        Returns:
            Safe filename with only the base name, no path components.

        Raises:
            ValidationException: If filename is invalid or empty after sanitization.
        """
        # Extract only the filename component (no directory path)
        safe_name = Path(filename).name

        # Remove any remaining path separators and null bytes
        safe_name = safe_name.replace("/", "_").replace("\\", "_").replace("\x00", "")

        # Remove leading/trailing dots and spaces
        safe_name = safe_name.strip(". ")

        # Replace potentially dangerous characters
        safe_name = re.sub(r'[<>:"|?*]', "_", safe_name)

        # Ensure we have a valid filename
        if not safe_name or safe_name in (".", ".."):
            raise ValidationException(
                "Invalid filename",
                details={"original_filename": filename},
            )

        # Limit filename length
        max_length = 255
        if len(safe_name) > max_length:
            # Preserve extension while truncating
            path = Path(safe_name)
            ext = path.suffix
            name = path.stem[:max_length - len(ext)]
            safe_name = name + ext

        return safe_name


from collections.abc import AsyncGenerator


async def get_upload_service() -> AsyncGenerator[UploadService, None]:
    """Get upload service dependency for FastAPI.

    Yields a fully configured UploadService with S3 client and file parser.
    """
    from app.config import get_settings
    from app.models.base import async_session_maker
    from app.repositories.upload_repository import UploadRepository
    from app.services.s3_client import S3Client
    from app.services.file_parser import FileParser

    settings = get_settings()

    s3_client = S3Client(
        endpoint_url=settings.s3_endpoint_url,
        bucket=settings.s3_bucket,
        access_key=settings.aws_access_key_id,
        secret_key=settings.aws_secret_access_key.get_secret_value() if settings.aws_secret_access_key else None,
        region=settings.aws_region,
    )
    file_parser = FileParser()

    # Calculate max upload size from settings (MB to bytes)
    max_upload_size = settings.max_upload_size_mb * 1024 * 1024

    async with async_session_maker() as db:
        repository = UploadRepository(db)
        service = UploadService(
            repository=repository,
            s3_client=s3_client,
            file_parser=file_parser,
            max_upload_size=max_upload_size,
        )
        yield service
