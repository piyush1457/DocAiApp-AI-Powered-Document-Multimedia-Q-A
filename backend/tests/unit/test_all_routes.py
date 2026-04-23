import pytest
import uuid
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_auth_routes_coverage(client):
    """Call all auth routes to ensure they are covered."""
    # Register
    with (
        patch("app.api.v1.routes.auth.get_password_hash", return_value="h"),
        patch("app.api.v1.routes.auth.create_access_token", return_value="a"),
        patch("app.api.v1.routes.auth.create_refresh_token", return_value="r"),
        patch("app.api.v1.routes.auth.hash_refresh_token", return_value="hash"),
    ):
        r = await client.post(
            "/docaiapp/v1/auth/register",
            json={
                "email": f"{uuid.uuid4()}@ex.com",
                "password": "Password123!",
                "full_name": "Test",
            },
        )
        assert r.status_code in [200, 400]

    # Login
    with (
        patch("app.api.v1.routes.auth.verify_password", return_value=True),
        patch("app.api.v1.routes.auth.create_access_token", return_value="a"),
        patch("app.api.v1.routes.auth.create_refresh_token", return_value="r"),
    ):
        r = await client.post(
            "/docaiapp/v1/auth/login",
            data={"username": "test@ex.com", "password": "Password123!"},
        )
        assert r.status_code in [200, 401]


@pytest.mark.asyncio
async def test_file_routes_coverage(client, auth_headers):
    """Call file listing route."""
    r = await client.get("/docaiapp/v1/files/", headers=auth_headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_chat_routes_coverage(client, auth_headers, test_user, db_session):
    """Call chat route with mocked services."""
    from app.db.models.file import File, FileStatus, FileType

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

    with (
        patch(
            "app.services.vector_service.vector_service.search",
            AsyncMock(return_value=[]),
        ),
        patch(
            "app.services.llm_service.llm_service.get_chat_response_stream",
            return_value=(x for x in ["data"]),
        ),
    ):
        r = await client.post(
            "/docaiapp/v1/chat/",
            json={"file_id": str(file_id), "question": "hi", "history": []},
            headers=auth_headers,
        )
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_summary_routes_coverage(client, auth_headers, test_user, db_session):
    """Call summary route."""
    from app.db.models.file import File, FileStatus, FileType
    from app.db.models.chunk import Chunk

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
    db_chunk = Chunk(
        id=uuid.uuid4(),
        file_id=file_id,
        text="chunk text",
        token_count=10,
        page_number=1,
    )
    db_session.add(db_chunk)
    await db_session.commit()

    with (
        patch(
            "app.services.llm_service.llm_service.get_summary",
            AsyncMock(
                return_value={"summary": "sum", "key_topics": [], "word_count": 1}
            ),
        ),
        patch("app.api.v1.routes.summary.redis_client") as mock_redis,
    ):
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        r = await client.get(f"/docaiapp/v1/summary/{file_id}", headers=auth_headers)
        assert r.status_code == 200
