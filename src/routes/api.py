"""
API routes for the video transcriber application.

This module provides RESTful API endpoints for configuration management,
performance monitoring, and system status information.
"""

import glob
import json
import logging
import multiprocessing
import os
import time
from datetime import datetime
from typing import Any, Optional

from flask import Blueprint, Response, jsonify, request, send_file

from src.config import AppConfig, Constants, PerformanceConfig, VideoConfig
from src.models.exceptions import UserFriendlyError
from src.utils import (
    handle_user_friendly_error,
    is_safe_path,
    is_valid_session_id,
    load_keywords,
    load_session_metadata,
    save_keywords,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)

# Global references (will be injected from main app)
memory_manager: Optional[Any] = None
file_manager: Optional[Any] = None
progress_tracker: Optional[Any] = None


def init_api_globals(mm: Any, fm: Any, pt: Any) -> None:
    """
    Initialize global references for API routes.

    This function is called during application initialization to inject
    dependencies that API routes need to access.

    Args:
        mm: MemoryManager instance for system monitoring
        fm: FileManager instance for file cleanup operations
        pt: ProgressTracker instance for session progress
    """
    global memory_manager, file_manager, progress_tracker
    memory_manager = mm
    file_manager = fm
    progress_tracker = pt


@api_bp.route("/keywords", methods=["GET"])
@handle_user_friendly_error
def get_keywords() -> Response:
    """
    Get current keywords list for content analysis.

    Returns:
        JSON response with current keywords list

    Response Format:
        {
            "success": true,
            "keywords": ["keyword1", "keyword2", ...]
        }
    """
    keywords = load_keywords()
    return jsonify({"success": True, "keywords": keywords})


@api_bp.route("/keywords", methods=["POST"])
@handle_user_friendly_error
def update_keywords() -> Response:
    """
    Update the entire keywords list for content analysis.

    Request Body:
        {
            "keywords": ["new_keyword1", "new_keyword2", ...]
        }

    Returns:
        JSON response with updated keywords list

    Raises:
        UserFriendlyError: If request format is invalid
    """
    data = request.get_json()
    if not data or "keywords" not in data:
        raise UserFriendlyError("Invalid request: 'keywords' field is required")

    keywords = data["keywords"]
    if not isinstance(keywords, list):
        raise UserFriendlyError("Keywords must be a list")

    # Validate keywords
    valid_keywords = []
    for keyword in keywords:
        if isinstance(keyword, str) and keyword.strip():
            valid_keywords.append(keyword.strip())

    save_keywords(valid_keywords)
    logger.info(f"Updated keywords list with {len(valid_keywords)} items")

    return jsonify(
        {
            "success": True,
            "message": f"Updated {len(valid_keywords)} keywords",
            "keywords": valid_keywords,
        }
    )


@api_bp.route("/keywords/add", methods=["POST"])
@handle_user_friendly_error
def add_keyword():
    """Add a new keyword"""
    data = request.get_json()
    if not data or "keyword" not in data:
        raise UserFriendlyError("Invalid request: 'keyword' field is required")

    new_keyword = data["keyword"].strip()
    if not new_keyword:
        raise UserFriendlyError("Keyword cannot be empty")

    keywords = load_keywords()
    if new_keyword not in keywords:
        keywords.append(new_keyword)
        save_keywords(keywords)
        logger.info(f"Added new keyword: {new_keyword}")
        return jsonify(
            {
                "success": True,
                "message": f"Added keyword: {new_keyword}",
                "keywords": keywords,
            }
        )
    else:
        return jsonify(
            {
                "success": True,
                "message": f"Keyword already exists: {new_keyword}",
                "keywords": keywords,
            }
        )


