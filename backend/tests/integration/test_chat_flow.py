import pytest
import json
import uuid
from unittest.mock import patch, AsyncMock
from app.db.models.file import File, FileStatus, FileType


@pytest.mark.asyncio
async def test_chat_sse_stream_success(client, auth_headers, db_session, test_user):
    """Test authenticated chat SSE stream including tokens and metadata."""
    # 1. Create a ready file in DB
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

    # 2. Mock FAISS and LLM
    with (
        patch(
            "app.services.vector_service.vector_service.search",
            AsyncMock(return_value=[]),
        ),
        patch(
            "app.services.llm_service.llm_service.get_chat_response_stream"
        ) as mock_stream,
    ):

        async def mock_gen(*args, **kwargs):
            yield "data: " + json.dumps({"token": "Hello"}) + "\n\n"
            yield "data: " + json.dumps(
                {"metadata": {"sources": [{"page": 1}]}}
            ) + "\n\n"

        mock_stream.return_value = mock_gen()

        # 3. Chat
        payload = {"file_id": str(file_id), "question": "What is this?", "history": []}

        async with client.stream(
            "POST", "/docaiapp/v1/chat/", json=payload, headers=auth_headers
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

            assert any("token" in e for e in events)
            assert any("metadata" in e for e in events)
            assert events[-1]["metadata"]["sources"][0]["page"] == 1


@pytest.mark.asyncio
async def test_chat_unauthenticated(client):
    """Test that unauthenticated chat requests return 401."""
    # Temporarily remove the get_current_user override to test real auth
    from app.main import app
    from app.core.dependencies import get_current_user

    app.dependency_overrides.pop(get_current_user, None)

    payload = {"file_id": str(uuid.uuid4()), "question": "Hi", "history": []}
    response = await client.post("/docaiapp/v1/chat/", json=payload)

    assert response.status_code == 401
