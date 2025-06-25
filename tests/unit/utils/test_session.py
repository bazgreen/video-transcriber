"""
Unit tests for session utility functions.

Tests the session management utilities including validation,
metadata loading, and security checks.
"""

import json
import os
import tempfile
from unittest.mock import mock_open, patch

import pytest

from src.models.exceptions import UserFriendlyError
from src.utils.session import (
    ensure_session_exists,
    get_session_list,
    validate_session_access,
    validate_session_for_socket,
)


class TestValidateSessionAccess:
    """Test session access validation."""

    @pytest.mark.unit
    def test_valid_session_id(self, test_directories):
        """Test validation with valid session ID."""
        session_id = "valid_session_123"
        results_folder = test_directories["results"]

        result = validate_session_access(session_id, results_folder)
        expected_path = os.path.join(results_folder, session_id)
        assert result == expected_path

    @pytest.mark.unit
    def test_invalid_session_id_format(self, test_directories):
        """Test validation with invalid session ID format."""
        invalid_ids = [
            "../malicious",
            "session with spaces",
            "session/with/slashes",
            "session\\with\\backslashes",
            "",
            None,
        ]

        results_folder = test_directories["results"]

        for invalid_id in invalid_ids:
            with pytest.raises(UserFriendlyError, match="Invalid session ID"):
                validate_session_access(invalid_id, results_folder)

    @pytest.mark.unit
    def test_path_traversal_protection(self, test_directories):
        """Test protection against path traversal attacks."""
        malicious_ids = [
            "../../etc/passwd",
            "..%2F..%2Fetc%2Fpasswd",
            "../../../root",
        ]

        results_folder = test_directories["results"]

        for malicious_id in malicious_ids:
            with pytest.raises(UserFriendlyError):
                validate_session_access(malicious_id, results_folder)

    @pytest.mark.unit
    def test_default_results_folder(self):
        """Test using default results folder from config."""
        session_id = "test_session"

        with patch("src.utils.session.config") as mock_config:
            mock_config.RESULTS_FOLDER = "/default/results"

            result = validate_session_access(session_id)
            expected_path = os.path.join("/default/results", session_id)
            assert result == expected_path


class TestEnsureSessionExists:
    """Test session existence validation with metadata loading."""

    @pytest.mark.unit
    def test_existing_session_with_metadata(
        self, test_directories, sample_session_metadata
    ):
        """Test with existing session that has metadata file."""
        session_id = "existing_session"
        results_folder = test_directories["results"]
        session_dir = os.path.join(results_folder, session_id)
        os.makedirs(session_dir)

        # Create metadata file
        metadata_file = os.path.join(session_dir, "metadata.json")
        with open(metadata_file, "w") as f:
            json.dump(sample_session_metadata, f)

        session_path, metadata = ensure_session_exists(session_id, results_folder)

        assert session_path == session_dir
        assert metadata == sample_session_metadata

    @pytest.mark.unit
    def test_existing_session_without_metadata(self, test_directories):
        """Test with existing session that lacks metadata file."""
        session_id = "legacy_session_20231225_143000"
        results_folder = test_directories["results"]
        session_dir = os.path.join(results_folder, session_id)
        os.makedirs(session_dir)

        session_path, metadata = ensure_session_exists(session_id, results_folder)

        assert session_path == session_dir
        assert metadata["session_id"] == session_id
        assert metadata["session_name"] == "legacy_session"
        assert metadata["status"] == "completed"

    @pytest.mark.unit
    def test_nonexistent_session(self, test_directories):
        """Test with nonexistent session."""
        session_id = "nonexistent_session"
        results_folder = test_directories["results"]

        with pytest.raises(
            UserFriendlyError, match="Session 'nonexistent_session' not found"
        ):
            ensure_session_exists(session_id, results_folder)

    @pytest.mark.unit
    def test_corrupted_metadata_file(self, test_directories):
        """Test with corrupted metadata file."""
        session_id = "corrupted_session"
        results_folder = test_directories["results"]
        session_dir = os.path.join(results_folder, session_id)
        os.makedirs(session_dir)

        # Create corrupted metadata file
        metadata_file = os.path.join(session_dir, "metadata.json")
        with open(metadata_file, "w") as f:
            f.write("invalid json content")

        session_path, metadata = ensure_session_exists(session_id, results_folder)

        # Should fall back to parsing from folder name
        assert session_path == session_dir
        assert metadata["session_id"] == session_id


