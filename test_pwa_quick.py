#!/usr/bin/env python3
"""
Quick PWA functionality verification test
"""

import json
import time

import requests


def test_pwa_endpoints():
    """Test all PWA endpoints quickly"""
    base_url = "http://localhost:5001"

    print("🧪 Quick PWA Functionality Test")
    print("=" * 40)

    tests = [
        ("Manifest JSON", f"{base_url}/manifest.json"),
        ("Service Worker", f"{base_url}/sw.js"),
        ("PWA Status API", f"{base_url}/api/pwa/status"),
        ("Offline Page", f"{base_url}/offline"),
        ("Cache Stats API", f"{base_url}/api/pwa/cache-stats"),
        ("VAPID Key API", f"{base_url}/api/push/vapid-key"),
        ("Update Check API", f"{base_url}/api/pwa/update-check"),
        ("Offline Queue API", f"{base_url}/api/pwa/offline-queue"),
    ]

    passed = 0
    for test_name, url in tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {test_name}")
                passed += 1
            else:
                print(f"❌ {test_name} (HTTP {response.status_code})")
        except Exception as e:
            print(f"❌ {test_name} (Error: {e})")

    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")

    # Test specific PWA functionality
    print("\n🔍 Testing PWA Features:")

    # Test manifest structure
    try:
        response = requests.get(f"{base_url}/manifest.json")
        manifest = response.json()

        required_fields = ["name", "short_name", "start_url", "display", "icons"]
        manifest_valid = all(field in manifest for field in required_fields)

        if manifest_valid:
            print(f"✅ Manifest structure ({len(manifest['icons'])} icons)")
        else:
            print("❌ Manifest structure invalid")
    except Exception as e:
        print(f"❌ Manifest structure test failed: {e}")

    # Test service worker headers
    try:
        response = requests.get(f"{base_url}/sw.js")
        headers = response.headers

        required_headers = ["Service-Worker-Allowed", "Cache-Control"]
        headers_valid = all(header in headers for header in required_headers)

        if headers_valid and "Service-Worker-Allowed" in headers:
            print(f"✅ Service worker headers")
        else:
            print("❌ Service worker headers missing")
    except Exception as e:
        print(f"❌ Service worker headers test failed: {e}")

    # Test PWA API response structure
    try:
        response = requests.get(f"{base_url}/api/pwa/status")
        data = response.json()

        required_fields = ["success", "pwa_enabled", "capabilities", "version"]
        api_valid = all(field in data for field in required_fields)

        if api_valid and data.get("success"):
            print(f"✅ PWA API structure")
        else:
            print("❌ PWA API structure invalid")
    except Exception as e:
        print(f"❌ PWA API test failed: {e}")

    # Test file sizes (for performance)
    print("\n📏 File Size Check:")
    size_tests = [
        ("Service Worker", f"{base_url}/sw.js", 25000),
        ("Manifest", f"{base_url}/manifest.json", 5000),
        ("PWA JavaScript", f"{base_url}/static/js/pwa.js", 35000),
        ("PWA CSS", f"{base_url}/static/css/pwa.css", 15000),
    ]

    for name, url, max_size in size_tests:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                size = len(response.content)
                if size <= max_size:
                    print(f"✅ {name} ({size} bytes)")
                else:
                    print(f"⚠️  {name} large ({size} > {max_size} bytes)")
            else:
                print(f"❌ {name} not accessible")
        except Exception as e:
            print(f"❌ {name} size check failed: {e}")

    print("\n🎯 PWA Installation Readiness:")

    # Check PWA install criteria
    try:
        # Manifest accessibility
        manifest_response = requests.get(f"{base_url}/manifest.json")
        manifest_ok = manifest_response.status_code == 200

        # Service worker accessibility
        sw_response = requests.get(f"{base_url}/sw.js")
        sw_ok = sw_response.status_code == 200

        # HTTPS or localhost (for testing)
        secure_context = True  # localhost is secure context

        if manifest_ok and sw_ok and secure_context:
            print("✅ PWA installable - all criteria met")
        else:
            print("❌ PWA not installable - missing criteria")

    except Exception as e:
        print(f"❌ PWA installability check failed: {e}")

    print("\n🏁 PWA functionality verification complete!")


if __name__ == "__main__":
    test_pwa_endpoints()
