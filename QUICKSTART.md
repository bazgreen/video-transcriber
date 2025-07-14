# Video Transcriber - Quick Start Guide

## 🚀 Quick Setup

### Core Installation (2-3 minutes)
```bash
git clone https://github.com/bazgreen/video-transcriber.git
cd video-transcriber
./run.sh  # Interactive installation with feature selection
```

### Docker Deployment (5 minutes)
```bash
# Built-in monitoring stack (8 services)
docker-compose up -d

# External monitoring (for enterprise)
docker-compose -f docker-compose.yml -f docker-compose.external-monitoring.yml up -d
```

## 🎯 Key Features

### 🎭 Speaker Diarization
- **Multi-speaker identification** with pyannote.audio
- **Interactive timeline visualization** with speaker segments
- **Export formats** with speaker information (SRT/VTT/TXT/JSON)
- **Real-time processing** with WebSocket updates

### 🌍 Multi-Language Support
- **99+ languages** with automatic detection
- **Language confidence scoring** and fallback options
- **Localized processing** optimized per language

### � Production Infrastructure
- **Docker containerization** with 8-service stack
- **Kubernetes manifests** with auto-scaling
- **Prometheus monitoring** with 281+ metrics
- **Grafana dashboards** for performance visualization
- **Celery background tasks** with Redis broker

## �📊 Monitoring Options

### Built-in Stack
- **Grafana**: <http://localhost:3000> (admin/admin)
- **Prometheus**: <http://localhost:9090>
- **Application**: <http://localhost:5001>
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### External Monitoring
For environments with existing Prometheus/Grafana:

```bash
export EXTERNAL_MONITORING=true
export PROMETHEUS_URL="http://your-prometheus:9090"
export GRAFANA_URL="http://your-grafana:3000"
docker-compose up -d
```

**Configuration Files:**
- `external-monitoring/prometheus-config.yml` - Scrape configuration
- `external-monitoring/grafana-dashboard.json` - Ready-to-import dashboard
- `external-monitoring/video_transcriber_alerts.yml` - Production alerts

## 🧪 Validation

Test all features including speaker diarization:
```bash
# Test speaker diarization service
python test_speaker_diarization.py

# Test speaker API endpoints  
python test_speaker_api.py

# Test external monitoring setup
python test_external_monitoring.py
```

## 🔧 Maintenance

### Stop Services
```bash
# Stop all services (Docker, Celery, Redis, etc.)
./kill.sh

# Stop just the main application
./kill_app.sh
```

### Clean Environment
```bash
# Complete cleanup (preserves source code)
python scripts/maintenance/clean_environment.py

# Quick cleanup
./clean.sh
```

## 📚 Documentation

- [Full Setup Guide](README.md)
- [Monitoring Documentation](docs/MONITORING.md)
- [Speaker Diarization Complete](SPEAKER_DIARIZATION_COMPLETE.md)
- [Infrastructure Guide](INFRASTRUCTURE_COMPLETE.md)
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)
