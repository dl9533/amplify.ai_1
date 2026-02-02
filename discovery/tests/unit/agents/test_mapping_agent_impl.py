# discovery/tests/unit/agents/test_mapping_agent_impl.py
"""Unit tests for mapping agent implementation."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4


@pytest.mark.asyncio
async def test_show_mappings():
    """Test showing role mappings."""
    from app.agents.mapping_agent import MappingSubagent

    mock_mapping_service = AsyncMock()
    mock_mapping_service.get_by_session_id.return_value = [
        {
            "id": str(uuid4()),
            "source_role": "Software Engineer",
            "onet_code": "15-1252.00",
            "confidence_score": 0.92,
            "user_confirmed": False,
        },
    ]

    session = MagicMock()
    session.id = uuid4()

    agent = MappingSubagent(session=session, mapping_service=mock_mapping_service)
    result = await agent.process("Show me the mappings")

    assert "message" in result
    assert "Software Engineer" in result["message"]


@pytest.mark.asyncio
async def test_bulk_confirm():
    """Test bulk confirming high-confidence mappings."""
    from app.agents.mapping_agent import MappingSubagent

    mock_mapping_service = AsyncMock()
    mock_mapping_service.bulk_confirm.return_value = {"confirmed_count": 5}
    # Need at least one mapping so we don't early return
    mock_mapping_service.get_by_session_id.return_value = [
        {
            "id": str(uuid4()),
            "source_role": "Engineer",
            "onet_code": "15-1252.00",
            "confidence_score": 0.90,
            "user_confirmed": False,
        },
    ]

    session = MagicMock()
    session.id = uuid4()

    agent = MappingSubagent(session=session, mapping_service=mock_mapping_service)
    result = await agent.process("Accept all high confidence")

    mock_mapping_service.bulk_confirm.assert_called()
    assert "confirmed" in result["message"].lower()


@pytest.mark.asyncio
async def test_continue_to_next_step():
    """Test continuing to next step when all confirmed."""
    from app.agents.mapping_agent import MappingSubagent

    mock_mapping_service = AsyncMock()
    mock_mapping_service.get_by_session_id.return_value = [
        {
            "id": str(uuid4()),
            "source_role": "Engineer",
            "onet_code": "15-1252.00",
            "confidence_score": 0.90,
            "user_confirmed": True,
        },
    ]

    session = MagicMock()
    session.id = uuid4()

    agent = MappingSubagent(session=session, mapping_service=mock_mapping_service)
    result = await agent.process("continue")

    assert "step_complete" in result
    assert result["step_complete"] is True


@pytest.mark.asyncio
async def test_no_mappings_found():
    """Test response when no mappings exist."""
    from app.agents.mapping_agent import MappingSubagent

    mock_mapping_service = AsyncMock()
    mock_mapping_service.get_by_session_id.return_value = []

    session = MagicMock()
    session.id = uuid4()

    agent = MappingSubagent(session=session, mapping_service=mock_mapping_service)
    result = await agent.process("Show mappings")

    assert "message" in result
    assert "no" in result["message"].lower() or "upload" in result["message"].lower()
