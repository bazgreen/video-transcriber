"""
Application configuration classes.

This module contains all configuration classes that centralize settings and constants
used throughout the video transcriber application. Each class groups related settings
for better organization and maintainability.
"""

import os
from typing import List, Set


class AppConfig:
    """
    Centralized application configuration.

    Contains settings for file handling, directories, and security.
    """

    # File Upload Configuration
    MAX_FILE_SIZE_BYTES: int = 1024 * 1024 * 1024  # 1GB max file size (optimized)
    CHUNK_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB chunks for large file streaming
    ALLOWED_FILE_EXTENSIONS: Set[str] = {
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".webm",
        ".flv",
        ".wmv",
        ".m4v",
    }
    MEMORY_PRESSURE_THRESHOLD: int = 90  # Percentage threshold for memory pressure
    MAX_SESSION_NAME_LENGTH: int = 50  # Maximum allowed session name length

    # Directory Configuration
    UPLOAD_FOLDER: str = "data/uploads"
    RESULTS_FOLDER: str = "data/results"
    TEMPLATES_FOLDER: str = "data/templates"
    LOGS_FOLDER: str = "logs"

    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "video-transcriber-secret-key")

    # Application Settings
    DEFAULT_HOST: str = "0.0.0.0"  # nosec B104 - Intended for development/container use
    DEFAULT_PORT: int = 5001

    @classmethod
    def is_debug(cls) -> bool:
        """Check if application is in debug mode."""
        return os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def is_using_default_secret(cls) -> bool:
        """Check if application is using the default secret key."""
        return cls.SECRET_KEY == "video-transcriber-secret-key"

    @classmethod
    def validate_security_config(cls) -> List[str]:
        """Validate security configuration and return warnings."""
        warnings = []

        if cls.is_using_default_secret():
            warnings.append(
                "⚠️  Using default SECRET_KEY. Set SECRET_KEY environment variable for production!"
            )

        if not cls.is_debug():
            cors_origins = cls.get_cors_origins()
            if "*" in cors_origins:
                warnings.append(
                    "⚠️  CORS allows all origins (*). Set CORS_ALLOWED_ORIGINS for production!"
                )

        return warnings

    @classmethod
    def get_cors_origins(cls) -> List[str]:
        """
        Get CORS allowed origins as a list.

        For development, allows common localhost ports.
        For production, should be set via CORS_ALLOWED_ORIGINS environment variable.

        Returns:
            List of allowed CORS origins
        """
        if cls.is_debug():
            # In debug mode, allow common development origins
            return [
                "http://localhost:3000",  # React dev server
                "http://localhost:5000",  # Flask dev server alt port
                "http://localhost:5001",  # Main Flask server
                "http://127.0.0.1:5001",  # Localhost IP variant
            ]
        else:
            # In production, only allow explicitly configured origins
            cors_origins = os.getenv(
                "CORS_ALLOWED_ORIGINS",
                "http://localhost:5001",  # Default fallback for production
            )
            origins = cors_origins.split(",")
            return [origin.strip() for origin in origins if origin.strip()]

    # Legacy property for backwards compatibility
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


class MemoryConfig:
    """
    Memory management configuration.

    Contains settings for memory monitoring, worker limits, and fallback values
    when system memory information is unavailable.
    """

    # Memory Limits
    DEFAULT_MEMORY_PERCENT_LIMIT: int = 75
    MEMORY_PER_WORKER_GB: float = 0.6
    SYSTEM_MEMORY_RESERVE_GB: float = 2.0

    # Conservative Fallback Values (when psutil unavailable)
    CONSERVATIVE_SYSTEM_TOTAL_GB: float = 8.0
    CONSERVATIVE_SYSTEM_AVAILABLE_GB: float = 4.0
    CONSERVATIVE_SYSTEM_USED_PERCENT: float = 50.0
    CONSERVATIVE_PROCESS_RSS_MB: float = 100.0
    CONSERVATIVE_PROCESS_VMS_MB: float = 200.0


class VideoConfig:
    """
    Video processing configuration.

    Contains settings for video chunking, audio processing, and Whisper model configuration.
    """

    # Chunk Duration Settings (in seconds)
    DEFAULT_CHUNK_DURATION_SECONDS: int = 300  # 5 minutes
    MIN_CHUNK_DURATION_SECONDS: int = 60  # 1 minute
    MAX_CHUNK_DURATION_SECONDS: int = 600  # 10 minutes
    DEFAULT_OVERLAP_SECONDS: int = 0

    # Adaptive Chunking Thresholds (in seconds)
    SHORT_VIDEO_THRESHOLD: int = 600  # 10 minutes
    LONG_VIDEO_THRESHOLD: int = 3600  # 60 minutes (1 hour)
    SHORT_VIDEO_CHUNK_LIMIT: int = 180  # 3 minutes for short videos
    LONG_VIDEO_CHUNK_LIMIT: int = 420  # 7 minutes for long videos

    # Audio Processing Settings
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1
    AUDIO_CODEC: str = "pcm_s16le"

    # Whisper Model Configuration
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
    SUPPORTED_WHISPER_MODELS: Set[str] = {
        "tiny",
        "tiny.en",
        "base",
        "base.en",
        "small",
        "small.en",
        "medium",
        "medium.en",
        "large",
        "large-v1",
        "large-v2",
        "large-v3",
    }


