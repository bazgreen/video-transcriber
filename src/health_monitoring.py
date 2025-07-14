"""
Health monitoring system for Video Transcriber application.
Provides comprehensive health checks and monitoring endpoints.
"""

import os
import subprocess
import time
from datetime import datetime
from typing import Any, Dict

import psutil
from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


class HealthMonitor:
    """Comprehensive health monitoring system."""

    def __init__(self, app=None):
        self.app = app
        self.checks = {
            "database": self.check_database,
            "disk_space": self.check_disk_space,
            "memory": self.check_memory,
            "cpu": self.check_cpu,
            "ffmpeg": self.check_ffmpeg,
            "whisper": self.check_whisper_models,
            "log_files": self.check_log_files,
        }

    def init_app(self, app):
        """Initialize health monitoring with Flask app."""
        self.app = app
        app.register_blueprint(health_bp)

    def run_health_checks(self, detailed: bool = False) -> Dict[str, Any]:
        """Run comprehensive health checks."""

        start_time = time.time()
        results = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "summary": {
                "total_checks": len(self.checks),
                "passed": 0,
                "failed": 0,
                "warnings": 0,
            },
        }

        # Run all health checks
        for check_name, check_function in self.checks.items():
            try:
                check_result = check_function()
                results["checks"][check_name] = check_result

                # Update summary
                if check_result["status"] == "healthy":
                    results["summary"]["passed"] += 1
                elif check_result["status"] == "warning":
                    results["summary"]["warnings"] += 1
                else:
                    results["summary"]["failed"] += 1
                    results["status"] = "unhealthy"

            except Exception as e:
                results["checks"][check_name] = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                results["summary"]["failed"] += 1
                results["status"] = "unhealthy"

        # Calculate overall health status
        if results["summary"]["failed"] > 0:
            results["status"] = "unhealthy"
        elif results["summary"]["warnings"] > 0:
            results["status"] = "degraded"

        results["duration"] = time.time() - start_time

        # Add detailed system information if requested
        if detailed:
            results["system_info"] = self.get_system_info()

        return results

    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            # Try to import and check database
            from main import app

            with app.app_context():
                from src.database import db

                db.session.execute("SELECT 1")

            return {"status": "healthy", "message": "Database connection successful"}

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "error": str(e),
            }

    def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            # Check main application directory
            app_disk = psutil.disk_usage("/")
            app_free_gb = app_disk.free / (1024**3)
            app_percent_used = (app_disk.used / app_disk.total) * 100

            # Check uploads directory
            uploads_path = os.path.join(os.getcwd(), "uploads")
            if os.path.exists(uploads_path):
                uploads_disk = psutil.disk_usage(uploads_path)
                uploads_free_gb = uploads_disk.free / (1024**3)
            else:
                uploads_free_gb = app_free_gb

            status = "healthy"
            message = "Sufficient disk space available"

            if app_free_gb < 1.0:  # Less than 1GB free
                status = "unhealthy"
                message = "Critical: Low disk space"
            elif app_free_gb < 5.0:  # Less than 5GB free
                status = "warning"
                message = "Warning: Low disk space"

            return {
                "status": status,
                "message": message,
                "free_space_gb": round(app_free_gb, 2),
                "percent_used": round(app_percent_used, 1),
                "uploads_free_gb": round(uploads_free_gb, 2),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Disk space check failed: {str(e)}",
                "error": str(e),
            }

    def check_memory(self) -> Dict[str, Any]:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()

            status = "healthy"
            message = "Memory usage normal"

            if memory.percent > 90:
                status = "unhealthy"
                message = "Critical: High memory usage"
            elif memory.percent > 80:
                status = "warning"
                message = "Warning: High memory usage"

            return {
                "status": status,
                "message": message,
                "memory_percent": round(memory.percent, 1),
                "memory_available_gb": round(memory.available / (1024**3), 2),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Memory check failed: {str(e)}",
                "error": str(e),
            }

    def check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            # Get CPU usage over 1 second interval
            cpu_percent = psutil.cpu_percent(interval=1)

            status = "healthy"
            message = "CPU usage normal"

            if cpu_percent > 95:
                status = "unhealthy"
                message = "Critical: High CPU usage"
            elif cpu_percent > 85:
                status = "warning"
                message = "Warning: High CPU usage"

            return {
                "status": status,
                "message": message,
                "cpu_percent": round(cpu_percent, 1),
                "cpu_count": psutil.cpu_count(),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"CPU check failed: {str(e)}",
                "error": str(e),
            }

    def check_ffmpeg(self) -> Dict[str, Any]:
        """Check FFmpeg availability and functionality."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                version_line = result.stdout.split("\n")[0]
                return {
                    "status": "healthy",
                    "message": "FFmpeg available",
                    "version": version_line,
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "FFmpeg not working properly",
                    "error": result.stderr,
                }

        except subprocess.TimeoutExpired:
            return {"status": "unhealthy", "message": "FFmpeg check timed out"}
        except FileNotFoundError:
            return {"status": "unhealthy", "message": "FFmpeg not found"}
        except Exception as e:
            return {
                "status": "error",
                "message": f"FFmpeg check failed: {str(e)}",
                "error": str(e),
            }

    def check_whisper_models(self) -> Dict[str, Any]:
        """Check Whisper model availability."""
        try:
            import whisper

            # Check available models
            available_models = whisper.available_models()

            # Try to load a small model to verify functionality
            try:
                whisper.load_model("tiny")
                model_check = True
            except Exception:
                model_check = False

            return {
                "status": "healthy" if model_check else "warning",
                "message": (
                    "Whisper models available"
                    if model_check
                    else "Whisper models not fully functional"
                ),
                "available_models": list(available_models),
                "test_load_success": model_check,
            }

        except ImportError:
            return {"status": "unhealthy", "message": "Whisper not installed"}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Whisper check failed: {str(e)}",
                "error": str(e),
            }

    def check_log_files(self) -> Dict[str, Any]:
        """Check log file status and recent errors."""
        try:
            log_dir = os.path.join(os.getcwd(), "logs")

            if not os.path.exists(log_dir):
                return {"status": "warning", "message": "Log directory not found"}

            # Check log files
            log_files = []
            total_size = 0
            recent_errors = 0

            for filename in os.listdir(log_dir):
                if filename.endswith(".log"):
                    filepath = os.path.join(log_dir, filename)
                    stat = os.stat(filepath)
                    total_size += stat.st_size

                    # Check for recent errors (last 1 hour)
                    if time.time() - stat.st_mtime < 3600:
                        try:
                            with open(filepath, "r") as f:
                                content = f.read()
                                recent_errors += content.lower().count("error")
                        except (IOError, UnicodeDecodeError):
                            pass

                    log_files.append(
                        {
                            "filename": filename,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                        }
                    )

            status = "healthy"
            message = "Log files normal"

            if recent_errors > 10:
                status = "warning"
                message = f"High error count in recent logs: {recent_errors}"

            return {
                "status": status,
                "message": message,
                "log_files": log_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "recent_errors": recent_errors,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Log file check failed: {str(e)}",
                "error": str(e),
            }

    def get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information."""
        try:
            import platform

            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "uptime": time.time() - psutil.boot_time(),
                "process_count": len(psutil.pids()),
            }
        except Exception as e:
            return {"error": str(e)}


