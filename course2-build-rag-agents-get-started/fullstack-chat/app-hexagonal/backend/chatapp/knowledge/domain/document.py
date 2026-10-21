"""The Document entity and the rules about its life. No database, no web, no AI in here."""
from dataclasses import dataclass
from enum import StrEnum

from chatapp.knowledge.domain.catalog import CatalogEntry

MAX_ERROR_LENGTH = 200


class DocumentStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class Document:
    key: str
    title: str
    url: str
    status: DocumentStatus = DocumentStatus.QUEUED
    chunks: int = 0
    error: str = ""
    id: int | None = None  # the database gives it one when it is first saved

    @classmethod
    def queued(cls, entry: CatalogEntry) -> "Document":
        return cls(key=entry.key, title=entry.title, url=entry.page_url)

    # The life of a document: queued -> processing -> ready or failed. Loading again starts over.
    def start(self) -> None:
        self.status = DocumentStatus.PROCESSING

    def finish(self, chunks: int) -> None:
        self.status, self.chunks, self.error = DocumentStatus.READY, chunks, ""

    def fail(self, reason: str) -> None:
        self.status, self.error = DocumentStatus.FAILED, reason[:MAX_ERROR_LENGTH]

    def requeue(self) -> None:
        self.status, self.error = DocumentStatus.QUEUED, ""

    def embedding_text(self, chunk: str) -> str:
        # A chunk like "Use parameterized queries" does not say which category it belongs to.
        # Putting the title in front helps its vector land near the right topic.
        return f"{self.title}\n\n{chunk}"


@dataclass(frozen=True)
class EmbeddedChunk:
    text: str
    vector: list[float]


@dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    text: str
    score: float  # cosine similarity: 1 means the same direction, near 0 means unrelated
