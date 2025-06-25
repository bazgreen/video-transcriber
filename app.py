from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import whisper
import ffmpeg
import os
import re
import json
from datetime import datetime, timedelta
from collections import Counter
import math
from werkzeug.utils import secure_filename
import tempfile
import shutil
import glob
import time
import threading
import multiprocessing
import logging
import functools
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

# Optional memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# === CONFIGURATION CONSTANTS ===

# File Upload Configuration
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500MB max file size
ALLOWED_FILE_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}

# Memory Management Constants
DEFAULT_MEMORY_PERCENT_LIMIT = 75
CONSERVATIVE_SYSTEM_TOTAL_GB = 8.0
CONSERVATIVE_SYSTEM_AVAILABLE_GB = 4.0
CONSERVATIVE_SYSTEM_USED_PERCENT = 50.0
CONSERVATIVE_PROCESS_RSS_MB = 100.0
CONSERVATIVE_PROCESS_VMS_MB = 200.0
MEMORY_PER_WORKER_GB = 0.6
SYSTEM_MEMORY_RESERVE_GB = 2.0

# Video Processing Constants
DEFAULT_CHUNK_DURATION_SECONDS = 300  # 5 minutes
MIN_CHUNK_DURATION_SECONDS = 60      # 1 minute
MAX_CHUNK_DURATION_SECONDS = 600     # 10 minutes
SHORT_VIDEO_CHUNK_LIMIT = 180        # 3 minutes for short videos
LONG_VIDEO_CHUNK_LIMIT = 420         # 7 minutes for long videos
SHORT_VIDEO_THRESHOLD = 600          # 10 minutes - threshold for short video
LONG_VIDEO_THRESHOLD = 3600          # 60 minutes - threshold for long video
DEFAULT_OVERLAP_SECONDS = 0
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# Performance Limits
MIN_WORKERS = 1
MAX_WORKERS_LIMIT = 14
DEFAULT_MAX_WORKERS = 4

# Content Analysis Constants
CONTEXT_WINDOW_CHARS = 50
MIN_KEYWORD_LENGTH = 2

# Time Constants
SECONDS_PER_MINUTE = 60
MILLISECONDS_PER_SECOND = 1000
BYTES_PER_MB = 1024 * 1024
BYTES_PER_GB = 1024 * 1024 * 1024

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE_BYTES
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'video-transcriber-secret-key')  # For SocketIO

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check for optional dependencies
if not PSUTIL_AVAILABLE:
    logger.warning("psutil not available - memory monitoring will use conservative estimates")


def is_valid_session_id(session_id):
    """Validate session_id to prevent path traversal attacks"""
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', session_id))

def is_safe_path(file_path, base_dir):
    """Check if file_path is within base_dir to prevent path traversal"""
    try:
        base_path = os.path.abspath(base_dir)
        requested_path = os.path.abspath(file_path)
        return requested_path.startswith(base_path)
    except (OSError, ValueError):
        return False

class MemoryManager:
    """Memory monitoring and management for efficient processing"""
    
    def __init__(self, max_memory_percent=DEFAULT_MEMORY_PERCENT_LIMIT):
        self.max_memory_percent = max_memory_percent
        self.available = PSUTIL_AVAILABLE
        if self.available:
            self.process = psutil.Process()
        self.lock = threading.Lock()
        
    def get_memory_info(self):
        """Get current memory usage information"""
        if not self.available:
            # Fallback when psutil is not available
            return {
                'system_total_gb': CONSERVATIVE_SYSTEM_TOTAL_GB,
                'system_available_gb': CONSERVATIVE_SYSTEM_AVAILABLE_GB,
                'system_used_percent': CONSERVATIVE_SYSTEM_USED_PERCENT,
                'process_rss_mb': CONSERVATIVE_PROCESS_RSS_MB,
                'process_vms_mb': CONSERVATIVE_PROCESS_VMS_MB
            }
            
        # System memory
        system_memory = psutil.virtual_memory()
        
        # Process memory
        process_memory = self.process.memory_info()
        
        return {
            'system_total_gb': system_memory.total / BYTES_PER_GB,
            'system_available_gb': system_memory.available / BYTES_PER_GB,
            'system_used_percent': system_memory.percent,
            'process_rss_mb': process_memory.rss / BYTES_PER_MB,
            'process_vms_mb': process_memory.vms / BYTES_PER_MB
        }
    
    def get_optimal_workers(self, min_workers=MIN_WORKERS, max_workers=None):
        """Calculate optimal number of workers based on available memory"""
        if max_workers is None:
            max_workers = min(multiprocessing.cpu_count(), DEFAULT_MAX_WORKERS)
            
        memory_info = self.get_memory_info()
        
        # Estimate memory per worker (Whisper model + processing overhead)
        memory_per_worker_gb = MEMORY_PER_WORKER_GB
        
        # Available memory for workers (reserve memory for system + main process)
        available_for_workers_gb = memory_info['system_available_gb'] - SYSTEM_MEMORY_RESERVE_GB
        
        # Calculate max workers based on memory
        memory_based_workers = max(MIN_WORKERS, int(available_for_workers_gb / memory_per_worker_gb))
        
        # Take minimum of CPU-based and memory-based limits
        optimal_workers = min(max_workers, memory_based_workers, multiprocessing.cpu_count())
        optimal_workers = max(min_workers, optimal_workers)
        
        logger.info(f"Memory analysis: {memory_info['system_available_gb']:.1f}GB available, "
                   f"optimal workers: {optimal_workers} (max: {max_workers})")
        
        return optimal_workers
    
    def check_memory_pressure(self):
        """Check if system is under memory pressure"""
        memory_info = self.get_memory_info()
        return memory_info['system_used_percent'] > self.max_memory_percent

# Global memory manager
memory_manager = MemoryManager()

class ProgressiveFileManager:
    """Progressive cleanup manager for temporary files during processing"""
    
    def __init__(self, max_temp_files=20):
        self.max_temp_files = max_temp_files
        self.temp_files = []
        self.lock = threading.Lock()
        
    def add_temp_file(self, file_path, file_type='audio'):
        """Add temporary file to cleanup queue with progressive management"""
        with self.lock:
            timestamp = time.time()
            self.temp_files.append({
                'path': file_path,
                'type': file_type,
                'timestamp': timestamp,
                'size': self.get_file_size(file_path)
            })
            
            # Progressive cleanup: remove oldest files if we exceed limit
            if len(self.temp_files) > self.max_temp_files:
                self._cleanup_oldest_files(keep_recent=self.max_temp_files)
    
    def get_file_size(self, file_path):
        """Get file size safely"""
        try:
            return os.path.getsize(file_path) if os.path.exists(file_path) else 0
        except OSError:
            return 0
    
    def _cleanup_oldest_files(self, keep_recent=10):
        """Clean up oldest temporary files"""
        if len(self.temp_files) <= keep_recent:
            return
            
        # Sort by timestamp (oldest first)
        self.temp_files.sort(key=lambda x: x['timestamp'])
        
        files_to_remove = self.temp_files[:-keep_recent]
        self.temp_files = self.temp_files[-keep_recent:]
        
        # Remove old files
        for file_info in files_to_remove:
            self._safe_remove_file(file_info['path'])
    
    def _safe_remove_file(self, file_path):
        """Safely remove a file with logging"""
        try:
            if os.path.exists(file_path):
                file_size = self.get_file_size(file_path)
                os.remove(file_path)
                logger.debug(f"Cleaned up temp file: {os.path.basename(file_path)} "
                           f"({file_size / (1024*1024):.1f}MB)")
        except OSError as e:
            logger.warning(f"Failed to remove temp file {file_path}: {e}")
    
    def cleanup_all(self):
        """Clean up all tracked temporary files"""
        with self.lock:
            total_size = 0
            for file_info in self.temp_files:
                total_size += file_info['size']
                self._safe_remove_file(file_info['path'])
            
            if self.temp_files:
                logger.info(f"Cleaned up {len(self.temp_files)} temp files "
                           f"({total_size / (1024*1024):.1f}MB total)")
            
            self.temp_files.clear()
    
    def get_cleanup_stats(self):
        """Get statistics about temporary files"""
        with self.lock:
            total_size = sum(f['size'] for f in self.temp_files)
            return {
                'count': len(self.temp_files),
                'total_size_mb': total_size / (1024*1024),
                'types': {t: len([f for f in self.temp_files if f['type'] == t]) 
                         for t in set(f['type'] for f in self.temp_files)}
            }

