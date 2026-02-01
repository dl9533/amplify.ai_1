"""Discovery activity selection model."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DiscoveryActivitySelection(Base):
    """User selections of DWAs for analysis."""
    __tablename__ = "discovery_activity_selections"

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
    role_mapping_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("discovery_role_mappings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dwa_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("onet_dwa.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected: Mapped[bool] = mapped_column(Boolean, default=True)
    user_modified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    role_mapping: Mapped["DiscoveryRoleMapping"] = relationship(
        back_populates="activity_selections"
    )

    def __repr__(self) -> str:
        return f"<DiscoveryActivitySelection(id={self.id}, dwa={self.dwa_id}, selected={self.selected})>"
