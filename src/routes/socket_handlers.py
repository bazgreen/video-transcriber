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


def init_socket_globals(pt: Any) -> None:
    """
    Initialize global references for socket handlers.

    This function is called during application initialization to inject
    dependencies that socket handlers need to access.

    Args:
        pt: ProgressTracker instance for real-time updates
    """
    global progress_tracker
    progress_tracker = pt


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
