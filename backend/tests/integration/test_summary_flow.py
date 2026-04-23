import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from app.db.models.file import File, FileStatus, FileType

@pytest.mark.asyncio
async def test_summary_caching_flow(client, auth_headers, db_session, test_user):
    """Test that summary is generated once and then served from cache."""
    file_id = uuid.uuid4()
    db_file = File(
        id=file_id,
        user_id=test_user.id,
        filename="test.pdf",
        original_filename="test.pdf",
        file_size=1000,
        file_type=FileType.PDF,
        status=FileStatus.READY,
        storage_path="/tmp/test.pdf"
    )
    db_session.add(db_file)
    await db_session.commit()
    
    from app.db.models.chunk import Chunk
    db_chunk = Chunk(
        id=uuid.uuid4(),
        file_id=file_id,
        text="chunk text",
        token_count=10,
        page_number=1
    )
    db_session.add(db_chunk)
    await db_session.commit()
    
    summary_data = {"summary": "Generated summary", "key_topics": ["T1"], "word_count": 100}
    
    class FakeRedis:
        def __init__(self):
            self.store = {}
        async def get(self, key):
            return self.store.get(key)
        async def setex(self, key, ttl, val):
            self.store[key] = val
    
    fake_redis = FakeRedis()
    
    with patch("app.services.llm_service.llm_service.get_summary", AsyncMock(return_value=summary_data)) as mock_sum, \
         patch("app.api.v1.routes.summary.redis_client", fake_redis): # To avoid real redis
        
        # 1. First request -> Calls LLM
        response = await client.get(f"/docaiapp/v1/summary/{file_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["summary"] == "Generated summary"
        assert mock_sum.call_count == 1
        
        # 2. Second request -> Served from Redis cache
        response = await client.get(f"/docaiapp/v1/summary/{file_id}", headers=auth_headers)
        assert response.status_code == 200
        assert mock_sum.call_count == 1 # Still 1
