"""The Celery app. Both the queue adapter (sending jobs) and the worker (running them) use it."""
from celery import Celery

from chatapp.infrastructure import settings

celery_app = Celery("chat", broker=settings.REDIS_URL)  # status lives in Postgres, so no result backend
