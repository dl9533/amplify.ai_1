# discovery/tests/unit/services/test_upload_service_impl.py
"""Unit tests for implemented upload service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.exceptions import ValidationException


@pytest.mark.asyncio
async def test_process_upload():
    """Test process_upload creates record and parses file."""
    from app.services.upload_service import UploadService

    mock_repo = AsyncMock()
    mock_s3 = AsyncMock()
    mock_parser = MagicMock()

    mock_upload = MagicMock()
    mock_upload.id = uuid4()
    mock_upload.file_name = "test.csv"
    mock_upload.row_count = 10
    mock_upload.created_at = MagicMock()
    mock_upload.created_at.isoformat.return_value = "2026-02-01T00:00:00"
    mock_repo.create.return_value = mock_upload

    mock_s3.upload_file.return_value = {"url": "s3://bucket/key", "key": "key"}
    mock_parser.parse.return_value = {
        "row_count": 10,
        "detected_schema": {"columns": []},
        "column_suggestions": {"role": "job_title"},
        "preview": [],
    }

    service = UploadService(
        repository=mock_repo,
        s3_client=mock_s3,
        file_parser=mock_parser,
    )

    session_id = uuid4()
    result = await service.process_upload(
        session_id=session_id,
        file_name="test.csv",
        content=b"name,job_title\nJohn,Engineer",
    )

    assert result is not None
    assert "id" in result
    mock_repo.create.assert_called_once()
    mock_s3.upload_file.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_session_id():
    """Test get_by_session_id returns uploads."""
    from app.services.upload_service import UploadService

    mock_repo = AsyncMock()
    mock_upload = MagicMock()
    mock_upload.id = uuid4()
    mock_upload.file_name = "test.csv"
    mock_upload.row_count = 10
    mock_upload.detected_schema = {}
    mock_upload.column_mappings = {}
    mock_upload.created_at = MagicMock()
    mock_upload.created_at.isoformat.return_value = "2026-02-01T00:00:00"
    mock_repo.get_for_session.return_value = [mock_upload]

    service = UploadService(repository=mock_repo)
    result = await service.get_by_session_id(uuid4())

    assert len(result) == 1
    mock_repo.get_for_session.assert_called_once()


@pytest.mark.asyncio
async def test_update_column_mappings():
    """Test updating column mappings."""
    from app.services.upload_service import UploadService

    mock_repo = AsyncMock()
    mock_upload = MagicMock()
    mock_upload.id = uuid4()
    mock_upload.file_name = "test.csv"
    mock_upload.column_mappings = {"role": "job_title"}
    mock_repo.update_mappings.return_value = mock_upload

    service = UploadService(repository=mock_repo)
    result = await service.update_column_mappings(
        upload_id=mock_upload.id,
        mappings={"role": "job_title"}
    )

    assert result is not None
    assert result["column_mappings"]["role"] == "job_title"
    mock_repo.update_mappings.assert_called_once()


class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_sanitize_removes_path_traversal(self):
        """Test path traversal sequences are removed."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        service = UploadService(repository=mock_repo)

        result = service._sanitize_filename("../../../etc/passwd")
        assert result == "passwd"
        assert ".." not in result
        assert "/" not in result

    def test_sanitize_removes_backslash_path(self):
        """Test Windows-style backslashes are replaced with underscores."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        service = UploadService(repository=mock_repo)

        result = service._sanitize_filename("..\\..\\windows\\system32\\file.csv")
        # On Unix, backslashes are not path separators, but they get replaced with underscores
        assert "\\" not in result
        assert result.endswith("file.csv")

    def test_sanitize_removes_null_bytes(self):
        """Test null bytes are removed."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        service = UploadService(repository=mock_repo)

        result = service._sanitize_filename("file\x00.csv")
        assert result == "file.csv"
        assert "\x00" not in result

    def test_sanitize_truncates_long_names(self):
        """Test long filenames are truncated while preserving extension."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        service = UploadService(repository=mock_repo)

        long_name = "a" * 300 + ".csv"
        result = service._sanitize_filename(long_name)

        assert len(result) <= 255
        assert result.endswith(".csv")

    def test_sanitize_empty_result_raises(self):
        """Test empty filename after sanitization raises error."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        service = UploadService(repository=mock_repo)

        with pytest.raises(ValidationException, match="Invalid filename"):
            service._sanitize_filename("...")

    def test_sanitize_dot_dot_raises(self):
        """Test '..' filename raises error."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        service = UploadService(repository=mock_repo)

        with pytest.raises(ValidationException, match="Invalid filename"):
            service._sanitize_filename("..")

    def test_sanitize_removes_dangerous_chars(self):
        """Test dangerous characters are replaced."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        service = UploadService(repository=mock_repo)

        result = service._sanitize_filename('file<>:"|?*.csv')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result
        assert result.endswith(".csv")

    def test_sanitize_preserves_valid_filename(self):
        """Test valid filenames are preserved."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        service = UploadService(repository=mock_repo)

        result = service._sanitize_filename("my_data_file.csv")
        assert result == "my_data_file.csv"

    def test_sanitize_strips_leading_trailing_dots_spaces(self):
        """Test leading/trailing dots and spaces are stripped."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        service = UploadService(repository=mock_repo)

        result = service._sanitize_filename("  ..file.csv.. ")
        assert not result.startswith(".")
        assert not result.startswith(" ")
        assert not result.endswith(" ")


class TestFileSizeValidation:
    """Test file size validation."""

    @pytest.mark.asyncio
    async def test_oversized_file_raises_validation_error(self):
        """Test file exceeding max size raises ValidationException."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        mock_parser = MagicMock()
        mock_parser.parse.return_value = {
            "row_count": 10,
            "detected_schema": {"columns": []},
        }

        # Set max size to 1KB for testing
        service = UploadService(
            repository=mock_repo,
            file_parser=mock_parser,
            max_upload_size=1024,  # 1KB
        )

        # Try to upload 2KB file
        large_content = b"x" * 2048

        with pytest.raises(ValidationException, match="exceeds maximum"):
            await service.process_upload(
                session_id=uuid4(),
                file_name="large.csv",
                content=large_content,
            )

    @pytest.mark.asyncio
    async def test_file_within_size_limit_succeeds(self):
        """Test file within size limit is processed."""
        from app.services.upload_service import UploadService

        mock_repo = AsyncMock()
        mock_parser = MagicMock()

        mock_upload = MagicMock()
        mock_upload.id = uuid4()
        mock_upload.file_name = "small.csv"
        mock_upload.row_count = 1
        mock_upload.created_at = MagicMock()
        mock_upload.created_at.isoformat.return_value = "2026-02-01T00:00:00"
        mock_repo.create.return_value = mock_upload

        mock_parser.parse.return_value = {
            "row_count": 1,
            "detected_schema": {"columns": []},
            "column_suggestions": {},
            "preview": [],
        }

        # Set max size to 10KB
        service = UploadService(
            repository=mock_repo,
            file_parser=mock_parser,
            max_upload_size=10240,  # 10KB
        )

        # Upload 1KB file
        small_content = b"x" * 1024

        result = await service.process_upload(
            session_id=uuid4(),
            file_name="small.csv",
            content=small_content,
        )

        assert result is not None
        mock_repo.create.assert_called_once()
