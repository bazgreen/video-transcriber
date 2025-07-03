"""Main web routes for the video transcriber application."""

import json
import logging
import os

from flask import Blueprint, redirect, render_template, request, send_file, url_for

from src.config import AppConfig
from src.models.exceptions import UserFriendlyError
from src.utils import is_safe_path, is_valid_session_id, load_session_metadata

main_bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)
config = AppConfig()


@main_bp.route("/")
def index():
    """Main page"""
    return render_template("index.html")


@main_bp.route("/results/<session_id>")
def results(session_id):
    """Show results for a specific session"""
    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID")

    session_path = os.path.join(config.RESULTS_FOLDER, session_id)
    if not os.path.exists(session_path):
        raise UserFriendlyError(f"Session '{session_id}' not found")

    # Load session metadata
    metadata = load_session_metadata(session_id, session_path)

    # Load analysis data
    analysis_file = os.path.join(session_path, "analysis.json")
    analysis = {}
    if os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r") as f:
                analysis_data = json.load(f)
                # Extract nested analysis data if it exists
                if "analysis" in analysis_data:
                    analysis = analysis_data["analysis"]
                else:
                    analysis = analysis_data
                logger.debug(f"Loaded analysis data for session {session_id}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(
                f"Failed to load analysis file for session {session_id}: {e}"
            )
            # Provide empty analysis data structure
            analysis = {
                "keyword_matches": [],
                "questions": [],
                "emphasis_cues": [],
                "total_words": 0,
            }

    return render_template(
        "results.html",
        session_id=session_id,
        metadata=metadata,
        analysis=analysis,
        session_path=session_path,
    )


@main_bp.route("/download/<session_id>/<filename>")
def download_file(session_id, filename):
    """Download a specific file from a session"""
    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID")

    session_path = os.path.join(config.RESULTS_FOLDER, session_id)
    file_path = os.path.join(session_path, filename)

    if not is_safe_path(file_path, config.RESULTS_FOLDER):
        raise UserFriendlyError("Invalid file path")

    if not os.path.exists(file_path):
        raise UserFriendlyError("File not found")

    return send_file(file_path, as_attachment=True)


@main_bp.route("/transcript/<session_id>")
def transcript(session_id):
    """Show interactive transcript for a session"""
    if not is_valid_session_id(session_id):
        raise UserFriendlyError("Invalid session ID")

    session_path = os.path.join(config.RESULTS_FOLDER, session_id)
    if not os.path.exists(session_path):
        raise UserFriendlyError(f"Session '{session_id}' not found")

    # Load session metadata
    metadata = load_session_metadata(session_id, session_path)

    # Load analysis data
    analysis_file = os.path.join(session_path, "analysis.json")
    analysis = {}
    if os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r") as f:
                analysis_data = json.load(f)
                # Extract nested analysis data if it exists
                if "analysis" in analysis_data:
                    analysis = analysis_data["analysis"]
                else:
                    analysis = analysis_data
                logger.debug(f"Loaded analysis data for transcript {session_id}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(
                f"Failed to load analysis file for transcript {session_id}: {e}"
            )
            # Provide empty analysis data structure
            analysis = {
                "keyword_matches": [],
                "questions": [],
                "emphasis_cues": [],
                "total_words": 0,
            }

    # Load transcript segments from analysis or session data
    segments = []

    # First try to get segments from the loaded analysis data
    if "segments" in analysis_data:
        segments = analysis_data["segments"]
    elif "segments" in analysis:
        segments = analysis["segments"]
    else:
        # Fallback: create segments from questions and emphasis cues only
        if "questions" in analysis:
            segments.extend(analysis["questions"])
        if "emphasis_cues" in analysis:
            segments.extend(analysis["emphasis_cues"])

    # Sort segments by timestamp for proper display
    segments.sort(key=lambda x: x.get("start", 0))

    # Function to detect low-quality transcription segments
    def is_likely_gibberish(text):
        """Detect if a text segment is likely gibberish or low-quality transcription"""
        if not text or len(text.strip()) == 0:
            return True

        text = text.strip()

        # Check for excessive non-ASCII characters (Unicode gibberish)
        ascii_chars = sum(1 for char in text if ord(char) < 128)
        total_chars = len(text)
        if total_chars > 0 and ascii_chars / total_chars < 0.6:
            return True

        # Check for specific gibberish patterns
        gibberish_patterns = [
            "ᄟᄳ",
            "овор",
            "ᆽᄲᓜ",
            "değiş",
            "λε",
            "먹을",
            "maki k",
            "cleaningspeak",
            "팍له",
            "plaint trope",
            "amis member",
            "towe",
            "appargewana",
            "Indere Payter",
            "valentina",
            "ー quite",
            "weirdest eyelashes",
            "gêė",
            "PCBėę",
            "whèn inducté",
            "tý valuation",
            "bewядz",
            "Stall reportedly",
            "mės adhesive",
            "Padnam Alle",
            "dopol",
            "meses y tutti",
            "githé",
            "avour thinking",
            "jazz linders",
            "nye dėoh",
            "tūl ach cheat",
            "vill ehm",
            "así misto",
            "tut zhiò",
            "s'hė Interview",
            "pexãŒ",
            "PxãŒ",
        ]

        # If text contains any of these known gibberish patterns, mark as gibberish
        text_lower = text.lower()
        for pattern in gibberish_patterns:
            if pattern.lower() in text_lower:
                return True

        # Check for segments with unusual character combinations
        import re

        # Look for segments with mixed scripts (Latin + Korean + Arabic + Greek + Cyrillic)
        if re.search(r"[ᄀ-ힿ].*[а-я]|[а-я].*[ᄀ-ힿ]|[α-ω].*[ᄀ-ힿ]|[ᄀ-ힿ].*[α-ω]", text):
            return True

        # Check for segments with too many non-standard characters
        unusual_chars = re.findall(r"[^\w\s.,!?\'\"-]", text)
        if len(unusual_chars) > len(text) * 0.2:
            return True

        # Check for very short segments that don't make sense
        words = text.split()
        if len(words) <= 3:
            # Single/short segments that are likely noise
            noise_words = ["exch", "ー", "eh", "ehm", "uh", "um", "ah", "hmm"]
            if any(word.lower() in noise_words for word in words):
                return True

            # Very short segments with weird character combinations
            for word in words:
                if len(word) > 0 and not re.match(r"^[a-zA-Z.,!?\'\"-]*$", word):
                    # Contains non-standard characters
                    if len(word) < 4 or not any(char.isalpha() for char in word):
                        return True

        return False

    # Process segments for template rendering
    processed_segments = []
    for segment in segments:
        text = segment.get("text", "")

        # Skip likely gibberish segments
        if is_likely_gibberish(text):
            continue

        # Determine segment type and styling
        segment_classes = []
        segment_types = []

        # Check if this segment is a question
        if any(
            q.get("start") == segment.get("start")
            for q in analysis.get("questions", [])
        ):
            segment_classes.append("question")
            segment_types.append("questions")

        # Check if this segment has emphasis
        if any(
            e.get("start") == segment.get("start")
            for e in analysis.get("emphasis_cues", [])
        ):
            segment_classes.append("emphasis")
            segment_types.append("emphasis")

        # Check if this segment contains keywords
        highlighted_text = text
        has_keyword = False

        for keyword_match in analysis.get("keyword_matches", []):
            keyword = keyword_match.get("keyword", "")
            if keyword.lower() in text.lower():
                has_keyword = True
                # Simple highlighting - replace keyword with highlighted version
                highlighted_text = highlighted_text.replace(
                    keyword, f'<span class="keyword">{keyword}</span>'
                )

        if has_keyword:
            segment_classes.append("highlight")
            segment_types.append("keywords")

        # Default styling if no special type
        if not segment_types:
            segment_types.append("normal")

        processed_segments.append(
            {
                "timestamp_str": segment.get("timestamp_str", ""),
                "highlighted_text": highlighted_text,
                "classes": segment_classes,
                "types": segment_types,
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": text,
            }
        )

    return render_template(
        "transcript.html",
        session_id=session_id,
        analysis=analysis,
        metadata=metadata,
        segments=processed_segments,
    )


