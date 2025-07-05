"""
Batch Processing API Routes.

This module provides REST API endpoints for managing batch video processing,
including creating batches, adding videos, monitoring progress, and retrieving results.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import Blueprint, Response, jsonify, request
from werkzeug.utils import secure_filename

# Import CSRF exemption
try:
    from flask_wtf.csrf import exempt

    CSRF_AVAILABLE = True
except ImportError:
    # Fallback decorator if CSRF not available
    def exempt(func):
        return func

    CSRF_AVAILABLE = False

from src.services.batch_processing import batch_processor
from src.utils.helpers import is_safe_path, is_valid_session_id

logger = logging.getLogger(__name__)

# Create blueprint
batch_bp = Blueprint("batch", __name__, url_prefix="/api/batch")


@batch_bp.route("/create", methods=["POST"])
@exempt
def create_batch() -> Response:
    """Create a new batch processing session."""
    logger.info("Batch create endpoint called")
    try:
        data = request.get_json() or {}

        name = data.get("name")
        max_concurrent = data.get("max_concurrent")

        # Validate max_concurrent if provided
        if max_concurrent is not None:
            if (
                not isinstance(max_concurrent, int)
                or max_concurrent < 1
                or max_concurrent > 5
            ):
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "max_concurrent must be an integer between 1 and 5",
                        }
                    ),
                    400,
                )

        batch_id = batch_processor.create_batch(
            name=name,
            max_concurrent=max_concurrent,
        )

        return jsonify(
            {
                "success": True,
                "batch_id": batch_id,
                "message": "Batch created successfully",
            }
        )

    except Exception as e:
        logger.error(f"Failed to create batch: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@batch_bp.route("/add-video", methods=["POST"])
@exempt
def add_video_to_batch() -> Dict[str, Any]:
    """Add a video file to an existing batch."""
    try:
        # Check if file was uploaded
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400

        # Get batch ID
        batch_id = request.form.get("batch_id")
        if not batch_id:
            return jsonify({"success": False, "error": "batch_id is required"}), 400

        # Validate batch exists
        batch = batch_processor.get_batch(batch_id)
        if not batch:
            return jsonify({"success": False, "error": "Batch not found"}), 404

        # Get optional session name
        session_name = request.form.get("session_name")

        # Secure filename and save
        original_filename = file.filename
        filename = secure_filename(original_filename)

        # Create uploads directory if it doesn't exist
        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)

        # Save file with unique name to avoid conflicts
        import uuid

        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(uploads_dir, unique_filename)
        file.save(file_path)

        # Add to batch
        job_id = batch_processor.add_video_to_batch(
            batch_id=batch_id,
            file_path=file_path,
            original_filename=original_filename,
            session_name=session_name,
        )

        return jsonify(
            {
                "success": True,
                "job_id": job_id,
                "message": f"Video '{original_filename}' added to batch",
            }
        )

    except Exception as e:
        logger.error(f"Failed to add video to batch: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@batch_bp.route("/<batch_id>/start", methods=["POST"])
@exempt
def start_batch(batch_id: str) -> Dict[str, Any]:
    """Start processing a batch."""
    try:
        success = batch_processor.start_batch(batch_id)

        if success:
            return jsonify({"success": True, "message": "Batch processing started"})
        else:
            return jsonify({"success": False, "error": "Failed to start batch"}), 400

    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Failed to start batch {batch_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@batch_bp.route("/<batch_id>", methods=["GET"])
def get_batch(batch_id: str) -> Dict[str, Any]:
    """Get batch details and progress."""
    try:
        batch = batch_processor.get_batch(batch_id)

        if not batch:
            return jsonify({"success": False, "error": "Batch not found"}), 404

        return jsonify({"success": True, "batch": batch.to_dict()})

    except Exception as e:
        logger.error(f"Failed to get batch {batch_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@batch_bp.route("/list", methods=["GET"])
def list_batches() -> Dict[str, Any]:
    """List all batches with summary information."""
    try:
        batches = batch_processor.list_batches()

        return jsonify({"success": True, "batches": batches})

    except Exception as e:
        logger.error(f"Failed to list batches: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@batch_bp.route("/<batch_id>/cancel", methods=["POST"])
@exempt
def cancel_batch(batch_id: str) -> Dict[str, Any]:
    """Cancel a batch."""
    try:
        success = batch_processor.cancel_batch(batch_id)

        if success:
            return jsonify({"success": True, "message": "Batch cancelled"})
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Cannot cancel batch (already completed or not found)",
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Failed to cancel batch {batch_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@batch_bp.route("/<batch_id>", methods=["DELETE"])
def delete_batch(batch_id: str) -> Dict[str, Any]:
    """Delete a batch and its metadata."""
    try:
        success = batch_processor.delete_batch(batch_id)

        if success:
            return jsonify({"success": True, "message": "Batch deleted"})
        else:
            return jsonify({"success": False, "error": "Batch not found"}), 404

    except Exception as e:
        logger.error(f"Failed to delete batch {batch_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@batch_bp.route("/<batch_id>/results", methods=["GET"])
def get_batch_results(batch_id: str) -> Dict[str, Any]:
    """Get results from all completed jobs in a batch."""
    try:
        batch = batch_processor.get_batch(batch_id)

        if not batch:
            return jsonify({"success": False, "error": "Batch not found"}), 404

        results = []
        for job in batch.jobs:
            if job.status.value == "completed" and job.results_path:
                # Read basic job information
                job_result = {
                    "job_id": job.job_id,
                    "original_filename": job.original_filename,
                    "session_name": job.session_name,
                    "session_id": job.session_id,
                    "results_path": job.results_path,
                    "completed_at": (
                        job.completed_at.isoformat() if job.completed_at else None
                    ),
                }

                # Try to read metadata if available
                metadata_file = os.path.join(job.results_path, "metadata.json")
                if os.path.exists(metadata_file):
                    try:
                        import json

                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                        job_result["metadata"] = metadata
                    except Exception as e:
                        logger.warning(
                            f"Failed to read metadata for job {job.job_id}: {e}"
                        )

                results.append(job_result)

        return jsonify(
            {
                "success": True,
                "batch_id": batch_id,
                "batch_name": batch.name,
                "total_jobs": len(batch.jobs),
                "completed_jobs": len(results),
                "results": results,
            }
        )

    except Exception as e:
        logger.error(f"Failed to get batch results {batch_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@batch_bp.route("/<batch_id>/download", methods=["GET"])
def download_batch_results(batch_id: str) -> Any:
    """Download all batch results as a ZIP file."""
    try:
        batch = batch_processor.get_batch(batch_id)

        if not batch:
            return jsonify({"success": False, "error": "Batch not found"}), 404

        import tempfile
        import zipfile

        from flask import send_file

        # Create temporary ZIP file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")

        with zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
            for job in batch.jobs:
                if (
                    job.status.value == "completed"
                    and job.results_path
                    and os.path.exists(job.results_path)
                ):
                    # Add all files from job results directory
                    for root, dirs, files in os.walk(job.results_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Create archive path with job prefix
                            archive_path = os.path.join(
                                f"{job.session_name}_{job.job_id[:8]}",
                                os.path.relpath(file_path, job.results_path),
                            )
                            zipf.write(file_path, archive_path)

        # Send ZIP file
        zip_filename = f"batch_{batch.name}_{batch_id[:8]}.zip"

        def remove_file(response):
            try:
                os.unlink(temp_zip.name)
            except Exception:
                pass
            return response

        return send_file(
            temp_zip.name,
            as_attachment=True,
            download_name=zip_filename,
            mimetype="application/zip",
        )

    except Exception as e:
        logger.error(f"Failed to download batch results {batch_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Error handlers
@batch_bp.errorhandler(413)
def file_too_large(error):
    """Handle file too large error."""
    return (
        jsonify(
            {"success": False, "error": "File too large. Maximum file size is 500MB."}
        ),
        413,
    )


@batch_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request error."""
    return jsonify({"success": False, "error": "Bad request"}), 400


