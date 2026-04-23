import pytest
import uuid
from datetime import timedelta
from jose import jwt
from pydantic import ValidationError
from app.core.security import create_access_token, ALGORITHM, verify_password, get_password_hash
from app.core.config import settings
from app.schemas.user import UserCreate

def test_access_token_round_trip():
    """Test that an access token can be encoded and correctly decoded."""
    uid = str(uuid.uuid4())
    token = create_access_token(uid)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == uid

def test_expired_token_raises_error():
    """Test that an expired token raises ExpiredSignatureError."""
    token = create_access_token("uid", expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

def test_password_hashing_security():
    """Test that hashed password does not equal raw password and is verifiable."""
    password = "StrongPassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)

def test_password_strength_validation():
    """Test that UserCreate schema enforces password strength policies."""
    # Too short
    with pytest.raises(ValueError, match="at least 8 characters"):
        UserCreate(email="t@e.com", password="Short1!")
    
    # No uppercase
    with pytest.raises(ValueError, match="uppercase"):
        UserCreate(email="t@e.com", password="password123!")
    
    # No number
    with pytest.raises(ValueError, match="number"):
        UserCreate(email="t@e.com", password="Password!")
    
    # No special
    with pytest.raises(ValueError, match="special character"):
        UserCreate(email="t@e.com", password="Password123")
    
    # Valid
    user = UserCreate(email="t@e.com", password="ValidPassword123!")
    assert user.password == "ValidPassword123!"

def test_refresh_token_hashing_logic():
    """Test that refresh token hashing is deterministic and secure."""
    from app.api.v1.routes.auth import hash_refresh_token
    token = "some_random_refresh_token"
    h1 = hash_refresh_token(token)
    h2 = hash_refresh_token(token)
    assert h1 == h2
    assert h1 != token
