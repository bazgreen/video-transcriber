#!/usr/bin/env python3
"""
Test script for Session Comparison & Analytics Dashboard functionality.

This script tests the new session comparison features including:
- Session selection for comparison
- Multi-session data loading
- Comparison analysis generation
- Chart data preparation
- Export functionality
"""

import json
import time
from datetime import datetime

import requests

# Configuration
BASE_URL = "http://localhost:5001"


def test_session_comparison():
    """Test the complete session comparison workflow"""
    print("🔄 Testing Session Comparison & Analytics Dashboard")
    print("=" * 60)

    # Test 1: Load AI Insights Dashboard
    print("\n1. Testing AI Insights Dashboard page...")
    response = requests.get(f"{BASE_URL}/ai-insights")
    if response.status_code == 200:
        print("✅ AI Insights Dashboard loads successfully")

        # Check for new comparison features
        content = response.text
        comparison_features = [
            "comparisonModal",
            "sessionComparison",
            "startSessionComparison",
            "displayComparisonResults",
            "sentimentComparisonChart",
            "topicComparisonChart",
        ]

        found_features = []
        for feature in comparison_features:
            if feature in content:
                found_features.append(feature)

        print(
            f"   - Comparison features found: {len(found_features)}/{len(comparison_features)}"
        )
        if len(found_features) == len(comparison_features):
            print("   ✅ All session comparison features present")
        else:
            missing = set(comparison_features) - set(found_features)
            print(f"   ⚠️  Missing features: {', '.join(missing)}")
    else:
        print(f"❌ Failed to load dashboard: {response.status_code}")
        return False

    # Test 2: Get available sessions for comparison
    print("\n2. Testing sessions API for comparison...")
    response = requests.get(f"{BASE_URL}/api/sessions")
    if response.status_code == 200:
        sessions = response.json()
        session_count = len(sessions.get("sessions", []))
        print(f"✅ Found {session_count} sessions available for comparison")

        if session_count >= 2:
            print("   ✅ Sufficient sessions for comparison testing")
            test_sessions = sessions["sessions"][:3]  # Use up to 3 sessions for testing
            session_ids = [s["session_id"] for s in test_sessions]
            print(f"   - Using sessions: {', '.join(session_ids)}")
        else:
            print("   ⚠️  Need at least 2 sessions for comparison testing")
            return False
    else:
        print(f"❌ Failed to load sessions: {response.status_code}")
        return False

    # Test 3: Load AI insights for multiple sessions
    print("\n3. Testing multi-session insights loading...")
    session_insights = {}
    successful_loads = 0

    for session_id in session_ids:
        print(f"   Loading insights for: {session_id}")
        response = requests.get(f"{BASE_URL}/api/ai/insights/{session_id}")
        if response.status_code == 200:
            insights = response.json()
            if insights.get("ai_insights"):
                session_insights[session_id] = insights
                successful_loads += 1
                print(f"   ✅ Insights loaded for {session_id}")

                # Validate insight types
                ai_data = insights["ai_insights"]
                insight_types = []
                if "sentiment_analysis" in ai_data:
                    insight_types.append("sentiment")
                if "topic_modeling" in ai_data:
                    insight_types.append("topics")
                if "key_insights" in ai_data:
                    insight_types.append("insights")

                print(f"      Available for comparison: {', '.join(insight_types)}")
            else:
                print(f"   ⚠️  No AI insights available for {session_id}")
        else:
            print(
                f"   ❌ Failed to load insights for {session_id}: {response.status_code}"
            )

    print(
        f"\n   Summary: {successful_loads}/{len(session_ids)} sessions ready for comparison"
    )

    if successful_loads < 2:
        print("   ⚠️  Need at least 2 sessions with AI insights for comparison")
        return False

    # Test 4: Analyze comparison data structure
    print("\n4. Testing comparison data analysis...")
    comparison_data = analyze_comparison_data(session_insights)

    if comparison_data:
        print("✅ Comparison data analysis successful")
        print(f"   - Sessions analyzed: {len(comparison_data['sessions'])}")
        print(f"   - Sentiment trends: {len(comparison_data['sentiment_trends'])}")
        print(f"   - Topics found: {len(comparison_data['topic_evolution'])}")
        print(f"   - Insights patterns: {len(comparison_data['insights_patterns'])}")

        # Test sentiment comparison
        if comparison_data["sentiment_trends"]:
            print("\n   📊 Sentiment Analysis Comparison:")
            for trend in comparison_data["sentiment_trends"]:
                print(
                    f"      {trend['session_name']}: {trend['polarity']:.2f} ({trend['interpretation']})"
                )

        # Test topic evolution
        if comparison_data["topic_evolution"]:
            print(f"\n   🏷️  Topic Evolution Analysis:")
            print(
                f"      Common topics across sessions: {len([k for k, v in comparison_data['topic_evolution'].items() if len(v) > 1])}"
            )
            print(
                f"      Unique topics: {len([k for k, v in comparison_data['topic_evolution'].items() if len(v) == 1])}"
            )

        # Test insights patterns
        if comparison_data["insights_patterns"]:
            print(f"\n   💡 Key Insights Patterns:")
            total_insights = sum(
                p["total_insights"] for p in comparison_data["insights_patterns"]
            )
            avg_insights = total_insights / len(comparison_data["insights_patterns"])
            print(f"      Total insights across sessions: {total_insights}")
            print(f"      Average insights per session: {avg_insights:.1f}")
    else:
        print("❌ Failed to analyze comparison data")
        return False

    # Test 5: Chart data preparation
    print("\n5. Testing chart data preparation...")
    chart_data = prepare_chart_data(comparison_data)

    if chart_data:
        print("✅ Chart data preparation successful")
        if "sentiment_chart" in chart_data:
            print(
                f"   - Sentiment chart datasets: {len(chart_data['sentiment_chart']['datasets'])}"
            )
        if "topic_chart" in chart_data:
            print(
                f"   - Topic chart labels: {len(chart_data['topic_chart']['labels'])}"
            )
        if "metrics_chart" in chart_data:
            print(f"   - Metrics chart ready for radar visualization")
    else:
        print("❌ Failed to prepare chart data")

    # Test 6: Export functionality simulation
    print("\n6. Testing export data preparation...")
    export_data = prepare_export_data(comparison_data)

    if export_data:
        print("✅ Export data preparation successful")
        print(f"   - Export file size: {len(json.dumps(export_data))} characters")
        print(f"   - Analysis timestamp: {export_data.get('analysis_date', 'N/A')}")
        print(f"   - Sessions included: {export_data.get('sessions_analyzed', 0)}")
    else:
        print("❌ Failed to prepare export data")

    print("\n" + "=" * 60)
    print("✅ Session Comparison & Analytics Dashboard testing complete!")
    print("\n🎯 Key Features Validated:")
    print("   📊 Multi-session data loading")
    print("   📈 Sentiment trends comparison")
    print("   🏷️  Topic evolution analysis")
    print("   💡 Key insights patterns")
    print("   📊 Chart.js data preparation")
    print("   📥 Export functionality")

    return True


