import pytest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.mark.asyncio
async def test_upload_route_success(client, auth_headers):
    """Test upload route success path."""
    with (
        patch("shutil.copyfileobj"),
        patch("os.makedirs"),
        patch("builtins.open", MagicMock()),
        patch(
            "app.api.v1.routes.upload.IngestionService.process_file",
            new_callable=AsyncMock,
        ),
    ):
        response = await client.post(
            "/docaiapp/v1/upload/upload",
            headers=auth_headers,
            files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")},
        )
        assert response.status_code == 202
        assert response.json()["status"] == "processing"


@pytest.mark.asyncio
async def test_upload_route_invalid_type(client, auth_headers):
    """Test upload route with invalid MIME type returns error body."""
    response = await client.post(
        "/docaiapp/v1/upload/upload",
        headers=auth_headers,
        files={"file": ("test.txt", b"txt content", "text/plain")},
    )
    # Route returns 200 with error object for invalid type
    data = response.json()
    assert "error" in data
    assert data["code"] == "INVALID_FILE_TYPE"


@pytest.mark.asyncio
async def test_chat_route_no_file(client, auth_headers):
    """Test chat route when file is not found returns 404."""
    response = await client.post(
        "/docaiapp/v1/chat/",
        headers=auth_headers,
        json={"file_id": str(uuid.uuid4()), "question": "test", "history": []},
    )
    assert response.status_code == 404
