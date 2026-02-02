# discovery/tests/unit/agents/test_upload_agent_impl.py
"""Unit tests for upload agent implementation."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_process_file_uploaded():
    """Test processing when file is uploaded."""
    from app.agents.upload_agent import UploadSubagent

    mock_upload_service = AsyncMock()
    mock_upload_service.get_by_session_id.return_value = [{
        "id": str(uuid4()),
        "file_name": "workforce.xlsx",
        "row_count": 100,
        "detected_schema": {"columns": [{"name": "role"}, {"name": "department"}]},
        "column_suggestions": {"role": "role", "department": "department"},
    }]

    session = MagicMock()
    session.id = uuid4()

    agent = UploadSubagent(
        session=session,
        upload_service=mock_upload_service,
    )

    result = await agent.process("I've uploaded my file")

    assert "message" in result
    assert "quick_actions" in result


@pytest.mark.asyncio
async def test_confirm_column_mappings():
    """Test confirming column mappings advances step."""
    from app.agents.upload_agent import UploadSubagent

    mock_upload_service = AsyncMock()
    mock_upload_service.update_column_mappings.return_value = {"id": str(uuid4())}
    mock_upload_service.get_by_session_id.return_value = [{
        "id": str(uuid4()),
        "file_name": "workforce.xlsx",
        "row_count": 100,
        "detected_schema": {"columns": [{"name": "role"}, {"name": "department"}]},
        "column_suggestions": {"role": "role", "department": "department"},
    }]

    session = MagicMock()
    session.id = uuid4()
    session.current_step = 1

    agent = UploadSubagent(
        session=session,
        upload_service=mock_upload_service,
    )

    # First set pending mappings and awaiting confirmation state
    agent._awaiting_confirmation = True
    agent._pending_mappings = {"role": "role", "department": "department"}
    agent._current_upload_id = str(uuid4())

    result = await agent.process("Yes, looks good")

    mock_upload_service.update_column_mappings.assert_called()
    assert "step_complete" in result


@pytest.mark.asyncio
async def test_no_uploads_yet():
    """Test response when no uploads exist."""
    from app.agents.upload_agent import UploadSubagent

    mock_upload_service = AsyncMock()
    mock_upload_service.get_by_session_id.return_value = []

    session = MagicMock()
    session.id = uuid4()

    agent = UploadSubagent(
        session=session,
        upload_service=mock_upload_service,
    )

    result = await agent.process("Hello")

    assert "upload" in result["message"].lower()
    assert "quick_actions" in result


@pytest.mark.asyncio
async def test_column_selection():
    """Test user selecting a column for role."""
    from app.agents.upload_agent import UploadSubagent

    mock_upload_service = AsyncMock()
    mock_upload_service.get_by_session_id.return_value = [{
        "id": str(uuid4()),
        "file_name": "workforce.xlsx",
        "row_count": 100,
        "detected_schema": {"columns": [
            {"name": "Job_Title"},
            {"name": "Department"},
            {"name": "Location"},
        ]},
        "column_suggestions": {},  # No auto-suggestions
    }]

    session = MagicMock()
    session.id = uuid4()

    agent = UploadSubagent(
        session=session,
        upload_service=mock_upload_service,
    )

    result = await agent.process("Job_Title is the role column")

    assert "message" in result
    # After setting role, should ask for department
    assert "Job_Title" in str(agent._pending_mappings.get("role", ""))
