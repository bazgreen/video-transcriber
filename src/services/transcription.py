"""Video transcription service."""

import json
import logging
import math
import os
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

try:
    import ffmpeg

    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    ffmpeg = None

from flask import render_template

from src.config import AnalysisConfig, VideoConfig
from src.models import MemoryManager, ModelManager, ProgressiveFileManager
from src.models.exceptions import UserFriendlyError
from src.services.export import EnhancedExportService
from src.utils import format_timestamp, load_keywords
from src.utils.performance_optimizer import performance_optimizer

# Import language detection service
try:
    from src.services.language_detection import LanguageDetectionService

    LANGUAGE_DETECTION_AVAILABLE = True
except ImportError:
    LANGUAGE_DETECTION_AVAILABLE = False
    LanguageDetectionService = None

# Import AI insights engine
try:
    from src.services.ai_insights import create_ai_insights_engine

    AI_INSIGHTS_AVAILABLE = True
except ImportError:
    AI_INSIGHTS_AVAILABLE = False
    create_ai_insights_engine = None

logger = logging.getLogger(__name__)

# Configuration instances
video_config = VideoConfig()
analysis_config = AnalysisConfig()

# Patterns are now configured in AnalysisConfig


def init_worker() -> None:
    """
    Initialize worker process for parallel transcription.

    This function is called when a new worker process is created for
    parallel chunk processing. It prepares the worker for memory-efficient
    operation by deferring model loading until needed.
    """
    logger.info("Worker process initialized (model will be loaded on demand)")


def get_model() -> Any:
    """
    Get the Whisper model with efficient memory management.

    This function provides lazy loading of the Whisper model for worker
    processes, ensuring memory efficiency in parallel processing scenarios.

    Returns:
        Loaded Whisper model instance

    Note:
        This function is primarily used by worker processes and will be
        refactored to use dependency injection in future versions.
    """
    model_manager = ModelManager()
    return model_manager.get_model()


def process_chunk_parallel(chunk_info: Tuple[str, str, float, str]) -> Dict[str, Any]:
    """
    Process a single video chunk in parallel using ProcessPoolExecutor.

    This function handles audio extraction and transcription for a single
    video chunk in a separate process for parallel processing efficiency.

    Args:
        chunk_info: Tuple containing (chunk_path, audio_path, start_time, filename)
            - chunk_path: Path to the video chunk file
            - audio_path: Path where extracted audio will be saved
            - start_time: Start time offset for timestamp adjustment
            - filename: Original filename for identification

    Returns:
        Dictionary containing transcription results:
        - filename: Original filename
        - transcription: Full text transcription
        - segments: List of timestamped segments
        - start_time: Start time offset
        - success: Boolean indicating success/failure
        - error: Error message (if success=False)

    Raises:
        ValueError: If chunk_info format is invalid

    Note:
        This function is designed for use with ProcessPoolExecutor and
        includes error handling for robust parallel processing.
    """
    if not isinstance(chunk_info, tuple) or len(chunk_info) != 4:
        raise ValueError(
            "Invalid chunk_info format. Expected a tuple with 4 elements: "
            "(chunk_path, audio_path, start_time, filename)."
        )

    try:
        chunk_path, audio_path, start_time, filename = chunk_info

        # Extract audio
        (
            ffmpeg.input(chunk_path)
            .output(
                audio_path,
                acodec=video_config.AUDIO_CODEC,
                ac=video_config.AUDIO_CHANNELS,
                ar=str(video_config.AUDIO_SAMPLE_RATE),
            )
            .overwrite_output()
            .run(quiet=True)
        )

        # Get model and transcribe
        model = get_model()
        result = model.transcribe(audio_path, word_timestamps=True)

        # Format with timestamps
        timestamped_segments = []
        for segment in result["segments"]:
            adjusted_segment = {
                "start": segment["start"] + start_time,
                "end": segment["end"] + start_time,
                "text": segment["text"].strip(),
                "timestamp_str": format_timestamp(segment["start"] + start_time),
            }
            timestamped_segments.append(adjusted_segment)

        # Note: file_manager access will need to be refactored
        # file_manager.add_temp_file(audio_path, 'audio')

        return {
            "filename": filename,
            "transcription": result["text"],
            "segments": timestamped_segments,
            "start_time": start_time,
            "success": True,
        }
    except Exception as e:
        return {
            "filename": filename,
            "error": str(e),
            "start_time": start_time,
            "success": False,
        }


