"""
Main application entry point for the modularized video transcriber.

This module initializes and configures the Flask application with all required
components including routing, WebSocket handling, and dependency injection.
"""

import logging
import os
from typing import Any, Dict, Tuple

from flask import Flask, jsonify
from flask_socketio import SocketIO

# Import modular components
from src.config import AppConfig
from src.models import MemoryManager, ProgressiveFileManager, ProgressTracker
from src.routes import api_bp, main_bp, register_socket_handlers
from src.routes.api import init_api_globals
from src.routes.socket_handlers import init_socket_globals
from src.services import VideoTranscriber, delete_session, process_upload
from src.utils import handle_user_friendly_error


def configure_logging() -> logging.Logger:
    """Configure application logging with appropriate format and level."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def create_app() -> Tuple[Flask, SocketIO]:
    """
    Create and configure the Flask application.

    Returns:
        Tuple[Flask, SocketIO]: Configured Flask app and SocketIO instance
    """
    config = AppConfig()

    # Create Flask app with proper template folder
    app = Flask(__name__, template_folder="data/templates")

    # Configure Flask app
    app.config.update(
        {
            "MAX_CONTENT_LENGTH": config.MAX_FILE_SIZE_BYTES,
            "UPLOAD_FOLDER": config.UPLOAD_FOLDER,
            "RESULTS_FOLDER": config.RESULTS_FOLDER,
            "SECRET_KEY": config.SECRET_KEY,
            "DEBUG": False,  # Should be controlled by environment
        }
    )

    # Initialize SocketIO with security considerations
    cors_origins = AppConfig.get_cors_origins()
    logging.info(f"Configuring CORS for origins: {cors_origins}")

    socketio = SocketIO(
        app,
        cors_allowed_origins=cors_origins,
        logger=False,  # Disable socketio logging to reduce noise
        engineio_logger=False,
    )

    return app, socketio


def ensure_directories(config: AppConfig) -> None:
    """
    Ensure required directories exist.

    Args:
        config: Application configuration instance
    """
    directories = [config.UPLOAD_FOLDER, config.RESULTS_FOLDER]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def initialize_managers(
    socketio: SocketIO,
) -> Tuple[MemoryManager, ProgressiveFileManager, ProgressTracker]:
    """
    Initialize and configure manager instances.

    Args:
        socketio: SocketIO instance for progress tracking

    Returns:
        Tuple of manager instances
    """
    memory_manager = MemoryManager()
    file_manager = ProgressiveFileManager()
    progress_tracker = ProgressTracker(socketio)

    return memory_manager, file_manager, progress_tracker


def create_transcriber(
    memory_manager: MemoryManager,
    file_manager: ProgressiveFileManager,
    progress_tracker: ProgressTracker,
    results_folder: str,
) -> VideoTranscriber:
    """
    Create and configure the video transcriber service.

    Args:
        memory_manager: Memory management instance
        file_manager: File management instance
        progress_tracker: Progress tracking instance
        results_folder: Path to results directory

    Returns:
        Configured VideoTranscriber instance
    """
    return VideoTranscriber(
        memory_manager=memory_manager,
        file_manager=file_manager,
        progress_tracker=progress_tracker,
        results_folder=results_folder,
    )


def register_routes(
    app: Flask,
    socketio: SocketIO,
    transcriber: VideoTranscriber,
    memory_manager: MemoryManager,
    file_manager: ProgressiveFileManager,
    progress_tracker: ProgressTracker,
    config: AppConfig,
) -> None:
    """
    Register all application routes and handlers.

    Args:
        app: Flask application instance
        socketio: SocketIO instance
        transcriber: Video transcriber service
        memory_manager: Memory management instance
        file_manager: File management instance
        progress_tracker: Progress tracking instance
        config: Application configuration
    """
    # Initialize route globals
    init_api_globals(memory_manager, file_manager, progress_tracker)
    init_socket_globals(progress_tracker)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    # Register socket handlers
    register_socket_handlers(socketio)

    # Register additional routes
    register_upload_route(app, transcriber, memory_manager, config)
    register_session_routes(app, config)


def register_upload_route(
    app: Flask,
    transcriber: VideoTranscriber,
    memory_manager: MemoryManager,
    config: AppConfig,
) -> None:
    """
    Register the upload route with proper error handling.

    Args:
        app: Flask application instance
        transcriber: Video transcriber service
        memory_manager: Memory management instance
        config: Application configuration
    """

    @app.route("/upload", methods=["POST"])
    @handle_user_friendly_error
    def upload() -> Tuple[Dict[str, Any], int]:
        """
        Upload endpoint for video processing.

        Returns:
            Tuple of response data and HTTP status code
        """
        logger = logging.getLogger(__name__)
        try:
            response_data, status_code = process_upload(
                transcriber, memory_manager, config.UPLOAD_FOLDER
            )
            return response_data, status_code
        except Exception as e:
            logger.error(f"Upload processing error: {e}", exc_info=True)
            return {"success": False, "error": "Internal server error"}, 500


def register_session_routes(app: Flask, config: AppConfig) -> None:
    """
    Register session management routes.

    Args:
        app: Flask application instance
        config: Application configuration
    """

    @app.route("/sessions/delete/<session_id>", methods=["POST"])
    def delete_session_endpoint(session_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Delete session endpoint.

        Args:
            session_id: ID of session to delete

        Returns:
            Tuple of response data and HTTP status code
        """
        response_data, status_code = delete_session(session_id, config.RESULTS_FOLDER)
        return response_data, status_code


def main() -> None:
    """Main application entry point."""
    logger = configure_logging()

    try:
        # Configuration
        config = AppConfig()

        # Create application
        app, socketio = create_app()

        # Ensure directories exist
        ensure_directories(config)

        # Initialize managers
        memory_manager, file_manager, progress_tracker = initialize_managers(socketio)

        # Create transcriber
        transcriber = create_transcriber(
            memory_manager, file_manager, progress_tracker, config.RESULTS_FOLDER
        )

        # Register routes
        register_routes(
            app,
            socketio,
            transcriber,
            memory_manager,
            file_manager,
            progress_tracker,
            config,
        )

        # Start application
        logger.info("Starting modularized video transcriber application...")
        logger.info(f"Access the application at: http://localhost:5001")

        socketio.run(
            app,
            debug=False,  # Should be controlled by environment
            host="0.0.0.0",
            port=5001,
            use_reloader=False,  # Disable reloader in production
        )

    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