# Global progressive file manager
file_manager = ProgressiveFileManager()

# Ensure upload and results directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

class ModelManager:
    """Memory-efficient Whisper model management"""
    
    def __init__(self):
        self._model = None
        self._model_lock = threading.Lock()
        self._load_count = 0
        
    def get_model(self):
        """Get Whisper model with lazy loading and memory monitoring"""
        if self._model is None:
            with self._model_lock:
                if self._model is None:  # Double-check locking
                    logger.info("Loading Whisper model (small)...")
                    memory_before = memory_manager.get_memory_info()
                    
                    self._model = whisper.load_model("small")
                    self._load_count += 1
                    
                    memory_after = memory_manager.get_memory_info()
                    memory_used = memory_after['process_rss_mb'] - memory_before['process_rss_mb']
                    
                    logger.info(f"Whisper model loaded. Memory used: {memory_used:.1f}MB "
                               f"(Total process memory: {memory_after['process_rss_mb']:.1f}MB)")
        
        return self._model
    
    def clear_model(self):
        """Clear model from memory if needed"""
        with self._model_lock:
            if self._model is not None:
                logger.info("Clearing Whisper model from memory")
                del self._model
                self._model = None

# Global model manager
model_manager = ModelManager()

class ProgressTracker:
    """Real-time progress tracking for WebSocket communication"""
    
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()
    
    def start_session(self, session_id, total_chunks=0, video_duration=0):
        """Initialize a new progress tracking session"""
        with self.lock:
            self.sessions[session_id] = {
                'status': 'starting',
                'progress': 0,
                'current_task': 'Initializing...',
                'chunks_total': total_chunks,
                'chunks_completed': 0,
                'current_chunk': 0,
                'start_time': time.time(),
                'estimated_time': None,
                'video_duration': video_duration,
                'stage': 'initialization',
                'stage_progress': 0,
                'details': {}
            }
            logger.info(f"Started progress tracking for session {session_id}")
            self.emit_progress(session_id)
    
    def update_progress(self, session_id, **updates):
        """Update progress for a session"""
        with self.lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.update(updates)
                
                # Calculate estimated time remaining
                if session['progress'] > 0 and session['progress'] < 100:
                    elapsed = time.time() - session['start_time']
                    total_estimated = elapsed / (session['progress'] / 100)
                    session['estimated_time'] = max(0, total_estimated - elapsed)
                
                self.emit_progress(session_id)
                logger.debug(f"Progress update for {session_id}: {session['current_task']} "
                           f"({session['progress']:.1f}%)")
    
    def update_chunk_progress(self, session_id, chunk_number, chunk_total, task_description=""):
        """Update progress based on chunk completion"""
        if session_id not in self.sessions:
            return
            
        # Calculate overall progress (chunks are 70% of total work)
        chunk_progress = (chunk_number / chunk_total) * 70 if chunk_total > 0 else 0
        overall_progress = 20 + chunk_progress  # 20% for initial setup
        
        self.update_progress(
            session_id,
            current_chunk=chunk_number,
            chunks_completed=chunk_number,
            progress=overall_progress,
            current_task=f"Processing chunk {chunk_number}/{chunk_total}" + 
                         (f" - {task_description}" if task_description else ""),
            stage='transcription',
            stage_progress=chunk_progress
        )
    
    def complete_session(self, session_id, success=True, message="Processing complete!"):
        """Mark session as completed"""
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].update({
                    'status': 'completed' if success else 'error',
                    'progress': 100 if success else self.sessions[session_id]['progress'],
                    'current_task': message,
                    'stage': 'completed' if success else 'error'
                })
                self.emit_progress(session_id)
                logger.info(f"Session {session_id} marked as {'completed' if success else 'failed'}")
    
    def emit_progress(self, session_id):
        """Emit progress update via SocketIO"""
        if session_id in self.sessions:
            try:
                progress_data = self.sessions[session_id]
                logger.debug(f"Emitting progress for session {session_id}: {progress_data.get('progress', 0):.1f}% - {progress_data.get('current_task', 'Unknown')}")
                socketio.emit('progress_update', progress_data, room=session_id)
            except Exception as e:
                logger.warning(f"Failed to emit progress for session {session_id}: {e}")
    
    def get_session_progress(self, session_id):
        """Get current progress for a session"""
        with self.lock:
            return self.sessions.get(session_id, None)
    
    def cleanup_session(self, session_id):
        """Remove session from tracking"""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.debug(f"Cleaned up progress tracking for session {session_id}")

# Global progress tracker
progress_tracker = ProgressTracker()

class UserFriendlyError(Exception):
    """User-friendly error messages with solutions"""
    
    ERROR_SOLUTIONS = {
        'insufficient_memory': {
            'message': 'Not enough memory available for processing',
            'solution': 'Try reducing max workers or close other applications',
            'action': 'Reduce workers in Performance Monitor',
            'icon': '⚠️'
        },
        'large_file_size': {
            'message': 'File size exceeds recommended limits for optimal processing',
            'solution': 'Consider splitting the video or reducing quality',
            'action': 'Use video editing software to compress',
            'icon': '📁'
        },
        'unsupported_format': {
            'message': 'Video format not supported',
            'solution': 'Convert to MP4, AVI, or MOV format',
            'action': 'Use video converter tool like FFmpeg',
            'icon': '🎥'
        },
        'processing_timeout': {
            'message': 'Video processing took longer than expected',
            'solution': 'Try processing with fewer workers or smaller chunks',
            'action': 'Adjust settings in Performance Monitor',
            'icon': '⏱️'
        },
        'network_error': {
            'message': 'Network connection issue detected',
            'solution': 'Check your internet connection and try again',
            'action': 'Refresh page and retry upload',
            'icon': '🌐'
        },
        'storage_full': {
            'message': 'Insufficient storage space for processing',
            'solution': 'Free up disk space or process smaller files',
            'action': 'Clean up old results or temporary files',
            'icon': '💾'
        }
    }
    
    def __init__(self, error_type, details=None):
        self.error_type = error_type
        self.details = details or {}
        
        error_info = self.ERROR_SOLUTIONS.get(error_type, {
            'message': 'An unexpected error occurred',
            'solution': 'Please try again or contact support',
            'action': 'Refresh page and retry',
            'icon': '❌'
        })
        
        super().__init__(error_info['message'])
        self.solution = error_info['solution']
        self.action = error_info['action']
        self.icon = error_info['icon']
    
    def to_dict(self):
        """Convert error to dictionary for JSON response"""
        return {
            'type': 'user_friendly_error',
            'error_type': self.error_type,
            'message': str(self),
            'solution': self.solution,
            'action': self.action,
            'icon': self.icon,
            'details': self.details
        }

