from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
import bcrypt
from app.core.config import settings

ALGORITHM = "HS256"


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    import uuid

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        import hashlib

        pw_hash = hashlib.sha256(plain_password.encode("utf-8")).digest()
        return bcrypt.checkpw(pw_hash, hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    # Use bcrypt with salt (12 rounds)
    # We truncate to 72 chars to avoid bcrypt limits
    # But usually it's better to hash the password first with SHA256 if it's long
    import hashlib

    pw_hash = hashlib.sha256(password.encode("utf-8")).digest()
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pw_hash, salt)
    return hashed.decode("utf-8")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
