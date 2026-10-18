"""Prompts and the model calls."""
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

import settings

SYSTEM = (
    "You are a security assistant that answers questions about the OWASP Top 10:2025. "
    "Use only the context below. Name the category you rely on, like [A05:2025], in your answer. "
    "If the context does not contain the answer, say you don't know and suggest which OWASP "
    "category might be related. Be concise and practical.\n\nContext:\n{context}"
)
REWRITE = (
    "Rewrite the user's last question so it makes sense on its own, using the chat history. "
    "Return only the question."
)


def get_llm(**kwargs) -> ChatOpenAI:
    return ChatOpenAI(model=settings.CHAT_MODEL, **kwargs)


def to_messages(history: list[dict]):
    return [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]


async def standalone_question(history: list[dict], question: str) -> str:
    # "How do I prevent it?" cannot be searched. "How do I prevent SQL injection?" can.
    if not history:
        return question
    messages = [SystemMessage(REWRITE), *to_messages(history), HumanMessage(question)]
    return (await get_llm(temperature=0, max_tokens=100).ainvoke(messages)).content.strip()


def format_context(sources: list[dict]) -> str:
    return "\n\n".join(f"[{s['title']}]\n{s['text']}" for s in sources)


async def stream_answer(history: list[dict], question: str, sources: list[dict]) -> AsyncIterator[str]:
    messages = [SystemMessage(SYSTEM.format(context=format_context(sources))), *to_messages(history), HumanMessage(question)]
    async for chunk in get_llm(temperature=0.2, max_tokens=600).astream(messages):
        if chunk.content:
            yield chunk.content
