from fastapi import Request
from psycopg_pool import AsyncConnectionPool
from redis.asyncio import Redis


def get_pool(request: Request) -> AsyncConnectionPool:
    return request.app.state.pool


def get_redis(request: Request) -> Redis:
    return request.app.state.redis