@main_bp.route("/sessions")
def sessions():
    """List all sessions"""
    if not os.path.exists(config.RESULTS_FOLDER):
        os.makedirs(config.RESULTS_FOLDER)
        return render_template("sessions.html", sessions=[])

    sessions_list = []
    for session_folder in os.listdir(config.RESULTS_FOLDER):
        session_path = os.path.join(config.RESULTS_FOLDER, session_folder)
        if os.path.isdir(session_path):
            metadata = load_session_metadata(session_folder, session_path)
            sessions_list.append(metadata)

    # Sort by creation time (newest first)
    sessions_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return render_template("sessions.html", sessions=sessions_list)


@main_bp.route("/sessions/search")
def search_sessions():
    """Search sessions by keyword"""
    query = request.args.get("q", "").strip().lower()
    if not query:
        return redirect(url_for("main.sessions"))

    if not os.path.exists(config.RESULTS_FOLDER):
        return render_template("sessions.html", sessions=[], search_query=query)

    matching_sessions = []
    for session_folder in os.listdir(config.RESULTS_FOLDER):
        session_path = os.path.join(config.RESULTS_FOLDER, session_folder)
        if os.path.isdir(session_path):
            # Load session metadata
            metadata = load_session_metadata(session_folder, session_path)

            # Search in session name and original filename
            if (
                query in metadata.get("session_name", "").lower()
                or query in metadata.get("original_filename", "").lower()
                or query in session_folder.lower()
            ):
                matching_sessions.append(metadata)
                continue

            # Search in transcript content
            transcript_file = os.path.join(session_path, "full_transcript.txt")
            if os.path.exists(transcript_file):
                try:
                    with open(transcript_file, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        if query in content:
                            matching_sessions.append(metadata)
                except (IOError, UnicodeDecodeError):
                    pass

    # Sort by creation time (newest first)
    matching_sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return render_template(
        "sessions.html", sessions=matching_sessions, search_query=query
    )


@main_bp.route("/config")
def config_page():
    """Configuration page"""
    from src.utils import load_keywords
    keywords = load_keywords()
    return render_template("config.html", keywords=keywords)


@main_bp.route("/performance")
def performance():
    """Performance monitoring page"""
    return render_template("performance.html")
