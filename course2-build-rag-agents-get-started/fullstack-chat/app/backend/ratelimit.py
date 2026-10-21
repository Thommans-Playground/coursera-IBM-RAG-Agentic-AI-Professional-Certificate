"""Rate limiting with Redis: one counter per client per minute."""
import time

from redis.asyncio import Redis


async def rate_limited(r: Redis, who: str, limit: int) -> bool:
    key = f"rate:{who}:{int(time.time() // 60)}"
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, 60)  # the counter deletes itself, no cleanup code needed
    return count > limit
