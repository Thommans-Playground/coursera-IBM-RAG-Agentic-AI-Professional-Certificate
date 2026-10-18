"""FastAPI app for the RAG lab. One endpoint per pipeline stage."""
import os
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import db
import qa
from lab import Lab


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    pool = db.make_pool()
    pool.open()
    app.state.pool = pool
    app.state.lab = Lab(pool)
    if not app.state.lab.is_built():  # first run only: the index then survives restarts in Postgres
        app.state.lab.build("character", 1000, 0)  # the lab's own settings
    yield
    pool.close()


app = FastAPI(title="RAG Lab", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/chunks")
def chunks(request: Request):
    return request.app.state.lab.state()


@app.post("/api/index")
def index(body: IndexIn, request: Request):
    if body.chunk_overlap >= body.chunk_size:
        raise HTTPException(status_code=422, detail="chunk_overlap must be smaller than chunk_size")
    lab = request.app.state.lab
    lab.build(body.splitter, body.chunk_size, body.chunk_overlap)
    return lab.state()


@app.post("/api/search")
def search(body: SearchIn, request: Request):
    return {"hits": request.app.state.lab.search(body.question, body.k)}


@app.post("/api/ask")
def ask(body: AskIn, request: Request):
    history = [t.model_dump() for t in body.history]
    reply, standalone, hits = qa.answer(request.app.state.lab, body.question, body.k, body.strict, history)
    return {"answer": reply, "standalone_question": standalone, "hits": hits}
