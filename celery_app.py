"""
Celery configuration for Video Transcriber application.
"""

import os
from celery import Celery

# Set default Django settings module for celery
os.environ.setdefault('CELERY_CONFIG_MODULE', 'celery_config')

# Create Celery app
app = Celery('video_transcriber')

# Configure Celery
app.config_from_object('celery_config')

# Auto-discover tasks
app.autodiscover_tasks(['src.tasks'])

if __name__ == '__main__':
    app.start()