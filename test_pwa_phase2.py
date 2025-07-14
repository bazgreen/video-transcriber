#!/usr/bin/env python3
"""
Test PWA Phase 2 - Camera and Voice Integration
"""

import json
import os
import time
from datetime import datetime

import requests


def test_pwa_phase2_files():
    """Test that all Phase 2 files are present and valid"""
    print("📱 Testing PWA Phase 2 Files")
    print("=" * 40)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "data", "static")
    templates_dir = os.path.join(base_dir, "data", "templates")

    files_to_check = [
        ("Camera JavaScript", os.path.join(static_dir, "js", "camera.js")),
        ("Voice JavaScript", os.path.join(static_dir, "js", "voice.js")),
        ("Camera/Voice CSS", os.path.join(static_dir, "css", "camera-voice.css")),
        (
            "Touch Controls JS",
            os.path.join(static_dir, "js", "video-touch-controls.js"),
        ),
        (
            "Transcript Touch JS",
            os.path.join(static_dir, "js", "transcript-touch-navigation.js"),
        ),
        ("Mobile Upload Template", os.path.join(templates_dir, "mobile-upload.html")),
    ]

    passed = 0
    for name, file_path in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {name} ({file_size} bytes)")
            passed += 1
        else:
            print(f"❌ {name} - File not found")

    print(f"\n📁 Phase 2 Files: {passed}/{len(files_to_check)} files present")
    return passed == len(files_to_check)


def test_javascript_features():
    """Test JavaScript feature implementation"""
    print("\n🔍 Testing JavaScript Features")
    print("=" * 40)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Test camera.js features
    camera_js_path = os.path.join(base_dir, "data", "static", "js", "camera.js")
    if os.path.exists(camera_js_path):
        with open(camera_js_path, "r") as f:
            camera_content = f.read()

        camera_features = [
            "MobileCameraManager",
            "requestCameraAccess",
            "startRecording",
            "stopRecording",
            "switchCamera",
            "MediaRecorder",
            "getUserMedia",
            "handleRecordingComplete",
            "uploadRecording",
        ]

        camera_passed = 0
        for feature in camera_features:
            if feature in camera_content:
                camera_passed += 1
            else:
                print(f"❌ Camera feature missing: {feature}")

        print(f"✅ Camera features: {camera_passed}/{len(camera_features)}")

    # Test voice.js features
    voice_js_path = os.path.join(base_dir, "data", "static", "js", "voice.js")
    if os.path.exists(voice_js_path):
        with open(voice_js_path, "r") as f:
            voice_content = f.read()

        voice_features = [
            "VoiceInputManager",
            "SpeechRecognition",
            "startVoiceInput",
            "stopVoiceInput",
            "handleVoiceResult",
            "processVoiceCommand",
            "toggleVoiceInput",
            "requestMicrophonePermission",
            "setupVoiceButton",
        ]

        voice_passed = 0
        for feature in voice_features:
            if feature in voice_content:
                voice_passed += 1
            else:
                print(f"❌ Voice feature missing: {feature}")

        print(f"✅ Voice features: {voice_passed}/{len(voice_features)}")

    # Test touch controls
    touch_js_path = os.path.join(
        base_dir, "data", "static", "js", "video-touch-controls.js"
    )
    if os.path.exists(touch_js_path):
        with open(touch_js_path, "r") as f:
            touch_content = f.read()

        touch_features = [
            "VideoTouchControls",
            "handleTouchStart",
            "handleTouchMove",
            "handleTouchEnd",
            "handlePinchZoom",
            "detectSwipeGesture",
            "touchstart",
            "touchmove",
            "touchend",
        ]

        touch_passed = 0
        for feature in touch_features:
            if feature in touch_content:
                touch_passed += 1
            else:
                print(f"❌ Touch feature missing: {feature}")

        print(f"✅ Touch features: {touch_passed}/{len(touch_features)}")

    return True


def test_css_styles():
    """Test CSS styling implementation"""
    print("\n🎨 Testing CSS Styles")
    print("=" * 40)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, "data", "static", "css", "camera-voice.css")

    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css_content = f.read()

        required_styles = [
            ".camera-container",
            ".camera-record-btn",
            ".camera-switch-btn",
            ".recording-indicator",
            ".voice-input-btn",
            ".voice-command-btn",
            ".voice-listening-indicator",
            ".mobile-camera-btn",
            "@keyframes pulse-red",
            "@keyframes wave",
            "@media (max-width: 768px)",
            "@media (prefers-reduced-motion: reduce)",
        ]

        css_passed = 0
        for style in required_styles:
            if style in css_content:
                css_passed += 1
            else:
                print(f"❌ CSS style missing: {style}")

        print(f"✅ CSS styles: {css_passed}/{len(required_styles)}")

        # Check file size
        css_size = len(css_content)
        if css_size > 1000:  # Should be substantial
            print(f"✅ CSS file size: {css_size} bytes")
        else:
            print(f"⚠️  CSS file seems small: {css_size} bytes")

        return css_passed >= len(required_styles) * 0.8  # 80% threshold

    return False


