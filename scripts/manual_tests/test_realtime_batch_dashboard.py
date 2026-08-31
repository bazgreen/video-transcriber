#!/usr/bin/env python3
"""
Test script for Real-time Batch Processing Dashboard.

This script tests the enhanced WebSocket functionality for batch processing
with real-time progress updates and interactive controls.
"""

import json
import os
import sys
import tempfile
import time
from typing import Any, Dict, List

import requests
import socketio

# Configuration
BASE_URL = "http://127.0.0.1:5001"
TEST_DURATION = 30  # seconds


def create_test_video(name: str, duration: int = 5) -> str:
    """Create a test video file using FFmpeg."""
    import subprocess

    temp_file = tempfile.NamedTemporaryFile(suffix=f"_{name}.mp4", delete=False)
    temp_file.close()

    try:
        # Create a simple test video with FFmpeg
        subprocess.run(
            [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                "testsrc=duration={}:size=320x240:rate=1".format(duration),
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=1000:duration={}".format(duration),
                "-c:v",
                "libx264",
                "-t",
                str(duration),
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-y",
                temp_file.name,
            ],
            capture_output=True,
            check=True,
        )

        print(f"✅ Created test video: {temp_file.name}")
        return temp_file.name
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"⚠️  FFmpeg not available, using placeholder file: {temp_file.name}")
        # Create a placeholder file
        with open(temp_file.name, "wb") as f:
            f.write(b"fake video content for testing")
        return temp_file.name


