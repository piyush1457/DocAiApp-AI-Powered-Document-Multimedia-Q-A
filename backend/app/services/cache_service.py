import json
import hashlib
import logging
from typing import Any, Optional, Union
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(str(settings.REDIS_URL), decode_responses=True)

    async def get(self, key: str) -> Optional[Union[dict, str]]:
        try:
            data = await self.redis.get(key)
            if data is None:
                return None
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return data
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        try:
            if isinstance(value, (dict, list)):
                data = json.dumps(value)
            else:
                data = str(value)
            await self.redis.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    async def delete(self, key: str):
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    async def delete_pattern(self, pattern: str):
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete_pattern error: {e}")

    @staticmethod
    def hash_key(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

cache_service = CacheService()
