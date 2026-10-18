import time

from redis.asyncio import Redis


class RedisRateLimiter:
    def __init__(self, redis: Redis, limit_per_minute: int) -> None:
        self.redis, self.limit = redis, limit_per_minute

    async def is_limited(self, client_id: str) -> bool:
        key = f"rate:{client_id}:{int(time.time() // 60)}"  # one counter per client per minute
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60)  # the counter deletes itself, no cleanup code needed
        return count > self.limit
