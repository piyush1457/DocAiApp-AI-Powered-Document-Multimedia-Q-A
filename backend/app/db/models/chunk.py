from __future__ import annotations
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, timestamp

if TYPE_CHECKING:
    from .file import File


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"), nullable=False
    )

    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Source metadata
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    start_time: Mapped[Optional[float]] = mapped_column(Float)
    end_time: Mapped[Optional[float]] = mapped_column(Float)

    embedding_id: Mapped[Optional[int]] = mapped_column(
        Integer
    )  # Internal index in FAISS

    created_at: Mapped[timestamp]

    # Relationships
    file: Mapped[File] = relationship(back_populates="chunks")
