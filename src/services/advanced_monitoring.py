"""
Advanced monitoring and alerting system for Video Transcriber
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil
from flask import Blueprint, jsonify, render_template

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import prometheus_client
    from prometheus_client import Counter, Gauge, Histogram, Info

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    metric: str
    operator: str  # 'gt', 'lt', 'eq'
    threshold: float
    duration: int  # seconds
    severity: str  # 'info', 'warning', 'critical'
    message: str


@dataclass
class Alert:
    """Active alert"""

    rule_name: str
    severity: str
    message: str
    timestamp: datetime
    value: float
    resolved: bool = False


class AdvancedMonitoringService:
    """Comprehensive monitoring and alerting service"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.metrics = {}
        self.alerts: List[Alert] = []
        self.alert_rules = self._init_default_rules()

        if PROMETHEUS_AVAILABLE:
            self._init_prometheus_metrics()

    def _init_default_rules(self) -> List[AlertRule]:
        """Initialize default alert rules"""
        return [
            AlertRule(
                name="high_cpu_usage",
                metric="cpu_percent",
                operator="gt",
                threshold=80.0,
                duration=300,  # 5 minutes
                severity="warning",
                message="High CPU usage detected: {value}%",
            ),
            AlertRule(
                name="high_memory_usage",
                metric="memory_percent",
                operator="gt",
                threshold=85.0,
                duration=300,
                severity="warning",
                message="High memory usage detected: {value}%",
            ),
            AlertRule(
                name="low_disk_space",
                metric="disk_percent",
                operator="gt",
                threshold=90.0,
                duration=60,
                severity="critical",
                message="Low disk space: {value}% used",
            ),
            AlertRule(
                name="high_transcription_failure_rate",
                metric="transcription_failure_rate",
                operator="gt",
                threshold=20.0,
                duration=600,  # 10 minutes
                severity="critical",
                message="High transcription failure rate: {value}%",
            ),
            AlertRule(
                name="long_processing_queue",
                metric="queue_length",
                operator="gt",
                threshold=10.0,
                duration=300,
                severity="warning",
                message="Long processing queue: {value} items",
            ),
        ]

    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        if not PROMETHEUS_AVAILABLE:
            return

        self.prom_metrics = {
            "transcription_requests": Counter(
                "transcription_requests_total",
                "Total transcription requests",
                ["status", "language"],
            ),
            "transcription_duration": Histogram(
                "transcription_duration_seconds",
                "Time spent on transcription",
                ["model_size", "language"],
            ),
            "active_sessions": Gauge(
                "active_sessions", "Number of active transcription sessions"
            ),
            "queue_length": Gauge(
                "processing_queue_length", "Number of items in processing queue"
            ),
            "system_cpu": Gauge("system_cpu_percent", "System CPU usage percentage"),
            "system_memory": Gauge(
                "system_memory_percent", "System memory usage percentage"
            ),
            "system_disk": Gauge("system_disk_percent", "System disk usage percentage"),
            "app_info": Info(
                "video_transcriber_info", "Video Transcriber application info"
            ),
        }

        # Set application info
        self.prom_metrics["app_info"].info(
            {
                "version": "2.0.0",
                "python_version": os.sys.version.split()[0],
                "environment": os.getenv("ENVIRONMENT", "development"),
            }
        )

    def collect_system_metrics(self) -> Dict[str, float]:
        """Collect system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024**3),
                "disk_total_gb": disk.total / (1024**3),
                "timestamp": time.time(),
            }

            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, "prom_metrics"):
                self.prom_metrics["system_cpu"].set(cpu_percent)
                self.prom_metrics["system_memory"].set(memory.percent)
                self.prom_metrics["system_disk"].set(disk.percent)

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}

    def collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics"""
        try:
            metrics = {
                "active_sessions": self._get_active_sessions_count(),
                "queue_length": self._get_queue_length(),
                "transcription_success_rate": self._get_transcription_success_rate(),
                "transcription_failure_rate": self._get_transcription_failure_rate(),
                "average_processing_time": self._get_average_processing_time(),
                "total_processed_today": self._get_total_processed_today(),
                "timestamp": time.time(),
            }

            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, "prom_metrics"):
                self.prom_metrics["active_sessions"].set(metrics["active_sessions"])
                self.prom_metrics["queue_length"].set(metrics["queue_length"])

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return {}

    def _get_active_sessions_count(self) -> int:
        """Get number of active transcription sessions"""
        try:
            if REDIS_AVAILABLE and self.redis_client:
                # Count active sessions in Redis
                pattern = "session:*:status"
                keys = self.redis_client.keys(pattern)
                active_count = 0
                for key in keys:
                    status = self.redis_client.get(key)
                    if status and status.decode() in ["processing", "uploading"]:
                        active_count += 1
                return active_count
            else:
                # Fallback to file system check
                results_dir = os.path.join(os.getcwd(), "results")
                if os.path.exists(results_dir):
                    return len(
                        [
                            d
                            for d in os.listdir(results_dir)
                            if os.path.isdir(os.path.join(results_dir, d))
                        ]
                    )
                return 0
        except Exception:
            return 0

    def _get_queue_length(self) -> int:
        """Get processing queue length"""
        try:
            if REDIS_AVAILABLE and self.redis_client:
                # Check Celery queue length
                return self.redis_client.llen("celery") or 0
            return 0
        except Exception:
            return 0

    def _get_transcription_success_rate(self) -> float:
        """Calculate transcription success rate"""
        try:
            if REDIS_AVAILABLE and self.redis_client:
                success_count = int(
                    self.redis_client.get("transcription:success:count") or 0
                )
                total_count = int(
                    self.redis_client.get("transcription:total:count") or 0
                )
                if total_count > 0:
                    return (success_count / total_count) * 100
            return 100.0
        except Exception:
            return 100.0

    def _get_transcription_failure_rate(self) -> float:
        """Calculate transcription failure rate"""
        return 100.0 - self._get_transcription_success_rate()

    def _get_average_processing_time(self) -> float:
        """Get average processing time in seconds"""
        try:
            if REDIS_AVAILABLE and self.redis_client:
                total_time = float(
                    self.redis_client.get("transcription:total:time") or 0
                )
                total_count = int(
                    self.redis_client.get("transcription:total:count") or 0
                )
                if total_count > 0:
                    return total_time / total_count
            return 0.0
        except Exception:
            return 0.0

    def _get_total_processed_today(self) -> int:
        """Get total transcriptions processed today"""
        try:
            if REDIS_AVAILABLE and self.redis_client:
                today = datetime.now().strftime("%Y-%m-%d")
                return int(self.redis_client.get(f"transcription:daily:{today}") or 0)
            return 0
        except Exception:
            return 0

    def check_alerts(self, metrics: Dict[str, Any]) -> List[Alert]:
        """Check metrics against alert rules"""
        new_alerts = []

        for rule in self.alert_rules:
            if rule.metric in metrics:
                value = metrics[rule.metric]

                if self._evaluate_rule(rule, value):
                    alert = Alert(
                        rule_name=rule.name,
                        severity=rule.severity,
                        message=rule.message.format(value=value),
                        timestamp=datetime.now(),
                        value=value,
                    )
                    new_alerts.append(alert)
                    logger.warning(f"Alert triggered: {alert.message}")

        return new_alerts

    def _evaluate_rule(self, rule: AlertRule, value: float) -> bool:
        """Evaluate if a metric value triggers an alert rule"""
        if rule.operator == "gt":
            return value > rule.threshold
        elif rule.operator == "lt":
            return value < rule.threshold
        elif rule.operator == "eq":
            return value == rule.threshold
        return False

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        system_metrics = self.collect_system_metrics()
        app_metrics = self.collect_application_metrics()

        # Determine overall health
        health_issues = []

        if system_metrics.get("cpu_percent", 0) > 90:
            health_issues.append("High CPU usage")
        if system_metrics.get("memory_percent", 0) > 95:
            health_issues.append("High memory usage")
        if system_metrics.get("disk_percent", 0) > 95:
            health_issues.append("Low disk space")
        if app_metrics.get("transcription_failure_rate", 0) > 50:
            health_issues.append("High failure rate")

        status = (
            "healthy"
            if not health_issues
            else "degraded"
            if len(health_issues) < 3
            else "unhealthy"
        )

        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "issues": health_issues,
            "system_metrics": system_metrics,
            "application_metrics": app_metrics,
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
        }

    def record_transcription_event(
        self,
        success: bool,
        duration: float,
        language: str = "unknown",
        model_size: str = "base",
    ):
        """Record a transcription event for metrics"""
        try:
            if REDIS_AVAILABLE and self.redis_client:
                # Update counters
                self.redis_client.incr("transcription:total:count")
                if success:
                    self.redis_client.incr("transcription:success:count")

                # Update timing
                total_time = float(
                    self.redis_client.get("transcription:total:time") or 0
                )
                self.redis_client.set("transcription:total:time", total_time + duration)

                # Update daily counter
                today = datetime.now().strftime("%Y-%m-%d")
                self.redis_client.incr(f"transcription:daily:{today}")

            # Update Prometheus metrics
            if PROMETHEUS_AVAILABLE and hasattr(self, "prom_metrics"):
                status = "success" if success else "failure"
                self.prom_metrics["transcription_requests"].labels(
                    status=status, language=language
                ).inc()

                if success:
                    self.prom_metrics["transcription_duration"].labels(
                        model_size=model_size, language=language
                    ).observe(duration)

        except Exception as e:
            logger.error(f"Failed to record transcription event: {e}")


