"""The ports of the Knowledge context: what its use cases need from the outside world.
Each one is named for the need, not for a tool. Adapters implement them."""
from collections.abc import Sequence
from typing import Protocol

from chatapp.knowledge.domain.document import Document, EmbeddedChunk, SearchHit


class DocumentRepository(Protocol):
    async def upsert(self, document: Document) -> Document: ...  # insert, or reset the same key; returns it with an id
    async def get(self, document_id: int) -> Document | None: ...
    async def save(self, document: Document) -> None: ...
    async def list_all(self) -> list[Document]: ...


class ChunkStore(Protocol):
    async def replace(self, document_id: int, chunks: Sequence[EmbeddedChunk]) -> None: ...
    async def search(self, vector: list[float], k: int) -> list[SearchHit]: ...
    async def count(self) -> int: ...


class Embedder(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...


class DocumentSource(Protocol):
    async def fetch(self, key: str) -> str: ...  # the text of one catalog entry


class TextSplitter(Protocol):
    def split(self, text: str) -> list[str]: ...


class JobQueue(Protocol):
    def enqueue_ingest(self, document_id: int) -> None: ...  # run IngestDocument later, somewhere else
