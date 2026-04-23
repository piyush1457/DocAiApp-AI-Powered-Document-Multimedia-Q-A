import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, AsyncMock, patch
from app.core.dependencies import get_current_user, AuthRateLimiter

from jose import JWTError


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session):
    with patch("app.core.dependencies.decode_token", side_effect=JWTError("Invalid")):
        with pytest.raises(HTTPException) as exc:
            await get_current_user(db=db_session, token="invalid_token")
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_not_found(db_session):
    with (
        patch("app.core.dependencies.decode_token", return_value={"sub": "123"}),
        patch.object(db_session, "execute") as mock_exec,
    ):
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_exec.return_value = mock_res

        with pytest.raises(HTTPException) as exc:
            await get_current_user(db=db_session, token="token")
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_rate_limiter_exceeded():
    limiter = AuthRateLimiter(max_calls=1, period=60)
    mock_request = MagicMock()
    mock_request.client.host = "1.2.3.4"
    mock_request.url.path = "/auth"

    with patch.object(limiter.redis, "pipeline") as mock_pipe:
        mock_pipe.return_value.__aenter__.return_value.execute = AsyncMock(
            return_value=[None, 2]
        )
        with pytest.raises(HTTPException) as exc:
            await limiter(mock_request)
        assert exc.value.status_code == 429
