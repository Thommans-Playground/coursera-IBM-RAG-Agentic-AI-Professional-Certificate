import json

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from redis.asyncio import Redis

import llm
import rag
import settings
import store
from deps import get_redis

router = APIRouter(prefix="/api/conversations")


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    k: int = Field(default=4, ge=1, le=10)


def sse(event: dict) -> str:
    # One server-sent event: a line starting with "data:" and a blank line after it.
    return f"data: {json.dumps(event)}\n\n"


@router.post("/{cid}/chat")
async def chat(cid: str, body: ChatIn, request: Request, r: Redis = Depends(get_redis)):
    who = request.client.host if request.client else "unknown"
    if await store.rate_limited(r, who, settings.RATE_LIMIT_PER_MINUTE):
        raise HTTPException(status_code=429, detail="Too many messages. Wait a minute.")
    if not await store.conversation_exists(r, cid):
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = await store.get_messages(r, cid, limit=settings.HISTORY_LIMIT)
    chunks = await store.get_chunks(r, cid)
    sources = rag.top_k(await rag.embed_query(body.message), chunks, body.k) if chunks else []
    await store.add_message(r, cid, "user", body.message)

    async def events():
        parts: list[str] = []
        try:
            async for token in llm.stream_answer(history, body.message, sources):
                parts.append(token)
                yield sse({"type": "token", "text": token})
        except Exception as e:  # tell the page, instead of cutting the stream
            yield sse({"type": "error", "message": str(e)[:200]})
            return
        await store.add_message(r, cid, "assistant", "".join(parts), sources)
        if sources:
            yield sse({"type": "sources", "sources": sources})
        yield sse({"type": "done"})

    return StreamingResponse(events(), media_type="text/event-stream")
