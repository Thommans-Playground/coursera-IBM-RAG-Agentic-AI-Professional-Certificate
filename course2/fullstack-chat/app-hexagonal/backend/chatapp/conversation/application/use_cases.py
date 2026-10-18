"""The use cases of the Conversation context."""
from collections.abc import AsyncIterator

from chatapp.conversation.application.errors import ConversationNotFound, KnowledgeBaseEmpty, RateLimitExceeded
from chatapp.conversation.application.events import AnswerFailed, AnswerFinished, ChatEvent, SourcesFound, TokenGenerated
from chatapp.conversation.application.ports import AnswerGenerator, ConversationRepository, KnowledgeSearch, RateLimiter
from chatapp.conversation.domain.conversation import Conversation, clean_question
from chatapp.conversation.domain.message import Message, Role, Source


class StartConversation:
    def __init__(self, conversations: ConversationRepository) -> None:
        self.conversations = conversations

    async def execute(self) -> Conversation:
        conversation = Conversation.start()
        await self.conversations.add(conversation)
        return conversation


class ListConversations:
    def __init__(self, conversations: ConversationRepository) -> None:
        self.conversations = conversations

    async def execute(self) -> list[Conversation]:
        return await self.conversations.list_all()


class GetMessages:
    def __init__(self, conversations: ConversationRepository) -> None:
        self.conversations = conversations

    async def execute(self, conversation_id: str) -> list[Message]:
        if await self.conversations.get(conversation_id) is None:
            raise ConversationNotFound(conversation_id)
        return await self.conversations.messages(conversation_id)


class DeleteConversation:
    def __init__(self, conversations: ConversationRepository) -> None:
        self.conversations = conversations

    async def execute(self, conversation_id: str) -> None:
        await self.conversations.delete(conversation_id)


class AnswerStream:
    """A question that passed every check. Iterating `events()` produces the answer."""

    def __init__(self, conversations: ConversationRepository, answers: AnswerGenerator, conversation_id: str,
                 history: list[Message], question: str, sources: list[Source]) -> None:
        self.conversations, self.answers = conversations, answers
        self.conversation_id, self.history, self.question, self.sources = conversation_id, history, question, sources

    async def events(self) -> AsyncIterator[ChatEvent]:
        parts: list[str] = []
        try:
            async for token in self.answers.stream(self.history, self.question, self.sources):
                parts.append(token)
                yield TokenGenerated(token)
        except Exception as e:  # tell the page, instead of cutting the stream
            yield AnswerFailed(str(e)[:200])
            return
        await self.conversations.append(self.conversation_id, Message(Role.ASSISTANT, "".join(parts), tuple(self.sources)))
        yield SourcesFound(tuple(self.sources))
        yield AnswerFinished()


class SendMessage:
    def __init__(self, conversations: ConversationRepository, answers: AnswerGenerator, knowledge: KnowledgeSearch,
                 limiter: RateLimiter, history_window: int) -> None:
        self.conversations, self.answers, self.knowledge = conversations, answers, knowledge
        self.limiter, self.history_window = limiter, history_window

    async def execute(self, conversation_id: str, text: str, k: int, client_id: str) -> AnswerStream:
        # Every check happens here, before any streaming starts, so the page gets a real error code.
        if await self.limiter.is_limited(client_id):
            raise RateLimitExceeded(client_id)
        conversation = await self.conversations.get(conversation_id)
        if conversation is None:
            raise ConversationNotFound(conversation_id)
        if await self.knowledge.is_empty():
            raise KnowledgeBaseEmpty()
        question = clean_question(text)

        history = await self.conversations.messages(conversation_id, limit=self.history_window)
        search_text = await self.answers.standalone_question(history, question)
        sources = await self.knowledge.search(search_text, k)

        await self.conversations.append(conversation_id, Message(Role.USER, question))
        if conversation.name_from(question):
            await self.conversations.rename(conversation)
        return AnswerStream(self.conversations, self.answers, conversation_id, history, question, sources)
