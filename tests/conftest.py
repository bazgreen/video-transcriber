"""
Pytest configuration and shared fixtures for video transcriber tests.

This module provides common test fixtures, configuration, and utilities
used across all test modules.
"""

import os
import shutil
import sys
import tempfile
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, Mock

import pytest
from flask import Flask
from flask.testing import FlaskClient

# Import our application components first
from src.config import AnalysisConfig, AppConfig, MemoryConfig, VideoConfig
from src.models import MemoryManager, ModelManager, ProgressiveFileManager
from src.models.progress import ProgressTracker
from src.services.transcription import VideoTranscriber
from src.utils.memory import get_memory_status_safe
from src.utils.session import validate_session_access
from src.utils.validation import validate_file_upload

# Mock whisper module to avoid installation issues in tests
mock_whisper = MagicMock()
mock_whisper.load_model = Mock(return_value=Mock())
sys.modules["whisper"] = mock_whisper


@pytest.fixture(scope="session")
def test_config() -> AppConfig:
    """Create test configuration with safe defaults."""
    config = AppConfig()
    # Override with test-safe values
    config.DEBUG = True
    config.MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB for tests
    config.MEMORY_PRESSURE_THRESHOLD = 95  # Higher threshold for tests
    return config


@pytest.fixture(scope="session")
def temp_directory() -> Generator[str, None, None]:
    """Create temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="video_transcriber_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def test_directories() -> Generator[Dict[str, str], None, None]:
    """Create test directory structure with fresh directories for each test."""
    temp_dir = tempfile.mkdtemp(prefix="video_transcriber_test_")
    dirs = {
        "uploads": os.path.join(temp_dir, "uploads"),
        "results": os.path.join(temp_dir, "results"),
        "config": os.path.join(temp_dir, "config"),
        "logs": os.path.join(temp_dir, "logs"),
    }

    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)

    yield dirs
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_memory_manager() -> Mock:
    """Create mock memory manager for testing."""
    mock_manager = Mock(spec=MemoryManager)
    mock_manager.get_memory_info.return_value = {
        "system_total_gb": 16.0,
        "system_available_gb": 8.0,
        "system_used_percent": 50.0,
        "process_rss_mb": 100.0,
        "process_vms_mb": 200.0,
        "available": True,
    }
    mock_manager.get_optimal_workers.return_value = 4
    mock_manager.check_memory_pressure.return_value = False
    return mock_manager


@pytest.fixture
def mock_file_manager() -> Mock:
    """Create mock file manager for testing."""
    mock_manager = Mock(spec=ProgressiveFileManager)
    mock_manager.get_cleanup_stats.return_value = {
        "count": 0,
        "total_size_mb": 0.0,
        "types": {},
    }
    return mock_manager


@pytest.fixture
def mock_progress_tracker() -> Mock:
    """Create mock progress tracker for testing."""
    mock_tracker = Mock(spec=ProgressTracker)
    mock_tracker.sessions = {}
    mock_tracker.get_session_progress.return_value = None
    return mock_tracker


@pytest.fixture
def mock_model_manager() -> Mock:
    """Create mock model manager for testing."""
    mock_manager = Mock(spec=ModelManager)
    mock_model = Mock()
    mock_model.transcribe.return_value = {
        "text": "This is a test transcription.",
        "segments": [
            {"start": 0.0, "end": 5.0, "text": "This is a test transcription."}
        ],
    }
    mock_manager.get_model.return_value = mock_model
    return mock_manager


@pytest.fixture
def mock_whisper_model() -> Mock:
    """Create mock Whisper model for testing."""
    mock_model = Mock()
    mock_model.transcribe.return_value = {
        "text": "Hello world test transcription",
        "segments": [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "Hello world",
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "test transcription",
            },
        ],
    }
    return mock_model


@pytest.fixture
def sample_video_data() -> bytes:
    """Generate sample video data for testing."""
    # Create minimal valid MP4 header for testing
    return b"\x00\x00\x00\x20ftypmp41\x00\x00\x00\x00mp41isom" + b"\x00" * 100


@pytest.fixture
def sample_audio_data() -> bytes:
    """Generate sample audio data for testing."""
    # Create minimal valid WAV header for testing
    return (
        b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00"
        b"\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00"
        b"\x02\x00\x10\x00data\x00\x08\x00\x00"
    ) + b"\x00" * 100


@pytest.fixture
def sample_session_metadata() -> Dict[str, Any]:
    """Generate sample session metadata for testing."""
    return {
        "session_id": "test_session_123",
        "session_name": "Test Session",
        "original_filename": "test_video.mp4",
        "created_at": "2024-01-01T12:00:00",
        "status": "completed",
        "processing_time": 45.2,
        "video_duration": 120.0,
        "file_size_mb": 25.5,
    }


@pytest.fixture
def sample_transcription_result() -> Dict[str, Any]:
    """Generate sample transcription result for testing."""
    return {
        "text": "This is a sample transcription for testing purposes.",
        "segments": [
            {
                "start": 0.0,
                "end": 3.0,
                "text": "This is a sample transcription",
                "timestamp_str": "00:00:00",
            },
            {
                "start": 3.0,
                "end": 6.0,
                "text": "for testing purposes.",
                "timestamp_str": "00:00:03",
            },
        ],
        "analysis": {
            "keyword_matches": [],
            "questions": [],
            "emphasis_cues": [],
            "keyword_frequency": {},
            "total_words": 8,
        },
    }


@pytest.fixture
def flask_app(test_config: AppConfig, test_directories: Dict[str, str]) -> Flask:
    """Create Flask app for testing."""
    # Import main app creation function and other dependencies
    from main import (
        create_app,
        create_transcriber,
        initialize_managers,
        register_routes,
    )

    # Override config paths with test directories
    test_config.UPLOAD_FOLDER = test_directories["uploads"]
    test_config.RESULTS_FOLDER = test_directories["results"]

    # Create app and socketio
    app, socketio = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    # Initialize managers for full functionality
    memory_manager, file_manager, progress_tracker = initialize_managers(socketio)

    # Create transcriber
    transcriber = create_transcriber(
        memory_manager, file_manager, progress_tracker, test_directories["results"]
    )

    # Register all routes (this includes the API routes)
    register_routes(
        app,
        socketio,
        transcriber,
        memory_manager,
        file_manager,
        progress_tracker,
        test_config,
    )

    return app


@pytest.fixture
def client(flask_app: Flask) -> FlaskClient:
    """Create test client for Flask app."""
    return flask_app.test_client()


@pytest.fixture
def runner(flask_app: Flask):
    """Create test CLI runner."""
    return flask_app.test_cli_runner()


# Performance testing fixtures
@pytest.fixture
def performance_test_data() -> Dict[str, Any]:
    """Generate data for performance testing."""
    return {
        "small_video_size": 1024 * 1024,  # 1MB
        "medium_video_size": 10 * 1024 * 1024,  # 10MB
        "large_video_size": 50 * 1024 * 1024,  # 50MB
        "expected_processing_time": {
            "small": 5.0,  # seconds
            "medium": 30.0,
            "large": 120.0,
        },
    }


# Utility functions for tests
def create_test_file(directory: str, filename: str, content: bytes) -> str:
    """Helper function to create test files."""
    file_path = os.path.join(directory, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path


def assert_valid_session_id(session_id: str) -> None:
    """Helper function to validate session IDs in tests."""
    assert session_id is not None
    assert len(session_id) > 0
    assert all(c.isalnum() or c in "_-" for c in session_id)


def assert_valid_file_structure(directory: str, expected_files: list) -> None:
    """Helper function to validate file structure in tests."""
    actual_files = os.listdir(directory)
    for expected_file in expected_files:
        assert expected_file in actual_files, f"Expected file {expected_file} not found"


# Mark slow tests
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "requires_model: mark test as requiring Whisper model"
    )
    config.addinivalue_line("markers", "requires_ffmpeg: mark test as requiring FFmpeg")
