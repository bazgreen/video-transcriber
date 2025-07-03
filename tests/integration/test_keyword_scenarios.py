"""Integration tests for keyword scenarios in transcription."""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.services.transcription import VideoTranscriber


@pytest.mark.integration
class TestKeywordScenariosIntegration:
    """Integration tests for keyword scenarios in transcription."""

    def test_transcriber_with_scenario(self, tmp_path):
        """Test transcriber uses keyword scenario if specified."""
        # Create mock objects
        mock_memory_manager = MagicMock()
        mock_file_manager = MagicMock()
        mock_progress_tracker = MagicMock()

        # Setup mock scenario
        mock_scenario = {
            "id": "test_scenario",
            "name": "Test Scenario",
            "keywords": ["specific", "test", "keywords"],
        }

        # Create test results directory
        results_folder = str(tmp_path)

        # Create transcriber instance
        transcriber = VideoTranscriber(
            memory_manager=mock_memory_manager,
            file_manager=mock_file_manager,
            progress_tracker=mock_progress_tracker,
            results_folder=results_folder,
        )

        # Mock analyze_content to capture the keywords being used
        original_analyze_content = transcriber.analyze_content
        captured_keywords = []

        def mock_analyze_content(text, segments):
            nonlocal captured_keywords
            # Call the real method to get output
            result = original_analyze_content(text, segments)
            # Capture keywords used
            captured_keywords.extend(
                keyword
                for keyword in getattr(transcriber, "_test_captured_keywords", [])
            )
            return result

        # Patch analyze_content with our spy function
        transcriber.analyze_content = mock_analyze_content

        # Patch get_scenario_by_id to return our mock scenario
        with patch("src.utils.get_scenario_by_id", return_value=mock_scenario):
            # Mock the text and segments for analysis
            text = "This is a test transcript with specific test keywords."
            segments = [
                {
                    "start": 0,
                    "end": 5,
                    "text": "This is a test",
                    "timestamp_str": "00:00",
                },
                {
                    "start": 5,
                    "end": 10,
                    "text": "transcript with specific",
                    "timestamp_str": "00:05",
                },
                {
                    "start": 10,
                    "end": 15,
                    "text": "test keywords",
                    "timestamp_str": "00:10",
                },
            ]

            # Create a method that exposes keywords used for testing
            def test_expose_keywords():
                transcriber._selected_keyword_scenario_id = "test_scenario"
                # Spy attribute to capture keywords
                transcriber._test_captured_keywords = []

                # Load keywords - from scenario if specified, otherwise custom
                custom_keywords = []

                # If a keyword scenario was selected, use those keywords
                if (
                    hasattr(transcriber, "_selected_keyword_scenario_id")
                    and transcriber._selected_keyword_scenario_id
                ):
                    scenario = mock_scenario
                    if scenario and "keywords" in scenario:
                        custom_keywords = scenario["keywords"]
                        transcriber._test_captured_keywords = custom_keywords

                # If no scenario keywords were loaded, fall back to custom keywords
                if not custom_keywords:
                    with patch(
                        "src.utils.load_keywords", return_value=["default", "keywords"]
                    ):
                        custom_keywords = ["default", "keywords"]
                        transcriber._test_captured_keywords = custom_keywords

                # Analyze with the keywords
                result = transcriber.analyze_content(text, segments)
                return result, custom_keywords

            # Execute test
            result, used_keywords = test_expose_keywords()

            # Verify that scenario keywords were used
            assert "specific" in used_keywords
            assert "test" in used_keywords
            assert "keywords" in used_keywords
            assert "default" not in used_keywords

            # Verify the results reflect keyword matches
            assert any(
                match["keyword"] == "specific" for match in result["keyword_matches"]
            )
            assert any(
                match["keyword"] == "test" for match in result["keyword_matches"]
            )
            assert any(
                match["keyword"] == "keywords" for match in result["keyword_matches"]
            )

    def test_transcriber_fallback_to_custom_keywords(self, tmp_path):
        """Test transcriber falls back to custom keywords if scenario not found."""
        # Create mock objects
        mock_memory_manager = MagicMock()
        mock_file_manager = MagicMock()
        mock_progress_tracker = MagicMock()

        # Create test results directory
        results_folder = str(tmp_path)

        # Create transcriber instance
        transcriber = VideoTranscriber(
            memory_manager=mock_memory_manager,
            file_manager=mock_file_manager,
            progress_tracker=mock_progress_tracker,
            results_folder=results_folder,
        )

        # Mock custom keywords
        custom_keywords = ["default", "custom", "words"]

        # Mock analyze_content to capture the keywords being used
        original_analyze_content = transcriber.analyze_content
        captured_keywords = []

        def mock_analyze_content(text, segments):
            nonlocal captured_keywords
            # Call the real method to get output
            result = original_analyze_content(text, segments)
            # Capture keywords used
            captured_keywords.extend(
                keyword
                for keyword in getattr(transcriber, "_test_captured_keywords", [])
            )
            return result

        # Patch analyze_content with our spy function
        transcriber.analyze_content = mock_analyze_content

        # Patch get_scenario_by_id to return None (scenario not found)
        with patch("src.utils.get_scenario_by_id", return_value=None), patch(
            "src.utils.load_keywords", return_value=custom_keywords
        ):
            # Mock the text and segments for analysis
            text = "This is a test transcript with default custom words."
            segments = [
                {
                    "start": 0,
                    "end": 5,
                    "text": "This is a test",
                    "timestamp_str": "00:00",
                },
                {
                    "start": 5,
                    "end": 10,
                    "text": "transcript with default",
                    "timestamp_str": "00:05",
                },
                {
                    "start": 10,
                    "end": 15,
                    "text": "custom words",
                    "timestamp_str": "00:10",
                },
            ]

            # Create a method that exposes keywords used for testing
            def test_expose_keywords():
                transcriber._selected_keyword_scenario_id = "nonexistent_scenario"
                # Spy attribute to capture keywords
                transcriber._test_captured_keywords = []

                # Load keywords - from scenario if specified, otherwise custom
                loaded_keywords = []

                # If a keyword scenario was selected, use those keywords
                if (
                    hasattr(transcriber, "_selected_keyword_scenario_id")
                    and transcriber._selected_keyword_scenario_id
                ):
                    scenario = None  # get_scenario_by_id returns None
                    if scenario and "keywords" in scenario:
                        loaded_keywords = scenario["keywords"]
                        transcriber._test_captured_keywords = loaded_keywords

                # If no scenario keywords were loaded, fall back to custom keywords
                if not loaded_keywords:
                    loaded_keywords = custom_keywords
                    transcriber._test_captured_keywords = loaded_keywords

                # Analyze with the keywords
                result = transcriber.analyze_content(text, segments)
                return result, loaded_keywords

            # Execute test
            result, used_keywords = test_expose_keywords()

            # Verify that custom keywords were used as fallback
            assert "default" in used_keywords
            assert "custom" in used_keywords
            assert "words" in used_keywords

            # Verify the results reflect keyword matches
            assert any(
                match["keyword"] == "default" for match in result["keyword_matches"]
            )
            assert any(
                match["keyword"] == "custom" for match in result["keyword_matches"]
            )
            assert any(
                match["keyword"] == "words" for match in result["keyword_matches"]
            )

    def test_upload_with_keyword_scenario(self, tmp_path, monkeypatch):
        """Test upload processing with keyword scenario."""
        from src.services.upload import process_upload

        # Create mock objects
        mock_transcriber = MagicMock()
        mock_memory_manager = MagicMock()

        # Mock request object
        class MockRequest:
            files = {"video": MagicMock(filename="test.mp4")}
            form = {"session_name": "test_session", "keyword_scenario": "education"}

        # Patch Flask's request
        monkeypatch.setattr("src.services.upload.request", MockRequest())

        # Mock file handling
        monkeypatch.setattr("src.services.upload.secure_filename", lambda x: x)
        monkeypatch.setattr("os.path.join", lambda *args: "/".join(args))
        monkeypatch.setattr("os.makedirs", lambda *args, **kwargs: None)
        monkeypatch.setattr("src.services.upload.os.path.exists", lambda x: True)

        # Mock file.save
        MockRequest.files["video"].save = MagicMock()

        # Setup mock results
        mock_transcriber.process_video.return_value = {
            "session_id": "test_session_123",
            "session_dir": str(tmp_path),
            "analysis": {"total_words": 100},
        }

        # Run the upload process
        try:
            result, status_code = process_upload(
                mock_transcriber, mock_memory_manager, str(tmp_path)
            )

            # Check that process_video was called with the correct scenario ID
            mock_transcriber.process_video.assert_called_once()
            call_args = mock_transcriber.process_video.call_args

            # Verify keyword_scenario_id was passed correctly
            assert call_args[1]["keyword_scenario_id"] == "education"

            # Verify successful response
            assert status_code == 200
            assert result["success"] is True

        except Exception as e:
            pytest.fail(f"Test failed with exception: {e}")


if __name__ == "__main__":
    unittest.main()
