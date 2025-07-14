"""
Comprehensive tests for PWA (Progressive Web App) functionality
Tests all PWA components including manifest, service worker, routes, and integration
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from flask import Flask

from src.routes.pwa_routes import pwa_bp


class TestPWAManifest(unittest.TestCase):
    """Test PWA manifest.json functionality"""

    def setUp(self):
        """Set up test environment"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.manifest_path = os.path.join(
            self.base_dir, "data", "static", "manifest.json"
        )

    def test_manifest_exists(self):
        """Test that manifest.json file exists"""
        self.assertTrue(
            os.path.exists(self.manifest_path), "manifest.json file should exist"
        )

    def test_manifest_valid_json(self):
        """Test that manifest.json is valid JSON"""
        with open(self.manifest_path, "r") as f:
            try:
                manifest_data = json.load(f)
                self.assertIsInstance(manifest_data, dict)
            except json.JSONDecodeError:
                self.fail("manifest.json should be valid JSON")

    def test_manifest_required_fields(self):
        """Test that manifest.json contains required PWA fields"""
        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)

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
            self.assertIn(field, manifest, f"Manifest should contain {field}")

    def test_manifest_icons(self):
        """Test that manifest has proper icon configuration"""
        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)

        icons = manifest.get("icons", [])
        self.assertGreater(len(icons), 0, "Manifest should have at least one icon")

        # Check for required icon sizes
        required_sizes = ["192x192", "512x512"]
        icon_sizes = [icon.get("sizes") for icon in icons]

        for size in required_sizes:
            self.assertIn(size, icon_sizes, f"Should have {size} icon")

    def test_manifest_shortcuts(self):
        """Test that manifest has app shortcuts configured"""
        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)

        shortcuts = manifest.get("shortcuts", [])
        self.assertGreater(len(shortcuts), 0, "Manifest should have shortcuts")

        for shortcut in shortcuts:
            self.assertIn("name", shortcut)
            self.assertIn("url", shortcut)


