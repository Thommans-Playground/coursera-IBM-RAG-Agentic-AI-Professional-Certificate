from psycopg_pool import AsyncConnectionPool

from chatapp.infrastructure import db
from chatapp.knowledge.domain.document import Document, DocumentStatus


def _to_document(row: dict) -> Document:
    return Document(id=row["id"], key=row["key"], title=row["title"], url=row["url"],
                    status=DocumentStatus(row["status"]), chunks=row["chunks"], error=row["error"])


COLUMNS = "id, key, title, url, status, chunks, error"


class PostgresDocumentRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self.pool = pool

    async def upsert(self, document: Document) -> Document:
        row = await db.one(
            self.pool,
            "INSERT INTO documents (key, title, url, status) VALUES (%s, %s, %s, 'queued') "
            f"ON CONFLICT (key) DO UPDATE SET status = 'queued', error = '', updated_at = now() RETURNING {COLUMNS}",
            (document.key, document.title, document.url),
        )
        return _to_document(row)

    async def get(self, document_id: int) -> Document | None:
        row = await db.one(self.pool, f"SELECT {COLUMNS} FROM documents WHERE id = %s", (document_id,))
        return _to_document(row) if row else None

    async def save(self, document: Document) -> None:
        await db.execute(
            self.pool,
            "UPDATE documents SET status = %s, chunks = %s, error = %s, updated_at = now() WHERE id = %s",
            (document.status.value, document.chunks, document.error, document.id),
        )

    async def list_all(self) -> list[Document]:
        return [_to_document(r) for r in await db.many(self.pool, f"SELECT {COLUMNS} FROM documents ORDER BY key")]
