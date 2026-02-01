"""Tests for MappingSubagent O*NET role matching."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.agents.mapping_agent import MappingSubagent
from app.agents.base import BaseSubagent


@pytest.fixture
def mapping_agent():
    return MappingSubagent(
        session=MagicMock(id=uuid4()),
        memory_service=AsyncMock(),
    )


@pytest.fixture
def mock_onet_repo():
    repo = AsyncMock()
    repo.search_occupations.return_value = [
        MagicMock(code="15-1252.00", title="Software Developers", score=0.95),
        MagicMock(code="15-1254.00", title="Web Developers", score=0.85),
    ]
    return repo


class TestMappingSubagentSetup:
    """Tests for mapping agent configuration."""

    def test_mapping_agent_extends_base_subagent(self, mapping_agent):
        """MappingSubagent should extend BaseSubagent."""
        assert isinstance(mapping_agent, BaseSubagent)

    def test_mapping_agent_type_is_mapping(self, mapping_agent):
        """Agent type should be 'mapping'."""
        assert mapping_agent.agent_type == "mapping"


class TestOnetMatching:
    """Tests for O*NET occupation matching."""

    @pytest.mark.asyncio
    async def test_suggest_onet_matches_for_role(
        self, mapping_agent, mock_onet_repo
    ):
        """Should suggest O*NET occupations for a source role."""
        result = await mapping_agent.suggest_matches(
            source_role="Software Engineer",
            onet_repo=mock_onet_repo,
            limit=5,
        )

        assert len(result) == 2
        assert result[0].code == "15-1252.00"
        mock_onet_repo.search_occupations.assert_called_once_with(
            query="Software Engineer",
            limit=5,
        )

    @pytest.mark.asyncio
    async def test_confirm_mapping_stores_selection(
        self, mapping_agent, mock_onet_repo
    ):
        """Should store confirmed mapping."""
        role_mapping_id = uuid4()

        await mapping_agent.confirm_mapping(
            role_mapping_id=role_mapping_id,
            onet_code="15-1252.00",
            confidence=0.95,
        )

        assert mapping_agent._confirmed_mappings[str(role_mapping_id)] == {
            "onet_code": "15-1252.00",
            "confidence": 0.95,
        }


class TestBrainstormingFlow:
    """Tests for brainstorming-style role mapping."""

    @pytest.mark.asyncio
    async def test_process_presents_mapping_choices(self, mapping_agent, mock_onet_repo):
        """Should present O*NET choices for unmapped role."""
        mapping_agent._onet_repo = mock_onet_repo
        mapping_agent._current_role = MagicMock(source_role="Data Analyst")

        response = await mapping_agent.process("Map this role")

        assert response.get("message") is not None or response.get("question") is not None
        assert len(response.get("choices", [])) >= 1

    @pytest.mark.asyncio
    async def test_process_handles_none_of_these(self, mapping_agent):
        """Should handle 'none of these' selection."""
        mapping_agent._pending_role_id = uuid4()

        response = await mapping_agent.process("None of these match")

        msg = response.get("message", "").lower() + response.get("question", "").lower()
        assert "search" in msg or "specify" in msg or "custom" in msg

    @pytest.mark.asyncio
    async def test_process_default_state(self, mapping_agent):
        """Should return ready message when no role is being mapped."""
        response = await mapping_agent.process("Hello")
        assert "Ready" in response.get("message", "") or "ready" in response.get("message", "").lower()
