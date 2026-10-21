"""Live test of the real stack. No fakes.

Needs Postgres running (docker compose up -d postgres) and the API on port 8000
(uv run uvicorn main:app --port 8000, or the whole stack with docker compose up).
It calls the real OpenAI API, so it costs a fraction of a cent.

    uv run python test_live.py
"""
import os

import httpx

API = os.getenv("API_URL", "http://localhost:8000")
client = httpx.Client(base_url=API, timeout=60)


def test_pipeline() -> None:
    assert client.get("/api/health").json() == {"status": "ok"}

    # The lab's own splitter: 16 chunks, and some are lone headings.
    built = client.post("/api/index", json={"splitter": "character", "chunk_size": 1000, "chunk_overlap": 0}).json()
    assert len(built["chunks"]) == 16, len(built["chunks"])
    assert any(c["length"] < 60 for c in built["chunks"]), "expected tiny heading-only chunks"

    # State comes from Postgres, so a second read returns the same thing.
    assert client.get("/api/chunks").json() == built

    hits = client.post("/api/search", json={"question": "Can I smoke in company vehicles?", "k": 3}).json()["hits"]
    assert len(hits) == 3 and hits[0]["score"] > hits[-1]["score"]
    assert "smok" in hits[0]["text"].lower(), hits[0]["text"][:80]

    # A better splitter gives more, smaller chunks, and replaces the old ones.
    better = client.post("/api/index", json={"splitter": "recursive", "chunk_size": 500, "chunk_overlap": 50}).json()
    assert len(better["chunks"]) > 30 and max(c["length"] for c in better["chunks"]) <= 500
    assert client.get("/api/chunks").json()["settings"]["splitter"] == "recursive"
    client.post("/api/index", json={"splitter": "character", "chunk_size": 1000, "chunk_overlap": 0})  # put the lab's settings back


def test_answers() -> None:
    body = {"question": "Can I smoke in company vehicles?", "k": 3, "strict": True}
    smoke = client.post("/api/ask", json=body).json()
    assert "not" in smoke["answer"].lower(), smoke["answer"]

    # The lab's trap question. With the rule on, the model should decline.
    eat = client.post("/api/ask", json={**body, "question": "Can I eat in company vehicles?"}).json()
    assert "know" in eat["answer"].lower(), eat["answer"]

    # Memory: a follow-up with no topic words is rewritten using the history.
    history = [{"role": "user", "content": "What is the mobile phone policy?"}, {"role": "assistant", "content": "It covers phone use at work."}]
    follow = client.post("/api/ask", json={"question": "List the points in it.", "k": 3, "strict": True, "history": history}).json()
    assert "phone" in follow["standalone_question"].lower(), follow["standalone_question"]


def test_validation() -> None:
    assert client.post("/api/index", json={"chunk_size": 200, "chunk_overlap": 200}).status_code == 422
    assert client.post("/api/search", json={"question": "", "k": 3}).status_code == 422
    assert client.post("/api/search", json={"question": "x", "k": 99}).status_code == 422


if __name__ == "__main__":
    for test in (test_pipeline, test_answers, test_validation):
        test()
        print("ok  ", test.__name__)
    print("ALL LIVE TESTS PASSED")
