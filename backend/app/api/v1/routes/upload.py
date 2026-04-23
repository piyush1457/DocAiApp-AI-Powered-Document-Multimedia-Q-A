import os
import uuid
import shutil
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File as FastFile, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_user, RateLimiter
from app.db.models.file import File, FileStatus, FileType
from app.db.models.user import User
from app.services.ingestion_service import IngestionService
from app.core.exceptions import DocAiError, IngestionError

router = APIRouter()

ALLOWED_EXTENSIONS = {
    "PDF": FileType.PDF,
    "MP3": FileType.MP3,
    "MP4": FileType.MP4,
    "WAV": FileType.WAV,
    "M4A": FileType.M4A,
    "WEBM": FileType.WEBM
}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# 10 uploads per hour per user
upload_limiter = RateLimiter(max_calls=10, period=3600)

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(upload_limiter)])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = FastFile(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Uploads a file and triggers background ingestion.
    """
    # 1. Validate extension
    ext = file.filename.split(".")[-1].upper() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return {
            "error": "Invalid file type",
            "code": "INVALID_FILE_TYPE",
            "details": {"allowed": list(ALLOWED_EXTENSIONS.keys())}
        }

    # 2. Validate size (this is a basic check, real enforcement might need a middleware or reading chunk by chunk)
    # UploadFile might not have 'size' if not spooling to disk yet, but we can check it
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return {
            "error": f"File too large. Max size is 500MB. Got {file_size / (1024*1024):.2f}MB",
            "code": "FILE_TOO_LARGE",
            "details": {"max_size": MAX_FILE_SIZE, "actual_size": file_size}
        }

    # 3. Save file
    upload_id = uuid.uuid4()
    storage_dir = f"/tmp/uploads/{current_user.id}"
    os.makedirs(storage_dir, exist_ok=True)
    
    # Use lowercase extension for compatibility with external APIs like Groq
    storage_filename = f"{upload_id}.{ext.lower()}"
    storage_path = os.path.join(storage_dir, storage_filename)
    
    try:
        with open(storage_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        return {
            "error": "Failed to save file",
            "code": "STORAGE_ERROR",
            "details": {"message": str(e)}
        }

    # 4. Create DB entry
    db_file = File(
        id=upload_id,
        user_id=current_user.id,
        filename=storage_filename,
        original_filename=file.filename,
        file_type=FileType(ext),
        storage_path=storage_path,
        file_size=file_size,
        status=FileStatus.uploading
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    # 5. Trigger background task
    ingestion_service = IngestionService(db)
    background_tasks.add_task(ingestion_service.process_file, db_file.id)

    return {
        "file_id": str(db_file.id),
        "status": "processing"
    }

@router.get("/{file_id}/status")
async def get_file_status(
    file_id: uuid.UUID, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import select
    # Enforce ownership at query level
    stmt = select(File).where((File.id == file_id) & (File.user_id == current_user.id))
    result = await db.execute(stmt)
    file = result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
        
    return {
        "id": str(file.id),
        "status": file.status,
        "error_message": file.error_message
    }
