import pytest
import time
import uuid
import asyncio
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.core.dependencies import RateLimiter

@pytest.mark.asyncio
async def test_sliding_window_limit_and_retry_after():
    """Test that the 11th request fails and returns an accurate Retry-After header."""
    # 10 calls per 60 seconds
    max_calls = 10
    period = 60
    limiter = RateLimiter(max_calls=max_calls, period=period)
    
    request = MagicMock()
    request.url.path = "/api/chat"
    user = MagicMock()
    user.id = uuid.uuid4()
    
    # 10 successful requests
    for _ in range(max_calls):
        await limiter(request, current_user=user)
        
    # 11th request should fail
    with pytest.raises(HTTPException) as exc:
        await limiter(request, current_user=user)
        
    assert exc.value.status_code == 429
    retry_after = int(exc.value.headers["Retry-After"])
    assert 0 < retry_after <= period

@pytest.mark.asyncio
async def test_window_slides_correctly():
    """Test that old requests expire and allow new ones within the same window."""
    limiter = RateLimiter(max_calls=1, period=1)
    request = MagicMock()
    request.url.path = "/api/upload"
    user = MagicMock()
    user.id = uuid.uuid4()
    
    # First call
    await limiter(request, current_user=user)
    
    # Immediate second call fails
    with pytest.raises(HTTPException):
        await limiter(request, current_user=user)
        
    # Wait for window to slide
    await asyncio.sleep(1.1)
    
    # Third call succeeds
    await limiter(request, current_user=user)

@pytest.mark.asyncio
async def test_rate_limit_headers_presence():
    """Test that rate limit headers are present in the 429 response."""
    limiter = RateLimiter(max_calls=1, period=10)
    request = MagicMock()
    request.url.path = "/api/test"
    user = MagicMock()
    user.id = uuid.uuid4()
    
    await limiter(request, current_user=user)
    with pytest.raises(HTTPException) as exc:
        await limiter(request, current_user=user)
        
    headers = exc.value.headers
    assert "X-RateLimit-Limit" in headers
    assert headers["X-RateLimit-Remaining"] == "0"
