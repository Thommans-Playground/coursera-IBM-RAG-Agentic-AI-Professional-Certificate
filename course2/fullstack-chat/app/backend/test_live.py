"""Live test of the real stack. No fakes.

Needs everything running: Postgres and Redis (docker compose up -d), the API on port 8000,
and the Celery worker. It calls the real OpenAI API, so it costs a fraction of a cent.

    uv run python test_live.py
"""
import asyncio
import json
import os
import time
import uuid

import httpx
from redis.asyncio import Redis

import db
import ratelimit
import settings
from tasks import celery_app

API = os.getenv("API_URL", "http://localhost:8000")
client = httpx.Client(base_url=API, timeout=60)


def chat(cid: str, message: str) -> dict:
    """Send one message and collect the stream into text, sources and the event types seen."""
    out = {"text": "", "sources": [], "types": []}
    with client.stream("POST", f"/api/conversations/{cid}/chat", json={"message": message}) as res:
        assert res.status_code == 200, res.read()
        for line in res.iter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                out["types"].append(event["type"])
                if event["type"] == "token":
                    out["text"] += event["text"]
                if event["type"] == "sources":
                    out["sources"] = event["sources"]
                assert event["type"] != "error", event
    return out


def ensure_knowledge_base() -> None:
    docs = client.get("/api/knowledge").json()
    if len(docs) == 10 and all(d["status"] == "ready" for d in docs):
        return
    assert client.post("/api/knowledge/load").json() == {"queued": 10}
    deadline = time.time() + 180
    while time.time() < deadline:
        docs = client.get("/api/knowledge").json()
        assert not any(d["status"] == "failed" for d in docs), docs
        if len(docs) == 10 and all(d["status"] == "ready" for d in docs):
            return
        time.sleep(3)
    raise AssertionError("The worker did not finish in 3 minutes. Is it running?")


def test_infrastructure() -> None:
    assert client.get("/api/hello").json()["message"].startswith("Hello")
    assert celery_app.control.inspect(timeout=3).ping(), "No Celery worker answered"
    with db.sync_connect() as conn:
        assert conn.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'").fetchone()
        assert conn.execute("SELECT count(*) AS n FROM chunks").fetchone()["n"] > 100


def test_rate_limiter_on_real_redis() -> None:
    async def run():
        r = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        who = f"test-{uuid.uuid4().hex[:6]}"
        results = [await ratelimit.rate_limited(r, who, 3) for _ in range(5)]
        await r.aclose()
        return results

    assert asyncio.run(run()) == [False, False, False, True, True]


def test_chat_flow() -> None:
    cid = client.post("/api/conversations").json()["id"]
    first = chat(cid, "What is SQL injection and how do I prevent it?")
    assert first["text"] and first["types"][-1] == "done"
    assert first["sources"] and "A05" in first["sources"][0]["title"], first["sources"][:1]
    assert first["sources"][0]["url"].startswith("https://owasp.org/Top10/2025/")

    # A follow-up with no topic words. It only works if the question is rewritten using the history.
    second = chat(cid, "Which category is it in?")
    assert "A05" in second["text"], second["text"]

    # Something the OWASP pages do not cover.
    third = chat(cid, "What is the best pizza topping?")
    assert "know" in third["text"].lower(), third["text"]
    assert third["sources"][0]["score"] < 0.35, third["sources"][0]["score"]

    messages = client.get(f"/api/conversations/{cid}/messages").json()
    assert [m["role"] for m in messages] == ["user", "assistant"] * 3
    assert messages[1]["sources"], "sources must be saved with the answer"
    title = next(c["title"] for c in client.get("/api/conversations").json() if c["id"] == cid)
    assert title.startswith("What is SQL injection")

    assert client.delete(f"/api/conversations/{cid}").json() == {"deleted": cid}
    assert client.get(f"/api/conversations/{cid}/messages").status_code == 404
    with db.sync_connect() as conn:  # ON DELETE CASCADE removed the messages
        assert conn.execute("SELECT count(*) AS n FROM messages WHERE conversation_id = %s", (cid,)).fetchone()["n"] == 0


def test_errors() -> None:
    cid = client.post("/api/conversations").json()["id"]
    assert client.post("/api/conversations/nope/chat", json={"message": "x"}).status_code == 404
    assert client.post(f"/api/conversations/{cid}/chat", json={"message": ""}).status_code == 422
    assert client.post(f"/api/conversations/{cid}/chat", json={"message": "x", "k": 99}).status_code == 422
    client.delete(f"/api/conversations/{cid}")


if __name__ == "__main__":
    ensure_knowledge_base()
    for test in (test_infrastructure, test_rate_limiter_on_real_redis, test_chat_flow, test_errors):
        test()
        print("ok  ", test.__name__)
    print("ALL LIVE TESTS PASSED")
