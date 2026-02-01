import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.memory_service import AgentMemoryService


@pytest.fixture
def memory_service():
    return AgentMemoryService()


@pytest.fixture
def mock_repos():
    return {
        "working_memory_repo": AsyncMock(),
        "episodic_memory_repo": AsyncMock(),
        "semantic_memory_repo": AsyncMock(),
    }


class TestWorkingMemory:
    """Tests for working memory operations."""

    @pytest.mark.asyncio
    async def test_get_working_memory_returns_session_context(
        self, memory_service, mock_repos
    ):
        """Should retrieve current session context from working memory."""
        session_id = uuid4()
        mock_repos["working_memory_repo"].get_by_session_id.return_value = MagicMock(
            context={"current_step": "upload", "last_action": "file_selected"}
        )

        result = await memory_service.get_working_memory(
            session_id=session_id,
            working_memory_repo=mock_repos["working_memory_repo"],
        )

        assert result["current_step"] == "upload"
        mock_repos["working_memory_repo"].get_by_session_id.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_update_working_memory_merges_context(
        self, memory_service, mock_repos
    ):
        """Should merge new context into existing working memory."""
        session_id = uuid4()
        mock_repos["working_memory_repo"].get_by_session_id.return_value = MagicMock(
            context={"current_step": "upload"}
        )

        await memory_service.update_working_memory(
            session_id=session_id,
            updates={"last_action": "column_mapped"},
            working_memory_repo=mock_repos["working_memory_repo"],
        )

        mock_repos["working_memory_repo"].update.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_working_memory_on_session_complete(
        self, memory_service, mock_repos
    ):
        """Should clear working memory when session completes."""
        session_id = uuid4()

        await memory_service.clear_working_memory(
            session_id=session_id,
            working_memory_repo=mock_repos["working_memory_repo"],
        )

        mock_repos["working_memory_repo"].delete_by_session_id.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_working_memory_returns_empty_dict_when_none(
        self, memory_service, mock_repos
    ):
        """Should return empty dict when no memory exists for session."""
        session_id = uuid4()
        mock_repos["working_memory_repo"].get_by_session_id.return_value = None

        result = await memory_service.get_working_memory(
            session_id=session_id,
            working_memory_repo=mock_repos["working_memory_repo"],
        )

        assert result == {}
        mock_repos["working_memory_repo"].get_by_session_id.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_update_working_memory_handles_missing_session(
        self, memory_service, mock_repos
    ):
        """Should use updates as context when session not found."""
        session_id = uuid4()
        mock_repos["working_memory_repo"].get_by_session_id.return_value = None
        updates = {"current_step": "upload", "last_action": "started"}

        await memory_service.update_working_memory(
            session_id=session_id,
            updates=updates,
            working_memory_repo=mock_repos["working_memory_repo"],
        )

        mock_repos["working_memory_repo"].update.assert_called_once_with(session_id, updates)


class TestEpisodicMemory:
    """Tests for episodic memory operations."""

    @pytest.mark.asyncio
    async def test_store_episode_saves_interaction(
        self, memory_service, mock_repos
    ):
        """Should store an interaction episode for learning."""
        agent_id = uuid4()
        episode = {
            "action": "suggested_mapping",
            "input": "Software Engineer",
            "output": "15-1252.00",
            "feedback": "accepted",
        }

        await memory_service.store_episode(
            agent_id=agent_id,
            episode=episode,
            episodic_memory_repo=mock_repos["episodic_memory_repo"],
        )

        mock_repos["episodic_memory_repo"].create.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_similar_episodes(
        self, memory_service, mock_repos
    ):
        """Should retrieve similar past episodes for context."""
        agent_id = uuid4()
        mock_repos["episodic_memory_repo"].find_similar.return_value = [
            MagicMock(action="suggested_mapping", feedback="accepted"),
            MagicMock(action="suggested_mapping", feedback="rejected"),
        ]

        result = await memory_service.retrieve_similar_episodes(
            agent_id=agent_id,
            query="Software Engineer mapping",
            limit=5,
            episodic_memory_repo=mock_repos["episodic_memory_repo"],
        )

        assert len(result) == 2


class TestSemanticMemory:
    """Tests for semantic memory operations."""

    @pytest.mark.asyncio
    async def test_store_learned_pattern(
        self, memory_service, mock_repos
    ):
        """Should store a learned pattern in semantic memory."""
        agent_id = uuid4()
        pattern = {
            "pattern_type": "role_mapping_preference",
            "description": "User prefers exact title matches",
            "confidence": 0.85,
        }

        await memory_service.store_pattern(
            agent_id=agent_id,
            pattern=pattern,
            semantic_memory_repo=mock_repos["semantic_memory_repo"],
        )

        mock_repos["semantic_memory_repo"].create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_patterns_for_context(
        self, memory_service, mock_repos
    ):
        """Should retrieve relevant patterns for current context."""
        agent_id = uuid4()
        mock_repos["semantic_memory_repo"].get_by_agent_and_type.return_value = [
            MagicMock(pattern_type="role_mapping_preference", confidence=0.85),
        ]

        result = await memory_service.get_patterns(
            agent_id=agent_id,
            pattern_type="role_mapping_preference",
            semantic_memory_repo=mock_repos["semantic_memory_repo"],
        )

        assert len(result) == 1
        assert result[0].confidence == 0.85
