"""
AI Insights API Routes for Advanced Content Analysis.

This module provides REST API endpoints for accessing AI-powered insights
including sentiment analysis, topic modeling, speaker analysis, and
advanced content classification.
"""

import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, jsonify, request

# Import AI insights engine with graceful fallback
try:
    from src.services.ai_insights import create_ai_insights_engine

    AI_INSIGHTS_AVAILABLE = True
except ImportError:
    AI_INSIGHTS_AVAILABLE = False
    create_ai_insights_engine = None

logger = logging.getLogger(__name__)

# Create blueprint for AI insights routes
ai_insights_bp = Blueprint("ai_insights", __name__, url_prefix="/api/ai")


def get_session_data(session_id: str, results_folder: str) -> Optional[Dict[str, Any]]:
    """
    Load session data including basic analysis and AI insights.

    Args:
        session_id: Session identifier
        results_folder: Path to results directory

    Returns:
        Dictionary containing session data or None if not found
    """
    session_dir = os.path.join(results_folder, session_id)

    if not os.path.exists(session_dir):
        return None

    session_data = {"session_id": session_id}

    # Load basic analysis
    analysis_file = os.path.join(session_dir, "analysis.json")
    if os.path.exists(analysis_file):
        with open(analysis_file, "r") as f:
            session_data["analysis"] = json.load(f)

    # Load AI insights if available
    ai_insights_file = os.path.join(session_dir, "ai_insights.json")
    if os.path.exists(ai_insights_file):
        with open(ai_insights_file, "r") as f:
            session_data["ai_insights"] = json.load(f)

    # Load metadata
    metadata_file = os.path.join(session_dir, "metadata.json")
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            session_data["metadata"] = json.load(f)

    # Load transcript
    transcript_file = os.path.join(session_dir, "full_transcript.txt")
    if os.path.exists(transcript_file):
        with open(transcript_file, "r") as f:
            session_data["transcript"] = f.read()

    return session_data


@ai_insights_bp.route("/capabilities", methods=["GET"])
def get_ai_capabilities() -> Tuple[Dict[str, Any], int]:
    """
    Get available AI capabilities and their status.

    Returns:
        JSON response with capability information
    """
    try:
        capabilities = {
            "ai_insights_available": AI_INSIGHTS_AVAILABLE,
            "features": {
                "sentiment_analysis": AI_INSIGHTS_AVAILABLE,
                "topic_modeling": AI_INSIGHTS_AVAILABLE,
                "speaker_analysis": True,  # Basic speaker analysis always available
                "content_classification": True,  # Basic classification always available
                "key_insights_extraction": True,  # Pattern-based extraction always available
                "advanced_analytics": True,  # Basic analytics always available
            },
            "installation_info": {
                "required_packages": ["textblob", "scikit-learn", "spacy"],
                "install_command": "pip install -r config/requirements/requirements-ai.txt",
                "spacy_model_command": "python -m spacy download en_core_web_sm",
            },
        }

        if AI_INSIGHTS_AVAILABLE:
            # Test actual capabilities
            try:
                engine = create_ai_insights_engine()
                capabilities["features"][
                    "sentiment_analysis"
                ] = engine.sentiment_available
                capabilities["features"][
                    "topic_modeling"
                ] = engine.topic_modeling_available
                capabilities["features"]["advanced_nlp"] = engine.nlp_available
            except Exception as e:
                logger.warning(f"Error testing AI capabilities: {e}")

        return jsonify(capabilities), 200

    except Exception as e:
        logger.error(f"Error getting AI capabilities: {e}")
        return (
            jsonify({"error": "Failed to get AI capabilities", "details": str(e)}),
            500,
        )


