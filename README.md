# 🎥 Video Transcriber

A powerful Python web application that transforms educational videos into searchable, analyzed transcripts using AI. Built with Flask, OpenAI Whisper, and FFmpeg.

![Video Transcriber](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 🎯 Core Functionality
- **Auto Video Splitting** - Automatically splits long videos into 5-minute chunks for efficient processing
- **AI-Powered Transcription** - Uses OpenAI Whisper for accurate speech-to-text conversion
- **Timestamped Transcripts** - Precise timing for each segment with clickable timestamps
- **Smart Content Analysis** - Detects questions, emphasis cues, and educational keywords
- **Interactive HTML Transcripts** - Searchable, filterable browser-based transcript viewer
- **Multiple Export Formats** - TXT, JSON, and HTML outputs for maximum flexibility

### 🔍 Advanced Analysis
- **Question Detection** - Automatically identifies spoken questions with timestamps
- **Emphasis Cue Recognition** - Finds important phrases like "make sure...", "don't forget..."
- **Educational Keyword Tracking** - Monitors assessment-related terms and their frequency
- **Keyword Frequency Analysis** - Visual charts showing usage patterns
- **Content Summarization** - Extracts key points and highlights

### 📚 Session Management
- **Session Browser** - View and manage all previous transcription sessions
- **Smart Search** - Search across session metadata and transcript content
- **Flexible Sorting** - Sort by date, name, word count, or keyword count
- **Session Statistics** - Track processing time, word count, and analysis metrics
- **Delete Management** - Remove unwanted sessions with confirmation

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- FFmpeg installed on your system
- At least 4GB RAM for video processing

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/bazgreen/video-transcriber.git
   cd video-transcriber
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg** (if not already installed)
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
   - **Windows**: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### Running the Application

1. **Start the web server**
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5001
   ```

3. **Upload a video** and let the AI do the work!

## 📖 Usage Guide

### Web Interface (Recommended)

1. **Upload Video** - Drag and drop or select your video file
2. **Add Session Name** - Optional: Give your session a meaningful name
3. **Start Processing** - Click "Start Transcription" and wait for completion
4. **View Results** - Access comprehensive analysis and downloadable files
5. **Browse Sessions** - Use the session browser to manage your transcription history

### Command Line Interface

For simple transcription without the web interface:

```bash
python transcribe.py
```

## 📊 Output Files

Each transcription session generates multiple output files:

- **`full_transcript.txt`** - Complete timestamped transcription
- **`assessment_mentions.txt`** - Educational keyword highlights
- **`questions.txt`** - Detected questions with timestamps
- **`emphasis_cues.txt`** - Important phrases and emphasis markers
- **`analysis.json`** - Complete analysis data in JSON format
- **`searchable_transcript.html`** - Interactive browser-based transcript
- **`metadata.json`** - Session information and statistics

## 🎯 Educational Keywords

The system automatically detects and highlights these educational terms:

**Academic Terms:**
- assignment, submission, deadline
- assessment, grading, criteria, feedback
- notebook, reference, output

**Technical Terms:**
- python, ipython, automate
- proof of concept

**Project-Specific:**
- RO1, RO2, RO3 (Research Objectives)

## 🛠️ Technical Architecture

### Core Components
- **Flask Web Framework** - RESTful API and web interface
- **OpenAI Whisper** - Speech-to-text transcription engine
- **FFmpeg** - Video processing and audio extraction
- **Python Libraries** - NumPy, JSON, regex for data processing

### Processing Pipeline
1. **Video Upload** - Secure file handling with validation
2. **Auto-Splitting** - FFmpeg splits video into 5-minute chunks
3. **Audio Extraction** - Convert video chunks to 16kHz mono WAV
4. **AI Transcription** - Whisper processes each audio chunk
5. **Content Analysis** - Regex patterns detect questions, keywords, emphasis
6. **Output Generation** - Multiple formats created automatically
7. **Session Storage** - Metadata and results saved for future access

## 🔧 Configuration

### Environment Variables
```bash
FLASK_ENV=production          # Set to 'development' for debug mode
MAX_CONTENT_LENGTH=500MB      # Maximum upload file size
WHISPER_MODEL=small           # Whisper model size (tiny/small/medium/large)
```

### Whisper Models
- **tiny** - Fastest, least accurate (~1GB)
- **small** - Balanced speed/accuracy (~2GB) - **Default**
- **medium** - Better accuracy (~5GB)
- **large** - Best accuracy (~10GB)

## 📁 Project Structure

```
video-transcriber/
├── app.py                    # Main Flask application
├── transcribe.py            # CLI transcription tool
├── requirements.txt         # Python dependencies
├── CLAUDE.md               # Development documentation
├── features.txt            # Feature specifications
├── templates/              # HTML templates
│   ├── index.html         # Upload interface
│   ├── results.html       # Results dashboard
│   └── sessions.html      # Session browser
├── uploads/               # Temporary upload storage
└── results/              # Transcription results
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

**Made with ❤️ for educational content creators**