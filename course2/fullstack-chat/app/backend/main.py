from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import chat
import conversations
import docs
import settings

app = FastAPI(title="Full-stack chat")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(docs.router)


@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}
