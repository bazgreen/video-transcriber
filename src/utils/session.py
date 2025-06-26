"""
Session management utilities.

This module provides centralized session validation and management functions
to eliminate duplicate code across routes and services.
"""

import logging
import os
from typing import Any, Dict, Tuple

from src.config import AppConfig
from src.models.exceptions import UserFriendlyError
from src.utils.helpers import is_valid_session_id, load_session_metadata

logger = logging.getLogger(__name__)
config = AppConfig()


def validate_session_access(session_id: str, results_folder: str = None) -> str:
    """
    Validate session ID and return session path.

    This function centralizes session validation logic that was duplicated
    across multiple routes.

    Args:
        session_id: Session identifier to validate
        results_folder: Optional results folder path (uses config default if None)

    Returns:
        Validated session path

    Raises:
        UserFriendlyError: If session ID is invalid or path is unsafe
    """
    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID")

    if results_folder is None:
        results_folder = config.RESULTS_FOLDER

    session_path = os.path.join(results_folder, session_id)

    # Ensure the path is within the results folder (prevent path traversal)
    if not os.path.abspath(session_path).startswith(os.path.abspath(results_folder)):
        raise UserFriendlyError("Invalid session path")

    return session_path


def ensure_session_exists(
    session_id: str, results_folder: str = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Validate session exists and return path with metadata.

    This function combines session validation with existence checking and
    metadata loading, eliminating duplicate code patterns.

    Args:
        session_id: Session identifier to validate
        results_folder: Optional results folder path (uses config default if None)

    Returns:
        Tuple of (session_path, metadata_dict)

    Raises:
        UserFriendlyError: If session is invalid or doesn't exist
    """
    session_path = validate_session_access(session_id, results_folder)

    if not os.path.exists(session_path):
        raise UserFriendlyError(f"Session '{session_id}' not found")

    # Load session metadata
    metadata = load_session_metadata(session_id, session_path)

    logger.debug(f"Validated session access: {session_id}")
    return session_path, metadata


def validate_session_for_socket(session_id: str) -> bool:
    """
    Validate session for WebSocket operations.

    This is a lighter validation for socket operations that only checks
    session ID format without requiring file system access.

    Args:
        session_id: Session identifier to validate

    Returns:
        True if session ID is valid format, False otherwise
    """
    return is_valid_session_id(session_id)


def get_session_list(results_folder: str = None) -> list:
    """
    Get list of all available sessions with metadata.

    Args:
        results_folder: Optional results folder path (uses config default if None)

    Returns:
        List of session metadata dictionaries
    """
    if results_folder is None:
        results_folder = config.RESULTS_FOLDER

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
        return []

    sessions_list = []
    for session_folder in os.listdir(results_folder):
        session_path = os.path.join(results_folder, session_folder)
        if os.path.isdir(session_path):
            try:
                metadata = load_session_metadata(session_folder, session_path)
                sessions_list.append(metadata)
            except Exception as e:
                logger.warning(
                    f"Failed to load metadata for session {session_folder}: {e}"
                )

    # Sort by creation time (newest first)
    sessions_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return sessions_list
