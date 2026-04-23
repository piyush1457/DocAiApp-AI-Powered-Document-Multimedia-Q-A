from pydantic import BaseModel
from typing import List, Optional

class ChapterMarker(BaseModel):
    title: str
    start_time: float
    end_time: float

class SummaryResponse(BaseModel):
    summary: str
    key_topics: List[str]
    word_count: int
    chapter_markers: Optional[List[ChapterMarker]] = None
