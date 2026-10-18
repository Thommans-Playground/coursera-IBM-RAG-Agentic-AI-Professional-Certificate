"""Live test of the real stack. No fakes.

Needs the API on port 8000 (uv run uvicorn main:app --port 8000, or docker compose up).
It calls the real OpenAI API, so it costs a fraction of a cent.

    uv run python test_live.py
"""
import os
import uuid

import httpx

API = os.getenv("API_URL", "http://localhost:8000")
client = httpx.Client(base_url=API, timeout=90)


def test_basics() -> None:
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.post("/api/echo", json={"text": "hi"}).json() == {"text": "hi"}
    assert client.post("/api/greet", json={"name": "Ann", "times": 2}).json()["message"] == "Hello, Ann! Hello, Ann!"
    assert client.post("/api/greet", json={"name": "Ann", "times": 99}).status_code == 422
    files = [("files", ("a.txt", b"x")), ("files", ("b.txt", b"y"))]
    assert client.post("/api/count-files", files=files).json()["count"] == 2


def test_rag() -> None:
    # A made-up fact that no model could know. It can only come from the uploaded file.
    code = f"PINEAPPLE-{uuid.uuid4().hex[:4].upper()}"
    name = f"vault-{uuid.uuid4().hex[:4]}.txt"
    text = f"Office handbook. The vault door code is {code}. Visitors must sign in at reception. " * 3
    added = client.post("/api/documents", files=[("files", (name, text.encode()))]).json()
    assert added["added"][name] >= 1 and name in added["sources"]

    reply = client.post("/api/ask", json={"question": "What is the vault door code?", "k": 4}).json()
    assert code in reply["answer"], reply["answer"]
    assert any(s["source"] == name for s in reply["sources"])
    assert {"source", "start_index", "text"} <= set(reply["sources"][0])

    # Something the notes do not cover: the rule in the prompt should make the bot decline.
    unknown = client.post("/api/ask", json={"question": "Who won the 2010 World Cup?", "k": 4}).json()
    assert "know" in unknown["answer"].lower(), unknown["answer"]


def test_memory_and_validation() -> None:
    history = [
        {"role": "user", "content": "What is cosine similarity?"},
        {"role": "assistant", "content": "It measures how much two vectors point the same way."},
    ]
    r = client.post("/api/ask", json={"question": "And how is it different from the dot product?", "history": history, "k": 4})
    assert r.status_code == 200 and r.json()["answer"]

    assert client.post("/api/ask", json={"question": "x", "k": 50}).status_code == 422
    assert client.post("/api/ask", json={"question": "x", "model": "gpt-9"}).status_code == 422
    assert client.post("/api/ask", json={"question": ""}).status_code == 422


if __name__ == "__main__":
    for test in (test_basics, test_rag, test_memory_and_validation):
        test()
        print("ok  ", test.__name__)
    print("ALL LIVE TESTS PASSED")