def handle_user_friendly_error(func):
    """Decorator to handle and convert exceptions to user-friendly errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UserFriendlyError:
            raise  # Re-raise user-friendly errors as-is
        except MemoryError:
            raise UserFriendlyError('insufficient_memory')
        except FileNotFoundError as e:
            if 'video' in str(e).lower():
                raise UserFriendlyError('unsupported_format')
            raise UserFriendlyError('storage_full')
        except TimeoutError:
            raise UserFriendlyError('processing_timeout')
        except Exception as e:
            # Log the original error for debugging
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            # Convert to generic user-friendly error
            raise UserFriendlyError('unknown_error', {'original_error': str(e)})
    
    return wrapper

# ...existing code...

def init_worker():
    """Initialize worker process - now more memory efficient"""
    logger.info("Worker process initialized (model will be loaded on demand)")

def get_model():
    """Get the Whisper model with efficient memory management"""
    return model_manager.get_model()

def process_chunk_parallel(chunk_info):
    """Process a single chunk in parallel - for use with ProcessPoolExecutor"""
    # Validate chunk_info format
    if not isinstance(chunk_info, tuple) or len(chunk_info) != 4:
        raise ValueError("Invalid chunk_info format. Expected a tuple with 4 elements: (chunk_path, audio_path, start_time, filename).")
    
    try:
        chunk_path, audio_path, start_time, filename = chunk_info
        
        # Extract audio
        (
            ffmpeg
            .input(chunk_path)
            .output(audio_path, acodec='pcm_s16le', ac=AUDIO_CHANNELS, ar=str(AUDIO_SAMPLE_RATE))
            .overwrite_output()
            .run(quiet=True)
        )
        
        # Get model and transcribe
        model = get_model()
        result = model.transcribe(audio_path, word_timestamps=True)
        
        # Format with timestamps
        timestamped_segments = []
        for segment in result['segments']:
            adjusted_segment = {
                'start': segment['start'] + start_time,
                'end': segment['end'] + start_time,
                'text': segment['text'].strip(),
                'timestamp_str': format_timestamp(segment['start'] + start_time)
            }
            timestamped_segments.append(adjusted_segment)
        
        # Register audio file for progressive cleanup
        file_manager.add_temp_file(audio_path, 'audio')
            
        return {
            'filename': filename,
            'transcription': result['text'],
            'segments': timestamped_segments,
            'start_time': start_time,
            'success': True
        }
    except Exception as e:
        return {
            'filename': filename,
            'error': str(e),
            'start_time': start_time,
            'success': False
        }

def format_timestamp(seconds):
    """Format seconds as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# Load keywords from config file
def load_keywords():
    keywords_file = 'config/keywords_config.json'
    try:
        with open(keywords_file, 'r') as f:
            config = json.load(f)
            return config.get('keywords', [])
    except FileNotFoundError:
        # If file doesn't exist, create it with minimal default keywords
        default_keywords = []
        save_keywords(default_keywords)
        return default_keywords

def save_keywords(keywords):
    keywords_file = 'config/keywords_config.json'
    temp_file = keywords_file + '.tmp'
    
    # Write to temporary file first
    try:
        with open(temp_file, 'w') as f:
            json.dump({'keywords': keywords}, f, indent=4)
        
        # Atomic rename (on POSIX systems)
        os.replace(temp_file, keywords_file)
    except Exception as e:
        # Clean up temp file if something goes wrong
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e

# Keywords for content analysis
CUSTOM_KEYWORDS = load_keywords()

# Emphasis cue patterns
EMPHASIS_PATTERNS = [
    r"make sure.*",
    r"don't forget.*",
    r"this will.*be.*assessment.*",
    r"important.*to.*remember.*",
    r"pay attention.*",
    r"note that.*",
    r"be careful.*",
    r"remember.*"
]

# Question patterns
QUESTION_PATTERNS = [
    r"what.*\?",
    r"how.*\?", 
    r"why.*\?",
    r"when.*\?",
    r"where.*\?",
    r"which.*\?",
    r"who.*\?"
]