# Create monitoring blueprint
monitoring_bp = Blueprint("monitoring", __name__, url_prefix="/monitoring")

# Global monitoring service instance
monitoring_service = None


def init_monitoring_service(redis_client=None):
    """Initialize the global monitoring service"""
    global monitoring_service
    monitoring_service = AdvancedMonitoringService(redis_client)


@monitoring_bp.route("/health")
def health_check():
    """Comprehensive health check endpoint"""
    if not monitoring_service:
        return jsonify({"error": "Monitoring not initialized"}), 503

    health_status = monitoring_service.get_health_status()

    status_code = 200
    if health_status["status"] == "degraded":
        status_code = 207  # Multi-status
    elif health_status["status"] == "unhealthy":
        status_code = 503  # Service unavailable

    return jsonify(health_status), status_code


@monitoring_bp.route("/metrics")
def metrics_endpoint():
    """Prometheus metrics endpoint"""
    if PROMETHEUS_AVAILABLE:
        return prometheus_client.generate_latest(), 200, {"Content-Type": "text/plain"}
    else:
        return jsonify({"error": "Prometheus not available"}), 503


@monitoring_bp.route("/dashboard")
def monitoring_dashboard():
    """Monitoring dashboard"""
    if not monitoring_service:
        return "Monitoring not initialized", 503

    health_status = monitoring_service.get_health_status()
    return render_template("monitoring_dashboard.html", health=health_status)


@monitoring_bp.route("/alerts")
def get_alerts():
    """Get current alerts"""
    if not monitoring_service:
        return jsonify({"error": "Monitoring not initialized"}), 503

    active_alerts = [
        {
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "value": alert.value,
            "resolved": alert.resolved,
        }
        for alert in monitoring_service.alerts
        if not alert.resolved
    ]

    return jsonify({"alerts": active_alerts, "count": len(active_alerts)})
