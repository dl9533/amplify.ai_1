# discovery/tests/unit/services/test_role_mapping_service_impl.py
"""Unit tests for implemented role mapping service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.agents.role_mapping_agent import RoleMappingResult, ConfidenceTier


@pytest.mark.asyncio
async def test_create_mappings_from_upload():
    """Test creating mappings from uploaded file roles."""
    from app.services.role_mapping_service import RoleMappingService

    mock_repo = AsyncMock()
    mock_agent = AsyncMock()
    mock_upload_service = AsyncMock()

    # Mock repository methods
    mock_repo.delete_for_session.return_value = 0  # No existing mappings to delete

    # Mock upload with file content
    mock_upload_service.get_file_content.return_value = b"name,role\nJohn,Engineer"

    # Mock upload record
    mock_upload = MagicMock()
    mock_upload.file_name = "test.csv"
    mock_upload_service.repository.get_by_id.return_value = mock_upload

    # Mock agent results
    mock_agent.map_roles.return_value = [
        RoleMappingResult(
            source_role="Engineer",
            onet_code="15-1252.00",
            onet_title="Software Developers",
            confidence=ConfidenceTier.HIGH,
            reasoning="Clear match",
        )
    ]

    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.source_role = "Engineer"
    mock_mapping.onet_code = "15-1252.00"
    mock_mapping.confidence_score = 0.95
    mock_mapping.row_count = 1
    mock_mapping.user_confirmed = False
    mock_mapping.industry_match_score = None
    mock_mapping.lob_value = None
    mock_mapping.department_value = None
    mock_mapping.geography_value = None
    # Service now uses bulk_upsert instead of individual create calls
    mock_repo.bulk_upsert.return_value = [mock_mapping]

    service = RoleMappingService(
        repository=mock_repo,
        role_mapping_agent=mock_agent,
        upload_service=mock_upload_service,
    )

    # Patch file parser
    with patch.object(service, "_file_parser") as mock_parser:
        mock_parser.extract_role_lob_values.return_value = [
            {"role": "Engineer", "lob": None, "count": 1}
        ]

        session_id = uuid4()
        upload_id = uuid4()
        result = await service.create_mappings_from_upload(
            session_id=session_id,
            upload_id=upload_id,
            role_column="role",
        )

    assert len(result) == 1
    assert result[0]["source_role"] == "Engineer"
    assert result[0]["confidence_tier"] == "HIGH"
    mock_agent.map_roles.assert_called_once()
    mock_repo.bulk_upsert.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_mapping():
    """Test confirming a role mapping."""
    from app.services.role_mapping_service import RoleMappingService

    mock_repo = AsyncMock()
    mock_agent = MagicMock()
    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.source_role = "Engineer"
    mock_mapping.onet_code = "15-1252.00"
    mock_mapping.user_confirmed = True
    mock_repo.confirm.return_value = mock_mapping

    service = RoleMappingService(
        repository=mock_repo,
        role_mapping_agent=mock_agent,
    )
    result = await service.confirm_mapping(mock_mapping.id, "15-1252.00")

    assert result is not None
    assert result["is_confirmed"] is True
    mock_repo.confirm.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_session_id():
    """Test getting mappings by session ID."""
    from app.services.role_mapping_service import RoleMappingService

    mock_repo = AsyncMock()
    mock_agent = MagicMock()
    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.source_role = "Engineer"
    mock_mapping.onet_code = "15-1252.00"
    mock_mapping.confidence_score = 0.85
    mock_mapping.row_count = 5
    mock_mapping.user_confirmed = False
    mock_repo.get_for_session.return_value = [mock_mapping]

    service = RoleMappingService(
        repository=mock_repo,
        role_mapping_agent=mock_agent,
    )
    result = await service.get_by_session_id(uuid4())

    assert len(result) == 1
    assert result[0]["source_role"] == "Engineer"


@pytest.mark.asyncio
async def test_bulk_confirm():
    """Test bulk confirmation of mappings."""
    from app.services.role_mapping_service import RoleMappingService

    mock_repo = AsyncMock()
    mock_agent = MagicMock()
    mock_mapping = MagicMock()
    mock_mapping.id = uuid4()
    mock_mapping.onet_code = "15-1252.00"
    mock_mapping.confidence_score = 0.90
    mock_mapping.user_confirmed = False
    mock_repo.get_for_session.return_value = [mock_mapping]

    service = RoleMappingService(
        repository=mock_repo,
        role_mapping_agent=mock_agent,
    )
    result = await service.bulk_confirm(uuid4(), threshold=0.85)

    assert result["confirmed_count"] == 1
    mock_repo.confirm.assert_called_once()
