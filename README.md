# 🎥 Video Transcriber

A comprehensive Python web application that transforms videos into searchable, analyzed transcripts with synchronized video playback and advanced analytics. Built with Flask, OpenAI Whisper, FFmpeg, and Chart.js.

![Video Transcriber](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Chart.js](https://img.shields.io/badge/Chart.js-4.0+-orange.svg)

## ✨ Features

### 🎯 Core Functionality

- **⚡ Parallel Processing** - Multi-core transcription with 2-4x speed improvements
- **🧩 Adaptive Video Splitting** - Smart chunk sizing based on video length (3-7 minutes)
- **🤖 AI-Powered Transcription** - Uses OpenAI Whisper for accurate speech-to-text conversion
- **⏱️ Timestamped Transcripts** - Precise timing for each segment with clickable timestamps
- **🔍 Smart Content Analysis** - Detects questions, emphasis cues, and custom keywords
- **📱 Interactive HTML Transcripts** - Searchable, filterable browser-based transcript viewer
- **📊 Multiple Export Formats** - Text, JSON, HTML, subtitles (SRT/VTT), PDF reports, and DOCX documents

### 🎥 Synchronized Video Player

- **� Interactive Video Playback** - Watch videos alongside synchronized transcripts
- **🎯 Transcript Synchronization** - Real-time highlighting of current spoken text
- **📑 Chapter Navigation** - Jump to specific sections with visual timeline markers
- **⏱️ Timestamp Clicking** - Click any transcript line to jump to that moment
- **🎮 Full Video Controls** - Play, pause, seek, speed control, and fullscreen
- **📱 Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **🔄 Multiple Formats** - Supports MP4, AVI, MOV, MKV, WebM, and more

### 📊 Performance Dashboard & Analytics

- **📈 Real-time Performance Monitoring** - Live system metrics with Chart.js visualizations
- **💾 Memory Usage Tracking** - Monitor RAM consumption and optimization recommendations
- **⚡ Processing Speed Analytics** - Track transcription performance and bottlenecks
- **🎯 Session Analytics** - Detailed statistics on processing time and efficiency
- **📋 Performance Recommendations** - AI-powered suggestions for optimal settings
- **🔧 Live Parameter Tuning** - Adjust chunk size and worker count in real-time
- **📊 Historical Performance Data** - Track improvements and trends over time
- **🚀 Automatic Optimization** - Smart defaults based on system capabilities

### 🔐 Authentication System (Optional)

- **👤 User Account Management** - Secure registration and login system
- **🔒 Session Privacy** - Personal transcription sessions with access control
- **📊 User Analytics** - Individual usage statistics and session history
- **🛡️ CSRF Protection** - Advanced security with token-based validation
- **🔑 Flexible Authentication** - Works alongside anonymous usage
- **📱 Mobile-Friendly Auth** - Responsive login and registration forms

- **📝 SubRip Subtitles (SRT)** - Standard format for video players with precise timestamps
- **🌐 WebVTT Subtitles (VTT)** - Web-based video player format with styling support
- **📄 PDF Reports** - Professional analysis documents with statistics and highlights
- **📝 Word Documents (DOCX)** - Microsoft Word format with structured content and tables
- **📋 Enhanced Text** - Improved plain text with better formatting and analysis sections
- **💾 JSON Data** - Complete analysis results for integration with other tools
- **🔍 Searchable HTML** - Interactive web-based transcript with filters and highlights

### 🔍 Advanced Analysis

- **🎭 Pre-Built Keyword Scenarios** - Choose from domain-specific keyword sets (Education, Business, Interviews, Technical)

- **Question Detection** - Automatically identifies spoken questions with timestamps
- **Emphasis Cue Recognition** - Finds important phrases like "make sure...", "don't forget..."
- **Custom Keyword Tracking** - Monitors user-defined terms and their frequency
- **Keyword Frequency Analysis** - Visual charts showing usage patterns
- **Content Summarization** - Extracts key points and highlights

### 📚 Session Management

- **Session Browser** - View and manage all previous transcription sessions
- **Smart Search** - Search across session metadata and transcript content
- **Flexible Sorting** - Sort by date, name, word count, or keyword count
- **Session Statistics** - Track processing time, word count, and analysis metrics
- **Delete Management** - Remove unwanted sessions with confirmation

### 🔤 Keyword Configuration

- **Custom Keywords** - Add, remove, and manage keywords for any use case
- **Visual Keyword Cloud** - See all active keywords at a glance
- **Persistent Storage** - Keywords saved in JSON configuration file
- **Real-time Updates** - Changes take effect immediately
- **Flexible Configuration** - Start with empty keywords or import predefined sets

### ⚡ Performance Optimization

- **Multi-Core Processing** - Utilizes all available CPU cores for transcription
- **Parallel Video Splitting** - Concurrent FFmpeg operations for faster chunking
- **Smart Worker Management** - Automatically optimizes based on system resources
- **Adaptive Chunking** - Dynamic chunk sizing for optimal performance
- **Memory Management** - Intelligent RAM usage with automatic cleanup
- **Performance Tuning API** - Real-time adjustment of processing parameters

### 🛡️ Security & Stability

- **Input Validation** - Comprehensive file type and size validation
- **Path Traversal Protection** - Security measures against malicious file access
- **Atomic Operations** - Thread-safe configuration updates
- **Error Recovery** - Robust error handling for video processing failures
- **Session Isolation** - Secure session management with validation

## 🚀 Quick Start

### One-Command Setup & Launch

1. **Clone the repository**

   ```bash
   git clone https://github.com/bazgreen/video-transcriber.git
   cd video-transcriber
   ```

2. **Run the app** (handles everything automatically)

   ```bash
   # macOS/Linux
   ./run.sh
   
   # Windows
   run.bat
   
   # Or directly with Python
   python scripts/setup/setup_and_run.py
   ```

That's it! The script will:

- ✅ Check Python version (3.8+ required)
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Check for FFmpeg
- ✅ Start the web server
- ✅ Open your browser automatically

### Prerequisites

- Python 3.8 or higher
- FFmpeg (for video processing) - the script will guide you if not installed
- At least 4GB RAM for video processing

### Development Setup (Advanced)

For developers who want to contribute or customize the application:

1. **Clone and setup development environment**

   ```bash
   git clone https://github.com/bazgreen/video-transcriber.git
   cd video-transcriber
   make setup-dev
   ```

2. **Available development commands**

   ```bash
   make help              # Show all available commands
   make install-dev       # Install with development dependencies
   make test              # Run all tests
   make test-unit         # Run unit tests only
   make test-integration  # Run integration tests only
   make test-coverage     # Run tests with coverage report
   make lint              # Run code quality checks
   make format            # Auto-format code with black and isort
   make pre-commit        # Run all pre-commit hooks
   make benchmark         # Run performance benchmarks
   make clean             # Clean up temporary files
   ```

3. **Run the development server**

   ```bash
   make dev               # Start development server
   ```

### Manual Installation (Advanced)

**Click to expand manual setup instructions:**

1. **Create and activate virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   # Basic installation (includes SRT, VTT, Enhanced Text, JSON, HTML export)
   pip install -r requirements.txt
   ```

3. **Optional: Enhanced Export Formats**

   Enable additional professional export formats:

   **Option A: Full Feature Installation (Recommended)**
   ```bash
   pip install -r requirements-full.txt
   ```

   **Option B: Selective Installation**
   ```bash
   # PDF export only (professional reports)
   pip install reportlab
   
   # DOCX export only (Microsoft Word documents)
   pip install python-docx
   
   # Both PDF and DOCX
   pip install reportlab python-docx
   ```

   **Option C: Individual Requirements Files**
   ```bash
   # PDF support only
   pip install -r requirements-pdf.txt
   
   # DOCX support only
   pip install -r requirements-docx.txt
   ```

   **Available Export Formats:**
   - ✅ **Always Available:** SRT, VTT, Enhanced Text, JSON, HTML
   - 📄 **With reportlab:** Professional PDF reports 
   - 📝 **With python-docx:** Microsoft Word documents

4. **Install FFmpeg** (if not already installed)
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
   - **Windows**: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

5. **Run the application**

   ```bash
   python app.py
   ```

```
## 📖 Usage Guide

### Web Interface (Recommended)

1. **Upload Video** - Drag and drop or select your video file
2. **Add Session Name** - Optional: Give your session a meaningful name
3. **Start Processing** - Click "Start Transcription" and watch real-time progress
4. **Watch & Analyze** - Use the synchronized video player to review results
5. **View Analytics** - Check the performance dashboard for processing insights
6. **Download Results** - Access multiple export formats (PDF, DOCX, SRT, VTT, etc.)
7. **Browse Sessions** - Use the session browser to manage transcription history
8. **Configure Keywords** - Customize detection keywords for your specific needs

### Key Features Access

- **🎥 Video Player**: Click "▶️ Watch Video" on any results page for synchronized playback
- **📊 Performance Monitor**: Visit `/performance` for real-time system analytics
- **⚙️ Keyword Configuration**: Click "🔧 Config" to customize detection keywords
- **📁 Session Browser**: Click "📂 Sessions" to manage all transcriptions
- **🔐 User Accounts**: Visit `/auth/register` for personal session management (optional)

### Command Line Interface

For simple transcription without the web interface:

```bash
python scripts/transcribe.py
```

## 📊 Output Files

Each transcription session generates multiple output files:

- **`full_transcript.txt`** - Complete timestamped transcription
- **`keyword_matches.txt`** - Custom keyword highlights
- **`questions.txt`** - Detected questions with timestamps
- **`emphasis_cues.txt`** - Important phrases and emphasis markers
- **`analysis.json`** - Complete analysis data in JSON format
- **`searchable_transcript.html`** - Interactive browser-based transcript
- **`metadata.json`** - Session information and statistics

## 🎯 Use Cases & Keywords

The system can be customized for various industries and use cases through keyword configuration.

**Example Use Cases:**

**🎓 Education & Training:**

- Lectures, workshops, online courses
- Keywords: assignment, assessment, homework, exam, grade

**💼 Business & Corporate:**

- Meetings, presentations, training sessions
- Keywords: action items, deadline, budget, KPI, ROI

**🎙️ Media & Podcasts:**

- Interviews, podcasts, webinars
- Keywords: guest, sponsor, announcement, call-to-action

**🔬 Research & Academia:**

- Research presentations, thesis defenses
- Keywords: hypothesis, methodology, results, conclusion

**🏥 Healthcare & Medical:**

- Medical training, patient consultations
- Keywords: diagnosis, treatment, symptoms, medication

**Customization:**

- Start with empty keywords or choose a preset
- Access the configuration page at `/config`
- Add keywords relevant to your specific use case
- Keywords are stored in `config/keywords_config.json`

## 🔧 External Customization Tools

For advanced keyword management, external customization scripts are available:

### Video Transcriber Customizer

**Location:** `/Users/barrygreen/video_transcriber_customizer.py`

**Features:**

- **7+ Predefined Industry Sets** - Education, Business, Media, Research, Healthcare, Legal, Technology
- **Interactive CLI Interface** - Easy-to-use command-line management
- **Backup & Restore** - Automatic backup before changes with easy restore
- **Custom Keyword Management** - Add, remove, and modify keywords
- **Automatic Detection** - Finds your transcriber installation automatically

**Quick Launch:**

```bash
# macOS/Linux
./customize_transcriber.sh

# Windows
customize_transcriber.bat

# Or directly
python video_transcriber_customizer.py
```

**Example Usage:**

```bash
# Apply business keyword set
python video_transcriber_customizer.py
# Select option 2, then type "business"

# Add custom keywords
python video_transcriber_customizer.py  
# Select option 4, then enter: "meeting, deadline, action item"
```

## 🛠️ Technical Architecture

### Core Components

- **Flask Web Framework** - RESTful API and web interface
- **OpenAI Whisper** - Speech-to-text transcription engine
- **FFmpeg** - Video processing and audio extraction
- **Python Libraries** - NumPy, JSON, regex for data processing

### Processing Pipeline

1. **Video Upload** - Secure file handling with validation
2. **Parallel Video Splitting** - FFmpeg splits video into adaptive chunks using ThreadPoolExecutor
3. **Concurrent Audio Extraction** - Multiple audio streams processed simultaneously
4. **Parallel AI Transcription** - Whisper processes multiple chunks using ProcessPoolExecutor
5. **Content Analysis** - Regex patterns detect questions, keywords, emphasis
6. **Output Generation** - Multiple formats created automatically
7. **Session Storage** - Metadata and results saved for future access
8. **Cleanup** - Automatic removal of temporary files to optimize disk usage

## 🔧 Configuration

### Environment Variables

```bash
# Application Configuration
FLASK_ENV=production          # Set to 'development' for debug mode
DEBUG=false                   # Enable debug mode (true/false)
MAX_CONTENT_LENGTH=500MB      # Maximum upload file size
WHISPER_MODEL=small           # Whisper model size (tiny/small/medium/large)

# Security Configuration
SECRET_KEY=your-secret-key    # Flask secret key for sessions
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com  # Production CORS origins
```

### CORS Security Configuration

The application implements secure CORS (Cross-Origin Resource Sharing) configuration:

**Development Mode** (`DEBUG=true`):

- Automatically allows common development origins:
  - `http://localhost:3000` (React dev server)
  - `http://localhost:5000` (Flask alt port)
  - `http://localhost:5001` (Main Flask server)
  - `http://127.0.0.1:5001` (Localhost IP variant)

**Production Mode** (`DEBUG=false`):

- Only allows origins specified in `CORS_ALLOWED_ORIGINS`
- Multiple origins can be specified, comma-separated
- Example: `CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com`
- ⚠️ **Never use `*` (wildcard) in production** - this is a security risk

**Security Best Practices**:

- Always set specific domains in production
- Use HTTPS origins in production
- Regularly review and update allowed origins
- Monitor CORS logs for unauthorized access attempts

### Whisper Models

- **tiny** - Fastest, least accurate (~1GB)
- **small** - Balanced speed/accuracy (~2GB) - **Default**
- **medium** - Better accuracy (~5GB)
- **large** - Best accuracy (~10GB)

### Performance Configuration

**Automatic Optimization:**

- **Worker Count**: Automatically set to `min(CPU_cores, 4)` to balance speed and memory usage
- **Chunk Duration**: Adaptive sizing based on video length
  - Short videos (<10 min): 3-minute chunks
  - Medium videos (10-60 min): 5-minute chunks (default)
  - Long videos (>60 min): 7-minute chunks
- **Memory Management**: Each worker uses ~2GB RAM, system prevents overallocation

**Manual Tuning via API:**

```bash
# Get current performance settings
curl http://localhost:5001/api/performance

# Update performance settings
curl -X POST http://localhost:5001/api/performance \
  -H "Content-Type: application/json" \
  -d '{"chunk_duration": 240, "max_workers": 2}'
```

**Performance Expectations:**

- **20-minute video**: ~8-12 minutes (vs 25 minutes sequential)
- **1-hour video**: ~25-35 minutes (vs 75 minutes sequential)
- **Speed improvement**: 2-4x faster depending on video length and system specs

## 📁 Project Structure

```text
video-transcriber/
├── Makefile                     # Development workflow automation
├── setup_and_run.py            # One-command setup & launch script
├── run.sh                      # macOS/Linux launcher
├── run.bat                     # Windows launcher
├── main.py                     # Application entry point
├── requirements.txt            # Core Python dependencies
├── requirements-*.txt          # Optional feature dependencies
├── LICENSE                     # MIT License
├── README.md                   # This documentation
├── src/                        # Source code (modular architecture)
│   ├── routes/                 # Flask route handlers
│   │   ├── main.py            # Main application routes
│   │   ├── api.py             # API endpoints
│   │   ├── auth.py            # Authentication routes (optional)
│   │   └── socket_handlers.py # WebSocket handlers
│   ├── services/              # Business logic services
│   │   ├── transcription.py   # Core transcription service
│   │   ├── upload.py          # File upload handling
│   │   └── export.py          # Export format generation
│   ├── models/                # Data models
│   │   ├── auth.py            # User authentication models
│   │   ├── memory.py          # Memory management models
│   │   └── exceptions.py      # Custom exception classes
│   ├── utils/                 # Utility functions
│   │   ├── helpers.py         # General helper functions
│   │   ├── keywords.py        # Keyword management
│   │   ├── security.py        # Security utilities
│   │   └── performance_optimizer.py # Performance tuning
│   ├── forms/                 # WTForms form definitions
│   │   └── auth.py            # Authentication forms
│   └── config.py              # Application configuration
├── data/                      # Application data
│   └── templates/             # HTML templates
│       ├── index.html         # Upload interface
│       ├── results.html       # Results with video player
│       ├── sessions.html      # Session browser
│       ├── config.html        # Keyword configuration
│       ├── performance.html   # Performance dashboard
│       └── auth/              # Authentication templates
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── benchmarks/            # Performance benchmarks
├── config/                    # Configuration files
│   ├── keywords_config.json   # Keyword configuration
│   └── requirements/          # Organized requirements files
├── scripts/                   # Utility scripts
│   ├── transcribe.py          # CLI transcription tool
│   ├── setup/                 # Setup and installation scripts
│   └── validation/            # Validation and testing scripts
├── docs/                      # Documentation
├── uploads/                   # Temporary upload storage
└── results/                   # Transcription results
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [FFmpeg](https://ffmpeg.org/) for video processing
- [Flask](https://flask.palletsprojects.com/) for the web framework

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/bazgreen/video-transcriber/issues) page
2. Create a new issue with detailed information
3. Include your system information and error logs

## 🔄 Changelog

### v2.0.0 (2025-07-05) - Major Feature Update

- **🎥 Synchronized Video Player**: Interactive video playback with transcript synchronization
- **📊 Performance Dashboard**: Real-time monitoring with Chart.js visualizations
- **🔐 Authentication System**: Optional user accounts and session management
- **📄 Enhanced Export Formats**: PDF reports, DOCX documents, and professional outputs
- **🏗️ Modular Architecture**: Complete codebase reorganization for better maintainability
- **⚙️ Development Workflow**: Comprehensive Makefile with testing, linting, and formatting
- **🧪 Test Suite**: Unit tests, integration tests, and performance benchmarks
- **📱 Mobile Optimization**: Improved responsive design across all features
- **🔧 Advanced Configuration**: Real-time performance tuning and optimization

### v1.2.0 (2025-06-24) - Performance Optimization

- **⚡ Major Performance Improvements**: 2-4x faster transcription with parallel processing
- **🔄 Parallel Video Splitting**: Concurrent FFmpeg operations using ThreadPoolExecutor
- **🚀 Parallel Transcription**: Multi-core Whisper processing using ProcessPoolExecutor
- **🧩 Adaptive Chunking**: Smart chunk sizing based on video length (3-7 minutes)
- **💾 Memory Management**: Intelligent worker allocation and automatic cleanup
- **📊 Performance Tuning API**: Real-time adjustment of processing parameters
- **🎯 Automatic Optimization**: CPU-based worker count and memory-aware processing
- **🧹 Disk Space Management**: Automatic cleanup of temporary video chunks

### v1.1.0 (2025-06-24)

- Added keyword configuration page
- Customizable educational keywords
- Visual keyword cloud interface
- Persistent keyword storage in JSON
- Navigation improvements

### v1.0.0 (2025-06-24)

- Initial release
- Web interface with drag-and-drop upload
- Auto video splitting into 5-minute chunks
- AI transcription with Whisper
- Question and emphasis detection
- Session management and browsing
- Multiple export formats
- Responsive design for mobile/desktop

---

Made with ❤️ for educational content creators
