"""Every SQL statement lives here. Other files ask in plain words."""
import uuid

import numpy as np
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

import owasp

DEFAULT_TITLE = "New chat"


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



async def create_conversation(pool: AsyncConnectionPool) -> dict:
    cid = uuid.uuid4().hex[:8]
    await execute(pool, "INSERT INTO conversations (id) VALUES (%s)", (cid,))
    return {"id": cid, "title": DEFAULT_TITLE}


async def conversation_exists(pool: AsyncConnectionPool, cid: str) -> bool:
    return await one(pool, "SELECT 1 FROM conversations WHERE id = %s", (cid,)) is not None


async def list_conversations(pool: AsyncConnectionPool) -> list[dict]:
    return await many(pool, "SELECT id, title FROM conversations ORDER BY created_at DESC")


async def add_message(pool: AsyncConnectionPool, cid: str, role: str, content: str, sources: list | None = None) -> None:
    await execute(
        pool,
        "INSERT INTO messages (conversation_id, role, content, sources) VALUES (%s, %s, %s, %s)",
        (cid, role, content, Jsonb(sources or [])),
    )
    if role == "user":  # the first message names the chat
        await execute(
            pool,
            "UPDATE conversations SET title = %s WHERE id = %s AND title = %s",
            (content[:40], cid, DEFAULT_TITLE),
        )


async def get_messages(pool: AsyncConnectionPool, cid: str, limit: int | None = None) -> list[dict]:
    # Newest N, then put them back in time order.
    return await many(
        pool,
        "SELECT role, content, sources FROM ("
        "  SELECT id, role, content, sources FROM messages WHERE conversation_id = %s ORDER BY id DESC LIMIT %s"
        ") recent ORDER BY id",
        (cid, limit),
    )


async def delete_conversation(pool: AsyncConnectionPool, cid: str) -> None:
    await execute(pool, "DELETE FROM conversations WHERE id = %s", (cid,))  # messages go too (ON DELETE CASCADE)


async def list_documents(pool: AsyncConnectionPool) -> list[dict]:
    return await many(pool, "SELECT id, key, title, status, chunks, error FROM documents ORDER BY key")


async def queue_documents(pool: AsyncConnectionPool) -> list[int]:
    """One row per OWASP category. Running it twice resets the rows instead of adding more."""
    ids = []
    for key, name, _ in owasp.CATEGORIES:
        row = await one(
            pool,
            "INSERT INTO documents (key, title, url, status) VALUES (%s, %s, %s, 'queued') "
            "ON CONFLICT (key) DO UPDATE SET status = 'queued', error = '', updated_at = now() RETURNING id",
            (key, owasp.title(key, name), owasp.page_url(key)),
        )
        ids.append(row["id"])
    return ids


async def ready_chunk_count(pool: AsyncConnectionPool) -> int:
    return (await one(pool, "SELECT count(*) AS n FROM chunks"))["n"]


async def search_chunks(pool: AsyncConnectionPool, embedding: list[float], k: int) -> list[dict]:
    # <=> is pgvector's cosine DISTANCE (0 = same direction). 1 - distance = similarity.
    rows = await many(
        pool,
        "SELECT d.title, d.url, c.content AS text, 1 - (c.embedding <=> %s) AS score "
        "FROM chunks c JOIN documents d ON d.id = c.document_id "
        "ORDER BY c.embedding <=> %s LIMIT %s",
        (np.array(embedding), np.array(embedding), k),
    )
    return [{**r, "score": round(float(r["score"]), 4)} for r in rows]
