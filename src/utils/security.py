"""
Security utilities for file access control and session protection.

This module provides secure file access controls while maintaining
backward compatibility with anonymous usage.
"""

import logging
import os
from typing import Optional, Tuple

from flask import abort, request
from flask_login import current_user

from src.models.auth import AnonymousSession, UserSession
from src.utils.helpers import is_valid_session_id

logger = logging.getLogger(__name__)


class SessionAccessControl:
    """Centralized session access control."""

    @staticmethod
    def check_session_access(
        session_id: str, allow_anonymous: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if current user can access a session.

        Args:
            session_id: Session identifier
            allow_anonymous: Whether to allow anonymous session access

        Returns:
            Tuple of (has_access, reason_if_denied)
        """
        if not is_valid_session_id(session_id):
            return False, "Invalid session ID"

        # Check user sessions first
        user_session = UserSession.find_by_session_id(session_id)
        if user_session:
            # If user is authenticated and owns the session
            if (
                current_user.is_authenticated
                and user_session.user_id == current_user.id
            ):
                return True, None

            # If session is public
            if user_session.is_public:
                return True, None

            # Check for valid share token
            share_token = request.args.get("token")
            if share_token and user_session.shared_token == share_token:
                return True, None

            return False, "Session is private"

        # Check anonymous sessions (backward compatibility)
        if allow_anonymous:
            anonymous_session = AnonymousSession.find_by_session_id(session_id)
            if anonymous_session:
                return True, None

            # Allow access to new sessions that aren't in database yet
            return True, None

        return False, "Session not found"

    @staticmethod
    def require_session_access(session_id: str, allow_anonymous: bool = True) -> None:
        """
        Require session access or abort with 403/404.

        Args:
            session_id: Session identifier
            allow_anonymous: Whether to allow anonymous session access

        Raises:
            HTTPException: 403 or 404 if access denied
        """
        has_access, reason = SessionAccessControl.check_session_access(
            session_id, allow_anonymous
        )

        if not has_access:
            if reason == "Session not found":
                abort(404)
            elif reason == "Session is private":
                abort(403)
            else:
                abort(403)

    @staticmethod
    def get_user_sessions(
        user_id: Optional[int] = None, include_public: bool = False
    ) -> list:
        """
        Get sessions accessible by user.

        Args:
            user_id: User ID (None for current user)
            include_public: Whether to include public sessions from other users

        Returns:
            List of accessible sessions
        """
        if user_id is None and current_user.is_authenticated:
            user_id = current_user.id

        sessions = []

        if user_id:
            # Get user's own sessions
            user_sessions = UserSession.query.filter_by(user_id=user_id).all()
            sessions.extend([us.session_id for us in user_sessions])

            # Include public sessions if requested
            if include_public:
                public_sessions = UserSession.query.filter(
                    UserSession.is_public is True, UserSession.user_id != user_id
                ).all()
                sessions.extend([ps.session_id for ps in public_sessions])
        else:
            # Anonymous user - only get anonymous sessions and public sessions
            anonymous_sessions = AnonymousSession.query.all()
            sessions.extend([ans.session_id for ans in anonymous_sessions])

            if include_public:
                public_sessions = UserSession.query.filter_by(is_public=True).all()
                sessions.extend([ps.session_id for ps in public_sessions])

        return list(set(sessions))  # Remove duplicates

    @staticmethod
    def is_session_owner(session_id: str, user_id: Optional[int] = None) -> bool:
        """
        Check if user owns a session.

        Args:
            session_id: Session identifier
            user_id: User ID (None for current user)

        Returns:
            True if user owns the session
        """
        if user_id is None and current_user.is_authenticated:
            user_id = current_user.id

        if not user_id:
            return False

        user_session = UserSession.find_by_session_id(session_id)
        return user_session is not None and user_session.user_id == user_id

    @staticmethod
    def secure_file_path(session_id: str, filename: str, results_folder: str) -> str:
        """
        Get secure file path after access validation.

        Args:
            session_id: Session identifier
            filename: File name within session
            results_folder: Results folder path

        Returns:
            Secure file path

        Raises:
            HTTPException: If access denied or path unsafe
        """
        # Validate session access
        SessionAccessControl.require_session_access(session_id)

        # Validate file path security
        session_path = os.path.join(results_folder, session_id)
        file_path = os.path.join(session_path, filename)

        # Ensure path is within session directory
        if not os.path.abspath(file_path).startswith(os.path.abspath(session_path)):
            abort(403)

        # Check if file exists
        if not os.path.exists(file_path):
            abort(404)

        return file_path


def secure_download(session_id: str, filename: str, results_folder: str):
    """
    Secure file download with access control.

    Args:
        session_id: Session identifier
        filename: File name to download
        results_folder: Results folder path

    Returns:
        Flask send_file response
    """
    from flask import send_file

    file_path = SessionAccessControl.secure_file_path(
        session_id, filename, results_folder
    )

    try:
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"Error serving file {file_path}: {e}")
        abort(500)


def log_access_attempt(session_id: str, action: str, success: bool, reason: str = None):
    """
    Log session access attempts for security monitoring.

    Args:
        session_id: Session identifier
        action: Action attempted (view, download, etc.)
        success: Whether access was granted
        reason: Reason for denial if unsuccessful
    """
    user_info = "authenticated" if current_user.is_authenticated else "anonymous"
    if current_user.is_authenticated:
        user_info = f"user:{current_user.id}:{current_user.username}"

    ip_address = request.remote_addr if request else "unknown"

    log_message = (
        f"Session access: {action} {session_id} by {user_info} from {ip_address}"
    )

    if success:
        logger.info(f"{log_message} - GRANTED")
    else:
        logger.warning(f"{log_message} - DENIED: {reason}")


# Decorator for securing routes
def require_session_access(allow_anonymous: bool = True):
    """
    Decorator to require session access for routes.

    Args:
        allow_anonymous: Whether to allow anonymous access
    """

    def decorator(f):
        def decorated_function(*args, **kwargs):
            session_id = kwargs.get("session_id")
            if session_id:
                SessionAccessControl.require_session_access(session_id, allow_anonymous)
                log_access_attempt(session_id, f.__name__, True)
            return f(*args, **kwargs)

        decorated_function.__name__ = f.__name__
        return decorated_function

    return decorator
