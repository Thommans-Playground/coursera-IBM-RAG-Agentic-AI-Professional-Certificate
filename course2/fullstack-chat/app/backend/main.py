from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

import chat
import conversations
import db
import knowledge
import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_schema()
    app.state.pool = db.make_pool()
    await app.state.pool.open()
    app.state.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    yield
    await app.state.pool.close()
    await app.state.redis.aclose()


app = FastAPI(title="OWASP Top 10 chat", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(knowledge.router)


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}
