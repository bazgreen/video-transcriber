"""
Multi-language support routes and utilities
"""

import logging
from typing import Dict, List, Optional

from flask import Blueprint, jsonify, render_template, request

# Import language detection service
try:
    from src.services.language_detection import LanguageDetectionService

    LANGUAGE_DETECTION_AVAILABLE = True
except ImportError:
    LANGUAGE_DETECTION_AVAILABLE = False
    LanguageDetectionService = None

logger = logging.getLogger(__name__)

# Create blueprint
multilang_bp = Blueprint("multilang", __name__, url_prefix="/api/multilang")


@multilang_bp.route("/supported-languages", methods=["GET"])
def get_supported_languages():
    """Get list of all supported languages"""
    if not LANGUAGE_DETECTION_AVAILABLE:
        return (
            jsonify({"error": "Multi-language support not available", "languages": {}}),
            503,
        )

    try:
        service = LanguageDetectionService()
        languages = service.get_supported_languages()

        # Format for frontend
        formatted_languages = [
            {"code": code, "name": name.title(), "native_name": name.title()}
            for code, name in languages.items()
        ]

        return jsonify(
            {
                "languages": formatted_languages,
                "total_count": len(formatted_languages),
                "status": "success",
            }
        )

    except Exception as e:
        logger.error(f"Failed to get supported languages: {e}")
        return jsonify({"error": str(e)}), 500


@multilang_bp.route("/detect-language", methods=["POST"])
def detect_language_from_text():
    """Detect language from provided text"""
    if not LANGUAGE_DETECTION_AVAILABLE:
        return jsonify({"error": "Language detection not available"}), 503

    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Text is required"}), 400

        text = data["text"]
        if not text.strip():
            return jsonify({"error": "Text cannot be empty"}), 400

        service = LanguageDetectionService()
        detected_code = service.detect_language_from_text(text)

        if detected_code:
            language_name = service.get_language_name(detected_code)
            return jsonify(
                {
                    "detected_language": detected_code,
                    "language_name": language_name,
                    "confidence": "high",  # langdetect doesn't provide confidence
                    "status": "success",
                }
            )
        else:
            return jsonify(
                {
                    "detected_language": None,
                    "language_name": None,
                    "confidence": "low",
                    "status": "no_detection",
                    "message": "Could not detect language",
                }
            )

    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        return jsonify({"error": str(e)}), 500


@multilang_bp.route("/language-preferences", methods=["GET", "POST"])
def manage_language_preferences():
    """Get or set user language preferences"""
    if request.method == "GET":
        # Return current preferences (could be stored in session/database)
        return jsonify(
            {
                "default_language": "auto",  # auto-detect
                "fallback_language": "en",
                "preferred_languages": ["en", "es", "fr", "de"],
                "auto_detect": True,
            }
        )

    elif request.method == "POST":
        try:
            data = request.get_json()
            # Here you would save preferences to session/database

            return jsonify(
                {
                    "message": "Language preferences updated",
                    "preferences": data,
                    "status": "success",
                }
            )

        except Exception as e:
            logger.error(f"Failed to update language preferences: {e}")
            return jsonify({"error": str(e)}), 500