class PerformanceConfig:
    """
    Performance and parallelization configuration.

    Contains settings for worker management and performance monitoring.
    """

    # Worker Limits (Enhanced for better performance)
    MIN_WORKERS: int = 2  # Increased minimum for better throughput
    MAX_WORKERS_LIMIT: int = 16  # Increased for high-performance systems
    DEFAULT_MAX_WORKERS: int = 6  # Optimized default

    # Memory-Aware Configuration
    MEMORY_SAFETY_FACTOR: float = 0.8  # Use 80% of available memory
    HIGH_MEMORY_THRESHOLD_GB: int = 8  # Systems with 8GB+ get more workers

    # Progress Monitoring (Optimized)
    MEMORY_CHECK_INTERVAL: int = 3  # Check memory more frequently
    CHUNK_SIZE_OPTIMIZATION: bool = True  # Enable dynamic chunk sizing

    # Processing Timeouts (in seconds) - Optimized for performance
    CHUNK_PROCESSING_TIMEOUT: int = 600  # 10 minutes per chunk (increased)
    TOTAL_PROCESSING_TIMEOUT: int = 7200  # 2 hours total (increased)

    # Performance Features
    ENABLE_PARALLEL_UPLOAD: bool = True  # Enable parallel chunk uploads
    ENABLE_MEMORY_CLEANUP: bool = True  # Enable aggressive memory cleanup


class AnalysisConfig:
    """
    Content analysis configuration.

    Contains settings for text analysis, keyword detection, and pattern matching.
    """

    # Text Analysis Settings
    CONTEXT_WINDOW_CHARS: int = 50
    MIN_KEYWORD_LENGTH: int = 2
    MAX_KEYWORD_LENGTH: int = 100

    # Pattern Detection (regex patterns)
    QUESTION_PATTERNS: List[str] = [
        r"\?",
        r"\bwhat\b",
        r"\bhow\b",
        r"\bwhy\b",
        r"\bwhen\b",
        r"\bwhere\b",
        r"\bwho\b",
    ]

    EMPHASIS_PATTERNS: List[str] = [
        r"\bmake sure\b",
        r"\bdon\'t forget\b",
        r"\bremember\b",
        r"\bimportant\b",
        r"\bnote that\b",
        r"\bpay attention\b",
        r"\bkeep in mind\b",
    ]

    # Analysis Limits
    MAX_KEYWORDS_PER_ANALYSIS: int = 1000
    MAX_MATCHES_PER_KEYWORD: int = 100


class Constants:
    """
    General constants and conversions.

    Contains universal constants for time, data size, and other unit conversions.
    """

    # Time Conversions
    SECONDS_PER_MINUTE: int = 60
    MINUTES_PER_HOUR: int = 60
    HOURS_PER_DAY: int = 24
    MILLISECONDS_PER_SECOND: int = 1000

    # Data Size Conversions (binary)
    BYTES_PER_KB: int = 1024
    BYTES_PER_MB: int = 1024 * 1024
    BYTES_PER_GB: int = 1024 * 1024 * 1024

    # HTTP Status Codes (commonly used)
    HTTP_OK: int = 200
    HTTP_BAD_REQUEST: int = 400
    HTTP_NOT_FOUND: int = 404
    HTTP_INTERNAL_SERVER_ERROR: int = 500

    # File Extensions
    VIDEO_EXTENSIONS: Set[str] = AppConfig.ALLOWED_FILE_EXTENSIONS
    AUDIO_EXTENSIONS: Set[str] = {".wav", ".mp3", ".m4a", ".flac"}
    TEXT_EXTENSIONS: Set[str] = {".txt", ".json", ".html"}


# Configuration Validation
def validate_configurations() -> None:
    """
    Validate configuration values for consistency and correctness.

    Raises:
        ValueError: If any configuration values are invalid
    """
    # Validate VideoConfig
    if VideoConfig.MIN_CHUNK_DURATION_SECONDS >= VideoConfig.MAX_CHUNK_DURATION_SECONDS:
        raise ValueError(
            "MIN_CHUNK_DURATION_SECONDS must be less than MAX_CHUNK_DURATION_SECONDS"
        )

    if (
        VideoConfig.DEFAULT_CHUNK_DURATION_SECONDS
        < VideoConfig.MIN_CHUNK_DURATION_SECONDS
    ):
        raise ValueError(
            "DEFAULT_CHUNK_DURATION_SECONDS must be >= MIN_CHUNK_DURATION_SECONDS"
        )

    if (
        VideoConfig.DEFAULT_CHUNK_DURATION_SECONDS
        > VideoConfig.MAX_CHUNK_DURATION_SECONDS
    ):
        raise ValueError(
            "DEFAULT_CHUNK_DURATION_SECONDS must be <= MAX_CHUNK_DURATION_SECONDS"
        )

    # Validate PerformanceConfig
    if PerformanceConfig.MIN_WORKERS > PerformanceConfig.DEFAULT_MAX_WORKERS:
        raise ValueError("MIN_WORKERS must be <= DEFAULT_MAX_WORKERS")

    if PerformanceConfig.DEFAULT_MAX_WORKERS > PerformanceConfig.MAX_WORKERS_LIMIT:
        raise ValueError("DEFAULT_MAX_WORKERS must be <= MAX_WORKERS_LIMIT")

    # Validate MemoryConfig
    if (
        MemoryConfig.DEFAULT_MEMORY_PERCENT_LIMIT <= 0
        or MemoryConfig.DEFAULT_MEMORY_PERCENT_LIMIT > 100
    ):
        raise ValueError("DEFAULT_MEMORY_PERCENT_LIMIT must be between 1 and 100")

    # Validate AppConfig
    if AppConfig.MAX_FILE_SIZE_BYTES <= 0:
        raise ValueError("MAX_FILE_SIZE_BYTES must be positive")


# Run validation on import
validate_configurations()
