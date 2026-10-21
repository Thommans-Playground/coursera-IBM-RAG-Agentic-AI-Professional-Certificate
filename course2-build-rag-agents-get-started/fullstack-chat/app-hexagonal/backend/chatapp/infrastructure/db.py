"""Postgres plumbing shared by the outbound adapters of every context."""
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector_async
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from chatapp.infrastructure import settings

SCHEMA = Path(__file__).with_name("schema.sql")


def init_schema() -> None:
    # Safe to run on every start: every statement says IF NOT EXISTS.
    with psycopg.connect(settings.DATABASE_URL, autocommit=True) as conn:
        conn.execute(SCHEMA.read_text())


async def _configure(conn) -> None:
    await register_vector_async(conn)  # lets us pass numpy arrays as vectors


def make_pool() -> AsyncConnectionPool:
    return AsyncConnectionPool(
        settings.DATABASE_URL,
        min_size=1,
        max_size=5,
        open=False,
        configure=_configure,
        kwargs={"row_factory": dict_row, "autocommit": True},
    )


# Small helpers. A pool hands out a connection for the length of one `with` block.
async def execute(pool: AsyncConnectionPool, sql: str, params=None) -> None:
    async with pool.connection() as conn:
        await conn.execute(sql, params)


async def one(pool: AsyncConnectionPool, sql: str, params=None) -> dict | None:
    async with pool.connection() as conn:
        return await (await conn.execute(sql, params)).fetchone()


async def many(pool: AsyncConnectionPool, sql: str, params=None) -> list[dict]:
    async with pool.connection() as conn:
        return await (await conn.execute(sql, params)).fetchall()