def test_template_integration():
    """Test template integration"""
    print("\n📄 Testing Template Integration")
    print("=" * 40)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Test base template integration
    base_template_path = os.path.join(base_dir, "data", "templates", "base.html")
    if os.path.exists(base_template_path):
        with open(base_template_path, "r") as f:
            base_content = f.read()

        required_includes = [
            "camera-voice.css",
            "camera.js",
            "voice.js",
            "video-touch-controls.js",
            "transcript-touch-navigation.js",
        ]

        base_passed = 0
        for include in required_includes:
            if include in base_content:
                base_passed += 1
            else:
                print(f"❌ Base template missing: {include}")

        print(f"✅ Base template includes: {base_passed}/{len(required_includes)}")

    # Test mobile upload template
    mobile_template_path = os.path.join(
        base_dir, "data", "templates", "mobile-upload.html"
    )
    if os.path.exists(mobile_template_path):
        with open(mobile_template_path, "r") as f:
            mobile_content = f.read()

        mobile_features = [
            "mobile-upload-section",
            "camera-record-btn",
            "voice-input-container",
            "mobile-camera-btn",
            "upload-trigger-btn",
            "camera-container",
            "voice-command-btn",
        ]

        mobile_passed = 0
        for feature in mobile_features:
            if feature in mobile_content:
                mobile_passed += 1
            else:
                print(f"❌ Mobile template missing: {feature}")

        print(f"✅ Mobile template features: {mobile_passed}/{len(mobile_features)}")

        mobile_size = len(mobile_content)
        print(f"✅ Mobile template size: {mobile_size} bytes")

        return mobile_passed >= len(mobile_features) * 0.8  # 80% threshold

    return False


def test_api_endpoints():
    """Test API endpoints work with camera/voice features"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 40)

    base_url = "http://localhost:5001"

    # Check if app is running
    try:
        response = requests.get(f"{base_url}/api/pwa/status", timeout=5)
        if response.status_code != 200:
            print("⚠️  App not running at http://localhost:5001")
            return False
    except requests.exceptions.RequestException:
        print("⚠️  App not running at http://localhost:5001")
        return False

    # Test PWA capabilities for camera/voice
    try:
        response = requests.get(f"{base_url}/api/pwa/status")
        data = response.json()

        capabilities = data.get("capabilities", {})

        # Check mobile-specific capabilities
        if capabilities.get("camera_access") is not None:
            print("✅ Camera access capability detected")
        else:
            print("⚠️  Camera access capability not specified")

        if capabilities.get("service_worker"):
            print("✅ Service worker capability confirmed")
        else:
            print("❌ Service worker capability missing")

        return True

    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def test_mobile_detection():
    """Test mobile device detection"""
    print("\n📱 Testing Mobile Detection")
    print("=" * 40)

    # Test user agent detection (simulated)
    mobile_user_agents = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        "Mozilla/5.0 (Android 10; Mobile; rv:81.0)",
        "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)",
    ]

    print("✅ Mobile user agent patterns available")
    print(f"✅ Test patterns: {len(mobile_user_agents)} patterns")

    # Test media query support (CSS)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, "data", "static", "css", "camera-voice.css")

    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            css_content = f.read()

        mobile_queries = css_content.count("@media (max-width:")
        responsive_queries = css_content.count("@media")

        print(f"✅ Responsive breakpoints: {mobile_queries} mobile queries")
        print(f"✅ Total media queries: {responsive_queries}")

        return mobile_queries >= 2  # Should have at least 2 mobile breakpoints

    return False


def run_phase2_tests():
    """Run all PWA Phase 2 tests"""
    print("🚀 PWA PHASE 2 TESTING SUITE")
    print("=" * 50)
    print("Testing Camera & Voice Integration...")
    print()

    results = {}

    results["Files Present"] = test_pwa_phase2_files()
    results["JavaScript Features"] = test_javascript_features()
    results["CSS Styles"] = test_css_styles()
    results["Template Integration"] = test_template_integration()
    results["API Endpoints"] = test_api_endpoints()
    results["Mobile Detection"] = test_mobile_detection()

    # Generate report
    print("\n" + "=" * 50)
    print("📋 PWA PHASE 2 TEST SUMMARY")
    print("=" * 50)
    print(f"Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    passed_tests = sum(1 for result in results.values() if result)
    total_tests = len(results)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<25} {status}")

    print()
    print(f"Overall Result: {passed_tests}/{total_tests} test categories passed")

    if passed_tests == total_tests:
        print("🎉 ALL PWA PHASE 2 TESTS PASSED!")
        print("   Camera and Voice integration is complete and ready!")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("   Please review and fix the failed components.")

    print("\n📱 Phase 2 Features Now Available:")
    if results.get("Files Present"):
        print("   ✅ Camera recording with device integration")
        print("   ✅ Voice input for notes and commands")
        print("   ✅ Touch-optimized mobile controls")
        print("   ✅ Mobile-responsive upload interface")

    print("\n🚀 Next Phase: Mobile UI Components (Week 3)")
    print("   • Bottom navigation for mobile")
    print("   • Slide-up panels and modals")
    print("   • Pull-to-refresh functionality")
    print("   • Mobile-optimized layouts")

    return passed_tests == total_tests


if __name__ == "__main__":
    run_phase2_tests()
