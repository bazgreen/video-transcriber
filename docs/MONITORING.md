# Video Transcriber - Monitoring Documentation

## 📊 Overview

The Video Transcriber application provides comprehensive monitoring capabilities with support for both self-contained and external monitoring infrastructure setups.

## 🎯 Monitoring Architecture

### Self-Contained Monitoring

**Components:**
- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **AlertManager** - Alert routing and notifications

**Default Deployment:**
```bash
# Includes built-in monitoring stack
docker-compose up -d
```

**Access Points:**
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- AlertManager: http://localhost:9093

### External Monitoring Integration

For enterprise environments with existing Prometheus and Grafana infrastructure.

**Environment Configuration:**
```bash
export EXTERNAL_MONITORING=true
export PROMETHEUS_URL="http://your-prometheus-server:9090"
export GRAFANA_URL="http://your-grafana-server:3000"
```

**Deployment:**
```bash
# Use external monitoring override
docker-compose -f docker-compose.yml -f docker-compose.external-monitoring.yml up -d
```

**Features:**
- Automatic detection of external monitoring setup
- Disables built-in monitoring containers when external setup detected
- Provides metrics endpoints optimized for external scraping
- Configuration validation via `/monitoring/config` endpoint

## 📈 Metrics Collection

### Application Metrics

**HTTP Metrics:**
```
http_requests_total{method, endpoint, status}           # Request count by method/endpoint/status
http_request_duration_seconds{method, endpoint}        # Request duration histogram
http_requests_in_progress{method, endpoint}            # Active requests gauge
```

**Transcription Metrics:**
```
transcription_jobs_total                               # Total transcription jobs
transcription_jobs_active                              # Currently active jobs
transcription_jobs_completed{status}                   # Completed jobs by status
transcription_jobs_failed{error_type}                  # Failed jobs by error type
transcription_duration_seconds                         # Job processing time
transcription_file_size_bytes                          # Input file sizes
```

**System Metrics:**
```
process_resident_memory_bytes                          # Memory usage
process_cpu_seconds_total                              # CPU time
process_open_fds                                       # Open file descriptors
database_connections_active                            # Active DB connections
database_connections_total                             # Total DB connections
redis_connected_clients                                # Redis connections
```

**Business Metrics:**
```
user_sessions_active                                   # Active user sessions
file_uploads_total{file_type}                          # Uploads by type
export_requests_total{format}                          # Export requests by format
ai_insights_generated_total                            # AI insights count
```

### Health Endpoints

**Application Health:**
```
GET /health
{
  "status": "healthy",
  "timestamp": "2025-07-14T10:30:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "disk_space": "healthy",
    "memory": "healthy"
  },
  "version": "1.0.0"
}
```

**Detailed Monitoring:**
```
GET /monitoring/health
{
  "status": "healthy",
  "timestamp": "2025-07-14T10:30:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5,
      "active_connections": 12
    },
    "redis": {
      "status": "healthy",
      "response_time_ms": 2,
      "connected_clients": 8
    },
    "disk_space": {
      "status": "healthy",
      "used_percent": 45,
      "available_gb": 150
    },
    "memory": {
      "status": "healthy",
      "used_percent": 68,
      "available_mb": 2048
    },
    "ffmpeg": {
      "status": "healthy",
      "version": "4.4.2"
    }
  }
}
```

## 🔧 External Monitoring Setup

### Prometheus Configuration

Add these job configurations to your existing `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'video-transcriber-app'
    static_configs:
      - targets: ['video-transcriber-app:5000']
    metrics_path: '/monitoring/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s

  - job_name: 'video-transcriber-health'
    static_configs:
      - targets: ['video-transcriber-app:5000']
    metrics_path: '/monitoring/health'
    scrape_interval: 30s
    scrape_timeout: 10s
```

**Using Configuration File:**
```bash
# Copy provided configuration
cp external-monitoring/prometheus-config.yml /etc/prometheus/conf.d/video-transcriber.yml

# Reload Prometheus configuration
curl -X POST http://your-prometheus:9090/-/reload
```

### Grafana Dashboard Setup

**Method 1: Import JSON Dashboard**
1. Download `external-monitoring/grafana-dashboard.json`
2. In Grafana UI: Dashboards → Import
3. Upload the JSON file
4. Configure datasource (use your Prometheus instance)

**Method 2: Provision Dashboard**
```bash
# Copy dashboard to Grafana provisioning directory
cp external-monitoring/grafana-dashboard.json /etc/grafana/provisioning/dashboards/

# Copy datasource configuration
cp external-monitoring/grafana-datasource.yml /etc/grafana/provisioning/datasources/

# Restart Grafana to load configurations
systemctl restart grafana-server
```

