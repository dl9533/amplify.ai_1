# discovery/tests/unit/services/test_upload_service_impl.py
"""Unit tests for implemented upload service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


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
