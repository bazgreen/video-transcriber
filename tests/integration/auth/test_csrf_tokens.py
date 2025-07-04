#!/usr/bin/env python3
"""
Test CSRF token generation and session handling.
"""

import re
from urllib.parse import urljoin

import requests


def test_csrf_tokens(base_url="http://localhost:5001"):
    """Test CSRF token generation and usage."""
    print("🔒 Testing CSRF Token Handling")
    print("=" * 40)

    session = requests.Session()

    # Test 1: Get login page and check for CSRF token
    print("1️⃣  Testing login page CSRF token...")
    try:
        response = session.get(urljoin(base_url, "/auth/login"))
        if response.status_code == 200:
            # Look for CSRF token in HTML
            csrf_match = re.search(
                r'name="csrf_token".*?value="([^"]+)"', response.text
            )
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"   ✅ CSRF token found: {csrf_token[:20]}...")

                # Test 2: Submit form with CSRF token
                print("2️⃣  Testing form submission with CSRF token...")

                login_data = {
                    "csrf_token": csrf_token,
                    "username": "testuser",
                    "password": "wrongpassword",
                    "submit": "Sign In",
                }

                response = session.post(
                    urljoin(base_url, "/auth/login"), data=login_data
                )

                if response.status_code == 200:
                    if "Invalid username" in response.text:
                        print("   ✅ Form processed (invalid credentials as expected)")
                    elif (
                        "token" in response.text.lower()
                        and "expired" in response.text.lower()
                    ):
                        print("   ⚠️  CSRF token issue detected")
                    else:
                        print("   ✅ Form submitted successfully")
                elif response.status_code == 400:
                    print("   ❌ CSRF token validation failed (400 error)")
                    if "missing" in response.text.lower():
                        print("       → CSRF token missing from session")
                    elif "expired" in response.text.lower():
                        print("       → CSRF token expired")
                else:
                    print(f"   ⚠️  Unexpected response: {response.status_code}")

                # Test 3: Submit form without CSRF token
                print("3️⃣  Testing form submission without CSRF token...")

                login_data_no_csrf = {
                    "username": "testuser",
                    "password": "wrongpassword",
                    "submit": "Sign In",
                }

                response = session.post(
                    urljoin(base_url, "/auth/login"), data=login_data_no_csrf
                )

                if response.status_code == 400:
                    print("   ✅ CSRF protection working (400 error for missing token)")
                elif response.status_code == 200 and "token" in response.text.lower():
                    print("   ✅ CSRF protection working (error message displayed)")
                else:
                    print(
                        f"   ⚠️  CSRF protection may not be working: {response.status_code}"
                    )

            else:
                print("   ❌ CSRF token not found in login form")
        else:
            print(f"   ❌ Login page failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ CSRF test error: {e}")

    # Test 4: Check session cookies
    print("4️⃣  Testing session cookies...")
    try:
        cookies = session.cookies
        session_cookie = None
        for cookie in cookies:
            if "session" in cookie.name.lower():
                session_cookie = cookie
                break

        if session_cookie:
            print(f"   ✅ Session cookie found: {session_cookie.name}")
        else:
            print("   ⚠️  No session cookie found")
            print(f"   Available cookies: {[c.name for c in cookies]}")
    except Exception as e:
        print(f"   ❌ Cookie test error: {e}")

    print("\n🎯 CSRF Token Test Summary:")
    print("   If CSRF errors persist, try:")
    print("   1. Clear browser cookies and refresh")
    print("   2. Restart the application")
    print("   3. Use a fresh browser session")


if __name__ == "__main__":
    test_csrf_tokens()
