from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from rq import Queue

from clara.config import get_settings

_redis: Redis | None = None
_async_redis: AsyncRedis | None = None
_queue: Queue | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(str(get_settings().redis_url))
    return _redis


def get_queue() -> Queue:
    global _queue
    if _queue is None:
        _queue = Queue("default", connection=get_redis())
    return _queue


def get_async_redis() -> AsyncRedis:
    global _async_redis
    if _async_redis is None:
        _async_redis = AsyncRedis.from_url(str(get_settings().redis_url))
    return _async_redis


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JWT ID to the blacklist with expiry matching token lifetime."""
    if ttl_seconds > 0:
        await get_async_redis().setex(f"blacklist:{jti}", ttl_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    result: int = await get_async_redis().exists(f"blacklist:{jti}")
    return result > 0
