import json
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user, RateLimiter
from app.db.models.user import User
from app.db.models.file import File, FileType
from app.db.models.transcript_segment import TranscriptSegment
from app.schemas.chat import ChatRequest
from app.services.llm_service import llm_service
from app.services.vector_service import vector_service

router = APIRouter()

# 60 chat requests per hour per user
chat_limiter = RateLimiter(max_calls=60, period=3600)

@router.post("/", dependencies=[Depends(chat_limiter)])
async def chat_with_file(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    RAG-based chat endpoint with streaming response.
    """
    # 1. Validate file and ownership
    stmt = select(File).where(
        (File.id == request.file_id) & (File.user_id == current_user.id)
    )
    result = await db.execute(stmt)
    file = result.scalar_one_or_none()
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Chat request: file_id={request.file_id}, question={request.question}")
    
    if not file:
        logger.error(f"File {request.file_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="File not found")

    # 2. Retrieve context from FAISS
    try:
        logger.info(f"Step 1: Ensuring FAISS index is loaded for user {current_user.id}")
        await vector_service.ensure_index_loaded(str(current_user.id), str(request.file_id), db)
        
        logger.info(f"Step 2: Running FAISS similarity search for file {request.file_id}")
        chunks = await vector_service.similarity_search(
            query=request.question,
            user_id=str(current_user.id),
            file_id=str(request.file_id),
            top_k=6
        )
        logger.info(f"Step 3: FAISS returned {len(chunks)} relevant chunks")
    except Exception as e:
        logger.error(f"RAG Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG failed: {str(e)}")

    if not chunks:
        # Fallback if no chunks found but file exists
        chunks = []

    # 3. Enrich with timestamps for audio/video if needed
    context_data = []
    for chunk in chunks:
        chunk_dict = {
            "text_preview": chunk.text,
            "page_number": chunk.metadata.get("page_number"),
            "start_time": chunk.metadata.get("start_time"),
            "end_time": chunk.metadata.get("end_time")
        }
        
        # If it's multimedia and we don't have timestamps on the chunk, enrichment logic:
        if file.file_type in [FileType.MP3, FileType.MP4, FileType.WAV, FileType.M4A, FileType.WEBM]:
            if not chunk_dict["start_time"]:
                # Query transcript_segments for overlap (simplified: find segments containing chunk text)
                # In a real system, we'd use fuzzy matching or exact substring search
                ts_stmt = select(TranscriptSegment).where(
                    (TranscriptSegment.file_id == file.id) & 
                    (TranscriptSegment.text.contains(chunk.text[:50]))
                ).limit(1)
                ts_result = await db.execute(ts_stmt)
                segment = ts_result.scalar_one_or_none()
                if segment:
                    chunk_dict["start_time"] = segment.start_time
                    chunk_dict["end_time"] = segment.end_time
        
        context_data.append(chunk_dict)

    # 4. Stream response
    messages = [{"role": m.role, "content": m.content} for m in request.history]
    messages.append({"role": "user", "content": request.question})

    return StreamingResponse(
        llm_service.get_chat_response_stream(messages, context_data),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )
