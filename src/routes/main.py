"""Main web routes for the video transcriber application."""

import os
import logging
from flask import Blueprint, render_template, request, send_file, redirect, url_for

from src.config import AppConfig
from src.utils import is_valid_session_id, is_safe_path, load_session_metadata
from src.models.exceptions import UserFriendlyError

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)
config = AppConfig()


@main_bp.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@main_bp.route('/results/<session_id>')
def results(session_id):
    """Show results for a specific session"""
    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID")
    
    session_path = os.path.join(config.RESULTS_FOLDER, session_id)
    if not os.path.exists(session_path):
        raise UserFriendlyError(f"Session '{session_id}' not found")
    
    # Load session metadata
    metadata = load_session_metadata(session_id, session_path)
    
    return render_template('results.html', 
                         session_id=session_id,
                         metadata=metadata,
                         session_path=session_path)


@main_bp.route('/download/<session_id>/<filename>')
def download_file(session_id, filename):
    """Download a specific file from a session"""
    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID")
    
    session_path = os.path.join(config.RESULTS_FOLDER, session_id)
    file_path = os.path.join(session_path, filename)
    
    if not is_safe_path(file_path, config.RESULTS_FOLDER):
        raise UserFriendlyError("Invalid file path")
    
    if not os.path.exists(file_path):
        raise UserFriendlyError("File not found")
    
    return send_file(file_path, as_attachment=True)


@main_bp.route('/transcript/<session_id>')
def transcript(session_id):
    """Show interactive transcript for a session"""
    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID")
    
    session_path = os.path.join(config.RESULTS_FOLDER, session_id)
    if not os.path.exists(session_path):
        raise UserFriendlyError(f"Session '{session_id}' not found")
    
    return render_template('transcript.html', session_id=session_id)


@main_bp.route('/sessions')
def sessions():
    """List all sessions"""
    if not os.path.exists(config.RESULTS_FOLDER):
        os.makedirs(config.RESULTS_FOLDER)
        return render_template('sessions.html', sessions=[])
    
    sessions_list = []
    for session_folder in os.listdir(config.RESULTS_FOLDER):
        session_path = os.path.join(config.RESULTS_FOLDER, session_folder)
        if os.path.isdir(session_path):
            metadata = load_session_metadata(session_folder, session_path)
            sessions_list.append(metadata)
    
    # Sort by creation time (newest first)
    sessions_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('sessions.html', sessions=sessions_list)


@main_bp.route('/sessions/search')
def search_sessions():
    """Search sessions by keyword"""
    query = request.args.get('q', '').strip().lower()
    if not query:
        return redirect(url_for('main.sessions'))
    
    if not os.path.exists(config.RESULTS_FOLDER):
        return render_template('sessions.html', sessions=[], search_query=query)
    
    matching_sessions = []
    for session_folder in os.listdir(config.RESULTS_FOLDER):
        session_path = os.path.join(config.RESULTS_FOLDER, session_folder)
        if os.path.isdir(session_path):
            # Load session metadata
            metadata = load_session_metadata(session_folder, session_path)
            
            # Search in session name and original filename
            if (query in metadata.get('session_name', '').lower() or 
                query in metadata.get('original_filename', '').lower() or
                query in session_folder.lower()):
                
                matching_sessions.append(metadata)
                continue
            
            # Search in transcript content
            transcript_file = os.path.join(session_path, 'full_transcript.txt')
            if os.path.exists(transcript_file):
                try:
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                        if query in content:
                            matching_sessions.append(metadata)
                except (IOError, UnicodeDecodeError):
                    pass
    
    # Sort by creation time (newest first)
    matching_sessions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('sessions.html', sessions=matching_sessions, search_query=query)


@main_bp.route('/config')
def config_page():
    """Configuration page"""
    return render_template('config.html')


@main_bp.route('/performance')
def performance():
    """Performance monitoring page"""
    return render_template('performance.html')