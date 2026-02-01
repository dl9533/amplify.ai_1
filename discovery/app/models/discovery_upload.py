"""Discovery upload model."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DiscoveryUpload(Base):
    """Uploaded file metadata and schema detection."""
    __tablename__ = "discovery_uploads"

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
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_mappings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    detected_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    session: Mapped["DiscoverySession"] = relationship(back_populates="uploads")

    def __repr__(self) -> str:
        return f"<DiscoveryUpload(id={self.id}, file_name={self.file_name})>"
