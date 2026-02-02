# discovery/tests/unit/services/test_role_mapping_service_impl.py
"""Unit tests for implemented role mapping service."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_create_mappings_from_upload():
    """Test creating mappings from uploaded file roles."""
    from app.services.role_mapping_service import RoleMappingService

    mock_repo = AsyncMock()
    mock_onet_client = AsyncMock()
    mock_upload_service = AsyncMock()
    mock_fuzzy = MagicMock()

    # Mock upload with file content
    mock_upload_service.get_file_content.return_value = b"name,role\nJohn,Engineer"

    # Mock upload record
    mock_upload = MagicMock()
    mock_upload.file_name = "test.csv"
    mock_upload_service.repository.get_by_id.return_value = mock_upload

    # Mock O*NET search results
    mock_onet_client.search_occupations.return_value = [
        {"code": "15-1252.00", "title": "Software Developers"},
    ]

    mock_fuzzy.find_best_matches.return_value = [
        {"code": "15-1252.00", "title": "Software Developers", "score": 0.85},
    ]

    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.source_role = "Engineer"
    mock_mapping.onet_code = "15-1252.00"
    mock_mapping.confidence_score = 0.85
    mock_mapping.row_count = 1
    mock_mapping.user_confirmed = False
    mock_repo.create.return_value = mock_mapping

    service = RoleMappingService(
        repository=mock_repo,
        onet_client=mock_onet_client,
        upload_service=mock_upload_service,
        fuzzy_matcher=mock_fuzzy,
    )

    session_id = uuid4()
    upload_id = uuid4()
    result = await service.create_mappings_from_upload(
        session_id=session_id,
        upload_id=upload_id,
        role_column="role",
    )

    assert len(result) > 0
    mock_onet_client.search_occupations.assert_called()


@pytest.mark.asyncio
async def test_confirm_mapping():
    """Test confirming a role mapping."""
    from app.services.role_mapping_service import RoleMappingService

    mock_repo = AsyncMock()
    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.source_role = "Engineer"
    mock_mapping.onet_code = "15-1252.00"
    mock_mapping.user_confirmed = True
    mock_repo.confirm.return_value = mock_mapping

    service = RoleMappingService(repository=mock_repo)
    result = await service.confirm_mapping(mock_mapping.id, "15-1252.00")

    assert result is not None
    mock_repo.confirm.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_session_id():
    """Test getting mappings by session ID."""
    from app.services.role_mapping_service import RoleMappingService

    mock_repo = AsyncMock()
    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.source_role = "Engineer"
    mock_mapping.onet_code = "15-1252.00"
    mock_mapping.confidence_score = 0.85
    mock_mapping.row_count = 5
    mock_mapping.user_confirmed = False
    mock_repo.get_for_session.return_value = [mock_mapping]

    service = RoleMappingService(repository=mock_repo)
    result = await service.get_by_session_id(uuid4())

    assert len(result) == 1
    assert result[0]["source_role"] == "Engineer"


@pytest.mark.asyncio
async def test_bulk_confirm():
    """Test bulk confirmation of mappings."""
    from app.services.role_mapping_service import RoleMappingService

    mock_repo = AsyncMock()
    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.onet_code = "15-1252.00"
    mock_mapping.confidence_score = 0.90
    mock_mapping.user_confirmed = False
    mock_repo.get_for_session.return_value = [mock_mapping]

    service = RoleMappingService(repository=mock_repo)
    result = await service.bulk_confirm(uuid4(), min_confidence=0.85)

    assert result["confirmed_count"] == 1
    mock_repo.confirm.assert_called_once()
