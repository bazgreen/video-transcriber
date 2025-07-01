#!/usr/bin/env python3
"""
Test script for enhanced export API endpoints.
Tests the new export format capabilities without requiring a full transcription.
"""

import sys
from pathlib import Path

import pytest
import requests


def test_export_endpoints():
    """Test the enhanced export API endpoints"""
    base_url = "http://localhost:5000"

    print("🧪 Testing Enhanced Export API Endpoints...")
    print("-" * 50)

    # Skip if server not running
    try:
        response = requests.get(f"{base_url}/api/export/formats", timeout=1)
    except (requests.ConnectionError, requests.Timeout):
        pytest.skip("Server not running - integration test requires running server")

    # Test 1: Get available export formats
    print("1. Testing export formats endpoint...")
    assert (
        response.status_code == 200
    ), f"Export formats endpoint failed with status {response.status_code}"

    data = response.json()
    assert data.get(
        "success"
    ), f"API returned error: {data.get('error', 'Unknown error')}"

    assert "formats" in data, "Response missing 'formats' key"

    print("✅ Export formats endpoint working")
    print("📋 Available formats:")
    for format_name, info in data["formats"].items():
        status = "✅" if info["available"] else "❌"
        print(f"   {status} {format_name}: {info['description']}")

    # Assert that core formats are present
    expected_formats = ["srt", "vtt", "enhanced_txt", "json", "html"]
    for fmt in expected_formats:
        assert (
            fmt in data["formats"]
        ), f"Required format '{fmt}' missing from API response"

    print()

    # Test 2: Look for an existing session to test download endpoints
    print("2. Looking for existing sessions...")
    results_folder = Path("results")

    if not results_folder.exists():
        print(
            "❌ No results folder found. Run a transcription first to test "
            "download endpoints."
        )
        return

    sessions = [d for d in results_folder.iterdir() if d.is_dir()]
    if not sessions:
        print(
            "❌ No sessions found. Run a transcription first to test download endpoints."
        )
        return

    # Use the most recent session
    test_session = max(sessions, key=lambda x: x.stat().st_mtime)
    session_id = test_session.name
    print(f"📁 Using session: {session_id}")

    # Test 3: Test individual format downloads
    print("\n3. Testing individual format downloads...")
    formats_to_test = ["srt", "vtt", "enhanced_txt", "pdf", "docx", "json", "html"]

    download_results = {}
    for format_name in formats_to_test:
        print(f"   Testing {format_name} download...")
        try:
            response = requests.get(f"{base_url}/api/export/{session_id}/{format_name}")
            download_results[format_name] = response.status_code
            if response.status_code == 200:
                print(
                    f"   ✅ {format_name} download successful "
                    f"({len(response.content)} bytes)"
                )
            elif response.status_code == 404:
                print(f"   ⚠️  {format_name} file not found (may need to be generated)")
            else:
                print(f"   ❌ {format_name} failed: HTTP {response.status_code}")
        except requests.RequestException as e:
            print(f"   ❌ {format_name} request failed: {e}")
            download_results[format_name] = "error"

    # Assert that at least basic formats are testable
    assert any(
        download_results[fmt] in [200, 404] for fmt in ["srt", "vtt", "enhanced_txt"]
    ), "Basic export formats should be accessible via API"

    # Test 4: Test export generation
    print("\n4. Testing export generation...")
    try:
        export_options = {
            "formats": {
                "srt": True,
                "vtt": True,
                "enhanced_txt": True,
                "pdf": True,  # Will work if reportlab is installed
                "docx": True,  # Will work if python-docx is installed
            }
        }

        response = requests.post(
            f"{base_url}/api/export/{session_id}/generate",
            json=export_options,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200, (
            f"Export generation failed with status {response.status_code}: "
            f"{response.text}"
        )

        data = response.json()
        assert data.get(
            "success"
        ), f"Export generation failed: {data.get('error', 'Unknown error')}"
        assert "exported_files" in data, "Response missing 'exported_files' key"

        print("✅ Export generation successful")
        print(f"📦 Generated files: {', '.join(data.get('exported_files', {}).keys())}")

        # Assert that at least some files were generated
        assert (
            len(data.get("exported_files", {})) > 0
        ), "No files were generated during export"

    except requests.RequestException as e:
        print(f"❌ Export generation request failed: {e}")
        raise AssertionError(f"Failed to connect to export generation endpoint: {e}")

    print("\n" + "=" * 50)
    print("🏁 Export API testing complete!")
    print("\n💡 Tips:")
    print("   • Install reportlab for PDF exports: pip install reportlab")
    print("   • Install python-docx for DOCX exports: pip install python-docx")
    print("   • SRT, VTT, and enhanced text work without additional dependencies")


def main():
    """Main test function"""
    print("🚀 Enhanced Export API Test Suite")
    print("=" * 50)

    # Check if server is running
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️  Server returned HTTP {response.status_code}")
    except requests.RequestException:
        print("❌ Server is not running. Start the application first with:")
        print("   python app.py")
        sys.exit(1)

    print()
    test_export_endpoints()


if __name__ == "__main__":
    main()
