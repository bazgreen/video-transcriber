"""
Background tasks for video transcription processing.

This module contains Celery tasks for handling asynchronous video processing,
transcription, and cleanup operations.
"""

import logging
import os
from typing import Any, Dict

from celery import current_app as celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def transcribe_audio_task(
    self, file_path: str, session_id: str, **kwargs
) -> Dict[str, Any]:
    """
    Background task for audio transcription.

    Args:
        file_path: Path to the audio file to transcribe
        session_id: Session identifier for tracking
        **kwargs: Additional transcription options

    Returns:
        Dict containing transcription results
    """
    try:
        logger.info(f"Starting transcription task for session {session_id}")

        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 10, "total": 100, "status": "Preparing transcription..."},
        )

        # Import transcriber (avoid circular imports)
        from src.models import MemoryManager, ProgressiveFileManager, ProgressTracker
        from src.services import VideoTranscriber

        # Create transcriber instance for this task
        memory_manager = MemoryManager()
        file_manager = ProgressiveFileManager()
        progress_tracker = ProgressTracker(None)  # No socketio in background task

        VideoTranscriber(
            memory_manager=memory_manager,
            file_manager=file_manager,
            progress_tracker=progress_tracker,
            results_folder=kwargs.get("results_folder", "/app/results"),
        )

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 30, "total": 100, "status": "Transcribing audio..."},
        )

        # Perform transcription
        # This is a simplified version - you would integrate with your actual transcription logic
        result = {
            "session_id": session_id,
            "file_path": file_path,
            "status": "completed",
            "transcription": "Background transcription completed successfully",
            "timestamp": (
                str(os.path.getmtime(file_path)) if os.path.exists(file_path) else None
            ),
        }

        # Update final progress
        self.update_state(
            state="SUCCESS",
            meta={"current": 100, "total": 100, "status": "Transcription completed"},
        )

        logger.info(f"Transcription task completed for session {session_id}")
        return result

    except Exception as exc:
        logger.error(f"Transcription task failed for session {session_id}: {exc}")
        self.update_state(
            state="FAILURE",
            meta={"current": 0, "total": 100, "status": f"Error: {str(exc)}"},
        )
        raise


@celery_app.task
def cleanup_task(session_id: str, file_paths: list) -> Dict[str, Any]:
    """
    Background task for cleaning up temporary files.

    Args:
        session_id: Session identifier
        file_paths: List of file paths to clean up

    Returns:
        Dict containing cleanup results
    """
    try:
        logger.info(f"Starting cleanup task for session {session_id}")

        cleaned_files = []
        failed_files = []

        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    cleaned_files.append(file_path)
                    logger.debug(f"Cleaned up file: {file_path}")
            except Exception as e:
                failed_files.append(file_path)
                logger.warning(f"Failed to clean up file {file_path}: {e}")

        result = {
            "session_id": session_id,
            "cleaned_files": cleaned_files,
            "failed_files": failed_files,
            "total_cleaned": len(cleaned_files),
            "status": "completed",
        }

        logger.info(
            f"Cleanup task completed for session {session_id}: {len(cleaned_files)} files cleaned"
        )
        return result

    except Exception as exc:
        logger.error(f"Cleanup task failed for session {session_id}: {exc}")
        raise


@celery_app.task
def health_check_task() -> Dict[str, Any]:
    """
    Background task for system health checks.

    Returns:
        Dict containing health check results
    """
    try:
        logger.debug("Running background health check")

        # Import health monitor
        from src.health_monitoring import health_monitor

        # Perform health checks
        health_data = health_monitor.run_health_checks(detailed=True)

        return {
            "status": "completed",
            "timestamp": health_data.get("timestamp"),
            "health_status": health_data.get("status"),
            "checks": health_data.get("checks", {}),
        }

    except Exception as exc:
        logger.error(f"Health check task failed: {exc}")
        raise


@celery_app.task
def process_batch_task(batch_id: str, file_list: list) -> Dict[str, Any]:
    """
    Background task for processing multiple files in batch.

    Args:
        batch_id: Batch identifier
        file_list: List of files to process

    Returns:
        Dict containing batch processing results
    """
    try:
        logger.info(f"Starting batch processing task for batch {batch_id}")

        processed_files = []
        failed_files = []

        for i, file_info in enumerate(file_list):
            try:
                # Process each file (simplified)
                # In a real implementation, you would call the actual transcription logic
                result = {
                    "file_path": file_info.get("path"),
                    "status": "processed",
                    "transcription": f"Batch transcription for {file_info.get('name', 'unknown')}",
                }
                processed_files.append(result)

                # Update progress
                progress = int((i + 1) / len(file_list) * 100)
                logger.debug(f"Batch progress: {progress}% ({i + 1}/{len(file_list)})")

            except Exception as e:
                failed_files.append(
                    {"file_path": file_info.get("path"), "error": str(e)}
                )
                logger.warning(f"Failed to process file {file_info.get('path')}: {e}")

        result = {
            "batch_id": batch_id,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "total_processed": len(processed_files),
            "total_failed": len(failed_files),
            "status": "completed",
        }

        logger.info(
            f"Batch processing completed for batch {batch_id}: {len(processed_files)} files processed"
        )
        return result

    except Exception as exc:
        logger.error(f"Batch processing task failed for batch {batch_id}: {exc}")
        raise