class VideoTranscriber:
    def __init__(self):
        self.model = None
        # Memory-aware performance tuning
        self.max_workers = memory_manager.get_optimal_workers()
        self.chunk_duration = DEFAULT_CHUNK_DURATION_SECONDS  # Default chunk duration, can be adjusted for performance
        
        # Log memory and worker configuration
        memory_info = memory_manager.get_memory_info()
        logger.info(f"VideoTranscriber initialized with {self.max_workers} max workers. "
                   f"System memory: {memory_info['system_total_gb']:.1f}GB total, "
                   f"{memory_info['system_available_gb']:.1f}GB available")
        
    def load_model(self):
        if self.model is None:
            self.model = whisper.load_model("small")
        return self.model
    
    def split_video(self, input_path, output_dir, chunk_duration=None):
        """Split video into chunks of specified duration (default 5 minutes) with parallel processing"""
        chunks = []
        
        # Use instance default if not specified
        if chunk_duration is None:
            chunk_duration = self.chunk_duration
        
        # Get video info with proper error handling
        try:
            probe = ffmpeg.probe(input_path)
            # Check if streams exist and have duration
            if 'streams' not in probe or len(probe['streams']) == 0:
                raise ValueError(f"No streams found in video file: {input_path}")
            
            # Find video stream with duration
            duration = None
            for stream in probe['streams']:
                if 'duration' in stream:
                    duration = float(stream['duration'])
                    break
            
            if duration is None:
                # Try to get duration from format
                if 'format' in probe and 'duration' in probe['format']:
                    duration = float(probe['format']['duration'])
                else:
                    raise ValueError(f"Could not determine video duration for: {input_path}")
                    
        except ffmpeg.Error as e:
            raise Exception(f"Failed to probe video file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error analyzing video file: {str(e)}")
        
        # Adaptive chunk sizing for better performance
        # For shorter videos, use smaller chunks for faster parallel processing
        if duration < SHORT_VIDEO_THRESHOLD:
            chunk_duration = min(chunk_duration, SHORT_VIDEO_CHUNK_LIMIT)
        elif duration > LONG_VIDEO_THRESHOLD:
            chunk_duration = min(chunk_duration, LONG_VIDEO_CHUNK_LIMIT)
        
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
            
            chunk_tasks.append((input_path, chunk_path, start_time, actual_duration, chunk_name))
            
            chunks.append({
                'filename': chunk_name,
                'path': chunk_path,
                'start_time': start_time,
                'duration': actual_duration
            })
        
        # Process chunks in parallel using ThreadPoolExecutor (I/O bound for ffmpeg)
        with ThreadPoolExecutor(max_workers=min(self.max_workers, num_chunks)) as executor:
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
    
    def _split_single_chunk(self, input_path, chunk_path, start_time, duration, chunk_name):
        """Split a single video chunk - helper method for parallel processing"""
        try:
            (
                ffmpeg
                .input(input_path, ss=start_time, t=duration)
                .output(chunk_path, vcodec='libx264', acodec='aac')
                .overwrite_output()
                .run(quiet=True)
            )
            # Register chunk for progressive cleanup
            file_manager.add_temp_file(chunk_path, 'video')
        except Exception as e:
            raise Exception(f"Failed to split chunk {chunk_name}: {str(e)}")
    
    def extract_audio(self, video_path, audio_path):
        """Extract audio from video"""
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='pcm_s16le', ac=AUDIO_CHANNELS, ar=str(AUDIO_SAMPLE_RATE))
            .overwrite_output()
            .run(quiet=True)
        )
    
    def transcribe_with_timestamps(self, audio_path):
        """Transcribe audio with timestamp information"""
        model = self.load_model()
        result = model.transcribe(audio_path, word_timestamps=True)
        
        # Format with timestamps
        timestamped_segments = []
        for segment in result['segments']:
            timestamped_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'timestamp_str': self.format_timestamp(segment['start'])
            })
        
        return {
            'text': result['text'],
            'segments': timestamped_segments
        }
    
    def format_timestamp(self, seconds):
        """Format seconds as MM:SS or HH:MM:SS"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        try:
            probe = ffmpeg.probe(video_path)
            duration = float(probe['streams'][0]['duration'])
            return duration
        except Exception as e:
            logger.warning(f"Could not get video duration: {e}")
            return 0
    
    def analyze_content(self, text, segments):
        """Analyze content for keywords, questions, and emphasis cues"""
        analysis = {
            'keyword_matches': [],
            'questions': [],
            'emphasis_cues': [],
            'keyword_frequency': {},
            'total_words': len(text.split())
        }
        
        # Keyword analysis
        for keyword in CUSTOM_KEYWORDS:
            pattern = re.compile(f'.{{0,{CONTEXT_WINDOW_CHARS}}}' + re.escape(keyword) + f'.{{0,{CONTEXT_WINDOW_CHARS}}}', re.IGNORECASE)
            matches = pattern.findall(text)
            if matches:
                analysis['keyword_matches'].append({
                    'keyword': keyword,
                    'matches': matches,
                    'count': len(matches)
                })
        
        # Count keyword frequency
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = Counter(words)
        
        # Filter for relevant keywords
        for keyword in CUSTOM_KEYWORDS:
            if keyword.lower() in word_freq:
                analysis['keyword_frequency'][keyword] = word_freq[keyword.lower()]
        
        # Find questions in segments
        for segment in segments:
            for pattern in QUESTION_PATTERNS:
                if re.search(pattern, segment['text'], re.IGNORECASE):
                    analysis['questions'].append({
                        'timestamp': segment['timestamp_str'],
                        'text': segment['text'].strip(),
                        'start': segment['start']
                    })
                    break
        
        # Find emphasis cues
        for segment in segments:
            for pattern in EMPHASIS_PATTERNS:
                if re.search(pattern, segment['text'], re.IGNORECASE):
                    analysis['emphasis_cues'].append({
                        'timestamp': segment['timestamp_str'],
                        'text': segment['text'].strip(),
                        'start': segment['start']
                    })
                    break
        
        return analysis
    
    def process_video(self, video_path, session_name="", original_filename=""):
        """Complete video processing pipeline"""
        session_id, session_dir, metadata, results = self._initialize_session(session_name, original_filename)
        
        try:
            self._process_video_chunks(video_path, session_id, session_dir, results)
            self._finalize_session(session_id, session_dir, metadata, results)
            return results
            
        except Exception as e:
            # Handle errors and update progress
            error_message = f"Processing failed: {str(e)}"
            logger.error(error_message)
            progress_tracker.complete_session(session_id, success=False, message=error_message)
            raise
    
    def _initialize_session(self, session_name="", original_filename=""):
        """Initialize a new processing session"""
        # Create session directory
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_name:
            session_id = f"{session_name}_{session_id}"
        
        session_dir = os.path.join(app.config['RESULTS_FOLDER'], session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Store session metadata
        metadata = {
            'session_id': session_id,
            'session_name': session_name,
            'original_filename': original_filename,
            'created_at': datetime.now().isoformat(),
            'status': 'processing'
        }
        
        results = {
            'session_id': session_id,
            'session_dir': session_dir,
            'chunks': [],
            'full_transcript': '',
            'analysis': {},
            'html_file': None
        }
        
        return session_id, session_dir, metadata, results
    
    def _process_video_chunks(self, video_path, session_id, session_dir, results):
        """Process video chunks and transcribe them"""
        # Initialize progress tracking
        progress_tracker.start_session(session_id)
        progress_tracker.update_progress(session_id, 
                                       current_task="Analyzing video file...", 
                                       progress=5,
                                       stage='analysis')
        
        # Split video into chunks
        chunks = self.split_video(video_path, session_dir)
        
        # Update progress after video splitting
        progress_tracker.start_session(session_id, 
                                     total_chunks=len(chunks),
                                     video_duration=self.get_video_duration(video_path))
        progress_tracker.update_progress(session_id,
                                       current_task=f"Video split into {len(chunks)} chunks. Starting transcription...",
                                       progress=15,
                                       stage='preparation')
        
        # Process chunks and combine results
        all_segments, all_text = self._transcribe_chunks_parallel(session_id, session_dir, chunks)
        
        # Store results
        results['chunks'] = all_segments
        results['full_transcript'] = '\n'.join(all_text)
        
        # Analyze content
        progress_tracker.update_progress(session_id,
                                       current_task="Analyzing content for keywords and insights...",
                                       progress=90,
                                       stage='analysis')
        results['analysis'] = self.analyze_content(results['full_transcript'], all_segments)
    
    def _transcribe_chunks_parallel(self, session_id, session_dir, chunks):
        """Transcribe video chunks in parallel"""
        all_segments = []
        all_text = []
        
        # Process chunks in parallel
        chunk_info_list = []
        for chunk in chunks:
            audio_path = os.path.join(session_dir, f"{os.path.splitext(chunk['filename'])[0]}.wav")
            chunk_info_list.append((
                chunk['path'],
                audio_path,
                chunk['start_time'],
                chunk['filename']
            ))
        
        # Use ProcessPoolExecutor for CPU-intensive transcription work with memory monitoring
        completed_chunks = []
        
        # Dynamic memory-aware worker calculation
        memory_info = memory_manager.get_memory_info()
        optimal_workers = memory_manager.get_optimal_workers(max_workers=self.max_workers)
        num_workers = min(optimal_workers, len(chunks))
        
        logger.info(f"Processing {len(chunks)} chunks in parallel using {num_workers} workers "
                   f"(Memory: {memory_info['system_used_percent']:.1f}% used, "
                   f"{memory_info['system_available_gb']:.1f}GB available)")
        
        with ProcessPoolExecutor(max_workers=num_workers, initializer=init_worker) as executor:
            # Submit all chunk processing tasks
            futures = {executor.submit(process_chunk_parallel, chunk_info): chunk_info for chunk_info in chunk_info_list}
            
            # Collect results as they complete with memory monitoring
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    if result['success']:
                        completed_chunks.append(result)
                        
                        # Update progress for each completed chunk
                        progress_tracker.update_chunk_progress(session_id, i + 1, len(chunks), 
                                                             f"Transcribed {result['filename']}")
                        
                        # Periodic memory monitoring (every 25% of chunks)
                        if (i + 1) % max(1, len(chunks) // 4) == 0:
                            current_memory = memory_manager.get_memory_info()
                            logger.info(f"Completed chunk {i+1}/{len(chunks)}: {result['filename']} "
                                       f"(Memory: {current_memory['process_rss_mb']:.0f}MB process, "
                                       f"{current_memory['system_used_percent']:.1f}% system)")
                            
                            # Check for memory pressure
                            if memory_manager.check_memory_pressure():
                                logger.warning(f"High memory usage detected: {current_memory['system_used_percent']:.1f}%")
                        else:
                            logger.info(f"Completed chunk {i+1}/{len(chunks)}: {result['filename']}")
                    else:
                        logger.error(f"Error processing chunk {result['filename']}: {result.get('error', 'Unknown error')}")
                        # Update progress even for failed chunks
                        progress_tracker.update_chunk_progress(session_id, i + 1, len(chunks), 
                                                             f"Error in {result['filename']}")
                except Exception as e:
                    logger.error(f"Exception processing chunk: {e}")
                    # Update progress for exception cases
                    progress_tracker.update_chunk_progress(session_id, i + 1, len(chunks), 
                                                         f"Exception processing chunk")
        
        # Sort results by start time to maintain order
        completed_chunks.sort(key=lambda x: x['start_time'])
        
        # Update progress for final processing stages
        progress_tracker.update_progress(session_id,
                                       current_task="Combining transcription results...",
                                       progress=85,
                                       stage='post_processing')
        
        # Combine results
        for chunk_result in completed_chunks:
            all_segments.extend(chunk_result['segments'])
            all_text.append(f"\n\n--- {chunk_result['filename']} [{format_timestamp(chunk_result['start_time'])}] ---\n\n{chunk_result['transcription']}")
        
        return all_segments, all_text
    
    def _finalize_session(self, session_id, session_dir, metadata, results):
        """Finalize session processing and generate outputs"""
        # Update metadata with final stats
        chunks_count = len(results['chunks'])
        metadata.update({
            'status': 'completed',
            'total_chunks': chunks_count,
            'total_words': results['analysis']['total_words'],
            'keywords_found': len(results['analysis']['keyword_matches']),
            'questions_found': len(results['analysis']['questions']),
            'emphasis_cues_found': len(results['analysis']['emphasis_cues']),
            'processing_time': (datetime.now() - datetime.fromisoformat(metadata['created_at'])).total_seconds()
        })
        
        # Save metadata
        with open(os.path.join(session_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update progress for final generation
        progress_tracker.update_progress(session_id,
                                       current_task="Generating output files...",
                                       progress=95,
                                       stage='finalization')
        
        # Generate outputs
        self.save_results(results)
        results['html_file'] = self.generate_html_transcript(results)
        results['metadata'] = metadata
        
        # Complete progress tracking
        progress_tracker.complete_session(session_id, success=True, 
                                        message=f"Processing complete! Transcribed {chunks_count} chunks, found {results['analysis']['total_words']} words.")
        
        # Clean up all temporary files using progressive file manager
        cleanup_stats = file_manager.get_cleanup_stats()
        logger.info(f"Final cleanup: {cleanup_stats['count']} temp files, "
                   f"{cleanup_stats['total_size_mb']:.1f}MB")
        file_manager.cleanup_all()
    
    def save_results(self, results):
        """Save transcription results to files"""
        session_dir = results['session_dir']
        
        # Save full transcript
        with open(os.path.join(session_dir, 'full_transcript.txt'), 'w') as f:
            f.write(results['full_transcript'])
        
        # Save analysis results
        with open(os.path.join(session_dir, 'analysis.json'), 'w') as f:
            json.dump(results['analysis'], f, indent=2)
        
        # Save keyword highlights
        with open(os.path.join(session_dir, 'assessment_mentions.txt'), 'w') as f:
            f.write("Assessment-Related Content:\n\n")
            for match in results['analysis']['keyword_matches']:
                f.write(f"\n🔹 Keyword: **{match['keyword']}** ({match['count']} mentions)\n")
                for text in match['matches']:
                    f.write(f"- {text.strip()}\n")
        
        # Save questions
        with open(os.path.join(session_dir, 'questions.txt'), 'w') as f:
            f.write("Questions Detected:\n\n")
            for q in results['analysis']['questions']:
                f.write(f"[{q['timestamp']}] {q['text']}\n\n")
        
        # Save emphasis cues
        with open(os.path.join(session_dir, 'emphasis_cues.txt'), 'w') as f:
            f.write("Emphasis Cues:\n\n")
            for cue in results['analysis']['emphasis_cues']:
                f.write(f"[{cue['timestamp']}] {cue['text']}\n\n")
    
    def generate_html_transcript(self, results):
        """Generate searchable HTML transcript using template"""
        # Prepare all segments with metadata
        all_segments = []
        for chunk in results['chunks']:
            all_segments.extend(chunk['segments'])
        
        # Sort by timestamp
        all_segments.sort(key=lambda x: x['start'])
        
        # Create sets for quick lookup
        question_times = {q['start'] for q in results['analysis']['questions']}
        emphasis_times = {e['start'] for e in results['analysis']['emphasis_cues']}
        
        # Process segments for template
        processed_segments = []
        for segment in all_segments:
            classes = ['segment']
            types = []
            
            if segment['start'] in question_times:
                classes.append('question')
                types.append('question')
            if segment['start'] in emphasis_times:
                classes.append('emphasis')
                types.append('emphasis')
            
            # Highlight keywords
            text = segment['text']
            has_keywords = False
            for keyword in CUSTOM_KEYWORDS:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                text = pattern.sub(f'<span class="keyword">{keyword}</span>', text)
                if pattern.search(segment['text']):
                    has_keywords = True
            
            if has_keywords:
                classes.append('highlight')
                types.append('highlight')
            
            processed_segments.append({
                'classes': classes,
                'types': types,
                'timestamp_str': segment['timestamp_str'],
                'highlighted_text': text
            })
        
        # Render template
        html_content = render_template('transcript.html',
                                     session_id=results['session_id'],
                                     analysis=results['analysis'],
                                     segments=processed_segments)
        
        # Save HTML file
        html_path = os.path.join(results['session_dir'], 'searchable_transcript.html')
        with open(html_path, 'w') as f:
            f.write(html_content)
        
        return html_path

# Initialize transcriber
transcriber = VideoTranscriber()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@handle_user_friendly_error
def upload_file():
    if 'video' not in request.files:
        raise UserFriendlyError('unsupported_format', {'reason': 'No file uploaded'})
    
    file = request.files['video']
    if file.filename == '':
        raise UserFriendlyError('unsupported_format', {'reason': 'No file selected'})
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        raise UserFriendlyError('unsupported_format', {
            'current_format': file_ext,
            'supported_formats': list(ALLOWED_FILE_EXTENSIONS)
        })
    
    # Enhanced file size validation with context
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    file_size_mb = file_size / (1024 * 1024)
    if file_size > 500 * 1024 * 1024:  # 500MB
        raise UserFriendlyError('large_file_size', {
            'file_size_mb': f"{file_size_mb:.1f}",
            'max_size_mb': '500'
        })
    
    # Check available memory before processing
    memory_info = memory_manager.get_memory_info()
    if memory_info['system_used_percent'] > 90:
        raise UserFriendlyError('insufficient_memory', {
            'current_usage': f"{memory_info['system_used_percent']:.1f}%",
            'available_gb': f"{memory_info['system_available_gb']:.1f}"
        })
    
    session_name = request.form.get('session_name', '').strip()
    
    # Validate session name
    if not session_name:
        return jsonify({
            "type": "validation_error",
            "message": "Session name is required and cannot be empty",
            "solution": "Please enter a descriptive name for your video session",
            "action": "Fill in the session name field",
            "icon": "📝"
        }), 400
    
    # Remove potentially problematic characters
    session_name = re.sub(r'[^a-zA-Z0-9_-]', '_', session_name)
    # Limit length
    session_name = session_name[:50]
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(upload_path)
    except IOError:
        raise UserFriendlyError('storage_full')
    
    try:
        # Process video
        results = transcriber.process_video(upload_path, session_name, file.filename)
        
        return jsonify({
            'success': True,
            'session_id': results['session_id'],
            'message': 'Video processed successfully!',
            'stats': {
                'chunks': len(results.get('chunks', [])),
                'words': results.get('analysis', {}).get('total_words', 0),
                'duration': results.get('metadata', {}).get('processing_time', 0)
            }
        })
    
    except UserFriendlyError as e:
        return jsonify(e.to_dict()), 400
    except Exception as e:
        logger.error(f"Upload processing error: {str(e)}")
        error = UserFriendlyError('processing_timeout', {'original_error': str(e)})
        return jsonify(error.to_dict()), 500
    
    finally:
        # Clean up uploaded file
        if os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except OSError:
                logger.warning(f"Could not remove uploaded file: {upload_path}")

@app.route('/results/<session_id>')
def view_results(session_id):
    # Validate session_id to prevent path traversal
    if not is_valid_session_id(session_id):
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session_dir = os.path.join(app.config['RESULTS_FOLDER'], session_id)
    if not os.path.exists(session_dir):
        return jsonify({'error': 'Session not found'}), 404
    
    # Load analysis results
    analysis_path = os.path.join(session_dir, 'analysis.json')
    if os.path.exists(analysis_path):
        with open(analysis_path, 'r') as f:
            analysis = json.load(f)
    else:
        analysis = {}
    
    return render_template('results.html', session_id=session_id, analysis=analysis)

@app.route('/download/<session_id>/<filename>')
def download_file(session_id, filename):
    # Validate inputs to prevent path traversal
    if not is_valid_session_id(session_id):
        return jsonify({'error': 'Invalid session ID'}), 400
    
    # Validate filename
    if not re.match(r'^[a-zA-Z0-9_.-]+$', filename) or '..' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    session_dir = os.path.join(app.config['RESULTS_FOLDER'], session_id)
    file_path = os.path.join(session_dir, filename)
    
    # Ensure the file path is within the session directory
    if not is_safe_path(file_path, session_dir):
        return jsonify({'error': 'Access denied'}), 403
    
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/transcript/<session_id>')
def view_transcript(session_id):
    # Validate session_id to prevent path traversal
    if not is_valid_session_id(session_id):
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session_dir = os.path.join(app.config['RESULTS_FOLDER'], session_id)
    html_path = os.path.join(session_dir, 'searchable_transcript.html')
    
    if os.path.exists(html_path):
        return send_file(html_path)
    else:
        return jsonify({'error': 'Transcript not found'}), 404

@app.route('/sessions')
def list_sessions():
    """List all previous transcription sessions"""
    sessions = []
    results_dir = app.config['RESULTS_FOLDER']
    
    if os.path.exists(results_dir):
        for session_folder in sorted(os.listdir(results_dir), reverse=True):
            session_path = os.path.join(results_dir, session_folder)
            if os.path.isdir(session_path):
                metadata_path = os.path.join(session_path, 'metadata.json')
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        sessions.append(metadata)
                    except (json.JSONDecodeError, IOError):
                        # Handle corrupted metadata by creating basic info
                        sessions.append({
                            'session_id': session_folder,
                            'session_name': '',
                            'original_filename': 'Unknown',
                            'created_at': datetime.fromtimestamp(os.path.getctime(session_path)).isoformat(),
                            'status': 'unknown'
                        })
                else:
                    # Legacy session without metadata - try to extract session name from folder
                    session_name = ''
                    original_filename = 'Unknown'
                    
                    # Try to parse session folder name (format: SessionName_YYYYMMDD_HHMMSS)
                    parts = session_folder.split('_')
                    if len(parts) >= 3:
                        # Check if last two parts look like date and time
                        if (len(parts[-2]) == 8 and parts[-2].isdigit() and 
                            len(parts[-1]) == 6 and parts[-1].isdigit()):
                            # Extract session name (everything except the last two parts)
                            session_name = '_'.join(parts[:-2])
                            # Guess original filename based on session name
                            if session_name:
                                original_filename = f"{session_name.split('_')[-1]}.mp4"
                    
                    sessions.append({
                        'session_id': session_folder,
                        'session_name': session_name,
                        'original_filename': original_filename,
                        'created_at': datetime.fromtimestamp(os.path.getctime(session_path)).isoformat(),
                        'status': 'completed'
                    })
    
    return render_template('sessions.html', sessions=sessions)

@app.route('/sessions/delete/<session_id>', methods=['POST'])
def delete_session(session_id):
    """Delete a transcription session"""
    # Validate session_id to prevent path traversal
    if not is_valid_session_id(session_id):
        return jsonify({'error': 'Invalid session ID'}), 400
    
    session_dir = os.path.join(app.config['RESULTS_FOLDER'], session_id)
    
    # Ensure the path is within the results folder
    if not os.path.abspath(session_dir).startswith(os.path.abspath(app.config['RESULTS_FOLDER'])):
        return jsonify({'error': 'Access denied'}), 403
    
    if os.path.exists(session_dir):
        try:
            shutil.rmtree(session_dir)
            return jsonify({'success': True, 'message': 'Session deleted successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Session not found'}), 404

@app.route('/sessions/search')
def search_sessions():
    """Search sessions by name or content"""
    query = request.args.get('q', '').lower()
    sessions = []
    results_dir = app.config['RESULTS_FOLDER']
    
    if os.path.exists(results_dir) and query:
        for session_folder in os.listdir(results_dir):
            session_path = os.path.join(results_dir, session_folder)
            if os.path.isdir(session_path):
                metadata_path = os.path.join(session_path, 'metadata.json')
                
                # Check metadata
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        # Search in session name and filename
                        if (query in metadata.get('session_name', '').lower() or 
                            query in metadata.get('original_filename', '').lower()):
                            sessions.append(metadata)
                            continue
                    except (json.JSONDecodeError, IOError):
                        pass
                
                # Search in transcript content
                transcript_path = os.path.join(session_path, 'full_transcript.txt')
                if os.path.exists(transcript_path):
                    try:
                        with open(transcript_path, 'r') as f:
                            content = f.read().lower()
                        if query in content:
                            # Load metadata if available
                            if os.path.exists(metadata_path):
                                with open(metadata_path, 'r') as f:
                                    metadata = json.load(f)
                            else:
                                # Legacy session without metadata - try to extract session name from folder
                                session_name = ''
                                original_filename = 'Unknown'
                                
                                # Try to parse session folder name (format: SessionName_YYYYMMDD_HHMMSS)
                                parts = session_folder.split('_')
                                if len(parts) >= 3:
                                    # Check if last two parts look like date and time
                                    if (len(parts[-2]) == 8 and parts[-2].isdigit() and 
                                        len(parts[-1]) == 6 and parts[-1].isdigit()):
                                        # Extract session name (everything except the last two parts)
                                        session_name = '_'.join(parts[:-2])
                                        # Guess original filename based on session name
                                        if session_name:
                                            original_filename = f"{session_name.split('_')[-1]}.mp4"
                                
                                metadata = {
                                    'session_id': session_folder,
                                    'session_name': session_name,
                                    'original_filename': original_filename,
                                    'created_at': datetime.fromtimestamp(os.path.getctime(session_path)).isoformat(),
                                    'status': 'completed'
                                }
                            sessions.append(metadata)
                    except IOError:
                        pass
    
    return jsonify(sessions)

@app.route('/config')
def config():
    """Show keyword configuration page"""
    return render_template('config.html', keywords=CUSTOM_KEYWORDS)

@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    """Get current keywords"""
    return jsonify({'success': True, 'keywords': CUSTOM_KEYWORDS})

@app.route('/api/keywords', methods=['POST'])
def update_keywords():
    """Update keywords list"""
    global CUSTOM_KEYWORDS
    data = request.get_json()
    
    if 'keywords' not in data:
        return jsonify({'success': False, 'error': 'No keywords provided'}), 400
    
    keywords = data['keywords']
    
    # Validate keywords
    if not isinstance(keywords, list):
        return jsonify({'success': False, 'error': 'Keywords must be a list'}), 400
    
    # Clean and validate each keyword
    cleaned_keywords = []
    for keyword in keywords:
        if isinstance(keyword, str) and keyword.strip():
            cleaned_keywords.append(keyword.strip())
    
    if not cleaned_keywords:
        return jsonify({'success': False, 'error': 'At least one valid keyword is required'}), 400
    
    # Save to file and update global variable
    save_keywords(cleaned_keywords)
    CUSTOM_KEYWORDS = cleaned_keywords
    
    return jsonify({'success': True, 'keywords': cleaned_keywords})

@app.route('/api/keywords/add', methods=['POST'])
def add_keyword():
    """Add a single keyword"""
    global CUSTOM_KEYWORDS
    data = request.get_json()
    
    if 'keyword' not in data:
        return jsonify({'success': False, 'error': 'No keyword provided'}), 400
    
    keyword = data['keyword'].strip()
    
    if not keyword:
        return jsonify({'success': False, 'error': 'Keyword cannot be empty'}), 400
    
    if keyword.lower() in [k.lower() for k in CUSTOM_KEYWORDS]:
        return jsonify({'success': False, 'error': 'Keyword already exists'}), 400
    
    # Add keyword and save
    CUSTOM_KEYWORDS.append(keyword)
    save_keywords(CUSTOM_KEYWORDS)
    
    return jsonify({'success': True, 'keywords': CUSTOM_KEYWORDS})

@app.route('/api/keywords/remove', methods=['POST'])
def remove_keyword():
    """Remove a keyword"""
    global CUSTOM_KEYWORDS
    data = request.get_json()
    
    if 'keyword' not in data:
        return jsonify({'success': False, 'error': 'No keyword provided'}), 400
    
    keyword = data['keyword']
    
    if keyword not in CUSTOM_KEYWORDS:
        return jsonify({'success': False, 'error': 'Keyword not found'}), 404
    
    # Remove keyword and save
    CUSTOM_KEYWORDS.remove(keyword)
    save_keywords(CUSTOM_KEYWORDS)
    
    return jsonify({'success': True, 'keywords': CUSTOM_KEYWORDS})

@app.route('/api/performance', methods=['GET'])
def get_performance_info():
    """Get current performance settings and system information"""
    memory_info = memory_manager.get_memory_info()
    
    # Get current transcriber settings
    performance_data = {
        'system_info': {
            'cpu_count': multiprocessing.cpu_count(),
            'memory_total_gb': memory_info['system_total_gb'],
            'memory_available_gb': memory_info['system_available_gb'],
            'memory_used_percent': memory_info['system_used_percent'],
            'process_memory_mb': memory_info['process_rss_mb'],
            'whisper_model': 'small',
            'psutil_available': PSUTIL_AVAILABLE
        },
        'current_settings': {
            'max_workers': transcriber.max_workers,
            'chunk_duration': transcriber.chunk_duration,
            'optimal_workers': memory_manager.get_optimal_workers(max_workers=transcriber.max_workers)
        },
        'file_manager_stats': file_manager.get_cleanup_stats(),
        'active_sessions': len(progress_tracker.sessions),
        'memory_pressure': memory_manager.check_memory_pressure(),
        'recommendations': _get_performance_recommendations()
    }
    
    return jsonify({'success': True, 'data': performance_data})

@app.route('/api/performance', methods=['POST'])
def update_performance_settings():
    """Update performance settings"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    try:
        # Update chunk duration if provided
        if 'chunk_duration' in data:
            chunk_duration = int(data['chunk_duration'])
            if MIN_CHUNK_DURATION_SECONDS <= chunk_duration <= MAX_CHUNK_DURATION_SECONDS:
                transcriber.chunk_duration = chunk_duration
            else:
                return jsonify({'success': False, 'error': f'Chunk duration must be between {MIN_CHUNK_DURATION_SECONDS} and {MAX_CHUNK_DURATION_SECONDS} seconds (provided: {chunk_duration})'}), 400
        
        # Update max workers if provided
        if 'max_workers' in data:
            max_workers = int(data['max_workers'])
            max_cpu_limit = min(multiprocessing.cpu_count(), MAX_WORKERS_LIMIT)  # Allow up to CPU count or limit, whichever is lower
            if MIN_WORKERS <= max_workers <= max_cpu_limit:
                transcriber.max_workers = max_workers
            else:
                return jsonify({'success': False, 'error': f'Max workers must be between 1 and {max_cpu_limit} (provided: {max_workers})'}), 400
        
        return jsonify({
            'success': True, 
            'message': 'Performance settings updated',
            'current_settings': {
                'max_workers': transcriber.max_workers,
                'chunk_duration': transcriber.chunk_duration
            }
        })
        
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to update settings: {str(e)}'}), 500

