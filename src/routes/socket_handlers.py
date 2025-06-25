"""Socket.IO event handlers for the video transcriber application."""

import logging
from flask import request
from flask_socketio import emit, join_room, leave_room

from src.utils import is_valid_session_id

logger = logging.getLogger(__name__)

# Global references (will be injected from main app)
progress_tracker = None


def init_socket_globals(pt):
    """Initialize global references for socket handlers"""
    global progress_tracker
    progress_tracker = pt


def register_socket_handlers(socketio):
    """Register all socket event handlers"""
    
    @socketio.on('connect')
    def on_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'status': 'connected'})
    
    
    @socketio.on('disconnect')
    def on_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")
    
    
    @socketio.on('join_session')
    def on_join_session(data):
        """Handle client joining a session room"""
        session_id = data.get('session_id', '')
        
        if not is_valid_session_id(session_id):
            emit('error', {'message': 'Invalid session ID'})
            return
        
        join_room(session_id)
        logger.debug(f"Client {request.sid} joined session {session_id}")
        emit('joined_session', {'session_id': session_id})
        
        # Send current progress if available
        if progress_tracker:
            current_progress = progress_tracker.get_session_progress(session_id)
            if current_progress:
                emit('progress_update', current_progress)
    
    
    @socketio.on('leave_session')
    def on_leave_session(data):
        """Handle client leaving a session room"""
        session_id = data.get('session_id', '')
        leave_room(session_id)
        logger.debug(f"Client {request.sid} left session {session_id}")
        emit('left_session', {'session_id': session_id})
    
    
    @socketio.on('get_progress')
    def on_get_progress(data):
        """Handle request for current progress"""
        session_id = data.get('session_id', '')
        
        if not is_valid_session_id(session_id):
            emit('error', {'message': 'Invalid session ID'})
            return
        
        if progress_tracker:
            current_progress = progress_tracker.get_session_progress(session_id)
            if current_progress:
                emit('progress_update', current_progress)
            else:
                emit('error', {'message': f'No progress data for session {session_id}'})