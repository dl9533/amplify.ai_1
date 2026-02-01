# backend/tests/unit/modules/discovery/test_onet_sync.py
"""Unit tests for O*NET sync job service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.discovery.services.onet_sync import OnetSyncJob


@pytest.fixture
def mock_onet_client():
    return AsyncMock()


@pytest.fixture
def mock_occupation_repo():
    return AsyncMock()


@pytest.fixture
def sync_job(mock_onet_client, mock_occupation_repo):
    return OnetSyncJob(
        onet_client=mock_onet_client,
        occupation_repo=mock_occupation_repo
    )


@pytest.mark.asyncio
async def test_sync_fetches_all_occupations(sync_job, mock_onet_client):
    """Sync should fetch all O*NET occupations."""
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Software Developers"}
    ]

    await sync_job.sync_occupations()

    mock_onet_client.search_occupations.assert_called()


@pytest.mark.asyncio
async def test_sync_upserts_occupations(sync_job, mock_onet_client, mock_occupation_repo):
    """Sync should upsert occupations to database."""
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Software Developers"}
    ]

    await sync_job.sync_occupations()

    mock_occupation_repo.upsert.assert_called()


@pytest.mark.asyncio
async def test_sync_handles_api_errors(sync_job, mock_onet_client):
    """Sync should handle API errors gracefully."""
    mock_onet_client.search_occupations.side_effect = Exception("API Error")

    # Should not raise, should log error
    result = await sync_job.sync_occupations()
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_sync_tracks_progress(sync_job, mock_onet_client):
    """Sync should track and report progress."""
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Dev1"},
        {"code": "15-1251.00", "title": "Dev2"},
    ]

    result = await sync_job.sync_occupations()

    assert "processed_count" in result
    assert result["processed_count"] == 2


@pytest.mark.asyncio
async def test_sync_handles_empty_results(sync_job, mock_onet_client):
    """Sync should handle empty API results gracefully."""
    mock_onet_client.search_occupations.return_value = []

    result = await sync_job.sync_occupations()

    assert result["success"] is True
    assert result["processed_count"] == 0
    assert result["skipped_count"] == 0


@pytest.mark.asyncio
async def test_sync_skips_occupation_missing_code(sync_job, mock_onet_client, mock_occupation_repo):
    """Sync should skip occupations missing code and log warning."""
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Software Developers"},
        {"title": "Missing Code Occupation"},  # Missing code
    ]

    with patch("app.modules.discovery.services.onet_sync.logger") as mock_logger:
        result = await sync_job.sync_occupations()

        assert result["success"] is True
        assert result["processed_count"] == 1
        assert result["skipped_count"] == 1
        mock_logger.warning.assert_called_once()
        assert "Skipping occupation" in mock_logger.warning.call_args[0][0]

    # Should only upsert the valid one
    assert mock_occupation_repo.upsert.call_count == 1


@pytest.mark.asyncio
async def test_sync_skips_occupation_missing_title(sync_job, mock_onet_client, mock_occupation_repo):
    """Sync should skip occupations missing title and log warning."""
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Software Developers"},
        {"code": "15-1251.00"},  # Missing title
    ]

    with patch("app.modules.discovery.services.onet_sync.logger") as mock_logger:
        result = await sync_job.sync_occupations()

        assert result["success"] is True
        assert result["processed_count"] == 1
        assert result["skipped_count"] == 1
        mock_logger.warning.assert_called_once()

    # Should only upsert the valid one
    assert mock_occupation_repo.upsert.call_count == 1


@pytest.mark.asyncio
async def test_sync_skips_occupation_missing_both(sync_job, mock_onet_client, mock_occupation_repo):
    """Sync should skip occupations missing both code and title."""
    mock_onet_client.search_occupations.return_value = [
        {"description": "Only description, no code or title"},
        {},  # Empty object
    ]

    with patch("app.modules.discovery.services.onet_sync.logger") as mock_logger:
        result = await sync_job.sync_occupations()

        assert result["success"] is True
        assert result["processed_count"] == 0
        assert result["skipped_count"] == 2
        assert mock_logger.warning.call_count == 2

    mock_occupation_repo.upsert.assert_not_called()


@pytest.mark.asyncio
async def test_sync_database_error_reports_partial_success(
    sync_job, mock_onet_client, mock_occupation_repo
):
    """Sync should report actual processed_count on database errors."""
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Dev1"},
        {"code": "15-1251.00", "title": "Dev2"},
        {"code": "15-1253.00", "title": "Dev3"},
    ]

    # First upsert succeeds, second fails
    mock_occupation_repo.upsert.side_effect = [
        None,  # First succeeds
        Exception("Database connection error"),  # Second fails
    ]

    result = await sync_job.sync_occupations()

    assert result["success"] is False
    assert result["processed_count"] == 1  # Only first one succeeded
    assert "error" in result
    assert "Database connection error" in result["error"]


@pytest.mark.asyncio
async def test_sync_passes_keyword_to_client(sync_job, mock_onet_client):
    """Sync should pass keyword parameter to API client."""
    mock_onet_client.search_occupations.return_value = []

    await sync_job.sync_occupations(keyword="software")

    mock_onet_client.search_occupations.assert_called_once_with("software")


@pytest.mark.asyncio
async def test_sync_passes_empty_keyword_to_client(sync_job, mock_onet_client):
    """Sync should pass empty string keyword to API client."""
    mock_onet_client.search_occupations.return_value = []

    await sync_job.sync_occupations(keyword="")

    mock_onet_client.search_occupations.assert_called_once_with("")


@pytest.mark.asyncio
async def test_sync_default_keyword_is_empty_string(sync_job, mock_onet_client):
    """Sync should use empty string as default keyword."""
    mock_onet_client.search_occupations.return_value = []

    await sync_job.sync_occupations()

    mock_onet_client.search_occupations.assert_called_once_with("")
