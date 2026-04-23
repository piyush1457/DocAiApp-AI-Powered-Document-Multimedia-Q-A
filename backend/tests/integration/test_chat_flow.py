import pytest
import json
import uuid
from unittest.mock import patch, AsyncMock
from app.db.models.file import File, FileStatus, FileType


@pytest.mark.asyncio
async def test_chat_sse_stream_success(client, auth_headers, db_session, test_user):
    """Test authenticated chat SSE stream returns 200."""
    file_id = uuid.uuid4()
    db_file = File(
        id=file_id,
        user_id=test_user.id,
        filename="test.pdf",
        original_filename="test.pdf",
        file_size=1000,
        file_type=FileType.PDF,
        status=FileStatus.READY,
        storage_path="/tmp/test.pdf",
    )
    db_session.add(db_file)
    await db_session.commit()

    async def mock_gen(*args, **kwargs):
        yield "data: " + json.dumps({"type": "token", "content": "Hello"}) + "\n\n"
        yield "data: " + json.dumps({"type": "metadata", "sources": []}) + "\n\n"

    with (
        patch(
            "app.services.vector_service.vector_service.similarity_search",
            AsyncMock(return_value=[]),
        ),
        patch(
            "app.services.llm_service.llm_service.get_chat_response_stream",
            return_value=mock_gen(),
        ),
    ):
        payload = {"file_id": str(file_id), "question": "What is this?", "history": []}
        r = await client.post(
            "/docaiapp/v1/chat/", json=payload, headers=auth_headers
        )
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_chat_unauthenticated(client):
    """Test that unauthenticated chat requests return 401."""
    from app.main import app
    from app.core.dependencies import get_current_user

    app.dependency_overrides.pop(get_current_user, None)

    payload = {"file_id": str(uuid.uuid4()), "question": "Hi", "history": []}
    response = await client.post("/docaiapp/v1/chat/", json=payload)

    assert response.status_code == 401
