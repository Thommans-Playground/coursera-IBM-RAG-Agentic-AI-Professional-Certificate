from collections.abc import Sequence

import numpy as np
from psycopg_pool import AsyncConnectionPool

from chatapp.infrastructure import db
from chatapp.knowledge.domain.document import EmbeddedChunk, SearchHit


class PgVectorChunkStore:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self.pool = pool

    async def replace(self, document_id: int, chunks: Sequence[EmbeddedChunk]) -> None:
        async with self.pool.connection() as conn, conn.transaction():  # all or nothing
            await conn.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))  # reloading replaces, never duplicates
            for position, chunk in enumerate(chunks):
                await conn.execute(
                    "INSERT INTO chunks (document_id, position, content, embedding) VALUES (%s, %s, %s, %s)",
                    (document_id, position, chunk.text, np.array(chunk.vector)),
                )

    async def search(self, vector: list[float], k: int) -> list[SearchHit]:
        # <=> is pgvector's cosine DISTANCE (0 = same direction). 1 - distance = similarity.
        rows = await db.many(
            self.pool,
            "SELECT d.title, d.url, c.content AS text, 1 - (c.embedding <=> %s) AS score "
            "FROM chunks c JOIN documents d ON d.id = c.document_id "
            "ORDER BY c.embedding <=> %s LIMIT %s",
            (np.array(vector), np.array(vector), k),
        )
        return [SearchHit(r["title"], r["url"], r["text"], round(float(r["score"]), 4)) for r in rows]

    async def count(self) -> int:
        return (await db.one(self.pool, "SELECT count(*) AS n FROM chunks"))["n"]
