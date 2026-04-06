import json
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings


class RedisCache:
    def __init__(self, client: redis.Redis) -> None:
        self._r = client

    @classmethod
    async def from_url(cls) -> "RedisCache":
        settings = get_settings()
        client = redis.from_url(str(settings.redis_url), decode_responses=True)
        return cls(client)

    async def get_json(self, key: str) -> Any | None:
        raw = await self._r.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        await self._r.set(key, json.dumps(value), ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._r.delete(key)
