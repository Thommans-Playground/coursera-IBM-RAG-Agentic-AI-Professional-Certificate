from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from redis.asyncio import Redis

import store
from deps import get_redis
from tasks import ingest

router = APIRouter(prefix="/api/conversations")


@router.get("/{cid}/documents")
async def documents(cid: str, r: Redis = Depends(get_redis)):
    return await store.list_documents(r, cid)


@router.post("/{cid}/documents")
async def upload(cid: str, files: Annotated[list[UploadFile], File()], r: Redis = Depends(get_redis)):
    if not await store.conversation_exists(r, cid):
        raise HTTPException(status_code=404, detail="Conversation not found")
    queued = []
    for f in files:
        text = (await f.read()).decode("utf-8", errors="ignore")
        doc_id = await store.create_document(r, cid, f.filename or "file")
        # .delay() puts a job on the Redis queue and returns at once. A worker picks it up.
        ingest.delay(cid, doc_id, f.filename or "file", text)
        queued.append(doc_id)
    return {"queued": queued}
