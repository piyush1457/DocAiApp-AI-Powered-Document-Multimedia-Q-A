"""
File management routes.
"""

from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.dependencies import get_db, get_current_user
from app.db.models.user import User
from app.db.models.file import File, FileType
from app.schemas.file import File as FileSchema

router = APIRouter()


@router.get("/", response_model=List[FileSchema])
async def list_files(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Lists all files belonging to the current user.
    """
    result = await db.execute(select(File).where(File.user_id == current_user.id))
    return result.scalars().all()


@router.get("/{file_id}", response_model=FileSchema)
async def get_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gets details of a specific file.
    """
    result = await db.execute(
        select(File).where((File.id == file_id) & (File.user_id == current_user.id))
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.delete("/{file_id}")
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes a file and its associated data.
    """
    result = await db.execute(
        select(File).where((File.id == file_id) & (File.user_id == current_user.id))
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    await db.delete(file)
    await db.commit()

    # Clean up Vector Store
    from app.services.vector_service import vector_service

    vector_service.delete_by_file_id(str(current_user.id), str(file_id))

    # Invalidate cache
    from app.services.cache_service import cache_service

    await cache_service.delete_pattern(f"summary:{file_id}")
    await cache_service.delete_pattern(f"*:{file_id}")


@router.get("/{file_id}/content")
async def get_file_content(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the file content for viewing/streaming.
    On Vercel: if storage_path is a Blob URL, redirect to it (survives cold starts).
    If local file is missing on ephemeral disk, return 410 with actionable message.
    """
    from fastapi.responses import FileResponse, RedirectResponse
    import os
    import mimetypes

    result = await db.execute(
        select(File).where((File.id == file_id) & (File.user_id == current_user.id))
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Blob URL -> redirect (public URL, no need to proxy through serverless)
    if file.storage_path.startswith("http://") or file.storage_path.startswith(
        "https://"
    ):
        # Use 307 to preserve auth not needed; browser/axios will follow automatically
        return RedirectResponse(url=file.storage_path, status_code=307)

    # Try local file, with support for blob cache re-download via storage_service
    try:
        from app.services.storage_service import storage_service as _storage

        # If local missing but blob token configured, this will attempt download
        # (in case DB still has local path from before blob was enabled)
        local_path = _storage.ensure_local(file.storage_path)
        # If ensure_local downloaded a blob, use that path
        storage_path = local_path
    except FileNotFoundError as e:
        from app.core.config import settings as _settings

        msg = str(e)
        # Propagate specific Blob token guidance from storage_service
        if "BLOB_STORE_ID" in msg or "BLOB_READ_WRITE_TOKEN" in msg:
            raise HTTPException(status_code=410, detail=msg)
        if _settings.is_blob_enabled:
            raise HTTPException(
                status_code=410,
                detail="File expired from ephemeral storage and could not be restored from Blob. Please re-upload.",
            )
        if _settings.is_vercel:
            raise HTTPException(
                status_code=410,
                detail="File not found on Vercel ephemeral disk (/tmp). "
                "Files do not persist across serverless restarts. "
                "Add BLOB_READ_WRITE_TOKEN or VERCEL_BLOB_READ_WRITE_TOKEN in Vercel dashboard -> Storage -> Blob Store -> .env.local -> copy token to Project Settings -> Environment Variables, then Redeploy (uncheck Build Cache) and re-upload.",
            )
        raise HTTPException(status_code=404, detail=msg)

    if not os.path.exists(storage_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Determine media type for video/audio (FileResponse will guess if None, but be explicit)
    media_type = None
    if file.file_type == FileType.PDF:
        media_type = "application/pdf"
    else:
        guessed, _ = mimetypes.guess_type(file.original_filename)
        media_type = guessed

    return FileResponse(
        storage_path,
        filename=file.original_filename,
        media_type=media_type,
    )
