# backend/tests/unit/modules/discovery/test_activity_selection_repository.py
"""Unit tests for DiscoveryActivitySelectionRepository."""

import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.modules.discovery.repositories.activity_selection_repository import (
    DiscoveryActivitySelectionRepository,
)
from app.modules.discovery.models.session import DiscoveryActivitySelection


@pytest.mark.asyncio
async def test_create_activity_selection(mock_db_session):
    """Should create activity selection with all fields."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()
    dwa_id = "4.A.1.a.1"

    selection = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id=dwa_id,
        selected=True,
        user_modified=False,
    )

    assert selection.session_id == session_id
    assert selection.role_mapping_id == role_mapping_id
    assert selection.dwa_id == dwa_id
    assert selection.selected is True
    assert selection.user_modified is False
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_activity_selection_with_defaults(mock_db_session):
    """Should create activity selection with default values."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()
    dwa_id = "4.A.2.b.3"

    selection = await repo.create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id=dwa_id,
    )

    assert selection.session_id == session_id
    assert selection.role_mapping_id == role_mapping_id
    assert selection.dwa_id == dwa_id
    assert selection.selected is True  # default
    assert selection.user_modified is False  # default


@pytest.mark.asyncio
async def test_get_selection_by_id(mock_db_session):
    """Should retrieve activity selection by ID."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    selection_id = uuid4()
    session_id = uuid4()
    role_mapping_id = uuid4()

    # Create mock selection
    mock_selection = DiscoveryActivitySelection(
        id=selection_id,
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.1.a.1",
        selected=True,
        user_modified=False,
    )

    # Configure mock to return selection
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_selection

    retrieved = await repo.get_by_id(selection_id)

    assert retrieved is not None
    assert retrieved.id == selection_id
    assert retrieved.dwa_id == "4.A.1.a.1"


@pytest.mark.asyncio
async def test_get_selection_by_id_not_found(mock_db_session):
    """Should return None when selection not found."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.get_by_id(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_selections_by_session_id(mock_db_session):
    """Should retrieve all selections for a session."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    # Create mock selections
    selection1 = DiscoveryActivitySelection(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.1.a.1",
        selected=True,
    )
    selection2 = DiscoveryActivitySelection(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.2.b.3",
        selected=False,
    )

    # Configure mock to return selections
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [selection1, selection2]
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.get_by_session_id(session_id)

    assert len(selections) == 2
    assert selections[0].session_id == session_id
    assert selections[1].session_id == session_id


@pytest.mark.asyncio
async def test_get_selections_by_session_id_empty(mock_db_session):
    """Should return empty list when session has no selections."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    # Configure mock to return empty list
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.get_by_session_id(uuid4())

    assert len(selections) == 0


@pytest.mark.asyncio
async def test_get_selections_by_role_mapping(mock_db_session):
    """Should retrieve all selections for a role mapping."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()

    # Create mock selections
    selection1 = DiscoveryActivitySelection(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.1.a.1",
        selected=True,
    )
    selection2 = DiscoveryActivitySelection(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.2.b.3",
        selected=True,
    )

    # Configure mock to return selections
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [selection1, selection2]
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.get_by_role_mapping_id(role_mapping_id)

    assert len(selections) == 2
    assert all(s.role_mapping_id == role_mapping_id for s in selections)


@pytest.mark.asyncio
async def test_get_selections_by_role_mapping_empty(mock_db_session):
    """Should return empty list when role mapping has no selections."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    # Configure mock to return empty list
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.get_by_role_mapping_id(uuid4())

    assert len(selections) == 0


@pytest.mark.asyncio
async def test_toggle_selection(mock_db_session):
    """Should toggle selected state and set user_modified=True."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    selection_id = uuid4()

    # Create mock selection with selected=True
    mock_selection = DiscoveryActivitySelection(
        id=selection_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dwa_id="4.A.1.a.1",
        selected=True,
        user_modified=False,
    )

    # Configure mock to return selection
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_selection

    updated = await repo.toggle_selection(selection_id)

    assert updated.selected is False  # toggled from True to False
    assert updated.user_modified is True  # set to True
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_toggle_selection_from_false_to_true(mock_db_session):
    """Should toggle selected state from False to True."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    selection_id = uuid4()

    # Create mock selection with selected=False
    mock_selection = DiscoveryActivitySelection(
        id=selection_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dwa_id="4.A.1.a.1",
        selected=False,
        user_modified=False,
    )

    # Configure mock to return selection
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_selection

    updated = await repo.toggle_selection(selection_id)

    assert updated.selected is True  # toggled from False to True
    assert updated.user_modified is True


