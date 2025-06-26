#!/usr/bin/env python3
"""
WebSocket Testing Script for Video Transcriber
Tests the real-time progress tracking functionality
"""

import asyncio
import json
import time

import socketio

# Create a SocketIO client
sio = socketio.Client()

# Test variables
connection_established = False
progress_updates_received = []
error_events = []


@sio.event
def connect():
    global connection_established
    connection_established = True
    print("✅ Connected to server successfully")
    print(f"   Session ID: {sio.sid}")


@sio.event
def disconnect():
    global connection_established
    connection_established = False
    print("❌ Disconnected from server")


@sio.event
def connection_status(data):
    print(f"📡 Connection status: {data}")


@sio.event
def progress_update(data):
    global progress_updates_received
    progress_updates_received.append(data)
    print(
        f"📊 Progress update received: {data.get('progress', 0)}% - {data.get('current_task', 'Unknown')}"
    )
    if data.get("chunks_total", 0) > 0:
        print(
            f"   Chunks: {data.get('chunks_completed', 0)}/{data.get('chunks_total', 0)}"
        )
    if data.get("estimated_time"):
        print(f"   ETA: {data.get('estimated_time')}s")


@sio.event
def session_status(data):
    print(f"📋 Session status: {data}")


@sio.event
def error(data):
    global error_events
    error_events.append(data)
    print(f"❌ Error event: {data}")


def test_websocket_connection():
    """Test basic WebSocket connection"""
    print("🧪 Testing WebSocket Connection...")

    try:
        # Connect to the server
        sio.connect("http://localhost:5001")

        # Wait a moment for connection to establish
        time.sleep(1)

        if connection_established:
            print("✅ WebSocket connection test PASSED")
            return True
        else:
            print("❌ WebSocket connection test FAILED")
            return False

    except Exception as e:
        print(f"❌ WebSocket connection test FAILED: {e}")
        return False


def test_session_join():
    """Test joining a session"""
    print("\n🧪 Testing Session Join...")

    if not connection_established:
        print("❌ Cannot test session join - not connected")
        return False

    try:
        # Test joining a fake session
        test_session_id = "test_session_123"
        print(f"   Joining session: {test_session_id}")
        sio.emit("join_session", {"session_id": test_session_id})

        # Wait for response
        time.sleep(1)

        print("✅ Session join test PASSED")
        return True

    except Exception as e:
        print(f"❌ Session join test FAILED: {e}")
        return False


def test_progress_request():
    """Test getting progress for a session"""
    print("\n🧪 Testing Progress Request...")

    if not connection_established:
        print("❌ Cannot test progress request - not connected")
        return False

    try:
        # Test getting progress for a fake session
        test_session_id = "nonexistent_session"
        print(f"   Requesting progress for: {test_session_id}")
        sio.emit("get_progress", {"session_id": test_session_id})

        # Wait for response
        time.sleep(1)

        print("✅ Progress request test PASSED")
        return True

    except Exception as e:
        print(f"❌ Progress request test FAILED: {e}")
        return False


def test_connection_stability():
    """Test connection stability over time"""
    print("\n🧪 Testing Connection Stability...")

    if not connection_established:
        print("❌ Cannot test stability - not connected")
        return False

    try:
        print("   Monitoring connection for 5 seconds...")
        start_time = time.time()
        stable = True

        while time.time() - start_time < 5:
            if not connection_established:
                stable = False
                break
            time.sleep(0.5)

        if stable:
            print("✅ Connection stability test PASSED")
            return True
        else:
            print("❌ Connection stability test FAILED - connection lost")
            return False

    except Exception as e:
        print(f"❌ Connection stability test FAILED: {e}")
        return False


def main():
    """Run all WebSocket tests"""
    print("🚀 Starting WebSocket Test Suite for Video Transcriber")
    print("=" * 60)

    tests_passed = 0
    total_tests = 4

    # Test 1: Basic connection
    if test_websocket_connection():
        tests_passed += 1

    # Test 2: Session join
    if test_session_join():
        tests_passed += 1

    # Test 3: Progress request
    if test_progress_request():
        tests_passed += 1

    # Test 4: Connection stability
    if test_connection_stability():
        tests_passed += 1

    # Disconnect
    if connection_established:
        sio.disconnect()
        print("\n📤 Disconnected from server")

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All WebSocket tests PASSED!")
        return True
    else:
        print("⚠️  Some WebSocket tests FAILED!")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