@app.route('/api/memory', methods=['GET'])
def get_memory_info():
    """Get detailed memory information"""
    memory_info = memory_manager.get_memory_info()
    
    # Add process-specific memory details if psutil is available
    if PSUTIL_AVAILABLE:
        try:
            import psutil
            process = psutil.Process()
            memory_details = {
                'system': {
                    'total_gb': memory_info['system_total_gb'],
                    'available_gb': memory_info['system_available_gb'],
                    'used_percent': memory_info['system_used_percent'],
                    'free_gb': memory_info['system_available_gb']
                },
                'process': {
                    'rss_mb': memory_info['process_rss_mb'],
                    'vms_mb': memory_info['process_vms_mb'],
                    'percent': process.memory_percent(),
                    'num_threads': process.num_threads()
                },
                'recommendations': _get_memory_recommendations(memory_info)
            }
        except Exception as e:
            logger.warning(f"Error getting detailed memory info: {e}")
            memory_details = {
                'system': {
                    'total_gb': memory_info['system_total_gb'],
                    'available_gb': memory_info['system_available_gb'],
                    'used_percent': memory_info['system_used_percent']
                },
                'process': {
                    'rss_mb': memory_info['process_rss_mb'],
                    'vms_mb': memory_info['process_vms_mb']
                }
            }
    else:
        memory_details = {
            'system': {
                'total_gb': memory_info['system_total_gb'],
                'available_gb': memory_info['system_available_gb'],
                'used_percent': memory_info['system_used_percent']
            },
            'process': {
                'rss_mb': memory_info['process_rss_mb'],
                'vms_mb': memory_info['process_vms_mb']
            },
            'note': 'Install psutil for detailed memory monitoring'
        }
    
    return jsonify({'success': True, 'data': memory_details})

