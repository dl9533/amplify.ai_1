"""Discovery session model."""
import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Integer, Enum, func, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SessionStatus(enum.Enum):
    """Discovery session status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DiscoverySession(Base):
    """Discovery session tracking wizard progress."""
    __tablename__ = "discovery_sessions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus),
        default=SessionStatus.DRAFT,
        nullable=False,
    )
    current_step: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    industry_naics_sector: Mapped[str | None] = mapped_column(
        String(2), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    uploads: Mapped[list["DiscoveryUpload"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    role_mappings: Mapped[list["DiscoveryRoleMapping"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DiscoverySession(id={self.id}, status={self.status.value}, step={self.current_step})>"
