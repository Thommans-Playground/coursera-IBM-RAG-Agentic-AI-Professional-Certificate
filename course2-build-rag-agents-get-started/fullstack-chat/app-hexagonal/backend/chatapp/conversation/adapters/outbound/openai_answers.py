from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from chatapp.conversation.domain.message import Message, Role, Source
from chatapp.infrastructure import settings

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


def _llm(**kwargs) -> ChatOpenAI:
    return ChatOpenAI(model=settings.CHAT_MODEL, **kwargs)


def _to_langchain(history: list[Message]):
    return [HumanMessage(m.content) if m.role is Role.USER else AIMessage(m.content) for m in history]


class OpenAIAnswerGenerator:
    async def standalone_question(self, history: list[Message], question: str) -> str:
        # "How do I prevent it?" cannot be searched. "How do I prevent SQL injection?" can.
        if not history:
            return question
        messages = [SystemMessage(REWRITE), *_to_langchain(history), HumanMessage(question)]
        return (await _llm(temperature=0, max_tokens=100).ainvoke(messages)).content.strip()

    async def stream(self, history: list[Message], question: str, sources: list[Source]) -> AsyncIterator[str]:
        context = "\n\n".join(f"[{s.title}]\n{s.text}" for s in sources)
        messages = [SystemMessage(SYSTEM.format(context=context)), *_to_langchain(history), HumanMessage(question)]
        async for chunk in _llm(temperature=0.2, max_tokens=600).astream(messages):
            if chunk.content:
                yield chunk.content
