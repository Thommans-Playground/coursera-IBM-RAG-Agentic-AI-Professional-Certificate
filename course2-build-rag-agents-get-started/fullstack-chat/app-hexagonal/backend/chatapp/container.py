"""The composition root: the ONE place that knows which adapter fills which port."""
from contextlib import asynccontextmanager
from dataclasses import dataclass

from redis.asyncio import Redis

from chatapp.conversation.adapters.outbound.knowledge_gateway import KnowledgeContextGateway
from chatapp.conversation.adapters.outbound.openai_answers import OpenAIAnswerGenerator
from chatapp.conversation.adapters.outbound.postgres_conversations import PostgresConversationRepository
from chatapp.conversation.adapters.outbound.redis_rate_limiter import RedisRateLimiter
from chatapp.conversation.application import use_cases as conversation_cases
from chatapp.infrastructure import db, settings
from chatapp.knowledge.adapters.outbound.celery_queue import CeleryJobQueue
from chatapp.knowledge.adapters.outbound.github_source import GithubOwaspSource
from chatapp.knowledge.adapters.outbound.markdown_splitter import MarkdownSplitter
from chatapp.knowledge.adapters.outbound.openai_embedder import OpenAIEmbedder
from chatapp.knowledge.adapters.outbound.pgvector_chunks import PgVectorChunkStore
from chatapp.knowledge.adapters.outbound.postgres_documents import PostgresDocumentRepository
from chatapp.knowledge.application import use_cases as knowledge_cases


@dataclass
class KnowledgeUseCases:
    load_knowledge_base: knowledge_cases.LoadKnowledgeBase
    ingest_document: knowledge_cases.IngestDocument
    list_knowledge: knowledge_cases.ListKnowledge


@dataclass
class ConversationUseCases:
    start_conversation: conversation_cases.StartConversation
    list_conversations: conversation_cases.ListConversations
    get_messages: conversation_cases.GetMessages
    delete_conversation: conversation_cases.DeleteConversation
    send_message: conversation_cases.SendMessage


@dataclass
class Container:
    knowledge: KnowledgeUseCases
    conversation: ConversationUseCases


@asynccontextmanager
async def build_container():
    pool = db.make_pool()
    await pool.open()
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        # Knowledge context: adapters first, then the use cases that need them.
        documents = PostgresDocumentRepository(pool)
        chunks = PgVectorChunkStore(pool)
        embedder = OpenAIEmbedder()
        knowledge = KnowledgeUseCases(
            load_knowledge_base=knowledge_cases.LoadKnowledgeBase(documents, CeleryJobQueue()),
            ingest_document=knowledge_cases.IngestDocument(documents, chunks, GithubOwaspSource(), MarkdownSplitter(), embedder),
            list_knowledge=knowledge_cases.ListKnowledge(documents),
        )
        # Conversation context. Its view of Knowledge goes through one gateway.
        gateway = KnowledgeContextGateway(knowledge_cases.SearchKnowledge(chunks, embedder), knowledge_cases.CountKnowledge(chunks))
        conversations = PostgresConversationRepository(pool)
        conversation = ConversationUseCases(
            start_conversation=conversation_cases.StartConversation(conversations),
            list_conversations=conversation_cases.ListConversations(conversations),
            get_messages=conversation_cases.GetMessages(conversations),
            delete_conversation=conversation_cases.DeleteConversation(conversations),
            send_message=conversation_cases.SendMessage(
                conversations, OpenAIAnswerGenerator(), gateway,
                RedisRateLimiter(redis, settings.RATE_LIMIT_PER_MINUTE), settings.HISTORY_LIMIT,
            ),
        )
        yield Container(knowledge=knowledge, conversation=conversation)
    finally:
        await pool.close()
        await redis.aclose()