class VideoTranscriber:
    """
    Comprehensive video transcription service.

    This service handles the complete video-to-text transcription pipeline,
    including video splitting, parallel processing, audio extraction,
    speech recognition, content analysis, and result generation.

    Features:
    - Parallel video chunk processing for performance
    - Memory-aware worker management
    - Real-time progress tracking via WebSocket
    - Comprehensive content analysis (keywords, questions, emphasis)
    - Multiple output formats (text, JSON, HTML)
    - Progressive file cleanup during processing

    Attributes:
        model: Loaded Whisper model (lazy-loaded)
        memory_manager: Memory monitoring and optimization
        file_manager: Progressive file cleanup management
        progress_tracker: Real-time progress updates
        results_folder: Base folder for storing transcription results
        max_workers: Optimal number of parallel workers
        chunk_duration: Default chunk duration for video splitting
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        file_manager: ProgressiveFileManager,
        progress_tracker: Any,  # ProgressTracker type
        results_folder: str,
    ) -> None:
        """
        Initialize the VideoTranscriber service.

        Args:
            memory_manager: Memory monitoring and management instance
            file_manager: Progressive file cleanup manager
            progress_tracker: Real-time progress tracking for WebSocket updates
            results_folder: Base directory for storing transcription results
        """
        self.model = None
        self.memory_manager = memory_manager
        self.file_manager = file_manager
        self.progress_tracker = progress_tracker
        self.results_folder = results_folder

        # Memory-aware performance tuning
        self.max_workers = memory_manager.get_optimal_workers()
        self.chunk_duration = video_config.DEFAULT_CHUNK_DURATION_SECONDS

        # Initialize AI insights engine if available
        self.ai_insights_engine = None
        if AI_INSIGHTS_AVAILABLE:
            try:
                self.ai_insights_engine = create_ai_insights_engine()
                logger.info("AI Insights Engine initialized successfully")
            except Exception as e:
                logger.warning(f"AI Insights Engine initialization failed: {e}")
                self.ai_insights_engine = None
        else:
            logger.info(
                "AI Insights Engine not available (install optional dependencies for full AI features)"
            )

        # Initialize language detection service if available
        self.language_detector = None
        if LANGUAGE_DETECTION_AVAILABLE:
            try:
                self.language_detector = LanguageDetectionService()
                logger.info("Language Detection Service initialized successfully")
            except Exception as e:
                logger.warning(f"Language Detection Service initialization failed: {e}")
                self.language_detector = None
        else:
            logger.info(
                "Language Detection Service not available (install langdetect for multi-language support)"
            )

        # Log memory and worker configuration
        memory_info = memory_manager.get_memory_info()
        logger.info(
            f"VideoTranscriber initialized with {self.max_workers} max workers. "
            f"System memory: {memory_info['system_total_gb']:.1f}GB total, "
            f"{memory_info['system_available_gb']:.1f}GB available"
        )

    def load_model(self) -> Any:
        """
        Load Whisper model with lazy initialization.

        The model is loaded on-demand to optimize memory usage, especially
        in multi-process environments where each worker loads its own model.

        Returns:
            Loaded Whisper model instance

        Note:
            Model loading is thread-safe and cached after first load.
        """
        if self.model is None:
            logger.info(f"Loading Whisper model: {video_config.WHISPER_MODEL}")
            self.model = whisper.load_model(video_config.WHISPER_MODEL)
            logger.info("Whisper model loaded successfully")
        return self.model

    def split_video(
        self, input_path: str, output_dir: str, chunk_duration: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Split video into chunks for parallel processing.

        This method intelligently splits videos into optimal chunks based on
        video duration and system capabilities, using parallel processing
        for maximum efficiency.

        Args:
            input_path: Path to the input video file
            output_dir: Directory where video chunks will be saved
            chunk_duration: Duration of each chunk in seconds (uses instance
                          default if None)

        Returns:
            List of chunk information dictionaries, each containing:
            - filename: Name of the chunk file
            - path: Full path to the chunk file
            - start_time: Start time offset in seconds
            - duration: Duration of the chunk in seconds

        Raises:
            Exception: If video file cannot be processed or split

        Features:
        - Adaptive chunk sizing based on video length
        - Parallel chunk creation using ThreadPoolExecutor
        - Automatic video duration detection
        - Progressive file tracking for cleanup
        """
        chunks = []

        # Get file size for performance optimization
        file_size_mb = os.path.getsize(input_path) / (1024 * 1024)

        # Get video info first to determine duration
        try:
            probe = ffmpeg.probe(input_path)
            video_info = next(
                (
                    stream
                    for stream in probe["streams"]
                    if stream["codec_type"] == "video"
                ),
                None,
            )
            if not video_info:
                raise UserFriendlyError(
                    f"Unable to analyze video file: {os.path.basename(input_path)}. "
                    f"Please ensure it's a valid video format."
                )

            duration = float(video_info["duration"])

        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error analyzing video: {e}")
            raise UserFriendlyError(
                f"Unable to analyze video file: {os.path.basename(input_path)}. "
                f"Please ensure it's a valid video format."
            ) from e
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing video metadata: {e}")
            raise UserFriendlyError(
                f"Error analyzing video file: {os.path.basename(input_path)}. "
                f"Please try again or use a different file."
            ) from e

        # Use performance optimizer for optimal settings
        if chunk_duration is None:
            chunk_duration = performance_optimizer.get_optimal_chunk_size(
                duration, file_size_mb
            )

        optimal_workers = performance_optimizer.get_optimal_worker_count(file_size_mb)

        logger.info(
            f"Video processing optimization: {file_size_mb:.1f}MB file, "
            f"{duration:.1f}s duration, {chunk_duration}s chunks, "
            f"{optimal_workers} workers"
        )

        # Adaptive chunk sizing for better performance
        # For shorter videos, use smaller chunks for faster parallel processing
        if duration < video_config.SHORT_VIDEO_THRESHOLD:
            chunk_duration = min(chunk_duration, video_config.SHORT_VIDEO_CHUNK_LIMIT)
        elif duration > video_config.LONG_VIDEO_THRESHOLD:
            chunk_duration = min(chunk_duration, video_config.LONG_VIDEO_CHUNK_LIMIT)

        # Calculate number of chunks
        num_chunks = math.ceil(duration / chunk_duration)

        base_name = os.path.splitext(os.path.basename(input_path))[0]

        # Prepare chunk info for parallel processing
        chunk_tasks = []
        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_name = f"{base_name}_part_{i:03d}.mp4"
            chunk_path = os.path.join(output_dir, chunk_name)
            actual_duration = min(chunk_duration, duration - start_time)

            chunk_tasks.append(
                (input_path, chunk_path, start_time, actual_duration, chunk_name)
            )

            chunks.append(
                {
                    "filename": chunk_name,
                    "path": chunk_path,
                    "start_time": start_time,
                    "duration": actual_duration,
                }
            )

        # Process chunks in parallel using ThreadPoolExecutor (I/O bound for ffmpeg)
        # Use optimized worker count
        with ThreadPoolExecutor(
            max_workers=min(optimal_workers, num_chunks)
        ) as executor:
            futures = []
            for task in chunk_tasks:
                future = executor.submit(self._split_single_chunk, *task)
                futures.append(future)

            # Wait for all chunks to complete
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise any exceptions that occurred
                except Exception as e:
                    logger.error(f"Error splitting chunk: {e}")

        return chunks

    def _split_single_chunk(
        self, input_path, chunk_path, start_time, duration, chunk_name
    ):
        """Split a single video chunk - helper method for parallel processing"""
        try:
            (
                ffmpeg.input(input_path, ss=start_time, t=duration)
                .output(chunk_path, vcodec="libx264", acodec="aac")
                .overwrite_output()
                .run(quiet=True)
            )
            # Register chunk for progressive cleanup
            self.file_manager.add_temp_file(chunk_path, "video")
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error splitting chunk {chunk_name}: {e}")
            raise UserFriendlyError(
                "Failed to split video chunk. Please check video format compatibility."
            )
        except Exception as e:
            logger.error(
                f"Unexpected error splitting chunk {chunk_name}: {e}", exc_info=True
            )
            raise UserFriendlyError("Error processing video chunk. Please try again.")

    def extract_audio(self, video_path, audio_path):
        """Extract audio from video"""
        (
            ffmpeg.input(video_path)
            .output(
                audio_path,
                acodec=video_config.AUDIO_CODEC,
                ac=video_config.AUDIO_CHANNELS,
                ar=str(video_config.AUDIO_SAMPLE_RATE),
            )
            .overwrite_output()
            .run(quiet=True)
        )

    def transcribe_with_timestamps(
        self, audio_path: str, force_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file with detailed timestamp information and language detection.

        Args:
            audio_path: Path to the audio file to transcribe
            force_language: Force specific language (optional)

        Returns:
            Dictionary containing:
            - text: Full transcription text
            - segments: List of timestamped segments with start/end times
            - detected_language: Auto-detected language code (if detection available)
            - language_confidence: Confidence score for language detection
            - language_name: Full name of detected language

        Note:
            Uses Whisper's word-level timestamps for precise timing information.
            Supports automatic language detection when available.
        """
        model = self.load_model()

        # Use language detection if available and no language forced
        detected_language = None
        language_confidence = 0.0
        language_name = None

        if self.language_detector and not force_language:
            try:
                (
                    detected_language,
                    language_confidence,
                ) = self.language_detector.detect_language_from_audio(
                    audio_path, model_size="base"
                )
                if detected_language:
                    language_name = self.language_detector.get_language_name(
                        detected_language
                    )
                    logger.info(
                        f"Detected language: {language_name} ({detected_language}) with confidence {language_confidence:.2f}"
                    )
            except Exception as e:
                logger.warning(f"Language detection failed: {e}")

        # Use forced language or detected language
        language_to_use = force_language or detected_language

        # Transcribe with language specification
        transcribe_kwargs = {"word_timestamps": True}
        if language_to_use:
            transcribe_kwargs["language"] = language_to_use

        result = model.transcribe(audio_path, **transcribe_kwargs)

        # Format with timestamps
        timestamped_segments = []
        for segment in result["segments"]:
            timestamped_segments.append(
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "timestamp_str": format_timestamp(segment["start"]),
                }
            )

        # Add language detection results
        enhanced_result = {
            "text": result["text"],
            "segments": timestamped_segments,
            "detected_language": detected_language,
            "language_confidence": language_confidence,
            "language_name": language_name,
            "forced_language": force_language,
        }

        return enhanced_result

    def get_video_duration(self, video_path: str) -> float:
        """
        Extract video duration using FFmpeg probe.

        Args:
            video_path: Path to the video file

        Returns:
            Video duration in seconds, or 0.0 if duration cannot be determined

        Note:
            This is a utility method that safely handles various video formats
            and provides fallback behavior for problematic files.
        """
        try:
            probe = ffmpeg.probe(video_path)
            duration = float(probe["streams"][0]["duration"])
            return duration
        except Exception as e:
            logger.warning(f"Could not get video duration for {video_path}: {e}")
            return 0.0

    def analyze_content(
        self, text: str, segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive content analysis on transcribed text.

        This method analyzes the transcription for educational keywords,
        questions, emphasis cues, and generates frequency statistics.

        Args:
            text: Full transcription text
            segments: List of timestamped text segments

        Returns:
            Dictionary containing analysis results:
            - keyword_matches: List of keyword matches with context
            - questions: List of detected questions with timestamps
            - emphasis_cues: List of emphasis phrases with timestamps
            - keyword_frequency: Frequency count of detected keywords
            - total_words: Total word count in transcription

        Features:
        - Context-aware keyword matching with surrounding text
        - Pattern-based question detection
        - Emphasis cue recognition for important content
        - Statistical analysis with word frequency counting
        """
        analysis: Dict[str, Any] = {
            "keyword_matches": [],
            "questions": [],
            "emphasis_cues": [],
            "keyword_frequency": {},
            "total_words": len(text.split()),
        }

        # Load keywords - from scenario if specified, otherwise from custom keywords
        custom_keywords = []

        # If a keyword scenario was selected during upload, use those keywords
        if (
            hasattr(self, "_selected_keyword_scenario_id")
            and self._selected_keyword_scenario_id
        ):
            from src.utils import get_scenario_by_id

            scenario = get_scenario_by_id(self._selected_keyword_scenario_id)
            if scenario and "keywords" in scenario:
                custom_keywords = scenario["keywords"]
                logger.info(
                    f"Using {len(custom_keywords)} keywords from scenario: {scenario.get('name', self._selected_keyword_scenario_id)}"
                )

        # If no scenario keywords were loaded, fall back to custom keywords
        if not custom_keywords:
            custom_keywords = load_keywords()
            logger.info(f"Using {len(custom_keywords)} custom keywords")

        # Keyword analysis
        for keyword in custom_keywords:
            pattern = re.compile(
                f".{{0,{analysis_config.CONTEXT_WINDOW_CHARS}}}"
                + re.escape(keyword)
                + f".{{0,{analysis_config.CONTEXT_WINDOW_CHARS}}}",
                re.IGNORECASE,
            )
            matches = pattern.findall(text)
            if matches:
                analysis["keyword_matches"].append(
                    {"keyword": keyword, "matches": matches, "count": len(matches)}
                )

        # Count keyword frequency
        words = re.findall(r"\b\w+\b", text.lower())
        word_freq = Counter(words)

        # Filter for relevant keywords
        for keyword in custom_keywords:
            if keyword.lower() in word_freq:
                analysis["keyword_frequency"][keyword] = word_freq[keyword.lower()]

        # Find questions in segments
        for segment in segments:
            for question_pattern in analysis_config.QUESTION_PATTERNS:
                if re.search(question_pattern, segment["text"], re.IGNORECASE):
                    analysis["questions"].append(
                        {
                            "timestamp": segment["timestamp_str"],
                            "text": segment["text"].strip(),
                            "start": segment["start"],
                        }
                    )
                    break

        # Find emphasis cues
        for segment in segments:
            for emphasis_pattern in analysis_config.EMPHASIS_PATTERNS:
                if re.search(emphasis_pattern, segment["text"], re.IGNORECASE):
                    analysis["emphasis_cues"].append(
                        {
                            "timestamp": segment["timestamp_str"],
                            "text": segment["text"].strip(),
                            "start": segment["start"],
                        }
                    )
                    break

        return analysis

    def process_video(
        self,
        video_path: str,
        session_name: str = "",
        original_filename: str = "",
        keyword_scenario_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Complete video processing pipeline"""
        session_id, session_dir, metadata, results = self._initialize_session(
            session_name, original_filename, keyword_scenario_id
        )

        try:
            self._process_video_chunks(video_path, session_id, session_dir, results)
            self._finalize_session(session_id, session_dir, metadata, results)
            return results

        except Exception as e:
            # Handle errors and update progress
            error_message = f"Processing failed: {str(e)}"
            logger.error(error_message)
            self.progress_tracker.complete_session(
                session_id, success=False, message=error_message
            )
            raise

    def _initialize_session(
        self,
        session_name: str = "",
        original_filename: str = "",
        keyword_scenario_id: Optional[str] = None,
    ) -> Tuple[str, str, Dict[str, Any], Dict[str, Any]]:
        """Initialize a new processing session"""
        # Create session directory
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_name:
            session_id = f"{session_name}_{session_id}"

        # Store scenario ID for later use in keyword analysis
        self._selected_keyword_scenario_id = keyword_scenario_id

        session_dir = os.path.join(self.results_folder, session_id)
        os.makedirs(session_dir, exist_ok=True)

        # Store session metadata
        metadata = {
            "session_id": session_id,
            "session_name": session_name,
            "original_filename": original_filename,
            "created_at": datetime.now().isoformat(),
            "status": "processing",
        }

        results = {
            "session_id": session_id,
            "session_dir": session_dir,
            "chunks": [],
            "full_transcript": "",
            "analysis": {},
            "html_file": None,
        }

        return session_id, session_dir, metadata, results

    def _process_video_chunks(self, video_path, session_id, session_dir, results):
        """Process video chunks and transcribe them"""
        # Initialize progress tracking
        self.progress_tracker.start_session(session_id)
        self.progress_tracker.update_progress(
            session_id,
            current_task="Analyzing video file...",
            progress=5,
            stage="analysis",
        )

        # Split video into chunks
        chunks = self.split_video(video_path, session_dir)

        # Update progress after video splitting
        self.progress_tracker.start_session(
            session_id,
            total_chunks=len(chunks),
            video_duration=self.get_video_duration(video_path),
        )
        self.progress_tracker.update_progress(
            session_id,
            current_task=(
                f"Video split into {len(chunks)} chunks. Starting transcription..."
            ),
            progress=15,
            stage="preparation",
        )

        # Process chunks and combine results
        all_segments, all_text = self._transcribe_chunks_parallel(
            session_id, session_dir, chunks
        )

        # Store results
        results["segments"] = all_segments
        results["full_transcript"] = "\n".join(all_text)

        # Analyze content
        self.progress_tracker.update_progress(
            session_id,
            current_task="Analyzing content for keywords and insights...",
            progress=90,
            stage="analysis",
        )
        results["analysis"] = self.analyze_content(
            results["full_transcript"], all_segments
        )

        # Enhanced AI insights analysis
        if self.ai_insights_engine:
            self.progress_tracker.update_progress(
                session_id,
                current_task="Generating AI-powered insights...",
                progress=93,
                stage="ai_analysis",
            )
            try:
                results["ai_insights"] = self.ai_insights_engine.analyze_comprehensive(
                    results["full_transcript"], all_segments, results["analysis"]
                )
                logger.info("AI insights analysis completed successfully")
            except Exception as e:
                logger.warning(f"AI insights analysis failed: {e}")
                results["ai_insights"] = {"error": str(e), "available": False}
        else:
            results["ai_insights"] = {
                "available": False,
                "message": "AI insights engine not available",
            }

    def _transcribe_chunks_parallel(
        self, session_id: str, session_dir: str, chunks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Transcribe video chunks in parallel"""
        all_segments = []
        all_text = []

        # Process chunks in parallel
        chunk_info_list = []
        for chunk in chunks:
            audio_path = os.path.join(
                session_dir, f"{os.path.splitext(chunk['filename'])[0]}.wav"
            )
            chunk_info_list.append(
                (chunk["path"], audio_path, chunk["start_time"], chunk["filename"])
            )

        # Use ProcessPoolExecutor for CPU-intensive transcription work with
        # memory monitoring
        completed_chunks = []

        # Dynamic memory-aware worker calculation
        memory_info = self.memory_manager.get_memory_info()
        optimal_workers = self.memory_manager.get_optimal_workers(
            max_workers=self.max_workers
        )
        num_workers = min(optimal_workers, len(chunks))

        logger.info(
            f"Processing {len(chunks)} chunks in parallel using {num_workers} workers "
            f"(Memory: {memory_info['system_used_percent']:.1f}% used, "
            f"{memory_info['system_available_gb']:.1f}GB available)"
        )

        with ProcessPoolExecutor(
            max_workers=num_workers, initializer=init_worker
        ) as executor:
            # Submit all chunk processing tasks
            futures = {
                executor.submit(process_chunk_parallel, chunk_info): chunk_info
                for chunk_info in chunk_info_list
            }

            # Collect results as they complete with memory monitoring
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    if result["success"]:
                        completed_chunks.append(result)

                        # Update progress for each completed chunk
                        self.progress_tracker.update_chunk_progress(
                            session_id,
                            i + 1,
                            len(chunks),
                            f"Transcribed {result['filename']}",
                        )

                        # Periodic memory monitoring (every 25% of chunks)
                        if (i + 1) % max(1, len(chunks) // 4) == 0:
                            current_memory = self.memory_manager.get_memory_info()
                            logger.info(
                                f"Completed chunk {i + 1}/{len(chunks)}: "
                                f"{result['filename']} (Memory: "
                                f"{current_memory['process_rss_mb']:.0f}MB process, "
                                f"{current_memory['system_used_percent']:.1f}% system)"
                            )

                            # Check for memory pressure
                            if self.memory_manager.check_memory_pressure():
                                logger.warning(
                                    f"High memory usage detected: "
                                    f"{current_memory['system_used_percent']:.1f}%"
                                )
                        else:
                            logger.info(
                                f"Completed chunk {i + 1}/{len(chunks)}: "
                                f"{result['filename']}"
                            )
                    else:
                        logger.error(
                            f"Error processing chunk {result['filename']}: "
                            f"{result.get('error', 'Unknown error')}"
                        )
                        # Update progress even for failed chunks
                        self.progress_tracker.update_chunk_progress(
                            session_id,
                            i + 1,
                            len(chunks),
                            f"Error in {result['filename']}",
                        )
                except Exception as e:
                    logger.error(f"Exception processing chunk: {e}")
                    # Update progress for exception cases
                    self.progress_tracker.update_chunk_progress(
                        session_id, i + 1, len(chunks), "Exception processing chunk"
                    )

        # Sort results by start time to maintain order
        completed_chunks.sort(key=lambda x: x["start_time"])

        # Update progress for final processing stages
        self.progress_tracker.update_progress(
            session_id,
            current_task="Combining transcription results...",
            progress=85,
            stage="post_processing",
        )

        # Combine results
        for chunk_result in completed_chunks:
            all_segments.extend(chunk_result["segments"])
            all_text.append(
                f"\n\n--- {chunk_result['filename']} "
                f"[{format_timestamp(chunk_result['start_time'])}] ---\n\n"
                f"{chunk_result['transcription']}"
            )

        return all_segments, all_text

    def _finalize_session(self, session_id, session_dir, metadata, results):
        """Finalize session processing and generate outputs"""
        # Get chunk count from progress tracker or calculate from segments
        progress_data = self.progress_tracker.get_session_progress(session_id)
        chunks_count = progress_data.get("total_chunks", 1) if progress_data else 1

        # Update metadata with final stats
        metadata.update(
            {
                "status": "completed",
                "total_chunks": chunks_count,
                "total_words": results["analysis"]["total_words"],
                "keywords_found": len(results["analysis"]["keyword_matches"]),
                "questions_found": len(results["analysis"]["questions"]),
                "emphasis_cues_found": len(results["analysis"]["emphasis_cues"]),
                "processing_time": (
                    datetime.now() - datetime.fromisoformat(metadata["created_at"])
                ).total_seconds(),
            }
        )

        # Save metadata
        with open(os.path.join(session_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)

        # Update progress for final generation
        self.progress_tracker.update_progress(
            session_id,
            current_task="Generating output files...",
            progress=95,
            stage="finalization",
        )

        # Generate outputs
        self.save_results(results)
        results["html_file"] = self.generate_html_transcript(results)
        results["metadata"] = metadata

        # Complete progress tracking
        self.progress_tracker.complete_session(
            session_id,
            success=True,
            message=(
                f"Processing complete! Transcribed {chunks_count} chunks, "
                f"found {results['analysis']['total_words']} words."
            ),
        )

        # Clean up all temporary files using progressive file manager
        cleanup_stats = self.file_manager.get_cleanup_stats()
        logger.info(
            f"Final cleanup: {cleanup_stats['count']} temp files, "
            f"{cleanup_stats['total_size_mb']:.1f}MB"
        )
        self.file_manager.cleanup_all()

    def save_results(self, results):
        """
        Save transcription results to files using enhanced export service.

        This method now supports multiple output formats including:
        - Traditional text files (full_transcript.txt, questions.txt, etc.)
        - Subtitle formats (SRT, VTT)
        - Professional documents (PDF, DOCX)
        - Enhanced structured text
        """
        # Initialize enhanced export service
        export_service = EnhancedExportService()

        # Save traditional formats (for backward compatibility)
        self._save_traditional_formats(results)

        # Export enhanced formats
        try:
            exported_files = export_service.export_all_formats(results)

            # Add exported file paths to results for reference
            results["exported_files"] = exported_files

            # Log successful exports
            for format_name, file_path in exported_files.items():
                logger.info(
                    f"Exported {format_name.upper()}: {os.path.basename(file_path)}"
                )

        except Exception as e:
            logger.warning(f"Some enhanced export formats failed: {e}")
            # Continue with traditional formats only

    def _save_traditional_formats(self, results):
        """Save traditional text-based output formats for backward compatibility."""
        session_dir = results["session_dir"]

        # Save full transcript
        with open(os.path.join(session_dir, "full_transcript.txt"), "w") as f:
            f.write(results["full_transcript"])

        # Save analysis results
        with open(os.path.join(session_dir, "analysis.json"), "w") as f:
            json.dump(results["analysis"], f, indent=2)

        # Save AI insights if available
        if "ai_insights" in results and results["ai_insights"].get("available", True):
            with open(os.path.join(session_dir, "ai_insights.json"), "w") as f:
                json.dump(results["ai_insights"], f, indent=2)

        # Save keyword highlights
        with open(os.path.join(session_dir, "assessment_mentions.txt"), "w") as f:
            f.write("Assessment-Related Content:\n\n")
            for match in results["analysis"]["keyword_matches"]:
                f.write(
                    f"\n🔹 Keyword: **{match['keyword']}** ({match['count']} mentions)\n"
                )
                for text in match["matches"]:
                    f.write(f"- {text.strip()}\n")

        # Save questions
        with open(os.path.join(session_dir, "questions.txt"), "w") as f:
            f.write("Questions Detected:\n\n")
            for q in results["analysis"]["questions"]:
                f.write(f"[{q['timestamp']}] {q['text']}\n\n")

        # Save emphasis cues
        with open(os.path.join(session_dir, "emphasis_cues.txt"), "w") as f:
            f.write("Emphasis Cues:\n\n")
            for cue in results["analysis"]["emphasis_cues"]:
                f.write(f"[{cue['timestamp']}] {cue['text']}\n\n")

    def generate_html_transcript(self, results):
        """Generate searchable HTML transcript using template"""
        # Prepare all segments with metadata
        all_segments = results.get("segments", [])

        # Sort by timestamp
        all_segments.sort(key=lambda x: x["start"])

        # Create sets for quick lookup
        question_times = {q["start"] for q in results["analysis"]["questions"]}
        emphasis_times = {e["start"] for e in results["analysis"]["emphasis_cues"]}

        # Load keywords - from scenario if specified, otherwise from custom keywords
        custom_keywords = []

        # If a keyword scenario was selected during upload, use those keywords
        if (
            hasattr(self, "_selected_keyword_scenario_id")
            and self._selected_keyword_scenario_id
        ):
            from src.utils import get_scenario_by_id

            scenario = get_scenario_by_id(self._selected_keyword_scenario_id)
            if scenario and "keywords" in scenario:
                custom_keywords = scenario["keywords"]

        # If no scenario keywords were loaded, fall back to custom keywords
        if not custom_keywords:
            custom_keywords = load_keywords()

        # Process segments for template
        processed_segments = []
        for segment in all_segments:
            classes = ["segment"]
            types = []

            if segment["start"] in question_times:
                classes.append("question")
                types.append("question")
            if segment["start"] in emphasis_times:
                classes.append("emphasis")
                types.append("emphasis")

            # Highlight keywords
            text = segment["text"]
            has_keywords = False
            for keyword in custom_keywords:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                text = pattern.sub(f'<span class="keyword">{keyword}</span>', text)
                if pattern.search(segment["text"]):
                    has_keywords = True

            if has_keywords:
                classes.append("highlight")
                types.append("highlight")

            processed_segments.append(
                {
                    "classes": classes,
                    "types": types,
                    "timestamp_str": segment["timestamp_str"],
                    "highlighted_text": text,
                }
            )

        # Render template
        html_content = render_template(
            "transcript.html",
            session_id=results["session_id"],
            analysis=results["analysis"],
            segments=processed_segments,
        )

        # Save HTML file
        html_path = os.path.join(results["session_dir"], "searchable_transcript.html")
        with open(html_path, "w") as f:
            f.write(html_content)

        return html_path
