#!/usr/bin/env python3
"""
Progress Tracking Test Script
Tests real-time progress updates during simulated video processing
"""

import socketio
import time
import threading
import requests
from datetime import datetime

# Create a SocketIO client
sio = socketio.Client()

# Test variables
connection_established = False
progress_updates = []
session_id = None

@sio.event
def connect():
    global connection_established
    connection_established = True
    print("✅ Connected to server for progress testing")

@sio.event
def disconnect():
    global connection_established
    connection_established = False
    print("❌ Disconnected from server")

@sio.event
def progress_update(data):
    global progress_updates
    progress_updates.append({
        'timestamp': datetime.now().isoformat(),
        'data': data
    })
    
    # Print detailed progress information
    progress = data.get('progress', 0)
    task = data.get('current_task', 'Unknown task')
    stage = data.get('stage', 'unknown')
    chunks_completed = data.get('chunks_completed', 0)
    chunks_total = data.get('chunks_total', 0)
    estimated_time = data.get('estimated_time')
    
    print(f"📊 Progress: {progress:.1f}% | Stage: {stage}")
    print(f"   Task: {task}")
    if chunks_total > 0:
        print(f"   Chunks: {chunks_completed}/{chunks_total}")
    if estimated_time:
        print(f"   ETA: {estimated_time:.1f}s")
    if data.get('status') == 'completed':
        print("🎉 Processing completed!")
    elif data.get('status') == 'error':
        print(f"❌ Processing failed: {task}")
    print("-" * 50)

def simulate_progress_session():
    """Simulate a video processing session with progress updates"""
    global session_id
    
    # Generate a test session ID
    session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"🎬 Starting simulated video processing session: {session_id}")
    
    # Join the session
    sio.emit('join_session', {'session_id': session_id})
    time.sleep(0.5)
    
    # Manually trigger progress updates (simulating video processing)
    print("🔄 Simulating video processing with progress updates...")
    
    # Import the progress tracker from the app
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Import progress tracker from app
        from app import progress_tracker
        
        # Start session
        progress_tracker.start_session(session_id, total_chunks=5, video_duration=300)
        time.sleep(1)
        
        # Simulate video splitting
        progress_tracker.update_progress(session_id,
                                       current_task="Analyzing video file...",
                                       progress=10,
                                       stage='analysis')
        time.sleep(2)
        
        # Simulate chunk processing
        for i in range(1, 6):
            progress_tracker.update_chunk_progress(session_id, i, 5, 
                                                 f"Transcribing chunk_{i}.mp4")
            time.sleep(2)
        
        # Simulate final processing
        progress_tracker.update_progress(session_id,
                                       current_task="Analyzing content and generating insights...",
                                       progress=90,
                                       stage='analysis')
        time.sleep(2)
        
        # Complete processing
        progress_tracker.complete_session(session_id, success=True,
                                        message="Test processing completed successfully!")
        
        print("✅ Simulated processing completed")
        return True
        
    except Exception as e:
        print(f"❌ Error during simulation: {e}")
        return False

def test_progress_tracking():
    """Test comprehensive progress tracking"""
    print("🧪 Testing Real-time Progress Tracking...")
    
    try:
        # Connect to server
        sio.connect('http://localhost:5001')
        time.sleep(1)
        
        if not connection_established:
            print("❌ Failed to connect to server")
            return False
        
        # Start progress simulation in a separate thread
        progress_thread = threading.Thread(target=simulate_progress_session)
        progress_thread.start()
        
        # Monitor progress for 20 seconds
        start_time = time.time()
        while time.time() - start_time < 20:
            time.sleep(1)
            
            # Check if we received any progress updates
            if len(progress_updates) > 0:
                latest_update = progress_updates[-1]['data']
                if latest_update.get('status') == 'completed':
                    print("✅ Processing completed successfully!")
                    break
        
        progress_thread.join()
        
        # Analyze results
        print(f"\n📈 Progress Analysis:")
        print(f"   Total updates received: {len(progress_updates)}")
        
        if len(progress_updates) > 0:
            first_update = progress_updates[0]['data']
            last_update = progress_updates[-1]['data']
            
            print(f"   First progress: {first_update.get('progress', 0):.1f}%")
            print(f"   Final progress: {last_update.get('progress', 0):.1f}%")
            print(f"   Final status: {last_update.get('status', 'unknown')}")
            
            # Check if progress increased over time
            if last_update.get('progress', 0) > first_update.get('progress', 0):
                print("✅ Progress increased over time")
                return True
            else:
                print("❌ Progress did not increase properly")
                return False
        else:
            print("❌ No progress updates received")
            return False
            
    except Exception as e:
        print(f"❌ Progress tracking test failed: {e}")
        return False
    finally:
        if connection_established:
            sio.disconnect()

def test_ui_accessibility():
    """Test that the UI is accessible and responsive"""
    print("\n🧪 Testing UI Accessibility...")
    
    try:
        # Test that the main page loads
        response = requests.get('http://localhost:5001/')
        if response.status_code == 200:
            print("✅ Main page loads successfully")
            
            # Check for WebSocket-related elements in HTML
            html_content = response.text
            if 'socket.io' in html_content:
                print("✅ SocketIO client library included")
            else:
                print("❌ SocketIO client library missing")
                return False
                
            # Check for progress tracking elements
            progress_elements = [
                'progressSection',
                'connectionStatus', 
                'progressDetails',
                'chunksProgress',
                'timeRemaining',
                'currentStage'
            ]
            
            missing_elements = []
            for element in progress_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("✅ All progress tracking UI elements present")
                return True
            else:
                print(f"❌ Missing UI elements: {missing_elements}")
                return False
        else:
            print(f"❌ Main page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ UI accessibility test failed: {e}")
        return False

def main():
    """Run comprehensive progress tracking tests"""
    print("🚀 Starting Comprehensive Progress Tracking Tests")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Real-time progress tracking
    if test_progress_tracking():
        tests_passed += 1
    
    # Test 2: UI accessibility
    if test_ui_accessibility():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All progress tracking tests PASSED!")
        return True
    else:
        print("⚠️  Some progress tracking tests FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)