"""
Socket.IO event handlers for the video transcriber application.

This module provides real-time WebSocket communication for progress updates,
session management, and client-server interaction during video processing.
"""

import logging
from typing import Any, Dict, Optional

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

from src.utils import is_valid_session_id

logger = logging.getLogger(__name__)

# Global references (will be injected from main app)
progress_tracker: Optional[Any] = None
batch_processor: Optional[Any] = None


def init_socket_globals(pt: Any, bp: Optional[Any] = None) -> None:
    """
    Initialize global references for socket handlers.

    This function is called during application initialization to inject
    dependencies that socket handlers need to access.

    Args:
        pt: ProgressTracker instance for real-time updates
        bp: BatchProcessor instance for batch operations
    """
    global progress_tracker, batch_processor
    progress_tracker = pt
    batch_processor = bp


def register_socket_handlers(socketio: SocketIO) -> None:
    """
    Register all WebSocket event handlers with the SocketIO instance.

    This function sets up all the WebSocket event handlers for client
    communication during video processing operations.

    Args:
        socketio: Flask-SocketIO instance to register handlers with

    Registered Events:
    - connect: Client connection handling
    - disconnect: Client disconnection cleanup
    - join_session: Join session room for progress updates
    - leave_session: Leave session room
    - get_progress: Request current progress for a session
    """

    @socketio.on("connect")
    def on_connect() -> None:
        """
        Handle client WebSocket connection.

        Logs the connection and sends confirmation to the client.
        """
        logger.info(f"Client connected: {request.sid}")  # type: ignore
        emit("connected", {"status": "connected"})

    @socketio.on("disconnect")
    def on_disconnect() -> None:
        """
        Handle client WebSocket disconnection.

        Performs cleanup logging when clients disconnect.
        """
        logger.info(f"Client disconnected: {request.sid}")  # type: ignore

    @socketio.on("join_session")
    def on_join_session(data: Dict[str, Any]) -> None:
        """
        Handle client joining a session room for progress updates.

        Args:
            data: Dictionary containing session_id

        Emits:
            joined_session: Confirmation of room join
            progress_update: Current progress if available
            error: If session ID is invalid
        """
        session_id = data.get("session_id", "")

        if not is_valid_session_id(session_id):
            emit("error", {"message": "Invalid session ID"})
            return

        join_room(session_id)
        logger.debug(
            f"Client {request.sid} joined session {session_id}"  # type: ignore
        )
        emit("joined_session", {"session_id": session_id})

        # Send current progress if available
        if progress_tracker:
            current_progress = progress_tracker.get_session_progress(session_id)
            if current_progress:
                emit("progress_update", current_progress)

    @socketio.on("leave_session")
    def on_leave_session(data: Dict[str, Any]) -> None:
        """
        Handle client leaving a session room.

        Args:
            data: Dictionary containing session_id

        Emits:
            left_session: Confirmation of room leave
        """
        session_id = data.get("session_id", "")
        leave_room(session_id)
        logger.debug(f"Client {request.sid} left session {session_id}")  # type: ignore
        emit("left_session", {"session_id": session_id})

    @socketio.on("get_progress")
    def on_get_progress(data: Dict[str, Any]) -> None:
        """
        Handle request for current progress of a session.

        Args:
            data: Dictionary containing session_id

        Emits:
            progress_update: Current progress data if available
            error: If session ID is invalid or no progress data exists
        """
        session_id = data.get("session_id", "")

        if not is_valid_session_id(session_id):
            emit("error", {"message": "Invalid session ID"})
            return

        if progress_tracker:
            current_progress = progress_tracker.get_session_progress(session_id)
            if current_progress:
                emit("progress_update", current_progress)
            else:
                emit("error", {"message": f"No progress data for session {session_id}"})

    @socketio.on("get_active_sessions")
    def on_get_active_sessions() -> None:
        """
        Handle request for all active sessions.

        Emits:
            active_sessions: Dictionary of active session data
        """
        if progress_tracker:
            active_sessions = progress_tracker.get_active_sessions()
            emit("active_sessions", active_sessions)
        else:
            emit("active_sessions", {})

    # ========================================
    # BATCH PROCESSING WEBSOCKET HANDLERS
    # ========================================

    @socketio.on("join_batch")
    def on_join_batch(data: Dict[str, Any]) -> None:
        """
        Handle client joining a batch room for real-time batch progress updates.

        Args:
            data: Dictionary containing batch_id

        Emits:
            joined_batch: Confirmation of batch room join
            batch_status: Current batch status and progress
            error: If batch ID is invalid or not found
        """
        batch_id = data.get("batch_id", "")

        if not batch_id:
            emit("error", {"message": "Batch ID is required"})
            return

        if not batch_processor:
            emit("error", {"message": "Batch processor not available"})
            return

        # Validate batch exists
        batch = batch_processor.get_batch(batch_id)
        if not batch:
            emit("error", {"message": f"Batch {batch_id} not found"})
            return

        # Join batch room
        batch_room = f"batch_{batch_id}"
        join_room(batch_room)
        logger.debug(f"Client {request.sid} joined batch room {batch_room}")

        # Send confirmation and current batch status
        emit("joined_batch", {"batch_id": batch_id, "room": batch_room})

        # Send current batch progress
        batch_data = batch.to_dict()
        emit(
            "batch_status_update",
            {
                "batch_id": batch_id,
                "status": batch_data["status"],
                "progress": batch_data["progress"],
                "jobs": batch_data["jobs"],
            },
        )

    @socketio.on("leave_batch")
    def on_leave_batch(data: Dict[str, Any]) -> None:
        """
        Handle client leaving a batch room.

        Args:
            data: Dictionary containing batch_id

        Emits:
            left_batch: Confirmation of leaving batch room
        """
        batch_id = data.get("batch_id", "")

        if batch_id:
            batch_room = f"batch_{batch_id}"
            leave_room(batch_room)
            logger.debug(f"Client {request.sid} left batch room {batch_room}")
            emit("left_batch", {"batch_id": batch_id})

    @socketio.on("get_batch_status")
    def on_get_batch_status(data: Dict[str, Any]) -> None:
        """
        Handle request for current batch status and progress.

        Args:
            data: Dictionary containing batch_id

        Emits:
            batch_status_update: Current batch status and detailed progress
            error: If batch ID is invalid or not found
        """
        batch_id = data.get("batch_id", "")

        if not batch_id:
            emit("error", {"message": "Batch ID is required"})
            return

        if not batch_processor:
            emit("error", {"message": "Batch processor not available"})
            return

        batch = batch_processor.get_batch(batch_id)
        if not batch:
            emit("error", {"message": f"Batch {batch_id} not found"})
            return

        # Send detailed batch status
        batch_data = batch.to_dict()
        emit(
            "batch_status_update",
            {
                "batch_id": batch_id,
                "status": batch_data["status"],
                "progress": batch_data["progress"],
                "jobs": batch_data["jobs"],
                "created_at": batch_data["created_at"],
                "started_at": batch_data["started_at"],
                "completed_at": batch_data["completed_at"],
                "total_duration": batch_data["total_duration"],
                "error_message": batch_data["error_message"],
            },
        )

    @socketio.on("get_all_batches")
    def on_get_all_batches() -> None:
        """
        Handle request for all batches summary.

        Emits:
            all_batches_update: List of all batches with summary info
            error: If batch processor not available
        """
        if not batch_processor:
            emit("error", {"message": "Batch processor not available"})
            return

        try:
            batches = batch_processor.list_batches()
            emit("all_batches_update", {"batches": batches})
        except Exception as e:
            logger.error(f"Failed to get all batches: {e}")
            emit("error", {"message": f"Failed to get batches: {str(e)}"})

    @socketio.on("batch_control")
    def on_batch_control(data: Dict[str, Any]) -> None:
        """
        Handle batch control operations (cancel, delete, etc.).

        Args:
            data: Dictionary containing batch_id and action

        Emits:
            batch_control_result: Result of the control operation
            error: If operation fails or is invalid
        """
        batch_id = data.get("batch_id", "")
        action = data.get("action", "")

        if not batch_id or not action:
            emit("error", {"message": "Batch ID and action are required"})
            return

        if not batch_processor:
            emit("error", {"message": "Batch processor not available"})
            return

        try:
            result = False
            message = ""

            if action == "cancel":
                result = batch_processor.cancel_batch(batch_id)
                message = (
                    "Batch cancelled successfully"
                    if result
                    else "Failed to cancel batch"
                )
            elif action == "delete":
                result = batch_processor.delete_batch(batch_id)
                message = (
                    "Batch deleted successfully" if result else "Failed to delete batch"
                )
            else:
                emit("error", {"message": f"Unknown action: {action}"})
                return

            emit(
                "batch_control_result",
                {
                    "batch_id": batch_id,
                    "action": action,
                    "success": result,
                    "message": message,
                },
            )

            # If successful, broadcast batch status update
            if result and action != "delete":
                batch = batch_processor.get_batch(batch_id)
                if batch:
                    batch_room = f"batch_{batch_id}"
                    socketio.emit(
                        "batch_status_update",
                        {
                            "batch_id": batch_id,
                            "status": batch.status.value,
                            "progress": batch.get_progress(),
                            "jobs": [job.to_dict() for job in batch.jobs],
                        },
                        room=batch_room,
                    )

        except Exception as e:
            logger.error(f"Batch control operation failed: {e}")
            emit("error", {"message": f"Operation failed: {str(e)}"})