@api_bp.route("/keywords/remove", methods=["POST"])
@handle_user_friendly_error
def remove_keyword():
    """Remove a keyword"""
    data = request.get_json()
    if not data or "keyword" not in data:
        raise UserFriendlyError("Invalid request: 'keyword' field is required")

    keyword_to_remove = data["keyword"].strip()
    keywords = load_keywords()

    if keyword_to_remove in keywords:
        keywords.remove(keyword_to_remove)
        save_keywords(keywords)
        logger.info(f"Removed keyword: {keyword_to_remove}")
        return jsonify(
            {
                "success": True,
                "message": f"Removed keyword: {keyword_to_remove}",
                "keywords": keywords,
            }
        )
    else:
        raise UserFriendlyError(f"Keyword not found: {keyword_to_remove}")


@api_bp.route("/performance", methods=["GET"])
@handle_user_friendly_error
def get_performance_settings():
    """Get current performance settings and system information"""
    optimal_workers = (
        memory_manager.get_optimal_workers()
        if memory_manager
        else PerformanceConfig.DEFAULT_MAX_WORKERS
    )
    memory_info = memory_manager.get_memory_info() if memory_manager else {}

    # Get system information in the format expected by the frontend
    system_info = {
        "cpu_count": multiprocessing.cpu_count(),
        "memory_total_gb": memory_info.get("system_total_gb", 0),
        "memory_available_gb": memory_info.get("system_available_gb", 0),
        "memory_used_percent": memory_info.get("system_used_percent", 0),
        "process_memory_mb": memory_info.get("process_rss_mb", 0),
    }

    current_settings = {
        "chunk_duration": getattr(PerformanceConfig, "current_chunk_duration", 300),
        "max_workers": getattr(
            PerformanceConfig, "current_max_workers", optimal_workers
        ),
        "optimal_workers": optimal_workers,
    }

    # Generate basic recommendations
    recommendations = []
    if memory_info.get("system_used_percent", 0) > 85:
        recommendations.append(
            "High memory usage detected - consider reducing max workers"
        )

    if optimal_workers < multiprocessing.cpu_count():
        recommendations.append(
            f"Memory limits optimal workers to {optimal_workers} (CPU cores: {multiprocessing.cpu_count()})"
        )

    # Structure the response to match what the frontend expects
    response_data = {
        "system_info": system_info,
        "current_settings": current_settings,
        "recommendations": recommendations,
        "limits": {
            "min_workers": PerformanceConfig.MIN_WORKERS,
            "max_workers_limit": PerformanceConfig.MAX_WORKERS_LIMIT,
            "min_chunk_duration": VideoConfig.MIN_CHUNK_DURATION_SECONDS,
            "max_chunk_duration": VideoConfig.MAX_CHUNK_DURATION_SECONDS,
        },
    }

    return jsonify({"success": True, "data": response_data})


@api_bp.route("/performance", methods=["POST"])
@handle_user_friendly_error
def update_performance_settings():
    """Update performance settings"""
    data = request.get_json()
    if not data:
        raise UserFriendlyError("Invalid request: JSON data is required")

    # Validate and update chunk duration
    if "chunk_duration" in data:
        chunk_duration = data["chunk_duration"]
        if (
            not isinstance(chunk_duration, (int, float))
            or chunk_duration < VideoConfig.MIN_CHUNK_DURATION_SECONDS
            or chunk_duration > VideoConfig.MAX_CHUNK_DURATION_SECONDS
        ):
            raise UserFriendlyError(
                f"Chunk duration must be between "
                f"{VideoConfig.MIN_CHUNK_DURATION_SECONDS} and "
                f"{VideoConfig.MAX_CHUNK_DURATION_SECONDS} seconds, "
                f"got: {chunk_duration}"
            )
        PerformanceConfig.current_chunk_duration = int(chunk_duration)

    # Validate and update max workers
    if "max_workers" in data:
        max_workers = data["max_workers"]
        if (
            not isinstance(max_workers, int)
            or max_workers < PerformanceConfig.MIN_WORKERS
            or max_workers > PerformanceConfig.MAX_WORKERS_LIMIT
        ):
            raise UserFriendlyError(
                f"Max workers must be between {PerformanceConfig.MIN_WORKERS} "
                f"and {PerformanceConfig.MAX_WORKERS_LIMIT}, got: {max_workers}"
            )
        PerformanceConfig.current_max_workers = max_workers

    chunk_duration_val = getattr(
        PerformanceConfig, "current_chunk_duration", "unchanged"
    )
    max_workers_val = getattr(PerformanceConfig, "current_max_workers", "unchanged")
    logger.info(
        f"Updated performance settings: "
        f"chunk_duration={chunk_duration_val}, max_workers={max_workers_val}"
    )

    return jsonify(
        {
            "success": True,
            "message": "Performance settings updated successfully",
            "settings": {
                "chunk_duration": getattr(
                    PerformanceConfig, "current_chunk_duration", 300
                ),
                "max_workers": getattr(
                    PerformanceConfig,
                    "current_max_workers",
                    PerformanceConfig.DEFAULT_MAX_WORKERS,
                ),
            },
        }
    )


