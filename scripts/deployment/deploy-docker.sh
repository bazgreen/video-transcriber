#!/bin/bash
set -euo pipefail

# Video Transcriber - Docker Deployment Script
# This script builds and deploys the video transcriber using Docker Compose

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Check if Docker is running
check_docker() {
    log "Checking Docker availability..."
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    success "Docker is running"
}

# Check if Docker Compose is available
check_docker_compose() {
    log "Checking Docker Compose availability..."
    if ! command -v docker-compose >/dev/null 2>&1; then
        error "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    success "Docker Compose is available"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."

    local directories=(
        "data"
        "uploads"
        "logs"
        "results"
        "monitoring/prometheus"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
        "nginx"
        "scripts"
    )

    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done

    success "Directories created successfully"
}

# Create monitoring configuration files
create_monitoring_config() {
    log "Creating monitoring configuration..."

    # Prometheus configuration
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'video-transcriber'
    static_configs:
      - targets: ['video-transcriber:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
EOF

    # Grafana datasource configuration
    mkdir -p monitoring/grafana/datasources
    cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    success "Monitoring configuration created"
}

# Create Nginx configuration
create_nginx_config() {
    log "Creating Nginx configuration..."

    cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;

error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 500M;

    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/x-javascript
        application/xml+rss
        application/json;

    upstream video_transcriber {
        server video-transcriber:5000;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://video_transcriber;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Increase timeouts for large file uploads
            proxy_connect_timeout 600s;
            proxy_send_timeout 600s;
            proxy_read_timeout 600s;
        }

        location /health {
            proxy_pass http://video_transcriber/health;
            access_log off;
        }

        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

    success "Nginx configuration created"
}

# Build Docker images
build_images() {
    log "Building Docker images..."

    # Build main application image
    log "Building main application image..."
    docker build -t video-transcriber:latest --target production .

    success "Docker images built successfully"
}

# Deploy with Docker Compose
deploy() {
    log "Deploying with Docker Compose..."

    # Stop any existing containers
    docker-compose down

    # Start all services
    docker-compose up -d

    success "Deployment completed successfully"
}

# Check service health
check_health() {
    log "Checking service health..."

    # Wait a bit for services to start
    sleep 30

    # Check main application
    local app_health=""
    for i in {1..30}; do
        if app_health=$(curl -s http://localhost:5000/health 2>/dev/null); then
            success "Main application is healthy"
            break
        else
            log "Waiting for main application to be ready... (attempt $i/30)"
            sleep 10
        fi
    done

    if [[ -z "$app_health" ]]; then
        error "Main application failed to start properly"
        return 1
    fi

    # Check other services
    local services=("prometheus:9090" "grafana:3000" "postgres:5432" "redis:6379")

    for service in "${services[@]}"; do
        local host="${service%:*}"
        local port="${service#*:}"

        if docker-compose exec -T "$host" sh -c "echo 'Service check'" >/dev/null 2>&1; then
            success "$host service is running"
        else
            warning "$host service may not be ready yet"
        fi
    done
}

# Show deployment information
show_info() {
    log "Deployment Information:"
    echo ""
    echo "🌐 Application URL: http://localhost:5000"
    echo "📊 Prometheus: http://localhost:9090"
    echo "📈 Grafana: http://localhost:3000 (admin/admin)"
    echo "💾 Database: localhost:5432"
    echo "🗄️ Redis: localhost:6379"
    echo ""
    echo "📁 Data Directories:"
    echo "   - uploads/     - Uploaded files"
    echo "   - data/        - Application data"
    echo "   - logs/        - Application logs"
    echo "   - results/     - Transcription results"
    echo ""
    echo "🔧 Management Commands:"
    echo "   - docker-compose logs -f        # View logs"
    echo "   - docker-compose down           # Stop all services"
    echo "   - docker-compose restart        # Restart services"
    echo "   - docker-compose ps             # Show service status"
    echo ""
    success "Deployment completed successfully!"
}

# Main execution
main() {
    log "Starting Video Transcriber deployment..."

    check_docker
    check_docker_compose
    create_directories
    create_monitoring_config
    create_nginx_config
    build_images
    deploy
    check_health
    show_info
}

# Run main function
main "$@"
