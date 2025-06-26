"""
Unit tests for validation utility functions.

Tests the validation utilities including request validation,
file upload validation, and data sanitization functions.
"""

from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

import pytest
from werkzeug.datastructures import FileStorage

from src.models.exceptions import UserFriendlyError
from src.utils.validation import (
    validate_boolean_param,
    validate_file_upload,
    validate_keyword_list,
    validate_numeric_range,
    validate_request_data,
    validate_session_name,
)


class TestValidateRequestData:
    """Test request data validation."""

    @pytest.mark.unit
    def test_valid_request_data(self):
        """Test validation with valid request data."""
        data = {"name": "test", "value": 123, "enabled": True}
        required_fields = ["name", "value"]

        # Should not raise any exception
        validate_request_data(data, required_fields)

    @pytest.mark.unit
    def test_none_request_data(self):
        """Test validation with None data."""
        with pytest.raises(
            UserFriendlyError, match="Invalid request: JSON data is required"
        ):
            validate_request_data(None, ["field1"])

    @pytest.mark.unit
    def test_empty_request_data(self):
        """Test validation with empty data."""
        with pytest.raises(
            UserFriendlyError, match="Invalid request: JSON data is required"
        ):
            validate_request_data({}, ["field1"])

    @pytest.mark.unit
    def test_missing_single_field(self):
        """Test validation with single missing field."""
        data = {"field1": "value1"}
        required_fields = ["field1", "field2"]

        with pytest.raises(UserFriendlyError) as exc_info:
            validate_request_data(data, required_fields)

        error_msg = str(exc_info.value)
        assert "missing required field(s): 'field2'" in error_msg

    @pytest.mark.unit
    def test_missing_multiple_fields(self):
        """Test validation with multiple missing fields."""
        data = {"field1": "value1"}
        required_fields = ["field1", "field2", "field3"]

        with pytest.raises(UserFriendlyError) as exc_info:
            validate_request_data(data, required_fields)

        error_msg = str(exc_info.value)
        assert "missing required field(s): 'field2', 'field3'" in error_msg

    @pytest.mark.unit
    def test_empty_required_fields_list(self):
        """Test validation with empty required fields list."""
        data = {"field1": "value1"}

        # Should not raise any exception
        validate_request_data(data, [])


class TestValidateFileUpload:
    """Test file upload validation."""

    def create_mock_file(self, filename: str, content: bytes, size: int = None):
        """Helper to create mock file upload."""
        if size is None:
            size = len(content)

        mock_file = Mock(spec=FileStorage)
        mock_file.filename = filename
        mock_file.seek = Mock()
        mock_file.tell = Mock(return_value=size)
        return mock_file

    @pytest.mark.unit
    def test_valid_file_upload(self):
        """Test validation with valid file upload."""
        content = b"test video content"
        mock_file = self.create_mock_file("test.mp4", content)

        result = validate_file_upload(mock_file)

        assert result["filename"] == "test.mp4"
        assert result["extension"] == ".mp4"
        assert result["size_bytes"] == len(content)

        # Verify seek was called twice: once to get file size, once to reset
        assert mock_file.seek.call_count == 2
        mock_file.seek.assert_any_call(0, 2)  # SEEK_END
        mock_file.seek.assert_called_with(0)  # Reset to beginning
        mock_file.tell.assert_called()

    @pytest.mark.unit
    def test_no_file_selected(self):
        """Test validation with no file selected."""
        mock_file = Mock(spec=FileStorage)
        mock_file.filename = ""

        with pytest.raises(UserFriendlyError, match="No file selected"):
            validate_file_upload(mock_file)

    @pytest.mark.unit
    def test_none_file(self):
        """Test validation with None file."""
        with pytest.raises(UserFriendlyError, match="No file selected"):
            validate_file_upload(None)

    @pytest.mark.unit
    def test_invalid_file_extension(self):
        """Test validation with invalid file extension."""
        mock_file = self.create_mock_file("test.txt", b"content")
        allowed_extensions = {".mp4", ".avi", ".mov"}

        with pytest.raises(UserFriendlyError) as exc_info:
            validate_file_upload(mock_file, allowed_extensions)

        error_msg = str(exc_info.value)
        assert "Unsupported file format: '.txt'" in error_msg
        assert "'.avi', '.mov', '.mp4'" in error_msg

    @pytest.mark.unit
    def test_file_too_large(self):
        """Test validation with file that's too large."""
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        mock_file = self.create_mock_file("large.mp4", large_content)
        max_size = 5 * 1024 * 1024  # 5MB limit

        with pytest.raises(UserFriendlyError) as exc_info:
            validate_file_upload(mock_file, max_size_bytes=max_size)

        error_msg = str(exc_info.value)
        assert "File too large: 10.0MB" in error_msg
        assert "Maximum allowed: 5MB" in error_msg

    @pytest.mark.unit
    def test_custom_allowed_extensions(self):
        """Test validation with custom allowed extensions."""
        mock_file = self.create_mock_file("test.webm", b"content")
        custom_extensions = {".webm", ".mkv"}

        result = validate_file_upload(mock_file, custom_extensions)
        assert result["extension"] == ".webm"

    @pytest.mark.unit
    def test_case_insensitive_extension(self):
        """Test validation with uppercase file extension."""
        mock_file = self.create_mock_file("test.MP4", b"content")

        result = validate_file_upload(mock_file)
        assert result["extension"] == ".mp4"  # Should be normalized to lowercase


