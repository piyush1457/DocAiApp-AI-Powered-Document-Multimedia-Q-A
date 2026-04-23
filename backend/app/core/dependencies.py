import time
import logging
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from app.core.config import settings
from app.core.security import decode_token
from app.db.base import async_session
from app.db.models.user import User

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


class RateLimiter:
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.redis = redis.from_url(str(settings.REDIS_URL), decode_responses=True)

    async def __call__(
        self, request: Request, current_user: User = Depends(get_current_user)
    ):
        if settings.DEBUG:
            return True
        user_id = str(current_user.id)
        endpoint = request.url.path
        key = f"ratelimit:{user_id}:{endpoint}"

        now = time.time()
        # Sliding window using ZSET
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, now - self.period)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.period)
            res = await pipe.execute()

        request_count = res[1]

        if request_count >= self.max_calls:
            # Calculate wait time
            first_request_time_list = await self.redis.zrange(
                key, 0, 0, withscores=True
            )
            if first_request_time_list:
                retry_after = int(self.period - (now - first_request_time_list[0][1]))
            else:
                retry_after = self.period

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_calls),
                    "X-RateLimit-Remaining": "0",
                },
            )

        request.state.ratelimit_limit = self.max_calls
        request.state.ratelimit_remaining = self.max_calls - request_count - 1
        return True


class AuthRateLimiter:
    """Rate limiter for auth endpoints based on IP."""

    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.redis = redis.from_url(str(settings.REDIS_URL), decode_responses=True)

    async def __call__(self, request: Request):
        if settings.DEBUG:
            return True
        ip = request.client.host
        endpoint = request.url.path
        key = f"authlimit:{ip}:{endpoint}"

        now = time.time()
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zremrangebyscore(key, 0, now - self.period)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, self.period)
            res = await pipe.execute()

        if res[1] >= self.max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Please try again later.",
            )
        return True