@pytest.mark.asyncio
async def test_toggle_selection_not_found(mock_db_session):
    """Should return None when selection to toggle not found."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.toggle_selection(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_update_selection(mock_db_session):
    """Should update selected state and set user_modified=True."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    selection_id = uuid4()

    # Create mock selection
    mock_selection = DiscoveryActivitySelection(
        id=selection_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dwa_id="4.A.1.a.1",
        selected=True,
        user_modified=False,
    )

    # Configure mock to return selection
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_selection

    updated = await repo.update_selection(selection_id, selected=False)

    assert updated.selected is False
    assert updated.user_modified is True
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_update_selection_not_found(mock_db_session):
    """Should return None when selection to update not found."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.update_selection(uuid4(), selected=True)
    assert result is None


@pytest.mark.asyncio
async def test_bulk_create_selections(mock_db_session):
    """Should bulk create multiple activity selections."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()
    dwa_ids = ["4.A.1.a.1", "4.A.2.b.3", "4.A.3.c.5"]

    # Create mock selections that will be returned by the batch refresh query
    mock_selections = [
        DiscoveryActivitySelection(
            id=uuid4(),
            session_id=session_id,
            role_mapping_id=role_mapping_id,
            dwa_id=dwa_id,
            selected=True,
            user_modified=False,
        )
        for dwa_id in dwa_ids
    ]

    # Configure mock to return selections from the batch refresh query
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_selections
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.bulk_create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_ids=dwa_ids,
        selected=True,
    )

    assert len(selections) == 3
    assert all(s.session_id == session_id for s in selections)
    assert all(s.role_mapping_id == role_mapping_id for s in selections)
    assert all(s.selected is True for s in selections)
    assert all(s.user_modified is False for s in selections)
    # Verify each dwa_id is present
    created_dwa_ids = {s.dwa_id for s in selections}
    assert created_dwa_ids == set(dwa_ids)
    # Should call add for each selection
    assert mock_db_session.add.call_count == 3
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_create_selections_with_selected_false(mock_db_session):
    """Should bulk create selections with selected=False."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    session_id = uuid4()
    role_mapping_id = uuid4()
    dwa_ids = ["4.A.1.a.1", "4.A.2.b.3"]

    # Create mock selections that will be returned by the batch refresh query
    mock_selections = [
        DiscoveryActivitySelection(
            id=uuid4(),
            session_id=session_id,
            role_mapping_id=role_mapping_id,
            dwa_id=dwa_id,
            selected=False,
            user_modified=False,
        )
        for dwa_id in dwa_ids
    ]

    # Configure mock to return selections from the batch refresh query
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = mock_selections
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.bulk_create(
        session_id=session_id,
        role_mapping_id=role_mapping_id,
        dwa_ids=dwa_ids,
        selected=False,
    )

    assert len(selections) == 2
    assert all(s.selected is False for s in selections)


@pytest.mark.asyncio
async def test_bulk_create_empty_list(mock_db_session):
    """Should return empty list when dwa_ids is empty."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    selections = await repo.bulk_create(
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dwa_ids=[],
        selected=True,
    )

    assert len(selections) == 0
    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_get_selected_activities(mock_db_session):
    """Should get only selected=True activities for a role mapping."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    role_mapping_id = uuid4()

    # Create mock selections - only selected ones
    selection1 = DiscoveryActivitySelection(
        id=uuid4(),
        session_id=uuid4(),
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.1.a.1",
        selected=True,
    )
    selection2 = DiscoveryActivitySelection(
        id=uuid4(),
        session_id=uuid4(),
        role_mapping_id=role_mapping_id,
        dwa_id="4.A.2.b.3",
        selected=True,
    )

    # Configure mock to return only selected
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [selection1, selection2]
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.get_selected_for_role_mapping(role_mapping_id)

    assert len(selections) == 2
    assert all(s.selected is True for s in selections)


@pytest.mark.asyncio
async def test_get_selected_activities_empty(mock_db_session):
    """Should return empty list when no selected activities."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    # Configure mock to return empty list
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.get_selected_for_role_mapping(uuid4())

    assert len(selections) == 0


@pytest.mark.asyncio
async def test_get_user_modified_selections(mock_db_session):
    """Should get only user_modified=True selections for a session."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    session_id = uuid4()

    # Create mock modified selections
    selection1 = DiscoveryActivitySelection(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=uuid4(),
        dwa_id="4.A.1.a.1",
        selected=True,
        user_modified=True,
    )
    selection2 = DiscoveryActivitySelection(
        id=uuid4(),
        session_id=session_id,
        role_mapping_id=uuid4(),
        dwa_id="4.A.2.b.3",
        selected=False,
        user_modified=True,
    )

    # Configure mock to return modified selections
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [selection1, selection2]
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.get_user_modified(session_id)

    assert len(selections) == 2
    assert all(s.user_modified is True for s in selections)


@pytest.mark.asyncio
async def test_get_user_modified_selections_empty(mock_db_session):
    """Should return empty list when no user modified selections."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    # Configure mock to return empty list
    mock_result = mock_db_session.execute.return_value
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars

    selections = await repo.get_user_modified(uuid4())

    assert len(selections) == 0


@pytest.mark.asyncio
async def test_delete_selection(mock_db_session):
    """Should delete selection record."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    selection_id = uuid4()

    # Create mock selection
    mock_selection = DiscoveryActivitySelection(
        id=selection_id,
        session_id=uuid4(),
        role_mapping_id=uuid4(),
        dwa_id="4.A.1.a.1",
        selected=True,
    )

    # Configure mock to return selection
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = mock_selection

    result = await repo.delete(selection_id)

    assert result is True
    mock_db_session.delete.assert_called_once_with(mock_selection)
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_selection_not_found(mock_db_session):
    """Should return False when selection to delete not found."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    # Configure mock to return None
    mock_result = mock_db_session.execute.return_value
    mock_result.scalar_one_or_none.return_value = None

    result = await repo.delete(uuid4())

    assert result is False
    mock_db_session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_by_role_mapping(mock_db_session):
    """Should delete all selections for a role mapping using bulk delete."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)
    role_mapping_id = uuid4()

    # Configure mock to return rowcount from bulk delete
    mock_result = mock_db_session.execute.return_value
    mock_result.rowcount = 2

    count = await repo.delete_by_role_mapping_id(role_mapping_id)

    assert count == 2
    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_by_role_mapping_none_found(mock_db_session):
    """Should return 0 when no selections found for role mapping."""
    repo = DiscoveryActivitySelectionRepository(mock_db_session)

    # Configure mock to return rowcount of 0 from bulk delete
    mock_result = mock_db_session.execute.return_value
    mock_result.rowcount = 0

    count = await repo.delete_by_role_mapping_id(uuid4())

    assert count == 0
    mock_db_session.execute.assert_called_once()
    mock_db_session.commit.assert_called()