class TestServiceWorker(unittest.TestCase):
    """Test service worker functionality"""

    def setUp(self):
        """Set up test environment"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sw_path = os.path.join(self.base_dir, "data", "static", "sw.js")

    def test_service_worker_exists(self):
        """Test that service worker file exists"""
        self.assertTrue(
            os.path.exists(self.sw_path), "Service worker file should exist"
        )

    def test_service_worker_content(self):
        """Test that service worker contains required functionality"""
        with open(self.sw_path, "r") as f:
            sw_content = f.read()

        required_features = [
            "self.addEventListener",
            "install",
            "activate",
            "fetch",
            "caches",
            "IndexedDB",
            "sync",
        ]

        for feature in required_features:
            self.assertIn(
                feature, sw_content, f"Service worker should contain {feature}"
            )

    def test_service_worker_cache_strategy(self):
        """Test that service worker implements proper caching strategies"""
        with open(self.sw_path, "r") as f:
            sw_content = f.read()

        # Check for cache strategies
        self.assertIn("cache.match", sw_content, "Should implement cache matching")
        self.assertIn("cache.put", sw_content, "Should implement cache storage")
        self.assertIn("CACHE_NAME", sw_content, "Should define cache name")

    def test_service_worker_offline_support(self):
        """Test that service worker supports offline functionality"""
        with open(self.sw_path, "r") as f:
            sw_content = f.read()

        self.assertIn("OFFLINE_URL", sw_content, "Should define offline URL")
        self.assertIn("navigator.onLine", sw_content, "Should check online status")


class TestPWARoutes(unittest.TestCase):
    """Test PWA API routes"""

    def setUp(self):
        """Set up Flask app for testing"""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret-key"

        # Mock static folder
        self.app.static_folder = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "static"
        )

        self.app.register_blueprint(pwa_bp)
        self.client = self.app.test_client()

    def test_manifest_route(self):
        """Test /manifest.json route"""
        response = self.client.get("/manifest.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json")

        # Test that response is valid JSON
        data = json.loads(response.data)
        self.assertIsInstance(data, dict)

    def test_service_worker_route(self):
        """Test /sw.js route"""
        response = self.client.get("/sw.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/javascript; charset=utf-8")

        # Check for proper headers
        self.assertEqual(response.headers.get("Service-Worker-Allowed"), "/")
        self.assertEqual(response.headers.get("Cache-Control"), "no-cache")

    def test_pwa_status_route(self):
        """Test /api/pwa/status route"""
        response = self.client.get("/api/pwa/status")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data.get("success"))
        self.assertTrue(data.get("pwa_enabled"))
        self.assertIn("capabilities", data)

    def test_offline_route(self):
        """Test /offline route"""
        response = self.client.get("/offline")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"offline", response.data.lower())

    def test_install_stats_route(self):
        """Test /api/pwa/install-stats route"""
        test_data = {"event_type": "install_accepted", "user_agent": "test-browser"}

        response = self.client.post(
            "/api/pwa/install-stats",
            data=json.dumps(test_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data.get("success"))

    def test_cache_stats_route(self):
        """Test /api/pwa/cache-stats route"""
        response = self.client.get("/api/pwa/cache-stats")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data.get("success"))
        self.assertIn("stats", data)

    def test_push_subscription_routes(self):
        """Test push notification subscription routes"""
        # Test VAPID key endpoint
        response = self.client.get("/api/push/vapid-key")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data.get("success"))
        self.assertIn("publicKey", data)

        # Test subscription endpoint
        test_subscription = {
            "endpoint": "https://test-endpoint.com",
            "keys": {"p256dh": "test-key", "auth": "test-auth"},
        }

        response = self.client.post(
            "/api/push/subscribe",
            data=json.dumps(test_subscription),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertTrue(data.get("success"))


class TestPWAFiles(unittest.TestCase):
    """Test PWA static files"""

    def setUp(self):
        """Set up test environment"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.static_dir = os.path.join(self.base_dir, "data", "static")

    def test_pwa_js_exists(self):
        """Test that PWA JavaScript file exists"""
        pwa_js_path = os.path.join(self.static_dir, "js", "pwa.js")
        self.assertTrue(os.path.exists(pwa_js_path), "PWA JS file should exist")

    def test_pwa_css_exists(self):
        """Test that PWA CSS file exists"""
        pwa_css_path = os.path.join(self.static_dir, "css", "pwa.css")
        self.assertTrue(os.path.exists(pwa_css_path), "PWA CSS file should exist")

    def test_pwa_js_functionality(self):
        """Test that PWA JS contains required functionality"""
        pwa_js_path = os.path.join(self.static_dir, "js", "pwa.js")

        with open(pwa_js_path, "r") as f:
            pwa_content = f.read()

        required_features = [
            "VideoTranscriberPWA",
            "registerServiceWorker",
            "setupInstallPrompt",
            "IndexedDB",
            "addEventListener",
        ]

        for feature in required_features:
            self.assertIn(feature, pwa_content, f"PWA JS should contain {feature}")

    def test_pwa_css_functionality(self):
        """Test that PWA CSS contains required styles"""
        pwa_css_path = os.path.join(self.static_dir, "css", "pwa.css")

        with open(pwa_css_path, "r") as f:
            css_content = f.read()

        required_styles = [
            ".pwa-install-banner",
            ".offline-indicator",
            "@media (display-mode: standalone)",
            "touch-action",
        ]

        for style in required_styles:
            self.assertIn(style, css_content, f"PWA CSS should contain {style}")


