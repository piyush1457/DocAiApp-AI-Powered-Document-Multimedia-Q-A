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
    """
    from fastapi.responses import FileResponse
    import os

    result = await db.execute(
        select(File).where((File.id == file_id) & (File.user_id == current_user.id))
    )
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if not os.path.exists(file.storage_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        file.storage_path,
        filename=file.original_filename,
        media_type="application/pdf" if file.file_type == FileType.PDF else None,
    )
