"""FastAPI app for the RAG lab. One endpoint per pipeline stage."""
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from lab import Lab

app = FastAPI(title="RAG Lab")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_lab: Lab | None = None


def lab() -> Lab:
    # Built on first use, with the lab's own settings, so the first page load already works.
    global _lab
    if _lab is None:
        _lab = Lab()
        _lab.build("character", 1000, 0)
    return _lab


class IndexIn(BaseModel):
    splitter: Literal["character", "recursive"] = "character"
    chunk_size: int = Field(default=1000, ge=100, le=3000)
    chunk_overlap: int = Field(default=0, ge=0, le=500)


class SearchIn(BaseModel):
    question: str = Field(min_length=1)
    k: int = Field(default=4, ge=1, le=10)


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskIn(SearchIn):
    strict: bool = True
    history: list[Turn] = []


def chunk_summary(docs):
    return [{"id": d.metadata["chunk_id"], "length": len(d.page_content), "text": d.page_content} for d in docs]


def hit_json(hits):
    return [{"id": d.metadata["chunk_id"], "score": round(float(s), 4), "text": d.page_content} for d, s in hits]


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/document")
def document():
    return {"name": "companyPolicies.txt", "characters": len(lab().text), "text": lab().text}


@app.get("/api/chunks")
def chunks():
    return {"settings": lab().settings, "chunks": chunk_summary(lab().chunks)}


@app.post("/api/index")
def index(body: IndexIn):
    if body.chunk_overlap >= body.chunk_size:
        raise HTTPException(status_code=422, detail="chunk_overlap must be smaller than chunk_size")
    lab().build(body.splitter, body.chunk_size, body.chunk_overlap)
    return {"settings": lab().settings, "chunks": chunk_summary(lab().chunks)}


@app.post("/api/search")
def search(body: SearchIn):
    return {"hits": hit_json(lab().search(body.question, body.k))}


@app.post("/api/ask")
def ask(body: AskIn):
    history = [t.model_dump() for t in body.history]
    answer, standalone, hits = lab().ask(body.question, body.k, body.strict, history)
    return {"answer": answer, "standalone_question": standalone, "hits": hit_json(hits)}

