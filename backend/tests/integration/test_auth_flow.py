import pytest
import uuid
from app.core.security import decode_token

@pytest.mark.asyncio
async def test_full_auth_lifecycle(client):
    """Test register -> login -> access -> logout -> reject."""
    email = f"user_{uuid.uuid4()}@example.com"
    password = "StrongPassword123!"
    
    # 1. Register
    reg_resp = await client.post("/docaiapp/v1/auth/register", json={
        "email": email,
        "password": password
    })
    assert reg_resp.status_code == 200
    tokens = reg_resp.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    # 2. Access protected route
    headers = {"Authorization": f"Bearer {access_token}"}
    prot_resp = await client.get("/docaiapp/v1/files/", headers=headers)
    assert prot_resp.status_code == 200
    
    # 3. Logout
    logout_resp = await client.post("/docaiapp/v1/auth/logout", json={"refresh_token": refresh_token}, headers=headers)
    assert logout_resp.status_code == 200
    
    # 4. Refresh should fail now (if we check revoked status in DB)
    refresh_resp = await client.post("/docaiapp/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_rotation(client):
    """Test that refresh token rotation works and second use of old token is rejected."""
    email = f"rot_{uuid.uuid4()}@example.com"
    password = "StrongPassword123!"
    
    # Register to get tokens
    reg_resp = await client.post("/docaiapp/v1/auth/register", json={"email": email, "password": password})
    tokens = reg_resp.json()
    old_refresh = tokens["refresh_token"]
    
    # First refresh (Success)
    resp1 = await client.post("/docaiapp/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp1.status_code == 200
    new_refresh = resp1.json()["refresh_token"]
    assert new_refresh != old_refresh
    
    # Second refresh with old token (Fail)
    resp2 = await client.post("/docaiapp/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp2.status_code == 401
