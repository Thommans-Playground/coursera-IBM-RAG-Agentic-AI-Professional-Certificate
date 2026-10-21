from fastapi import APIRouter, Depends
from psycopg_pool import AsyncConnectionPool

import store
from deps import get_pool
from tasks import ingest_document

router = APIRouter(prefix="/api/knowledge")


@router.get("")
async def documents(pool: AsyncConnectionPool = Depends(get_pool)):
    return await store.list_documents(pool)


@router.post("/load")
async def load(pool: AsyncConnectionPool = Depends(get_pool)):
    ids = await store.queue_documents(pool)
    for doc_id in ids:
        # .delay() puts a job on the Redis queue and returns at once. A worker picks it up.
        ingest_document.delay(doc_id)
    return {"queued": len(ids)}
