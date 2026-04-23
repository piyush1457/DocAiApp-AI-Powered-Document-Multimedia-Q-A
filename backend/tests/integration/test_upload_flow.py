import pytest
from unittest.mock import patch, AsyncMock
from app.db.models.file import File, FileStatus


@pytest.mark.asyncio
async def test_full_upload_flow_success(
    client, auth_headers, sample_pdf_bytes, db_session
):
    """Test valid PDF upload returns 202 with file_id."""
    files = {"file": ("test.pdf", sample_pdf_bytes, "application/pdf")}

    with patch(
        "app.api.v1.routes.upload.IngestionService.process_file",
        new_callable=AsyncMock,
    ):
        response = await client.post(
            "/docaiapp/v1/upload/upload", files=files, headers=auth_headers
        )

    assert response.status_code == 202
    body = response.json()
    assert "file_id" in body
    assert body["status"] == "processing"


@pytest.mark.asyncio
async def test_upload_invalid_mime_type(client, auth_headers):
    """Test that uploading an unsupported file type returns error in body."""
    files = {"file": ("test.txt", b"some text", "text/plain")}
    response = await client.post(
        "/docaiapp/v1/upload/upload", files=files, headers=auth_headers
    )
    body = response.json()
    assert "error" in body
    assert body["code"] == "INVALID_FILE_TYPE"


@pytest.mark.asyncio
async def test_upload_oversized_file(client, auth_headers):
    """Test that uploading a file exceeding limit is rejected."""
    large_content = b"0" * 1024
    files = {"file": ("huge.pdf", large_content, "application/pdf")}

    with patch("app.api.v1.routes.upload.MAX_FILE_SIZE", 512):
        response = await client.post(
            "/docaiapp/v1/upload/upload", files=files, headers=auth_headers
        )
        assert response.json()["code"] == "FILE_TOO_LARGE"


@pytest.mark.asyncio
async def test_upload_status_polling(client, auth_headers, sample_pdf_bytes, db_session):
    """Test status polling after upload."""
    files = {"file": ("test.pdf", sample_pdf_bytes, "application/pdf")}

    with patch(
        "app.api.v1.routes.upload.IngestionService.process_file",
        new_callable=AsyncMock,
    ):
        response = await client.post(
            "/docaiapp/v1/upload/upload", files=files, headers=auth_headers
        )

    assert response.status_code == 202
    file_id = response.json()["file_id"]

    # Poll status
    status_resp = await client.get(
        f"/docaiapp/v1/upload/{file_id}/status", headers=auth_headers
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ["uploading", "processing", "ready"]
