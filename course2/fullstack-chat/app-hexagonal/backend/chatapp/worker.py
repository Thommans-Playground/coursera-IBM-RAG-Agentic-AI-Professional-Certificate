"""Entry point for the Celery worker:  celery -A chatapp.worker worker --loglevel=info"""
from chatapp.infrastructure.celery_app import celery_app
from chatapp.knowledge.adapters.inbound import celery_tasks  # noqa: F401  (importing it registers the task)

__all__ = ["celery_app"]
