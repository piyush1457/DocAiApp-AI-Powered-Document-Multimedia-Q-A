from datetime import datetime, timedelta
import uuid
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    decode_token,
)
from app.core.dependencies import get_db, AuthRateLimiter, get_current_user
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.schemas.user import UserCreate, Token

router = APIRouter()

# Rate limit: 100 attempts per 15 minutes for auth endpoints
auth_limiter = AuthRateLimiter(max_calls=100, period=900)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/register", response_model=Token, dependencies=[Depends(auth_limiter)])
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )

    db_user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(db_user)
    await db.flush()  # Get ID

    # Generate tokens
    access_token = create_access_token(subject=db_user.id)
    refresh_token = create_refresh_token(subject=db_user.id)

    # Store hashed refresh token
    db_refresh = RefreshToken(
        user_id=db_user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_refresh)

    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token, dependencies=[Depends(auth_limiter)])
async def login(
    db: AsyncSession = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    # Identical error message for security
    generic_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
    )

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise generic_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    # Store hashed refresh token
    db_refresh = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(db_refresh)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Body(..., embed=True), db: AsyncSession = Depends(get_db)
):
    try:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError()
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Verify against DB
    token_hash = hash_refresh_token(refresh_token)
    stmt = select(RefreshToken).where(
        (RefreshToken.token_hash == token_hash)
        & (not RefreshToken.is_revoked)

        & (RefreshToken.expires_at > datetime.utcnow())
    )
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token expired or revoked")

    # Rotate token: revoke old one
    db_token.is_revoked = True

    # Issue new tokens
    new_access = create_access_token(subject=user_id)
    new_refresh = create_refresh_token(subject=user_id)

    # Store new hashed refresh token
    new_db_refresh = RefreshToken(
        user_id=uuid.UUID(user_id),
        token_hash=hash_refresh_token(new_refresh),
        expires_at=datetime.utcnow()
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_db_refresh)
    await db.commit()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    refresh_token: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    token_hash = hash_refresh_token(refresh_token)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(is_revoked=True)
    )
    await db.commit()
    return {"message": "Successfully logged out"}
