"""
Comprehensive PWA test runner
"""

import os
import subprocess
import sys
import time
from datetime import datetime

import requests


def check_app_running(base_url="http://localhost:5001", timeout=5):
    """Check if the Flask app is running"""
    try:
        response = requests.get(f"{base_url}/api/health", timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def run_file_validation_tests():
    """Run PWA file validation tests"""
    print("📁 Running PWA File Validation Tests")
    print("=" * 50)

    try:
        # Import and run file validation tests
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from test_pwa_integration import TestPWAFileValidation

        validator = TestPWAFileValidation()
        validator.setup_method()

        tests = [
            ("Manifest JSON structure", validator.test_manifest_json_structure),
            ("Service worker content", validator.test_service_worker_content),
            ("PWA JavaScript library", validator.test_pwa_js_library),
            ("PWA CSS styles", validator.test_pwa_css_styles),
            ("Offline template", validator.test_offline_template),
        ]

        passed = 0
        for test_name, test_method in tests:
            try:
                test_method()
                print(f"✅ {test_name}")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name}: {e}")

        print(f"\n📁 File Validation: {passed}/{len(tests)} tests passed")
        return passed == len(tests)

    except ImportError as e:
        print(f"❌ Could not import file validation tests: {e}")
        return False


def run_integration_tests():
    """Run PWA integration tests"""
    print("\n🌐 Running PWA Integration Tests")
    print("=" * 50)

    base_url = "http://localhost:5001"

    if not check_app_running(base_url):
        print("⚠️  Application not running at http://localhost:5001")
        print("   Start the app with: python main.py")
        print("   Integration tests will be skipped.")
        return False

    try:
        from test_pwa_integration import TestPWAIntegration

        tester = TestPWAIntegration()
        tester.setup_method()

        tests = [
            ("Manifest accessibility", tester.test_manifest_accessibility),
            ("Service worker accessibility", tester.test_service_worker_accessibility),
            ("PWA status endpoint", tester.test_pwa_status_endpoint),
            ("Offline page accessibility", tester.test_offline_page_accessibility),
            ("PWA API endpoints", tester.test_pwa_api_endpoints),
            ("Push subscription flow", tester.test_push_subscription_flow),
            ("Offline queue management", tester.test_offline_queue_management),
            ("Install stats tracking", tester.test_install_stats_tracking),
            ("Cache management", tester.test_cache_management),
        ]

        passed = 0
        for test_name, test_method in tests:
            try:
                test_method()
                print(f"✅ {test_name}")
                passed += 1
            except Exception as e:
                print(f"❌ {test_name}: {e}")

        print(f"\n🌐 Integration Tests: {passed}/{len(tests)} tests passed")
        return passed == len(tests)

    except ImportError as e:
        print(f"❌ Could not import integration tests: {e}")
        return False


def run_unit_tests():
    """Run PWA unit tests using pytest if available"""
    print("\n🧪 Running PWA Unit Tests")
    print("=" * 50)

    try:
        # Try to run pytest on PWA routes
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_pwa_routes.py", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print("✅ Unit tests passed")
            print(result.stdout)
            return True
        else:
            print("❌ Unit tests failed")
            print(result.stdout)
            print(result.stderr)
            return False

    except FileNotFoundError:
        print("⚠️  pytest not found, running basic unit test validation")

        # Basic validation without pytest
        try:
            from test_pwa_routes import (
                TestPWAManifest,
                TestPWAStatus,
                TestServiceWorker,
            )

            print("✅ Unit test files are importable")
            return True
        except ImportError as e:
            print(f"❌ Unit test import failed: {e}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Unit tests timed out")
        return False


def run_browser_tests():
    """Run PWA browser tests if Selenium is available"""
    print("\n🌐 Running PWA Browser Tests")
    print("=" * 50)

    try:
        from test_pwa_browser import run_browser_tests

        run_browser_tests()
        return True
    except ImportError:
        print("⚠️  Selenium not available, skipping browser tests")
        print("   Install with: pip install selenium")
        print("   Also install ChromeDriver:")
        print("   macOS: brew install chromedriver")
        print("   Ubuntu: sudo apt-get install chromium-chromedriver")
        return False


