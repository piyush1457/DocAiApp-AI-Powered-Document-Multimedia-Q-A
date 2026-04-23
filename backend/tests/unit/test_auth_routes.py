import pytest
import uuid
from unittest.mock import patch


@pytest.mark.asyncio
async def test_register_success(client):
    """Test user registration success path."""
    response = await client.post(
        "/docaiapp/v1/auth/register",
        json={
            "email": f"new_{uuid.uuid4()}@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    """Test user login success path."""
    with patch("app.api.v1.routes.auth.verify_password", return_value=True):
        response = await client.post(
            "/docaiapp/v1/auth/login",
            data={"username": test_user.email, "password": "Password123!"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Test that registering with duplicate email returns 400."""
    email = f"dup_{uuid.uuid4()}@example.com"
    # First registration
    await client.post(
        "/docaiapp/v1/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    # Second registration with same email
    response = await client.post(
        "/docaiapp/v1/auth/register",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 400
