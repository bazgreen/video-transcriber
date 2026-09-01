#!/usr/bin/env python3
"""
Test script for transcript correction functionality.
Tests the API endpoints and core features.
"""

import requests
import json
import time

def test_transcript_correction():
    """Test the transcript correction API endpoints."""
    base_url = "http://127.0.0.1:5001"

    # Sample transcript with errors
    sample_transcript = """Hello, welcome to today's meating about artifical inteligence and machine lerning. We're going to discus the latest advancements in AI technolgy and how they effect our bussiness operations.

First, lets talk about natural language procesing. NLP has become incredibley powerfull in recent years, allowing us to analayze large amounts of text data very efectively. However, there are still some chalenges we need to adress.

One major issue is the acuracy of speech recognishion systems. Sometimes they missinterpret words, especialy when dealing with technicle terminology or proper nouns. For example, the system might transcribe "machine learning" as "masheen lerning" or "AI" as "eye".

In conclustion, while AI has made remarkabel progress, we stil need to be carefull about data quality and acuracy. Thank you for your atention, and let's move on to the Q&A sesion."""

    print("🧪 Testing Transcript Correction Feature")
    print("=" * 50)

    # Test 1: Quality Analysis
    print("\n1. Testing Quality Analysis...")
    try:
        response = requests.post(
            f"{base_url}/api/correction/quality-analysis",
            json={
                "transcript": sample_transcript
            },
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                metrics = result.get('quality_metrics', {})
                print(f"   ✅ Quality analysis successful!")
                print(f"   📊 Overall Score: {metrics.get('overall_score', 0) * 100:.1f}%")
                print(f"   📝 Grammar Score: {metrics.get('grammar_score', 0) * 100:.1f}%")
                print(f"   🔤 Spelling Score: {metrics.get('spelling_score', 0) * 100:.1f}%")
                print(f"   📚 Readability Score: {metrics.get('readability_score', 0) * 100:.1f}%")
                print(f"   🎯 Confidence Score: {metrics.get('confidence_score', 0) * 100:.1f}%")
                print(f"   ⚠️  Issues Found: {metrics.get('issues_found', 0)}")

                session_id = result.get('session_id')
                print(f"   🆔 Session ID: {session_id}")
            else:
                print(f"   ❌ Quality analysis failed: {result.get('error')}")
                return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

    # Test 2: Generate Suggestions
    print("\n2. Testing Correction Suggestions...")
    try:
        response = requests.post(
            f"{base_url}/api/correction/suggestions",
            json={
                "transcript": sample_transcript,
                "session_id": session_id
            },
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                suggestions = result.get('suggestions', [])
                print(f"   ✅ Generated {len(suggestions)} correction suggestions!")

                for i, suggestion in enumerate(suggestions[:5]):  # Show first 5
                    print(f"   📝 Suggestion {i+1}:")
                    print(f"      Original: '{suggestion.get('original_text')}'")
                    print(f"      Suggested: '{suggestion.get('suggested_text')}'")
                    print(f"      Type: {suggestion.get('type')}")
                    print(f"      Confidence: {suggestion.get('confidence', 0) * 100:.1f}%")
                    if suggestion.get('explanation'):
                        print(f"      Explanation: {suggestion.get('explanation')}")
                    print()

                if len(suggestions) > 5:
                    print(f"   ... and {len(suggestions) - 5} more suggestions")
            else:
                print(f"   ❌ Suggestion generation failed: {result.get('error')}")
                return False
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

    # Test 3: Dictionary Information
    print("\n3. Testing Dictionary Features...")
    try:
        response = requests.get(f"{base_url}/api/correction/dictionaries")

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                dictionaries = result.get('dictionaries', {})
                print(f"   ✅ Available dictionaries: {list(dictionaries.keys())}")

                for name, info in dictionaries.items():
                    print(f"   📚 {name}: {info.get('description', 'No description')}")
                    print(f"      Terms: {info.get('term_count', 0)}")
            else:
                print(f"   ❌ Dictionary request failed: {result.get('error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    # Test 4: Statistics
    print("\n4. Testing Statistics...")
    try:
        response = requests.get(f"{base_url}/api/correction/statistics")

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                stats = result.get('statistics', {})
                print(f"   ✅ Statistics retrieved!")
                print(f"   📈 Total Sessions: {stats.get('total_sessions', 0)}")
                print(f"   🔧 Total Corrections: {stats.get('total_corrections', 0)}")
                print(f"   📊 Average Quality Score: {stats.get('average_quality_score', 0) * 100:.1f}%")
            else:
                print(f"   ❌ Statistics request failed: {result.get('error')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    print("\n" + "=" * 50)
    print("🎉 Transcript Correction Test Completed!")
    print("\n📝 To test the web interface:")
    print(f"   Visit: {base_url}/transcript-correction")
    print("\n💡 Next steps:")
    print("   - Test the web interface manually")
    print("   - Try different types of text with errors")
    print("   - Test custom dictionary functionality")
    print("   - Test export features")

    return True

if __name__ == "__main__":
    print("Starting transcript correction tests...")
    print("Make sure the application is running on http://127.0.0.1:5001")

    # Wait a moment for the server to be ready
    time.sleep(2)

    try:
        test_transcript_correction()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