def emit_batch_progress_update(
    socketio_instance: SocketIO, batch_id: str, batch_data: Dict[str, Any]
) -> None:
    """
    Emit batch progress update to all clients in the batch room.

    This function is called by the batch processor when progress updates occur.

    Args:
        socketio_instance: SocketIO instance for emitting events
        batch_id: ID of the batch to update
        batch_data: Current batch data including progress and job statuses
    """
    try:
        batch_room = f"batch_{batch_id}"
        socketio_instance.emit(
            "batch_progress_update",
            {
                "batch_id": batch_id,
                "status": batch_data.get("status"),
                "progress": batch_data.get("progress"),
                "jobs": batch_data.get("jobs", []),
                "timestamp": batch_data.get("timestamp"),
            },
            room=batch_room,
        )

        logger.debug(f"Emitted batch progress update for {batch_id}")
    except Exception as e:
        logger.warning(f"Failed to emit batch progress update for {batch_id}: {e}")


def emit_job_status_update(
    socketio_instance: SocketIO, batch_id: str, job_data: Dict[str, Any]
) -> None:
    """
    Emit individual job status update to batch room.

    Args:
        socketio_instance: SocketIO instance for emitting events
        batch_id: ID of the batch containing the job
        job_data: Current job data including status and progress
    """
    try:
        batch_room = f"batch_{batch_id}"
        socketio_instance.emit(
            "job_status_update",
            {
                "batch_id": batch_id,
                "job_id": job_data.get("job_id"),
                "status": job_data.get("status"),
                "progress": job_data.get("progress", 0),
                "session_name": job_data.get("session_name"),
                "original_filename": job_data.get("original_filename"),
                "error_message": job_data.get("error_message"),
                "timestamp": job_data.get("timestamp"),
            },
            room=batch_room,
        )

        logger.debug(
            f"Emitted job status update for {job_data.get('job_id')} in batch {batch_id}"
        )
    except Exception as e:
        logger.warning(f"Failed to emit job status update: {e}")
