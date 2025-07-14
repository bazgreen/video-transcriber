"""
Celery application instance for background task processing.
This module provides a standalone Celery app that can be used by workers.
"""

import os

from celery import Celery

# Create standalone Celery app
celery_app = Celery(
    "video_transcriber",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    include=["src.tasks"],  # Include task modules
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_concurrency=2,
    task_routes={
        "src.tasks.transcribe_audio_task": {"queue": "transcription"},
        "src.tasks.cleanup_task": {"queue": "cleanup"},
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks()

if __name__ == "__main__":
    celery_app.start()
