from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
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
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
import functools
import logging

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Security constants
ALLOWED_FILE_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'}

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

# Ensure upload and results directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Global variable to store model for worker processes
_model_cache = None

def init_worker():
    """Initialize worker process with Whisper model - called once per worker"""
    global _model_cache
    _model_cache = whisper.load_model("small")
    logger.info("Whisper model loaded in worker process")

def get_model():
    """Get the pre-loaded Whisper model for parallel processing"""
    global _model_cache
    if _model_cache is None:
        # Fallback if not initialized via worker initializer
        _model_cache = whisper.load_model("small")
    return _model_cache

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
            .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
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
        
        # Clean up audio file
        try:
            os.remove(audio_path)
        except:
            pass
            
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
        # Performance tuning: Limit max workers based on system capabilities
        # Each Whisper process can use ~2GB RAM, so limit accordingly
        cpu_count = multiprocessing.cpu_count()
        # Estimate based on typical 8GB+ systems
        self.max_workers = min(cpu_count, 4) if cpu_count >= 4 else max(1, cpu_count // 2)
        self.chunk_duration = 300  # 5 minutes default, can be adjusted for performance
        
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
        if duration < 600:  # Less than 10 minutes
            chunk_duration = min(chunk_duration, 180)  # 3 minutes max
        elif duration > 3600:  # More than 1 hour
            chunk_duration = min(chunk_duration, 420)  # 7 minutes max
        
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
        except Exception as e:
            raise Exception(f"Failed to split chunk {chunk_name}: {str(e)}")
    
    def extract_audio(self, video_path, audio_path):
        """Extract audio from video"""
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
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
            pattern = re.compile(r'.{0,50}' + re.escape(keyword) + r'.{0,50}', re.IGNORECASE)
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
        
        # Split video into chunks
        chunks = self.split_video(video_path, session_dir)
        
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
        
        # Use ProcessPoolExecutor for CPU-intensive transcription work
        completed_chunks = []
        num_workers = min(self.max_workers, len(chunks))
        logger.info(f"Processing {len(chunks)} chunks in parallel using {num_workers} workers...")
        
        with ProcessPoolExecutor(max_workers=num_workers, initializer=init_worker) as executor:
            # Submit all chunk processing tasks
            futures = {executor.submit(process_chunk_parallel, chunk_info): chunk_info for chunk_info in chunk_info_list}
            
            # Collect results as they complete
            for i, future in enumerate(as_completed(futures)):
                try:
                    result = future.result()
                    if result['success']:
                        completed_chunks.append(result)
                        logger.info(f"Completed chunk {i+1}/{len(chunks)}: {result['filename']}")
                    else:
                        logger.error(f"Error processing chunk {result['filename']}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"Exception processing chunk: {e}")
        
        # Sort results by start time to maintain order
        completed_chunks.sort(key=lambda x: x['start_time'])
        
        # Combine results
        for chunk_result in completed_chunks:
            all_segments.extend(chunk_result['segments'])
            all_text.append(f"\n\n--- {chunk_result['filename']} [{format_timestamp(chunk_result['start_time'])}] ---\n\n{chunk_result['transcription']}")
            results['chunks'].append(chunk_result)
        
        # Combine all text
        results['full_transcript'] = '\n'.join(all_text)
        
        # Analyze complete content
        results['analysis'] = self.analyze_content(results['full_transcript'], all_segments)
        
        # Update metadata with final stats
        metadata.update({
            'status': 'completed',
            'total_chunks': len(chunks),
            'total_words': results['analysis']['total_words'],
            'keywords_found': len(results['analysis']['keyword_matches']),
            'questions_found': len(results['analysis']['questions']),
            'emphasis_cues_found': len(results['analysis']['emphasis_cues']),
            'processing_time': (datetime.now() - datetime.fromisoformat(metadata['created_at'])).total_seconds()
        })
        
        # Save metadata
        with open(os.path.join(session_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Generate outputs
        self.save_results(results)
        results['html_file'] = self.generate_html_transcript(results)
        results['metadata'] = metadata
        
        # Clean up temporary video chunks to save disk space
        self.cleanup_temp_files(session_dir)
        
        return results
    
    def cleanup_temp_files(self, session_dir):
        """Clean up temporary video chunk files to save disk space"""
        try:
            # Remove all .mp4 chunks (keep only final outputs)
            for file in glob.glob(os.path.join(session_dir, "*.mp4")):
                if "_part_" in file and os.path.exists(file):  # Only remove chunk files that exist
                    try:
                        os.remove(file)
                    except OSError as e:
                        logger.warning(f"Could not remove file {file}: {e}")
        except Exception as e:
            logger.warning(f"Could not clean up temporary files: {e}")
    
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
        """Generate searchable HTML transcript"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Transcript - {results['session_id']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .search-box {{ margin-bottom: 20px; }}
                .search-box input {{ width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ddd; border-radius: 4px; }}
                .filters {{ margin-bottom: 20px; }}
                .filter-btn {{ padding: 8px 16px; margin: 4px; border: none; border-radius: 4px; cursor: pointer; }}
                .filter-btn.active {{ background-color: #007bff; color: white; }}
                .filter-btn:not(.active) {{ background-color: #e9ecef; color: #495057; }}
                .segment {{ margin-bottom: 15px; padding: 10px; border-left: 3px solid #dee2e6; }}
                .segment.highlight {{ border-left-color: #ffc107; background-color: #fff3cd; }}
                .segment.question {{ border-left-color: #17a2b8; background-color: #d1ecf1; }}
                .segment.emphasis {{ border-left-color: #dc3545; background-color: #f8d7da; }}
                .timestamp {{ font-weight: bold; color: #6c757d; margin-right: 10px; }}
                .keyword {{ background-color: #ffeb3b; padding: 2px 4px; border-radius: 2px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
                .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 4px; text-align: center; }}
                .hidden {{ display: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Video Transcript Analysis</h1>
                <p><strong>Session:</strong> {results['session_id']}</p>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>{len(results['analysis']['keyword_matches'])}</h3>
                        <p>Keywords Found</p>
                    </div>
                    <div class="stat-card">
                        <h3>{len(results['analysis']['questions'])}</h3>
                        <p>Questions Detected</p>
                    </div>
                    <div class="stat-card">
                        <h3>{len(results['analysis']['emphasis_cues'])}</h3>
                        <p>Emphasis Cues</p>
                    </div>
                    <div class="stat-card">
                        <h3>{results['analysis']['total_words']}</h3>
                        <p>Total Words</p>
                    </div>
                </div>
                
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search transcript...">
                </div>
                
                <div class="filters">
                    <button class="filter-btn active" onclick="filterSegments('all')">All</button>
                    <button class="filter-btn" onclick="filterSegments('keywords')">Keywords</button>
                    <button class="filter-btn" onclick="filterSegments('questions')">Questions</button>
                    <button class="filter-btn" onclick="filterSegments('emphasis')">Emphasis</button>
                </div>
                
                <div id="transcript">
        """
        
        # Add all segments
        all_segments = []
        for chunk in results['chunks']:
            all_segments.extend(chunk['segments'])
        
        # Sort by timestamp
        all_segments.sort(key=lambda x: x['start'])
        
        # Create sets for quick lookup
        question_times = {q['start'] for q in results['analysis']['questions']}
        emphasis_times = {e['start'] for e in results['analysis']['emphasis_cues']}
        
        for segment in all_segments:
            classes = ['segment']
            if segment['start'] in question_times:
                classes.append('question')
            if segment['start'] in emphasis_times:
                classes.append('emphasis')
            
            # Highlight keywords
            text = segment['text']
            for keyword in CUSTOM_KEYWORDS:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                text = pattern.sub(f'<span class="keyword">{keyword}</span>', text)
                if pattern.search(segment['text']):
                    classes.append('highlight')
            
            html_content += f'''
                    <div class="{' '.join(classes)}" data-type="{' '.join(classes[1:]) if len(classes) > 1 else 'normal'}">
                        <span class="timestamp">{segment['timestamp_str']}</span>
                        {text}
                    </div>
            '''
        
        html_content += """
                </div>
            </div>
            
            <script>
                // Search functionality
                document.getElementById('searchInput').addEventListener('input', function(e) {
                    const searchTerm = e.target.value.toLowerCase();
                    const segments = document.querySelectorAll('.segment');
                    
                    segments.forEach(segment => {
                        const text = segment.textContent.toLowerCase();
                        if (text.includes(searchTerm) || searchTerm === '') {
                            segment.style.display = 'block';
                        } else {
                            segment.style.display = 'none';
                        }
                    });
                });
                
                // Filter functionality
                let currentFilter = 'all';
                
                function filterSegments(type) {
                    currentFilter = type;
                    const segments = document.querySelectorAll('.segment');
                    const buttons = document.querySelectorAll('.filter-btn');
                    
                    // Update button states
                    buttons.forEach(btn => btn.classList.remove('active'));
                    event.target.classList.add('active');
                    
                    segments.forEach(segment => {
                        const segmentType = segment.getAttribute('data-type');
                        if (type === 'all' || segmentType.includes(type)) {
                            segment.style.display = 'block';
                        } else {
                            segment.style.display = 'none';
                        }
                    });
                }
            </script>
        </body>
        </html>
        """
        
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
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        return jsonify({"error": f"Invalid file type. Allowed types: {', '.join(ALLOWED_FILE_EXTENSIONS)}"}), 400
    
    # Validate file size (500MB limit)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    if file_size > 500 * 1024 * 1024:  # 500MB
        return jsonify({'error': 'File too large. Maximum size is 500MB'}), 400
    
    session_name = request.form.get('session_name', '').strip()
    
    # Validate session name
    if not session_name:
        return jsonify({"error": "Session name is required and cannot be empty"}), 400
    
    # Remove potentially problematic characters
    session_name = re.sub(r'[^a-zA-Z0-9_-]', '_', session_name)
    # Limit length
    session_name = session_name[:50]
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(upload_path)
    
    try:
        # Process video
        results = transcriber.process_video(upload_path, session_name, file.filename)
        
        return jsonify({
            'success': True,
            'session_id': results['session_id'],
            'message': 'Video processed successfully!'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up uploaded file
        if os.path.exists(upload_path):
            os.remove(upload_path)

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
        return jsonify({'error': 'No keywords provided'}), 400
    
    keywords = data['keywords']
    
    # Validate keywords
    if not isinstance(keywords, list):
        return jsonify({'error': 'Keywords must be a list'}), 400
    
    # Clean and validate each keyword
    cleaned_keywords = []
    for keyword in keywords:
        if isinstance(keyword, str) and keyword.strip():
            cleaned_keywords.append(keyword.strip())
    
    if not cleaned_keywords:
        return jsonify({'error': 'At least one valid keyword is required'}), 400
    
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
        return jsonify({'error': 'No keyword provided'}), 400
    
    keyword = data['keyword'].strip()
    
    if not keyword:
        return jsonify({'error': 'Keyword cannot be empty'}), 400
    
    if keyword.lower() in [k.lower() for k in CUSTOM_KEYWORDS]:
        return jsonify({'error': 'Keyword already exists'}), 400
    
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
        return jsonify({'error': 'No keyword provided'}), 400
    
    keyword = data['keyword']
    
    if keyword not in CUSTOM_KEYWORDS:
        return jsonify({'error': 'Keyword not found'}), 404
    
    # Remove keyword and save
    CUSTOM_KEYWORDS.remove(keyword)
    save_keywords(CUSTOM_KEYWORDS)
    
    return jsonify({'success': True, 'keywords': CUSTOM_KEYWORDS})

@app.route('/api/performance', methods=['GET'])
def get_performance_info():
    """Get system performance information"""
    return jsonify({
        'cpu_count': multiprocessing.cpu_count(),
        'max_workers': transcriber.max_workers,
        'chunk_duration': transcriber.chunk_duration,
        'whisper_model': 'small'
    })

@app.route('/api/performance', methods=['POST'])
def update_performance_settings():
    """Update performance settings"""
    data = request.get_json()
    errors = []
    
    if 'chunk_duration' in data:
        try:
            duration = int(data['chunk_duration'])
            if 60 <= duration <= 600:  # 1-10 minutes
                transcriber.chunk_duration = duration
            else:
                errors.append(f"chunk_duration must be between 60-600 seconds, got {duration}")
        except (ValueError, TypeError):
            errors.append("chunk_duration must be a valid integer")
    
    if 'max_workers' in data:
        try:
            workers = int(data['max_workers'])
            max_cpu = multiprocessing.cpu_count()
            if 1 <= workers <= max_cpu:
                transcriber.max_workers = workers
            else:
                errors.append(f"max_workers must be between 1-{max_cpu}, got {workers}")
        except (ValueError, TypeError):
            errors.append("max_workers must be a valid integer")
    
    if errors:
        return jsonify({'success': False, 'errors': errors}), 400
    
    return jsonify({'success': True, 'message': 'Performance settings updated'})

if __name__ == '__main__':
    # Ensure multiprocessing works on all platforms
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        # Method already set, ignore
        pass
    app.run(debug=True, host='0.0.0.0', port=5001)