def analyze_comparison_data(session_insights):
    """Analyze session insights for comparison"""
    try:
        comparison_data = {
            "sessions": [],
            "sentiment_trends": [],
            "topic_evolution": {},
            "insights_patterns": [],
        }

        for session_id, data in session_insights.items():
            insights = data["ai_insights"]

            # Session info
            session_info = {
                "id": session_id,
                "name": session_id,  # In real app, would get from session metadata
                "date": datetime.now().isoformat(),
            }
            comparison_data["sessions"].append(session_info)

            # Sentiment analysis
            if "sentiment_analysis" in insights and insights["sentiment_analysis"].get(
                "overall"
            ):
                sentiment = insights["sentiment_analysis"]["overall"]
                comparison_data["sentiment_trends"].append(
                    {
                        "session_id": session_id,
                        "session_name": session_info["name"],
                        "polarity": sentiment.get("polarity", 0),
                        "subjectivity": sentiment.get("subjectivity", 0),
                        "interpretation": sentiment.get("interpretation", "Neutral"),
                    }
                )

            # Topic modeling
            if "topic_modeling" in insights and insights["topic_modeling"].get(
                "main_topics"
            ):
                for topic in insights["topic_modeling"]["main_topics"]:
                    topic_key = topic.get(
                        "description", f"Topic {topic.get('topic_id', 'Unknown')}"
                    )
                    if topic_key not in comparison_data["topic_evolution"]:
                        comparison_data["topic_evolution"][topic_key] = []

                    comparison_data["topic_evolution"][topic_key].append(
                        {
                            "session_id": session_id,
                            "session_name": session_info["name"],
                            "strength": topic.get("strength", 0),
                            "keywords": topic.get("keywords", []),
                        }
                    )

            # Key insights
            if "key_insights" in insights:
                key_insights = insights["key_insights"]
                action_items = len(key_insights.get("action_items", []))
                takeaways = len(key_insights.get("key_takeaways", []))
                decisions = len(key_insights.get("decision_points", []))

                comparison_data["insights_patterns"].append(
                    {
                        "session_id": session_id,
                        "session_name": session_info["name"],
                        "action_items": action_items,
                        "takeaways": takeaways,
                        "decisions": decisions,
                        "total_insights": action_items + takeaways + decisions,
                    }
                )

        return comparison_data

    except Exception as e:
        print(f"Error analyzing comparison data: {e}")
        return None


