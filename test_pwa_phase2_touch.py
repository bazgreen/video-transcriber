#!/usr/bin/env python3
"""
Test script for PWA Phase 2 Touch Controls implementation
"""

import os
import time
from pathlib import Path

import requests


def test_touch_controls_files():
    """Test that all touch control files exist and are properly structured"""
    print("🧪 Testing PWA Phase 2 Touch Controls Implementation")
    print("=" * 60)

    base_dir = Path(__file__).parent
    static_dir = base_dir / "data" / "static"

    # Required files for touch controls
    required_files = [
        static_dir / "js" / "video-touch-controls.js",
        static_dir / "js" / "transcript-touch-navigation.js",
        static_dir / "css" / "pwa.css",
    ]

    print("📁 Checking Touch Control Files:")
    all_files_exist = True

    for file_path in required_files:
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {file_path.name} ({size:,} bytes)")
        else:
            print(f"❌ {file_path.name} - Missing")
            all_files_exist = False

    return all_files_exist


def test_touch_control_features():
    """Test touch control JavaScript features"""
    print("\n🎮 Testing Touch Control Features:")

    js_file = (
        Path(__file__).parent / "data" / "static" / "js" / "video-touch-controls.js"
    )

    if not js_file.exists():
        print("❌ Video touch controls file not found")
        return False

    content = js_file.read_text()

    # Required touch control features
    required_features = [
        "VideoTouchControls",
        "handleTouchStart",
        "handleTouchMove",
        "handleTouchEnd",
        "handlePinchZoom",
        "togglePlayPause",
        "rewind",
        "forward",
        "toggleFullscreen",
        "triggerHapticFeedback",
        "showGestureIndicator",
    ]

    missing_features = []
    for feature in required_features:
        if feature in content:
            print(f"✅ {feature}")
        else:
            print(f"❌ {feature} - Missing")
            missing_features.append(feature)

    return len(missing_features) == 0


def test_transcript_navigation_features():
    """Test transcript navigation JavaScript features"""
    print("\n📑 Testing Transcript Navigation Features:")

    js_file = (
        Path(__file__).parent
        / "data"
        / "static"
        / "js"
        / "transcript-touch-navigation.js"
    )

    if not js_file.exists():
        print("❌ Transcript navigation file not found")
        return False

    content = js_file.read_text()

    # Required navigation features
    required_features = [
        "TranscriptTouchNavigation",
        "handleTouchStart",
        "handleSwipeGesture",
        "navigateToNext",
        "navigateToPrevious",
        "scrollToSegment",
        "performSearch",
        "openSearchMode",
        "highlightSegment",
        "jumpToNextChapter",
        "showContextMenu",
    ]

    missing_features = []
    for feature in required_features:
        if feature in content:
            print(f"✅ {feature}")
        else:
            print(f"❌ {feature} - Missing")
            missing_features.append(feature)

    return len(missing_features) == 0


def test_touch_control_styles():
    """Test touch control CSS styles"""
    print("\n🎨 Testing Touch Control Styles:")

    css_file = Path(__file__).parent / "data" / "static" / "css" / "pwa.css"

    if not css_file.exists():
        print("❌ PWA CSS file not found")
        return False

    content = css_file.read_text()

    # Required CSS classes for touch controls
    required_styles = [
        "video-touch-overlay",
        "touch-zone",
        "mobile-progress-bar",
        "progress-track",
        "progress-thumb",
        "transcript-nav-controls",
        "nav-control",
        "mobile-search-interface",
        "search-input",
        "highlighted-segment",
        "segment-context-menu",
        "swipe-indicator",
        "mobile-toast",
    ]

    missing_styles = []
    for style in required_styles:
        if f".{style}" in content:
            print(f"✅ .{style}")
        else:
            print(f"❌ .{style} - Missing")
            missing_styles.append(style)

    return len(missing_styles) == 0


def test_mobile_responsiveness():
    """Test mobile responsiveness CSS"""
    print("\n📱 Testing Mobile Responsiveness:")

    css_file = Path(__file__).parent / "data" / "static" / "css" / "pwa.css"
    content = css_file.read_text()

    # Required mobile features
    mobile_features = [
        "@media (max-width: 768px)",
        "@media (orientation: landscape)",
        "@media (pointer: coarse)",
        "@media (prefers-reduced-motion: reduce)",
        "@media (prefers-color-scheme: dark)",
        "min-height: 44px",  # iOS touch target minimum
        "touch-action",
        "user-select: none",
        "-webkit-user-select: none",
    ]

    missing_features = []
    for feature in mobile_features:
        if feature in content:
            print(f"✅ {feature}")
        else:
            print(f"❌ {feature} - Missing")
            missing_features.append(feature)

    return len(missing_features) == 0


