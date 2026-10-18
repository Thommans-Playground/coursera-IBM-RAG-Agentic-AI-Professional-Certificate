"""The ONLY place the Conversation context touches the Knowledge context.
It is an anti-corruption layer: it calls Knowledge's use cases and translates the results into Conversation's own types."""
from chatapp.conversation.domain.message import Source
from chatapp.knowledge.application.use_cases import CountKnowledge, SearchKnowledge


class KnowledgeContextGateway:
    def __init__(self, search: SearchKnowledge, count: CountKnowledge) -> None:
        self._search, self._count = search, count

    async def is_empty(self) -> bool:
        return await self._count.execute() == 0

    async def search(self, question: str, k: int) -> list[Source]:
        hits = await self._search.execute(question, k)
        return [Source(title=h.title, url=h.url, text=h.text, score=h.score) for h in hits]
