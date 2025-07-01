#!/usr/bin/env python3
"""
Test script for performance optimization endpoints.
"""

import json
import sys
from time import sleep

import pytest
import requests

BASE_URL = "http://localhost:5000"


def test_performance_endpoints():
    """Test performance API endpoints"""
    endpoints = [
        ("/api/system/status", "GET"),
        ("/api/performance", "GET"),
        ("/api/performance/optimization", "GET"),
        ("/api/performance/optimize", "POST", {"force_memory_cleanup": False}),
    ]

    # Skip if server not running
    try:
        requests.get(f"{BASE_URL}/api/system/status", timeout=1)
    except (requests.ConnectionError, requests.Timeout):
        pytest.skip("Server not running - integration test requires running server")

    success_count = 0
    for endpoint_data in endpoints:
        endpoint = endpoint_data[0]
        method = endpoint_data[1]
        data = endpoint_data[2] if len(endpoint_data) > 2 else None

        if _test_endpoint(endpoint, method, data):
            success_count += 1

    assert (
        success_count >= len(endpoints) // 2
    ), f"Only {success_count}/{len(endpoints)} endpoints working"


def _test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=data, timeout=5)

        return response.status_code == 200

    except (requests.ConnectionError, requests.Timeout):
        return False
    except Exception:
        return False


if __name__ == "__main__":
    # Run as standalone script
    from unittest import main as unittest_main

    unittest_main()
