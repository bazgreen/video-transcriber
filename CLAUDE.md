# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based video transcription tool that processes video chunks and generates educational transcripts. The tool uses OpenAI Whisper for speech-to-text conversion and FFmpeg for audio extraction.

## Architecture

The main script `scripts/transcribe.py` orchestrates the entire transcription workflow:
- **Audio Extraction**: Uses FFmpeg to extract 16kHz mono audio from video chunks
- **Speech Recognition**: Uses Whisper's "small" model for transcription
- **Content Analysis**: Searches for educational keywords and generates assessment-related highlights
- **Output Generation**: Creates structured outputs including full transcripts, keyword highlights, and summaries

## Development Environment

- **Python Version**: 3.11.13
- **Virtual Environment**: `venv311/` (Python 3.11 virtual environment)
- **Key Dependencies**: 
  - `openai-whisper` for speech-to-text
  - `ffmpeg-python` for audio processing
  - Standard libraries: `os`, `re` for file operations and pattern matching

## Common Commands

### Setup and Activation
```bash
# Activate virtual environment
source venv311/bin/activate

# Install dependencies (if needed)
./venv311/bin/python -m pip install openai-whisper ffmpeg-python flask
```

### Running the Tools

#### Web Interface (Recommended)
```bash
# Start the web application
./venv311/bin/python app.py

# Access at http://localhost:5001
```

#### Command Line Interface
```bash
# Run the original CLI transcription script
./venv311/bin/python scripts/transcribe.py
```

### Package Management
```bash
# List installed packages
./venv311/bin/python -m pip list

# Install new packages
./venv311/bin/python -m pip install <package_name>
```

## Data Structure

The tool expects a specific directory structure:
- Input: Directory containing video chunks named `w1_part_XXX.mp4`
- Output: `transcripts/` subdirectory containing:
  - `full_transcript.txt` - Complete transcription
  - `assessment_mentions.txt` - Educational keyword highlights
  - `summary.txt` - Extracted assessment-related content

## Educational Keywords

The tool searches for these assessment-related terms:
- Academic: "assignment", "submission", "deadline", "assessment", "grading", "criteria", "feedback"
- Technical: "notebook", "python", "ipython", "output", "reference", "automate"
- Project-specific: "RO1", "RO2", "RO3", "proof of concept"

## Web Interface Features

The new web application (`app.py`) provides a comprehensive interface with all features from `features.txt`:

### Core Features
- **Auto Video Splitting**: Automatically splits long videos into 5-minute chunks
- **Timestamped Transcripts**: Precise timestamps for each segment
- **Smart Analysis**: Detects questions, emphasis cues, and educational keywords
- **Interactive HTML Transcripts**: Searchable, filterable transcript viewer
- **Keyword Frequency Analysis**: Visual charts showing keyword usage patterns
- **Multiple Export Formats**: TXT, JSON, and HTML outputs

### Analysis Capabilities
- **Question Detection**: Identifies spoken questions with timestamps
- **Emphasis Cue Recognition**: Finds phrases like "make sure...", "don't forget..."
- **Assessment Keyword Tracking**: Monitors educational terms and their frequency
- **Content Summarization**: Extracts key points and highlights

### File Outputs
- `full_transcript.txt` - Complete timestamped transcription
- `assessment_mentions.txt` - Educational keyword highlights  
- `questions.txt` - Detected questions with timestamps
- `emphasis_cues.txt` - Important phrases and emphasis markers
- `analysis.json` - Complete analysis data
- `searchable_transcript.html` - Interactive browser-based transcript

## File Processing Logic

### Performance Optimizations (v1.2.0)

- **Parallel Video Splitting**: Uses ThreadPoolExecutor to split multiple video chunks simultaneously
- **Parallel Transcription**: Uses ProcessPoolExecutor to transcribe multiple chunks on different CPU cores
- **Adaptive Chunking**: Dynamic chunk sizing (3-7 minutes) based on video length for optimal performance
- **Smart Worker Management**: Automatically determines optimal worker count based on CPU cores and memory
- **Memory Management**: Limits concurrent workers to prevent RAM overload (~2GB per Whisper process)
- **Automatic Cleanup**: Removes temporary video chunks after processing to save disk space

### Traditional Processing

- Automatically splits input videos using FFmpeg with parallel operations
- Extracts audio to `.wav` format (16kHz, mono, PCM) concurrently
- Transcribes chunks with Whisper's "small" model using multiple processes
- Aggregates results with adjusted timestamps maintaining chronological order
- Uses regex pattern matching for keyword extraction with 50-character context windows
- Generates comprehensive analysis and multiple output formats

### Performance APIs

- `GET /api/performance` - View current performance settings
- `POST /api/performance` - Update chunk duration and worker count for tuning