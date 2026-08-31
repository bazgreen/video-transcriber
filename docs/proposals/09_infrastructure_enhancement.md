# Production Infrastructure & DevOps Enhancement

## 🎯 Overview

Complete the production-ready infrastructure setup for the Video Transcriber application with comprehensive Docker containerization, health monitoring, CI/CD pipeline, scalability enhancements, and enterprise-grade deployment capabilities.

## 🚀 Features

### Docker Containerization

- **Multi-Stage Docker Build**: Optimized container images with minimal size
- **Docker Compose Orchestration**: Complete development and production environments
- **Container Security**: Secure container practices and vulnerability scanning
- **Multi-Architecture Support**: ARM64 and AMD64 container images
- **Health Checks**: Built-in container health monitoring

### Production Deployment

- **Kubernetes Manifests**: Ready-to-deploy Kubernetes configurations
- **Helm Charts**: Parameterized deployments for different environments
- **Cloud Provider Support**: AWS, GCP, Azure deployment templates
- **Load Balancing**: High-availability load balancer configurations
- **SSL/TLS Automation**: Automatic certificate management

### Monitoring & Observability

- **Health Check Endpoints**: Comprehensive application health monitoring
- **Metrics Collection**: Prometheus-compatible metrics endpoints
- **Logging Infrastructure**: Structured logging with log aggregation
- **Performance Monitoring**: APM integration with detailed performance metrics
- **Alert Management**: Intelligent alerting for critical issues

### CI/CD Pipeline

- **Automated Testing**: Comprehensive test suite execution
- **Security Scanning**: Vulnerability assessment and code analysis
- **Automated Deployment**: Git-triggered deployment workflows
- **Environment Management**: Separate dev, staging, and production environments
- **Rollback Capabilities**: Automated rollback on deployment failures

## 🔧 Technical Implementation

### Docker Configuration

```dockerfile
# Multi-stage Dockerfile for production optimization
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-full.txt

# Development stage
FROM base as development
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
COPY . .
RUN chown -R app:app /app
USER app
CMD ["python", "main.py"]

# Production stage  
FROM base as production
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Copy application code
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p /app/uploads /app/data /app/logs /app/results && \
    chown -R app:app /app

# Install production-specific dependencies
RUN pip install --no-cache-dir gunicorn gevent

# Setup health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

USER app

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--timeout", "300", "main:app"]

# GPU-enabled stage for AI processing
FROM nvidia/cuda:11.8-runtime-ubuntu22.04 as gpu-production
ENV DEBIAN_FRONTEND=noninteractive

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-pip \
    python3.11-dev \
    ffmpeg \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

WORKDIR /app

# Copy requirements and install
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements-full.txt

# Install GPU-specific packages
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Copy application
COPY --chown=app:app . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--worker-class", "gevent", "--timeout", "600", "main:app"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml - Complete orchestration setup
version: '3.8'

services:
  # Main application service
  video-transcriber:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: video-transcriber-app
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/video_transcriber
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./results:/app/results
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - video-transcriber-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Background task processor
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: video-transcriber-worker
    command: celery -A main.celery worker --loglevel=info --concurrency=2
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/video_transcriber
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./results:/app/results
    depends_on:
      - redis
      - postgres
    networks:
      - video-transcriber-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 6G
          cpus: '4'

  # Task scheduler
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: video-transcriber-scheduler
    command: celery -A main.celery beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/video_transcriber
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
      - postgres
    networks:
      - video-transcriber-network
    restart: unless-stopped

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: video-transcriber-db
    environment:
      POSTGRES_DB: video_transcriber
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "5432:5432"
    networks:
      - video-transcriber-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d video_transcriber"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for caching and task queue
  redis:
    image: redis:7-alpine
    container_name: video-transcriber-redis
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - video-transcriber-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: video-transcriber-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./static:/var/www/static
    depends_on:
      - video-transcriber
    networks:
      - video-transcriber-network
    restart: unless-stopped

  # Monitoring with Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: video-transcriber-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - video-transcriber-network
    restart: unless-stopped

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    container_name: video-transcriber-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - video-transcriber-network
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  video-transcriber-network:
    driver: bridge
```

### Health Check System