# Health monitoring instance
health_monitor = HealthMonitor()


# Flask routes for health monitoring
@health_bp.route("/health")
def health_check():
    """Basic health check endpoint."""
    results = health_monitor.run_health_checks(detailed=False)

    status_code = 200 if results["status"] == "healthy" else 503
    return jsonify(results), status_code


@health_bp.route("/health/detailed")
def detailed_health_check():
    """Detailed health check with system information."""
    results = health_monitor.run_health_checks(detailed=True)

    status_code = 200 if results["status"] == "healthy" else 503
    return jsonify(results), status_code


@health_bp.route("/health/live")
def liveness_probe():
    """Kubernetes liveness probe endpoint."""
    try:
        # Basic application responsiveness check
        return (
            jsonify({"status": "alive", "timestamp": datetime.utcnow().isoformat()}),
            200,
        )
    except Exception:
        return (
            jsonify({"status": "dead", "timestamp": datetime.utcnow().isoformat()}),
            503,
        )


@health_bp.route("/health/ready")
def readiness_probe():
    """Kubernetes readiness probe endpoint."""
    # Check critical dependencies
    critical_checks = ["database", "ffmpeg"]
    results = {}
    ready = True

    for check_name in critical_checks:
        check_function = health_monitor.checks[check_name]
        try:
            result = check_function()
            results[check_name] = result
            if result["status"] != "healthy":
                ready = False
        except Exception as e:
            results[check_name] = {"status": "error", "error": str(e)}
            ready = False

    response = {
        "status": "ready" if ready else "not_ready",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": results,
    }

    return jsonify(response), 200 if ready else 503


@health_bp.route("/metrics")
def metrics_endpoint():
    """Prometheus-compatible metrics endpoint."""
    results = health_monitor.run_health_checks(detailed=True)

    # Convert health check results to Prometheus format
    metrics = []

    # Application health metrics
    metrics.append(f'app_health_status{{status="{results["status"]}"}} 1')
    metrics.append(f'app_health_checks_total {results["summary"]["total_checks"]}')
    metrics.append(f'app_health_checks_passed {results["summary"]["passed"]}')
    metrics.append(f'app_health_checks_failed {results["summary"]["failed"]}')
    metrics.append(f'app_health_checks_warnings {results["summary"]["warnings"]}')

    # System metrics
    if "system_info" in results:
        system_info = results["system_info"]
        if "uptime" in system_info:
            metrics.append(f'app_uptime_seconds {system_info["uptime"]}')
        if "process_count" in system_info:
            metrics.append(f'app_process_count {system_info["process_count"]}')

    # Individual check metrics
    for check_name, check_result in results["checks"].items():
        status_value = 1 if check_result["status"] == "healthy" else 0
        metrics.append(f'app_check_status{{check="{check_name}"}} {status_value}')

    return "\n".join(metrics), 200, {"Content-Type": "text/plain"}
