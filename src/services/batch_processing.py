"""
Batch Processing Service for Video Transcriber.

This service manages the processing of multiple video files in batches,
providing queue management, progress tracking, and resource optimization.
"""

import json
import logging
import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.models.memory import MemoryManager
from src.services.transcription import VideoTranscriber
from src.utils.helpers import format_timestamp, is_safe_path, is_valid_session_id

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Batch processing status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoStatus(Enum):
    """Individual video processing status enumeration."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class BatchJob:
    """Represents a single video job within a batch."""

    def __init__(
        self,
        job_id: str,
        file_path: str,
        original_filename: str,
        session_name: Optional[str] = None,
    ):
        """Initialize a new batch job with smart session naming.

        Args:
            job_id: Unique identifier for the job
            file_path: Path to the video file
            original_filename: Original name of the uploaded file
            session_name: Optional custom session name (auto-generated if None)
        """
        self.job_id = job_id
        self.file_path = file_path
        self.original_filename = original_filename

        # Improved session naming logic
        if session_name:
            # Use provided custom session name
            self.session_name = session_name
        else:
            # Generate meaningful name from original filename
            self.session_name = self._generate_session_name_from_filename(
                original_filename
            )

        self.status = VideoStatus.QUEUED
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.session_id: Optional[str] = None
        self.results_path: Optional[str] = None
        self.progress: float = 0.0

    def _generate_session_name_from_filename(self, filename: str) -> str:
        """Generate a clean, readable session name from the original filename."""
        # Remove file extension
        base_name = os.path.splitext(filename)[0]

        # Replace common separators with spaces
        cleaned_name = re.sub(r"[_\-\.]+", " ", base_name)

        # Clean up multiple spaces and strip
        cleaned_name = " ".join(cleaned_name.split())

        # Capitalize first letter of each word for better readability
        cleaned_name = " ".join(word.capitalize() for word in cleaned_name.split())

        # Limit length to prevent overly long session names
        if len(cleaned_name) > 50:
            cleaned_name = cleaned_name[:47] + "..."

        # Add timestamp for uniqueness (shorter format)
        timestamp = datetime.now().strftime("%m%d_%H%M")

        return f"{cleaned_name}_{timestamp}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "session_name": self.session_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error_message": self.error_message,
            "session_id": self.session_id,
            "results_path": self.results_path,
            "progress": self.progress,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchJob":
        """Create job from dictionary."""
        job = cls(
            job_id=data["job_id"],
            file_path=data["file_path"],
            original_filename=data["original_filename"],
            session_name=data.get("session_name"),
        )
        job.status = VideoStatus(data["status"])
        job.created_at = datetime.fromisoformat(data["created_at"])
        job.started_at = (
            datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None
        )
        job.completed_at = (
            datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None
        )
        job.error_message = data.get("error_message")
        job.session_id = data.get("session_id")
        job.results_path = data.get("results_path")
        job.progress = data.get("progress", 0.0)
        return job


class BatchSession:
    """Represents a batch processing session containing multiple video jobs."""

    def __init__(
        self,
        batch_id: str,
        name: Optional[str] = None,
        max_concurrent: int = 2,
    ):
        """Initialize a new batch session.

        Args:
            batch_id: Unique identifier for the batch
            name: Optional custom name for the batch
            max_concurrent: Maximum number of concurrent jobs to process
        """
        self.batch_id = batch_id
        self.name = name or f"Batch {batch_id[:8]}"
        self.max_concurrent = max_concurrent
        self.status = BatchStatus.PENDING
        self.jobs: List[BatchJob] = []
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.total_duration = 0.0
        self.error_message: Optional[str] = None

    def add_job(self, job: BatchJob) -> None:
        """Add a job to the batch."""
        self.jobs.append(job)

    def get_progress(self) -> Dict[str, Any]:
        """Get overall batch progress."""
        total_jobs = len(self.jobs)
        if total_jobs == 0:
            return {
                "total_jobs": 0,
                "completed_jobs": 0,
                "failed_jobs": 0,
                "progress_percentage": 0.0,
                "estimated_remaining": None,
            }

        completed_jobs = len(
            [j for j in self.jobs if j.status == VideoStatus.COMPLETED]
        )
        failed_jobs = len([j for j in self.jobs if j.status == VideoStatus.FAILED])
        processing_jobs = len(
            [j for j in self.jobs if j.status == VideoStatus.PROCESSING]
        )

        # Calculate weighted progress including partial progress of processing jobs
        total_progress = float(completed_jobs)
        for job in self.jobs:
            if job.status == VideoStatus.PROCESSING:
                total_progress += job.progress

        progress_percentage = (
            (total_progress / total_jobs) * 100 if total_jobs > 0 else 0
        )

        # Estimate remaining time based on completed jobs
        estimated_remaining = None
        if completed_jobs > 0 and self.started_at:
            elapsed_time = (datetime.now() - self.started_at).total_seconds()
            avg_time_per_job = elapsed_time / completed_jobs
            remaining_jobs = total_jobs - completed_jobs
            estimated_remaining = avg_time_per_job * remaining_jobs

        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "processing_jobs": processing_jobs,
            "progress_percentage": round(progress_percentage, 1),
            "estimated_remaining": (
                format_timestamp(estimated_remaining) if estimated_remaining else None
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert batch to dictionary for JSON serialization."""
        return {
            "batch_id": self.batch_id,
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "total_duration": self.total_duration,
            "error_message": self.error_message,
            "jobs": [job.to_dict() for job in self.jobs],
            "progress": self.get_progress(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchSession":
        """Create batch from dictionary."""
        batch = cls(
            batch_id=data["batch_id"],
            name=data.get("name"),
            max_concurrent=data.get("max_concurrent", 2),
        )
        batch.status = BatchStatus(data["status"])
        batch.created_at = datetime.fromisoformat(data["created_at"])
        batch.started_at = (
            datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None
        )
        batch.completed_at = (
            datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None
        )
        batch.total_duration = data.get("total_duration", 0.0)
        batch.error_message = data.get("error_message")
        batch.jobs = [BatchJob.from_dict(job_data) for job_data in data.get("jobs", [])]
        return batch


class BatchProcessor:
    """Main batch processing service."""

    def __init__(
        self,
        results_dir: str = "results",
        transcriber: Optional[VideoTranscriber] = None,
        app=None,
    ):
        """Initialize the batch processor.

        Args:
            results_dir: Directory to store batch metadata and results
            transcriber: Video transcriber instance (injected later if None)
            app: Flask application instance for context in background threads
        """
        self.results_dir = results_dir
        self.batches: Dict[str, BatchSession] = {}
        self.memory_manager = MemoryManager()
        self.transcriber = transcriber  # Will be injected later if not provided
        self.app = app  # Flask app instance for context

        # Ensure batch metadata directory exists
        self.batch_metadata_dir = os.path.join(results_dir, "batches")
        os.makedirs(self.batch_metadata_dir, exist_ok=True)

        # Load existing batches
        self._load_existing_batches()

    def set_transcriber(self, transcriber: VideoTranscriber) -> None:
        """Set the transcriber instance (for dependency injection)."""
        self.transcriber = transcriber

    def set_app(self, app) -> None:
        """Set the Flask app instance (for application context in background threads)."""
        self.app = app

    def create_batch(
        self,
        name: Optional[str] = None,
        max_concurrent: Optional[int] = None,
    ) -> str:
        """Create a new batch session."""
        batch_id = str(uuid.uuid4())

        # Auto-determine max concurrent based on system resources
        if max_concurrent is None:
            memory_info = self.memory_manager.get_memory_info()
            max_concurrent = min(
                self.memory_manager.get_optimal_workers(),
                2 if memory_info["system_available_gb"] < 8 else 3,
            )

        batch = BatchSession(
            batch_id=batch_id,
            name=name,
            max_concurrent=max_concurrent,
        )

        self.batches[batch_id] = batch
        self._save_batch_metadata(batch)

        logger.info(f"Created batch {batch_id} with max_concurrent={max_concurrent}")
        return batch_id

    def add_video_to_batch(
        self,
        batch_id: str,
        file_path: str,
        original_filename: str,
        session_name: Optional[str] = None,
    ) -> str:
        """Add a video to an existing batch."""
        if batch_id not in self.batches:
            raise ValueError(f"Batch {batch_id} not found")

        batch = self.batches[batch_id]

        if batch.status != BatchStatus.PENDING:
            raise ValueError(
                f"Cannot add videos to batch with status {batch.status.value}"
            )

        job_id = str(uuid.uuid4())
        job = BatchJob(
            job_id=job_id,
            file_path=file_path,
            original_filename=original_filename,
            session_name=session_name,
        )

        batch.add_job(job)
        self._save_batch_metadata(batch)

        logger.info(f"Added job {job_id} to batch {batch_id}")
        return job_id

    def start_batch(self, batch_id: str) -> bool:
        """Start processing a batch."""
        if batch_id not in self.batches:
            raise ValueError(f"Batch {batch_id} not found")

        batch = self.batches[batch_id]

        if batch.status != BatchStatus.PENDING:
            raise ValueError(f"Cannot start batch with status {batch.status.value}")

        if not batch.jobs:
            raise ValueError("Cannot start empty batch")

        batch.status = BatchStatus.PROCESSING
        batch.started_at = datetime.now()
        self._save_batch_metadata(batch)

        # Start processing in background thread
        import threading

        thread = threading.Thread(target=self._process_batch, args=(batch,))
        thread.daemon = True
        thread.start()

        logger.info(f"Started batch {batch_id} with {len(batch.jobs)} jobs")
        return True

    def _process_batch(self, batch: BatchSession) -> None:
        """Process all jobs in a batch with concurrency control."""
        try:
            with ThreadPoolExecutor(max_workers=batch.max_concurrent) as executor:
                # Submit all jobs
                future_to_job = {
                    executor.submit(self._process_single_job, batch, job): job
                    for job in batch.jobs
                }

                # Process completed jobs
                for future in as_completed(future_to_job):
                    job = future_to_job[future]
                    try:
                        future.result()  # This will raise any exceptions
                    except Exception as e:
                        logger.error(f"Job {job.job_id} failed: {e}")
                        job.status = VideoStatus.FAILED
                        job.error_message = str(e)
                        job.completed_at = datetime.now()

                    self._save_batch_metadata(batch)

            # Update batch completion status
            batch.completed_at = datetime.now()
            if batch.started_at:
                batch.total_duration = (
                    batch.completed_at - batch.started_at
                ).total_seconds()
            else:
                batch.total_duration = 0.0

            # Determine final batch status
            failed_jobs = [j for j in batch.jobs if j.status == VideoStatus.FAILED]
            if failed_jobs and len(failed_jobs) == len(batch.jobs):
                batch.status = BatchStatus.FAILED
                batch.error_message = "All jobs failed"
            elif failed_jobs:
                batch.status = BatchStatus.COMPLETED
                batch.error_message = (
                    f"{len(failed_jobs)} of {len(batch.jobs)} jobs failed"
                )
            else:
                batch.status = BatchStatus.COMPLETED

            self._save_batch_metadata(batch)
            logger.info(
                f"Batch {batch.batch_id} completed with status {batch.status.value}"
            )

        except Exception as e:
            batch.status = BatchStatus.FAILED
            batch.error_message = f"Batch processing failed: {str(e)}"
            batch.completed_at = datetime.now()
            self._save_batch_metadata(batch)
            logger.error(f"Batch {batch.batch_id} failed: {e}")

    def _process_single_job(self, batch: BatchSession, job: BatchJob) -> None:
        """Process a single video job."""
        if not self.transcriber:
            raise RuntimeError(
                "Transcriber not initialized. Call set_transcriber() first."
            )

        # Run within Flask application context if available
        if self.app:
            with self.app.app_context():
                self._process_single_job_with_context(batch, job)
        else:
            self._process_single_job_with_context(batch, job)

    def _process_single_job_with_context(
        self, batch: BatchSession, job: BatchJob
    ) -> None:
        """Process a single video job with proper context."""
        assert (
            self.transcriber is not None
        ), "Transcriber must be set before processing jobs"

        try:
            job.status = VideoStatus.PROCESSING
            job.started_at = datetime.now()

            # Generate unique session ID for this job
            job.session_id = f"batch_{batch.batch_id[:8]}_{job.job_id[:8]}"

            # Save metadata when job starts processing
            self._save_batch_metadata(batch)

            logger.info(f"Starting job {job.job_id} for file {job.original_filename}")

            # Process the video using existing transcription service
            result = self.transcriber.process_video(
                video_path=job.file_path,
                session_name=job.session_name,
                original_filename=job.original_filename,
            )

            # Extract session information from result
            job.session_id = result["session_id"]
            job.results_path = result["session_dir"]

            job.status = VideoStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress = 1.0

            # Save metadata when job completes
            self._save_batch_metadata(batch)

            logger.info(f"Completed job {job.job_id}")

        except Exception as e:
            job.status = VideoStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()

            # Save metadata when job fails
            self._save_batch_metadata(batch)

            logger.error(f"Job {job.job_id} failed: {e}")
            raise

    def _update_job_progress(
        self, job: BatchJob, progress_data: Dict[str, Any]
    ) -> None:
        """Update job progress from transcription callback."""
        if "progress" in progress_data:
            job.progress = progress_data["progress"] / 100.0

    def get_batch(self, batch_id: str) -> Optional[BatchSession]:
        """Get batch by ID."""
        return self.batches.get(batch_id)

    def list_batches(self) -> List[Dict[str, Any]]:
        """List all batches with summary information."""
        return [
            {
                "batch_id": batch.batch_id,
                "name": batch.name,
                "status": batch.status.value,
                "created_at": batch.created_at.isoformat(),
                "total_jobs": len(batch.jobs),
                "progress": batch.get_progress(),
            }
            for batch in sorted(
                self.batches.values(), key=lambda b: b.created_at, reverse=True
            )
        ]

    def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a batch (only if pending or processing)."""
        if batch_id not in self.batches:
            return False

        batch = self.batches[batch_id]

        if batch.status in [
            BatchStatus.COMPLETED,
            BatchStatus.FAILED,
            BatchStatus.CANCELLED,
        ]:
            return False

        batch.status = BatchStatus.CANCELLED
        batch.completed_at = datetime.now()

        # Cancel pending jobs
        for job in batch.jobs:
            if job.status == VideoStatus.QUEUED:
                job.status = VideoStatus.SKIPPED

        self._save_batch_metadata(batch)
        logger.info(f"Cancelled batch {batch_id}")
        return True

    def delete_batch(self, batch_id: str) -> bool:
        """Delete a batch and its metadata."""
        if batch_id not in self.batches:
            return False

        # Remove from memory
        del self.batches[batch_id]

        # Remove metadata file
        metadata_file = os.path.join(self.batch_metadata_dir, f"{batch_id}.json")
        if os.path.exists(metadata_file):
            os.remove(metadata_file)

        logger.info(f"Deleted batch {batch_id}")
        return True

    def _save_batch_metadata(self, batch: BatchSession) -> None:
        """Save batch metadata to disk."""
        metadata_file = os.path.join(self.batch_metadata_dir, f"{batch.batch_id}.json")
        try:
            with open(metadata_file, "w") as f:
                json.dump(batch.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save batch metadata: {e}")

    def _load_existing_batches(self) -> None:
        """Load existing batch metadata from disk."""
        try:
            for filename in os.listdir(self.batch_metadata_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.batch_metadata_dir, filename)
                    try:
                        with open(filepath, "r") as f:
                            data = json.load(f)
                        batch = BatchSession.from_dict(data)
                        self.batches[batch.batch_id] = batch
                    except Exception as e:
                        logger.error(f"Failed to load batch from {filename}: {e}")
        except FileNotFoundError:
            # Directory doesn't exist yet, which is fine
            pass


# Global batch processor instance
batch_processor = BatchProcessor()
