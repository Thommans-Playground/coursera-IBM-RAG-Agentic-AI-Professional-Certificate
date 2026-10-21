from chatapp.infrastructure.celery_app import celery_app


class CeleryJobQueue:
    def enqueue_ingest(self, document_id: int) -> None:
        # Sends a message by task NAME, so this adapter never imports the worker code.
        celery_app.send_task("knowledge.ingest_document", args=[document_id])
