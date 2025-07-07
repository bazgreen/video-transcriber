#!/usr/bin/env python3
"""
Comprehensive validation script for the video transcriber application.

This script validates that all major components are working correctly after
the linting fixes and improvements.
"""

import json
import sys
import time
from typing import Any, Dict

import requests


def test_server_health() -> bool:
    """Test if the server is running and responding."""
    print("🔍 Testing server health...")

    try:
        response = requests.get("http://localhost:5001/", timeout=10)
        if response.status_code == 200:
            print("✅ Main page accessible")
            return True
        else:
            print(f"❌ Main page returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False


def test_api_endpoints() -> bool:
    """Test critical API endpoints."""
    print("\n🔍 Testing API endpoints...")

    endpoints = [
        ("/api/performance/live", "Performance monitoring"),
        ("/api/sessions", "Sessions listing"),
        ("/api/ai/capabilities", "AI capabilities"),
        ("/api/keywords", "Keywords management"),
    ]

    all_passed = True

    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:5001{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: {endpoint}")
            else:
                print(f"❌ {description}: {endpoint} (status: {response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"❌ {description}: {endpoint} (error: {e})")
            all_passed = False

    return all_passed


def test_ai_insights_functionality() -> bool:
    """Test AI insights functionality."""
    print("\n🔍 Testing AI insights functionality...")

    try:
        # Test AI capabilities endpoint
        response = requests.get("http://localhost:5001/api/ai/capabilities", timeout=10)
        if response.status_code != 200:
            print("❌ AI capabilities endpoint failed")
            return False

        capabilities = response.json()
        print(
            f"✅ AI capabilities loaded: {capabilities.get('ai_insights_available', False)}"
        )

        # Test AI insights page accessibility
        response = requests.get("http://localhost:5001/ai-insights", timeout=10)
        if response.status_code != 200:
            print("❌ AI insights page not accessible")
            return False

        print("✅ AI insights page accessible")

        # Import and test AI insights engine directly
        from src.services.ai_insights import create_ai_insights_engine

        engine = create_ai_insights_engine()

        if engine.sentiment_available:
            print("✅ Sentiment analysis available")
        else:
            print("⚠️  Sentiment analysis not available")

        if engine.topic_modeling_available:
            print("✅ Topic modeling available")
        else:
            print("⚠️  Topic modeling not available")

        return True

    except Exception as e:
        print(f"❌ AI insights test failed: {e}")
        return False


def test_template_rendering() -> bool:
    """Test that all main templates render without errors."""
    print("\n🔍 Testing template rendering...")

    pages = [
        ("/", "Main page"),
        ("/ai-insights", "AI insights dashboard"),
        ("/sessions", "Sessions page"),
    ]

    all_passed = True

    for url, description in pages:
        try:
            response = requests.get(f"http://localhost:5001{url}", timeout=10)
            if response.status_code == 200 and "<!DOCTYPE html>" in response.text:
                print(f"✅ {description} renders correctly")
            else:
                print(
                    f"❌ {description} rendering failed (status: {response.status_code})"
                )
                all_passed = False
        except Exception as e:
            print(f"❌ {description} test failed: {e}")
            all_passed = False

    return all_passed


def test_static_files() -> bool:
    """Test that static files are accessible."""
    print("\n🔍 Testing static files...")

    static_files = [
        ("/static/css/app.css", "Main CSS"),
        ("/static/js/app.js", "Main JavaScript"),
    ]

    all_passed = True

    for url, description in static_files:
        try:
            response = requests.get(f"http://localhost:5001{url}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {description} accessible")
            else:
                print(
                    f"❌ {description} not accessible (status: {response.status_code})"
                )
                all_passed = False
        except Exception as e:
            print(f"❌ {description} test failed: {e}")
            all_passed = False

    return all_passed


def main():
    """Run comprehensive validation tests."""
    print("🚀 Video Transcriber - Comprehensive Validation Suite")
    print("=" * 60)

    # Give the server a moment to fully start if needed
    time.sleep(2)

    tests = [
        ("Server Health", test_server_health),
        ("API Endpoints", test_api_endpoints),
        ("AI Insights", test_ai_insights_functionality),
        ("Template Rendering", test_template_rendering),
        ("Static Files", test_static_files),
    ]

    results = {}
    all_passed = True

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
            all_passed = False

    print(f"\n{'='*60}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*60}")

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<30} {status}")

    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED! Application is working correctly.")
        print("\n📋 Ready for use:")
        print("   🌐 Main app: http://localhost:5001")
        print("   🤖 AI insights: http://localhost:5001/ai-insights")
        print("   📁 Sessions: http://localhost:5001/sessions")
        print("   ⚙️  Configuration: http://localhost:5001/config")
        return True
    else:
        print("⚠️  SOME TESTS FAILED. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