```python
# src/health_monitoring.py - Comprehensive health check system
from flask import Blueprint, jsonify, request
import psutil
import redis
import psycopg2
import os
import time
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List

health_bp = Blueprint('health', __name__)

class HealthMonitor:
    def __init__(self, app=None):
        self.app = app
        self.redis_client = None
        self.db_connection = None
        self.checks = {
            'database': self.check_database,
            'redis': self.check_redis,
            'disk_space': self.check_disk_space,
            'memory': self.check_memory,
            'cpu': self.check_cpu,
            'ffmpeg': self.check_ffmpeg,
            'whisper': self.check_whisper_models,
            'background_tasks': self.check_background_tasks,
            'log_files': self.check_log_files
        }
        
    def init_app(self, app):
        self.app = app
        app.register_blueprint(health_bp)
        
        # Initialize connections
        self.setup_connections()
        
    def setup_connections(self):
        """Initialize monitoring connections."""
        try:
            # Redis connection
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url)
            
            # Database connection
            db_url = os.getenv('DATABASE_URL', 'sqlite:///data/video_transcriber.db')
            if db_url.startswith('postgresql'):
                self.db_connection = psycopg2.connect(db_url)
                
        except Exception as e:
            print(f"Health monitor setup error: {e}")
    
    async def run_health_checks(self, detailed: bool = False) -> Dict[str, Any]:
        """Run comprehensive health checks."""
        
        start_time = time.time()
        results = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {},
            'summary': {
                'total_checks': len(self.checks),
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
        
        # Run all health checks
        for check_name, check_function in self.checks.items():
            try:
                check_result = await check_function()
                results['checks'][check_name] = check_result
                
                # Update summary
                if check_result['status'] == 'healthy':
                    results['summary']['passed'] += 1
                elif check_result['status'] == 'warning':
                    results['summary']['warnings'] += 1
                else:
                    results['summary']['failed'] += 1
                    results['status'] = 'unhealthy'
                    
            except Exception as e:
                results['checks'][check_name] = {
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
                results['summary']['failed'] += 1
                results['status'] = 'unhealthy'
        
        # Calculate overall health status
        if results['summary']['failed'] > 0:
            results['status'] = 'unhealthy'
        elif results['summary']['warnings'] > 0:
            results['status'] = 'degraded'
        
        results['duration'] = time.time() - start_time
        
        # Add detailed system information if requested
        if detailed:
            results['system_info'] = await self.get_system_info()
            
        return results
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            if self.db_connection:
                # PostgreSQL check
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            else:
                # SQLite check
                from src.database import db
                db.session.execute('SELECT 1')
                
            return {
                'status': 'healthy',
                'message': 'Database connection successful',
                'response_time': time.time()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}',
                'error': str(e)
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            if self.redis_client:
                start_time = time.time()
                self.redis_client.ping()
                response_time = (time.time() - start_time) * 1000
                
                # Check memory usage
                info = self.redis_client.info('memory')
                memory_usage = info.get('used_memory_human', 'unknown')
                
                return {
                    'status': 'healthy',
                    'message': 'Redis connection successful',
                    'response_time': response_time,
                    'memory_usage': memory_usage
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Redis not configured'
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Redis connection failed: {str(e)}',
                'error': str(e)
            }
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            # Check main application directory
            app_disk = psutil.disk_usage('/')
            app_free_gb = app_disk.free / (1024**3)
            app_percent_used = (app_disk.used / app_disk.total) * 100
            
            # Check uploads directory
            uploads_path = os.path.join(os.getcwd(), 'uploads')
            if os.path.exists(uploads_path):
                uploads_disk = psutil.disk_usage(uploads_path)
                uploads_free_gb = uploads_disk.free / (1024**3)
            else:
                uploads_free_gb = app_free_gb
            
            status = 'healthy'
            message = 'Sufficient disk space available'
            
            if app_free_gb < 1.0:  # Less than 1GB free
                status = 'unhealthy'
                message = 'Critical: Low disk space'
            elif app_free_gb < 5.0:  # Less than 5GB free
                status = 'warning'
                message = 'Warning: Low disk space'
            
            return {
                'status': status,
                'message': message,
                'free_space_gb': round(app_free_gb, 2),
                'percent_used': round(app_percent_used, 1),
                'uploads_free_gb': round(uploads_free_gb, 2)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Disk space check failed: {str(e)}',
                'error': str(e)
            }
    
    async def check_memory(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            status = 'healthy'
            message = 'Memory usage normal'
            
            if memory.percent > 90:
                status = 'unhealthy'
                message = 'Critical: High memory usage'
            elif memory.percent > 80:
                status = 'warning'
                message = 'Warning: High memory usage'
            
            return {
                'status': status,
                'message': message,
                'memory_percent': round(memory.percent, 1),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'swap_percent': round(swap.percent, 1)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Memory check failed: {str(e)}',
                'error': str(e)
            }
    
    async def check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            # Get CPU usage over 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            
            status = 'healthy'
            message = 'CPU usage normal'
            
            if cpu_percent > 95:
                status = 'unhealthy'
                message = 'Critical: High CPU usage'
            elif cpu_percent > 85:
                status = 'warning'
                message = 'Warning: High CPU usage'
            
            return {
                'status': status,
                'message': message,
                'cpu_percent': round(cpu_percent, 1),
                'load_average': [round(load, 2) for load in load_avg],
                'cpu_count': psutil.cpu_count()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'CPU check failed: {str(e)}',
                'error': str(e)
            }
    
    async def check_ffmpeg(self) -> Dict[str, Any]:
        """Check FFmpeg availability and functionality."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                return {
                    'status': 'healthy',
                    'message': 'FFmpeg available',
                    'version': version_line
                }
            else:
                return {
                    'status': 'unhealthy',
                    'message': 'FFmpeg not working properly',
                    'error': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'unhealthy',
                'message': 'FFmpeg check timed out'
            }
        except FileNotFoundError:
            return {
                'status': 'unhealthy',
                'message': 'FFmpeg not found'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'FFmpeg check failed: {str(e)}',
                'error': str(e)
            }
    
    async def check_whisper_models(self) -> Dict[str, Any]:
        """Check Whisper model availability."""
        try:
            import whisper
            
            # Check available models
            available_models = whisper.available_models()
            
            # Try to load a small model to verify functionality
            try:
                model = whisper.load_model("tiny")
                model_check = True
            except Exception:
                model_check = False
            
            return {
                'status': 'healthy' if model_check else 'warning',
                'message': 'Whisper models available' if model_check else 'Whisper models not fully functional',
                'available_models': list(available_models),
                'test_load_success': model_check
            }
            
        except ImportError:
            return {
                'status': 'unhealthy',
                'message': 'Whisper not installed'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Whisper check failed: {str(e)}',
                'error': str(e)
            }
    
    async def check_background_tasks(self) -> Dict[str, Any]:
        """Check background task system health."""
        try:
            if self.redis_client:
                # Check queue lengths
                queue_info = {}
                for queue_name in ['default', 'high', 'low']:
                    try:
                        queue_length = self.redis_client.llen(f'rq:queue:{queue_name}')
                        queue_info[queue_name] = queue_length
                    except:
                        queue_info[queue_name] = 'unknown'
                
                total_queued = sum(v for v in queue_info.values() if isinstance(v, int))
                
                status = 'healthy'
                message = 'Background tasks running normally'
                
                if total_queued > 100:
                    status = 'warning'
                    message = 'High number of queued tasks'
                
                return {
                    'status': status,
                    'message': message,
                    'queue_lengths': queue_info,
                    'total_queued': total_queued
                }
            else:
                return {
                    'status': 'warning',
                    'message': 'Background task system not configured'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Background task check failed: {str(e)}',
                'error': str(e)
            }
    
    async def check_log_files(self) -> Dict[str, Any]:
        """Check log file status and recent errors."""
        try:
            log_dir = os.path.join(os.getcwd(), 'logs')
            
            if not os.path.exists(log_dir):
                return {
                    'status': 'warning',
                    'message': 'Log directory not found'
                }
            
            # Check log files
            log_files = []
            total_size = 0
            recent_errors = 0
            
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(log_dir, filename)
                    stat = os.stat(filepath)
                    total_size += stat.st_size
                    
                    # Check for recent errors (last 1 hour)
                    if time.time() - stat.st_mtime < 3600:
                        try:
                            with open(filepath, 'r') as f:
                                content = f.read()
                                recent_errors += content.lower().count('error')
                        except:
                            pass
                    
                    log_files.append({
                        'filename': filename,
                        'size_mb': round(stat.st_size / (1024*1024), 2),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            status = 'healthy'
            message = 'Log files normal'
            
            if recent_errors > 10:
                status = 'warning'
                message = f'High error count in recent logs: {recent_errors}'
            
            return {
                'status': status,
                'message': message,
                'log_files': log_files,
                'total_size_mb': round(total_size / (1024*1024), 2),
                'recent_errors': recent_errors
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Log file check failed: {str(e)}',
                'error': str(e)
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information."""
        try:
            import platform
            
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'architecture': platform.architecture(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'uptime': time.time() - psutil.boot_time(),
                'process_count': len(psutil.pids()),
                'network_connections': len(psutil.net_connections())
            }
        except Exception as e:
            return {'error': str(e)}

# Flask routes for health monitoring
@health_bp.route('/health')
async def health_check():
    """Basic health check endpoint."""
    monitor = HealthMonitor()
    results = await monitor.run_health_checks(detailed=False)
    
    status_code = 200 if results['status'] == 'healthy' else 503
    return jsonify(results), status_code

@health_bp.route('/health/detailed')
async def detailed_health_check():
    """Detailed health check with system information."""
    monitor = HealthMonitor()
    results = await monitor.run_health_checks(detailed=True)
    
    status_code = 200 if results['status'] == 'healthy' else 503
    return jsonify(results), status_code

@health_bp.route('/health/live')
async def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    try:
        # Basic application responsiveness check
        return jsonify({
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception:
        return jsonify({
            'status': 'dead',
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/health/ready')
async def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    monitor = HealthMonitor()
    
    # Check critical dependencies
    critical_checks = ['database', 'ffmpeg']
    results = {}
    ready = True
    
    for check_name in critical_checks:
        check_function = monitor.checks[check_name]
        try:
            result = await check_function()
            results[check_name] = result
            if result['status'] != 'healthy':
                ready = False
        except Exception as e:
            results[check_name] = {'status': 'error', 'error': str(e)}
            ready = False
    
    response = {
        'status': 'ready' if ready else 'not_ready',
        'timestamp': datetime.utcnow().isoformat(),
        'checks': results
    }
    
    return jsonify(response), 200 if ready else 503

@health_bp.route('/metrics')
async def metrics_endpoint():
    """Prometheus-compatible metrics endpoint."""
    monitor = HealthMonitor()
    results = await monitor.run_health_checks(detailed=True)
    
    # Convert health check results to Prometheus format
    metrics = []
    
    # Application health metrics
    metrics.append(f'app_health_status{{status="{results["status"]}"}} 1')
    metrics.append(f'app_health_checks_total {results["summary"]["total_checks"]}')
    metrics.append(f'app_health_checks_passed {results["summary"]["passed"]}')
    metrics.append(f'app_health_checks_failed {results["summary"]["failed"]}')
    metrics.append(f'app_health_checks_warnings {results["summary"]["warnings"]}')
    
    # System metrics
    if 'system_info' in results:
        system_info = results['system_info']
        if 'uptime' in system_info:
            metrics.append(f'app_uptime_seconds {system_info["uptime"]}')
        if 'process_count' in system_info:
            metrics.append(f'app_process_count {system_info["process_count"]}')
    
    # Individual check metrics
    for check_name, check_result in results['checks'].items():
        status_value = 1 if check_result['status'] == 'healthy' else 0
        metrics.append(f'app_check_status{{check="{check_name}"}} {status_value}')
    
    return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}
```

