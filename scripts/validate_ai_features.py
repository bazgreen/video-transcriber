#!/usr/bin/env python3
"""
Validation script to check if all AI features are properly installed
"""


def check_ai_features():
    """Check if all AI features are working"""
    print("🔍 Checking AI Features Installation...")
    print("=" * 40)

    # Check TextBlob (sentiment analysis)
    try:
        import textblob

        blob = textblob.TextBlob("This is a test sentence.")
        _ = blob.sentiment  # Test sentiment analysis
        print("✅ TextBlob (Sentiment Analysis) - Working")
    except Exception as e:
        print(f"❌ TextBlob (Sentiment Analysis) - Failed: {e}")
        return False

    # Check scikit-learn (topic modeling)
    try:
        import sklearn
        from sklearn.feature_extraction.text import TfidfVectorizer

        _ = TfidfVectorizer()  # Test TfidfVectorizer instantiation
        print("✅ Scikit-learn (Topic Modeling) - Working")
    except Exception as e:
        print(f"❌ Scikit-learn (Topic Modeling) - Failed: {e}")
        return False

    # Check SpaCy (advanced NLP)
    try:
        import spacy

        nlp = spacy.load("en_core_web_sm")
        _ = nlp("Hello world")  # Test spacy processing
        print("✅ SpaCy (Advanced NLP) - Working")
    except Exception as e:
        print(f"❌ SpaCy (Advanced NLP) - Failed: {e}")
        return False

    # Test AI insights service
    try:
        from src.services.ai_insights import create_ai_insights_engine

        engine = create_ai_insights_engine()
        print("✅ AI Insights Engine - Working")
        print(
            f"   📊 Sentiment Analysis: {'✅' if engine.sentiment_available else '❌'}"
        )
        print(
            f"   📈 Topic Modeling: {'✅' if engine.topic_modeling_available else '❌'}"
        )
        print(f"   🧠 Advanced NLP: {'✅' if engine.nlp_available else '❌'}")
    except Exception as e:
        print(f"❌ AI Insights Engine - Failed: {e}")
        return False

    print("\n🚀 All AI features are properly installed and working!")
    return True


if __name__ == "__main__":
    success = check_ai_features()
    if not success:
        print("\n⚠️  Some AI features are not working correctly.")
        print("Try running: python install_ai_features.py")
        exit(1)
    else:
        print("\n✨ Your Video Transcriber has full AI capabilities enabled!")
