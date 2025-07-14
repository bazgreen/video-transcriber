# Video Transcriber - Quick Start Guide

## 🚀 Quick Setup

### Core Installation (2-3 minutes)
```bash
git clone https://github.com/bazgreen/video-transcriber.git
cd video-transcriber
python scripts/install_ai_features.py
```

### Docker Deployment (5 minutes)
```bash
# Built-in monitoring stack
docker-compose up -d

# External monitoring (for enterprise)
docker-compose -f docker-compose.yml -f docker-compose.external-monitoring.yml up -d
```

## 📊 Monitoring Options

### Built-in Stack
- **Grafana**: <http://localhost:3000> (admin/admin)
- **Prometheus**: <http://localhost:9090>
- **Application**: <http://localhost:5001>

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

## 🧪 Validation

Test external monitoring setup:
```bash
python test_external_monitoring.py
```

## 📚 Documentation

- [Full Setup Guide](README.md)
- [Monitoring Documentation](docs/MONITORING.md)
- [Infrastructure Guide](docs/INFRASTRUCTURE.md)
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)
