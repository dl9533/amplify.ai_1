# backend/tests/unit/modules/discovery/test_upload_repository.py
"""Unit tests for DiscoveryUploadRepository."""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.modules.discovery.repositories.upload_repository import (
    DiscoveryUploadRepository,
)
from app.modules.discovery.models.session import DiscoveryUpload


@pytest.mark.asyncio
async def test_create_upload(mock_db_session):
    """Should create upload with file metadata."""
    repo = DiscoveryUploadRepository(mock_db_session)
    session_id = uuid4()
    file_name = "employees.csv"
    file_url = "s3://bucket/employees.csv"
    row_count = 100
    column_mappings = {"role": "job_title", "department": "dept"}
    detected_schema = {"columns": ["role", "department", "count"]}

    upload = await repo.create(
        session_id=session_id,
        file_name=file_name,
        file_url=file_url,
        row_count=row_count,
        column_mappings=column_mappings,
        detected_schema=detected_schema,
    )

    assert upload.session_id == session_id
    assert upload.file_name == file_name
    assert upload.file_url == file_url
    assert upload.row_count == row_count
    assert upload.column_mappings == column_mappings
    assert upload.detected_schema == detected_schema
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_upload_without_optional_fields(mock_db_session):
    """Should create upload with only required fields."""
    repo = DiscoveryUploadRepository(mock_db_session)
    session_id = uuid4()
    file_name = "data.csv"
    file_url = "s3://bucket/data.csv"
    row_count = 50

    upload = await repo.create(
        session_id=session_id,
        file_name=file_name,
        file_url=file_url,
        row_count=row_count,
    )

    assert upload.session_id == session_id
    assert upload.file_name == file_name
    assert upload.file_url == file_url
    assert upload.row_count == row_count
    assert upload.column_mappings is None
    assert upload.detected_schema is None


@pytest.mark.asyncio
async def test_get_upload_by_id(mock_db_session):
    """Should retrieve upload by ID."""
    repo = DiscoveryUploadRepository(mock_db_session)
    upload_id = uuid4()
    session_id = uuid4()

    # Create a mock upload
    mock_upload = DiscoveryUpload(
        id=upload_id,
        session_id=session_id,
        file_name="test.csv",
        file_url="s3://bucket/test.csv",
        row_count=10,
    )

    # Configure mock to return upload
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_upload

    retrieved = await repo.get_by_id(upload_id)

    assert retrieved is not None
    assert retrieved.id == upload_id
    assert retrieved.session_id == session_id


@pytest.mark.asyncio
async def test_get_upload_by_id_not_found(mock_db_session):
    """Should return None when upload not found."""
    repo = DiscoveryUploadRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_uploads_by_session_id(mock_db_session):
    """Should retrieve all uploads for a session."""
    repo = DiscoveryUploadRepository(mock_db_session)
    session_id = uuid4()

    # Create mock uploads
    upload1 = DiscoveryUpload(
        id=uuid4(),
        session_id=session_id,
        file_name="file1.csv",
        file_url="s3://bucket/file1.csv",
        row_count=10,
    )
    upload2 = DiscoveryUpload(
        id=uuid4(),
        session_id=session_id,
        file_name="file2.csv",
        file_url="s3://bucket/file2.csv",
        row_count=20,
    )

    # Configure mock to return uploads
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [upload1, upload2]
    mock_result.scalars.return_value = mock_scalars

    uploads = await repo.get_by_session_id(session_id)

    assert len(uploads) == 2
    assert uploads[0].session_id == session_id
    assert uploads[1].session_id == session_id


@pytest.mark.asyncio
async def test_get_uploads_by_session_id_empty(mock_db_session):
    """Should return empty list when session has no uploads."""
    repo = DiscoveryUploadRepository(mock_db_session)

    # Configure mock to return empty list
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    uploads = await repo.get_by_session_id(uuid4())

    assert len(uploads) == 0


@pytest.mark.asyncio
async def test_update_column_mappings(mock_db_session):
    """Should update column mappings."""
    repo = DiscoveryUploadRepository(mock_db_session)
    upload_id = uuid4()

    # Create mock upload
    mock_upload = DiscoveryUpload(
        id=upload_id,
        session_id=uuid4(),
        file_name="test.csv",
        file_url="s3://bucket/test.csv",
        row_count=10,
        column_mappings=None,
    )

    # Configure mock to return upload
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_upload

    new_mappings = {"role": "job_title", "count": "headcount"}
    updated = await repo.update_column_mappings(upload_id, new_mappings)

    assert updated.column_mappings == new_mappings
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_column_mappings_not_found(mock_db_session):
    """Should return None when upload to update not found."""
    repo = DiscoveryUploadRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.update_column_mappings(uuid4(), {"role": "job"})
    assert result is None


@pytest.mark.asyncio
async def test_update_detected_schema(mock_db_session):
    """Should update detected schema."""
    repo = DiscoveryUploadRepository(mock_db_session)
    upload_id = uuid4()

    # Create mock upload
    mock_upload = DiscoveryUpload(
        id=upload_id,
        session_id=uuid4(),
        file_name="test.csv",
        file_url="s3://bucket/test.csv",
        row_count=10,
        detected_schema=None,
    )

    # Configure mock to return upload
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_upload

    new_schema = {"columns": ["role", "department"], "types": {"role": "string"}}
    updated = await repo.update_detected_schema(upload_id, new_schema)

    assert updated.detected_schema == new_schema
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_detected_schema_not_found(mock_db_session):
    """Should return None when upload to update not found."""
    repo = DiscoveryUploadRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.update_detected_schema(uuid4(), {"columns": []})
    assert result is None


@pytest.mark.asyncio
async def test_delete_upload(mock_db_session):
    """Should delete upload record."""
    repo = DiscoveryUploadRepository(mock_db_session)
    upload_id = uuid4()

    # Create mock upload
    mock_upload = DiscoveryUpload(
        id=upload_id,
        session_id=uuid4(),
        file_name="test.csv",
        file_url="s3://bucket/test.csv",
        row_count=10,
    )

    # Configure mock to return upload
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_upload

    result = await repo.delete(upload_id)

    assert result is True
    mock_db_session.delete.assert_called_once_with(mock_upload)
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_upload_not_found(mock_db_session):
    """Should return False when upload to delete not found."""
    repo = DiscoveryUploadRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.delete(uuid4())

    assert result is False
    mock_db_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_latest_upload_for_session(mock_db_session):
    """Should get most recent upload for session."""
    repo = DiscoveryUploadRepository(mock_db_session)
    session_id = uuid4()

    # Create mock upload (the latest one)
    mock_upload = DiscoveryUpload(
        id=uuid4(),
        session_id=session_id,
        file_name="latest.csv",
        file_url="s3://bucket/latest.csv",
        row_count=50,
    )

    # Configure mock to return upload
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_upload

    latest = await repo.get_latest_for_session(session_id)

    assert latest is not None
    assert latest.session_id == session_id
    assert latest.file_name == "latest.csv"


@pytest.mark.asyncio
async def test_get_latest_upload_for_session_no_uploads(mock_db_session):
    """Should return None when session has no uploads."""
    repo = DiscoveryUploadRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.get_latest_for_session(uuid4())
    assert result is None
