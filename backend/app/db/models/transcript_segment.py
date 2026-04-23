from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, timestamp

if TYPE_CHECKING:
    from .file import File


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"), nullable=False
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)  # In seconds
    end_time: Mapped[float] = mapped_column(Float, nullable=False)  # In seconds
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[timestamp]

    # Relationships
    file: Mapped[File] = relationship(back_populates="transcript_segments")
