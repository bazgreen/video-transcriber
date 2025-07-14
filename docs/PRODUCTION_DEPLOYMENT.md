# Video Transcriber - Production Deployment Guide

## 🎯 Deployment Prerequisites

Before deploying to production, ensure you have:

### Required Tools
- Docker 20.10+ with BuildKit enabled
- kubectl configured with cluster access  
- Helm 3.x (recommended for Kubernetes deployment)
- Access to container registry (Docker Hub, ECR, GCR, etc.)

### Infrastructure Requirements
- Kubernetes cluster (1.20+) or Docker Swarm
- Persistent storage (100GB+ recommended)
- Load balancer with SSL termination
- Monitoring infrastructure (Prometheus/Grafana)

### Security Requirements
- TLS certificates for HTTPS
- Database credentials and encryption keys
- Authentication provider configuration
- Network security policies

## 🚀 Production Deployment Steps

### Step 1: Container Image Build

```bash
# Build production images
docker build --target production -t video-transcriber:latest .
docker build --target gpu -t video-transcriber:gpu .

# Tag and push to registry
docker tag video-transcriber:latest your-registry/video-transcriber:v1.0.0
docker push your-registry/video-transcriber:v1.0.0
```

### Step 2: Environment Configuration

Create production environment file:

```bash
# Create production.env
cat > production.env << EOF
# Application Settings
FLASK_ENV=production
SECRET_KEY=your-super-secure-secret-key
DATABASE_URL=postgresql://user:pass@postgres:5432/video_transcriber
REDIS_URL=redis://redis:6379/0

# Security Settings
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
CSRF_COOKIE_SECURE=true

# Performance Settings
CELERY_WORKER_CONCURRENCY=4
MAX_CONTENT_LENGTH=2147483648  # 2GB max upload

# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
EOF
```

### Step 3: Deploy to Kubernetes

```bash
# Deploy using Helm (recommended)
helm upgrade --install video-transcriber ./helm/video-transcriber \
  --namespace video-transcriber-prod \
  --create-namespace \
  --set environment=production \
  --set image.repository=your-registry/video-transcriber \
  --set image.tag=v1.0.0 \
  --set ingress.enabled=true \
  --set ingress.hostname=transcriber.yourdomain.com \
  --values helm/video-transcriber/values-production.yaml

# Or deploy using kubectl
ENVIRONMENT=production NAMESPACE=video-transcriber-prod ./scripts/deployment/deploy-k8s.sh
```

### Step 4: SSL/TLS Configuration

```yaml
# ingress-tls.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: video-transcriber-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - transcriber.yourdomain.com
    secretName: video-transcriber-tls
  rules:
  - host: transcriber.yourdomain.com
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

### Step 5: Database Migration

```bash
# Run database migrations
kubectl exec -it deployment/video-transcriber -- flask db upgrade

# Create initial admin user (optional)
kubectl exec -it deployment/video-transcriber -- python scripts/create-admin.py
```

## 📊 Production Monitoring Setup

### Built-in Monitoring Stack

The application includes a complete monitoring solution:

### Prometheus Configuration

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'video-transcriber'
    static_configs:
      - targets: ['video-transcriber-service:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### External Monitoring Integration

For enterprise environments with existing Prometheus and Grafana infrastructure:

**Environment Setup:**
```bash
export EXTERNAL_MONITORING=true
export PROMETHEUS_URL="http://your-prometheus-server:9090"
export GRAFANA_URL="http://your-grafana-server:3000"
```

**Deployment with External Monitoring:**
```bash
# Use external monitoring override
docker-compose -f docker-compose.yml -f docker-compose.external-monitoring.yml up -d

# Or with Helm
helm upgrade --install video-transcriber ./helm/video-transcriber \
  --set monitoring.external.enabled=true \
  --set monitoring.external.prometheusUrl="http://your-prometheus:9090" \
  --set monitoring.external.grafanaUrl="http://your-grafana:3000"
```

**Integration Files:**
- `external-monitoring/prometheus-config.yml` - Scrape configuration for external Prometheus
- `external-monitoring/grafana-datasource.yml` - Datasource configuration 
- `external-monitoring/grafana-dashboard.json` - Pre-built dashboard with comprehensive metrics
- `external-monitoring/video_transcriber_alerts.yml` - Production alerting rules

**Automatic Detection:**
The application automatically detects external monitoring and:
- Disables built-in Prometheus/Grafana containers
- Configures metrics endpoints for external scraping
- Provides configuration validation via `/monitoring/config` endpoint

**Testing External Integration:**
```bash
# Validate external monitoring setup
python test_external_monitoring.py

