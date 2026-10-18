"""The use cases of the Knowledge context. They orchestrate domain objects through ports."""
from chatapp.knowledge.application.ports import ChunkStore, DocumentRepository, DocumentSource, Embedder, JobQueue, TextSplitter
from chatapp.knowledge.domain.catalog import CATALOG
from chatapp.knowledge.domain.document import Document, EmbeddedChunk, SearchHit


class LoadKnowledgeBase:
    """Queue every catalog entry for ingestion. Calling it twice resets the documents, never duplicates them."""

    def __init__(self, documents: DocumentRepository, jobs: JobQueue) -> None:
        self.documents, self.jobs = documents, jobs

    async def execute(self) -> int:
        for entry in CATALOG:
            document = await self.documents.upsert(Document.queued(entry))
            self.jobs.enqueue_ingest(document.id)
        return len(CATALOG)


class IngestDocument:
    """Download, split, embed and store one document. Runs in the worker."""

    def __init__(self, documents: DocumentRepository, chunks: ChunkStore, source: DocumentSource,
                 splitter: TextSplitter, embedder: Embedder) -> None:
        self.documents, self.chunks, self.source = documents, chunks, source
        self.splitter, self.embedder = splitter, embedder

    async def execute(self, document_id: int) -> int:
        document = await self.documents.get(document_id)
        if document is None:
            raise LookupError(f"document {document_id} does not exist")
        document.start()
        await self.documents.save(document)
        try:
            parts = self.splitter.split(await self.source.fetch(document.key))
            vectors = await self.embedder.embed_documents([document.embedding_text(p) for p in parts])
            await self.chunks.replace(document.id, [EmbeddedChunk(p, v) for p, v in zip(parts, vectors)])
            document.finish(len(parts))
            return len(parts)
        except Exception as e:  # show the reason in the page instead of failing silently
            document.fail(str(e))
            raise
        finally:
            await self.documents.save(document)


class ListKnowledge:
    def __init__(self, documents: DocumentRepository) -> None:
        self.documents = documents

    async def execute(self) -> list[Document]:
        return await self.documents.list_all()


class SearchKnowledge:
    def __init__(self, chunks: ChunkStore, embedder: Embedder) -> None:
        self.chunks, self.embedder = chunks, embedder

    async def execute(self, question: str, k: int) -> list[SearchHit]:
        return await self.chunks.search(await self.embedder.embed_query(question), k)


class CountKnowledge:
    def __init__(self, chunks: ChunkStore) -> None:
        self.chunks = chunks

    async def execute(self) -> int:
        return await self.chunks.count()