def _get_performance_recommendations():
    """Generate performance optimization recommendations"""
    recommendations = []
    memory_info = memory_manager.get_memory_info()
    
    # Memory-based recommendations
    if memory_info['system_used_percent'] > 85:
        recommendations.append({
            'type': 'warning',
            'category': 'memory',
            'message': 'High memory usage detected. Consider reducing max workers or chunk duration.',
            'action': 'Reduce max_workers or increase chunk_duration'
        })
    elif memory_info['system_used_percent'] < 50:
        recommendations.append({
            'type': 'info',
            'category': 'memory',
            'message': 'Memory usage is low. You can potentially increase workers for faster processing.',
            'action': 'Consider increasing max_workers'
        })
    
    # CPU-based recommendations
    cpu_count = multiprocessing.cpu_count()
    if transcriber.max_workers < cpu_count // 2:
        recommendations.append({
            'type': 'info',
            'category': 'cpu',
            'message': f'You have {cpu_count} CPU cores. Consider increasing workers for better parallelization.',
            'action': f'Increase max_workers (current: {transcriber.max_workers}, suggested: {min(cpu_count, 4)})'
        })
    
    # Chunk duration recommendations
    if transcriber.chunk_duration > 420:  # 7 minutes
        recommendations.append({
            'type': 'info',
            'category': 'chunking',
            'message': 'Large chunk duration may reduce parallelization benefits.',
            'action': f'Consider reducing chunk_duration to {DEFAULT_CHUNK_DURATION_SECONDS}-{LONG_VIDEO_CHUNK_LIMIT} seconds'
        })
    elif transcriber.chunk_duration < SHORT_VIDEO_CHUNK_LIMIT:
        recommendations.append({
            'type': 'info',
            'category': 'chunking',
            'message': 'Very small chunks may increase overhead.',
            'action': f'Consider increasing chunk_duration to {SHORT_VIDEO_CHUNK_LIMIT}-{DEFAULT_CHUNK_DURATION_SECONDS} seconds'
        })
    
    # File cleanup recommendations
    cleanup_stats = file_manager.get_cleanup_stats()
    if cleanup_stats['total_size_mb'] > 500:  # 500MB
        recommendations.append({
            'type': 'warning',
            'category': 'storage',
            'message': f'High temporary file usage: {cleanup_stats["total_size_mb"]:.1f}MB',
            'action': 'Temporary files will be cleaned automatically'
        })
    
    return recommendations

