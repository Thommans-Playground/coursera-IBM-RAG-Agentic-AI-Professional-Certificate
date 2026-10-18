from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

from chatapp.conversation.domain.conversation import Conversation
from chatapp.conversation.domain.message import Message, Role, Source
from chatapp.infrastructure import db


class PostgresConversationRepository:
    def __init__(self, pool: AsyncConnectionPool) -> None:
        self.pool = pool

    async def add(self, conversation: Conversation) -> None:
        await db.execute(self.pool, "INSERT INTO conversations (id, title) VALUES (%s, %s)", (conversation.id, conversation.title))

    async def get(self, conversation_id: str) -> Conversation | None:
        row = await db.one(self.pool, "SELECT id, title FROM conversations WHERE id = %s", (conversation_id,))
        return Conversation(**row) if row else None

    async def list_all(self) -> list[Conversation]:
        rows = await db.many(self.pool, "SELECT id, title FROM conversations ORDER BY created_at DESC")
        return [Conversation(**r) for r in rows]

    async def rename(self, conversation: Conversation) -> None:
        await db.execute(self.pool, "UPDATE conversations SET title = %s WHERE id = %s", (conversation.title, conversation.id))

    async def delete(self, conversation_id: str) -> None:
        await db.execute(self.pool, "DELETE FROM conversations WHERE id = %s", (conversation_id,))  # messages go too (ON DELETE CASCADE)

    async def append(self, conversation_id: str, message: Message) -> None:
        sources = [{"title": s.title, "url": s.url, "text": s.text, "score": s.score} for s in message.sources]
        await db.execute(
            self.pool,
            "INSERT INTO messages (conversation_id, role, content, sources) VALUES (%s, %s, %s, %s)",
            (conversation_id, message.role.value, message.content, Jsonb(sources)),
        )

    async def messages(self, conversation_id: str, limit: int | None = None) -> list[Message]:
        # Newest N, then put them back in time order.
        rows = await db.many(
            self.pool,
            "SELECT role, content, sources FROM ("
            "  SELECT id, role, content, sources FROM messages WHERE conversation_id = %s ORDER BY id DESC LIMIT %s"
            ") recent ORDER BY id",
            (conversation_id, limit),
        )
        return [Message(Role(r["role"]), r["content"], tuple(Source(**s) for s in r["sources"])) for r in rows]
