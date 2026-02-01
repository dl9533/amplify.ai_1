"""Discovery role mapping model."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Float, Boolean, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DiscoveryRoleMapping(Base):
    """Mapping between uploaded roles and O*NET occupations."""
    __tablename__ = "discovery_role_mappings"

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
    source_role: Mapped[str] = mapped_column(String(255), nullable=False)
    onet_code: Mapped[str | None] = mapped_column(
        String(10),
        ForeignKey("onet_occupations.code", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    session: Mapped["DiscoverySession"] = relationship(back_populates="role_mappings")
    activity_selections: Mapped[list["DiscoveryActivitySelection"]] = relationship(
        back_populates="role_mapping", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DiscoveryRoleMapping(id={self.id}, role={self.source_role}, onet={self.onet_code})>"