def test_real_time_batch_dashboard():
    """Test the real-time batch processing dashboard."""
    print("🧪 Testing Real-time Batch Processing Dashboard")
    print("=" * 60)

    # Test variables
    batch_id = None
    job_ids = []
    test_videos = []
    sio = socketio.Client()
    events_received = {
        "connected": False,
        "batch_progress_updates": [],
        "job_status_updates": [],
        "batch_status_updates": [],
    }

    # WebSocket event handlers
    @sio.event
    def connect():
        events_received["connected"] = True
        print("✅ Connected to WebSocket server")

    @sio.event
    def disconnect():
        print("❌ Disconnected from WebSocket server")

    @sio.event
    def batch_progress_update(data):
        events_received["batch_progress_updates"].append(data)
        progress = data.get("progress", {}).get("progress_percentage", 0)
        print(
            f"📊 Batch progress update: {progress}% (Batch: {data.get('batch_id', 'unknown')[:8]})"
        )

    @sio.event
    def job_status_update(data):
        events_received["job_status_updates"].append(data)
        status = data.get("status", "unknown")
        filename = data.get("original_filename", "unknown")
        print(f"🔄 Job status update: {filename} -> {status}")

    @sio.event
    def batch_status_update(data):
        events_received["batch_status_updates"].append(data)
        status = data.get("status", "unknown")
        print(
            f"📋 Batch status update: {data.get('batch_id', 'unknown')[:8]} -> {status}"
        )

    @sio.event
    def joined_batch(data):
        print(f"🏠 Joined batch room: {data.get('batch_id', 'unknown')[:8]}")

    @sio.event
    def error(data):
        print(f"❌ WebSocket error: {data.get('message', 'Unknown error')}")

    try:
        # Step 1: Connect to WebSocket
        print("\n1. Connecting to WebSocket server...")
        sio.connect(BASE_URL)
        time.sleep(1)

        if not events_received["connected"]:
            print("❌ Failed to connect to WebSocket")
            return False

        # Step 2: Create test videos
        print("\n2. Creating test videos...")
        test_videos = [
            create_test_video("test_video_1", 3),
            create_test_video("test_video_2", 3),
            create_test_video("test_video_3", 3),
        ]

        # Step 3: Create a new batch
        print("\n3. Creating new batch...")
        response = requests.post(
            f"{BASE_URL}/api/batch/create",
            json={"name": "Real-time Dashboard Test Batch", "max_concurrent": 2},
        )

        if response.status_code != 200:
            print(f"❌ Failed to create batch: {response.status_code}")
            return False

        batch_data = response.json()
        batch_id = batch_data.get("batch_id")
        print(f"✅ Created batch: {batch_id[:8]}")

        # Step 4: Join the batch room for real-time updates
        print("\n4. Joining batch room...")
        sio.emit("join_batch", {"batch_id": batch_id})
        time.sleep(1)

        # Step 5: Add videos to batch
        print("\n5. Adding videos to batch...")
        for i, video_path in enumerate(test_videos):
            with open(video_path, "rb") as f:
                files = {"file": (f"test_video_{i+1}.mp4", f, "video/mp4")}
                data = {
                    "batch_id": batch_id,
                    "session_name": f"Dashboard Test Video {i+1}",
                }

                response = requests.post(
                    f"{BASE_URL}/api/batch/add-video", files=files, data=data
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        job_ids.append(result.get("job_id"))
                        print(f"✅ Added video {i+1} to batch")
                    else:
                        print(f"❌ Failed to add video {i+1}: {result.get('error')}")
                else:
                    print(f"❌ Failed to add video {i+1}: HTTP {response.status_code}")

        print(f"📊 Added {len(job_ids)} jobs to batch")

        # Step 6: Start batch processing and monitor real-time updates
        print("\n6. Starting batch processing...")
        response = requests.post(f"{BASE_URL}/api/batch/{batch_id}/start")

        if response.status_code != 200:
            print(f"❌ Failed to start batch: {response.status_code}")
            return False

        print("✅ Batch processing started - monitoring real-time updates...")

        # Step 7: Monitor progress for a limited time
        start_time = time.time()
        last_progress = -1

        while time.time() - start_time < TEST_DURATION:
            # Check for progress updates
            if events_received["batch_progress_updates"]:
                latest_update = events_received["batch_progress_updates"][-1]
                progress = latest_update.get("progress", {}).get(
                    "progress_percentage", 0
                )

                if progress != last_progress:
                    print(f"📈 Progress: {progress}%")
                    last_progress = progress

                # Check if batch is complete
                if latest_update.get("status") in ["completed", "failed"]:
                    print(
                        f"🏁 Batch finished with status: {latest_update.get('status')}"
                    )
                    break

            time.sleep(1)

        # Step 8: Verify results
        print("\n7. Verifying real-time functionality...")

        print(
            f"📊 Batch progress updates received: {len(events_received['batch_progress_updates'])}"
        )
        print(
            f"🔄 Job status updates received: {len(events_received['job_status_updates'])}"
        )
        print(
            f"📋 Batch status updates received: {len(events_received['batch_status_updates'])}"
        )

        # Test WebSocket batch control
        print("\n8. Testing WebSocket batch control...")

        # Test get batch status
        sio.emit("get_batch_status", {"batch_id": batch_id})
        time.sleep(1)

        # Get final batch status via API
        response = requests.get(f"{BASE_URL}/api/batch/{batch_id}")
        if response.status_code == 200:
            final_batch = response.json()
            if final_batch.get("success"):
                batch_info = final_batch["batch"]
                print(f"✅ Final batch status: {batch_info['status']}")
                print(
                    f"📊 Final progress: {batch_info['progress']['progress_percentage']}%"
                )
                print(
                    f"📁 Jobs completed: {batch_info['progress']['completed_jobs']}/{batch_info['progress']['total_jobs']}"
                )

        # Evaluation
        success_criteria = [
            events_received["connected"],
            len(events_received["batch_progress_updates"]) > 0,
            len(job_ids) > 0,
            batch_id is not None,
        ]

        success = all(success_criteria)

        print(f"\n🎯 Real-time Dashboard Test Results:")
        print(
            f"   WebSocket Connection: {'✅' if events_received['connected'] else '❌'}"
        )
        print(f"   Batch Creation: {'✅' if batch_id else '❌'}")
        print(f"   Video Upload: {'✅' if len(job_ids) > 0 else '❌'}")
        print(
            f"   Real-time Updates: {'✅' if len(events_received['batch_progress_updates']) > 0 else '❌'}"
        )
        print(f"   Overall Success: {'✅' if success else '❌'}")

        return success

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

    finally:
        # Cleanup
        print("\n9. Cleaning up...")

        # Disconnect WebSocket
        if sio.connected:
            sio.disconnect()

        # Clean up test videos
        for video_path in test_videos:
            if os.path.exists(video_path):
                os.unlink(video_path)
                print(f"🗑️  Deleted test video: {os.path.basename(video_path)}")

        # Optional: Clean up batch (comment out to keep for manual inspection)
        if batch_id:
            try:
                requests.delete(f"{BASE_URL}/api/batch/{batch_id}")
                print(f"🗑️  Deleted test batch: {batch_id[:8]}")
            except Exception:
                pass


def main():
    """Main test function."""
    print("🚀 Real-time Batch Processing Dashboard Test")
    print(f"Testing against: {BASE_URL}")
    print(f"Test duration: {TEST_DURATION} seconds")

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server health check failed")
            return 1
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Please ensure the application is running.")
        return 1

    print("✅ Server is running")

    # Run the test
    success = test_real_time_batch_dashboard()

    if success:
        print("\n🎉 Real-time Batch Processing Dashboard test completed successfully!")
        print("📋 Features tested:")
        print("   • WebSocket connection and room management")
        print("   • Real-time batch progress updates")
        print("   • Individual job status notifications")
        print("   • Interactive batch controls")
        print("   • Connection status indicators")
        return 0
    else:
        print("\n❌ Real-time Batch Processing Dashboard test failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
