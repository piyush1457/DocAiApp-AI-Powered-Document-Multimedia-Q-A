import pytest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.ingestion_service import IngestionService
from app.db.models.file import File, FileStatus, FileType
from app.db.models.user import User

@pytest.fixture
async def test_file(db_session, test_user):
    file = File(
        id=uuid.uuid4(),
        user_id=test_user.id,
        filename="test.pdf",
        original_filename="test.pdf",
        storage_path="test.pdf",
        file_type=FileType.PDF,
        file_size=1000,
        status=FileStatus.PROCESSING
    )
    db_session.add(file)
    await db_session.commit()
    return file

@pytest.mark.asyncio
async def test_process_file_pdf_success(db_session, test_file):
    """Test ingestion service with real DB and mocked parser/vector store."""
    service = IngestionService(db_session)
    
    with patch("app.services.ingestion_service.parse_pdf") as mock_parse, \
         patch("app.services.ingestion_service.FAISSVectorStore.add_chunks", return_value=[123]):
        
        mock_parse.return_value = [{"text": "page 1", "page_number": 1}]
        
        await service.process_file(test_file.id)
        
        # Verify status update in DB
        await db_session.refresh(test_file)
        assert test_file.status == FileStatus.READY
        
        # Verify chunks created
        from app.db.models.chunk import Chunk
        from sqlalchemy import select
        res = await db_session.execute(select(Chunk).where(Chunk.file_id == test_file.id))
        chunks = res.scalars().all()
        assert len(chunks) == 1
        assert chunks[0].text == "page 1"

@pytest.mark.asyncio
async def test_process_file_audio_success(db_session, test_user):
    """Test ingestion service for audio with real DB."""
    service = IngestionService(db_session)
    file = File(
        id=uuid.uuid4(),
        user_id=test_user.id,
        filename="test.mp3",
        original_filename="test.mp3",
        storage_path="test.mp3",
        file_type=FileType.MP3,
        file_size=2000,
        status=FileStatus.PROCESSING
    )
    db_session.add(file)
    await db_session.commit()

    with patch("app.services.ingestion_service.TranscriptionService.transcribe_file") as mock_transcribe, \
         patch("app.services.ingestion_service.FAISSVectorStore.add_chunks", return_value=[456]):
        
        mock_transcribe.return_value = [{"text": "hello", "start": 0, "end": 2, "confidence": 0.9}]
        
        await service.process_file(file.id)
        
        await db_session.refresh(file)
        assert file.status == FileStatus.READY

@pytest.mark.asyncio
async def test_process_file_not_found(db_session):
    """Test ingestion service when file ID doesn't exist."""
    service = IngestionService(db_session)
    # Should just return without error
    await service.process_file(uuid.uuid4())
