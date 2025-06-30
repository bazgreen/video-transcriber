# API Documentation

## Overview

The Video Transcriber API provides RESTful endpoints for video processing, transcription, and analysis. The API is built with Flask and supports WebSocket connections for real-time progress updates.

## Base URL

```text
http://localhost:5001
```

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Content Types

- **Request**: `application/json`, `multipart/form-data` (for file uploads)
- **Response**: `application/json`

## Error Handling

All API responses follow a consistent error format:

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

## Endpoints

### Core Functionality

#### POST /upload

Upload and process a video file for transcription.

##### Request

- Method: `POST`
- Content-Type: `multipart/form-data`

##### Parameters

- `video` (file, required): Video file to process
- `session_name` (string, optional): Custom name for the session

##### Example Request

```bash
curl -X POST http://localhost:5001/upload \
  -F "video=@example.mp4" \
  -F "session_name=Meeting Recording"
```

##### Response
```json
{
  "success": true,
  "session_id": "meeting_recording_20250629_120000",
  "message": "Video processing started",
  "estimated_time": 300
}
```

#### GET /sessions

Retrieve list of all processing sessions.

**Response**
```json
{
  "sessions": [
    {
      "session_id": "meeting_20250629_120000",
      "session_name": "Team Meeting",
      "created_at": "2025-06-29T12:00:00Z",
      "status": "completed",
      "word_count": 1250,
      "duration": 300
    }
  ]
}
```

#### GET /results/<session_id>

Get detailed results for a specific session.

**Response**
```json
{
  "session_id": "meeting_20250629_120000",
  "metadata": {
    "original_filename": "meeting.mp4",
    "processing_time": 120.5,
    "created_at": "2025-06-29T12:00:00Z"
  },
  "analysis": {
    "total_words": 1250,
    "keyword_matches": [...],
    "questions": [...],
    "emphasis_cues": [...]
  }
}
```

### Configuration Management

#### GET /api/config/keywords

Get current keyword configuration.

**Response**
```json
{
  "keywords": ["important", "action", "decision", "deadline"]
}
```

#### POST /api/config/keywords

Update keyword configuration.

**Request Body**
```json
{
  "keywords": ["important", "action", "decision", "deadline", "follow-up"]
}
```

**Response**
```json
{
  "success": true,
  "message": "Keywords updated successfully",
  "count": 5
}
```

#### GET /api/performance

Get current performance configuration.

**Response**
```json
{
  "max_workers": 4,
  "chunk_duration": 300,
  "memory_limit": 8192,
  "parallel_processing": true
}
```

#### POST /api/performance

Update performance configuration.

**Request Body**
```json
{
  "max_workers": 6,
  "chunk_duration": 240
}
```

### Export Functionality

#### GET /download/<session_id>/<filename>

Download processed files (transcripts, analysis, etc.).

**Parameters**
- `session_id`: Session identifier
- `filename`: File to download (e.g., `full_transcript.txt`, `analysis.json`)

#### GET /api/export/<session_id>/<format>

Export session data in specific format.

**Supported Formats**
- `srt`: SubRip subtitle format
- `vtt`: WebVTT subtitle format
- `pdf`: PDF report
- `docx`: Word document
- `enhanced_txt`: Enhanced text format

**Response**
Returns the file in the requested format with appropriate Content-Type header.

#### POST /api/export/<session_id>/generate

Generate multiple export formats for a session.

**Request Body**
```json
{
  "formats": {
    "srt": true,
    "vtt": true,
    "pdf": true,
    "docx": false
  }
}
```

**Response**
```json
{
  "success": true,
  "exported_files": {
    "srt": "/download/session_123/subtitles.srt",
    "vtt": "/download/session_123/subtitles.vtt",
    "pdf": "/download/session_123/report.pdf"
  }
}
```

### Session Management

#### POST /sessions/delete/<session_id>

Delete a processing session and all associated files.

**Response**
```json
{
  "success": true,
  "message": "Session deleted successfully"
}
```

#### GET /transcript/<session_id>

Get interactive HTML transcript for a session.

**Response**
Returns HTML page with interactive transcript viewer.

## WebSocket Events

### Connection

Connect to WebSocket for real-time updates:

```javascript
const socket = io('http://localhost:5001');
```

### Events

#### join_session

