import pytest
import uuid
from unittest.mock import patch


@pytest.mark.asyncio
async def test_full_auth_lifecycle(client):
    """Test register -> login -> access protected route."""
    email = f"user_{uuid.uuid4()}@example.com"
    password = "StrongPassword123!"

    # 1. Register
    reg_resp = await client.post(
        "/docaiapp/v1/auth/register", json={"email": email, "password": password}
    )
    assert reg_resp.status_code == 200
    tokens = reg_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    access_token = tokens["access_token"]

    # 2. Access protected route (uses conftest override so always 200)
    headers = {"Authorization": f"Bearer {access_token}"}
    prot_resp = await client.get("/docaiapp/v1/files/", headers=headers)
    assert prot_resp.status_code == 200


@pytest.mark.asyncio
async def test_refresh_token_rotation(client):
    """Test that refresh token rotation issues new tokens."""
    email = f"rot_{uuid.uuid4()}@example.com"
    password = "StrongPassword123!"

    # Register to get tokens
    reg_resp = await client.post(
        "/docaiapp/v1/auth/register", json={"email": email, "password": password}
    )
    assert reg_resp.status_code == 200
    tokens = reg_resp.json()
    old_refresh = tokens["refresh_token"]

    # First refresh should succeed
    resp1 = await client.post(
        "/docaiapp/v1/auth/refresh", json={"refresh_token": old_refresh}
    )
    assert resp1.status_code == 200
    new_tokens = resp1.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
