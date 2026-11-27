import logging
import time
import redis.asyncio as redis
from core.config import REDIS_URL

# Connect to the Redis server with automatic byte decoding and short timeouts
cache = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)

_down_until = 0.0
_CIRCUIT_OPEN_SECONDS = 30.0


async def safe_get(key: str) -> str | None:
    """Reads from Redis with a 30s circuit breaker when Redis is unreachable."""
    global _down_until
    if time.monotonic() < _down_until:
        return None
    try:
        return await cache.get(key)
    except Exception as e:
        _down_until = time.monotonic() + _CIRCUIT_OPEN_SECONDS
        logging.error(f"Redis down, bypassing cache for {int(_CIRCUIT_OPEN_SECONDS)}s: {e}")
        return None


async def safe_setex(key: str, ttl: int, value: str) -> None:
    """Writes to Redis with a 30s circuit breaker when Redis is unreachable."""
    global _down_until
    if time.monotonic() < _down_until:
        return
    try:
        await cache.setex(key, ttl, value)
    except Exception as e:
        _down_until = time.monotonic() + _CIRCUIT_OPEN_SECONDS
        logging.error(f"Redis down, bypassing cache for {int(_CIRCUIT_OPEN_SECONDS)}s: {e}")