@api_bp.route("/memory", methods=["GET"])
@handle_user_friendly_error
def get_memory_status():
    """Get current memory status and recommendations"""
    if not memory_manager:
        return jsonify({"success": False, "error": "Memory manager not available"}), 503

    memory_info = memory_manager.get_memory_info()
    optimal_workers = memory_manager.get_optimal_workers()
    memory_pressure = memory_manager.check_memory_pressure()

    # Generate recommendations
    recommendations = []
    if memory_pressure:
        recommendations.append(
            "System is under memory pressure - consider reducing max workers"
        )

    if memory_info["system_available_gb"] < 2:
        recommendations.append("Low available memory - processing may be slower")

    if optimal_workers < multiprocessing.cpu_count():
        recommendations.append(
            f"Memory limits optimal workers to {optimal_workers} "
            f"(CPU cores: {multiprocessing.cpu_count()})"
        )

    return jsonify(
        {
            "success": True,
            "memory_info": memory_info,
            "optimal_workers": optimal_workers,
            "memory_pressure": memory_pressure,
            "recommendations": recommendations,
            "temp_files": file_manager.get_cleanup_stats() if file_manager else {},
        }
    )


@api_bp.route("/performance/live", methods=["GET"])
@handle_user_friendly_error
def get_live_performance():
    """Get live performance data"""
    if not memory_manager:
        return jsonify({"success": False, "error": "Memory manager not available"}), 503

    memory_info = memory_manager.get_memory_info()

    # Get active sessions info
    active_sessions_info = []
    if progress_tracker:
        for session_id, session_data in progress_tracker.sessions.items():
            active_sessions_info.append(
                {
                    "session_id": session_id,
                    "progress": session_data.get("progress", 0),
                    "stage": session_data.get("stage", "unknown"),
                    "current_task": session_data.get("current_task", ""),
                    "chunks_completed": session_data.get("chunks_completed", 0),
                    "chunks_total": session_data.get("chunks_total", 0),
                    "elapsed_time": (
                        time.time() - session_data.get("start_time", time.time())
                    ),
                }
            )

    live_data = {
        "timestamp": time.time(),
        "memory": {
            "system_used_percent": memory_info["system_used_percent"],
            "system_available_gb": memory_info["system_available_gb"],
            "process_rss_mb": memory_info["process_rss_mb"],
        },
        "active_sessions": active_sessions_info,
        "temp_files": file_manager.get_cleanup_stats() if file_manager else {},
        "system_load": {
            "cpu_count": multiprocessing.cpu_count(),
            "optimal_workers": memory_manager.get_optimal_workers(),
            "memory_pressure": memory_manager.check_memory_pressure(),
        },
    }

    return jsonify({"success": True, "data": live_data})


@api_bp.route("/performance/history", methods=["GET"])
@handle_user_friendly_error
def get_performance_history():
    """Get performance history (placeholder for future implementation)"""
    # This would require a database or persistent storage to track performance over time
    return jsonify(
        {
            "success": True,
            "message": "Performance history tracking not yet implemented",
            "data": [],
        }
    )


