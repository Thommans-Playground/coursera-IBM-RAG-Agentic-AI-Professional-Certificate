"""Wiring tests with fake models: no network, no API cost."""
from fastapi.testclient import TestClient
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from itertools import cycle

import main
import rag


def make_client():
    rag.OpenAIEmbeddings = lambda **_: DeterministicFakeEmbedding(size=32)
    rag.ChatOpenAI = lambda **_: GenericFakeChatModel(messages=cycle([AIMessage(content="fake answer")]))
    main._engine = None
    return TestClient(main.app)


def test_all():
    c = make_client()
    assert c.get("/api/health").json() == {"status": "ok"}
    assert c.post("/api/echo", json={"text": "hi"}).json() == {"text": "hi"}
    assert c.post("/api/greet", json={"name": "Ann", "times": 2}).json()["message"] == "Hello, Ann! Hello, Ann!"
    assert c.post("/api/greet", json={"name": "Ann", "times": 99}).status_code == 422
    r = c.post("/api/count-files", files=[("files", ("a.txt", b"x")), ("files", ("b.txt", b"y"))])
    assert r.json()["count"] == 2
    r = c.post("/api/documents", files=[("files", ("n.txt", b"Smoking is not allowed. " * 100))])
    assert r.json()["added"]["n.txt"] >= 1
    body = {"question": "Can I smoke?", "k": 3, "history": [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]}
    r = c.post("/api/ask", json=body)
    assert r.status_code == 200 and r.json()["answer"] == "fake answer" and len(r.json()["sources"]) == 3
    assert c.post("/api/ask", json={**body, "model": "nope"}).status_code == 422