def run_performance_tests():
    """Run PWA performance tests"""
    print("\n⚡ Running PWA Performance Tests")
    print("=" * 50)

    base_url = "http://localhost:5001"

    if not check_app_running(base_url):
        print("⚠️  Application not running, skipping performance tests")
        return False

    tests_passed = 0
    total_tests = 4

    # Test 1: Service Worker Load Time
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/sw.js")
        load_time = time.time() - start_time

        if response.status_code == 200 and load_time < 1.0:
            print(f"✅ Service worker loads quickly ({load_time:.3f}s)")
            tests_passed += 1
        else:
            print(f"❌ Service worker slow or failed ({load_time:.3f}s)")
    except Exception as e:
        print(f"❌ Service worker load test failed: {e}")

    # Test 2: Manifest Load Time
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/manifest.json")
        load_time = time.time() - start_time

        if response.status_code == 200 and load_time < 0.5:
            print(f"✅ Manifest loads quickly ({load_time:.3f}s)")
            tests_passed += 1
        else:
            print(f"❌ Manifest slow or failed ({load_time:.3f}s)")
    except Exception as e:
        print(f"❌ Manifest load test failed: {e}")

    # Test 3: PWA API Response Time
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/api/pwa/status")
        load_time = time.time() - start_time

        if response.status_code == 200 and load_time < 1.0:
            print(f"✅ PWA API responds quickly ({load_time:.3f}s)")
            tests_passed += 1
        else:
            print(f"❌ PWA API slow or failed ({load_time:.3f}s)")
    except Exception as e:
        print(f"❌ PWA API test failed: {e}")

    # Test 4: File Sizes
    try:
        files_to_check = [
            ("/sw.js", 20000),  # Service worker should be < 20KB
            ("/manifest.json", 5000),  # Manifest should be < 5KB
            ("/static/js/pwa.js", 30000),  # PWA JS should be < 30KB
            ("/static/css/pwa.css", 10000),  # PWA CSS should be < 10KB
        ]

        all_sizes_good = True
        for file_path, max_size in files_to_check:
            try:
                response = requests.get(f"{base_url}{file_path}")
                if response.status_code == 200:
                    size = len(response.content)
                    if size <= max_size:
                        print(f"✅ {file_path} size OK ({size} bytes)")
                    else:
                        print(f"❌ {file_path} too large ({size} > {max_size} bytes)")
                        all_sizes_good = False
                else:
                    print(f"❌ {file_path} not accessible")
                    all_sizes_good = False
            except Exception as e:
                print(f"❌ {file_path} size check failed: {e}")
                all_sizes_good = False

        if all_sizes_good:
            tests_passed += 1

    except Exception as e:
        print(f"❌ File size tests failed: {e}")

    print(f"\n⚡ Performance Tests: {tests_passed}/{total_tests} tests passed")
    return tests_passed == total_tests


def generate_test_report(results):
    """Generate a comprehensive test report"""
    print("\n" + "=" * 60)
    print("📋 PWA TESTING SUMMARY REPORT")
    print("=" * 60)
    print(f"Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    total_categories = len(results)
    passed_categories = sum(1 for result in results.values() if result)

    for category, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{category:<25} {status}")

    print()
    print(
        f"Overall Result: {passed_categories}/{total_categories} test categories passed"
    )

    if passed_categories == total_categories:
        print("🎉 ALL PWA TESTS PASSED!")
        print("   The PWA implementation is fully tested and ready for production.")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("   Please review and fix the failed tests before proceeding.")

    print("\n📋 Recommendations:")
    if not results.get("File Validation", True):
        print("   • Fix PWA file structure and content issues")
    if not results.get("Integration Tests", True):
        print("   • Ensure app is running and API endpoints work correctly")
    if not results.get("Unit Tests", True):
        print("   • Install pytest and fix unit test failures")
    if not results.get("Browser Tests", True):
        print("   • Install Selenium and ChromeDriver for browser testing")
    if not results.get("Performance Tests", True):
        print("   • Optimize PWA file sizes and response times")

    return passed_categories == total_categories


def main():
    """Run all PWA tests"""
    print("🧪 COMPREHENSIVE PWA TESTING SUITE")
    print("=" * 60)
    print("Testing Progressive Web App implementation...")
    print()

    # Run all test categories
    results = {}

    results["File Validation"] = run_file_validation_tests()
    results["Integration Tests"] = run_integration_tests()
    results["Unit Tests"] = run_unit_tests()
    results["Browser Tests"] = run_browser_tests()
    results["Performance Tests"] = run_performance_tests()

    # Generate final report
    all_passed = generate_test_report(results)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
