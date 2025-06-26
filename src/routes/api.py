"""
API routes for the video transcriber application.

This module provides RESTful API endpoints for configuration management,
performance monitoring, and system status information.
"""

import logging
import multiprocessing
import os
import time
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, Response, jsonify, request

from src.config import PerformanceConfig, VideoConfig
from src.models.exceptions import UserFriendlyError
from src.utils import (
    handle_user_friendly_error,
    is_valid_session_id,
    load_keywords,
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
    """Get current performance settings"""
    optimal_workers = (
        memory_manager.get_optimal_workers()
        if memory_manager
        else PerformanceConfig.DEFAULT_MAX_WORKERS
    )
    memory_info = memory_manager.get_memory_info() if memory_manager else {}

    settings = {
        "chunk_duration": getattr(PerformanceConfig, "current_chunk_duration", 300),
        "max_workers": getattr(
            PerformanceConfig, "current_max_workers", optimal_workers
        ),
        "optimal_workers": optimal_workers,
        "cpu_count": multiprocessing.cpu_count(),
        "memory_info": memory_info,
        "limits": {
            "min_workers": PerformanceConfig.MIN_WORKERS,
            "max_workers_limit": PerformanceConfig.MAX_WORKERS_LIMIT,
            "min_chunk_duration": VideoConfig.MIN_CHUNK_DURATION_SECONDS,
            "max_chunk_duration": VideoConfig.MAX_CHUNK_DURATION_SECONDS,
        },
    }

    return jsonify({"success": True, "settings": settings})


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
                f"Chunk duration must be between {VideoConfig.MIN_CHUNK_DURATION_SECONDS} and {VideoConfig.MAX_CHUNK_DURATION_SECONDS} seconds, got: {chunk_duration}"
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
                f"Max workers must be between {PerformanceConfig.MIN_WORKERS} and {PerformanceConfig.MAX_WORKERS_LIMIT}, got: {max_workers}"
            )
        PerformanceConfig.current_max_workers = max_workers

    logger.info(
        f"Updated performance settings: chunk_duration={getattr(PerformanceConfig, 'current_chunk_duration', 'unchanged')}, "
        f"max_workers={getattr(PerformanceConfig, 'current_max_workers', 'unchanged')}"
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
            f"Memory limits optimal workers to {optimal_workers} (CPU cores: {multiprocessing.cpu_count()})"
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
                    "elapsed_time": time.time()
                    - session_data.get("start_time", time.time()),
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
