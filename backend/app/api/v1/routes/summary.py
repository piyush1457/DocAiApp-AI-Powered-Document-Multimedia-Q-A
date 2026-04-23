import json
import uuid
import redis.asyncio as redis
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user, RateLimiter
from app.db.models.user import User
from app.db.models.file import File, FileType
from app.db.models.chunk import Chunk
from app.db.models.transcript_segment import TranscriptSegment
from app.schemas.summary import SummaryResponse, ChapterMarker
from app.services.llm_service import llm_service

router = APIRouter()

# 20 summary requests per hour per user
summary_limiter = RateLimiter(max_calls=20, period=3600)

# Redis client initialization
redis_client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)

@router.get("/{file_id}", response_model=SummaryResponse, dependencies=[Depends(summary_limiter)])
async def get_summary(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns a summary of the file, with logical chapters for multimedia.
    Uses Redis caching and map-reduce for large files.
    """
    # 1. Check Redis Cache
    cache_key = f"summary:{file_id}"
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        return SummaryResponse(**json.loads(cached_data))

    # 2. Validate file and ownership
    stmt = select(File).where(
        (File.id == file_id) & (File.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # 3. Retrieve all chunks
    chunk_stmt = select(Chunk).where(Chunk.file_id == file_id).order_by(Chunk.page_number, Chunk.start_time)
    chunk_result = await db.execute(chunk_stmt)
    chunks = chunk_result.scalars().all()
    
    if not chunks:
        raise HTTPException(
            status_code=400, 
            detail=f"File is not ready for querying. Current status: {file.status}"
        )

    chunk_texts = [c.text for c in chunks]

    # 4. Generate Summary (Map-Reduce if > 20 chunks)
    summary_data = await llm_service.get_summary(chunk_texts)
    
    # 5. Generate Chapters for audio/video
    chapter_markers = None
    if file.file_type in [FileType.MP3, FileType.MP4, FileType.WAV, FileType.M4A, FileType.WEBM]:
        # Fetch full transcript for chapter segmentation
        ts_stmt = select(TranscriptSegment).where(TranscriptSegment.file_id == file_id).order_by(TranscriptSegment.start_time)
        ts_result = await db.execute(ts_stmt)
        segments = ts_result.scalars().all()
        full_transcript = "\n".join([f"[{s.start_time}-{s.end_time}] {s.text}" for s in segments])
        
        if full_transcript:
            chapters_raw = await llm_service.generate_chapter_markers(full_transcript)
            chapter_markers = [ChapterMarker(**c) for c in chapters_raw]

    response_data = SummaryResponse(
        summary=summary_data["summary"],
        key_topics=summary_data["key_topics"],
        word_count=summary_data["word_count"],
        chapter_markers=chapter_markers
    )

    # 6. Cache in Redis (24 hours TTL)
    await redis_client.setex(
        cache_key,
        86400,
        response_data.model_dump_json()
    )

    return response_data