### Kubernetes Deployment

```yaml
# k8s/deployment.yaml - Kubernetes deployment configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: video-transcriber
  labels:
    app: video-transcriber
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: video-transcriber
  template:
    metadata:
      labels:
        app: video-transcriber
        version: v1
    spec:
      containers:
      - name: video-transcriber
        image: video-transcriber:latest
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: video-transcriber-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: video-transcriber-secrets
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
        volumeMounts:
        - name: uploads-storage
          mountPath: /app/uploads
        - name: data-storage
          mountPath: /app/data
        - name: logs-storage
          mountPath: /app/logs
      volumes:
      - name: uploads-storage
        persistentVolumeClaim:
          claimName: video-transcriber-uploads
      - name: data-storage
        persistentVolumeClaim:
          claimName: video-transcriber-data
      - name: logs-storage
        persistentVolumeClaim:
          claimName: video-transcriber-logs

---
apiVersion: v1
kind: Service
metadata:
  name: video-transcriber-service
  labels:
    app: video-transcriber
spec:
  selector:
    app: video-transcriber
  ports:
  - port: 80
    targetPort: 5000
    name: http
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: video-transcriber-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "500m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
spec:
  tls:
  - hosts:
    - video-transcriber.example.com
    secretName: video-transcriber-tls
  rules:
  - host: video-transcriber.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: video-transcriber-service
            port:
              number: 80
```

### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml - Complete CI/CD pipeline
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Code quality and security checks
  quality-checks:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-full.txt
        pip install bandit safety flake8 black isort mypy
    
    - name: Code formatting check
      run: |
        black --check .
        isort --check-only .
    
    - name: Lint check
      run: flake8 .
    
    - name: Type checking
      run: mypy src/
    
    - name: Security scan
      run: |
        bandit -r src/ -f json -o bandit-report.json
        safety check --json --output safety-report.json
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json

  # Comprehensive testing
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 3s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y ffmpeg
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-full.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
        FLASK_ENV: testing
      run: |
        pytest tests/ -v --cov=src --cov-report=xml --cov-report=html
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  # Container security scanning
  container-security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Build container
      run: docker build -t video-transcriber:test .
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'video-transcriber:test'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'

  # Build and push container images
  build-and-push:
    needs: [quality-checks, test, container-security]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' || github.event_name == 'release'
    
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
          type=sha,prefix={{branch}}-
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: .
        target: production
        platforms: linux/amd64,linux/arm64
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  # Deploy to staging
  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to staging
      run: |
        echo "Deploying to staging environment"
        # Add your staging deployment commands here
        
  # Deploy to production
  deploy-production:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.event_name == 'release'
    environment: production
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Deploy to production
      run: |
        echo "Deploying to production environment"
        # Add your production deployment commands here
