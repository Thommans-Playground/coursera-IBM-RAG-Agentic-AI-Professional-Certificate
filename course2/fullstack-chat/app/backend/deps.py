from redis.asyncio import Redis

import settings

_client: Redis | None = None


def get_redis() -> Redis:
    # One shared client. Tests replace this function with a fake.
    global _client
    if _client is None:
        _client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client
