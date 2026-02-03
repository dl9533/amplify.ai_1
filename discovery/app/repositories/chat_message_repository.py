"""Chat message repository."""
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_chat_message import DiscoveryChatMessage


class ChatMessageRepository:
    """Repository for chat message operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        session_id: UUID,
        role: str,
        content: str,
    ) -> DiscoveryChatMessage:
        """Create a new chat message."""
        message = DiscoveryChatMessage(
            session_id=session_id,
            role=role,
            content=content,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_for_session(
        self,
        session_id: UUID,
        limit: int | None = None,
    ) -> Sequence[DiscoveryChatMessage]:
        """Get all messages for a session, ordered by creation time."""
        stmt = (
            select(DiscoveryChatMessage)
            .where(DiscoveryChatMessage.session_id == session_id)
            .order_by(DiscoveryChatMessage.created_at.asc())
        )
        if limit:
            stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_for_session(self, session_id: UUID) -> int:
        """Delete all messages for a session."""
        stmt = select(DiscoveryChatMessage).where(
            DiscoveryChatMessage.session_id == session_id
        )
        result = await self.session.execute(stmt)
        messages = result.scalars().all()

        count = len(messages)
        for m in messages:
            await self.session.delete(m)
        await self.session.commit()
        return count