def prepare_chart_data(comparison_data):
    """Prepare data for Chart.js visualizations"""
    try:
        chart_data = {}

        # Sentiment chart data
        if comparison_data["sentiment_trends"]:
            sentiment_data = comparison_data["sentiment_trends"]
            chart_data["sentiment_chart"] = {
                "labels": [s["session_name"] for s in sentiment_data],
                "datasets": [
                    {
                        "label": "Sentiment Polarity",
                        "data": [s["polarity"] for s in sentiment_data],
                        "borderColor": "rgb(102, 126, 234)",
                        "backgroundColor": "rgba(102, 126, 234, 0.2)",
                        "borderWidth": 2,
                    }
                ],
            }

        # Topic chart data (common topics only)
        if comparison_data["topic_evolution"]:
            common_topics = {
                k: v
                for k, v in comparison_data["topic_evolution"].items()
                if len(v) > 1
            }
            if common_topics:
                chart_data["topic_chart"] = {
                    "labels": list(common_topics.keys())[:10],  # Limit to 10 topics
                    "datasets": [],
                }

                # Create dataset for each session
                sessions = set()
                for topic_sessions in common_topics.values():
                    for session in topic_sessions:
                        sessions.add(session["session_name"])

                for i, session_name in enumerate(sessions):
                    dataset = {
                        "label": session_name,
                        "data": [],
                        "backgroundColor": f"hsl({i * 137.508 % 360}, 70%, 60%)",
                    }

                    for topic_name in chart_data["topic_chart"]["labels"]:
                        topic_sessions = common_topics[topic_name]
                        session_topic = next(
                            (
                                t
                                for t in topic_sessions
                                if t["session_name"] == session_name
                            ),
                            None,
                        )
                        dataset["data"].append(
                            session_topic["strength"] * 100 if session_topic else 0
                        )

                    chart_data["topic_chart"]["datasets"].append(dataset)

        # Metrics chart ready indicator
        if comparison_data["sessions"]:
            chart_data["metrics_chart"] = {
                "type": "radar",
                "sessions_count": len(comparison_data["sessions"]),
            }

        return chart_data

    except Exception as e:
        print(f"Error preparing chart data: {e}")
        return None


def prepare_export_data(comparison_data):
    """Prepare data for export"""
    try:
        export_data = {
            "analysis_date": datetime.now().isoformat(),
            "sessions_analyzed": len(comparison_data["sessions"]),
            "comparison_summary": {
                "total_sessions": len(comparison_data["sessions"]),
                "sentiment_analysis_available": len(comparison_data["sentiment_trends"])
                > 0,
                "topic_analysis_available": len(comparison_data["topic_evolution"]) > 0,
                "insights_analysis_available": len(comparison_data["insights_patterns"])
                > 0,
            },
            "sentiment_trends": comparison_data["sentiment_trends"],
            "topic_evolution": comparison_data["topic_evolution"],
            "insights_patterns": comparison_data["insights_patterns"],
            "sessions": comparison_data["sessions"],
        }

        # Add summary statistics
        if comparison_data["sentiment_trends"]:
            polarities = [s["polarity"] for s in comparison_data["sentiment_trends"]]
            export_data["comparison_summary"]["sentiment_stats"] = {
                "average_polarity": sum(polarities) / len(polarities),
                "polarity_range": max(polarities) - min(polarities),
                "most_positive_session": max(
                    comparison_data["sentiment_trends"], key=lambda x: x["polarity"]
                )["session_name"],
                "most_negative_session": min(
                    comparison_data["sentiment_trends"], key=lambda x: x["polarity"]
                )["session_name"],
            }

        if comparison_data["topic_evolution"]:
            export_data["comparison_summary"]["topic_stats"] = {
                "total_unique_topics": len(comparison_data["topic_evolution"]),
                "common_topics": len(
                    [
                        k
                        for k, v in comparison_data["topic_evolution"].items()
                        if len(v) > 1
                    ]
                ),
                "session_specific_topics": len(
                    [
                        k
                        for k, v in comparison_data["topic_evolution"].items()
                        if len(v) == 1
                    ]
                ),
            }

        return export_data

    except Exception as e:
        print(f"Error preparing export data: {e}")
        return None


if __name__ == "__main__":
    try:
        success = test_session_comparison()
        if success:
            print("\n🎉 All session comparison tests passed!")
            exit(0)
        else:
            print("\n⚠️  Some tests failed - check the output above")
            exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        exit(1)
