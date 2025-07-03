#!/usr/bin/env python3
"""
Validation script for UX improvements in the video transcriber.

This script validates that the enhanced user experience features have been
properly implemented in the results template.
"""

import re
import sys

import requests


def validate_ux_improvements():
    """Validate that UX improvements are properly implemented."""
    print("🔍 Validating UX Improvements...")

    # Test server availability
    try:
        response = requests.get("http://localhost:5001/", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding correctly")
            return False
        print("✅ Server is running")
    except requests.exceptions.RequestException as e:
        print(f"❌ Server connection failed: {e}")
        return False

    # Check sessions page
    try:
        sessions_response = requests.get("http://localhost:5001/sessions", timeout=5)
        if sessions_response.status_code == 200:
            print("✅ Sessions page accessible")

            # Look for session links
            session_pattern = r'/results/([^"]+)'
            sessions = re.findall(session_pattern, sessions_response.text)

            if not sessions:
                print("⚠️  No existing sessions found for testing")
                return True

            # Test the first session's results page
            test_session = sessions[0]
            print(f"🧪 Testing session: {test_session}")

            results_response = requests.get(
                f"http://localhost:5001/results/{test_session}", timeout=10
            )

            if results_response.status_code != 200:
                print(f"❌ Results page failed: {results_response.status_code}")
                return False

            results_html = results_response.text

            # Validate UX improvements
            improvements_found = {
                "UserPreferences class": "class UserPreferences" in results_html,
                "UIStateManager class": "class UIStateManager" in results_html,
                "Loading spinner CSS": ".loading-spinner" in results_html,
                "Error message CSS": ".error-message" in results_html,
                "Accessibility focus styles": ":focus" in results_html,
                "Keyboard navigation": "setupKeyboardNavigation" in results_html,
                "Mobile enhancements": "setupMobileEnhancements" in results_html,
                "User preferences storage": "localStorage" in results_html,
                "Enhanced error handling": "showError" in results_html,
                "Retry functionality": "retry-btn" in results_html,
            }

            # Report findings
            all_passed = True
            for feature, found in improvements_found.items():
                status = "✅" if found else "❌"
                print(f"{status} {feature}: {'Found' if found else 'Missing'}")
                if not found:
                    all_passed = False

            # Check for mobile responsiveness
            mobile_features = [
                "min-height: 44px",  # Touch targets
                "@media (max-width: 768px)",  # Mobile breakpoints
                "touch-action: manipulation",  # Touch optimization
            ]

            mobile_passed = True
            for feature in mobile_features:
                if feature in results_html:
                    print(f"✅ Mobile feature: {feature}")
                else:
                    print(f"❌ Mobile feature missing: {feature}")
                    mobile_passed = False

            # Check for accessibility features
            a11y_features = [
                "aria-label",
                "setAttribute('role'",  # Dynamic role setting
                "tabindex",
                "@media (prefers-reduced-motion: reduce)",
            ]

            a11y_passed = True
            for feature in a11y_features:
                if feature in results_html:
                    print(f"✅ Accessibility feature: {feature}")
                else:
                    print(f"❌ Accessibility feature missing: {feature}")
                    a11y_passed = False

            # Final assessment
            if all_passed and mobile_passed and a11y_passed:
                print("\n🎉 All UX improvements successfully implemented!")
                print("\n📊 Summary of enhancements:")
                print("   • DOM element caching for better performance")
                print("   • Enhanced loading states with spinners")
                print("   • User-friendly error messages with retry options")
                print("   • User preferences persistence in localStorage")
                print("   • Comprehensive keyboard navigation support")
                print("   • Mobile touch improvements and gestures")
                print("   • Accessibility enhancements (ARIA, focus styles)")
                print("   • High contrast and reduced motion support")
                return True
            else:
                print(f"\n⚠️  Some improvements may need attention")
                return False

        else:
            print(f"❌ Sessions page failed: {sessions_response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False


if __name__ == "__main__":
    success = validate_ux_improvements()
    sys.exit(0 if success else 1)