@ai_insights_bp.route("/analyze/<session_id>", methods=["POST"])
def analyze_session_ai(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Generate AI insights for an existing session.

    Args:
        session_id: Session identifier

    Returns:
        JSON response with AI insights
    """
    if not AI_INSIGHTS_AVAILABLE:
        return (
            jsonify(
                {
                    "error": "AI insights not available",
                    "message": "Install AI dependencies to enable this feature",
                }
            ),
            503,
        )

    try:
        # Get results folder from app config (should be injected via globals or config)
        results_folder = request.args.get("results_folder", "data/results")

        # Load session data
        session_data = get_session_data(session_id, results_folder)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        # Check if we have required data
        if "analysis" not in session_data or "transcript" not in session_data:
            return jsonify({"error": "Session data incomplete"}), 400

        # Create AI insights engine
        engine = create_ai_insights_engine()

        # Parse transcript into segments (simplified approach)
        # In a full implementation, we'd load the actual segments
        transcript_text = session_data["transcript"]
        basic_analysis = session_data["analysis"]

        # Create dummy segments for analysis (real implementation would load actual segments)
        segments = []
        sentences = transcript_text.split(". ")
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                segments.append(
                    {
                        "text": sentence.strip() + ".",
                        "start": i * 5,  # Estimate 5 seconds per sentence
                        "end": (i + 1) * 5,
                        "timestamp_str": f"{i*5//60:02d}:{i*5 % 60:02d}",
                    }
                )

        # Generate AI insights
        ai_insights = engine.analyze_comprehensive(
            transcript_text, segments, basic_analysis
        )

        # Save AI insights to session
        ai_insights_file = os.path.join(results_folder, session_id, "ai_insights.json")
        with open(ai_insights_file, "w") as f:
            json.dump(ai_insights, f, indent=2)

        return (
            jsonify(
                {"success": True, "session_id": session_id, "ai_insights": ai_insights}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error analyzing session {session_id}: {e}")
        return jsonify({"error": "Analysis failed", "details": str(e)}), 500


@ai_insights_bp.route("/insights/<session_id>", methods=["GET"])
def get_session_insights(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get AI insights for a specific session.

    Args:
        session_id: Session identifier

    Returns:
        JSON response with AI insights
    """
    try:
        results_folder = request.args.get("results_folder", "data/results")

        session_data = get_session_data(session_id, results_folder)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        ai_insights = session_data.get("ai_insights", {})
        if not ai_insights:
            return (
                jsonify(
                    {
                        "error": "No AI insights found",
                        "message": "Run AI analysis first",
                        "available": False,
                    }
                ),
                404,
            )

        return (
            jsonify(
                {
                    "session_id": session_id,
                    "ai_insights": ai_insights,
                    "available": True,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting insights for session {session_id}: {e}")
        return jsonify({"error": "Failed to get insights", "details": str(e)}), 500


@ai_insights_bp.route("/insights/<session_id>/sentiment", methods=["GET"])
def get_sentiment_analysis(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get sentiment analysis for a specific session.

    Args:
        session_id: Session identifier

    Returns:
        JSON response with sentiment analysis
    """
    try:
        results_folder = request.args.get("results_folder", "data/results")

        session_data = get_session_data(session_id, results_folder)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        ai_insights = session_data.get("ai_insights", {})
        sentiment_data = ai_insights.get("sentiment_analysis", {})

        if not sentiment_data:
            return (
                jsonify({"error": "No sentiment analysis found", "available": False}),
                404,
            )

        return (
            jsonify(
                {
                    "session_id": session_id,
                    "sentiment_analysis": sentiment_data,
                    "available": True,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting sentiment for session {session_id}: {e}")
        return (
            jsonify({"error": "Failed to get sentiment analysis", "details": str(e)}),
            500,
        )


@ai_insights_bp.route("/insights/<session_id>/topics", methods=["GET"])
def get_topic_analysis(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get topic modeling results for a specific session.

    Args:
        session_id: Session identifier

    Returns:
        JSON response with topic analysis
    """
    try:
        results_folder = request.args.get("results_folder", "data/results")

        session_data = get_session_data(session_id, results_folder)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        ai_insights = session_data.get("ai_insights", {})
        topic_data = ai_insights.get("topic_modeling", {})

        if not topic_data:
            return (
                jsonify({"error": "No topic analysis found", "available": False}),
                404,
            )

        return (
            jsonify(
                {
                    "session_id": session_id,
                    "topic_analysis": topic_data,
                    "available": True,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting topics for session {session_id}: {e}")
        return (
            jsonify({"error": "Failed to get topic analysis", "details": str(e)}),
            500,
        )


@ai_insights_bp.route("/insights/<session_id>/key-insights", methods=["GET"])
def get_key_insights(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get key insights and action items for a specific session.

    Args:
        session_id: Session identifier

    Returns:
        JSON response with key insights
    """
    try:
        results_folder = request.args.get("results_folder", "data/results")

        session_data = get_session_data(session_id, results_folder)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        ai_insights = session_data.get("ai_insights", {})
        key_insights = ai_insights.get("key_insights", {})

        if not key_insights:
            return jsonify({"error": "No key insights found", "available": False}), 404

        return (
            jsonify(
                {
                    "session_id": session_id,
                    "key_insights": key_insights,
                    "available": True,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting key insights for session {session_id}: {e}")
        return jsonify({"error": "Failed to get key insights", "details": str(e)}), 500


@ai_insights_bp.route("/insights/<session_id>/analytics", methods=["GET"])
def get_advanced_analytics(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Get advanced analytics for a specific session.

    Args:
        session_id: Session identifier

    Returns:
        JSON response with advanced analytics
    """
    try:
        results_folder = request.args.get("results_folder", "data/results")

        session_data = get_session_data(session_id, results_folder)
        if not session_data:
            return jsonify({"error": "Session not found"}), 404

        ai_insights = session_data.get("ai_insights", {})
        analytics_data = ai_insights.get("advanced_analytics", {})

        if not analytics_data:
            return (
                jsonify({"error": "No advanced analytics found", "available": False}),
                404,
            )

        return (
            jsonify(
                {
                    "session_id": session_id,
                    "advanced_analytics": analytics_data,
                    "available": True,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error getting analytics for session {session_id}: {e}")
        return jsonify({"error": "Failed to get analytics", "details": str(e)}), 500


@ai_insights_bp.route("/batch-insights", methods=["POST"])
def analyze_batch_insights() -> Tuple[Dict[str, Any], int]:
    """
    Generate AI insights for multiple sessions in batch.

    Request body should contain:
    {
        "session_ids": ["session1", "session2", ...],
        "insights_types": ["sentiment", "topics", "key_insights"] (optional)
    }

    Returns:
        JSON response with batch analysis results
    """
    if not AI_INSIGHTS_AVAILABLE:
        return (
            jsonify(
                {
                    "error": "AI insights not available",
                    "message": "Install AI dependencies to enable this feature",
                }
            ),
            503,
        )

    try:
        data = request.get_json()
        if not data or "session_ids" not in data:
            return jsonify({"error": "Missing session_ids"}), 400

        session_ids = data["session_ids"]
        insights_types = data.get(
            "insights_types", ["sentiment", "topics", "key_insights"]
        )
        results_folder = data.get("results_folder", "data/results")

        if (
            not isinstance(session_ids, list) or len(session_ids) > 10
        ):  # Limit batch size
            return jsonify({"error": "Invalid session_ids (max 10 sessions)"}), 400

        batch_results = {
            "total_sessions": len(session_ids),
            "successful": 0,
            "failed": 0,
            "results": {},
        }

        engine = create_ai_insights_engine()

        for session_id in session_ids:
            try:
                session_data = get_session_data(session_id, results_folder)
                if not session_data or "transcript" not in session_data:
                    batch_results["results"][session_id] = {
                        "success": False,
                        "error": "Session not found or incomplete",
                    }
                    batch_results["failed"] += 1
                    continue

                # Generate insights (simplified version for batch processing)
                transcript_text = session_data["transcript"]
                basic_analysis = session_data.get("analysis", {})

                # Create simplified segments for batch processing
                segments = [
                    {"text": transcript_text, "start": 0, "timestamp_str": "00:00"}
                ]

                ai_insights = engine.analyze_comprehensive(
                    transcript_text, segments, basic_analysis
                )

                # Filter requested insights types
                filtered_insights = {}
                if "sentiment" in insights_types:
                    filtered_insights["sentiment_analysis"] = ai_insights.get(
                        "sentiment_analysis", {}
                    )
                if "topics" in insights_types:
                    filtered_insights["topic_modeling"] = ai_insights.get(
                        "topic_modeling", {}
                    )
                if "key_insights" in insights_types:
                    filtered_insights["key_insights"] = ai_insights.get(
                        "key_insights", {}
                    )

                batch_results["results"][session_id] = {
                    "success": True,
                    "insights": filtered_insights,
                }
                batch_results["successful"] += 1

            except Exception as e:
                batch_results["results"][session_id] = {
                    "success": False,
                    "error": str(e),
                }
                batch_results["failed"] += 1

        return jsonify(batch_results), 200

    except Exception as e:
        logger.error(f"Error in batch insights analysis: {e}")
        return jsonify({"error": "Batch analysis failed", "details": str(e)}), 500


# Error handlers
@ai_insights_bp.errorhandler(404)
def not_found(error):  # pylint: disable=unused-argument
    return jsonify({"error": "AI insights endpoint not found"}), 404


@ai_insights_bp.errorhandler(500)
def internal_error(error):  # pylint: disable=unused-argument
    return jsonify({"error": "Internal AI insights error"}), 500
