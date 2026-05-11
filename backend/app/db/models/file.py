from __future__ import annotations
import uuid
from typing import List, Optional, TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, timestamp, updated_timestamp

if TYPE_CHECKING:
    from .user import User
    from .chunk import Chunk
    from .transcript_segment import TranscriptSegment


class FileType(str, Enum):
    PDF = "PDF"
    MP3 = "MP3"
    MP4 = "MP4"
    WAV = "WAV"
    M4A = "M4A"
    WEBM = "WEBM"


class FileStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(SQLEnum(FileType), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)

    status: Mapped[FileStatus] = mapped_column(
        SQLEnum(FileStatus, values_callable=lambda x: [e.value for e in x]), 
        default=FileStatus.UPLOADING
    )
    error_message: Mapped[Optional[str]] = mapped_column(String(1024))

    created_at: Mapped[timestamp]
    updated_at: Mapped[updated_timestamp]

    # Relationships
    owner: Mapped[User] = relationship(back_populates="files")
    chunks: Mapped[List[Chunk]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )
    transcript_segments: Mapped[List[TranscriptSegment]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )
