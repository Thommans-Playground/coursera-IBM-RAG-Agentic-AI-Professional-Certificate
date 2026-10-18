from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chatapp.container import build_container
from chatapp.conversation.adapters.inbound import http as conversation_http
from chatapp.infrastructure import db, settings
from chatapp.knowledge.adapters.inbound import http as knowledge_http


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    async with build_container() as container:
        app.state.container = container
        yield


app = FastAPI(title="OWASP Top 10 chat", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(conversation_http.router)
app.include_router(knowledge_http.router)


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}
