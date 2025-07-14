"""
API routes for speaker diarization functionality
"""

import json
import logging
import os

from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

from src.services.speaker_diarization import SpeakerDiarizationService

logger = logging.getLogger(__name__)

# Create blueprint
speaker_bp = Blueprint("speaker", __name__, url_prefix="/api/speaker")

# Initialize service (will use mock if pyannote not available)
speaker_service = SpeakerDiarizationService(use_mock=True)


@speaker_bp.route("/status", methods=["GET"])
def get_speaker_status():
    """Get speaker diarization service status"""
    try:
        status = {
            "available": speaker_service.is_available(),
            "using_mock": getattr(speaker_service, "use_mock", False),
            "device": getattr(speaker_service, "device", "unknown"),
            "pipeline_loaded": speaker_service.pipeline is not None,
        }

        return jsonify({"success": True, "status": status})

    except Exception as e:
        logger.error(f"Error getting speaker status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@speaker_bp.route("/diarize", methods=["POST"])
def diarize_audio():
    """Perform speaker diarization on audio file"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        audio_path = data.get("audio_path")
        min_speakers = data.get("min_speakers", 1)
        max_speakers = data.get("max_speakers", 10)

        if not audio_path:
            return jsonify({"success": False, "error": "audio_path is required"}), 400

        # Validate file exists (in production, add proper validation)
        if not os.path.exists(audio_path):
            logger.warning(f"Audio file not found: {audio_path}")
            # For testing, continue with mock

        # Perform diarization
        diarization = speaker_service.diarize_audio(
            audio_path, min_speakers=min_speakers, max_speakers=max_speakers
        )

        if diarization is None:
            return jsonify({"success": False, "error": "Diarization failed"}), 500

        # Extract segments
        speaker_segments = speaker_service.extract_speaker_segments(diarization)

        return jsonify(
            {
                "success": True,
                "speaker_segments": speaker_segments,
                "total_segments": len(speaker_segments),
                "unique_speakers": len(set(seg["speaker"] for seg in speaker_segments)),
                "using_mock": getattr(speaker_service, "use_mock", False),
            }
        )

    except Exception as e:
        logger.error(f"Error in speaker diarization: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@speaker_bp.route("/align", methods=["POST"])
def align_with_transcription():
    """Align speaker segments with transcription"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        transcription_segments = data.get("transcription_segments", [])
        speaker_segments = data.get("speaker_segments", [])
        overlap_threshold = data.get("overlap_threshold", 0.5)

        if not transcription_segments:
            return (
                jsonify(
                    {"success": False, "error": "transcription_segments is required"}
                ),
                400,
            )

        if not speaker_segments:
            return (
                jsonify({"success": False, "error": "speaker_segments is required"}),
                400,
            )

        # Perform alignment
        enhanced_segments = speaker_service.align_transcription_with_speakers(
            transcription_segments,
            speaker_segments,
            overlap_threshold=overlap_threshold,
        )

        # Calculate statistics
        speaker_stats = speaker_service.get_speaker_statistics(enhanced_segments)

        return jsonify(
            {
                "success": True,
                "enhanced_segments": enhanced_segments,
                "speaker_statistics": speaker_stats,
                "total_segments": len(enhanced_segments),
                "segments_with_speakers": len(
                    [s for s in enhanced_segments if s.get("speaker") != "unknown"]
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error in speaker alignment: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@speaker_bp.route("/process", methods=["POST"])
def process_complete():
    """Complete speaker diarization pipeline"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        audio_path = data.get("audio_path")
        transcription_segments = data.get("transcription_segments", [])
        min_speakers = data.get("min_speakers", 1)
        max_speakers = data.get("max_speakers", 10)

        if not audio_path:
            return jsonify({"success": False, "error": "audio_path is required"}), 400

        if not transcription_segments:
            return (
                jsonify(
                    {"success": False, "error": "transcription_segments is required"}
                ),
                400,
            )

        # Process complete pipeline
        results = speaker_service.process_audio_with_speakers(
            audio_path,
            transcription_segments,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )

        return jsonify({"success": results.get("success", True), **results})

    except Exception as e:
        logger.error(f"Error in complete speaker processing: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@speaker_bp.route("/statistics/<session_id>", methods=["GET"])
def get_speaker_statistics(session_id):
    """Get speaker statistics for a session"""
    try:
        # In production, load from database or session storage
        # For now, return mock statistics

        mock_stats = {
            "total_speakers": 3,
            "total_duration": 120.5,
            "speaker_breakdown": {
                "SPEAKER_00": {
                    "total_duration": 65.2,
                    "segment_count": 8,
                    "word_count": 450,
                    "percentage": 54.1,
                },
                "SPEAKER_01": {
                    "total_duration": 38.7,
                    "segment_count": 5,
                    "word_count": 280,
                    "percentage": 32.1,
                },
                "SPEAKER_02": {
                    "total_duration": 16.6,
                    "segment_count": 3,
                    "word_count": 120,
                    "percentage": 13.8,
                },
            },
            "session_id": session_id,
        }

        return jsonify({"success": True, "statistics": mock_stats})

    except Exception as e:
        logger.error(f"Error getting speaker statistics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@speaker_bp.route("/export/<session_id>/<format>", methods=["GET"])
def export_speaker_enhanced(session_id, format):
    """Export transcription with speaker information"""
    try:
        supported_formats = ["srt", "vtt", "txt", "json"]

        if format not in supported_formats:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Unsupported format. Supported: {supported_formats}",
                    }
                ),
                400,
            )

        # In production, load actual session data
        # For now, return mock data structure

        mock_data = {
            "session_id": session_id,
            "enhanced_segments": [
                {
                    "start": 0.0,
                    "end": 3.5,
                    "text": "Welcome to our meeting today.",
                    "speaker": "SPEAKER_00",
                    "speaker_confidence": 0.95,
                },
                {
                    "start": 4.0,
                    "end": 7.2,
                    "text": "Thank you for joining us.",
                    "speaker": "SPEAKER_01",
                    "speaker_confidence": 0.88,
                },
            ],
            "speaker_statistics": {"total_speakers": 2, "total_duration": 7.2},
        }

        if format == "json":
            return jsonify({"success": True, "data": mock_data})

        elif format == "srt":
            # Generate SRT with speaker labels
            srt_content = ""
            for i, segment in enumerate(mock_data["enhanced_segments"], 1):
                start_time = format_srt_time(segment["start"])
                end_time = format_srt_time(segment["end"])
                speaker_name = segment["speaker"].replace("SPEAKER_", "Speaker ")
                text = f"[{speaker_name}] {segment['text']}"

                srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"

            return jsonify(
                {
                    "success": True,
                    "content": srt_content,
                    "filename": f"{session_id}_with_speakers.srt",
                }
            )

        elif format == "vtt":
            # Generate VTT with speaker labels
            vtt_content = "WEBVTT\n\n"
            for segment in mock_data["enhanced_segments"]:
                start_time = format_vtt_time(segment["start"])
                end_time = format_vtt_time(segment["end"])
                speaker_name = segment["speaker"].replace("SPEAKER_", "Speaker ")
                text = f"<v {speaker_name}>{segment['text']}"

                vtt_content += f"{start_time} --> {end_time}\n{text}\n\n"

            return jsonify(
                {
                    "success": True,
                    "content": vtt_content,
                    "filename": f"{session_id}_with_speakers.vtt",
                }
            )

        elif format == "txt":
            # Generate plain text with speaker labels
            txt_content = f"Transcription: {session_id}\n"
            txt_content += "=" * 50 + "\n\n"

            for segment in mock_data["enhanced_segments"]:
                timestamp = format_timestamp(segment["start"])
                speaker_name = segment["speaker"].replace("SPEAKER_", "Speaker ")
                txt_content += f"[{timestamp}] {speaker_name}: {segment['text']}\n\n"

            return jsonify(
                {
                    "success": True,
                    "content": txt_content,
                    "filename": f"{session_id}_with_speakers.txt",
                }
            )

    except Exception as e:
        logger.error(f"Error exporting speaker-enhanced transcript: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def format_srt_time(seconds):
    """Format time for SRT subtitle format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def format_vtt_time(seconds):
    """Format time for VTT subtitle format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def format_timestamp(seconds):
    """Format time as MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


# Error handlers
@speaker_bp.errorhandler(400)
def bad_request(error):
    return (
        jsonify({"success": False, "error": "Bad request", "message": str(error)}),
        400,
    )


@speaker_bp.errorhandler(500)
def internal_error(error):
    return (
        jsonify(
            {"success": False, "error": "Internal server error", "message": str(error)}
        ),
        500,
    )
