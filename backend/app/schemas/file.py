"""
Pydantic schemas for File domain.
"""

import uuid
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.db.models.file import FileType, FileStatus

class FileBase(BaseModel):
    filename: str
    file_type: FileType

class FileCreate(FileBase):
    pass

class File(FileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    file_size: int
    original_filename: str
    status: FileStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    file_id: uuid.UUID
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    answer: str
    context_used: List[str]
