import redis.asyncio as redis
from core.config import REDIS_URL

# Connect to the Redis server with automatic byte decoding and short timeouts
cache = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)