"""Routes module for the video transcriber application."""

from .api import api_bp
from .main import main_bp
from .socket_handlers import register_socket_handlers

__all__ = ["main_bp", "api_bp", "register_socket_handlers"]
