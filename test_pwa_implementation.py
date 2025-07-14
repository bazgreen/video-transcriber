#!/usr/bin/env python3
"""
Test script for PWA (Progressive Web App) implementation
Tests PWA routes, manifest, service worker, and functionality
"""

import json
import os
import sys
import traceback
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_pwa_files_exist():
    """Test that all required PWA files exist"""
    print("🔍 Testing PWA file existence...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "data", "static")

    required_files = ["manifest.json", "sw.js", "js/pwa.js", "css/pwa.css"]

    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(static_dir, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required PWA files")
        return False

    print("✅ All required PWA files exist")
    return True


def test_manifest_json():
    """Test the PWA manifest.json file"""
    print("\n🔍 Testing PWA manifest...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    manifest_path = os.path.join(base_dir, "data", "static", "manifest.json")

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # Check required fields
        required_fields = [
            "name",
            "short_name",
            "icons",
            "start_url",
            "display",
            "theme_color",
        ]
        missing_fields = []

        for field in required_fields:
            if field not in manifest:
                missing_fields.append(field)

        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False

        # Check icons
        if not isinstance(manifest["icons"], list) or len(manifest["icons"]) == 0:
            print("❌ No icons defined in manifest")
            return False

        print(f"✅ Manifest valid with {len(manifest['icons'])} icons")
        print(f"   App name: {manifest['name']}")
        print(f"   Display mode: {manifest['display']}")
        print(f"   Start URL: {manifest['start_url']}")

        return True

    except Exception as e:
        print(f"❌ Error reading manifest: {e}")
        return False


def test_service_worker():
    """Test the service worker file"""
    print("\n🔍 Testing service worker...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    sw_path = os.path.join(base_dir, "data", "static", "sw.js")

    try:
        with open(sw_path, "r") as f:
            sw_content = f.read()

        # Check for essential service worker features
        required_features = [
            "self.addEventListener",
            "install",
            "activate",
            "fetch",
            "caches",
            "IndexedDB",
            "sync",
        ]

        missing_features = []
        for feature in required_features:
            if feature not in sw_content:
                missing_features.append(feature)

        if missing_features:
            print(f"❌ Missing service worker features: {missing_features}")
            return False

        print("✅ Service worker contains all required features")
        print(f"   File size: {len(sw_content)} characters")

        return True

    except Exception as e:
        print(f"❌ Error reading service worker: {e}")
        return False


def test_pwa_routes():
    """Test PWA route registration"""
    print("\n🔍 Testing PWA routes...")

    try:
        from src.routes.pwa_routes import pwa_bp

        # Check that blueprint exists
        if not pwa_bp:
            print("❌ PWA blueprint not found")
            return False

        # Check route registration
        routes = []
        for rule in pwa_bp.deferred_functions:
            if hasattr(rule, "rule"):
                routes.append(rule.rule)

        # Get routes from the blueprint's url_map
        route_count = len([rule for rule in pwa_bp.deferred_functions])

        print(f"✅ PWA blueprint found with {route_count} routes registered")
        print(f"   Blueprint name: {pwa_bp.name}")

        return True

    except Exception as e:
        print(f"❌ Error testing PWA routes: {e}")
        traceback.print_exc()
        return False


def test_pwa_integration():
    """Test PWA integration in templates"""
    print("\n🔍 Testing PWA template integration...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    base_template_path = os.path.join(base_dir, "data", "templates", "base.html")

    try:
        with open(base_template_path, "r") as f:
            template_content = f.read()

        # Check for PWA integration
        required_integrations = [
            "manifest",
            "pwa.css",
            "pwa.js",
            "theme-color",
            "apple-touch-icon",
        ]

        missing_integrations = []
        for integration in required_integrations:
            if integration not in template_content:
                missing_integrations.append(integration)

        if missing_integrations:
            print(f"❌ Missing template integrations: {missing_integrations}")
            return False

        print("✅ Base template properly integrated with PWA")

        return True

    except Exception as e:
        print(f"❌ Error testing template integration: {e}")
        return False


def test_offline_template():
    """Test offline template exists"""
    print("\n🔍 Testing offline template...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    offline_template_path = os.path.join(base_dir, "data", "templates", "offline.html")

    try:
        with open(offline_template_path, "r") as f:
            template_content = f.read()

        # Check for essential offline features
        required_features = ["offline", "retry", "connection"]

        missing_features = []
        for feature in required_features:
            if feature.lower() not in template_content.lower():
                missing_features.append(feature)

        if missing_features:
            print(f"❌ Missing offline template features: {missing_features}")
            return False

        print("✅ Offline template properly configured")
        print(f"   Template size: {len(template_content)} characters")

        return True

    except Exception as e:
        print(f"❌ Error testing offline template: {e}")
        return False


def test_app_registration():
    """Test that PWA routes are registered in main app"""
    print("\n🔍 Testing app registration...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_py_path = os.path.join(base_dir, "main.py")

    try:
        with open(main_py_path, "r") as f:
            main_content = f.read()

        # Check for PWA blueprint import and registration
        required_items = ["pwa_routes", "pwa_bp", "register_blueprint(pwa_bp)"]

        missing_items = []
        for item in required_items:
            if item not in main_content:
                missing_items.append(item)

        if missing_items:
            print(f"❌ Missing app registration items: {missing_items}")
            return False

        print("✅ PWA properly registered in main app")

        return True

    except Exception as e:
        print(f"❌ Error testing app registration: {e}")
        return False


def main():
    """Run all PWA tests"""
    print("🧪 Starting PWA Implementation Tests\n")
    print("=" * 50)

    tests = [
        test_pwa_files_exist,
        test_manifest_json,
        test_service_worker,
        test_pwa_routes,
        test_pwa_integration,
        test_offline_template,
        test_app_registration,
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print()  # Add spacing after failed tests
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with exception: {e}")
            traceback.print_exc()

    print("\n" + "=" * 50)
    print(f"🧪 PWA Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All PWA tests passed! Phase 1 implementation complete.")
        print("\n📋 Next Steps:")
        print("   1. Create actual icon files (see data/static/icons/README.md)")
        print(
            "   2. Take screenshots for app store (see data/static/screenshots/README.md)"
        )
        print("   3. Test PWA installation on mobile devices")
        print("   4. Begin Phase 2: Mobile Optimizations")
        return True
    else:
        print(f"❌ {total - passed} tests failed. Please fix issues before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
