# backend/tests/unit/modules/discovery/test_role_mapping_repository.py
"""Unit tests for DiscoveryRoleMappingRepository."""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.modules.discovery.repositories.role_mapping_repository import (
    DiscoveryRoleMappingRepository,
)
from app.modules.discovery.models.session import DiscoveryRoleMapping


@pytest.mark.asyncio
async def test_create_role_mapping(mock_db_session):
    """Should create role mapping with all fields."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    session_id = uuid4()
    source_role = "Software Engineer"
    onet_code = "15-1252.00"
    confidence_score = 0.92
    row_count = 150

    mapping = await repo.create(
        session_id=session_id,
        source_role=source_role,
        onet_code=onet_code,
        confidence_score=confidence_score,
        user_confirmed=True,
        row_count=row_count,
    )

    assert mapping.session_id == session_id
    assert mapping.source_role == source_role
    assert mapping.onet_code == onet_code
    assert mapping.confidence_score == confidence_score
    assert mapping.user_confirmed is True
    assert mapping.row_count == row_count
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_role_mapping_minimal(mock_db_session):
    """Should create role mapping with only required fields."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    session_id = uuid4()
    source_role = "Project Manager"

    mapping = await repo.create(
        session_id=session_id,
        source_role=source_role,
        onet_code=None,
    )

    assert mapping.session_id == session_id
    assert mapping.source_role == source_role
    assert mapping.onet_code is None
    assert mapping.confidence_score is None
    assert mapping.user_confirmed is False
    assert mapping.row_count is None


@pytest.mark.asyncio
async def test_get_role_mapping_by_id(mock_db_session):
    """Should retrieve role mapping by ID."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    mapping_id = uuid4()
    session_id = uuid4()

    # Create mock mapping
    mock_mapping = DiscoveryRoleMapping(
        id=mapping_id,
        session_id=session_id,
        source_role="Data Analyst",
        onet_code="15-2051.00",
        confidence_score=0.85,
        user_confirmed=False,
    )

    # Configure mock to return mapping
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_mapping

    retrieved = await repo.get_by_id(mapping_id)

    assert retrieved is not None
    assert retrieved.id == mapping_id
    assert retrieved.source_role == "Data Analyst"


@pytest.mark.asyncio
async def test_get_role_mapping_by_id_not_found(mock_db_session):
    """Should return None when mapping not found."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_mappings_by_session_id(mock_db_session):
    """Should retrieve all mappings for a session."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    session_id = uuid4()

    # Create mock mappings
    mapping1 = DiscoveryRoleMapping(
        id=uuid4(),
        session_id=session_id,
        source_role="Developer",
        onet_code="15-1252.00",
    )
    mapping2 = DiscoveryRoleMapping(
        id=uuid4(),
        session_id=session_id,
        source_role="Designer",
        onet_code="27-1024.00",
    )

    # Configure mock to return mappings
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mapping1, mapping2]
    mock_result.scalars.return_value = mock_scalars

    mappings = await repo.get_by_session_id(session_id)

    assert len(mappings) == 2
    assert mappings[0].session_id == session_id
    assert mappings[1].session_id == session_id


@pytest.mark.asyncio
async def test_get_mappings_by_session_id_empty(mock_db_session):
    """Should return empty list when session has no mappings."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)

    # Configure mock to return empty list
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    mappings = await repo.get_by_session_id(uuid4())

    assert len(mappings) == 0


@pytest.mark.asyncio
async def test_update_onet_code(mock_db_session):
    """Should update O*NET code and set user_confirmed."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    mapping_id = uuid4()

    # Create mock mapping
    mock_mapping = DiscoveryRoleMapping(
        id=mapping_id,
        session_id=uuid4(),
        source_role="Accountant",
        onet_code=None,
        user_confirmed=False,
    )

    # Configure mock to return mapping
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_mapping

    new_onet_code = "13-2011.00"
    updated = await repo.update_onet_code(mapping_id, new_onet_code, user_confirmed=True)

    assert updated.onet_code == new_onet_code
    assert updated.user_confirmed is True
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_onet_code_not_confirmed(mock_db_session):
    """Should update O*NET code without setting user_confirmed."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    mapping_id = uuid4()

    # Create mock mapping
    mock_mapping = DiscoveryRoleMapping(
        id=mapping_id,
        session_id=uuid4(),
        source_role="Engineer",
        onet_code="15-1252.00",
        user_confirmed=False,
    )

    # Configure mock to return mapping
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_mapping

    new_onet_code = "15-1299.00"
    updated = await repo.update_onet_code(mapping_id, new_onet_code, user_confirmed=False)

    assert updated.onet_code == new_onet_code
    assert updated.user_confirmed is False


