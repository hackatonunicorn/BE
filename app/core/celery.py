from celery import Celery
from app.core.config_simple import settings

celery_app = Celery(
    "startup_vc_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.ai.tasks", "app.email.tasks"]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