# Check configuration endpoint
curl http://your-app/monitoring/config
```

### Alerting Rules

```yaml
# alert-rules.yml
groups:
- name: video-transcriber.rules
  rules:
  - alert: HighErrorRate
    expr: rate(flask_http_request_exceptions_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High error rate detected
      description: "Error rate is {{ $value }} errors per second"

  - alert: DatabaseDown
    expr: up{job="postgres"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: Database is down
      description: PostgreSQL database is not responding

  - alert: HighMemoryUsage
    expr: (container_memory_working_set_bytes / container_spec_memory_limit_bytes) > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High memory usage
      description: "Memory usage is {{ $value }}%"
```

## 🔒 Security Hardening

### Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: video-transcriber-netpol
spec:
  podSelector:
    matchLabels:
      app: video-transcriber
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 5000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Pod Security Standards

```yaml
# pod-security-policy.yaml
apiVersion: v1
kind: Pod
metadata:
  name: video-transcriber
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    resources:
      limits:
        memory: "2Gi"
        cpu: "1000m"
      requests:
        memory: "1Gi"
        cpu: "500m"
```

## 📈 Performance Optimization

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: video-transcriber-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: video-transcriber
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Pod Autoscaler

```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: video-transcriber-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: video-transcriber
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: app
      maxAllowed:
        cpu: "2"
        memory: "4Gi"
      minAllowed:
        cpu: "100m"
        memory: "512Mi"
```

## 🔄 Backup and Recovery

### Database Backup Strategy

```bash
#!/bin/bash
# backup-database.sh
set -euo pipefail

NAMESPACE="video-transcriber-prod"
BACKUP_BUCKET="s3://your-backup-bucket"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create database dump
kubectl exec -n "$NAMESPACE" deployment/postgres -- \
  pg_dump -U postgres video_transcriber | \
  gzip > "backup_${TIMESTAMP}.sql.gz"

# Upload to S3
aws s3 cp "backup_${TIMESTAMP}.sql.gz" "$BACKUP_BUCKET/database/"

# Clean up local file
rm "backup_${TIMESTAMP}.sql.gz"

# Retain backups for 30 days
aws s3 ls "$BACKUP_BUCKET/database/" | \
  awk '$1 < "'$(date -d '30 days ago' '+%Y-%m-%d')'" {print $4}' | \
  xargs -I {} aws s3 rm "$BACKUP_BUCKET/database/{}"
```

### Persistent Volume Backup

```yaml
# velero-backup.yaml
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: video-transcriber-backup
spec:
  includedNamespaces:
  - video-transcriber-prod
  storageLocation: default
  volumeSnapshotLocations:
  - default
  ttl: 720h0m0s  # 30 days
```

## 🚨 Disaster Recovery

### Recovery Procedures

1. **Database Recovery:**
   ```bash
   # Restore from backup
   kubectl exec -i deployment/postgres -- \
     psql -U postgres -d video_transcriber < backup_TIMESTAMP.sql
   ```

2. **Volume Recovery:**
   ```bash
   # Restore using Velero
   velero restore create --from-backup video-transcriber-backup
   ```

3. **Application Recovery:**
   ```bash
   # Redeploy application
   helm rollback video-transcriber
   ```

### Health Checks

```bash
#!/bin/bash
# health-check.sh
NAMESPACE="video-transcriber-prod"

# Check pod health
kubectl get pods -n "$NAMESPACE" --field-selector=status.phase!=Running

# Check service endpoints
kubectl get endpoints -n "$NAMESPACE"

# Test application health
kubectl exec -n "$NAMESPACE" deployment/video-transcriber -- \
  curl -f http://localhost:5000/health

# Check database connectivity
kubectl exec -n "$NAMESPACE" deployment/postgres -- \
  pg_isready -U postgres
```

## 📋 Production Checklist

### Pre-Deployment

- [ ] Security scan completed
- [ ] Load testing performed
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] SSL certificates installed
- [ ] Database migrations tested
- [ ] Resource limits defined
- [ ] Network policies applied

### Post-Deployment

- [ ] Health checks passing
- [ ] Metrics collection working
- [ ] Logs aggregation configured
- [ ] Alerting rules tested
- [ ] Backup automation verified
- [ ] Performance baseline established
- [ ] Documentation updated
- [ ] Team training completed

### Maintenance Schedule

- **Daily:** Monitor system health and performance
- **Weekly:** Review logs and error patterns
- **Monthly:** Security updates and patches
- **Quarterly:** Capacity planning review
- **Annually:** Disaster recovery testing

## 🔗 Additional Resources

- [Kubernetes Production Best Practices](https://kubernetes.io/docs/setup/best-practices/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Prometheus Monitoring Guide](https://prometheus.io/docs/practices/naming/)
- [Grafana Dashboard Examples](https://grafana.com/grafana/dashboards/)