class TestValidateSessionForSocket:
    """Test socket session validation."""

    @pytest.mark.unit
    def test_valid_socket_session_ids(self):
        """Test validation of valid session IDs for sockets."""
        valid_ids = [
            "session123",
            "session_123",
            "session-123",
            "Session_123-Test",
            "a",
            "123",
        ]

        for valid_id in valid_ids:
            assert validate_session_for_socket(valid_id) is True

    @pytest.mark.unit
    def test_invalid_socket_session_ids(self):
        """Test validation of invalid session IDs for sockets."""
        invalid_ids = [
            "",
            None,
            "session with spaces",
            "session/slash",
            "session\\backslash",
            "session.dot",
            "session@symbol",
            "../traversal",
        ]

        for invalid_id in invalid_ids:
            assert validate_session_for_socket(invalid_id) is False


class TestGetSessionList:
    """Test session list retrieval."""

    @pytest.mark.unit
    def test_empty_results_folder(self, test_directories):
        """Test with empty results folder."""
        results_folder = test_directories["results"]
        sessions = get_session_list(results_folder)
        assert sessions == []

    @pytest.mark.unit
    def test_nonexistent_results_folder(self, temp_directory):
        """Test with nonexistent results folder."""
        nonexistent_folder = os.path.join(temp_directory, "nonexistent")
        sessions = get_session_list(nonexistent_folder)
        assert sessions == []
        # Should create the folder
        assert os.path.exists(nonexistent_folder)

    @pytest.mark.unit
    def test_multiple_sessions_with_metadata(self, test_directories):
        """Test with multiple sessions containing metadata."""
        results_folder = test_directories["results"]

        # Create multiple test sessions
        session_data = [
            {
                "id": "session1",
                "name": "First Session",
                "created_at": "2024-01-01T10:00:00",
            },
            {
                "id": "session2",
                "name": "Second Session",
                "created_at": "2024-01-01T11:00:00",
            },
            {
                "id": "session3",
                "name": "Third Session",
                "created_at": "2024-01-01T09:00:00",
            },
        ]

        for data in session_data:
            session_dir = os.path.join(results_folder, data["id"])
            os.makedirs(session_dir)

            metadata = {
                "session_id": data["id"],
                "session_name": data["name"],
                "created_at": data["created_at"],
                "status": "completed",
            }

            metadata_file = os.path.join(session_dir, "metadata.json")
            with open(metadata_file, "w") as f:
                json.dump(metadata, f)

        sessions = get_session_list(results_folder)

        assert len(sessions) == 3
        # Should be sorted by creation time (newest first)
        assert sessions[0]["session_id"] == "session2"  # 11:00:00
        assert sessions[1]["session_id"] == "session1"  # 10:00:00
        assert sessions[2]["session_id"] == "session3"  # 09:00:00

    @pytest.mark.unit
    def test_sessions_with_files_not_directories(self, test_directories):
        """Test handling of files in results folder (should ignore them)."""
        results_folder = test_directories["results"]

        # Create a regular file in results folder
        file_path = os.path.join(results_folder, "not_a_session.txt")
        with open(file_path, "w") as f:
            f.write("This is not a session directory")

        # Create a valid session
        session_dir = os.path.join(results_folder, "valid_session")
        os.makedirs(session_dir)

        sessions = get_session_list(results_folder)

        # Should only return the valid session, ignoring the file
        assert len(sessions) == 1
        assert sessions[0]["session_id"] == "valid_session"

    @pytest.mark.unit
    def test_session_with_metadata_loading_error(self, test_directories):
        """Test handling of sessions with metadata loading errors."""
        results_folder = test_directories["results"]
        session_id = "error_session"
        session_dir = os.path.join(results_folder, session_id)
        os.makedirs(session_dir)

        # Mock the load_session_metadata to raise an exception
        with patch("src.utils.session.load_session_metadata") as mock_load:
            mock_load.side_effect = Exception("Metadata loading error")

            sessions = get_session_list(results_folder)

            # Should handle the error gracefully and return empty list
            assert sessions == []

    @pytest.mark.unit
    def test_default_results_folder_in_get_session_list(self):
        """Test using default results folder in get_session_list."""
        with patch("src.utils.session.config") as mock_config:
            mock_config.RESULTS_FOLDER = "/default/results"

            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = False

                with patch("os.makedirs") as mock_makedirs:
                    with patch("os.listdir") as mock_listdir:
                        mock_listdir.return_value = []

                        sessions = get_session_list()

                        mock_makedirs.assert_called_once_with("/default/results")
                        assert sessions == []