class TestValidateSessionName:
    """Test session name validation and sanitization."""

    @pytest.mark.unit
    def test_valid_session_name(self):
        """Test validation with valid session name."""
        valid_names = [
            "My Session",
            "session_123",
            "Session-Test",
            "Simple",
            "Test Session 123",
        ]

        for name in valid_names:
            result = validate_session_name(name)
            assert len(result) > 0
            assert result.replace("_", "").replace("-", "").replace(" ", "").isalnum()

    @pytest.mark.unit
    def test_empty_session_name(self):
        """Test validation with empty session name."""
        empty_names = ["", "   ", None]

        for name in empty_names:
            with pytest.raises(UserFriendlyError, match="Session name is required"):
                validate_session_name(name)

    @pytest.mark.unit
    def test_session_name_sanitization(self):
        """Test sanitization of problematic characters."""
        test_cases = [
            ("Session@#$%^&*()", "Session_"),
            ("Session with / slashes", "Session_with_slashes"),
            ("Session\\with\\backslashes", "Session_with_backslashes"),
            ("Session...dots", "Session_dots"),
            ("Session   multiple   spaces", "Session_multiple_spaces"),
            ("___Session___", "Session"),
        ]

        for input_name, expected_pattern in test_cases:
            result = validate_session_name(input_name)
            # Check that problematic characters are replaced
            assert not any(c in result for c in "@#$%^&*()/\\.")

    @pytest.mark.unit
    def test_session_name_length_limit(self):
        """Test session name length limiting."""
        long_name = "a" * 100  # 100 characters

        with patch("src.utils.validation.config") as mock_config:
            mock_config.MAX_SESSION_NAME_LENGTH = 50

            result = validate_session_name(long_name)
            assert len(result) == 50

    @pytest.mark.unit
    def test_session_name_only_invalid_characters(self):
        """Test session name with only invalid characters."""
        with pytest.raises(
            UserFriendlyError, match="Session name contains only invalid characters"
        ):
            validate_session_name("@#$%^&*()")


class TestValidateNumericRange:
    """Test numeric range validation."""

    @pytest.mark.unit
    def test_valid_integer_in_range(self):
        """Test validation with valid integer in range."""
        result = validate_numeric_range(5, "test_field", 1, 10, int)
        assert result == 5
        assert isinstance(result, int)

    @pytest.mark.unit
    def test_valid_float_in_range(self):
        """Test validation with valid float in range."""
        result = validate_numeric_range(3.5, "test_field", 1.0, 10.0, float)
        assert result == 3.5
        assert isinstance(result, float)

    @pytest.mark.unit
    def test_non_numeric_value(self):
        """Test validation with non-numeric value."""
        with pytest.raises(UserFriendlyError) as exc_info:
            validate_numeric_range("not_a_number", "test_field")

        assert "test_field must be a number" in str(exc_info.value)

    @pytest.mark.unit
    def test_value_below_minimum(self):
        """Test validation with value below minimum."""
        with pytest.raises(UserFriendlyError) as exc_info:
            validate_numeric_range(0, "count", min_value=1, max_value=10)

        error_msg = str(exc_info.value)
        assert "count must be >= 1" in error_msg
        assert "got: 0" in error_msg

    @pytest.mark.unit
    def test_value_above_maximum(self):
        """Test validation with value above maximum."""
        with pytest.raises(UserFriendlyError) as exc_info:
            validate_numeric_range(15, "count", min_value=1, max_value=10)

        error_msg = str(exc_info.value)
        assert "count must be <= 10" in error_msg
        assert "got: 15" in error_msg

    @pytest.mark.unit
    def test_no_range_limits(self):
        """Test validation without range limits."""
        result = validate_numeric_range(-100, "unlimited_field")
        assert result == -100

    @pytest.mark.unit
    def test_type_conversion(self):
        """Test type conversion during validation."""
        # Float to int conversion
        result = validate_numeric_range(5.7, "int_field", value_type=int)
        assert result == 5
        assert isinstance(result, int)

        # Int to float conversion
        result = validate_numeric_range(5, "float_field", value_type=float)
        assert result == 5.0
        assert isinstance(result, float)


