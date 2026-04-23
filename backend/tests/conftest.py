import asyncio
import pytest
import uuid
import os
import tempfile
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock, patch

from app.main import app
from app.db.base import Base
from app.db.models.user import User
from app.db.models.file import File
from app.db.models.chunk import Chunk
from app.db.models.transcript_segment import TranscriptSegment
from app.db.models.refresh_token import RefreshToken
from app.core.dependencies import get_db, get_current_user
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash

# Use a temporary file for the database to avoid memory issues with multiple connections
_, db_path = tempfile.mkstemp(suffix=".db")
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

test_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function", autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        # For SQLite, we might need to enable foreign keys if we want enforcement, 
        # but here we want to avoid NoReferencedTableError during creation.
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def test_user(db_session: AsyncSession):
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=f"test_{user_id}@example.com",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def auth_headers(test_user):
    token = create_access_token(subject=test_user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def client(db_session, test_user) -> AsyncGenerator[AsyncClient, None]:
    def override_get_db():
        yield db_session
    
    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    # Also override rate limiters
    from app.api.v1.routes.auth import auth_limiter
    from app.api.v1.routes.upload import upload_limiter
    from app.api.v1.routes.chat import chat_limiter
    from app.api.v1.routes.summary import summary_limiter
    
    app.dependency_overrides[auth_limiter] = lambda: True
    app.dependency_overrides[upload_limiter] = lambda: True
    app.dependency_overrides[chat_limiter] = lambda: True
    app.dependency_overrides[summary_limiter] = lambda: True

    # Mock Redis to avoid connection errors in RateLimiter
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_instance = AsyncMock()
        mock_redis.return_value = mock_instance
        mock_instance.pipeline.return_value.__aenter__.return_value.execute.return_value = [None, 1]
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
    
    app.dependency_overrides.clear()
    
@pytest.fixture(autouse=True)
def mock_external_apis(mocker):
    mocker.patch("app.services.llm_service.groq_client.chat.completions.create")
    mocker.patch("app.services.vector_service.genai.embed_content", 
        return_value={"embedding": [0.1] * 768})
    mocker.patch("app.services.transcription_service.groq_client.audio.transcriptions.create")

@pytest.fixture
def mock_openai(mocker):
    # Mock both Sync and Async clients just in case
    mocker.patch("openai.OpenAI")
    mock_client = mocker.patch("openai.AsyncOpenAI")
    instance = mock_client.return_value
    instance.chat.completions.create = AsyncMock()
    instance.embeddings.create = AsyncMock()
    instance.audio.transcriptions.create = AsyncMock()
    return instance

@pytest.fixture
def sample_pdf_bytes():
    return b"%PDF-1.4\n1 0 obj\n<< /Title (Test) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"

@pytest.fixture
def sample_audio_bytes():
    return b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
