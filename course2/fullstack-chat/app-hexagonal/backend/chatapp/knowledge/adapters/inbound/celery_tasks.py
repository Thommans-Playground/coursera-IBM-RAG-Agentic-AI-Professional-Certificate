"""Inbound adapter: a Celery job that calls a use case, just like an HTTP route does."""
import asyncio

from chatapp.container import build_container
from chatapp.infrastructure.celery_app import celery_app


@celery_app.task(name="knowledge.ingest_document")
def ingest_document(document_id: int) -> int:
    return asyncio.run(_run(document_id))


async def _run(document_id: int) -> int:
    # The worker is its own process, so it builds its own container (its own connections).
    async with build_container() as container:
        return await container.knowledge.ingest_document.execute(document_id)
