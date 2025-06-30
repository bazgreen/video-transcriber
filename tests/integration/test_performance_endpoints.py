#!/usr/bin/env python3
"""
Test script for performance optimization endpoints.
"""

import json
import sys
from time import sleep

import requests

BASE_URL = "http://localhost:5000"


def test_endpoint(endpoint, method="GET", data=None):
    """Test an API endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=data)

        print(f"✅ {method} {endpoint}: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            if "recommendations" in result:
                print(f"   Recommendations: {len(result['recommendations'])}")
            if "optimal_workers" in result:
                print(f"   Optimal workers: {result['optimal_workers']}")
            if "performance_summary" in result:
                print(f"   Summary: {result['performance_summary']}")
        else:
            print(f"   Error: {response.text}")

        return response.status_code == 200

    except requests.ConnectionError:
        print(f"❌ {method} {endpoint}: Connection failed (server not running)")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint}: {e}")
        return False


def main():
    """Test performance endpoints"""
    print("🧪 Testing Performance Optimization Endpoints")
    print("=" * 50)

    # Test basic endpoints
    endpoints = [
        ("/api/system/status", "GET"),
        ("/api/performance", "GET"),
        ("/api/performance/optimization", "GET"),
        ("/api/performance/optimize", "POST", {"force_memory_cleanup": False}),
    ]

    success_count = 0
    for endpoint_data in endpoints:
        endpoint = endpoint_data[0]
        method = endpoint_data[1]
        data = endpoint_data[2] if len(endpoint_data) > 2 else None

        if test_endpoint(endpoint, method, data):
            success_count += 1

        sleep(0.5)  # Small delay between requests

    print("=" * 50)
    print(f"📊 Results: {success_count}/{len(endpoints)} endpoints working")

    if success_count == 0:
        print("💡 Start the server with: python app.py")
        sys.exit(1)
    elif success_count < len(endpoints):
        print("⚠️  Some endpoints failed - check server logs")
        sys.exit(1)
    else:
        print("🎉 All performance endpoints working correctly!")


if __name__ == "__main__":
    main()
