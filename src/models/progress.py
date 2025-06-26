"""
Progress tracking module.

This module provides real-time progress tracking capabilities for WebSocket
communication during video processing operations.
"""

import logging
import threading
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Real-time progress tracking for WebSocket communication.

    This class manages progress tracking sessions for video processing operations,
    providing real-time updates via WebSocket communication and automatic time
    estimation capabilities.
    """

    def __init__(self, socketio: Optional[Any] = None) -> None:
        """
        Initialize the progress tracker.

        Args:
            socketio: Optional SocketIO instance for real-time updates
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.socketio = socketio

    def start_session(
        self, session_id: str, total_chunks: int = 0, video_duration: float = 0
    ) -> None:
        """
        Initialize a new progress tracking session.

        Args:
            session_id: Unique identifier for the session
            total_chunks: Total number of chunks to process
            video_duration: Duration of the video in seconds
        """
        with self.lock:
            self.sessions[session_id] = {
                "status": "starting",
                "progress": 0.0,
                "current_task": "Initializing...",
                "chunks_total": total_chunks,
                "chunks_completed": 0,
                "current_chunk": 0,
                "start_time": time.time(),
                "estimated_time": None,
                "video_duration": video_duration,
                "stage": "initialization",
                "stage_progress": 0.0,
                "details": {},
            }
            logger.info(f"Started progress tracking for session {session_id}")
            self.emit_progress(session_id)

    def update_progress(self, session_id: str, **updates: Any) -> None:
        """
        Update progress for a session.

        Args:
            session_id: Session identifier
            **updates: Progress updates to apply
        """
        with self.lock:
            if session_id not in self.sessions:
                logger.warning(
                    f"Attempted to update non-existent session: {session_id}"
                )
                return

            session = self.sessions[session_id]
            session.update(updates)

            # Calculate estimated time remaining
            progress = session.get("progress", 0)
            if 0 < progress < 100:
                elapsed = time.time() - session["start_time"]
                total_estimated = elapsed / (progress / 100)
                session["estimated_time"] = max(0, total_estimated - elapsed)

            self.emit_progress(session_id)
            logger.debug(
                f"Progress update for {session_id}: {session.get('current_task', 'Unknown')} "
                f"({progress:.1f}%)"
            )

    def update_chunk_progress(
        self,
        session_id: str,
        chunk_number: int,
        chunk_total: int,
        task_description: str = "",
    ) -> None:
        """
        Update progress based on chunk completion.

        Args:
            session_id: Session identifier
            chunk_number: Current chunk number being processed
            chunk_total: Total number of chunks
            task_description: Optional description of current task
        """
        if session_id not in self.sessions:
            logger.warning(
                f"Attempted to update chunks for non-existent session: {session_id}"
            )
            return

        # Calculate overall progress (chunks are 70% of total work)
        chunk_progress = (chunk_number / chunk_total) * 70 if chunk_total > 0 else 0
        overall_progress = 20 + chunk_progress  # 20% for initial setup

        task_text = f"Processing chunk {chunk_number}/{chunk_total}"
        if task_description:
            task_text += f" - {task_description}"

        self.update_progress(
            session_id,
            current_chunk=chunk_number,
            chunks_completed=chunk_number,
            progress=overall_progress,
            current_task=task_text,
            stage="transcription",
            stage_progress=chunk_progress,
        )

    def complete_session(
        self,
        session_id: str,
        success: bool = True,
        message: str = "Processing complete!",
    ) -> None:
        """
        Mark session as completed.

        Args:
            session_id: Session identifier
            success: Whether the session completed successfully
            message: Completion message to display
        """
        with self.lock:
            if session_id not in self.sessions:
                logger.warning(
                    f"Attempted to complete non-existent session: {session_id}"
                )
                return

            session = self.sessions[session_id]
            session.update(
                {
                    "status": "completed" if success else "error",
                    "progress": 100.0 if success else session["progress"],
                    "current_task": message,
                    "stage": "completed" if success else "error",
                }
            )
            self.emit_progress(session_id)
            logger.info(
                f"Session {session_id} marked as {'completed' if success else 'failed'}"
            )

    def emit_progress(self, session_id: str) -> None:
        """
        Emit progress update via SocketIO.

        Args:
            session_id: Session identifier
        """
        if session_id not in self.sessions:
            return

        if not self.socketio:
            logger.debug("No SocketIO instance available for progress emission")
            return

        try:
            progress_data = self.sessions[session_id]
            logger.debug(
                f"Emitting progress for session {session_id}: "
                f"{progress_data.get('progress', 0):.1f}% - "
                f"{progress_data.get('current_task', 'Unknown')}"
            )
            self.socketio.emit("progress_update", progress_data, room=session_id)
        except Exception as e:
            logger.warning(f"Failed to emit progress for session {session_id}: {e}")

    def get_session_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current progress for a session.

        Args:
            session_id: Session identifier

        Returns:
            Session progress data or None if session doesn't exist
        """
        with self.lock:
            return self.sessions.get(session_id, None)

    def cleanup_session(self, session_id: str) -> None:
        """
        Remove session from tracking.

        Args:
            session_id: Session identifier
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.debug(f"Cleaned up progress tracking for session {session_id}")

    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active tracking sessions.

        Returns:
            Dict of session IDs to their progress data
        """
        with self.lock:
            return self.sessions.copy()

    def cleanup_stale_sessions(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up sessions older than the specified age.

        Args:
            max_age_seconds: Maximum age for sessions in seconds (default: 1 hour)

        Returns:
            Number of sessions cleaned up
        """
        current_time = time.time()
        sessions_to_remove = []

        with self.lock:
            for session_id, session_data in self.sessions.items():
                session_age = current_time - session_data.get(
                    "start_time", current_time
                )
                if session_age > max_age_seconds:
                    sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                del self.sessions[session_id]

        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} stale progress sessions")

        return len(sessions_to_remove)
