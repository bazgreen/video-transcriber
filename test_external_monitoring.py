#!/usr/bin/env python3
"""
Test script for external monitoring integration.
Validates that the Video Transcriber application properly integrates with external Prometheus/Grafana.
"""

import json
import os
import sys
import time
from typing import Any, Dict, Optional

import requests


def test_external_monitoring_detection():
    """Test that the application detects external monitoring configuration."""
    print("🔍 Testing external monitoring detection...")

    # Test without external monitoring
    os.environ.pop("EXTERNAL_MONITORING", None)
    os.environ.pop("PROMETHEUS_URL", None)
    os.environ.pop("GRAFANA_URL", None)

    try:
        response = requests.get("http://localhost:5001/monitoring/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            assert not config.get(
                "external_monitoring", False
            ), "Should not detect external monitoring"
            print("✅ Internal monitoring mode detected correctly")
        else:
            print(f"❌ Failed to get monitoring config: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to application: {e}")
        return False

    # Test with external monitoring
    os.environ["EXTERNAL_MONITORING"] = "true"
    os.environ["PROMETHEUS_URL"] = "http://test-prometheus:9090"
    os.environ["GRAFANA_URL"] = "http://test-grafana:3000"

    # Wait a moment for config to reload
    time.sleep(2)

    try:
        response = requests.get("http://localhost:5001/monitoring/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            assert config.get(
                "external_monitoring", False
            ), "Should detect external monitoring"
            assert config.get("prometheus_url") == "http://test-prometheus:9090"
            assert config.get("grafana_url") == "http://test-grafana:3000"
            print("✅ External monitoring mode detected correctly")
        else:
            print(
                f"❌ Failed to get monitoring config with external setup: {response.status_code}"
            )
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to application with external config: {e}")
        return False

    return True


def test_metrics_endpoint():
    """Test that metrics endpoint works correctly."""
    print("📊 Testing metrics endpoint...")

    try:
        response = requests.get("http://localhost:5001/monitoring/metrics", timeout=10)
        if response.status_code == 200:
            metrics_text = response.text

            # Check for key metrics
            expected_metrics = [
                "http_requests_total",
                "http_request_duration_seconds",
                "transcription_jobs_total",
                "process_resident_memory_bytes",
                "process_cpu_seconds_total",
            ]

            for metric in expected_metrics:
                if metric in metrics_text:
                    print(f"✅ Found metric: {metric}")
                else:
                    print(f"❌ Missing metric: {metric}")
                    return False

            print("✅ All expected metrics found")
            return True
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access metrics endpoint: {e}")
        return False


def test_health_endpoint():
    """Test that health endpoint works correctly."""
    print("❤️ Testing health endpoint...")

    try:
        response = requests.get("http://localhost:5001/monitoring/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()

            required_checks = ["status", "timestamp", "checks"]
            for check in required_checks:
                if check not in health_data:
                    print(f"❌ Missing health check field: {check}")
                    return False

            if health_data["status"] == "healthy":
                print("✅ Application reports healthy status")
                return True
            else:
                print(f"❌ Application reports unhealthy: {health_data['status']}")
                return False
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access health endpoint: {e}")
        return False


def validate_prometheus_config():
    """Validate the Prometheus configuration file."""
    print("⚙️ Validating Prometheus configuration...")

    config_path = "external-monitoring/prometheus-config.yml"
    if not os.path.exists(config_path):
        print(f"❌ Prometheus config file not found: {config_path}")
        return False

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Check for required sections
        if "scrape_configs" not in config:
            print("❌ Missing scrape_configs in Prometheus config")
            return False

        # Check for Video Transcriber job
        jobs = [job.get("job_name") for job in config["scrape_configs"]]
        if "video-transcriber-app" not in jobs:
            print("❌ Missing video-transcriber-app job in Prometheus config")
            return False

        print("✅ Prometheus configuration is valid")
        return True
    except Exception as e:
        print(f"❌ Error validating Prometheus config: {e}")
        return False


def validate_grafana_dashboard():
    """Validate the Grafana dashboard configuration."""
    print("📈 Validating Grafana dashboard...")

    dashboard_path = "external-monitoring/grafana-dashboard.json"
    if not os.path.exists(dashboard_path):
        print(f"❌ Grafana dashboard file not found: {dashboard_path}")
        return False

    try:
        with open(dashboard_path, "r") as f:
            dashboard = json.load(f)

        # Check for required sections
        if "dashboard" not in dashboard:
            print("❌ Missing dashboard section in Grafana config")
            return False

        dashboard_config = dashboard["dashboard"]
        if "panels" not in dashboard_config:
            print("❌ Missing panels in Grafana dashboard")
            return False

        if len(dashboard_config["panels"]) < 5:
            print("❌ Insufficient panels in Grafana dashboard")
            return False

        print(
            f"✅ Grafana dashboard is valid with {len(dashboard_config['panels'])} panels"
        )
        return True
    except Exception as e:
        print(f"❌ Error validating Grafana dashboard: {e}")
        return False


def main():
    """Run all external monitoring integration tests."""
    print("🚀 Starting external monitoring integration tests...\n")

    tests = [
        ("External Monitoring Detection", test_external_monitoring_detection),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("Health Endpoint", test_health_endpoint),
        ("Prometheus Configuration", validate_prometheus_config),
        ("Grafana Dashboard", validate_grafana_dashboard),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print("=" * 50)

        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All external monitoring integration tests passed!")
        return 0
    else:
        print("💥 Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    # Install required dependencies if missing
    try:
        import yaml
    except ImportError:
        print("Installing PyYAML for configuration validation...")
        os.system("pip install PyYAML")
        import yaml

    exit_code = main()
    sys.exit(exit_code)
