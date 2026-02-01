# backend/tests/unit/modules/discovery/test_candidate_repository.py
"""Unit tests for AgentificationCandidateRepository."""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.modules.discovery.repositories.candidate_repository import (
    AgentificationCandidateRepository,
)
from app.modules.discovery.models.session import AgentificationCandidate
from app.modules.discovery.enums import PriorityTier


@pytest.mark.asyncio
async def test_create_candidate(mock_db_session):
    """Should create candidate with all fields."""
    repo = AgentificationCandidateRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()
    name = "Customer Support Agent"
    description = "Handles customer inquiries"
    priority_tier = PriorityTier.NOW
    estimated_impact = 0.85

    candidate = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name=name,
        description=description,
        priority_tier=priority_tier,
        estimated_impact=estimated_impact,
        selected_for_build=True,
    )

    assert candidate.session_id == session_id
    assert candidate.role_mapping_id == role_mapping_id
    assert candidate.name == name
    assert candidate.description == description
    assert candidate.priority_tier == priority_tier
    assert candidate.estimated_impact == estimated_impact
    assert candidate.selected_for_build is True
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_candidate_minimal(mock_db_session):
    """Should create candidate with only required fields."""
    repo = AgentificationCandidateRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()
    name = "Data Entry Agent"
    priority_tier = PriorityTier.NEXT_QUARTER
    estimated_impact = 0.5

    candidate = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name=name,
        priority_tier=priority_tier,
        estimated_impact=estimated_impact,
    )

    assert candidate.session_id == session_id
    assert candidate.role_mapping_id == role_mapping_id
    assert candidate.name == name
    assert candidate.description is None
    assert candidate.priority_tier == priority_tier
    assert candidate.estimated_impact == estimated_impact
    assert candidate.selected_for_build is False


@pytest.mark.asyncio
async def test_get_candidate_by_id(mock_db_session):
    """Should retrieve candidate by ID."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_id = uuid4()
    session_id = uuid4()
    role_mapping_id = uuid4()

    mock_candidate = AgentificationCandidate(
        id=candidate_id,
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        name="Sales Agent",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.75,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_candidate

    retrieved = await repo.get_by_id(candidate_id)

    assert retrieved is not None
    assert retrieved.id == candidate_id
    assert retrieved.name == "Sales Agent"


@pytest.mark.asyncio
async def test_get_candidate_by_id_not_found(mock_db_session):
    """Should return None when candidate not found."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_candidates_by_session_id(mock_db_session):
    """Should retrieve all candidates for a session."""
    repo = AgentificationCandidateRepository(mock_db_session)
    session_id = uuid4()

    candidate1 = AgentificationCandidate(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=uuid4(),
        name="Support Agent",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.8,
    )
    candidate2 = AgentificationCandidate(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=uuid4(),
        name="Analytics Agent",
        priority_tier=PriorityTier.FUTURE,
        estimated_impact=0.6,
    )

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [candidate1, candidate2]
    mock_result.scalars.return_value = mock_scalars

    candidates = await repo.get_by_session_id(session_id)

    assert len(candidates) == 2
    assert candidates[0].session_id == session_id
    assert candidates[1].session_id == session_id


@pytest.mark.asyncio
async def test_get_candidates_by_session_id_empty(mock_db_session):
    """Should return empty list when session has no candidates."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    candidates = await repo.get_by_session_id(uuid4())

    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_get_by_priority_tier(mock_db_session):
    """Should retrieve candidates filtered by priority tier."""
    repo = AgentificationCandidateRepository(mock_db_session)
    session_id = uuid4()

    candidate1 = AgentificationCandidate(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=uuid4(),
        name="Now Agent 1",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.9,
    )
    candidate2 = AgentificationCandidate(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=uuid4(),
        name="Now Agent 2",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.85,
    )

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [candidate1, candidate2]
    mock_result.scalars.return_value = mock_scalars

    candidates = await repo.get_by_priority_tier(session_id, PriorityTier.NOW)

    assert len(candidates) == 2
    assert all(c.priority_tier == PriorityTier.NOW for c in candidates)


@pytest.mark.asyncio
async def test_get_by_priority_tier_empty(mock_db_session):
    """Should return empty list when no candidates match tier."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    candidates = await repo.get_by_priority_tier(uuid4(), PriorityTier.FUTURE)

    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_update_priority_tier(mock_db_session):
    """Should update candidate priority tier."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_id = uuid4()

    mock_candidate = AgentificationCandidate(
        id=candidate_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="Test Agent",
        priority_tier=PriorityTier.FUTURE,
        estimated_impact=0.7,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_candidate

    updated = await repo.update_priority_tier(candidate_id, PriorityTier.NOW)

    assert updated.priority_tier == PriorityTier.NOW
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_priority_tier_not_found(mock_db_session):
    """Should return None when candidate to update not found."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.update_priority_tier(uuid4(), PriorityTier.NOW)
    assert result is None


