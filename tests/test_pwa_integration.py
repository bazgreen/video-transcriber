"""
Integration tests for PWA functionality in the complete application
"""

import json
import os
import tempfile
import time
from unittest.mock import MagicMock, patch

import requests


class TestPWAIntegration:
    """Test PWA integration with running app"""

    def setup_method(self):
        """Setup for each test"""
        self.base_url = "http://localhost:5001"
        self.app_running = self._check_app_running()

    def _check_app_running(self):
        """Check if the app is running"""
        try:
            response = requests.get(f"{self.base_url}/api/pwa/status", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def test_manifest_accessibility(self):
        """Test that manifest is accessible and valid"""
        if not self.app_running:
            print("⚠️  App not running, skipping integration test")
            return

        response = requests.get(f"{self.base_url}/manifest.json")
        assert response.status_code == 200
        assert (
            response.headers["content-type"]
            == "application/manifest+json; charset=utf-8"
        )

        manifest = response.json()
        required_fields = ["name", "short_name", "start_url", "display", "icons"]
        for field in required_fields:
            assert field in manifest, f"Required field '{field}' missing from manifest"

        # Validate icons structure
        assert len(manifest["icons"]) > 0, "Manifest must have at least one icon"
        for icon in manifest["icons"]:
            assert "src" in icon
            assert "sizes" in icon
            assert "type" in icon

    def test_service_worker_accessibility(self):
        """Test that service worker is accessible with correct headers"""
        if not self.app_running:
            print("⚠️  App not running, skipping integration test")
            return

        response = requests.get(f"{self.base_url}/sw.js")
        assert response.status_code == 200
        assert (
            response.headers["content-type"] == "application/javascript; charset=utf-8"
        )
        assert response.headers["service-worker-allowed"] == "/"
        assert response.headers["cache-control"] == "no-cache"

        # Validate service worker content
        sw_content = response.text
        required_sw_features = [
            "addEventListener",
            "install",
            "activate",
            "fetch",
            "caches",
            "CACHE_NAME",
        ]

        for feature in required_sw_features:
            assert (
                feature in sw_content
            ), f"Service worker missing required feature: {feature}"

    def test_pwa_status_endpoint(self):
        """Test PWA status endpoint functionality"""
        if not self.app_running:
            print("⚠️  App not running, skipping integration test")
            return

        response = requests.get(f"{self.base_url}/api/pwa/status")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["pwa_enabled"] is True
        assert "capabilities" in data
        assert "version" in data
        assert "last_updated" in data

        # Test capabilities
        capabilities = data["capabilities"]
        expected_capabilities = [
            "service_worker",
            "offline_support",
            "background_sync",
            "push_notifications",
            "install_prompt",
        ]

        for cap in expected_capabilities:
            assert cap in capabilities

    def test_offline_page_accessibility(self):
        """Test offline page is accessible"""
        if not self.app_running:
            print("⚠️  App not running, skipping integration test")
            return

        response = requests.get(f"{self.base_url}/offline")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

        # Check for key offline page elements
        content = response.text
        offline_indicators = ["offline", "connection", "retry", "Video Transcriber"]

        for indicator in offline_indicators:
            assert indicator.lower() in content.lower()

    def test_pwa_api_endpoints(self):
        """Test all PWA API endpoints are functional"""
        if not self.app_running:
            print("⚠️  App not running, skipping integration test")
            return

        endpoints = [
            ("/api/pwa/status", "GET"),
            ("/api/pwa/cache-stats", "GET"),
            ("/api/push/vapid-key", "GET"),
            ("/api/pwa/update-check", "GET"),
            ("/api/pwa/offline-queue", "GET"),
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = requests.get(f"{self.base_url}{endpoint}")
            else:
                response = requests.post(f"{self.base_url}{endpoint}")

            assert response.status_code == 200, f"Endpoint {endpoint} failed"
            data = response.json()
            assert (
                data.get("success") is True
            ), f"Endpoint {endpoint} returned error: {data}"

    def test_push_subscription_flow(self):
        """Test push notification subscription flow"""
        if not self.app_running:
            print("⚠️  App not running, skipping integration test")
            return

        # Get VAPID key
        response = requests.get(f"{self.base_url}/api/push/vapid-key")
        assert response.status_code == 200
        vapid_data = response.json()
        assert vapid_data["success"] is True
        assert "publicKey" in vapid_data

        # Test subscription
        subscription_data = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
            "keys": {"p256dh": "test-p256dh-key", "auth": "test-auth-key"},
        }

        response = requests.post(
            f"{self.base_url}/api/push/subscribe",
            json=subscription_data,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        sub_data = response.json()
        assert sub_data["success"] is True

        # Test unsubscription
        unsub_data = {"endpoint": subscription_data["endpoint"]}
        response = requests.post(
            f"{self.base_url}/api/push/unsubscribe",
            json=unsub_data,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        unsub_result = response.json()
        assert unsub_result["success"] is True

    def test_offline_queue_management(self):
        """Test offline queue functionality"""
        if not self.app_running:
            print("⚠️  App not running, skipping integration test")
            return

        # Get initial queue state
        response = requests.get(f"{self.base_url}/api/pwa/offline-queue")
        assert response.status_code == 200
        initial_data = response.json()
        assert initial_data["success"] is True
        assert "queue" in initial_data

        # Add item to queue
        queue_item = {
            "filename": "test-video.mp4",
            "action": "transcribe",
            "timestamp": time.time(),
            "metadata": {"duration": 120, "size": 1024000},
        }

        response = requests.post(
            f"{self.base_url}/api/pwa/offline-queue",
            json=queue_item,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        add_data = response.json()
        assert add_data["success"] is True
        assert "queue_id" in add_data

    def test_install_stats_tracking(self):
        """Test PWA installation statistics tracking"""
        if not self.app_running:
            print("⚠️  App not running, skipping integration test")
            return

        events = ["prompt_shown", "install_accepted", "install_dismissed"]

        for event_type in events:
            event_data = {
                "event_type": event_type,
                "timestamp": time.time(),
                "user_agent": "Mozilla/5.0 (Test Browser)",
            }

            response = requests.post(
                f"{self.base_url}/api/pwa/install-stats",
                json=event_data,
                headers={"Content-Type": "application/json"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["event_type"] == event_type

    def test_cache_management(self):
        """Test cache management functionality"""
        if not self.app_running:
            print("⚠️  App not running, skipping integration test")
            return

        # Get cache stats
        response = requests.get(f"{self.base_url}/api/pwa/cache-stats")
        assert response.status_code == 200
        stats_data = response.json()
        assert stats_data["success"] is True
        assert "stats" in stats_data

        stats = stats_data["stats"]
        required_stats = [
            "cache_version",
            "static_files_cached",
            "dynamic_content_cached",
            "estimated_storage_mb",
            "last_cache_update",
        ]

        for stat in required_stats:
            assert stat in stats

        # Test cache clearing
        response = requests.post(f"{self.base_url}/api/pwa/clear-cache")
        assert response.status_code == 200
        clear_data = response.json()
        assert clear_data["success"] is True


class TestPWAFileValidation:
    """Test PWA file content validation"""

    def setup_method(self):
        """Setup test paths"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.static_dir = os.path.join(self.base_dir, "data", "static")
        self.templates_dir = os.path.join(self.base_dir, "data", "templates")

    def test_manifest_json_structure(self):
        """Test manifest.json has correct structure"""
        manifest_path = os.path.join(self.static_dir, "manifest.json")
        assert os.path.exists(manifest_path), "manifest.json not found"

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # Required PWA manifest fields
        required_fields = [
            "name",
            "short_name",
            "start_url",
            "display",
            "theme_color",
            "background_color",
            "icons",
        ]

        for field in required_fields:
            assert field in manifest, f"Required manifest field missing: {field}"

        # Validate icons
        assert len(manifest["icons"]) >= 2, "Manifest should have multiple icon sizes"
        for icon in manifest["icons"]:
            assert "src" in icon
            assert "sizes" in icon
            assert "type" in icon
            assert icon["type"] == "image/png"

        # Validate display mode
        valid_displays = ["fullscreen", "standalone", "minimal-ui", "browser"]
        assert manifest["display"] in valid_displays

    def test_service_worker_content(self):
        """Test service worker has required functionality"""
        sw_path = os.path.join(self.static_dir, "sw.js")
        assert os.path.exists(sw_path), "sw.js not found"

        with open(sw_path, "r") as f:
            sw_content = f.read()

        # Required service worker features
        required_features = [
            "addEventListener",
            "install",
            "activate",
            "fetch",
            "caches",
            "CACHE_NAME",
            "IndexedDB",
            "sync",
        ]

        for feature in required_features:
            assert feature in sw_content, f"Service worker missing: {feature}"

        # Check for proper cache strategies
        cache_strategies = ["cache.match", "cache.put", "fetch("]
        for strategy in cache_strategies:
            assert (
                strategy in sw_content
            ), f"Service worker missing cache strategy: {strategy}"

    def test_pwa_js_library(self):
        """Test PWA JavaScript library"""
        pwa_js_path = os.path.join(self.static_dir, "js", "pwa.js")
        assert os.path.exists(pwa_js_path), "pwa.js not found"

        with open(pwa_js_path, "r") as f:
            pwa_content = f.read()

        # Required PWA client features
        required_features = [
            "VideoTranscriberPWA",
            "registerServiceWorker",
            "setupInstallPrompt",
            "IndexedDB",
            "offline",
        ]

        for feature in required_features:
            assert feature in pwa_content, f"PWA library missing: {feature}"

    def test_pwa_css_styles(self):
        """Test PWA CSS styles"""
        pwa_css_path = os.path.join(self.static_dir, "css", "pwa.css")
        assert os.path.exists(pwa_css_path), "pwa.css not found"

        with open(pwa_css_path, "r") as f:
            css_content = f.read()

        # Required PWA styles
        required_styles = [
            "install-banner",
            "offline-indicator",
            "touch",
            "safe-area",
            "@media",
            "standalone",
        ]

        for style in required_styles:
            assert style in css_content, f"PWA CSS missing: {style}"

    def test_offline_template(self):
        """Test offline template structure"""
        offline_path = os.path.join(self.templates_dir, "offline.html")
        assert os.path.exists(offline_path), "offline.html not found"

        with open(offline_path, "r") as f:
            template_content = f.read()

        # Required offline page elements
        required_elements = [
            "offline",
            "retry",
            "navigator.onLine",
            "connection",
            "Video Transcriber",
        ]

        for element in required_elements:
            assert element in template_content, f"Offline template missing: {element}"


def run_integration_tests():
    """Run all PWA integration tests"""
    print("🧪 Starting PWA Integration Tests\n")

    # File validation tests
    print("📁 Testing PWA file validation...")
    file_validator = TestPWAFileValidation()
    file_validator.setup_method()

    try:
        file_validator.test_manifest_json_structure()
        print("✅ Manifest structure valid")
    except Exception as e:
        print(f"❌ Manifest validation failed: {e}")

    try:
        file_validator.test_service_worker_content()
        print("✅ Service worker content valid")
    except Exception as e:
        print(f"❌ Service worker validation failed: {e}")

    try:
        file_validator.test_pwa_js_library()
        print("✅ PWA JavaScript library valid")
    except Exception as e:
        print(f"❌ PWA library validation failed: {e}")

    try:
        file_validator.test_pwa_css_styles()
        print("✅ PWA CSS styles valid")
    except Exception as e:
        print(f"❌ PWA CSS validation failed: {e}")

    try:
        file_validator.test_offline_template()
        print("✅ Offline template valid")
    except Exception as e:
        print(f"❌ Offline template validation failed: {e}")

    # Integration tests
    print("\n🌐 Testing PWA integration...")
    integration_tester = TestPWAIntegration()
    integration_tester.setup_method()

    if not integration_tester.app_running:
        print("⚠️  Application not running. Start with: python main.py")
        print("   Integration tests will be skipped.")
        return

    test_methods = [
        ("Manifest accessibility", integration_tester.test_manifest_accessibility),
        (
            "Service worker accessibility",
            integration_tester.test_service_worker_accessibility,
        ),
        ("PWA status endpoint", integration_tester.test_pwa_status_endpoint),
        (
            "Offline page accessibility",
            integration_tester.test_offline_page_accessibility,
        ),
        ("PWA API endpoints", integration_tester.test_pwa_api_endpoints),
        ("Push subscription flow", integration_tester.test_push_subscription_flow),
        ("Offline queue management", integration_tester.test_offline_queue_management),
        ("Install stats tracking", integration_tester.test_install_stats_tracking),
        ("Cache management", integration_tester.test_cache_management),
    ]

    passed = 0
    total = len(test_methods)

    for test_name, test_method in test_methods:
        try:
            test_method()
            print(f"✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {e}")

    print(f"\n🧪 Integration Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All PWA integration tests passed!")
    else:
        print(f"⚠️  {total - passed} tests failed. Please review and fix issues.")


if __name__ == "__main__":
    run_integration_tests()
