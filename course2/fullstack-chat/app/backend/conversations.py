from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis

import store
from deps import get_redis

router = APIRouter(prefix="/api/conversations")


@router.get("")
async def list_all(r: Redis = Depends(get_redis)):
    return await store.list_conversations(r)


@router.post("")
async def create(r: Redis = Depends(get_redis)):
    return await store.create_conversation(r)


@router.get("/{cid}/messages")
async def messages(cid: str, r: Redis = Depends(get_redis)):
    if not await store.conversation_exists(r, cid):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await store.get_messages(r, cid)


@router.delete("/{cid}")
async def delete(cid: str, r: Redis = Depends(get_redis)):
    await store.delete_conversation(r, cid)
    return {"deleted": cid}
