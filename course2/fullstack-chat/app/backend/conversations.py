from fastapi import APIRouter, Depends, HTTPException
from psycopg_pool import AsyncConnectionPool

import store
from deps import get_pool

router = APIRouter(prefix="/api/conversations")


@router.get("")
async def list_all(pool: AsyncConnectionPool = Depends(get_pool)):
    return await store.list_conversations(pool)


@router.post("")
async def create(pool: AsyncConnectionPool = Depends(get_pool)):
    return await store.create_conversation(pool)


@router.get("/{cid}/messages")
async def messages(cid: str, pool: AsyncConnectionPool = Depends(get_pool)):
    if not await store.conversation_exists(pool, cid):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await store.get_messages(pool, cid)


@router.delete("/{cid}")
async def delete(cid: str, pool: AsyncConnectionPool = Depends(get_pool)):
    await store.delete_conversation(pool, cid)
    return {"deleted": cid}