def get_batch_routes_info() -> Dict[str, Any]:
    """Get information about available batch processing routes."""
    return {
        "endpoints": [
            {
                "path": "/api/batch/create",
                "method": "POST",
                "description": "Create a new batch processing session",
                "parameters": {
                    "name": "Optional batch name",
                    "max_concurrent": "Maximum concurrent jobs (1-5)",
                },
            },
            {
                "path": "/api/batch/add-video",
                "method": "POST",
                "description": "Add a video file to an existing batch",
                "parameters": {
                    "file": "Video file (multipart/form-data)",
                    "batch_id": "Batch ID to add video to",
                    "session_name": "Optional session name for the video",
                },
            },
            {
                "path": "/api/batch/<batch_id>/start",
                "method": "POST",
                "description": "Start processing a batch",
            },
            {
                "path": "/api/batch/<batch_id>",
                "method": "GET",
                "description": "Get batch details and progress",
            },
            {
                "path": "/api/batch/list",
                "method": "GET",
                "description": "List all batches with summary information",
            },
            {
                "path": "/api/batch/<batch_id>/cancel",
                "method": "POST",
                "description": "Cancel a batch",
            },
            {
                "path": "/api/batch/<batch_id>",
                "method": "DELETE",
                "description": "Delete a batch and its metadata",
            },
            {
                "path": "/api/batch/<batch_id>/results",
                "method": "GET",
                "description": "Get results from all completed jobs in a batch",
            },
            {
                "path": "/api/batch/<batch_id>/download",
                "method": "GET",
                "description": "Download all batch results as a ZIP file",
            },
        ],
        "features": [
            "Concurrent processing with configurable limits",
            "Real-time progress tracking",
            "Individual job status monitoring",
            "Batch result aggregation",
            "ZIP download of all results",
            "Resource-aware scheduling",
        ],
    }
