"""Unit tests for the DiscoveryOrchestrator."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.agents.orchestrator import DiscoveryOrchestrator
from app.enums import DiscoveryStep


@pytest.fixture
def orchestrator():
    return DiscoveryOrchestrator(
        session=MagicMock(id=uuid4(), current_step=DiscoveryStep.UPLOAD),
        memory_service=AsyncMock(),
    )


@pytest.fixture
def mock_subagents():
    return {
        "upload": AsyncMock(),
        "mapping": AsyncMock(),
        "activity": AsyncMock(),
        "analysis": AsyncMock(),
        "roadmap": AsyncMock(),
    }


class TestOrchestratorRouting:
    """Tests for message routing to subagents."""

    @pytest.mark.asyncio
    async def test_routes_to_upload_agent_on_upload_step(
        self, orchestrator, mock_subagents
    ):
        """Should route to UploadSubagent during upload step."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.UPLOAD
        mock_subagents["upload"].process.return_value = {"step_complete": False}

        await orchestrator.process("I have a file")

        mock_subagents["upload"].process.assert_called_once()

    @pytest.mark.asyncio
    async def test_routes_to_mapping_agent_on_mapping_step(
        self, orchestrator, mock_subagents
    ):
        """Should route to MappingSubagent during mapping step."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.MAP_ROLES
        mock_subagents["mapping"].process.return_value = {"step_complete": False}

        await orchestrator.process("Map this role")

        mock_subagents["mapping"].process.assert_called_once()

    @pytest.mark.asyncio
    async def test_routes_to_activity_agent_on_activity_step(
        self, orchestrator, mock_subagents
    ):
        """Should route to ActivitySubagent during activity step."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.SELECT_ACTIVITIES
        mock_subagents["activity"].process.return_value = {"step_complete": False}

        await orchestrator.process("Select activities")

        mock_subagents["activity"].process.assert_called_once()


class TestStepTransitions:
    """Tests for wizard step transitions."""

    @pytest.mark.asyncio
    async def test_advance_step_on_completion(self, orchestrator, mock_subagents):
        """Should advance to next step when current completes."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.UPLOAD
        mock_subagents["upload"].process.return_value = {"step_complete": True}

        await orchestrator.process("Done uploading")

        assert orchestrator._session.current_step == DiscoveryStep.MAP_ROLES

    @pytest.mark.asyncio
    async def test_stay_on_step_if_not_complete(self, orchestrator, mock_subagents):
        """Should stay on current step if not complete."""
        orchestrator._subagents = mock_subagents
        orchestrator._session.current_step = DiscoveryStep.MAP_ROLES
        mock_subagents["mapping"].process.return_value = {"step_complete": False}

        await orchestrator.process("Still mapping")

        assert orchestrator._session.current_step == DiscoveryStep.MAP_ROLES


class TestConversationManagement:
    """Tests for conversation thread management."""

    @pytest.mark.asyncio
    async def test_maintains_single_conversation_thread(self, orchestrator, mock_subagents):
        """Should maintain one conversation thread per session."""
        orchestrator._subagents = mock_subagents
        mock_subagents["upload"].process.return_value = {"step_complete": False}

        assert orchestrator._conversation_id is not None

        conversation_id = orchestrator._conversation_id
        await orchestrator.process("Message 1")
        await orchestrator.process("Message 2")

        assert orchestrator._conversation_id == conversation_id

    @pytest.mark.asyncio
    async def test_stores_messages_in_history(self, orchestrator, mock_subagents):
        """Should store user and agent messages."""
        orchestrator._subagents = mock_subagents
        mock_subagents["upload"].process.return_value = {
            "message": "What file?", "step_complete": False
        }

        await orchestrator.process("Hello")

        assert len(orchestrator._message_history) >= 2  # User + Agent
