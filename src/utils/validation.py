"""
Request validation utilities.

This module provides centralized validation functions for request data,
file uploads, and common input validation patterns.
"""

import os
import re
import logging
from typing import Dict, Any, List, Set, Optional, Union
from werkzeug.datastructures import FileStorage

from src.config import AppConfig, Constants
from src.models.exceptions import UserFriendlyError

logger = logging.getLogger(__name__)
config = AppConfig()


def validate_request_data(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate request data contains all required fields.
    
    Args:
        data: Request data dictionary
        required_fields: List of field names that must be present
        
    Raises:
        UserFriendlyError: If data is invalid or missing required fields
    """
    if not data:
        raise UserFriendlyError("Invalid request: JSON data is required")
    
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        field_list = "', '".join(missing_fields)
        raise UserFriendlyError(f"Invalid request: missing required field(s): '{field_list}'")


def validate_file_upload(
    file: FileStorage, 
    allowed_extensions: Optional[Set[str]] = None,
    max_size_bytes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate uploaded file meets requirements.
    
    Args:
        file: Uploaded file object
        allowed_extensions: Set of allowed file extensions (uses config default if None)
        max_size_bytes: Maximum file size in bytes (uses config default if None)
        
    Returns:
        Dictionary with file information (size_mb, extension, etc.)
        
    Raises:
        UserFriendlyError: If file is invalid
    """
    if not file or file.filename == '':
        raise UserFriendlyError('No file selected')
    
    # Use config defaults if not specified
    if allowed_extensions is None:
        allowed_extensions = config.ALLOWED_FILE_EXTENSIONS
    if max_size_bytes is None:
        max_size_bytes = config.MAX_FILE_SIZE_BYTES
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        ext_list = "', '".join(sorted(allowed_extensions))
        raise UserFriendlyError(
            f"Unsupported file format: '{file_ext}'. "
            f"Supported formats: '{ext_list}'"
        )
    
    # Validate file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    file_size_mb = file_size / Constants.BYTES_PER_MB
    if file_size > max_size_bytes:
        max_size_mb = max_size_bytes / Constants.BYTES_PER_MB
        raise UserFriendlyError(
            f"File too large: {file_size_mb:.1f}MB. "
            f"Maximum allowed: {max_size_mb:.0f}MB"
        )
    
    return {
        'size_bytes': file_size,
        'size_mb': file_size_mb,
        'extension': file_ext,
        'filename': file.filename
    }


def validate_session_name(session_name: str) -> str:
    """
    Validate and sanitize session name.
    
    Args:
        session_name: Raw session name from user input
        
    Returns:
        Sanitized session name
        
    Raises:
        UserFriendlyError: If session name is invalid
    """
    if not session_name or not session_name.strip():
        raise UserFriendlyError('Session name is required and cannot be empty')
    
    # Clean the session name
    session_name = session_name.strip()
    
    # Remove potentially problematic characters
    sanitized_name = re.sub(r'[^a-zA-Z0-9_\-\s]', '_', session_name)
    
    # Replace multiple spaces/underscores with single underscore
    sanitized_name = re.sub(r'[\s_]+', '_', sanitized_name)
    
    # Remove leading/trailing underscores
    sanitized_name = sanitized_name.strip('_')
    
    # Limit length
    if len(sanitized_name) > config.MAX_SESSION_NAME_LENGTH:
        sanitized_name = sanitized_name[:config.MAX_SESSION_NAME_LENGTH]
        logger.info(f"Session name truncated to {config.MAX_SESSION_NAME_LENGTH} characters")
    
    # Ensure we still have a valid name after sanitization
    if not sanitized_name:
        raise UserFriendlyError('Session name contains only invalid characters')
    
    return sanitized_name


def validate_numeric_range(
    value: Union[int, float], 
    field_name: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    value_type: type = int
) -> Union[int, float]:
    """
    Validate numeric value is within specified range.
    
    Args:
        value: Value to validate
        field_name: Name of the field (for error messages)
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)
        value_type: Expected type (int or float)
        
    Returns:
        Validated and converted value
        
    Raises:
        UserFriendlyError: If value is invalid or out of range
    """
    if not isinstance(value, (int, float)):
        raise UserFriendlyError(f"{field_name} must be a number, got: {type(value).__name__}")
    
    if value_type == int:
        value = int(value)
    elif value_type == float:
        value = float(value)
    
    if min_value is not None and value < min_value:
        raise UserFriendlyError(f"{field_name} must be >= {min_value}, got: {value}")
    
    if max_value is not None and value > max_value:
        raise UserFriendlyError(f"{field_name} must be <= {max_value}, got: {value}")
    
    return value


def validate_keyword_list(keywords: List[str]) -> List[str]:
    """
    Validate and clean a list of keywords.
    
    Args:
        keywords: List of keyword strings
        
    Returns:
        Cleaned list of valid keywords
        
    Raises:
        UserFriendlyError: If keywords list is invalid
    """
    if not isinstance(keywords, list):
        raise UserFriendlyError("Keywords must be provided as a list")
    
    valid_keywords = []
    for keyword in keywords:
        if isinstance(keyword, str) and keyword.strip():
            cleaned_keyword = keyword.strip()
            if len(cleaned_keyword) >= 2:  # Minimum keyword length
                valid_keywords.append(cleaned_keyword)
            else:
                logger.debug(f"Skipping keyword too short: '{cleaned_keyword}'")
        else:
            logger.debug(f"Skipping invalid keyword: {keyword}")
    
    return valid_keywords


def validate_boolean_param(value: Any, field_name: str, default: bool = False) -> bool:
    """
    Validate and convert a parameter to boolean.
    
    Args:
        value: Value to convert to boolean
        field_name: Name of the field (for error messages)
        default: Default value if value is None
        
    Returns:
        Boolean value
    """
    if value is None:
        return default
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        lower_value = value.lower()
        if lower_value in ('true', '1', 'yes', 'on'):
            return True
        elif lower_value in ('false', '0', 'no', 'off'):
            return False
    
    raise UserFriendlyError(f"{field_name} must be a boolean value, got: {value}")