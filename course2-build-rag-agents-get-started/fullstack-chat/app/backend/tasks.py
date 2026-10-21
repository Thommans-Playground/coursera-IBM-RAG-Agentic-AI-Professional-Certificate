"""Celery worker code. It runs in its own process, so it only shares Postgres and Redis with the API."""
from celery import Celery

import db
import owasp
import rag
import settings

celery_app = Celery("chat", broker=settings.REDIS_URL)  # status lives in Postgres, so no result backend


@celery_app.task
def ingest_document(doc_id: int) -> int:
    with db.sync_connect() as conn:
        doc = conn.execute("SELECT key, title FROM documents WHERE id = %s", (doc_id,)).fetchone()
        conn.execute("UPDATE documents SET status = 'processing', updated_at = now() WHERE id = %s", (doc_id,))
        try:
            chunks = rag.split(owasp.fetch_markdown(doc["key"]))
            texts = [c.page_content for c in chunks]
            vectors = rag.embedder().embed_documents([rag.for_embedding(doc["title"], t) for t in texts])
            conn.execute("DELETE FROM chunks WHERE document_id = %s", (doc_id,))  # reloading replaces, never duplicates
            for position, (text, vec) in enumerate(zip(texts, vectors)):
                conn.execute(
                    "INSERT INTO chunks (document_id, position, content, embedding) VALUES (%s, %s, %s, %s)",
                    (doc_id, position, text, vec),
                )
            conn.execute(
                "UPDATE documents SET status = 'ready', chunks = %s, error = '', updated_at = now() WHERE id = %s",
                (len(texts), doc_id),
            )
            return len(texts)
        except Exception as e:  # show the reason in the page instead of failing silently
            conn.execute(
                "UPDATE documents SET status = 'failed', error = %s, updated_at = now() WHERE id = %s",
                (str(e)[:200], doc_id),
            )
            raise
