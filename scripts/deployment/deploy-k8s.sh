#!/bin/bash
set -euo pipefail

# Video Transcriber - Kubernetes Deployment Script
# This script deploys the video transcriber to a Kubernetes cluster

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="${NAMESPACE:-video-transcriber}"
ENVIRONMENT="${ENVIRONMENT:-development}"
HELM_RELEASE="${HELM_RELEASE:-video-transcriber}"

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

# Check if kubectl is available and configured
check_kubectl() {
    log "Checking kubectl availability..."
    if ! command -v kubectl >/dev/null 2>&1; then
        error "kubectl is not installed. Please install kubectl and try again."
        exit 1
    fi

    if ! kubectl cluster-info >/dev/null 2>&1; then
        error "kubectl is not configured or cluster is not accessible."
        exit 1
    fi

    success "kubectl is available and cluster is accessible"
}

# Check if Helm is available
check_helm() {
    log "Checking Helm availability..."
    if ! command -v helm >/dev/null 2>&1; then
        warning "Helm is not installed. Using kubectl for deployment."
        return 1
    fi
    success "Helm is available"
    return 0
}

# Create namespace
create_namespace() {
    log "Creating namespace: $NAMESPACE"

    if kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        log "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        success "Namespace $NAMESPACE created"
    fi
}

# Deploy using kubectl
deploy_kubectl() {
    log "Deploying using kubectl..."

    # Apply configurations in order
    local files=(
        "k8s/storage.yaml"
        "k8s/database.yaml"
        "k8s/monitoring.yaml"
        "k8s/workers.yaml"
        "k8s/deployment.yaml"
    )

    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            log "Applying $file..."
            kubectl apply -f "$file" -n "$NAMESPACE"
        else
            warning "File $file not found, skipping..."
        fi
    done

    success "Kubectl deployment completed"
}

# Deploy using Helm
deploy_helm() {
    log "Deploying using Helm..."

    local helm_dir="helm/video-transcriber"

    if [[ ! -d "$helm_dir" ]]; then
        error "Helm chart directory not found: $helm_dir"
        return 1
    fi

    # Install or upgrade the Helm release
    helm upgrade --install "$HELM_RELEASE" "$helm_dir" \
        --namespace "$NAMESPACE" \
        --create-namespace \
        --set environment="$ENVIRONMENT" \
        --wait \
        --timeout=10m

    success "Helm deployment completed"
}

# Wait for deployments to be ready
wait_for_deployments() {
    log "Waiting for deployments to be ready..."

    local deployments=(
        "postgres"
        "redis"
        "video-transcriber"
        "celery-worker"
        "celery-beat"
    )

    for deployment in "${deployments[@]}"; do
        log "Waiting for deployment: $deployment"
        if kubectl wait --for=condition=available --timeout=300s deployment/"$deployment" -n "$NAMESPACE" >/dev/null 2>&1; then
            success "$deployment is ready"
        else
            warning "$deployment may not be ready yet"
        fi
    done
}

# Check service health
check_service_health() {
    log "Checking service health..."

    # Get the service endpoint
    local service_name="video-transcriber-service"
    local service_port="80"

    # Port forward to test health endpoint
    log "Port forwarding to test health endpoint..."
    kubectl port-forward -n "$NAMESPACE" "svc/$service_name" 8080:$service_port &
    local port_forward_pid=$!

    # Wait a bit for port forward to establish
    sleep 5

    # Test health endpoint
    local health_check=""
    for i in {1..10}; do
        if health_check=$(curl -s http://localhost:8080/health 2>/dev/null); then
            success "Application health check passed"
            break
        else
            log "Waiting for application to be ready... (attempt $i/10)"
            sleep 10
        fi
    done

    # Clean up port forward
    kill $port_forward_pid 2>/dev/null || true

    if [[ -z "$health_check" ]]; then
        warning "Health check failed, but deployment may still be starting"
        return 1
    fi

    return 0
}

# Show deployment information
show_deployment_info() {
    log "Deployment Information:"
    echo ""
    echo "📦 Namespace: $NAMESPACE"
    echo "🌍 Environment: $ENVIRONMENT"
    echo ""

    # Show pod status
    echo "🔍 Pod Status:"
    kubectl get pods -n "$NAMESPACE" -o wide
    echo ""

    # Show service information
    echo "🌐 Services:"
    kubectl get services -n "$NAMESPACE"
    echo ""

    # Show ingress information
    echo "🚀 Ingress:"
    kubectl get ingress -n "$NAMESPACE" 2>/dev/null || echo "No ingress configured"
    echo ""

    # Show useful commands
    echo "🔧 Useful Commands:"
    echo "   kubectl get pods -n $NAMESPACE                    # View pods"
    echo "   kubectl logs -f deployment/video-transcriber -n $NAMESPACE  # View app logs"
    echo "   kubectl port-forward svc/video-transcriber-service 8080:80 -n $NAMESPACE  # Access app locally"
    echo "   kubectl port-forward svc/grafana 3000:3000 -n $NAMESPACE  # Access Grafana"
    echo "   kubectl delete namespace $NAMESPACE                # Clean up deployment"
    echo ""
}

# Clean up deployment
cleanup() {
    log "Cleaning up deployment..."

    if [[ "${1:-}" == "--confirm" ]]; then
        kubectl delete namespace "$NAMESPACE"
        success "Namespace $NAMESPACE deleted"
    else
        echo "To clean up the deployment, run:"
        echo "kubectl delete namespace $NAMESPACE"
        echo ""
        echo "Or run this script with: $0 cleanup --confirm"
    fi
}

# Main deployment function
deploy() {
    log "Starting Kubernetes deployment..."

    check_kubectl
    create_namespace

    # Try Helm first, fall back to kubectl
    if check_helm; then
        if ! deploy_helm; then
            warning "Helm deployment failed, falling back to kubectl"
            deploy_kubectl
        fi
    else
        deploy_kubectl
    fi

    wait_for_deployments

    if check_service_health; then
        success "Deployment completed successfully!"
    else
        warning "Deployment completed but health check failed"
    fi

    show_deployment_info
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "cleanup")
        cleanup "${2:-}"
        ;;
    "status")
        show_deployment_info
        ;;
    "health")
        check_service_health
        ;;
    *)
        echo "Usage: $0 {deploy|cleanup|status|health}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the application to Kubernetes"
        echo "  cleanup  - Remove the deployment from Kubernetes"
        echo "  status   - Show deployment status"
        echo "  health   - Check application health"
        echo ""
        echo "Environment Variables:"
        echo "  NAMESPACE    - Kubernetes namespace (default: video-transcriber)"
        echo "  ENVIRONMENT  - Deployment environment (default: development)"
        echo "  HELM_RELEASE - Helm release name (default: video-transcriber)"
        exit 1
        ;;
esac