class TestValidateKeywordList:
    """Test keyword list validation."""

    @pytest.mark.unit
    def test_valid_keyword_list(self):
        """Test validation with valid keyword list."""
        keywords = ["python", "programming", "test", "validation"]
        result = validate_keyword_list(keywords)
        assert result == keywords

    @pytest.mark.unit
    def test_non_list_input(self):
        """Test validation with non-list input."""
        with pytest.raises(
            UserFriendlyError, match="Keywords must be provided as a list"
        ):
            validate_keyword_list("not a list")

    @pytest.mark.unit
    def test_keyword_list_with_invalid_items(self):
        """Test validation with invalid items in list."""
        keywords = [
            "valid",
            "",
            "   ",
            None,
            123,
            "another_valid",
            "x",
        ]  # "x" is too short
        result = validate_keyword_list(keywords)

        # Should only include valid keywords (length >= 2)
        assert "valid" in result
        assert "another_valid" in result
        assert "" not in result
        assert None not in result
        assert 123 not in result
        assert "x" not in result

    @pytest.mark.unit
    def test_keyword_list_with_whitespace(self):
        """Test validation with keywords containing whitespace."""
        keywords = ["  python  ", "programming", "  test  "]
        result = validate_keyword_list(keywords)

        # Should strip whitespace
        assert "python" in result
        assert "programming" in result
        assert "test" in result
        assert "  python  " not in result

    @pytest.mark.unit
    def test_empty_keyword_list(self):
        """Test validation with empty keyword list."""
        result = validate_keyword_list([])
        assert result == []

    @pytest.mark.unit
    def test_keyword_list_all_invalid(self):
        """Test validation where all keywords are invalid."""
        keywords = ["", "   ", None, 123, "x"]
        result = validate_keyword_list(keywords)
        assert result == []


class TestValidateBooleanParam:
    """Test boolean parameter validation."""

    @pytest.mark.unit
    def test_boolean_values(self):
        """Test validation with actual boolean values."""
        assert validate_boolean_param(True, "test_field") is True
        assert validate_boolean_param(False, "test_field") is False

    @pytest.mark.unit
    def test_string_true_values(self):
        """Test validation with string values that should be True."""
        true_values = ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON"]

        for value in true_values:
            result = validate_boolean_param(value, "test_field")
            assert result is True, f"Failed for value: {value}"

    @pytest.mark.unit
    def test_string_false_values(self):
        """Test validation with string values that should be False."""
        false_values = ["false", "FALSE", "False", "0", "no", "NO", "off", "OFF"]

        for value in false_values:
            result = validate_boolean_param(value, "test_field")
            assert result is False, f"Failed for value: {value}"

    @pytest.mark.unit
    def test_none_value_with_default(self):
        """Test validation with None value and default."""
        assert validate_boolean_param(None, "test_field", default=True) is True
        assert validate_boolean_param(None, "test_field", default=False) is False

    @pytest.mark.unit
    def test_invalid_string_values(self):
        """Test validation with invalid string values."""
        invalid_values = ["maybe", "invalid", "2", "-1", ""]

        for value in invalid_values:
            with pytest.raises(UserFriendlyError) as exc_info:
                validate_boolean_param(value, "test_field")

            error_msg = str(exc_info.value)
            assert "test_field must be a boolean value" in error_msg
            assert f"got: {value}" in error_msg

    @pytest.mark.unit
    def test_invalid_non_string_values(self):
        """Test validation with invalid non-string values."""
        invalid_values = [123, 1.5, [], {}]

        for value in invalid_values:
            with pytest.raises(UserFriendlyError) as exc_info:
                validate_boolean_param(value, "test_field")

            error_msg = str(exc_info.value)
            assert "test_field must be a boolean value" in error_msg
