# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
make setup-dev          # Complete development environment setup
make install-dev        # Install development dependencies and pre-commit hooks
./run.sh               # Launch application (interactive installer)
```

### Testing
```bash
make test              # Run all tests with verbose output
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make test-coverage     # Run tests with coverage report (80% minimum required)
make benchmark         # Run performance benchmarks
pytest tests/unit -v   # Run unit tests directly
pytest -m "slow"       # Run slow tests
```

### Code Quality
```bash
make lint              # Run all linting checks (black, isort, flake8, mypy)
make format            # Format code with black and isort
make pre-commit        # Run all pre-commit hooks
make ci                # Run complete CI pipeline (lint + test-coverage)
```

### Application
```bash
make dev               # Run development server
python main.py         # Start Flask application directly
make docker-build      # Build Docker image
make docker-run        # Run in Docker (port 5001)
```

### Cleanup
```bash
make clean             # Clean temporary files and caches
./clean.sh             # Complete environment cleanup (removes .venv, uploads, results)
```

## Architecture

### Core Technologies
- **Python 3.11+** with Flask 3.0+ web framework
- **OpenAI Whisper** for speech-to-text transcription
- **FFmpeg** for video processing and audio extraction
- **SQLAlchemy + PostgreSQL** for production database
- **Celery + Redis** for background task processing
- **WebSocketIO** for real-time progress updates

### Modular Service Architecture
```
src/
├── config/           # Centralized configuration classes
├── models/           # Data models and core managers
├── routes/           # Web routes and API endpoints
├── services/         # Business logic and processing services
├── utils/            # Helper functions and utilities
└── tasks.py          # Celery background tasks
```

### Key Services
- **`src/services/transcription.py`** - Core video-to-text processing with parallel optimization
- **`src/services/ai_insights.py`** - Advanced AI analysis (sentiment, topics, entities)
- **`src/services/speaker_diarization.py`** - Multi-speaker identification
- **`src/services/export.py`** - Multi-format output generation (PDF, DOCX, SRT, VTT, HTML)
- **`src/services/batch_processing.py`** - Concurrent processing for multiple files

### Configuration Management
- **`src/config/settings.py`** - Centralized configuration with classes:
  - AppConfig - Application-wide settings and security
  - VideoConfig - Video processing and Whisper model settings
  - PerformanceConfig - Parallel processing optimization
  - MemoryConfig - Memory management and worker allocation
  - AnalysisConfig - Content analysis patterns and AI models

### Data Flow
1. **Video Upload** - Secure file handling with validation (`src/services/upload.py`)
2. **Parallel Processing** - Multi-core video splitting and transcription
3. **AI Analysis** - Optional sentiment analysis, topic modeling, entity recognition
4. **Export Generation** - Multiple output formats with professional styling
5. **Session Storage** - Persistent session management with metadata

## Development Patterns

### Dependency Injection
The application uses dependency injection where managers (memory, file, progress) are initialized centrally and passed to services for better testability and modularity.

### Graceful Fallback System
Optional AI dependencies are handled with feature detection:
```python
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
```

### Progressive Enhancement
- **Core Installation** - Essential transcription features (2-3 minutes setup)
- **Full Installation** - Complete AI capabilities (5-8 minutes setup)
- **One-Command Upgrade** - `python scripts/install_ai_features.py`

### Performance Optimization
- **Parallel Processing** - Multi-core transcription with 2-4x speed improvements
- **Adaptive Chunking** - Smart video segmentation (3-7 minutes based on video length)
- **Memory-Aware Processing** - Dynamic worker allocation based on system resources

## Testing Structure

### Test Organization
- `tests/unit/` - Component-level tests
- `tests/integration/` - End-to-end workflow tests
- `tests/benchmarks/` - Performance testing suite
- `tests/fixtures/` - Test data and mocks

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.benchmark` - Performance tests
- `@pytest.mark.requires_model` - Tests requiring Whisper model
- `@pytest.mark.requires_ffmpeg` - Tests requiring FFmpeg

### Coverage Requirements
- Minimum coverage: 80%
- Coverage scope: `src/` directory
- Reports: HTML (htmlcov/) and terminal

## Production Deployment

### Docker Stack
Complete production infrastructure with 8 services:
- Main application with Gunicorn WSGI server
- PostgreSQL database with connection pooling
- Redis for caching and task queuing
- Celery workers for background processing
- Nginx reverse proxy with SSL support
- Prometheus metrics collection
- Grafana visualization dashboards
- Comprehensive health monitoring

### Deployment Commands
```bash
docker-compose up -d                # Production deployment
kubectl apply -f k8s/               # Kubernetes deployment
```

### Monitoring Endpoints
- **Application Health**: `http://localhost/health`
- **Prometheus Metrics**: `http://localhost:9090`
- **Grafana Dashboards**: `http://localhost:3000` (admin/admin)

## Key File Locations

### Configuration
- `config/keywords_config.json` - Keyword detection configuration
- `data/config/` - Runtime configuration files
- `.env` - Environment variables (not in repo)

### Entry Points
- `main.py` - Flask application factory and entry point
- `src/routes/main.py` - Primary web routes and UI endpoints
- `src/routes/api.py` - RESTful API endpoints

### Templates & Static Assets
- `data/templates/` - HTML templates (Jinja2)
- `data/static/` - CSS, JavaScript, and PWA assets

## Development Notes

### Code Quality
- Pre-commit hooks enforce Black formatting, isort import sorting, flake8 linting, and mypy type checking
- All new code must maintain 80% test coverage
- Security scanning with Bandit is required

### AI Features
AI capabilities (sentiment analysis, topic modeling, entity recognition) are optional dependencies that can be installed separately with `python scripts/install_ai_features.py`.

### Performance Considerations
The application automatically optimizes for available system resources. Worker count defaults to `min(CPU_cores, 4)` and chunk duration adapts based on video length for optimal performance.