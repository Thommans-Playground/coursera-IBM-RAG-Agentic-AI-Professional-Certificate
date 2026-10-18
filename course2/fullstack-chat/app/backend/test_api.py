"""Wiring tests: fake Redis, fake models, Celery runs jobs inline. Free and offline."""
import json
from itertools import cycle

import fakeredis
from fastapi.testclient import TestClient
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

import deps
import llm
import main
import rag
import settings
import tasks


def make_client():
    server = fakeredis.FakeServer()
    async_client = fakeredis.FakeAsyncRedis(server=server, decode_responses=True)
    deps_override = lambda: async_client  # noqa: E731
    main.app.dependency_overrides[deps.get_redis] = deps_override
    tasks.sync_redis = lambda: fakeredis.FakeRedis(server=server, decode_responses=True)
    tasks.celery_app.conf.task_always_eager = True  # run .delay() jobs inline, no worker needed
    llm.get_llm = lambda: GenericFakeChatModel(messages=cycle([AIMessage(content="Hello there friend")]))
    rag.embedder = lambda: DeterministicFakeEmbedding(size=16)
    return TestClient(main.app)


def events(response):
    return [json.loads(line[6:]) for line in response.text.split("\n\n") if line.startswith("data: ")]


def test_all():
    c = make_client()
    assert c.get("/api/hello").json()["message"].startswith("Hello")

    cid = c.post("/api/conversations").json()["id"]
    assert c.get("/api/conversations").json()[0]["title"] == "New chat"

    # Plain chat: tokens stream, then done, and the history is saved.
    ev = events(c.post(f"/api/conversations/{cid}/chat", json={"message": "hi"}))
    assert [e["type"] for e in ev][-1] == "done" and "".join(e.get("text", "") for e in ev) == "Hello there friend"
    msgs = c.get(f"/api/conversations/{cid}/messages").json()
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert c.get("/api/conversations").json()[0]["title"] == "hi"

    # Upload: the Celery task runs inline, the document becomes ready.
    r = c.post(f"/api/conversations/{cid}/documents", files=[("files", ("n.txt", b"Smoking is not allowed. " * 80))])
    assert len(r.json()["queued"]) == 1
    doc = c.get(f"/api/conversations/{cid}/documents").json()[0]
    assert doc["status"] == "ready" and int(doc["chunks"]) >= 1

    # RAG chat: a sources event comes before done.
    ev = events(c.post(f"/api/conversations/{cid}/chat", json={"message": "smoking?", "k": 2}))
    sources = next(e for e in ev if e["type"] == "sources")["sources"]
    assert len(sources) == 2 and {"source", "start_index", "text", "score"} <= set(sources[0])

    # Errors and limits.
    assert c.post("/api/conversations/nope/chat", json={"message": "x"}).status_code == 404
    assert c.post(f"/api/conversations/{cid}/chat", json={"message": ""}).status_code == 422
    settings.RATE_LIMIT_PER_MINUTE = 1
    assert c.post(f"/api/conversations/{cid}/chat", json={"message": "again"}).status_code == 429

    assert c.delete(f"/api/conversations/{cid}").json() == {"deleted": cid}
    assert c.get(f"/api/conversations/{cid}/messages").status_code == 404
