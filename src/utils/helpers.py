"""Helper utility functions."""

import os
import re
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def is_valid_session_id(session_id: str) -> bool:
    """Validate session_id to prevent path traversal attacks"""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', session_id))


def is_safe_path(file_path: str, base_dir: str) -> bool:
    """Check if file_path is within base_dir to prevent path traversal"""
    try:
        base_path = os.path.abspath(base_dir)
        requested_path = os.path.abspath(file_path)
        return requested_path.startswith(base_path)
    except (OSError, ValueError):
        return False


def format_timestamp(seconds: float) -> str:
    """Format seconds as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def load_session_metadata(session_folder: str, session_path: str) -> Dict[str, str]:
    """
    Load session metadata from metadata.json or parse from folder name.
    
    This function centralizes metadata loading logic to eliminate duplication
    across routes that need session information.
    
    Args:
        session_folder: The session folder name
        session_path: Full path to the session folder
        
    Returns:
        Dictionary containing session metadata
    """
    metadata_file = os.path.join(session_path, 'metadata.json')
    
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                logger.debug(f"Loaded metadata from file for session {session_folder}")
                return metadata
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load metadata file for session {session_folder}: {e}")
            # Fall back to parsing from folder name
    
    # Parse metadata from folder name (legacy sessions)
    metadata = parse_session_metadata(session_folder, session_path)
    logger.debug(f"Parsed metadata from folder name for session {session_folder}")
    return metadata


def parse_session_metadata(session_folder: str, session_path: str) -> Dict[str, str]:
    """Parse session metadata from folder name for legacy sessions without metadata.json
    
    Args:
        session_folder: The session folder name (e.g., 'MySession_20231225_143000')
        session_path: Full path to the session folder
        
    Returns:
        Dictionary containing session metadata with keys:
        - session_id, session_name, original_filename, created_at, status
    """
    # Legacy session without metadata - try to extract session name from folder
    session_name = ''
    
    # Try to parse session folder name (format: SessionName_YYYYMMDD_HHMMSS)
    parts = session_folder.split('_')
    if len(parts) >= 3:
        # Last two parts should be date and time
        date_part = parts[-2]
        time_part = parts[-1]
        
        # Check if they look like date/time
        if (len(date_part) == 8 and date_part.isdigit() and 
            len(time_part) == 6 and time_part.isdigit()):
            # Everything before the last two underscores is the session name
            session_name = '_'.join(parts[:-2])
        else:
            # If it doesn't match the expected format, use the whole folder name
            session_name = session_folder
    else:
        session_name = session_folder
    
    return {
        'session_id': session_folder,
        'session_name': session_name or 'Unnamed Session',
        'original_filename': 'Unknown',
        'created_at': 'Unknown',
        'status': 'completed'  # Assume legacy sessions are completed
    }