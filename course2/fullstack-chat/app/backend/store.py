"""Everything we keep in Redis. Key names live here so the API and the worker agree."""
import json
import time
import uuid

from redis.asyncio import Redis

DEFAULT_TITLE = "New chat"


# Key builders. The Celery worker imports these too.
def conv_key(cid: str) -> str:
    return f"conv:{cid}"


def msgs_key(cid: str) -> str:
    return f"conv:{cid}:msgs"


def docs_key(cid: str) -> str:
    return f"conv:{cid}:docs"


def chunks_key(cid: str) -> str:
    return f"conv:{cid}:chunks"


def doc_key(doc_id: str) -> str:
    return f"doc:{doc_id}"


async def create_conversation(r: Redis) -> dict:
    cid = uuid.uuid4().hex[:8]
    now = time.time()
    await r.hset(conv_key(cid), mapping={"id": cid, "title": DEFAULT_TITLE, "created": now})
    await r.zadd("convs", {cid: now})  # sorted by creation time
    return {"id": cid, "title": DEFAULT_TITLE}


async def conversation_exists(r: Redis, cid: str) -> bool:
    return bool(await r.exists(conv_key(cid)))


async def list_conversations(r: Redis) -> list[dict]:
    ids = await r.zrevrange("convs", 0, -1)  # newest first
    out = []
    for cid in ids:
        title = await r.hget(conv_key(cid), "title")
        out.append({"id": cid, "title": title})
    return out


async def add_message(r: Redis, cid: str, role: str, content: str, sources: list | None = None) -> None:
    await r.rpush(msgs_key(cid), json.dumps({"role": role, "content": content, "sources": sources or []}))
    if role == "user" and await r.hget(conv_key(cid), "title") == DEFAULT_TITLE:
        await r.hset(conv_key(cid), "title", content[:40])


async def get_messages(r: Redis, cid: str, limit: int | None = None) -> list[dict]:
    start = -limit if limit else 0
    return [json.loads(m) for m in await r.lrange(msgs_key(cid), start, -1)]


async def delete_conversation(r: Redis, cid: str) -> None:
    doc_ids = await r.smembers(docs_key(cid))
    keys = [conv_key(cid), msgs_key(cid), docs_key(cid), chunks_key(cid), *[doc_key(d) for d in doc_ids]]
    await r.delete(*keys)
    await r.zrem("convs", cid)


async def create_document(r: Redis, cid: str, name: str) -> str:
    doc_id = uuid.uuid4().hex[:8]
    await r.hset(doc_key(doc_id), mapping={"id": doc_id, "name": name, "status": "queued", "chunks": 0, "error": ""})
    await r.sadd(docs_key(cid), doc_id)
    return doc_id


async def list_documents(r: Redis, cid: str) -> list[dict]:
    docs = [await r.hgetall(doc_key(d)) for d in await r.smembers(docs_key(cid))]
    return sorted(docs, key=lambda d: d["name"])


async def get_chunks(r: Redis, cid: str) -> list[dict]:
    return [json.loads(c) for c in await r.lrange(chunks_key(cid), 0, -1)]


async def rate_limited(r: Redis, who: str, limit: int) -> bool:
    # One counter per client per minute. The key expires by itself.
    key = f"rate:{who}:{int(time.time() // 60)}"
    count = await r.incr(key)
    if count == 1:
        await r.expire(key, 60)
    return count > limit
