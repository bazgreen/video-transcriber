"""
PWA-specific routes and functionality for Video Transcriber.

Handles service worker, manifest, offline mode, and PWA features.
"""

import json
import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template, request

pwa_bp = Blueprint("pwa", __name__)


@pwa_bp.route("/manifest.json")
def manifest():
    """Serve the web app manifest"""
    try:
        manifest_path = os.path.join(current_app.static_folder, "manifest.json")
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)

        return (
            jsonify(manifest_data),
            200,
            {"Content-Type": "application/manifest+json"},
        )
    except Exception as e:
        current_app.logger.error(f"Failed to serve manifest: {e}")
        return jsonify({"error": "Manifest not found"}), 404


@pwa_bp.route("/sw.js")
def service_worker():
    """Serve the service worker with proper headers"""
    try:
        sw_path = os.path.join(current_app.static_folder, "sw.js")
        with open(sw_path, "r") as f:
            sw_content = f.read()

        return (
            sw_content,
            200,
            {
                "Content-Type": "application/javascript",
                "Service-Worker-Allowed": "/",
                "Cache-Control": "no-cache",
            },
        )
    except Exception as e:
        current_app.logger.error(f"Failed to serve service worker: {e}")
        return "console.error('Service worker not found');", 404


@pwa_bp.route("/offline")
def offline():
    """Serve the offline page"""
    return render_template("offline.html")


@pwa_bp.route("/api/pwa/status")
def pwa_status():
    """Get PWA installation and capability status"""

    user_agent = request.headers.get("User-Agent", "").lower()

    # Detect if request is from PWA
    is_standalone = (
        request.headers.get("X-Requested-With") == "PWA"
        or "mobile" in user_agent
        and "standalone" in request.args
    )

    # Check PWA capabilities
    capabilities = {
        "service_worker": True,  # We provide service worker
        "offline_support": True,
        "background_sync": True,
        "push_notifications": True,
        "install_prompt": True,
        "file_system_access": "file" in user_agent or "chrome" in user_agent,
        "camera_access": "mobile" in user_agent or "chrome" in user_agent,
        "share_api": "mobile" in user_agent,
    }

    return jsonify(
        {
            "success": True,
            "pwa_enabled": True,
            "is_standalone": is_standalone,
            "capabilities": capabilities,
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
        }
    )


@pwa_bp.route("/api/pwa/install-stats", methods=["POST"])
def track_install_stats():
    """Track PWA installation statistics"""

    data = request.get_json() or {}
    event_type = data.get(
        "event_type"
    )  # 'prompt_shown', 'install_accepted', 'install_dismissed'
    user_agent = request.headers.get("User-Agent", "")

    # Log the installation event
    current_app.logger.info(
        f"PWA Install Event: {event_type} - User Agent: {user_agent}"
    )

    # In a real implementation, you might store this in a database
    # For now, we'll just acknowledge the event

    return jsonify(
        {"success": True, "message": "Install event tracked", "event_type": event_type}
    )


@pwa_bp.route("/api/pwa/cache-stats")
def cache_stats():
    """Get information about cached content and storage usage"""

    # This would typically check actual cache usage
    # For now, return mock data
    stats = {
        "cache_version": "1.0.0",
        "static_files_cached": 15,
        "dynamic_content_cached": 8,
        "estimated_storage_mb": 12.5,
        "last_cache_update": datetime.now().isoformat(),
        "offline_sessions_available": 3,
    }

    return jsonify({"success": True, "stats": stats})


@pwa_bp.route("/api/push/vapid-key")
def get_vapid_key():
    """Get the VAPID public key for push notifications"""

    # In a real implementation, this would return your actual VAPID public key
    # For now, return a placeholder
    vapid_public_key = current_app.config.get(
        "VAPID_PUBLIC_KEY", "demo-key-replace-with-real-vapid-key"
    )

    return jsonify({"success": True, "publicKey": vapid_public_key})


@pwa_bp.route("/api/push/subscribe", methods=["POST"])
def subscribe_to_push():
    """Subscribe a user to push notifications"""

    subscription_data = request.get_json()

    if not subscription_data:
        return (
            jsonify({"success": False, "error": "No subscription data provided"}),
            400,
        )

    # In a real implementation, you would:
    # 1. Validate the subscription data
    # 2. Store it in your database
    # 3. Associate it with the current user

    current_app.logger.info(
        f"Push subscription received: {subscription_data.get('endpoint', 'unknown')}"
    )

    return jsonify(
        {
            "success": True,
            "message": "Push subscription saved",
            "subscription_id": "demo-subscription-id",
        }
    )


@pwa_bp.route("/api/push/unsubscribe", methods=["POST"])
def unsubscribe_from_push():
    """Unsubscribe a user from push notifications"""

    subscription_data = request.get_json() or {}
    endpoint = subscription_data.get("endpoint")

    if not endpoint:
        return jsonify({"success": False, "error": "No endpoint provided"}), 400

    # In a real implementation, remove the subscription from database
    current_app.logger.info(f"Push unsubscription: {endpoint}")

    return jsonify({"success": True, "message": "Push subscription removed"})


@pwa_bp.route("/api/pwa/offline-queue", methods=["GET"])
def get_offline_queue():
    """Get the current offline processing queue"""

    # In a real implementation, this would check the actual queue
    # For now, return empty queue
    return jsonify(
        {"success": True, "queue": [], "queue_length": 0, "processing": False}
    )


@pwa_bp.route("/api/pwa/offline-queue", methods=["POST"])
def add_to_offline_queue():
    """Add an item to the offline processing queue"""

    queue_item = request.get_json()

    if not queue_item:
        return jsonify({"success": False, "error": "No queue item provided"}), 400

    # In a real implementation, add to queue database/storage
    current_app.logger.info(
        f"Added to offline queue: {queue_item.get('filename', 'unknown')}"
    )

    return jsonify(
        {
            "success": True,
            "message": "Item added to offline queue",
            "queue_id": "demo-queue-id",
        }
    )


@pwa_bp.route("/api/pwa/clear-cache", methods=["POST"])
def clear_cache():
    """Clear PWA cache (admin function)"""

    # This would typically trigger cache clearing
    # For now, just acknowledge the request

    current_app.logger.info("PWA cache clear requested")

    return jsonify({"success": True, "message": "Cache clear request processed"})


@pwa_bp.route("/api/pwa/update-check")
def check_for_updates():
    """Check if there are PWA updates available"""

    return jsonify(
        {
            "success": True,
            "update_available": False,
            "current_version": "1.0.0",
            "latest_version": "1.0.0",
            "release_notes": [],
        }
    )


@pwa_bp.route("/api/health")
def health_check():
    """Health check endpoint for testing"""
    return jsonify(
        {"status": "healthy", "timestamp": datetime.now().isoformat(), "pwa": True}
    )


# Error handlers specific to PWA routes
@pwa_bp.errorhandler(404)
def pwa_not_found(error):
    """Handle 404 errors for PWA routes."""
    _ = error  # Suppress unused argument warning
    return (
        jsonify(
            {
                "success": False,
                "error": "PWA resource not found",
                "available_endpoints": [
                    "/manifest.json",
                    "/sw.js",
                    "/offline",
                    "/api/pwa/status",
                ],
            }
        ),
        404,
    )


@pwa_bp.errorhandler(500)
def pwa_server_error(error):
    """Handle 500 errors for PWA routes."""
    _ = error  # Suppress unused argument warning
    return (
        jsonify(
            {
                "success": False,
                "error": "PWA service error",
                "message": "Please try again later",
            }
        ),
        500,
    )
