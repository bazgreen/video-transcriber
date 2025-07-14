"""
PWA Mobile UI Routes.

Handles mobile-specific UI components and navigation.
"""

import json
import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, current_app, jsonify, render_template, request

# Create blueprint
pwa_mobile_bp = Blueprint("pwa_mobile", __name__, url_prefix="/mobile")


def mobile_required(f):
    """Decorator to check if request is from mobile device"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_agent = request.headers.get("User-Agent", "").lower()
        is_mobile = any(
            device in user_agent
            for device in ["android", "iphone", "ipad", "mobile", "tablet"]
        )

        # Also check screen size from headers if available
        screen_width = request.headers.get("X-Screen-Width")
        if screen_width and int(screen_width) <= 768:
            is_mobile = True

        if not is_mobile:
            # Redirect to desktop version or show mobile hint
            return jsonify(
                {
                    "redirect": "/",
                    "message": "This page is optimized for mobile devices",
                }
            )

        return f(*args, **kwargs)

    return decorated_function


@pwa_mobile_bp.route("/sessions")
def mobile_sessions():
    """Mobile-optimized sessions page"""
    try:
        # Get sessions from database or mock data
        sessions = get_mobile_sessions()
        return render_template("mobile-sessions.html", sessions=sessions)
    except Exception as e:
        current_app.logger.error(f"Error loading mobile sessions: {e}")
        return render_template("mobile-sessions.html", sessions=[])


@pwa_mobile_bp.route("/upload")
def mobile_upload():
    """Mobile-optimized upload interface"""
    return render_template("mobile-upload.html")


@pwa_mobile_bp.route("/session/<session_id>")
def mobile_session_detail(session_id):
    """Mobile-optimized session detail view"""
    try:
        session = get_session_by_id(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        return render_template("mobile-session-detail.html", session=session)
    except Exception as e:
        current_app.logger.error(f"Error loading session {session_id}: {e}")
        return jsonify({"error": "Failed to load session"}), 500


@pwa_mobile_bp.route("/api/sessions")
def api_mobile_sessions():
    """API endpoint for mobile sessions with pagination"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        filter_type = request.args.get("filter", "all")
        search = request.args.get("search", "")

        sessions = get_mobile_sessions_paginated(page, per_page, filter_type, search)

        return jsonify(
            {
                "success": True,
                "sessions": sessions,
                "has_more": len(sessions) == per_page,
                "page": page,
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error fetching mobile sessions: {e}")
        return jsonify({"error": "Failed to fetch sessions"}), 500


@pwa_mobile_bp.route("/api/session/<session_id>/share")
def api_share_session(session_id):
    """Generate shareable link for session"""
    try:
        session = get_session_by_id(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        # Generate share token or use session ID
        share_url = f"{request.host_url}shared/{session_id}"

        return jsonify(
            {
                "success": True,
                "share_url": share_url,
                "title": f"Video Transcription: {session.get('filename', 'Untitled')}",
                "description": f"Transcribed video session from {session.get('created_at', 'Unknown date')}",
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error sharing session {session_id}: {e}")
        return jsonify({"error": "Failed to generate share link"}), 500


@pwa_mobile_bp.route("/api/ui/navigation")
def api_navigation_state():
    """Get navigation state for mobile UI"""
    try:
        return jsonify(
            {
                "success": True,
                "navigation": {
                    "home": {"active": request.endpoint == "main.index"},
                    "upload": {"active": "upload" in request.endpoint, "badge": 0},
                    "sessions": {
                        "active": "sessions" in request.endpoint,
                        "badge": get_unread_sessions_count(),
                    },
                    "insights": {"active": "insights" in request.endpoint, "badge": 0},
                    "profile": {"active": "profile" in request.endpoint, "badge": 0},
                },
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error getting navigation state: {e}")
        return jsonify({"error": "Failed to get navigation state"}), 500


@pwa_mobile_bp.route("/api/ui/panel/<panel_type>")
def api_panel_content(panel_type):
    """Get dynamic content for mobile panels"""
    try:
        if panel_type == "upload":
            return jsonify(
                {
                    "success": True,
                    "content": {
                        "title": "Upload Video",
                        "options": [
                            {
                                "id": "camera",
                                "icon": "camera",
                                "label": "Record Video",
                                "enabled": True,
                            },
                            {
                                "id": "file",
                                "icon": "file-video",
                                "label": "Choose File",
                                "enabled": True,
                            },
                            {
                                "id": "voice",
                                "icon": "microphone",
                                "label": "Voice Note",
                                "enabled": True,
                            },
                        ],
                    },
                }
            )
        elif panel_type == "profile":
            return jsonify(
                {
                    "success": True,
                    "content": {
                        "title": "Profile",
                        "options": [
                            {
                                "id": "settings",
                                "icon": "cog",
                                "label": "Settings",
                                "enabled": True,
                            },
                            {
                                "id": "export",
                                "icon": "download",
                                "label": "Export Data",
                                "enabled": True,
                            },
                            {
                                "id": "help",
                                "icon": "question-circle",
                                "label": "Help",
                                "enabled": True,
                            },
                            {
                                "id": "about",
                                "icon": "info-circle",
                                "label": "About",
                                "enabled": True,
                            },
                        ],
                    },
                }
            )
        else:
            return jsonify({"error": "Invalid panel type"}), 400
    except Exception as e:
        current_app.logger.error(f"Error getting panel content for {panel_type}: {e}")
        return jsonify({"error": "Failed to get panel content"}), 500


@pwa_mobile_bp.route("/api/ui/refresh")
def api_refresh_content():
    """Handle pull-to-refresh requests"""
    try:
        # Simulate refresh delay
        import time

        time.sleep(1)

        # Get fresh content
        updated_data = {
            "timestamp": datetime.now().isoformat(),
            "sessions_count": get_sessions_count(),
            "unread_notifications": get_unread_notifications_count(),
            "version": "1.0.0",
        }

        return jsonify(
            {
                "success": True,
                "message": "Content refreshed successfully",
                "data": updated_data,
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error refreshing content: {e}")
        return jsonify({"error": "Failed to refresh content"}), 500


def get_mobile_sessions():
    """Get sessions optimized for mobile display"""
    # Mock data for now - replace with actual database queries
    return [
        {
            "id": "1",
            "filename": "Meeting Recording.mp4",
            "status": "completed",
            "duration": "45:30",
            "created_at": datetime.now(),
            "file_size": "250 MB",
            "language": "English",
            "transcript_preview": "Welcome everyone to today's meeting. We have several important topics to discuss...",
        },
        {
            "id": "2",
            "filename": "Lecture Video.mp4",
            "status": "processing",
            "duration": "1:20:15",
            "created_at": datetime.now(),
            "file_size": "800 MB",
            "language": "English",
            "transcript_preview": "Today we will be covering the fundamentals of machine learning...",
        },
        {
            "id": "3",
            "filename": "Interview.mp4",
            "status": "completed",
            "duration": "32:45",
            "created_at": datetime.now(),
            "file_size": "180 MB",
            "language": "English",
            "transcript_preview": "Thank you for taking the time to speak with us today. Can you tell us about your background?",
        },
    ]


def get_mobile_sessions_paginated(page, per_page, filter_type, search):
    """Get paginated sessions for mobile"""
    sessions = get_mobile_sessions()

    # Apply filters
    if filter_type != "all":
        sessions = [s for s in sessions if s["status"] == filter_type]

    # Apply search
    if search:
        sessions = [
            s
            for s in sessions
            if search.lower() in s["filename"].lower()
            or search.lower() in s.get("transcript_preview", "").lower()
        ]

    # Paginate
    start = (page - 1) * per_page
    end = start + per_page

    return sessions[start:end]


def get_session_by_id(session_id):
    """Get session by ID"""
    sessions = get_mobile_sessions()
    return next((s for s in sessions if s["id"] == session_id), None)


def get_unread_sessions_count():
    """Get count of unread sessions"""
    return 2  # Mock count


def get_sessions_count():
    """Get total sessions count"""
    return len(get_mobile_sessions())


def get_unread_notifications_count():
    """Get count of unread notifications"""
    return 1  # Mock count


# Error handlers
@pwa_mobile_bp.errorhandler(404)
def mobile_not_found(error):
    """Handle 404 errors for mobile routes."""
    _ = error  # Suppress unused argument warning
    return jsonify({"error": "Resource not found"}), 404


@pwa_mobile_bp.errorhandler(500)
def mobile_server_error(error):
    """Handle 500 errors for mobile routes."""
    _ = error  # Suppress unused argument warning
    return jsonify({"error": "Internal server error"}), 500