@pytest.mark.asyncio
async def test_update_onet_code_not_found(mock_db_session):
    """Should return None when mapping to update not found."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.update_onet_code(uuid4(), "15-1252.00")
    assert result is None


@pytest.mark.asyncio
async def test_update_confidence_score(mock_db_session):
    """Should update confidence score."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    mapping_id = uuid4()

    # Create mock mapping
    mock_mapping = DiscoveryRoleMapping(
        id=mapping_id,
        session_id=uuid4(),
        source_role="Manager",
        onet_code="11-1021.00",
        confidence_score=0.75,
    )

    # Configure mock to return mapping
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_mapping

    new_score = 0.95
    updated = await repo.update_confidence_score(mapping_id, new_score)

    assert updated.confidence_score == new_score
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_confidence_score_not_found(mock_db_session):
    """Should return None when mapping to update not found."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.update_confidence_score(uuid4(), 0.90)
    assert result is None


@pytest.mark.asyncio
async def test_confirm_mapping(mock_db_session):
    """Should set user_confirmed to True."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    mapping_id = uuid4()

    # Create mock mapping
    mock_mapping = DiscoveryRoleMapping(
        id=mapping_id,
        session_id=uuid4(),
        source_role="Sales Rep",
        onet_code="41-3091.00",
        user_confirmed=False,
    )

    # Configure mock to return mapping
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_mapping

    updated = await repo.confirm_mapping(mapping_id)

    assert updated.user_confirmed is True
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_confirm_mapping_not_found(mock_db_session):
    """Should return None when mapping to confirm not found."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.confirm_mapping(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_bulk_confirm_mappings(mock_db_session):
    """Should confirm all mappings above confidence threshold."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    session_id = uuid4()
    threshold = 0.80

    # Create mock mappings - two above threshold, one below
    mapping1 = DiscoveryRoleMapping(
        id=uuid4(),
        session_id=session_id,
        source_role="Developer",
        onet_code="15-1252.00",
        confidence_score=0.92,
        user_confirmed=False,
    )
    mapping2 = DiscoveryRoleMapping(
        id=uuid4(),
        session_id=session_id,
        source_role="Designer",
        onet_code="27-1024.00",
        confidence_score=0.85,
        user_confirmed=False,
    )

    # Configure mock to return mappings above threshold
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mapping1, mapping2]
    mock_result.scalars.return_value = mock_scalars

    count = await repo.bulk_confirm_above_threshold(session_id, threshold)

    assert count == 2
    assert mapping1.user_confirmed is True
    assert mapping2.user_confirmed is True
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_bulk_confirm_mappings_none_above_threshold(mock_db_session):
    """Should return 0 when no mappings above threshold."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)

    # Configure mock to return empty list
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    count = await repo.bulk_confirm_above_threshold(uuid4(), 0.90)

    assert count == 0


@pytest.mark.asyncio
async def test_get_unconfirmed_mappings(mock_db_session):
    """Should get unconfirmed mappings for a session."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    session_id = uuid4()

    # Create mock unconfirmed mappings
    mapping1 = DiscoveryRoleMapping(
        id=uuid4(),
        session_id=session_id,
        source_role="Analyst",
        onet_code="15-2051.00",
        user_confirmed=False,
    )
    mapping2 = DiscoveryRoleMapping(
        id=uuid4(),
        session_id=session_id,
        source_role="Coordinator",
        onet_code=None,
        user_confirmed=False,
    )

    # Configure mock to return unconfirmed mappings
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [mapping1, mapping2]
    mock_result.scalars.return_value = mock_scalars

    unconfirmed = await repo.get_unconfirmed(session_id)

    assert len(unconfirmed) == 2
    assert all(m.user_confirmed is False for m in unconfirmed)


@pytest.mark.asyncio
async def test_get_unconfirmed_mappings_all_confirmed(mock_db_session):
    """Should return empty list when all mappings confirmed."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)

    # Configure mock to return empty list
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    unconfirmed = await repo.get_unconfirmed(uuid4())

    assert len(unconfirmed) == 0


@pytest.mark.asyncio
async def test_delete_role_mapping(mock_db_session):
    """Should delete role mapping record."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    mapping_id = uuid4()

    # Create mock mapping
    mock_mapping = DiscoveryRoleMapping(
        id=mapping_id,
        session_id=uuid4(),
        source_role="Specialist",
        onet_code="17-2199.00",
    )

    # Configure mock to return mapping
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_mapping

    result = await repo.delete(mapping_id)

    assert result is True
    mock_db_session.delete.assert_called_once_with(mock_mapping)
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_role_mapping_not_found(mock_db_session):
    """Should return False when mapping to delete not found."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.delete(uuid4())

    assert result is False
    mock_db_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_mapping_by_source_role(mock_db_session):
    """Should get mapping by source role name."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)
    session_id = uuid4()
    source_role = "Product Manager"

    # Create mock mapping
    mock_mapping = DiscoveryRoleMapping(
        id=uuid4(),
        session_id=session_id,
        source_role=source_role,
        onet_code="11-2021.00",
        confidence_score=0.88,
    )

    # Configure mock to return mapping
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_mapping

    found = await repo.get_by_source_role(session_id, source_role)

    assert found is not None
    assert found.source_role == source_role
    assert found.session_id == session_id


@pytest.mark.asyncio
async def test_get_mapping_by_source_role_not_found(mock_db_session):
    """Should return None when source role not found."""
    repo = DiscoveryRoleMappingRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.get_by_source_role(uuid4(), "Nonexistent Role")
    assert result is None
