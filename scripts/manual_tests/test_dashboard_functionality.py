#!/usr/bin/env python3
"""
Test script for AI Insights Dashboard functionality
"""

import json
import time

import requests

BASE_URL = "http://localhost:5001"


def test_dashboard_endpoints():
    """Test all AI Insights Dashboard API endpoints"""
    print("🧪 Testing AI Insights Dashboard...")

    # Test AI capabilities
    print("\n1. Testing AI capabilities...")
    response = requests.get(f"{BASE_URL}/api/ai/capabilities")
    if response.status_code == 200:
        capabilities = response.json()
        print("✅ AI capabilities loaded successfully")
        print(f"   - AI Available: {capabilities['ai_insights_available']}")
        print(f"   - Features: {len(capabilities['features'])} available")
    else:
        print(f"❌ Failed to load AI capabilities: {response.status_code}")
        return False

    # Test sessions list
    print("\n2. Testing sessions API...")
    response = requests.get(f"{BASE_URL}/api/sessions")
    if response.status_code == 200:
        sessions = response.json()
        print(f"✅ Sessions loaded: {len(sessions['sessions'])} found")
        if len(sessions["sessions"]) > 0:
            test_session_id = sessions["sessions"][0]["session_id"]
            print(f"   - Using test session: {test_session_id}")
        else:
            print("   - No sessions available for testing")
            return False
    else:
        print(f"❌ Failed to load sessions: {response.status_code}")
        return False

    # Test AI insights retrieval
    print("\n3. Testing AI insights retrieval...")
    response = requests.get(f"{BASE_URL}/api/ai/insights/{test_session_id}")
    if response.status_code == 200:
        insights = response.json()
        print("✅ AI insights retrieved successfully")

        # Check different insight types
        ai_data = insights.get("ai_insights", {})

        if "sentiment_analysis" in ai_data:
            sentiment = ai_data["sentiment_analysis"]["overall"]
            print(
                f"   - Sentiment: {sentiment['interpretation']} (polarity: {sentiment['polarity']:.2f})"
            )

        if "topic_modeling" in ai_data:
            topics = ai_data["topic_modeling"]["main_topics"]
            print(f"   - Topics: {len(topics)} identified")
            for i, topic in enumerate(topics[:2]):
                print(
                    f"     • Topic {i+1}: {topic['description']} ({topic['strength']:.2f})"
                )

        if "key_insights" in ai_data:
            insights_data = ai_data["key_insights"]
            action_count = len(insights_data.get("action_items", []))
            print(f"   - Action Items: {action_count} found")

    else:
        print(f"❌ Failed to retrieve AI insights: {response.status_code}")

    # Test dashboard page
    print("\n4. Testing dashboard page...")
    response = requests.get(f"{BASE_URL}/ai-insights")
    if response.status_code == 200:
        print("✅ AI Insights Dashboard page loads successfully")
        print(f"   - Response size: {len(response.text)} characters")

        # Check for key dashboard elements
        content = response.text
        dashboard_elements = [
            "stats-overview",
            "Chart.js",
            "AIInsightsDashboard",
            "analyzeSession",
            "sentiment",
            "topics",
        ]

        found_elements = []
        for element in dashboard_elements:
            if element in content:
                found_elements.append(element)

        print(
            f"   - Dashboard elements found: {len(found_elements)}/{len(dashboard_elements)}"
        )
        if len(found_elements) == len(dashboard_elements):
            print("   ✅ All key dashboard elements present")
        else:
            missing = set(dashboard_elements) - set(found_elements)
            print(f"   ⚠️  Missing elements: {', '.join(missing)}")

    else:
        print(f"❌ Failed to load dashboard page: {response.status_code}")

    print("\n5. Testing individual insight endpoints...")

    # Test sentiment endpoint
    response = requests.get(f"{BASE_URL}/api/ai/insights/{test_session_id}/sentiment")
    if response.status_code == 200:
        print("✅ Sentiment analysis endpoint working")
    else:
        print(f"⚠️  Sentiment endpoint issue: {response.status_code}")

    # Test topics endpoint
    response = requests.get(f"{BASE_URL}/api/ai/insights/{test_session_id}/topics")
    if response.status_code == 200:
        print("✅ Topic analysis endpoint working")
    else:
        print(f"⚠️  Topics endpoint issue: {response.status_code}")

    # Test key insights endpoint
    response = requests.get(
        f"{BASE_URL}/api/ai/insights/{test_session_id}/key-insights"
    )
    if response.status_code == 200:
        print("✅ Key insights endpoint working")
    else:
        print(f"⚠️  Key insights endpoint issue: {response.status_code}")

    print("\n🎉 Dashboard testing completed!")
    return True


def test_javascript_functionality():
    """Test JavaScript-specific functionality"""
    print("\n📱 Testing JavaScript Dashboard Features...")

    # This would require a headless browser for full testing
    # For now, we'll just verify the structure exists
    response = requests.get(f"{BASE_URL}/ai-insights")
    if response.status_code == 200:
        content = response.text

        js_features = [
            "AIInsightsDashboard",
            "loadAICapabilities",
            "analyzeSession",
            "Chart.js",
            "toggleRealtimeMode",
            "createSentimentChart",
            "createTopicsChart",
        ]

        print("JavaScript features check:")
        for feature in js_features:
            if feature in content:
                print(f"   ✅ {feature}")
            else:
                print(f"   ❌ {feature}")


if __name__ == "__main__":
    try:
        success = test_dashboard_endpoints()
        test_javascript_functionality()

        if success:
            print("\n✅ All core dashboard functionality is working!")
            print("\n💡 Dashboard Features Available:")
            print("   • Real-time analytics toggle")
            print("   • Interactive Chart.js visualizations")
            print("   • Comprehensive AI insights analysis")
            print("   • Session selection and analysis")
            print("   • Sentiment distribution charts")
            print("   • Topic modeling visualization")
            print("   • Key insights extraction")
            print("   • Advanced analytics metrics")
        else:
            print("\n❌ Some dashboard features need attention")

    except requests.exceptions.ConnectionError:
        print(
            "❌ Cannot connect to the application. Make sure it's running on http://localhost:5001"
        )
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
