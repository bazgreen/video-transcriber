# Video Transcriber - Infrastructure Documentation

## 🏗️ Infrastructure Overview

The Video Transcriber application includes comprehensive infrastructure for development, testing, and production deployment across multiple platforms.

## 📦 Deployment Options

### 1. Docker Development Stack

**Quick Start:**
```bash
# Build and run the complete development stack
./scripts/deployment/deploy-docker.sh

# Or run individual components
docker-compose up -d
```

**Features:**
- Multi-stage Dockerfile with development, production, and GPU variants
- Complete service orchestration with docker-compose
- Health monitoring and metrics collection
- Automatic service discovery and load balancing

### 2. Kubernetes Production Deployment

**Prerequisites:**
- kubectl configured with cluster access
- Helm 3.x (optional but recommended)
- Docker registry access

**Deployment:**
```bash
# Deploy to Kubernetes cluster
./scripts/deployment/deploy-k8s.sh

# Deploy to specific environment
ENVIRONMENT=production NAMESPACE=video-transcriber-prod ./scripts/deployment/deploy-k8s.sh

# Check deployment status
./scripts/deployment/deploy-k8s.sh status

# Clean up deployment
./scripts/deployment/deploy-k8s.sh cleanup --confirm
```

## 🐳 Docker Configuration

### Base Image Strategy

```dockerfile
# Multi-stage build for optimized images
FROM python:3.11-slim as base
# System dependencies and security hardening

FROM base as development
# Development tools and debugging capabilities

FROM base as production
# Optimized for production with minimal attack surface

FROM nvidia/cuda:11.8-base-ubuntu22.04 as gpu
# GPU-enabled variant for accelerated transcription
```

### Service Architecture

| Service | Purpose | Ports | Dependencies |
|---------|---------|-------|--------------|
| video-transcriber | Main web application | 5000 | postgres, redis |
| celery-worker | Background task processing | - | postgres, redis |
| celery-beat | Scheduled task management | - | postgres, redis |
| postgres | Primary database | 5432 | - |
| redis | Cache and message broker | 6379 | - |
| nginx | Reverse proxy and load balancer | 80, 443 | video-transcriber |
| prometheus | Metrics collection | 9090 | all services |
| grafana | Monitoring dashboard | 3000 | prometheus |

### Health Monitoring

The application includes comprehensive health monitoring:

```python
# Integrated health checks
- Database connectivity
- Disk space utilization
- Memory usage
- CPU load
- FFmpeg availability
- Whisper model accessibility
```

## ☸️ Kubernetes Deployment

### Manifest Structure

```
k8s/
├── deployment.yaml    # Main application deployment
├── storage.yaml      # Persistent volume claims
├── database.yaml     # PostgreSQL and Redis
├── workers.yaml      # Celery worker deployment
└── monitoring.yaml   # Prometheus and Grafana
```

### Helm Chart

The Helm chart provides parameterized deployment with environment-specific values:

```yaml
# Development values
replicaCount: 1
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"

# Production values  
replicaCount: 3
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
```

### Auto-scaling Configuration

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: video-transcriber-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: video-transcriber
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# Automated pipeline stages
1. Quality Checks
   - Code formatting (black, isort)
   - Linting (flake8, pylint)
   - Type checking (mypy)
   - Security scanning (bandit)

2. Testing
   - Unit tests with pytest
   - Integration tests
   - API endpoint validation
   - Database migration tests

3. Container Security
   - Vulnerability scanning (Trivy)
   - Image security analysis
   - Dependency audit

4. Build and Deploy
   - Multi-platform container builds
   - Registry push with tags
   - Automated deployment to staging
```

### Deployment Environments

| Environment | Trigger | Purpose | Configuration |
|-------------|---------|---------|---------------|
| Development | Feature branches | Testing new features | Minimal resources, debug enabled |
| Staging | Main branch | Pre-production validation | Production-like, test data |
| Production | Release tags | Live application | High availability, monitoring |

## 📊 Monitoring and Observability

### Metrics Collection

**Prometheus Metrics:**
- Application performance (request duration, error rates)
- System resources (CPU, memory, disk usage)
- Business metrics (transcription jobs, user activity)
- Database performance (query execution, connection pool)

**Grafana Dashboards:**
- Application Overview
- System Resources
- Database Performance
- Celery Task Monitoring
- Error Tracking

### Log Aggregation

```yaml
# Structured logging configuration
logging:
  version: 1
  formatters:
    structured:
      format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
  handlers:
    file:
      class: logging.FileHandler
      filename: /var/log/video-transcriber/app.log
      formatter: structured
```

### Alerting Rules

```yaml
# Prometheus alerting rules
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: High error rate detected

- alert: DatabaseConnectionFailure
  expr: up{job="postgres"} == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: Database connection failure
```

## 🔧 Maintenance and Operations

### Backup Strategy

```bash
# Database backup automation
#!/bin/bash
# Daily PostgreSQL backup with rotation
BACKUP_DIR="/var/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump video_transcriber > "$BACKUP_DIR/backup_$TIMESTAMP.sql"

# Keep last 30 days of backups
find "$BACKUP_DIR" -name "backup_*.sql" -mtime +30 -delete
```

### Scaling Considerations

**Horizontal Scaling:**
- Stateless application design
- Session storage in Redis
- File uploads to object storage
- Database read replicas

**Vertical Scaling:**
- Resource monitoring and adjustment
- Memory optimization for large files
- CPU allocation for transcription tasks

### Security Hardening

**Container Security:**
- Non-root user execution
- Read-only root filesystem
- Security context constraints
- Network policies

**Application Security:**
- JWT token authentication
- CSRF protection
- Rate limiting
- Input validation and sanitization

## 🚀 Quick Reference

### Essential Commands

```bash
# Development
docker-compose up -d                    # Start development stack
docker-compose logs -f video-transcriber # View application logs

# Production
kubectl get pods -n video-transcriber   # Check pod status
kubectl logs -f deployment/video-transcriber # View application logs
kubectl port-forward svc/grafana 3000:3000  # Access monitoring

# Maintenance
./scripts/deployment/deploy-docker.sh cleanup  # Clean development environment
./scripts/deployment/deploy-k8s.sh cleanup --confirm  # Clean production deployment
```

### Troubleshooting

**Common Issues:**
1. **Database Connection**: Check postgres service status and connection string
2. **Memory Issues**: Monitor container resource limits and usage
3. **File Upload Failures**: Verify storage permissions and disk space
4. **Transcription Errors**: Check FFmpeg installation and Whisper models

**Debug Mode:**
```bash
# Enable debug logging
export FLASK_ENV=development
export LOG_LEVEL=DEBUG

# Run with debug configuration
docker-compose -f docker-compose.debug.yml up
```

### Performance Optimization

**Recommended Settings:**
- **CPU**: 2+ cores for transcription processing
- **Memory**: 4GB+ for large audio files
- **Storage**: SSD for temporary file processing
- **Network**: 100Mbps+ for file uploads

**Tuning Parameters:**
```yaml
# Celery worker configuration
CELERY_WORKER_CONCURRENCY: 4
CELERY_WORKER_MAX_TASKS_PER_CHILD: 1000
CELERY_TASK_SOFT_TIME_LIMIT: 300
CELERY_TASK_TIME_LIMIT: 600
```

## 📚 Additional Resources

- [Docker Documentation](docs/DOCKER.md)
- [Kubernetes Guide](docs/KUBERNETES.md)
- [Monitoring Setup](docs/MONITORING.md)
- [Security Guidelines](docs/SECURITY.md)
- [Performance Tuning](docs/PERFORMANCE_OPTIMIZATION.md)
