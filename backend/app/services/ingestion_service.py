import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.file import File, FileStatus, FileType
from app.db.models.chunk import Chunk
from app.utils.file_parser import parse_pdf
from app.utils.chunker import RecursiveCharacterTextSplitter
from app.services.transcription_service import TranscriptionService
from app.services.vector_service import FAISSVectorStore
from app.core.exceptions import IngestionError

class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.transcription_service = TranscriptionService()
        self.vector_store = FAISSVectorStore()
        self.chunker = RecursiveCharacterTextSplitter()

    async def process_file(self, file_id: uuid.UUID):
        """
        Background task to process the uploaded file.
        """
        # Fetch file from DB
        stmt = select(File).where(File.id == file_id)
        result = await self.db.execute(stmt)
        file = result.scalar_one_or_none()
        
        if not file:
            return

        try:
            file.status = FileStatus.processing
            await self.db.commit()

            chunks_to_create = []

            if file.file_type == FileType.PDF:
                # PDF Parsing
                pages = parse_pdf(file.storage_path)
                for page in pages:
                    page_chunks = self.chunker.create_chunks(
                        text=page["text"],
                        metadata={"page_number": page["page_number"]}
                    )
                    chunks_to_create.extend(page_chunks)

            elif file.file_type in [FileType.MP3, FileType.MP4, FileType.WAV, FileType.M4A, FileType.WEBM]:
                # Transcription
                segments = await self.transcription_service.transcribe_file(
                    file_path=file.storage_path,
                    file_id=file_id,
                    db=self.db
                )
                # Chunk segments
                for seg in segments:
                    seg_chunks = self.chunker.create_chunks(
                        text=seg["text"],
                        metadata={
                            "start_time": seg["start"],
                            "end_time": seg["end"]
                        }
                    )
                    chunks_to_create.extend(seg_chunks)
            
            # Save chunks to DB and prepare for vector store
            db_chunks = []
            for i, chunk_data in enumerate(chunks_to_create):
                db_chunk = Chunk(
                    file_id=file_id,
                    text=chunk_data.text,
                    token_count=chunk_data.token_count,
                    page_number=chunk_data.metadata.get("page_number"),
                    start_time=chunk_data.metadata.get("start_time"),
                    end_time=chunk_data.metadata.get("end_time")
                )
                self.db.add(db_chunk)
                db_chunks.append(db_chunk)

            # Add to Vector Store
            await self.vector_store.add_chunks(db_chunks, str(file.user_id))

            file.status = FileStatus.ready
            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            file.status = FileStatus.failed
            file.error_message = str(e)
            await self.db.commit()
            raise IngestionError(f"Ingestion failed for file {file_id}: {str(e)}")