@pytest.mark.asyncio
async def test_update_details_name_and_description(mock_db_session):
    """Should update candidate name and description."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_id = uuid4()

    mock_candidate = AgentificationCandidate(
        id=candidate_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="Old Name",
        description="Old description",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.8,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_candidate

    updated = await repo.update_details(
        candidate_id, name="New Name", description="New description"
    )

    assert updated.name == "New Name"
    assert updated.description == "New description"
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_details_name_only(mock_db_session):
    """Should update only candidate name."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_id = uuid4()

    mock_candidate = AgentificationCandidate(
        id=candidate_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="Old Name",
        description="Keep this",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.8,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_candidate

    updated = await repo.update_details(candidate_id, name="New Name")

    assert updated.name == "New Name"
    assert updated.description == "Keep this"


@pytest.mark.asyncio
async def test_update_details_description_only(mock_db_session):
    """Should update only candidate description."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_id = uuid4()

    mock_candidate = AgentificationCandidate(
        id=candidate_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="Keep Name",
        description="Old description",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.8,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_candidate

    updated = await repo.update_details(candidate_id, description="New description")

    assert updated.name == "Keep Name"
    assert updated.description == "New description"


@pytest.mark.asyncio
async def test_update_details_not_found(mock_db_session):
    """Should return None when candidate to update not found."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.update_details(uuid4(), name="New Name")
    assert result is None


@pytest.mark.asyncio
async def test_select_for_build(mock_db_session):
    """Should set selected_for_build to True."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_id = uuid4()

    mock_candidate = AgentificationCandidate(
        id=candidate_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="Test Agent",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.8,
        selected_for_build=False,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_candidate

    updated = await repo.select_for_build(candidate_id)

    assert updated.selected_for_build is True
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_select_for_build_not_found(mock_db_session):
    """Should return None when candidate to select not found."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.select_for_build(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_deselect_for_build(mock_db_session):
    """Should set selected_for_build to False."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_id = uuid4()

    mock_candidate = AgentificationCandidate(
        id=candidate_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="Test Agent",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.8,
        selected_for_build=True,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_candidate

    updated = await repo.deselect_for_build(candidate_id)

    assert updated.selected_for_build is False
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_deselect_for_build_not_found(mock_db_session):
    """Should return None when candidate to deselect not found."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.deselect_for_build(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_link_intake_request(mock_db_session):
    """Should link candidate to intake request."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_id = uuid4()
    intake_request_id = uuid4()

    mock_candidate = AgentificationCandidate(
        id=candidate_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="Test Agent",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.8,
        intake_request_id=None,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_candidate

    updated = await repo.link_intake_request(candidate_id, intake_request_id)

    assert updated.intake_request_id == intake_request_id
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_link_intake_request_not_found(mock_db_session):
    """Should return None when candidate to link not found."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.link_intake_request(uuid4(), uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_selected_for_build(mock_db_session):
    """Should get candidates selected for build."""
    repo = AgentificationCandidateRepository(mock_db_session)
    session_id = uuid4()

    candidate1 = AgentificationCandidate(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=uuid4(),
        name="Selected Agent 1",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.9,
        selected_for_build=True,
    )
    candidate2 = AgentificationCandidate(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=uuid4(),
        name="Selected Agent 2",
        priority_tier=PriorityTier.NEXT_QUARTER,
        estimated_impact=0.75,
        selected_for_build=True,
    )

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [candidate1, candidate2]
    mock_result.scalars.return_value = mock_scalars

    selected = await repo.get_selected_for_build(session_id)

    assert len(selected) == 2
    assert all(c.selected_for_build is True for c in selected)


@pytest.mark.asyncio
async def test_get_selected_for_build_empty(mock_db_session):
    """Should return empty list when no candidates selected."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    selected = await repo.get_selected_for_build(uuid4())

    assert len(selected) == 0


@pytest.mark.asyncio
async def test_get_by_role_mapping_id(mock_db_session):
    """Should get candidates for a role mapping."""
    repo = AgentificationCandidateRepository(mock_db_session)
    role_mapping_id = uuid4()

    candidate1 = AgentificationCandidate(
        id=uuid4(),
        session_id=uuid4(),
        role_mapping_id=role_mapping_id,
        name="Role Agent 1",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.85,
    )
    candidate2 = AgentificationCandidate(
        id=uuid4(),
        session_id=uuid4(),
        role_mapping_id=role_mapping_id,
        name="Role Agent 2",
        priority_tier=PriorityTier.FUTURE,
        estimated_impact=0.6,
    )

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [candidate1, candidate2]
    mock_result.scalars.return_value = mock_scalars

    candidates = await repo.get_by_role_mapping_id(role_mapping_id)

    assert len(candidates) == 2
    assert all(c.role_mapping_id == role_mapping_id for c in candidates)


@pytest.mark.asyncio
async def test_get_by_role_mapping_id_empty(mock_db_session):
    """Should return empty list when role mapping has no candidates."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    candidates = await repo.get_by_role_mapping_id(uuid4())

    assert len(candidates) == 0


@pytest.mark.asyncio
async def test_delete_candidate(mock_db_session):
    """Should delete candidate record."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_id = uuid4()

    mock_candidate = AgentificationCandidate(
        id=candidate_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="To Delete",
        priority_tier=PriorityTier.FUTURE,
        estimated_impact=0.5,
    )

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_candidate

    result = await repo.delete(candidate_id)

    assert result is True
    mock_db_session.delete.assert_called_once_with(mock_candidate)
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_candidate_not_found(mock_db_session):
    """Should return False when candidate to delete not found."""
    repo = AgentificationCandidateRepository(mock_db_session)

    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.delete(uuid4())

    assert result is False
    mock_db_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_bulk_update_priority_tier(mock_db_session):
    """Should bulk update priority tier for multiple candidates."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_ids = [uuid4(), uuid4(), uuid4()]
    new_tier = PriorityTier.NOW

    # Mock rowcount for UPDATE
    mock_result = mock_db_session.execute.return_value
    mock_result.rowcount = 3

    count = await repo.bulk_update_priority_tier(candidate_ids, new_tier)

    assert count == 3
    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_update_priority_tier_partial(mock_db_session):
    """Should return count of actually updated rows."""
    repo = AgentificationCandidateRepository(mock_db_session)
    candidate_ids = [uuid4(), uuid4(), uuid4()]

    # Only 2 rows found and updated
    mock_result = mock_db_session.execute.return_value
    mock_result.rowcount = 2

    count = await repo.bulk_update_priority_tier(candidate_ids, PriorityTier.FUTURE)

    assert count == 2


@pytest.mark.asyncio
async def test_bulk_update_priority_tier_empty_list(mock_db_session):
    """Should return 0 when given empty list."""
    repo = AgentificationCandidateRepository(mock_db_session)

    count = await repo.bulk_update_priority_tier([], PriorityTier.NOW)

    assert count == 0
    mock_db_session.execute.assert_not_called()


# --- Validation Tests ---


@pytest.mark.asyncio
async def test_create_with_negative_estimated_impact_raises_error(mock_db_session):
    """Should raise ValueError when estimated_impact is negative."""
    repo = AgentificationCandidateRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.create(
            session_id=uuid4(),
            role_mapping_id=uuid4(),
            name="Test Agent",
            priority_tier=PriorityTier.NOW,
            estimated_impact=-0.1,
        )

    assert "estimated_impact must be between 0.0 and 1.0" in str(exc_info.value)
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_with_estimated_impact_greater_than_one_raises_error(
    mock_db_session,
):
    """Should raise ValueError when estimated_impact is greater than 1.0."""
    repo = AgentificationCandidateRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.create(
            session_id=uuid4(),
            role_mapping_id=uuid4(),
            name="Test Agent",
            priority_tier=PriorityTier.NOW,
            estimated_impact=1.5,
        )

    assert "estimated_impact must be between 0.0 and 1.0" in str(exc_info.value)
    mock_db_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_with_estimated_impact_at_zero_boundary(mock_db_session):
    """Should accept estimated_impact of exactly 0.0."""
    repo = AgentificationCandidateRepository(mock_db_session)

    candidate = await repo.create(
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="Test Agent",
        priority_tier=PriorityTier.NOW,
        estimated_impact=0.0,
    )

    assert candidate.estimated_impact == 0.0
    mock_db_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_create_with_estimated_impact_at_one_boundary(mock_db_session):
    """Should accept estimated_impact of exactly 1.0."""
    repo = AgentificationCandidateRepository(mock_db_session)

    candidate = await repo.create(
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        name="Test Agent",
        priority_tier=PriorityTier.NOW,
        estimated_impact=1.0,
    )

    assert candidate.estimated_impact == 1.0
    mock_db_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_create_with_none_estimated_impact_raises_error(mock_db_session):
    """Should raise ValueError when estimated_impact is None."""
    repo = AgentificationCandidateRepository(mock_db_session)

    with pytest.raises(ValueError) as exc_info:
        await repo.create(
            session_id=uuid4(),
            role_mapping_id=uuid4(),
            name="Test Agent",
            priority_tier=PriorityTier.NOW,
            estimated_impact=None,
        )

    assert "estimated_impact is required" in str(exc_info.value)
    mock_db_session.add.assert_not_called()
