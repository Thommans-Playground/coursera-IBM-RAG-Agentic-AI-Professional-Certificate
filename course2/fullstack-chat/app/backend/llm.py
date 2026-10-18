"""Building the prompt and streaming the model's reply."""
from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

import settings

PLAIN = "You are a helpful assistant. Keep answers short."
RAG = (
    "You are a helpful assistant. Answer using the context below. "
    "If the context does not contain the answer, say you don't know.\n\nContext:\n{context}"
)


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=settings.CHAT_MODEL, temperature=0.3, max_tokens=500)


def build_messages(history: list[dict], question: str, sources: list[dict]):
    system = RAG.format(context="\n\n".join(s["text"] for s in sources)) if sources else PLAIN
    past = [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]
    return [SystemMessage(system), *past, HumanMessage(question)]


async def stream_answer(history: list[dict], question: str, sources: list[dict]) -> AsyncIterator[str]:
    async for chunk in get_llm().astream(build_messages(history, question, sources)):
        if chunk.content:
            yield chunk.content