Join a session to receive progress updates.

**Emit**
```javascript
socket.emit('join_session', {
  'session_id': 'meeting_20250629_120000'
});
```

#### progress_update

Receive progress updates during processing.

**Listen**
```javascript
socket.on('progress_update', function(data) {
  console.log('Progress:', data.progress);
  console.log('Current task:', data.current_task);
  console.log('Stage:', data.stage);
});
```

**Data Format**
```json
{
  "session_id": "meeting_20250629_120000",
  "progress": 75,
  "current_task": "Transcribing chunk 3 of 4",
  "stage": "transcription",
  "estimated_remaining": 30
}
```

#### processing_complete

Receive notification when processing is complete.

**Data Format**
```json
{
  "session_id": "meeting_20250629_120000",
  "status": "completed",
  "message": "Processing completed successfully",
  "results_url": "/results/meeting_20250629_120000"
}
```

## Rate Limits

Currently, no rate limits are enforced. However, consider:
- Maximum file size: 1GB per upload
- Concurrent processing: Limited by system resources
- WebSocket connections: No explicit limit

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_FILE_TYPE` | Unsupported video format |
| `FILE_TOO_LARGE` | File exceeds maximum size limit |
| `PROCESSING_ERROR` | Error during video processing |
| `SESSION_NOT_FOUND` | Requested session does not exist |
| `INVALID_SESSION_ID` | Malformed session identifier |
| `EXPORT_FAILED` | Error generating export format |
| `INSUFFICIENT_STORAGE` | Not enough disk space |
| `MEMORY_LIMIT_EXCEEDED` | Processing requires too much memory |

## Example Client Code

### JavaScript/Node.js

```javascript
// Upload video file
const formData = new FormData();
formData.append('video', videoFile);
formData.append('session_name', 'My Video');

fetch('http://localhost:5001/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Upload successful:', data.session_id);
});

// WebSocket connection
const socket = io('http://localhost:5001');

socket.on('connect', () => {
  socket.emit('join_session', { session_id: sessionId });
});

socket.on('progress_update', (data) => {
  updateProgressBar(data.progress);
});
```

### Python

```python
import requests
import socketio

# Upload video
files = {'video': open('video.mp4', 'rb')}
data = {'session_name': 'Python Upload'}

response = requests.post(
    'http://localhost:5001/upload',
    files=files,
    data=data
)

result = response.json()
session_id = result['session_id']

# WebSocket connection
sio = socketio.Client()

@sio.on('progress_update')
def on_progress(data):
    print(f"Progress: {data['progress']}%")

sio.connect('http://localhost:5001')
sio.emit('join_session', {'session_id': session_id})
```

### cURL Examples

```bash
# Upload video
curl -X POST http://localhost:5001/upload \
  -F "video=@meeting.mp4" \
  -F "session_name=Team Meeting"

# Get sessions
curl http://localhost:5001/sessions

# Download transcript
curl http://localhost:5001/download/session_123/full_transcript.txt

# Export as SRT
curl http://localhost:5001/api/export/session_123/srt \
  -o subtitles.srt

# Update keywords
curl -X POST http://localhost:5001/api/config/keywords \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["important", "action", "decision"]}'
```

## Development

### Running the API

```bash
python main.py
```

### Testing

```bash
# Run all tests
pytest tests/

# Test specific endpoint
pytest tests/integration/test_api.py::test_upload_endpoint
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `False` |
| `HOST` | Server host | `localhost` |
| `PORT` | Server port | `5001` |
| `MAX_FILE_SIZE` | Maximum upload size | `1GB` |
| `UPLOAD_FOLDER` | Upload directory | `uploads` |
| `RESULTS_FOLDER` | Results directory | `results` |

### Response Headers

All API responses include these headers:
- `Content-Type: application/json`
- `Access-Control-Allow-Origin: *` (in debug mode)
- `X-API-Version: 1.0`

## Changelog

### v1.2.0
- Added parallel processing support
- Enhanced export formats (PDF, DOCX)
- Performance optimization endpoints
- Real-time progress tracking

### v1.1.0
- Added keyword configuration
- WebSocket support for progress updates
- Interactive HTML transcripts
- Session management improvements

### v1.0.0
- Initial API release
- Basic video upload and transcription
- Text and JSON export formats
