"""
Main application factory with optional authentication support.

This module provides a factory function to create the Flask application
with optional authentication enabled. It maintains backward compatibility
by allowing the app to run without authentication if dependencies are missing.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from flask import Flask

logger = logging.getLogger(__name__)


def create_app_with_auth(app: Flask, enable_auth: bool = True) -> Optional[object]:
    """
    Add authentication support to the Flask application.

    Args:
        app: Flask application instance
        enable_auth: Whether to enable authentication features

    Returns:
        LoginManager instance if authentication enabled, None otherwise
    """
    if not enable_auth:
        logger.info("Authentication disabled")
        return None

    try:
        # Import auth dependencies
        from flask_login import LoginManager
        from flask_wtf.csrf import CSRFProtect

        from src.models.auth import User, init_auth_db
        from src.routes.auth import auth_bp

        # Configure Flask-Login
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = "auth.login"
        login_manager.login_message = "Please sign in to access this page."
        login_manager.login_message_category = "info"

        # Configure CSRF Protection
        csrf = CSRFProtect()
        csrf.init_app(app)

        # CSRF error handler (using app.errorhandler instead of csrf.error_handler)
        @app.errorhandler(400)
        def handle_csrf_error(e):
            # Check if this is a CSRF error
            if hasattr(e, "description") and "csrf" in str(e.description).lower():
                logger.warning(f"CSRF error detected: {e.description}")
                from flask import flash, redirect, request
                from flask import session as flask_session
                from flask import url_for

                # Clear any potentially corrupted session data
                flask_session.clear()

                # Provide user-friendly error message
                flash(
                    "Your session has expired. Please refresh the page and try again.",
                    "error",
                )

                # Redirect back to the appropriate page
                if request.endpoint and "auth." in request.endpoint:
                    if "login" in request.endpoint:
                        return redirect(url_for("auth.login"))
                    elif "register" in request.endpoint:
                        return redirect(url_for("auth.register"))
                    elif "change_password" in request.endpoint:
                        return redirect(url_for("auth.change_password"))
                    elif "profile" in request.endpoint:
                        return redirect(
                            url_for("auth.login", next=url_for("auth.profile"))
                        )

                # Default redirect to login
                return redirect(url_for("auth.login"))

            # If not a CSRF error, return the default 400 error
            return e

        # User loader callback
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        # Configure database
        from src.config.settings import AppConfig

        config = AppConfig()

        # Ensure database directory exists and convert to absolute path
        database_url = config.DATABASE_URL
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
            if not os.path.isabs(db_path):
                # Convert relative path to absolute path
                db_path = os.path.abspath(db_path)
                database_url = f"sqlite:///{db_path}"

            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)

        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SESSION_PROTECTION"] = config.SESSION_PROTECTION
        app.config["REMEMBER_COOKIE_DURATION"] = config.REMEMBER_COOKIE_DURATION

        # Configure CSRF settings
        app.config["WTF_CSRF_ENABLED"] = config.WTF_CSRF_ENABLED
        app.config["WTF_CSRF_TIME_LIMIT"] = config.WTF_CSRF_TIME_LIMIT

        # Ensure session configuration for CSRF
        if not app.config.get("SECRET_KEY"):
            logger.warning("SECRET_KEY not set, using default for CSRF")

        # Configure session cookies for CSRF token storage
        app.config["SESSION_COOKIE_SECURE"] = (
            False  # Set to True in production with HTTPS
        )
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

        # Initialize database
        init_auth_db(app)

        # Register auth blueprint
        app.register_blueprint(auth_bp)

        logger.info("Authentication system initialized successfully")
        return login_manager

    except ImportError as e:
        logger.warning(f"Authentication dependencies not available: {e}")
        logger.info(
            "Install auth dependencies with: pip install -r requirements-auth.txt"
        )
        return None
    except Exception as e:
        logger.error(f"Failed to initialize authentication: {e}")
        return None


def configure_auth_context(app: Flask, login_manager: Optional[object]) -> None:
    """
    Configure authentication context for templates.

    Args:
        app: Flask application instance
        login_manager: LoginManager instance or None
    """
    if login_manager is None:
        # Provide dummy auth context for templates
        @app.context_processor
        def inject_auth_context():
            return {
                "current_user": type(
                    "AnonymousUser",
                    (),
                    {"is_authenticated": False, "display_name": "Anonymous"},
                )()
            }

    else:
        # Flask-Login automatically provides current_user
        pass


def check_auth_status() -> dict:
    """
    Check authentication system status.

    Returns:
        Dict with auth status information
    """
    try:
        import flask_login
        import flask_sqlalchemy
        import flask_wtf

        return {
            "enabled": True,
            "dependencies_available": True,
            "flask_login_version": getattr(flask_login, "__version__", "unknown"),
            "flask_sqlalchemy_version": getattr(
                flask_sqlalchemy, "__version__", "unknown"
            ),
        }
    except ImportError as e:
        return {
            "enabled": False,
            "dependencies_available": False,
            "missing_dependency": str(e),
            "install_command": "pip install -r requirements-auth.txt",
        }


def get_auth_routes_info() -> Dict[str, Any]:
    """
    Get information about available auth routes.

    Returns:
        Dict with route information
    """
    base_info: Dict[str, Any] = {
        "public_routes": [
            {"path": "/", "name": "Home", "description": "Main upload page"},
            {
                "path": "/sessions",
                "name": "Sessions",
                "description": "Browse sessions (anonymous + public)",
            },
            {
                "path": "/config",
                "name": "Configuration",
                "description": "Keyword configuration",
            },
        ]
    }

    auth_status = check_auth_status()
    if auth_status["enabled"]:
        base_info["auth_routes"] = [
            {"path": "/auth/login", "name": "Sign In", "description": "User login"},
            {
                "path": "/auth/register",
                "name": "Sign Up",
                "description": "Create new account",
            },
            {
                "path": "/auth/profile",
                "name": "Profile",
                "description": "User profile (login required)",
            },
            {"path": "/auth/logout", "name": "Logout", "description": "Sign out"},
        ]
    else:
        base_info["auth_routes"] = []
        base_info["auth_note"] = (
            "Authentication features not available. Install with: pip install -r requirements-auth.txt"
        )

    return base_info


def secure_session_list(sessions: list, user_id: Optional[int] = None) -> list:
    """
    Filter session list based on user access permissions.

    Args:
        sessions: List of session dictionaries
        user_id: Current user ID (None for anonymous)

    Returns:
        Filtered list of accessible sessions
    """
    try:
        from src.utils.security import SessionAccessControl

        accessible_session_ids = SessionAccessControl.get_user_sessions(
            user_id=user_id, include_public=True
        )

        # Filter sessions to only include accessible ones
        filtered_sessions = [
            session
            for session in sessions
            if session.get("session_id") in accessible_session_ids
        ]

        return filtered_sessions

    except ImportError:
        # Auth not available, return all sessions (backward compatibility)
        return sessions
    except Exception as e:
        logger.error(f"Error filtering sessions: {e}")
        return sessions  # Return all on error to maintain functionality
