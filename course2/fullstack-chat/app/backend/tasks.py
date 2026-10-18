"""Celery worker code. It runs in its own process, so it cannot share Python objects with the API.
Everything it produces goes into Redis."""
import json

import redis
from celery import Celery

import rag
import settings
import store

celery_app = Celery("chat", broker=settings.REDIS_URL, backend=settings.REDIS_URL)


def sync_redis() -> redis.Redis:
    # The worker is synchronous, so it uses the normal client, not redis.asyncio.
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


@celery_app.task
def ingest(cid: str, doc_id: str, name: str, text: str) -> int:
    r = sync_redis()
    r.hset(store.doc_key(doc_id), "status", "processing")
    try:
        chunks = rag.split(name, text)
        vectors = rag.embedder().embed_documents([c.page_content for c in chunks])
        for chunk, vec in zip(chunks, vectors):
            item = {"source": name, "start_index": chunk.metadata["start_index"], "text": chunk.page_content, "vec": vec}
            r.rpush(store.chunks_key(cid), json.dumps(item))
        r.hset(store.doc_key(doc_id), mapping={"status": "ready", "chunks": len(chunks)})
        return len(chunks)
    except Exception as e:  # show the reason in the page instead of failing silently
        r.hset(store.doc_key(doc_id), mapping={"status": "failed", "error": str(e)[:200]})
        raise