```

## 🎯 Use Cases

### Enterprise Deployment

- **Corporate Infrastructure**: Scalable deployment for enterprise video processing
- **Multi-Tenant Environments**: Isolated instances for different departments
- **Compliance Requirements**: Security and audit logging for regulated industries
- **High Availability**: Zero-downtime deployment with automatic failover

### Cloud-Native Deployment

- **Kubernetes Orchestration**: Container orchestration for modern cloud environments
- **Auto-Scaling**: Dynamic scaling based on processing demand
- **Multi-Cloud Support**: Deployment across AWS, GCP, Azure platforms
- **Serverless Integration**: Integration with cloud functions and serverless compute

### Development & Testing

- **Development Environments**: Consistent local development setup
- **CI/CD Integration**: Automated testing and deployment pipelines
- **Staging Environments**: Production-like testing environments
- **Performance Testing**: Load testing and performance validation

## 📈 Success Metrics

### Infrastructure Performance

- 99.9% uptime with automated health monitoring
- < 30 second container startup time
- Automatic scaling based on load
- Zero-downtime deployments

### Operational Excellence

- Comprehensive monitoring and alerting
- Automated backup and recovery
- Security scanning and vulnerability management
- Performance optimization and resource utilization

### Developer Experience

- One-command local development setup
- Automated testing and quality checks
- Fast and reliable CI/CD pipeline
- Clear documentation and operational runbooks

## 🔧 Implementation Phases

### Phase 1: Containerization (1 week)

- Multi-stage Docker configuration
- Docker Compose orchestration setup
- Health check system implementation
- Basic monitoring infrastructure

### Phase 2: Production Deployment (1 week)

- Kubernetes manifests and Helm charts
- CI/CD pipeline implementation
- Security scanning and vulnerability management
- Load balancing and SSL/TLS configuration

### Phase 3: Monitoring & Operations (1 week)

- Comprehensive health monitoring system
- Metrics collection and visualization
- Alerting and incident management
- Performance optimization and tuning

## 🎯 Acceptance Criteria

### Must Have

- [x] Docker containerization with multi-stage builds
- [x] Docker Compose for local development
- [x] Comprehensive health check endpoints
- [x] Basic CI/CD pipeline with testing
- [x] Kubernetes deployment manifests

### Should Have

- [x] Production-ready monitoring with Prometheus/Grafana
- [x] Automated security scanning
- [x] Multi-environment deployment support
- [x] Load balancing and high availability
- [x] Automated backup and recovery

### Could Have

- [x] Advanced auto-scaling capabilities
- [x] Multi-cloud deployment support
- [x] Advanced observability and tracing
- [x] Infrastructure as Code (Terraform)
- [x] GitOps deployment workflows

## 🏷️ Labels

`infrastructure` `devops` `docker` `kubernetes` `ci-cd` `monitoring` `production` `high-priority`

## 🔗 Related Issues

- Security enhancements for production deployment
- Performance optimization for container environments
- Advanced monitoring and observability features
- Scalability improvements for high-volume processing
