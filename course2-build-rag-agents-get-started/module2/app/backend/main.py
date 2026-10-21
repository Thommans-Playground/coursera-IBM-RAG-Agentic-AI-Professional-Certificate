"""FastAPI app. Each endpoint is the web version of a Gradio function."""
import os
from typing import Annotated, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag import ALLOWED_MODELS, RagEngine

app = FastAPI(title="RAG Notes Bot")

# The browser app runs on port 3000, so the API must allow that origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine: RagEngine | None = None


def engine() -> RagEngine:
    # Built on first use so the server starts instantly and tests can swap it.
    global _engine
    if _engine is None:
        _engine = RagEngine()
        _engine.seed()
    return _engine


class EchoIn(BaseModel):
    text: str


class GreetIn(BaseModel):
    name: str
    times: int = Field(ge=1, le=10)


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AskIn(BaseModel):
    question: str = Field(min_length=1)
    history: list[Turn] = []
    k: int = Field(default=4, ge=1, le=10)
    model: str = "gpt-4o-mini"
    style: Literal["concise", "detailed"] = "concise"


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/echo")
def echo(body: EchoIn):
    return {"text": body.text}


@app.post("/api/greet")
def greet(body: GreetIn):
    return {"message": " ".join([f"Hello, {body.name}!"] * body.times)}


@app.post("/api/count-files")
async def count_files(files: Annotated[list[UploadFile], File()]):
    return {"count": len(files), "names": [f.filename for f in files]}


@app.get("/api/documents")
def documents():
    return {"sources": engine().sources}


@app.post("/api/documents")
async def add_documents(files: Annotated[list[UploadFile], File()]):
    added = {}
    for f in files:
        text = (await f.read()).decode("utf-8", errors="ignore")
        added[f.filename] = engine().add_text(f.filename, text)
    return {"added": added, "sources": engine().sources}


@app.post("/api/ask")
def ask(body: AskIn):
    if body.model not in ALLOWED_MODELS:
        raise HTTPException(status_code=422, detail=f"model must be one of {sorted(ALLOWED_MODELS)}")
    history = [t.model_dump() for t in body.history]
    answer, docs = engine().ask(body.question, history, body.k, body.model, body.style)
    return {
        "answer": answer,
        "sources": [
            {"source": d.metadata["source"], "start_index": d.metadata["start_index"], "text": d.page_content}
            for d in docs
        ],
    }