@api_bp.route("/performance/optimization", methods=["GET"])
def get_performance_optimization():
    """Get performance optimization recommendations and current settings"""
    try:
        from src.utils.performance_optimizer import performance_optimizer

        # Get current system recommendations
        recommendations = performance_optimizer.get_performance_recommendations()

        # Get performance summary
        summary = performance_optimizer.get_performance_summary()

        # Get current configuration
        current_config = {
            "max_file_size_mb": (
                AppConfig.MAX_FILE_SIZE_BYTES / Constants.BYTES_PER_MB
            ),
            "chunk_upload_size_mb": (
                getattr(AppConfig, "CHUNK_UPLOAD_SIZE", 50 * 1024 * 1024)
                / Constants.BYTES_PER_MB
            ),
            "min_workers": PerformanceConfig.MIN_WORKERS,
            "max_workers_limit": PerformanceConfig.MAX_WORKERS_LIMIT,
            "default_max_workers": PerformanceConfig.DEFAULT_MAX_WORKERS,
            "memory_safety_factor": getattr(
                PerformanceConfig, "MEMORY_SAFETY_FACTOR", 0.8
            ),
            "high_memory_threshold_gb": getattr(
                PerformanceConfig, "HIGH_MEMORY_THRESHOLD_GB", 8
            ),
            "parallel_upload_enabled": getattr(
                PerformanceConfig, "ENABLE_PARALLEL_UPLOAD", True
            ),
            "memory_cleanup_enabled": getattr(
                PerformanceConfig, "ENABLE_MEMORY_CLEANUP", True
            ),
            "chunk_size_optimization": getattr(
                PerformanceConfig, "CHUNK_SIZE_OPTIMIZATION", True
            ),
        }

        return jsonify(
            {
                "status": "success",
                "recommendations": recommendations,
                "performance_summary": summary,
                "current_configuration": current_config,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting performance optimization data: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/performance/optimize", methods=["POST"])
def optimize_performance():
    """Apply performance optimizations based on current system state"""
    try:
        from src.utils.performance_optimizer import performance_optimizer

        data = request.get_json() or {}
        force_memory_cleanup = data.get("force_memory_cleanup", False)

        # Perform memory optimization
        memory_result = performance_optimizer.optimize_memory_usage(
            force=force_memory_cleanup
        )

        # Get updated recommendations
        recommendations = performance_optimizer.get_performance_recommendations()

        # Get optimal settings for current state
        optimal_workers = performance_optimizer.get_optimal_worker_count()

        return jsonify(
            {
                "status": "success",
                "message": "Performance optimization completed",
                "memory_optimization": memory_result,
                "recommendations": recommendations,
                "optimal_workers": optimal_workers,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error during performance optimization: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/export/formats", methods=["GET"])
@handle_user_friendly_error
def get_export_formats():
    """Get available export formats and their descriptions"""
    try:
        from src.services.export import EnhancedExportService

        export_service = EnhancedExportService()
        available_formats = export_service.get_available_formats()
        format_descriptions = export_service.get_format_descriptions()

        return jsonify(
            {
                "success": True,
                "formats": {
                    format_name: {
                        "available": available,
                        "description": format_descriptions.get(format_name, ""),
                    }
                    for format_name, available in available_formats.items()
                },
            }
        )
    except Exception as e:
        logger.error(f"Error getting export formats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/export/<session_id>/<export_format>", methods=["GET"])
@handle_user_friendly_error
def download_export_format(session_id: str, export_format: str):
    """Download a specific export format for a session"""

    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID")

    config = AppConfig()
    session_path = os.path.join(config.RESULTS_FOLDER, session_id)

    if not os.path.exists(session_path):
        raise UserFriendlyError(f"Session '{session_id}' not found")

    # Map export formats to filenames
    format_filenames = {
        "srt": "subtitles.srt",
        "vtt": "subtitles.vtt",
        "pdf": "analysis_report.pdf",
        "docx": "transcript_report.docx",
        "enhanced_txt": "transcript_enhanced.txt",
        "basic_txt": "transcript.txt",
        "json": "analysis.json",
        "html": "searchable_transcript.html",
    }

    if export_format not in format_filenames:
        raise UserFriendlyError(f"Unsupported export format: {export_format}")

    filename = format_filenames[export_format]
    file_path = os.path.join(session_path, filename)

    if not is_safe_path(file_path, config.RESULTS_FOLDER):
        raise UserFriendlyError("Invalid file path")

    if not os.path.exists(file_path):
        raise UserFriendlyError(
            f"File not found: {filename}. This format may not have been "
            f"generated for this session."
        )

    return send_file(file_path, as_attachment=True)


@api_bp.route("/export/<session_id>/generate", methods=["POST"])
@handle_user_friendly_error
def generate_export_formats(session_id: str):
    """Generate export formats for a session"""

    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID")

    config = AppConfig()
    session_path = os.path.join(config.RESULTS_FOLDER, session_id)

    if not os.path.exists(session_path):
        raise UserFriendlyError(f"Session '{session_id}' not found")

    # Load session results
    try:
        metadata = load_session_metadata(session_id, session_path)

        # Load analysis data
        analysis_file = os.path.join(session_path, "analysis.json")
        if os.path.exists(analysis_file):
            import json

            with open(analysis_file, "r", encoding="utf-8") as f:
                analysis = json.load(f)
        else:
            analysis = {}

        # Load full transcript
        transcript_file = os.path.join(session_path, "full_transcript.txt")
        full_transcript = ""
        if os.path.exists(transcript_file):
            with open(transcript_file, "r", encoding="utf-8") as f:
                full_transcript = f.read()

        # Prepare results dictionary
        results = {
            "session_id": session_id,
            "session_dir": session_path,
            "metadata": metadata,
            "analysis": analysis,
            "full_transcript": full_transcript,
        }

        # Get export options from request
        data = request.get_json() or {}
        export_options = data.get(
            "formats",
            {
                "srt": True,
                "vtt": True,
                "pdf": True,
                "docx": True,
                "enhanced_txt": True,
            },
        )

        # Generate exports
        from src.services.export import EnhancedExportService

        export_service = EnhancedExportService()
        exported_files = export_service.export_all_formats(results, export_options)

        return jsonify(
            {
                "success": True,
                "message": f"Generated {len(exported_files)} export formats",
                "exported_files": exported_files,
            }
        )

    except Exception as e:
        logger.error(f"Error generating export formats for session {session_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# =============================================================================
# Video Serving Infrastructure - Phase 1 Implementation
# =============================================================================


@api_bp.route("/video/<session_id>", methods=["GET"])
@handle_user_friendly_error
def serve_video(session_id: str) -> Response:
    """
    Serve original video file for synchronized playback.

    Provides secure video file serving with range request support for seeking.

    Args:
        session_id: Session identifier

    Returns:
        Video file response with appropriate headers for streaming

    Raises:
        UserFriendlyError: If session or video file not found
    """
    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID format")

    session_dir = os.path.join(AppConfig.RESULTS_FOLDER, session_id)

    # Check if session exists
    if not os.path.exists(session_dir):
        raise UserFriendlyError("Session not found")

    # Load session metadata to find original filename
    metadata_path = os.path.join(session_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        raise UserFriendlyError("Session metadata not found")

    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading metadata for session {session_id}: {e}")
        raise UserFriendlyError("Error reading session metadata")

    # Find video file in session directory
    video_file_path = _find_video_file(session_dir, metadata)

    # Security check - ensure file is within session directory
    if not is_safe_path(video_file_path, session_dir):
        raise UserFriendlyError("Invalid file path")

    # Determine MIME type
    mime_type = _get_video_mime_type(video_file_path)

    try:
        return send_file(
            video_file_path,
            as_attachment=False,
            mimetype=mime_type,
            conditional=True,  # Enable range requests for seeking
        )
    except Exception as e:
        logger.error(f"Error serving video file {video_file_path}: {e}")
        raise UserFriendlyError("Error serving video file")


@api_bp.route("/video/<session_id>/metadata", methods=["GET"])
@handle_user_friendly_error
def get_video_metadata(session_id: str) -> Response:
    """
    Get video metadata for player initialization.

    Returns structured data including chapters, keywords, and timeline markers
    for the synchronized video player.

    Args:
        session_id: Session identifier

    Returns:
        JSON response with video metadata and chapter information

    Raises:
        UserFriendlyError: If session or analysis data not found
    """
    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID format")

    session_dir = os.path.join(AppConfig.RESULTS_FOLDER, session_id)

    # Check if session exists
    if not os.path.exists(session_dir):
        raise UserFriendlyError("Session not found")

    # Load analysis data
    analysis_path = os.path.join(session_dir, "analysis.json")
    if not os.path.exists(analysis_path):
        raise UserFriendlyError("Analysis data not found")

    try:
        with open(analysis_path, "r") as f:
            analysis = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading analysis for session {session_id}: {e}")
        raise UserFriendlyError("Error reading analysis data")

    # Load session metadata for additional info
    metadata_path = os.path.join(session_dir, "metadata.json")
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load metadata for session {session_id}: {e}")

    # Generate chapter markers from content analysis
    chapters = generate_video_chapters(analysis)

    return jsonify(
        {
            "success": True,
            "session_id": session_id,
            "chapters": chapters,
            "total_duration": _calculate_total_duration(analysis),
            "segments_count": len(analysis.get("segments", [])),
            "keywords": analysis.get("keyword_matches", []),
            "questions": analysis.get("questions", []),
            "emphasis_cues": analysis.get("emphasis_cues", []),
            "metadata": {
                "original_filename": metadata.get("original_filename", ""),
                "session_name": metadata.get("session_name", ""),
                "created_at": metadata.get("created_at", ""),
                "total_words": metadata.get("total_words", 0),
            },
        }
    )


# =============================================================================
# Video Utility Functions
# =============================================================================


def _find_video_file(session_dir: str, metadata: dict) -> str:
    """
    Find the video file in the session directory.

    Args:
        session_dir: Path to session directory
        metadata: Session metadata dictionary

    Returns:
        Path to the video file

    Raises:
        UserFriendlyError: If no video file is found
    """
    # Look for video file by original name pattern
    video_extensions = ["mp4", "avi", "mov", "mkv", "webm", "flv", "wmv", "m4v"]

    # Try to find video files in session directory
    video_files = []
    for ext in video_extensions:
        # Check both lowercase and uppercase extensions
        for case_ext in [ext.lower(), ext.upper()]:
            pattern = os.path.join(session_dir, f"*.{case_ext}")
            video_files.extend(glob.glob(pattern))

    if not video_files:
        raise UserFriendlyError("Video file not found in session")

    # Return the first found video file
    # In a production system, we might want more sophisticated matching
    return video_files[0]


def _get_video_mime_type(file_path: str) -> str:
    """
    Determine MIME type for video file based on extension.

    Args:
        file_path: Path to video file

    Returns:
        MIME type string
    """
    ext = os.path.splitext(file_path)[1].lower()

    mime_types = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".flv": "video/x-flv",
        ".wmv": "video/x-ms-wmv",
        ".m4v": "video/mp4",
    }

    return mime_types.get(ext, "video/mp4")  # Default to mp4


def _calculate_total_duration(analysis: dict) -> float:
    """
    Calculate total video duration from analysis data.

    Args:
        analysis: Analysis data dictionary

    Returns:
        Total duration in seconds
    """
    # Try to find duration from questions (most reliable)
    questions = analysis.get("questions", [])
    if questions:
        max_time = 0.0
        for question in questions:
            try:
                start_time = float(question.get("start", 0))
                max_time = max(max_time, start_time)
            except (ValueError, TypeError):
                continue
        return max_time + 60  # Add buffer for content after last question

    # Try emphasis cues as fallback
    emphasis_cues = analysis.get("emphasis_cues", [])
    if emphasis_cues:
        max_time = 0.0
        for cue in emphasis_cues:
            try:
                start_time = float(cue.get("start", 0))
                max_time = max(max_time, start_time)
            except (ValueError, TypeError):
                continue
        return max_time + 60

    # Default fallback
    return 3600.0  # 1 hour default


def _calculate_total_duration_from_questions(questions: list) -> float:
    """Calculate duration from questions list."""
    if not questions:
        return 0.0

    max_time = 0.0
    for question in questions:
        try:
            start_time = float(question.get("start", 0))
            max_time = max(max_time, start_time)
        except (ValueError, TypeError):
            continue

    return max_time + 60  # Add buffer


def generate_chapter_title_from_question(question: dict, chapter_number: int) -> str:
    """
    Generate chapter title from a question.

    Args:
        question: Question dictionary with text and timing
        chapter_number: Chapter sequence number

    Returns:
        Generated chapter title string
    """
    question_text = question.get("text", "").strip()

    if question_text:
        # Clean and truncate question for title
        clean_question = question_text.replace("?", "").strip()
        if len(clean_question) > 50:
            clean_question = clean_question[:47] + "..."
        return f"Q: {clean_question}?"

    # Fallback to timestamp-based title
    start_time = float(question.get("start", 0))
    minutes = int(start_time // 60)
    seconds = int(start_time % 60)
    return f"Chapter {chapter_number} ({minutes:02d}:{seconds:02d})"


def _is_major_topic_shift(current_question: dict, previous_question: dict) -> bool:
    """
    Detect if there's a major topic shift between questions.

    Args:
        current_question: Current question dict
        previous_question: Previous question dict

    Returns:
        True if major topic shift detected
    """
    if not previous_question:
        return False

    current_text = current_question.get("text", "").lower()

    # Simple heuristic: look for topic change indicators
    topic_change_indicators = [
        "let's move on",
        "next topic",
        "moving on",
        "another thing",
        "different question",
        "now let's talk about",
        "switching to",
    ]

    return any(indicator in current_text for indicator in topic_change_indicators)


def generate_video_chapters(analysis_data: dict) -> list:
    """
    Generate chapter markers from content analysis.

    Creates intelligent chapter divisions based on content analysis including
    questions, keyword clusters, and natural content breaks.

    Args:
        analysis_data: Complete analysis dictionary from session

    Returns:
        List of chapter dictionaries with time, title, and metadata
    """
    chapters = []

    # Get questions as the primary source for chapters
    questions = analysis_data.get("questions", [])

    if not questions:
        # Fallback: create basic time-based chapters if no questions
        total_duration = _calculate_total_duration_from_questions(questions)
        if total_duration > 0:
            chapter_interval = 300  # 5 minutes
            chapter_count = 1
            for start_time in range(0, int(total_duration), chapter_interval):
                chapters.append(
                    {
                        "time": start_time,
                        "title": f"Chapter {chapter_count}",
                        "keywords": [],
                        "chapter_number": chapter_count,
                    }
                )
                chapter_count += 1
        return chapters

    # Sort questions by timestamp for chapter creation
    sorted_questions = sorted(questions, key=lambda q: q.get("start", 0))

    # Configuration for intelligent chapter breaks
    chapter_interval = 300  # 5 minutes minimum between chapters
    last_chapter_time = 0
    chapter_count = 1

    for i, question in enumerate(sorted_questions):
        try:
            question_start = float(question.get("start", 0))
        except (ValueError, TypeError):
            continue

        # Check if we should create a chapter at this question
        should_create_chapter = (
            # Time-based: at least 5 minutes since last chapter
            question_start - last_chapter_time >= chapter_interval
            or
            # First question always creates a chapter
            i == 0
            or
            # Major topic change detection (simple heuristic)
            _is_major_topic_shift(question, sorted_questions[i - 1] if i > 0 else None)
        )

        if should_create_chapter:
            # Generate chapter title from question
            title = generate_chapter_title_from_question(question, chapter_count)

            # Get nearby keywords for this chapter
            nearby_keywords = get_nearby_keywords(question_start, analysis_data)

            chapters.append(
                {
                    "time": question_start,
                    "title": title,
                    "keywords": nearby_keywords,
                    "chapter_number": chapter_count,
                }
            )

            last_chapter_time = question_start
            chapter_count += 1

    # Ensure we have at least one chapter
    if not chapters and sorted_questions:
        first_question = sorted_questions[0]
        chapters.append(
            {
                "time": float(first_question.get("start", 0)),
                "title": generate_chapter_title_from_question(first_question, 1),
                "keywords": get_nearby_keywords(
                    float(first_question.get("start", 0)), analysis_data
                ),
                "chapter_number": 1,
            }
        )

    return chapters


def generate_chapter_title(
    question_or_segment: dict, analysis_data: dict, chapter_number: int
) -> str:
    """
    Generate meaningful chapter title from question or segment content.

    Args:
        question_or_segment: Question or segment dictionary with text and timing
        analysis_data: Complete analysis data
        chapter_number: Chapter sequence number

    Returns:
        Generated chapter title string
    """
    # Handle question-based titles
    if "text" in question_or_segment:
        return generate_chapter_title_from_question(question_or_segment, chapter_number)

    # Fallback for segment-based titles (legacy support)
    segment_start = float(question_or_segment.get("start", 0))
    text = question_or_segment.get("text", "").strip()

    # Look for questions near this timestamp (within 30 seconds)
    questions = analysis_data.get("questions", [])
    nearby_question = next(
        (q for q in questions if abs(q.get("start", 0) - segment_start) < 30), None
    )

    if nearby_question:
        return generate_chapter_title_from_question(nearby_question, chapter_number)

    # Look for keyword clusters near this time
    nearby_keywords = get_nearby_keywords(segment_start, analysis_data, window=60)
    if nearby_keywords:
        primary_keyword = nearby_keywords[0]["keyword"]
        return f"Topic: {primary_keyword.title()}"

    # Use segment content if available
    if text and len(text.strip()) > 10:
        # Extract meaningful words (remove filler words)
        filler_words = {
            "um",
            "uh",
            "so",
            "like",
            "you",
            "know",
            "the",
            "and",
            "or",
            "but",
        }
        words = [w for w in text.split() if w.lower() not in filler_words]
        if words:
            content_preview = " ".join(words[:8])
            if len(content_preview) > 50:
                content_preview = content_preview[:47] + "..."
            return f"Content: {content_preview}"

    # Default chapter naming with timestamp
    minutes = int(segment_start // 60)
    seconds = int(segment_start % 60)
    return f"Chapter {chapter_number} ({minutes:02d}:{seconds:02d})"


def get_nearby_keywords(
    timestamp: float, analysis_data: dict, window: int = 120
) -> list:
    """
    Get keywords that appear near the given timestamp.

    Args:
        timestamp: Target timestamp in seconds
        analysis_data: Complete analysis data
        window: Time window in seconds to search around timestamp

    Returns:
        List of keyword dictionaries sorted by relevance
    """
    keywords = analysis_data.get("keyword_matches", [])
    nearby_keywords = []

    for keyword_data in keywords:
        keyword = keyword_data.get("keyword", "")
        # For now, we'll include all keywords since we don't have timestamp data
        # In a future enhancement, we could add timestamp tracking to keyword matches
        if keyword:
            nearby_keywords.append(
                {
                    "keyword": keyword,
                    "count": keyword_data.get("count", 0),
                    "relevance": keyword_data.get(
                        "count", 0
                    ),  # Use count as relevance score
                }
            )

    # Sort by relevance (count) descending
    nearby_keywords.sort(key=lambda x: x.get("relevance", 0), reverse=True)

    # Return top 5 most relevant keywords
    return nearby_keywords[:5]


def _is_question_boundary(
    timestamp: float, analysis_data: dict, threshold: int = 10
) -> bool:
    """
    Check if the timestamp is near a question boundary.

    Args:
        timestamp: Timestamp to check
        analysis_data: Analysis data
        threshold: Time threshold in seconds

    Returns:
        True if near a question, False otherwise
    """
    questions = analysis_data.get("questions", [])

    for question in questions:
        question_time = question.get("start", 0)  # Updated to use 'start' key
        if abs(question_time - timestamp) <= threshold:
            return True

    return False
