from celery import Celery

from institute.config import get_settings

settings = get_settings()

celery_app = Celery(
    "institute",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
    include=["institute.tasks"],  # modules with tasks
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,  # Confirm the task only after it's completed (not after receiving it).
    worker_prefetch_multiplier=1,  # process a task at a time (more predictable)
    task_track_started=True,
)
