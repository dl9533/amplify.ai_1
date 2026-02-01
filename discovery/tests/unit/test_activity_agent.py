"""Tests for ActivitySubagent DWA selection management."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.agents.activity_agent import ActivitySubagent
from app.agents.base import BaseSubagent


@pytest.fixture
def activity_agent():
    return ActivitySubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


@pytest.fixture
def mock_dwa_list():
    return [
        MagicMock(id="4.A.1.a.1", name="Analyzing data", gwa_exposure=0.85),
        MagicMock(id="4.A.2.b.2", name="Writing reports", gwa_exposure=0.70),
        MagicMock(id="4.A.3.c.3", name="Coordinating meetings", gwa_exposure=0.45),
    ]


class TestActivitySubagentSetup:
    """Tests for activity agent configuration."""

    def test_activity_agent_extends_base_subagent(self, activity_agent):
        """ActivitySubagent should extend BaseSubagent."""
        assert isinstance(activity_agent, BaseSubagent)

    def test_activity_agent_type_is_activity(self, activity_agent):
        """Agent type should be 'activity'."""
        assert activity_agent.agent_type == "activity"


class TestDwaSelection:
    """Tests for DWA selection management."""

    @pytest.mark.asyncio
    async def test_get_dwas_for_role_mapping(self, activity_agent, mock_dwa_list):
        """Should retrieve DWAs for a mapped O*NET occupation."""
        activity_agent._dwa_repo = AsyncMock()
        activity_agent._dwa_repo.get_by_occupation.return_value = mock_dwa_list

        result = await activity_agent.get_dwas_for_role(
            onet_code="15-1252.00",
        )

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_toggle_dwa_selection(self, activity_agent):
        """Should toggle DWA selection state."""
        role_mapping_id = uuid4()
        dwa_id = "4.A.1.a.1"

        await activity_agent.toggle_dwa(
            role_mapping_id=role_mapping_id,
            dwa_id=dwa_id,
            selected=True,
        )

        assert activity_agent._selections[(str(role_mapping_id), dwa_id)] is True

        await activity_agent.toggle_dwa(
            role_mapping_id=role_mapping_id,
            dwa_id=dwa_id,
            selected=False,
        )

        assert activity_agent._selections[(str(role_mapping_id), dwa_id)] is False

    @pytest.mark.asyncio
    async def test_bulk_select_by_exposure_threshold(self, activity_agent, mock_dwa_list):
        """Should bulk select DWAs above exposure threshold."""
        role_mapping_id = uuid4()
        activity_agent._current_dwas = mock_dwa_list

        await activity_agent.select_above_threshold(
            role_mapping_id=role_mapping_id,
            threshold=0.6,
        )

        # Should select 2 DWAs (0.85 and 0.70, not 0.45)
        selected = [k for k, v in activity_agent._selections.items() if v]
        assert len(selected) == 2


class TestBrainstormingFlow:
    """Tests for brainstorming-style activity selection."""

    @pytest.mark.asyncio
    async def test_process_asks_about_activity_relevance(self, activity_agent, mock_dwa_list):
        """Should ask if activity is relevant to role."""
        activity_agent._current_dwas = mock_dwa_list
        activity_agent._current_dwa_index = 0

        response = await activity_agent.process("Start activity selection")

        assert response.get("message") is not None or response.get("question") is not None
        assert "Analyzing data" in str(response) or mock_dwa_list[0].name in str(response)
