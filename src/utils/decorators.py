"""Decorator utilities."""

import functools
import logging

from flask import jsonify

from src.models.exceptions import UserFriendlyError

logger = logging.getLogger(__name__)


def handle_user_friendly_error(func):
    """Decorator to handle UserFriendlyError exceptions and return appropriate JSON responses"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UserFriendlyError as e:
            logger.warning(f"User-friendly error in {func.__name__}: {e}")
            return (
                jsonify(
                    {"success": False, "error": str(e), "error_type": "user_error"}
                ),
                400,
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "An unexpected error occurred. Please try again.",
                        "error_type": "server_error",
                    }
                ),
                500,
            )

    return wrapper
