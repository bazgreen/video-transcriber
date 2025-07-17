"""
Celery configuration settings.
"""

import os

# Broker settings
broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Worker settings
worker_prefetch_multiplier = 1
task_acks_late = True
worker_max_tasks_per_child = 1000

# Task routing
task_routes = {
    'src.tasks.transcribe_audio_task': {'queue': 'transcription'},
    'src.tasks.cleanup_task': {'queue': 'cleanup'},
}

# Task time limits
task_time_limit = 30 * 60  # 30 minutes
task_soft_time_limit = 25 * 60  # 25 minutes

# Result backend settings
result_expires = 3600  # 1 hour

# Monitoring
worker_send_task_events = True
task_send_sent_event = True