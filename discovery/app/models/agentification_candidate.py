"""Agentification candidate model."""
import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, Float, Boolean, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PriorityTier(enum.Enum):
    """Priority tier for agentification candidates."""
    NOW = "now"
    NEXT_QUARTER = "next_quarter"
    FUTURE = "future"


class AgentificationCandidate(Base):
    """Candidate agents identified for potential build."""
    __tablename__ = "agentification_candidates"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("discovery_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_mapping_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("discovery_role_mappings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority_tier: Mapped[PriorityTier] = mapped_column(
        Enum(PriorityTier),
        nullable=False,
    )
    estimated_impact: Mapped[float | None] = mapped_column(Float, nullable=True)
    selected_for_build: Mapped[bool] = mapped_column(Boolean, default=False)
    intake_request_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<AgentificationCandidate(id={self.id}, name={self.name}, tier={self.priority_tier.value})>"
