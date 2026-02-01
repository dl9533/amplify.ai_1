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
