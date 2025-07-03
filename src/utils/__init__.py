"""Utilities module for the video transcriber application."""

from .decorators import handle_user_friendly_error
from .helpers import (
    format_timestamp,
    is_safe_path,
    is_valid_session_id,
    load_session_metadata,
    parse_session_metadata,
)
from .keywords import (
    get_scenario_by_id,
    load_keywords,
    load_scenarios,
    save_keywords,
    save_scenarios,
)
from .memory import (
    check_memory_constraints,
    get_memory_status_safe,
    log_memory_status,
    validate_memory_for_operation,
)
from .session import (
    ensure_session_exists,
    get_session_list,
    validate_session_access,
    validate_session_for_socket,
)
from .validation import (
    validate_boolean_param,
    validate_file_upload,
    validate_keyword_list,
    validate_numeric_range,
    validate_request_data,
    validate_session_name,
)

__all__ = [
    # Core helpers
    "is_valid_session_id",
    "is_safe_path",
    "format_timestamp",
    "parse_session_metadata",
    "load_session_metadata",
    # Keywords
    "load_keywords",
    "save_keywords",
    "load_scenarios",
    "save_scenarios",
    "get_scenario_by_id",
    # Decorators
    "handle_user_friendly_error",
    # Session management
    "validate_session_access",
    "ensure_session_exists",
    "validate_session_for_socket",
    "get_session_list",
    # Memory management
    "get_memory_status_safe",
    "check_memory_constraints",
    "log_memory_status",
    "validate_memory_for_operation",
    # Validation
    "validate_request_data",
    "validate_file_upload",
    "validate_session_name",
    "validate_numeric_range",
    "validate_keyword_list",
    "validate_boolean_param",
]
