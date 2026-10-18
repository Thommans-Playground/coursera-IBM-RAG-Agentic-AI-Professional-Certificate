"""Postgres connections. The API uses an async pool. The Celery worker uses a normal connection."""
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector, register_vector_async
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

import settings

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


def sync_connect() -> psycopg.Connection:
    conn = psycopg.connect(settings.DATABASE_URL, row_factory=dict_row, autocommit=True)
    register_vector(conn)
    return conn
