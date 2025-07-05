#!/usr/bin/env python3
"""
Test script for the synchronized video player API endpoints.

This script tests the video streaming infrastructure to ensure it's working properly.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_api_endpoint(base_url: str, endpoint: str) -> bool:
    """Test a specific API endpoint."""
    try:
        url = f"{base_url}{endpoint}"
        logger.info(f"Testing endpoint: {url}")

        response = requests.get(url, timeout=10)
        logger.info(f"Response status: {response.status_code}")

        if response.status_code == 200:
            if endpoint.endswith("/metadata"):
                data = response.json()
                logger.info(f"Metadata response: {json.dumps(data, indent=2)[:200]}...")
            return True
        else:
            logger.warning(f"Endpoint returned status {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Error testing endpoint {endpoint}: {e}")
        return False


def find_test_session(base_url: str) -> str:
    """Find a test session to use for video player testing."""
    try:
        # Try to get sessions from the sessions page
        response = requests.get(f"{base_url}/sessions", timeout=10)
        if response.status_code == 200:
            # Parse HTML to find session IDs (simple approach)
            content = response.text
            if "session_id" in content:
                # Look for session IDs in the HTML
                import re

                pattern = r"/results/([a-zA-Z0-9_-]+)"
                matches = re.findall(pattern, content)
                if matches:
                    return matches[0]

        # Alternative: check for any session directories
        # This would require filesystem access which we don't have via API

    except Exception as e:
        logger.error(f"Error finding test session: {e}")

    return None


def test_video_endpoints(base_url: str = "http://localhost:5000") -> Dict[str, bool]:
    """Test all video-related API endpoints."""
    results = {}

    # Test basic API health
    results["api_health"] = test_api_endpoint(base_url, "/api/keywords")

    # Find a test session
    test_session = find_test_session(base_url)

    if test_session:
        logger.info(f"Using test session: {test_session}")

        # Test video metadata endpoint
        results["video_metadata"] = test_api_endpoint(
            base_url, f"/api/video/{test_session}/metadata"
        )

        # Test video streaming endpoint (just check if it responds)
        results["video_stream"] = test_api_endpoint(
            base_url, f"/api/video/{test_session}"
        )

        # Test results page with video player
        results["results_page"] = test_api_endpoint(
            base_url, f"/results/{test_session}"
        )

    else:
        logger.warning(
            "No test session found. Create a session first to test video endpoints."
        )
        results["video_metadata"] = False
        results["video_stream"] = False
        results["results_page"] = False

    return results


def main():
    """Main test function."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"

    logger.info(f"Testing video player integration at: {base_url}")

    results = test_video_endpoints(base_url)

    print("\n" + "=" * 50)
    print("VIDEO PLAYER API TEST RESULTS")
    print("=" * 50)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())

    print(f"\nPassed: {passed_tests}/{total_tests}")

    if passed_tests == total_tests:
        print("🎉 All tests passed! Video player integration is working.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
