import pytest
import uuid
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException
from app.core.dependencies import RateLimiter


def make_fake_redis(pipeline_return_values):
    """Helper to create a fake redis with pipelined results."""
    fake_redis = MagicMock()
    fake_pipe = AsyncMock()
    fake_pipe.__aenter__ = AsyncMock(return_value=fake_pipe)
    fake_pipe.__aexit__ = AsyncMock(return_value=None)
    fake_pipe.execute = AsyncMock(return_value=pipeline_return_values)
    fake_pipe.zremrangebyscore = MagicMock()
    fake_pipe.zcard = MagicMock()
    fake_pipe.zadd = MagicMock()
    fake_pipe.expire = MagicMock()
    fake_redis.pipeline = MagicMock(return_value=fake_pipe)
    fake_redis.zrange = AsyncMock(return_value=[("timestamp", 1000.0)])
    return fake_redis


@pytest.mark.asyncio
async def test_sliding_window_limit_and_retry_after():
    """Test that the 11th request fails and returns an accurate Retry-After header."""
    max_calls = 10
    period = 60
    limiter = RateLimiter(max_calls=max_calls, period=period)

    request = MagicMock()
    request.url.path = "/api/chat"
    request.state = MagicMock()
    user = MagicMock()
    user.id = uuid.uuid4()

    # Simulate request_count = max_calls (limit exceeded)
    limiter.redis = make_fake_redis([None, max_calls, None, None])

    with pytest.raises(HTTPException) as exc:
        await limiter(request, current_user=user)

    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


@pytest.mark.asyncio
async def test_window_slides_correctly():
    """Test that requests below the limit pass and over the limit fail."""
    limiter = RateLimiter(max_calls=2, period=10)

    request = MagicMock()
    request.url.path = "/api/upload"
    request.state = MagicMock()
    user = MagicMock()
    user.id = uuid.uuid4()

    # Under limit — request_count = 1
    limiter.redis = make_fake_redis([None, 1, None, None])
    result = await limiter(request, current_user=user)
    assert result is True

    # Over limit — request_count = 2
    limiter.redis = make_fake_redis([None, 2, None, None])
    with pytest.raises(HTTPException) as exc:
        await limiter(request, current_user=user)
    assert exc.value.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_headers_presence():
    """Test that rate limit headers are present in the 429 response."""
    limiter = RateLimiter(max_calls=1, period=10)

    request = MagicMock()
    request.url.path = "/api/test"
    request.state = MagicMock()
    user = MagicMock()
    user.id = uuid.uuid4()

    # Simulate limit exceeded (count == max_calls)
    limiter.redis = make_fake_redis([None, 1, None, None])

    with pytest.raises(HTTPException) as exc:
        await limiter(request, current_user=user)

    headers = exc.value.headers
    assert "X-RateLimit-Limit" in headers
    assert headers["X-RateLimit-Remaining"] == "0"
