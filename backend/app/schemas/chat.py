from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class ChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    file_id: uuid.UUID
    question: str = Field(..., max_length=1000)
    history: List[ChatMessage] = Field(default_factory=list, max_items=10)

class SourceMetadata(BaseModel):
    page_number: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    text_preview: str

class ChatResponseMetadata(BaseModel):
    sources: List[SourceMetadata]
