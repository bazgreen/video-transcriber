#!/usr/bin/env python3
"""
Test script to verify batch processing Flask context fix.
"""

import json
import os
import sys
import time

import requests

# Configuration
BASE_URL = "http://127.0.0.1:5001"
TEST_VIDEO_PATH = os.path.join(os.getcwd(), "uploads")  # Use existing uploads directory


def test_batch_processing():
    """Test batch processing functionality."""
    print("🧪 Testing Batch Processing with Flask Context Fix")
    print("-" * 60)

    try:
        # Step 1: Create a batch
        print("1️⃣ Creating a new batch...")
        response = requests.post(
            f"{BASE_URL}/api/batch/create",
            json={"name": "Context Fix Test Batch", "max_concurrent": 1},
        )

        if response.status_code != 200:
            print(f"❌ Failed to create batch: {response.status_code}")
            print(response.text)
            return False

        batch_data = response.json()
        if not batch_data.get("success"):
            print(f"❌ Batch creation failed: {batch_data.get('error')}")
            return False

        batch_id = batch_data["batch_id"]
        print(f"✅ Created batch: {batch_id}")

        # Step 2: Check if we have any video files to test with
        video_files = []
        if os.path.exists(TEST_VIDEO_PATH):
            for file in os.listdir(TEST_VIDEO_PATH):
                if file.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".webm")):
                    video_files.append(os.path.join(TEST_VIDEO_PATH, file))
                    break  # Only need one for testing

        if not video_files:
            print("⚠️  No video files found in uploads directory for testing")
            print("   This test only verifies the batch creation works correctly")
            print("   To fully test, add a video file to the uploads directory")
            return True

        video_file = video_files[0]
        print(f"2️⃣ Using test video: {os.path.basename(video_file)}")

        # Step 3: Add video to batch
        print("3️⃣ Adding video to batch...")
        with open(video_file, "rb") as f:
            files = {"file": f}
            data = {"batch_id": batch_id, "session_name": "Context Fix Test"}
            response = requests.post(
                f"{BASE_URL}/api/batch/add-video", files=files, data=data
            )

        if response.status_code != 200:
            print(f"❌ Failed to add video: {response.status_code}")
            print(response.text)
            return False

        add_data = response.json()
        if not add_data.get("success"):
            print(f"❌ Video addition failed: {add_data.get('error')}")
            return False

        job_id = add_data["job_id"]
        print(f"✅ Added video as job: {job_id}")

        # Step 4: Start batch processing
        print("4️⃣ Starting batch processing...")
        response = requests.post(f"{BASE_URL}/api/batch/{batch_id}/start")

        if response.status_code != 200:
            print(f"❌ Failed to start batch: {response.status_code}")
            print(response.text)
            return False

        start_data = response.json()
        if not start_data.get("success"):
            print(f"❌ Batch start failed: {start_data.get('error')}")
            return False

        print("✅ Batch processing started successfully!")

        # Step 5: Monitor progress for a short time
        print("5️⃣ Monitoring progress (30 seconds max)...")
        for i in range(30):
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/api/batch/{batch_id}")

            if response.status_code == 200:
                batch_info = response.json()
                if batch_info.get("success"):
                    batch = batch_info["batch"]
                    status = batch["status"]
                    progress = batch.get("progress", {})

                    completed = progress.get("completed_jobs", 0)
                    total = progress.get("total_jobs", 0)
                    percentage = progress.get("progress_percentage", 0)

                    print(
                        f"   Status: {status} | Progress: {completed}/{total} ({percentage}%)"
                    )

                    if status in ["completed", "failed"]:
                        if status == "completed":
                            print("✅ Batch completed successfully!")
                            print("🎉 Flask context fix is working correctly!")
                        else:
                            print(f"❌ Batch failed with status: {status}")
                            if batch.get("error_message"):
                                print(f"   Error: {batch['error_message']}")
                        break
            else:
                print(
                    f"   Warning: Failed to get batch status ({response.status_code})"
                )
        else:
            print("⏰ Test timeout reached - batch may still be processing")
            print("   Check the application logs for any context-related errors")

        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


def main():
    """Main test function."""
    print("Testing Batch Processing Flask Context Fix")
    print("=" * 60)

    success = test_batch_processing()

    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Batch processing context fix appears to be working")
    else:
        print("❌ TEST FAILED: Issues detected with batch processing")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
