"""Video transcription service."""

import os
import re
import json
import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

import whisper
import ffmpeg
from flask import render_template

from src.config import VideoConfig, AnalysisConfig
from src.utils import load_keywords, format_timestamp
from src.models.managers import MemoryManager, ProgressiveFileManager, ModelManager

logger = logging.getLogger(__name__)

# Configuration instances
video_config = VideoConfig()
analysis_config = AnalysisConfig()

# Patterns for content analysis
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

QUESTION_PATTERNS = [
    r"what.*\?",
    r"how.*\?", 
    r"why.*\?",
    r"when.*\?",
    r"where.*\?",
    r"which.*\?",
    r"who.*\?"
]


def init_worker():
    """Initialize worker process - now more memory efficient"""
    logger.info("Worker process initialized (model will be loaded on demand)")


def get_model():
    """Get the Whisper model with efficient memory management"""
    # This will need to be injected or managed differently in the modular version
    from src.models.managers import ModelManager
    model_manager = ModelManager()
    return model_manager.get_model()


def process_chunk_parallel(chunk_info):
    """Process a single chunk in parallel - for use with ProcessPoolExecutor"""
    # This function will need access to file_manager - will be refactored
    if not isinstance(chunk_info, tuple) or len(chunk_info) != 4:
        raise ValueError("Invalid chunk_info format. Expected a tuple with 4 elements: (chunk_path, audio_path, start_time, filename).")
    
    try:
        chunk_path, audio_path, start_time, filename = chunk_info
        
        # Extract audio
        (
            ffmpeg
            .input(chunk_path)
            .output(audio_path, acodec=video_config.AUDIO_CODEC, ac=video_config.AUDIO_CHANNELS, ar=str(video_config.AUDIO_SAMPLE_RATE))
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
        
        # Note: file_manager access will need to be refactored
        # file_manager.add_temp_file(audio_path, 'audio')
            
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


class VideoTranscriber:
    """Video transcription service"""
    
    def __init__(self, memory_manager: MemoryManager, file_manager: ProgressiveFileManager, 
                 progress_tracker, results_folder: str) -> None:
        self.model = None
        self.memory_manager = memory_manager
        self.file_manager = file_manager
        self.progress_tracker = progress_tracker
        self.results_folder = results_folder
        
        # Memory-aware performance tuning
        self.max_workers = memory_manager.get_optimal_workers()
        self.chunk_duration = video_config.DEFAULT_CHUNK_DURATION_SECONDS
        
        # Log memory and worker configuration
        memory_info = memory_manager.get_memory_info()
        logger.info(f"VideoTranscriber initialized with {self.max_workers} max workers. "
                   f"System memory: {memory_info['system_total_gb']:.1f}GB total, "
                   f"{memory_info['system_available_gb']:.1f}GB available")
        
    def load_model(self) -> Any:
        if self.model is None:
            self.model = whisper.load_model(video_config.WHISPER_MODEL)
        return self.model
    
    def split_video(self, input_path: str, output_dir: str, chunk_duration: Optional[int] = None) -> List[Dict[str, Union[str, int, float]]]:
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
            self.file_manager.add_temp_file(chunk_path, 'video')
        except Exception as e:
            raise Exception(f"Failed to split chunk {chunk_name}: {str(e)}")
    
    def extract_audio(self, video_path, audio_path):
        """Extract audio from video"""
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec=video_config.AUDIO_CODEC, ac=video_config.AUDIO_CHANNELS, ar=str(video_config.AUDIO_SAMPLE_RATE))
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
        
        # Load custom keywords
        custom_keywords = load_keywords()
        
        # Keyword analysis
        for keyword in custom_keywords:
            pattern = re.compile(f'.{{0,{analysis_config.CONTEXT_WINDOW_CHARS}}}' + re.escape(keyword) + f'.{{0,{analysis_config.CONTEXT_WINDOW_CHARS}}}', re.IGNORECASE)
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
        for keyword in custom_keywords:
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
    
    def process_video(self, video_path: str, session_name: str = "", original_filename: str = "") -> Dict[str, Any]:
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
            self.progress_tracker.complete_session(session_id, success=False, message=error_message)
            raise
    
    def _initialize_session(self, session_name: str = "", original_filename: str = "") -> Tuple[str, str, Dict[str, Any], Dict[str, Any]]:
        """Initialize a new processing session"""
        # Create session directory
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_name:
            session_id = f"{session_name}_{session_id}"
        
        session_dir = os.path.join(self.results_folder, session_id)
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
        self.progress_tracker.start_session(session_id)
        self.progress_tracker.update_progress(session_id, 
                                       current_task="Analyzing video file...", 
                                       progress=5,
                                       stage='analysis')
        
        # Split video into chunks
        chunks = self.split_video(video_path, session_dir)
        
        # Update progress after video splitting
        self.progress_tracker.start_session(session_id, 
                                     total_chunks=len(chunks),
                                     video_duration=self.get_video_duration(video_path))
        self.progress_tracker.update_progress(session_id,
                                       current_task=f"Video split into {len(chunks)} chunks. Starting transcription...",
                                       progress=15,
                                       stage='preparation')
        
        # Process chunks and combine results
        all_segments, all_text = self._transcribe_chunks_parallel(session_id, session_dir, chunks)
        
        # Store results
        results['chunks'] = all_segments
        results['full_transcript'] = '\n'.join(all_text)
        
        # Analyze content
        self.progress_tracker.update_progress(session_id,
                                       current_task="Analyzing content for keywords and insights...",
                                       progress=90,
                                       stage='analysis')
        results['analysis'] = self.analyze_content(results['full_transcript'], all_segments)
    
    def _transcribe_chunks_parallel(self, session_id: str, session_dir: str, chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
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
        memory_info = self.memory_manager.get_memory_info()
        optimal_workers = self.memory_manager.get_optimal_workers(max_workers=self.max_workers)
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
                        self.progress_tracker.update_chunk_progress(session_id, i + 1, len(chunks), 
                                                             f"Transcribed {result['filename']}")
                        
                        # Periodic memory monitoring (every 25% of chunks)
                        if (i + 1) % max(1, len(chunks) // 4) == 0:
                            current_memory = self.memory_manager.get_memory_info()
                            logger.info(f"Completed chunk {i+1}/{len(chunks)}: {result['filename']} "
                                       f"(Memory: {current_memory['process_rss_mb']:.0f}MB process, "
                                       f"{current_memory['system_used_percent']:.1f}% system)")
                            
                            # Check for memory pressure
                            if self.memory_manager.check_memory_pressure():
                                logger.warning(f"High memory usage detected: {current_memory['system_used_percent']:.1f}%")
                        else:
                            logger.info(f"Completed chunk {i+1}/{len(chunks)}: {result['filename']}")
                    else:
                        logger.error(f"Error processing chunk {result['filename']}: {result.get('error', 'Unknown error')}")
                        # Update progress even for failed chunks
                        self.progress_tracker.update_chunk_progress(session_id, i + 1, len(chunks), 
                                                             f"Error in {result['filename']}")
                except Exception as e:
                    logger.error(f"Exception processing chunk: {e}")
                    # Update progress for exception cases
                    self.progress_tracker.update_chunk_progress(session_id, i + 1, len(chunks), 
                                                         f"Exception processing chunk")
        
        # Sort results by start time to maintain order
        completed_chunks.sort(key=lambda x: x['start_time'])
        
        # Update progress for final processing stages
        self.progress_tracker.update_progress(session_id,
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
        self.progress_tracker.update_progress(session_id,
                                       current_task="Generating output files...",
                                       progress=95,
                                       stage='finalization')
        
        # Generate outputs
        self.save_results(results)
        results['html_file'] = self.generate_html_transcript(results)
        results['metadata'] = metadata
        
        # Complete progress tracking
        self.progress_tracker.complete_session(session_id, success=True, 
                                        message=f"Processing complete! Transcribed {chunks_count} chunks, found {results['analysis']['total_words']} words.")
        
        # Clean up all temporary files using progressive file manager
        cleanup_stats = self.file_manager.get_cleanup_stats()
        logger.info(f"Final cleanup: {cleanup_stats['count']} temp files, "
                   f"{cleanup_stats['total_size_mb']:.1f}MB")
        self.file_manager.cleanup_all()
    
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
        
        # Load custom keywords
        custom_keywords = load_keywords()
        
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
            for keyword in custom_keywords:
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