def _get_memory_recommendations(memory_info):
    """Generate memory-specific recommendations"""
    recommendations = []
    
    if memory_info['system_used_percent'] > 90:
        recommendations.append({
            'type': 'critical',
            'category': 'memory',
            'message': 'Critical: System memory usage is very high',
            'action': 'Close other applications or reduce workers'
        })
    elif memory_info['system_used_percent'] > 75:
        recommendations.append({
            'type': 'warning',
            'category': 'memory',
            'message': 'Warning: Consider closing other applications',
            'action': 'Close unnecessary applications'
        })
    elif memory_info['system_used_percent'] < 40:
        recommendations.append({
            'type': 'info',
            'category': 'memory',
            'message': 'Good: Plenty of memory available for processing',
            'action': 'Consider increasing workers for faster processing'
        })
    
    if memory_info['process_rss_mb'] > 2000:  # 2GB
        recommendations.append({
            'type': 'info',
            'category': 'memory',
            'message': 'Process using significant memory - normal during transcription',
            'action': 'Monitor memory usage during processing'
        })
    
    return recommendations

# Add real-time performance monitoring API
@app.route('/api/performance/live', methods=['GET'])
def get_live_performance():
    """Get real-time performance metrics"""
    memory_info = memory_manager.get_memory_info()
    
    # Get active session information
    active_sessions_info = []
    with progress_tracker.lock:
        for session_id, session_data in progress_tracker.sessions.items():
            active_sessions_info.append({
                'session_id': session_id,
                'progress': session_data.get('progress', 0),
                'stage': session_data.get('stage', 'unknown'),
                'current_task': session_data.get('current_task', ''),
                'chunks_completed': session_data.get('chunks_completed', 0),
                'chunks_total': session_data.get('chunks_total', 0),
                'elapsed_time': time.time() - session_data.get('start_time', time.time())
            })
    
    live_data = {
        'timestamp': time.time(),
        'memory': {
            'system_used_percent': memory_info['system_used_percent'],
            'system_available_gb': memory_info['system_available_gb'],
            'process_rss_mb': memory_info['process_rss_mb']
        },
        'active_sessions': active_sessions_info,
        'temp_files': file_manager.get_cleanup_stats(),
        'system_load': {
            'cpu_count': multiprocessing.cpu_count(),
            'optimal_workers': memory_manager.get_optimal_workers(),
            'memory_pressure': memory_manager.check_memory_pressure()
        }
    }
    
    return jsonify({'success': True, 'data': live_data})

