"""Wiring tests with fake models: no OpenAI cost. The policy file is downloaded once (free)."""
from itertools import cycle

from fastapi.testclient import TestClient
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

import lab
import main


def test_all():
    lab.OpenAIEmbeddings = lambda **_: DeterministicFakeEmbedding(size=32)
    lab.ChatOpenAI = lambda **_: GenericFakeChatModel(messages=cycle([AIMessage(content="fake answer")]))
    main._lab = None
    c = TestClient(main.app)
    assert c.get("/api/health").json() == {"status": "ok"}
    ch = c.get("/api/chunks").json()
    assert len(ch["chunks"]) == 16, len(ch["chunks"])  # the lab's own number
    rec = c.post("/api/index", json={"splitter": "recursive", "chunk_size": 500, "chunk_overlap": 50}).json()
    assert len(rec["chunks"]) > 30 and max(x["length"] for x in rec["chunks"]) <= 500
    assert c.post("/api/index", json={"chunk_size": 200, "chunk_overlap": 200}).status_code == 422
    hits = c.post("/api/search", json={"question": "smoking", "k": 3}).json()["hits"]
    assert len(hits) == 3 and {"id", "score", "text"} <= set(hits[0])
    h = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]
    r = c.post("/api/ask", json={"question": "q", "k": 2, "strict": False, "history": h}).json()
    assert r["answer"] == "fake answer" and len(r["hits"]) == 2
    assert c.post("/api/ask", json={"question": "q", "k": 99}).status_code == 422
