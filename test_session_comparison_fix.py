#!/usr/bin/env python3
"""
Test script to verify the session comparison fix is working
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_sessions_api():
    """Test that all sessions are now visible"""
    print("🔍 Testing Sessions API...")
    
    response = requests.get(f"{BASE_URL}/api/sessions")
    if response.status_code == 200:
        data = response.json()
        sessions = data.get('sessions', [])
        
        print(f"✅ Found {len(sessions)} sessions:")
        for session in sessions:
            print(f"   📁 {session['session_id']} - {session['session_name']}")
            
        # Check for the new sessions
        new_sessions = [s for s in sessions if s['session_id'].startswith('Dba')]
        print(f"\n🆕 New sessions found: {len(new_sessions)}")
        
        return sessions
    else:
        print(f"❌ Failed to get sessions: {response.status_code}")
        return []

def test_ai_insights_availability(sessions):
    """Test that AI insights are available for multiple sessions"""
    print("\n🧠 Testing AI Insights availability...")
    
    available_count = 0
    for session in sessions:
        session_id = session['session_id']
        
        # URL encode the session ID for spaces
        encoded_id = session_id.replace(' ', '%20')
        response = requests.get(f"{BASE_URL}/api/ai/insights/{encoded_id}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('available', False):
                available_count += 1
                print(f"   ✅ {session_id}: AI insights available")
            else:
                print(f"   ⚠️  {session_id}: No AI insights")
        else:
            print(f"   ❌ {session_id}: Error {response.status_code}")
    
    print(f"\n📊 Total sessions with AI insights: {available_count}/{len(sessions)}")
    return available_count >= 2

def test_session_comparison():
    """Test the session comparison functionality"""
    print("\n⚖️  Testing Session Comparison...")
    
    # Get sessions first
    sessions_response = requests.get(f"{BASE_URL}/api/sessions")
    if sessions_response.status_code != 200:
        print("❌ Cannot get sessions for comparison test")
        return False
        
    sessions = sessions_response.json().get('sessions', [])
    
    if len(sessions) < 2:
        print("❌ Need at least 2 sessions for comparison")
        return False
    
    # Select first 2 sessions for comparison
    session_ids = [sessions[0]['session_id'], sessions[1]['session_id']]
    
    comparison_data = {
        "session_ids": session_ids,
        "comparison_types": ["sentiment", "topics", "insights"]
    }
    
    print(f"🔍 Comparing sessions: {session_ids}")
    
    response = requests.post(
        f"{BASE_URL}/api/ai/compare-sessions",
        json=comparison_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Session comparison successful!")
        print(f"   📊 Sessions compared: {data.get('sessions_compared', 0)}")
        print(f"   📈 Comparison types: {', '.join(data.get('comparison_types', []))}")
        
        # Check if results contain expected data
        results = data.get('results', {})
        if 'sentiment' in results:
            sentiment_sessions = len(results['sentiment'].get('sessions', []))
            print(f"   😊 Sentiment data for {sentiment_sessions} sessions")
            
        if 'topics' in results:
            topic_count = results['topics']['statistics'].get('total_topics', 0)
            print(f"   🏷️ Found {topic_count} total topics")
            
        if 'insights' in results:
            total_insights = results['insights']['statistics'].get('total_insights', 0)
            print(f"   💡 Found {total_insights} total insights")
            
        return True
    else:
        print(f"❌ Session comparison failed: {response.status_code}")
        if response.headers.get('content-type', '').startswith('application/json'):
            error_data = response.json()
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
        return False

def main():
    print("🚀 Testing Session Comparison Fix")
    print("=" * 50)
    
    # Test 1: Sessions API
    sessions = test_sessions_api()
    if not sessions:
        print("❌ Cannot proceed without sessions")
        return
        
    # Test 2: AI Insights availability
    has_insights = test_ai_insights_availability(sessions)
    if not has_insights:
        print("⚠️  Limited testing possible without multiple AI insights")
    
    # Test 3: Session Comparison
    comparison_success = test_session_comparison()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   📁 Sessions found: {len(sessions)}")
    print(f"   🧠 AI insights available: {'✅' if has_insights else '❌'}")
    print(f"   ⚖️  Session comparison: {'✅' if comparison_success else '❌'}")
    
    if len(sessions) >= 2 and comparison_success:
        print("\n🎉 Session Comparison Fix: SUCCESS!")
        print("   The AI Insights Dashboard should now show all sessions")
        print("   and session comparison functionality should work properly.")
    else:
        print("\n⚠️  Partial success - some issues remain")

if __name__ == "__main__":
    main()
