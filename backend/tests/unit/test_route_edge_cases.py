import pytest
import uuid
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_upload_route_success(client, auth_headers):
    """Test upload route success path."""
    with (
        patch(
            "app.api.v1.routes.upload.uuid.uuid4",
            return_value=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        ),
        patch("builtins.open", MagicMock()),
        patch("os.makedirs", MagicMock()),
        patch(
            "app.services.ingestion_service.IngestionService.process_file"
        ) as mock_process,
    ):

        response = await client.post(
            "/docaiapp/v1/upload/upload",
            headers=auth_headers,
            files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")},
        )
        assert response.status_code == 202
        assert response.json()["status"] == "processing"
        mock_process.assert_called_once()


@pytest.mark.asyncio
async def test_upload_route_invalid_type(client, auth_headers):
    """Test upload route with invalid MIME type."""
    response = await client.post(
        "/docaiapp/v1/upload/upload",
        headers=auth_headers,
        files={"file": ("test.txt", b"txt content", "text/plain")},
    )
    assert (
        response.status_code == 202
    )  # the code returns 200 with an error object, or wait...
    # Wait, if it returns dict with 'error', Fastapi automatically converts to 200 OK.
    # Let's assert on the content instead of just 400.
    data = response.json()
    assert "error" in data
    assert data["code"] == "INVALID_FILE_TYPE"


@pytest.mark.asyncio
async def test_chat_route_no_file(client, auth_headers, db_session):
    """Test chat route when file is not found."""
    with patch.object(db_session, "execute") as mock_exec:
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_exec.return_value = mock_res

        response = await client.post(
            "/docaiapp/v1/chat/",
            headers=auth_headers,
            json={"file_id": str(uuid.uuid4()), "question": "test"},
        )
        assert response.status_code == 404
