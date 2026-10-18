import json
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from chatapp.conversation.application.errors import ConversationError, ConversationNotFound, KnowledgeBaseEmpty, RateLimitExceeded
from chatapp.conversation.application.events import AnswerFailed, AnswerFinished, ChatEvent, SourcesFound, TokenGenerated
from chatapp.conversation.domain.conversation import InvalidQuestion

router = APIRouter(prefix="/api/conversations")

# Business errors become HTTP status codes here, and only here.
STATUS = {
    ConversationNotFound: (404, "Conversation not found"),
    RateLimitExceeded: (429, "Too many messages. Wait a minute."),
    KnowledgeBaseEmpty: (409, "The knowledge base is empty. Press Load OWASP Top 10 first."),
}


def to_http(error: Exception) -> HTTPException:
    if isinstance(error, InvalidQuestion):
        return HTTPException(status_code=422, detail=str(error))
    code, detail = STATUS.get(type(error), (500, "Something went wrong"))
    return HTTPException(status_code=code, detail=detail)


def container(request: Request):
    return request.app.state.container


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    k: int = Field(default=4, ge=1, le=10)


def sse(event: ChatEvent) -> str:
    # One server-sent event: a line starting with "data:" and a blank line after it.
    match event:
        case TokenGenerated(text):
            body = {"type": "token", "text": text}
        case SourcesFound(sources):
            body = {"type": "sources", "sources": [asdict(s) for s in sources]}
        case AnswerFailed(message):
            body = {"type": "error", "message": message}
        case AnswerFinished():
            body = {"type": "done"}
    return f"data: {json.dumps(body)}\n\n"


@router.get("")
async def list_all(request: Request):
    conversations = await container(request).conversation.list_conversations.execute()
    return [{"id": c.id, "title": c.title} for c in conversations]


@router.post("")
async def create(request: Request):
    c = await container(request).conversation.start_conversation.execute()
    return {"id": c.id, "title": c.title}


@router.get("/{cid}/messages")
async def messages(cid: str, request: Request):
    try:
        found = await container(request).conversation.get_messages.execute(cid)
    except ConversationError as e:
        raise to_http(e)
    return [{"role": m.role.value, "content": m.content, "sources": [asdict(s) for s in m.sources]} for m in found]


@router.delete("/{cid}")
async def delete(cid: str, request: Request):
    await container(request).conversation.delete_conversation.execute(cid)
    return {"deleted": cid}


@router.post("/{cid}/chat")
async def chat(cid: str, body: ChatIn, request: Request):
    client_id = request.client.host if request.client else "unknown"
    try:
        stream = await container(request).conversation.send_message.execute(cid, body.message, body.k, client_id)
    except (ConversationError, InvalidQuestion) as e:
        raise to_http(e)

    async def events():
        async for event in stream.events():
            yield sse(event)

    return StreamingResponse(events(), media_type="text/event-stream")
