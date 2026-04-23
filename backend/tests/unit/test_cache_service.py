import pytest
from unittest.mock import patch, AsyncMock
from app.services.cache_service import CacheService


@pytest.fixture
def cache_service():
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_instance = AsyncMock()
        mock_redis.return_value = mock_instance
        service = CacheService()
        return service


@pytest.mark.asyncio
async def test_cache_set_get(cache_service):
    """Test setting and getting values from cache with serialization."""
    mock_redis = cache_service.redis
    mock_redis.get.return_value = '{"a": 1}'

    await cache_service.set("key", {"a": 1}, ttl=10)
    mock_redis.setex.assert_called_once()

    val = await cache_service.get("key")
    assert val == {"a": 1}


@pytest.mark.asyncio
async def test_cache_delete(cache_service):
    """Test deleting a key from cache."""
    await cache_service.delete("key")
    cache_service.redis.delete.assert_called_once_with("key")


@pytest.mark.asyncio
async def test_cache_delete_pattern(cache_service):
    """Test deleting keys by pattern."""
    mock_redis = cache_service.redis
    mock_redis.keys.return_value = ["k1", "k2"]

    await cache_service.delete_pattern("k*")
    mock_redis.delete.assert_called_with("k1", "k2")


@pytest.mark.asyncio
async def test_cache_hash_key(cache_service):
    """Test deterministic key hashing."""
    h1 = cache_service.hash_key("test")
    h2 = cache_service.hash_key("test")
    h3 = cache_service.hash_key("other")
    assert h1 == h2
    assert h1 != h3
