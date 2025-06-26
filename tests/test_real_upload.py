#!/usr/bin/env python3
"""
Real Upload Test - Tests actual video upload with progress tracking
"""

import os
import subprocess
import tempfile
import time
from datetime import datetime

import requests
import socketio

# Create a SocketIO client
sio = socketio.Client()

# Test variables
connection_established = False
progress_updates = []
upload_session_id = None


@sio.event
def connect():
    global connection_established
    connection_established = True
    print("✅ Connected to server for real upload test")


@sio.event
def disconnect():
    global connection_established
    connection_established = False
    print("❌ Disconnected from server")


@sio.event
def progress_update(data):
    global progress_updates
    progress_updates.append({"timestamp": datetime.now().isoformat(), "data": data})

    # Print progress information
    progress = data.get("progress", 0)
    task = data.get("current_task", "Unknown task")
    stage = data.get("stage", "unknown")
    chunks_completed = data.get("chunks_completed", 0)
    chunks_total = data.get("chunks_total", 0)
    estimated_time = data.get("estimated_time")

    print(f"📊 {progress:.1f}% | {stage} | {task}")
    if chunks_total > 0:
        print(f"   📦 Chunks: {chunks_completed}/{chunks_total}")
    if estimated_time:
        print(f"   ⏱️  ETA: {estimated_time:.1f}s")

    if data.get("status") == "completed":
        print("🎉 Processing completed!")
    elif data.get("status") == "error":
        print(f"❌ Processing failed: {task}")


def create_test_video():
    """Create a small test video file using ffmpeg"""
    print("🎬 Creating test video file...")

    try:
        # Create a temporary video file (5 seconds, simple pattern)
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_file.close()

        # Use ffmpeg to create a longer test video with audio tone (30 seconds to get multiple chunks)
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=duration=30:size=320x240:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=30",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            "-shortest",
            temp_file.name,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Test video created: {temp_file.name}")
            print(f"   Size: {os.path.getsize(temp_file.name)} bytes")
            return temp_file.name
        else:
            print(f"❌ Failed to create test video: {result.stderr}")
            return None

    except FileNotFoundError:
        print("❌ ffmpeg not found. Cannot create test video.")
        return None
    except Exception as e:
        print(f"❌ Error creating test video: {e}")
        return None


def test_real_upload_with_progress():
    """Test real video upload with progress tracking"""
    print("🧪 Testing Real Video Upload with Progress Tracking...")

    global upload_session_id

    try:
        # Connect to server
        sio.connect("http://localhost:5001")
        time.sleep(1)

        if not connection_established:
            print("❌ Failed to connect to server")
            return False

        # Create a test video
        video_path = create_test_video()
        if not video_path:
            print("❌ Cannot proceed without test video")
            return False

        try:
            # Pre-generate session ID and join before upload
            session_name = "test_progress_session"
            expected_session_id = (
                f"{session_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # Join the session preemptively
            print(f"🔗 Pre-joining session: {expected_session_id}")
            sio.emit("join_session", {"session_id": expected_session_id})
            time.sleep(0.5)  # Give time for join to complete

            # Upload the video
            print("📤 Uploading test video...")

            with open(video_path, "rb") as video_file:
                files = {"video": video_file}
                data = {"session_name": session_name}

                response = requests.post(
                    "http://localhost:5001/upload", files=files, data=data
                )

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    upload_session_id = result.get("session_id")
                    print(f"✅ Upload successful! Session ID: {upload_session_id}")

                    # Double-check we're in the right session
                    if upload_session_id != expected_session_id:
                        print(f"🔄 Re-joining actual session: {upload_session_id}")
                        sio.emit("join_session", {"session_id": upload_session_id})

                    # Monitor progress for up to 60 seconds
                    print("📡 Monitoring progress...")
                    start_time = time.time()
                    last_progress = -1

                    while time.time() - start_time < 60:
                        time.sleep(1)

                        if len(progress_updates) > 0:
                            latest_update = progress_updates[-1]["data"]
                            current_progress = latest_update.get("progress", 0)

                            # Check if progress is advancing
                            if current_progress > last_progress:
                                last_progress = current_progress

                            # Check if completed
                            if latest_update.get("status") == "completed":
                                print("✅ Processing completed successfully!")
                                break
                            elif latest_update.get("status") == "error":
                                print("❌ Processing failed!")
                                return False

                    # Analyze results
                    print(f"\n📈 Analysis:")
                    print(f"   Total progress updates: {len(progress_updates)}")
                    print(f"   Final progress: {last_progress:.1f}%")

                    if len(progress_updates) > 5 and last_progress >= 90:
                        print("✅ Real upload with progress tracking PASSED")
                        return True
                    else:
                        print(
                            "❌ Insufficient progress updates or incomplete processing"
                        )
                        return False

                else:
                    print(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Upload request failed: {response.status_code}")
                return False

        finally:
            # Clean up test video
            if video_path and os.path.exists(video_path):
                os.unlink(video_path)
                print("🗑️  Test video cleaned up")

    except Exception as e:
        print(f"❌ Real upload test failed: {e}")
        return False
    finally:
        if connection_established:
            sio.disconnect()


def main():
    """Run real upload test"""
    print("🚀 Starting Real Upload Progress Tracking Test")
    print("=" * 60)

    success = test_real_upload_with_progress()

    print("\n" + "=" * 60)
    if success:
        print("🎉 Real upload progress tracking test PASSED!")
        return True
    else:
        print("⚠️  Real upload progress tracking test FAILED!")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