class TestPWAIntegration(unittest.TestCase):
    """Test PWA integration with main application"""

    def setUp(self):
        """Set up test environment"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.template_dir = os.path.join(self.base_dir, "data", "templates")

    def test_base_template_pwa_integration(self):
        """Test that base template includes PWA elements"""
        base_template_path = os.path.join(self.template_dir, "base.html")

        with open(base_template_path, "r") as f:
            template_content = f.read()

        pwa_elements = [
            'rel="manifest"',
            "pwa.css",
            "pwa.js",
            "theme-color",
            "apple-touch-icon",
            "VideoTranscriberPWA",
        ]

        for element in pwa_elements:
            self.assertIn(
                element, template_content, f"Base template should include {element}"
            )

    def test_offline_template_exists(self):
        """Test that offline template exists and is properly configured"""
        offline_template_path = os.path.join(self.template_dir, "offline.html")
        self.assertTrue(
            os.path.exists(offline_template_path), "Offline template should exist"
        )

        with open(offline_template_path, "r") as f:
            template_content = f.read()

        self.assertIn(
            "offline",
            template_content.lower(),
            "Offline template should contain offline content",
        )

    def test_main_app_integration(self):
        """Test that PWA routes are registered in main app"""
        main_py_path = os.path.join(self.base_dir, "main.py")

        with open(main_py_path, "r") as f:
            main_content = f.read()

        integration_elements = [
            "from src.routes.pwa_routes import pwa_bp",
            "app.register_blueprint(pwa_bp)",
        ]

        for element in integration_elements:
            self.assertIn(element, main_content, f"Main app should include {element}")


class TestPWADirectories(unittest.TestCase):
    """Test PWA directory structure"""

    def setUp(self):
        """Set up test environment"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.static_dir = os.path.join(self.base_dir, "data", "static")

    def test_icons_directory_exists(self):
        """Test that icons directory exists"""
        icons_dir = os.path.join(self.static_dir, "icons")
        self.assertTrue(os.path.exists(icons_dir), "Icons directory should exist")

        # Check for README
        readme_path = os.path.join(icons_dir, "README.md")
        self.assertTrue(os.path.exists(readme_path), "Icons README should exist")

    def test_screenshots_directory_exists(self):
        """Test that screenshots directory exists"""
        screenshots_dir = os.path.join(self.static_dir, "screenshots")
        self.assertTrue(
            os.path.exists(screenshots_dir), "Screenshots directory should exist"
        )

        # Check for README
        readme_path = os.path.join(screenshots_dir, "README.md")
        self.assertTrue(os.path.exists(readme_path), "Screenshots README should exist")


class TestPWAPerformance(unittest.TestCase):
    """Test PWA performance characteristics"""

    def setUp(self):
        """Set up test environment"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_service_worker_size(self):
        """Test that service worker file is reasonably sized"""
        sw_path = os.path.join(self.base_dir, "data", "static", "sw.js")

        file_size = os.path.getsize(sw_path)
        # Service worker should be under 50KB for good performance
        self.assertLess(file_size, 50 * 1024, "Service worker should be under 50KB")

    def test_pwa_js_size(self):
        """Test that PWA JS file is reasonably sized"""
        pwa_js_path = os.path.join(self.base_dir, "data", "static", "js", "pwa.js")

        file_size = os.path.getsize(pwa_js_path)
        # PWA JS should be under 30KB for good performance
        self.assertLess(file_size, 30 * 1024, "PWA JS should be under 30KB")

    def test_manifest_size(self):
        """Test that manifest file is reasonably sized"""
        manifest_path = os.path.join(self.base_dir, "data", "static", "manifest.json")

        file_size = os.path.getsize(manifest_path)
        # Manifest should be under 10KB
        self.assertLess(file_size, 10 * 1024, "Manifest should be under 10KB")


if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestPWAManifest,
        TestServiceWorker,
        TestPWARoutes,
        TestPWAFiles,
        TestPWAIntegration,
        TestPWADirectories,
        TestPWAPerformance,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*60}")
    print(f"🧪 PWA Test Summary")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(
                f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}"
            )

    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")

    if result.wasSuccessful():
        print(f"\n🎉 All PWA tests passed!")
        print(f"✅ PWA implementation is fully tested and working")
    else:
        print(f"\n❌ Some tests failed. Please review and fix issues.")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