# Add performance history tracking
@app.route('/api/performance/history', methods=['GET'])
def get_performance_history():
    """Get performance history from recent sessions"""
    sessions_data = []
    results_dir = app.config['RESULTS_FOLDER']
    
    if os.path.exists(results_dir):
        # Get last 10 sessions for performance analysis
        session_folders = sorted(os.listdir(results_dir), reverse=True)[:10]
        
        for session_folder in session_folders:
            session_path = os.path.join(results_dir, session_folder)
            if os.path.isdir(session_path):
                metadata_path = os.path.join(session_path, 'metadata.json')
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            
                        # Calculate performance metrics
                        processing_time = metadata.get('processing_time', 0)
                        total_words = metadata.get('total_words', 0)
                        total_chunks = metadata.get('total_chunks', 0)
                        
                        performance_metrics = {
                            'session_id': metadata.get('session_id', session_folder),
                            'session_name': metadata.get('session_name', ''),
                            'created_at': metadata.get('created_at', ''),
                            'processing_time': processing_time,
                            'total_words': total_words,
                            'total_chunks': total_chunks,
                            'words_per_minute': (total_words / (processing_time / 60)) if processing_time > 0 else 0,
                            'chunks_per_minute': (total_chunks / (processing_time / 60)) if processing_time > 0 else 0,
                            'status': metadata.get('status', 'unknown')
                        }
                        
                        sessions_data.append(performance_metrics)
                        
                    except Exception as e:
                        logger.warning(f"Error reading metadata for {session_folder}: {e}")
    
    return jsonify({'success': True, 'data': sessions_data})

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_status', {'status': 'connected', 'message': 'WebSocket connection established'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    """Join a progress tracking session"""
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        logger.info(f"Client {request.sid} joined session {session_id}")
        
        # Send current progress if session exists
        current_progress = progress_tracker.get_session_progress(session_id)
        if current_progress:
            logger.debug(f"Sending existing progress to client {request.sid}: {current_progress.get('progress', 0):.1f}%")
            emit('progress_update', current_progress)
        else:
            logger.debug(f"No existing progress for session {session_id}, sending not_found status")
            emit('session_status', {'status': 'not_found', 'message': 'Session not found'})
    else:
        emit('error', {'message': 'Session ID required'})

@socketio.on('leave_session')
def handle_leave_session(data):
    """Leave a progress tracking session"""
    session_id = data.get('session_id')
    if session_id:
        leave_room(session_id)
        logger.info(f"Client {request.sid} left session {session_id}")

@socketio.on('get_progress')
def handle_get_progress(data):
    """Get current progress for a session"""
    session_id = data.get('session_id')
    if session_id:
        current_progress = progress_tracker.get_session_progress(session_id)
        if current_progress:
            emit('progress_update', current_progress)
        else:
            emit('session_status', {'status': 'not_found', 'message': 'Session not found'})
    else:
        emit('error', {'message': 'Session ID required'})

@app.route('/performance')
def performance_monitor():
    """Show performance monitoring dashboard"""
    return render_template('performance.html')

if __name__ == '__main__':
    # Ensure multiprocessing works on all platforms
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # Method already set, ignore
        pass
    
    # Determine if the environment is development
    is_development = os.getenv('FLASK_ENV', 'production') == 'development'
    socketio.run(app, debug=is_development, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=is_development)