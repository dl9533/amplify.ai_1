"""Agent memory service for working, episodic, and semantic memory operations."""
from typing import Any
from uuid import UUID


class AgentMemoryService:
    """Service for managing agent memory across different memory types.

    Supports three types of memory:
    - Working memory: Session-scoped context for current interactions
    - Episodic memory: Interaction history for learning from past experiences
    - Semantic memory: Learned patterns and preferences
    """

    # Working Memory Operations

    async def get_working_memory(
        self,
        session_id: UUID,
        working_memory_repo: Any,
    ) -> dict[str, Any]:
        """Retrieve current session context from working memory.

        Args:
            session_id: The session identifier.
            working_memory_repo: Repository for working memory operations.

        Returns:
            The session context dictionary.
        """
        memory = await working_memory_repo.get_by_session_id(session_id)
        if memory is None:
            return {}
        return memory.context

    async def update_working_memory(
        self,
        session_id: UUID,
        updates: dict[str, Any],
        working_memory_repo: Any,
    ) -> None:
        """Merge new context into existing working memory.

        Args:
            session_id: The session identifier.
            updates: Dictionary of context updates to merge.
            working_memory_repo: Repository for working memory operations.
        """
        memory = await working_memory_repo.get_by_session_id(session_id)
        if memory is None:
            merged_context = updates
        else:
            merged_context = {**memory.context, **updates}
        await working_memory_repo.update(session_id, merged_context)

    async def clear_working_memory(
        self,
        session_id: UUID,
        working_memory_repo: Any,
    ) -> None:
        """Clear working memory when session completes.

        Args:
            session_id: The session identifier.
            working_memory_repo: Repository for working memory operations.
        """
        await working_memory_repo.delete_by_session_id(session_id)

    # Episodic Memory Operations

    async def store_episode(
        self,
        agent_id: UUID,
        episode: dict[str, Any],
        episodic_memory_repo: Any,
    ) -> None:
        """Store an interaction episode for learning.

        Args:
            agent_id: The agent identifier.
            episode: Dictionary containing episode details (action, input, output, feedback).
            episodic_memory_repo: Repository for episodic memory operations.
        """
        await episodic_memory_repo.create(agent_id=agent_id, **episode)

    async def retrieve_similar_episodes(
        self,
        agent_id: UUID,
        query: str,
        limit: int,
        episodic_memory_repo: Any,
    ) -> list[Any]:
        """Retrieve similar past episodes for context.

        Args:
            agent_id: The agent identifier.
            query: Search query to find similar episodes.
            limit: Maximum number of episodes to return.
            episodic_memory_repo: Repository for episodic memory operations.

        Returns:
            List of similar episodes.
        """
        return await episodic_memory_repo.find_similar(
            agent_id=agent_id,
            query=query,
            limit=limit,
        )

    # Semantic Memory Operations

    async def store_pattern(
        self,
        agent_id: UUID,
        pattern: dict[str, Any],
        semantic_memory_repo: Any,
    ) -> None:
        """Store a learned pattern in semantic memory.

        Args:
            agent_id: The agent identifier.
            pattern: Dictionary containing pattern details (pattern_type, description, confidence).
            semantic_memory_repo: Repository for semantic memory operations.
        """
        await semantic_memory_repo.create(agent_id=agent_id, **pattern)

    async def get_patterns(
        self,
        agent_id: UUID,
        pattern_type: str,
        semantic_memory_repo: Any,
    ) -> list[Any]:
        """Retrieve relevant patterns for current context.

        Args:
            agent_id: The agent identifier.
            pattern_type: Type of patterns to retrieve.
            semantic_memory_repo: Repository for semantic memory operations.

        Returns:
            List of matching patterns.
        """
        return await semantic_memory_repo.get_by_agent_and_type(
            agent_id=agent_id,
            pattern_type=pattern_type,
        )