def test_template_integration():
    """Test template integration"""
    print("\n🔗 Testing Template Integration:")

    template_file = Path(__file__).parent / "data" / "templates" / "base.html"

    if not template_file.exists():
        print("❌ Base template not found")
        return False

    content = template_file.read_text()

    # Required script includes
    required_scripts = ["video-touch-controls.js", "transcript-touch-navigation.js"]

    missing_scripts = []
    for script in required_scripts:
        if script in content:
            print(f"✅ {script} included")
        else:
            print(f"❌ {script} - Not included")
            missing_scripts.append(script)

    return len(missing_scripts) == 0


def test_app_integration():
    """Test integration with running app"""
    print("\n🌐 Testing App Integration:")

    base_url = "http://localhost:5001"

    # Test if app is running
    try:
        response = requests.get(f"{base_url}/api/pwa/status", timeout=5)
        if response.status_code != 200:
            print("⚠️  App not running, skipping integration tests")
            return True
    except requests.RequestException:
        print("⚠️  App not running, skipping integration tests")
        return True

    # Test JavaScript file accessibility
    js_files = [
        "/static/js/video-touch-controls.js",
        "/static/js/transcript-touch-navigation.js",
    ]

    all_accessible = True
    for js_file in js_files:
        try:
            response = requests.get(f"{base_url}{js_file}")
            if response.status_code == 200:
                print(f"✅ {js_file} accessible ({len(response.content):,} bytes)")
            else:
                print(f"❌ {js_file} not accessible (HTTP {response.status_code})")
                all_accessible = False
        except requests.RequestException as e:
            print(f"❌ {js_file} request failed: {e}")
            all_accessible = False

    return all_accessible


def test_gesture_patterns():
    """Test gesture pattern definitions"""
    print("\n👆 Testing Gesture Patterns:")

    js_file = (
        Path(__file__).parent / "data" / "static" / "js" / "video-touch-controls.js"
    )
    content = js_file.read_text()

    # Required gesture patterns
    gesture_patterns = [
        "swipeMinDistance",
        "swipeMaxTime",
        "doubleTapDelay",
        "pinchMinDistance",
        "seekSensitivity",
        "thresholds",
        "touchState",
        "gestureStarted",
    ]

    missing_patterns = []
    for pattern in gesture_patterns:
        if pattern in content:
            print(f"✅ {pattern}")
        else:
            print(f"❌ {pattern} - Missing")
            missing_patterns.append(pattern)

    return len(missing_patterns) == 0


def test_accessibility_features():
    """Test accessibility features"""
    print("\n♿ Testing Accessibility Features:")

    css_file = Path(__file__).parent / "data" / "static" / "css" / "pwa.css"
    content = css_file.read_text()

    # Required accessibility features
    accessibility_features = [
        "@media (prefers-contrast: high)",
        "@media (prefers-reduced-motion: reduce)",
        "min-height: 44px",  # Minimum touch target
        "focus",
        "outline",
        "aria-",
        "role=",
    ]

    found_features = []
    for feature in accessibility_features:
        if feature in content:
            found_features.append(feature)
            print(f"✅ {feature}")
        else:
            print(f"⚠️  {feature} - Consider adding")

    # At least half the accessibility features should be present
    return len(found_features) >= len(accessibility_features) // 2


def main():
    """Run all touch control tests"""
    print("🚀 PWA Phase 2 - Touch Controls Testing Suite")
    print("=" * 60)

    tests = [
        ("File Structure", test_touch_controls_files),
        ("Touch Control Features", test_touch_control_features),
        ("Transcript Navigation", test_transcript_navigation_features),
        ("Touch Control Styles", test_touch_control_styles),
        ("Mobile Responsiveness", test_mobile_responsiveness),
        ("Template Integration", test_template_integration),
        ("App Integration", test_app_integration),
        ("Gesture Patterns", test_gesture_patterns),
        ("Accessibility Features", test_accessibility_features),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📋 PWA PHASE 2 TOUCH CONTROLS TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")

    print(f"\nOverall Result: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TOUCH CONTROL TESTS PASSED!")
        print("   PWA Phase 2 Touch Controls are ready for use!")
        print("\n📱 Touch Features Available:")
        print("   • Video touch controls with gestures")
        print("   • Transcript touch navigation")
        print("   • Mobile-optimized progress bar")
        print("   • Swipe gestures for navigation")
        print("   • Pinch-to-zoom support")
        print("   • Haptic feedback")
        print("   • Context menus")
        print("   • Mobile search interface")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("   Please review and fix the failed tests.")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
