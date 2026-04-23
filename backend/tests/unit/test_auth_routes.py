import pytest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import status

@pytest.mark.asyncio
async def test_register_success(client):
    """Test user registration success path."""
    with patch("app.api.v1.routes.auth.get_password_hash", return_value="hashed"), \
         patch("app.api.v1.routes.auth.create_access_token", return_value="access"), \
         patch("app.api.v1.routes.auth.create_refresh_token", return_value="refresh"), \
         patch("app.api.v1.routes.auth.hash_refresh_token", return_value="hash"):
        
        response = await client.post(
            "/docaiapp/v1/auth/register",
            json={
                "email": f"new_{uuid.uuid4()}@example.com",
                "password": "Password123!",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access"
        assert data["refresh_token"] == "refresh"

@pytest.mark.asyncio
async def test_login_success(client, test_user):
    """Test user login success path."""
    with patch("app.api.v1.routes.auth.verify_password", return_value=True), \
         patch("app.api.v1.routes.auth.create_access_token", return_value="access"), \
         patch("app.api.v1.routes.auth.create_refresh_token", return_value="refresh"):
        
        response = await client.post(
            "/docaiapp/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "Password123!"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access"
