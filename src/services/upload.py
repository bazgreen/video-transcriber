"""Upload processing service."""

import logging
import os
import re
import shutil
from typing import Any, Dict, Tuple

from flask import request
from werkzeug.utils import secure_filename

from src.config.settings import AppConfig, Constants
from src.models.exceptions import UserFriendlyError
from src.routes.auth import associate_session_with_user, get_current_user_id
from src.utils import is_valid_session_id
from src.utils.security import log_access_attempt

logger = logging.getLogger(__name__)
config = AppConfig()


def process_upload(
    transcriber, memory_manager, upload_folder: str
) -> Tuple[Dict[str, Any], int]:
    """Process uploaded video file for transcription"""

    # Validate file upload
    if "video" not in request.files:
        raise UserFriendlyError("No file uploaded")

    file = request.files["video"]
    if file.filename == "":
        raise UserFriendlyError("No file selected")

    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in config.ALLOWED_FILE_EXTENSIONS:
        raise UserFriendlyError(
            f"Unsupported format: {file_ext}. "
            f"Supported formats: {list(config.ALLOWED_FILE_EXTENSIONS)}"
        )

    # Enhanced file size validation with context
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer

    file_size_mb = file_size / Constants.BYTES_PER_MB
    if file_size > config.MAX_FILE_SIZE_BYTES:
        max_size_mb = config.MAX_FILE_SIZE_BYTES / Constants.BYTES_PER_MB
        raise UserFriendlyError(
            f"File too large: {file_size_mb:.1f}MB. "
            f"Maximum allowed: {max_size_mb:.0f}MB"
        )

    # Check available memory before processing
    memory_info = memory_manager.get_memory_info()
    if memory_info["system_used_percent"] > config.MEMORY_PRESSURE_THRESHOLD:
        raise UserFriendlyError(
            f'Insufficient memory: {memory_info["system_used_percent"]:.1f}% used, '
            f'{memory_info["system_available_gb"]:.1f}GB available'
        )

    session_name = request.form.get("session_name", "").strip()

    # Provide default session name if empty
    if not session_name:
        session_name = "video_transcription"

    # Remove potentially problematic characters (allow more characters)
    session_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", session_name)
    # Limit length
    session_name = session_name[: config.MAX_SESSION_NAME_LENGTH]

    # Ensure session name is not empty after cleaning
    if not session_name:
        session_name = "video_transcription"

    # Check if a keyword scenario was selected
    scenario_id = request.form.get("keyword_scenario", "").strip()
    if scenario_id:
        # We'll pass the scenario_id to the transcriber to apply the keywords
        logger.info(f"Using keyword scenario: {scenario_id}")

    # Save uploaded file
    filename = secure_filename(file.filename)
    upload_path = os.path.join(upload_folder, filename)

    try:
        file.save(upload_path)
    except IOError:
        raise UserFriendlyError("Storage full - unable to save file")

    try:
        # Process video
        results = transcriber.process_video(
            upload_path,
            session_name,
            file.filename,
            keyword_scenario_id=scenario_id if scenario_id else None,
        )

        # Associate session with current user (if authenticated)
        session_id = results["session_id"]
        try:
            associate_session_with_user(session_id, session_name)
            log_access_attempt(session_id, "create", True)
        except Exception as e:
            logger.warning(f"Failed to associate session {session_id} with user: {e}")

        # Copy original video file to session directory for synchronized playback
        session_dir = results.get("session_dir")
        if session_dir:
            # Ensure session directory exists
            os.makedirs(session_dir, exist_ok=True)

            if os.path.exists(session_dir):
                # Use a standardized filename for easier retrieval
                video_filename = f"original_video_{secure_filename(file.filename)}"
                video_destination = os.path.join(session_dir, video_filename)

                try:
                    shutil.copy2(upload_path, video_destination)
                    logger.info(
                        f"Copied original video to session: {video_destination}"
                    )

                    # Verify the copy was successful
                    if not os.path.exists(video_destination):
                        logger.error(
                            f"Video copy verification failed: {video_destination}"
                        )
                    else:
                        logger.info(
                            f"Video copy verified successfully: {video_destination}"
                        )

                except (IOError, OSError) as copy_error:
                    logger.error(
                        f"Could not copy video to session directory: {copy_error}"
                    )
                    # Still don't fail the entire process if copy fails
            else:
                logger.error(f"Session directory does not exist: {session_dir}")

        response_data = {
            "success": True,
            "session_id": results["session_id"],
            "message": "Video processed successfully!",
            "stats": {
                "chunks": len(results.get("chunks", [])),
                "words": results.get("analysis", {}).get("total_words", 0),
                "duration": results.get("metadata", {}).get("processing_time", 0),
            },
        }
        return response_data, 200

    except UserFriendlyError:
        raise  # Re-raise user-friendly errors
    except Exception as e:
        logger.error(f"Upload processing error: {str(e)}")
        raise UserFriendlyError(f"Processing failed: {str(e)}")

    finally:
        # Clean up uploaded file
        if os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except OSError:
                logger.warning(f"Could not remove uploaded file: {upload_path}")


def delete_session(session_id: str, results_folder: str) -> Tuple[Dict[str, Any], int]:
    """Delete a transcription session"""
    # Validate session_id to prevent path traversal
    if not is_valid_session_id(session_id):
        return {
            "success": False,
            "error": "Invalid session ID format",
            "error_type": "validation_error",
        }, 400

    session_dir = os.path.join(results_folder, session_id)

    # Ensure the path is within the results folder
    if not os.path.abspath(session_dir).startswith(os.path.abspath(results_folder)):
        return {
            "success": False,
            "error": "Access denied: Invalid session path",
            "error_type": "security_error",
        }, 403

    if not os.path.exists(session_dir):
        return {
            "success": False,
            "error": f'Session "{session_id}" not found',
            "error_type": "not_found_error",
        }, 404

    try:
        shutil.rmtree(session_dir)
        logger.info(f"Successfully deleted session {session_id}")
        return {
            "success": True,
            "message": f'Session "{session_id}" deleted successfully',
        }, 200
    except PermissionError as e:
        logger.error(f"Permission error deleting session {session_id}: {e}")
        return {
            "success": False,
            "error": "Insufficient permissions to delete session",
            "error_type": "permission_error",
        }, 500
    except Exception as e:
        logger.error(
            f"Unexpected error deleting session {session_id}: {e}", exc_info=True
        )
        return {
            "success": False,
            "error": "Failed to delete session due to internal error",
            "error_type": "server_error",
        }, 500