**Dashboard Panels:**
1. **Application Health** - Service status indicators
2. **Request Rate** - HTTP requests per second by endpoint
3. **Response Times** - 50th and 95th percentile response times
4. **Transcription Jobs** - Job counts by status over time
5. **System Resources** - Memory and CPU usage
6. **Database Connections** - Active and total connections
7. **Error Rate** - HTTP 4xx/5xx error rates with alerting

### Alerting Rules

Import alerting rules to your Prometheus:

```bash
# Copy alert rules
cp external-monitoring/video_transcriber_alerts.yml /etc/prometheus/rules/

# Add to prometheus.yml
rule_files:
  - "rules/video_transcriber_alerts.yml"

# Reload Prometheus
curl -X POST http://your-prometheus:9090/-/reload
```

**Key Alerts:**
- **HighErrorRate** - Error rate > 10% for 5 minutes
- **DatabaseDown** - Database connectivity failure
- **HighMemoryUsage** - Memory usage > 90% for 5 minutes
- **HighResponseTime** - 95th percentile > 5 seconds
- **TranscriptionJobsStuck** - Active jobs without progress for 30 minutes
- **DiskSpaceLow** - Available disk space < 10%

## 🧪 Testing and Validation

### External Monitoring Test

Run the comprehensive test suite:

```bash
# Test external monitoring integration
python test_external_monitoring.py
```

**Test Coverage:**
- External monitoring detection
- Metrics endpoint functionality
- Health endpoint responses
- Configuration file validation
- Grafana dashboard structure

### Manual Validation

**Check Configuration Detection:**
```bash
# Verify external monitoring is detected
curl http://your-app:5000/monitoring/config

# Expected response:
{
  "external_monitoring": true,
  "prometheus_url": "http://your-prometheus:9090",
  "grafana_url": "http://your-grafana:3000",
  "metrics_endpoint": "/monitoring/metrics",
  "health_endpoint": "/monitoring/health"
}
```

**Validate Metrics Endpoint:**
```bash
# Check metrics are being exported
curl http://your-app:5000/monitoring/metrics | grep "http_requests_total"

# Expected output:
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/",status="200"} 1234
```

**Test Health Endpoint:**
```bash
# Verify health checks
curl http://your-app:5000/monitoring/health | jq '.status'

# Expected: "healthy"
```

## 📋 Monitoring Checklist

### Pre-Production Setup

- [ ] External monitoring environment variables configured
- [ ] Prometheus scrape configuration added
- [ ] Grafana datasource configured
- [ ] Dashboard imported and functional
- [ ] Alerting rules loaded
- [ ] Test script executed successfully
- [ ] Baseline metrics established

### Production Monitoring

- [ ] All health checks passing
- [ ] Metrics collection stable (>95% success rate)
- [ ] Dashboard displaying data correctly
- [ ] Alerts configured and tested
- [ ] On-call procedures documented
- [ ] Monitoring documentation updated

### Ongoing Maintenance

- [ ] Weekly review of error patterns
- [ ] Monthly capacity planning assessment
- [ ] Quarterly alert rule optimization
- [ ] Annual monitoring infrastructure review

## 🔍 Troubleshooting

### Common Issues

**Metrics Not Appearing:**
1. Check Prometheus scrape configuration
2. Verify network connectivity to application
3. Confirm metrics endpoint is accessible
4. Check Prometheus logs for scrape errors

**External Monitoring Not Detected:**
1. Verify environment variables are set correctly
2. Check application logs for configuration errors
3. Confirm `/monitoring/config` endpoint shows external setup
4. Restart application after environment changes

**Dashboard Data Missing:**
1. Verify Grafana datasource configuration
2. Check Prometheus data retention
3. Confirm query syntax in dashboard panels
4. Review Grafana logs for errors

**Alerts Not Firing:**
1. Check alerting rule syntax
2. Verify alert thresholds are appropriate
3. Confirm AlertManager configuration
4. Test alert rules with promtool

### Debug Commands

```bash
# Check application configuration
kubectl exec deployment/video-transcriber -- curl localhost:5000/monitoring/config

# Validate Prometheus scraping
kubectl exec deployment/prometheus -- promtool query instant 'up{job="video-transcriber-app"}'

# Test Grafana datasource
kubectl exec deployment/grafana -- curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up

# Check alerting rules
kubectl exec deployment/prometheus -- promtool check rules /etc/prometheus/rules/
```

## 📚 Resources

### Configuration Files

- `external-monitoring/prometheus-config.yml` - Complete Prometheus configuration
- `external-monitoring/grafana-datasource.yml` - Grafana datasource setup
- `external-monitoring/grafana-dashboard.json` - Pre-built dashboard
- `external-monitoring/video_transcriber_alerts.yml` - Production alerting rules

### API Endpoints

- `GET /health` - Basic health check
- `GET /monitoring/health` - Detailed health information
- `GET /monitoring/metrics` - Prometheus metrics
- `GET /monitoring/config` - Monitoring configuration details

### External Documentation

- [Prometheus Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
- [Alert Rule Writing](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
