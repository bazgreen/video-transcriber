#!/usr/bin/env python3
"""
Simple test for transcript correction without authentication.
Tests the core TranscriptCorrectionEngine functionality directly.
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_correction_engine():
    """Test the TranscriptCorrectionEngine directly."""
    print("🧪 Testing TranscriptCorrectionEngine")
    print("=" * 50)
    
    try:
        from services.transcript_correction import TranscriptCorrectionEngine
        
        # Initialize the engine
        print("\n1. Initializing TranscriptCorrectionEngine...")
        engine = TranscriptCorrectionEngine()
        print("   ✅ Engine initialized successfully!")
        print(f"   📚 Correction available: {engine.correction_available}")
        
        # Sample transcript with errors
        sample_transcript = """Hello, welcome to today's meating about artifical inteligence and machine lerning. We're going to discus the latest advancements in AI technolgy and how they effect our bussiness operations.

First, lets talk about natural language procesing. NLP has become incredibley powerfull in recent years, allowing us to analayze large amounts of text data very efectively."""
        
        # Test quality analysis
        print("\n2. Testing quality analysis...")
        quality_metrics = engine.analyze_transcript_quality(sample_transcript)
        
        print(f"   ✅ Quality analysis completed!")
        print(f"   📊 Overall Score: {quality_metrics.overall_score * 100:.1f}%")
        print(f"   📝 Grammar Score: {quality_metrics.grammar_score * 100:.1f}%")
        print(f"   🔤 Spelling Score: {quality_metrics.spelling_score * 100:.1f}%")
        print(f"   📚 Readability Score: {quality_metrics.readability_score * 100:.1f}%")
        print(f"   🎯 Confidence Score: {quality_metrics.confidence_score * 100:.1f}%")
        print(f"   ⚠️  Issues Found: {quality_metrics.issues_count}")
        print(f"   💡 Suggestions: {quality_metrics.suggestions_count} items")
        
        # Test correction suggestions
        print("\n3. Testing correction suggestions...")
        suggestions = engine.generate_corrections(sample_transcript)
        
        print(f"   ✅ Generated {len(suggestions)} correction suggestions!")
        
        for i, suggestion in enumerate(suggestions[:5]):  # Show first 5
            print(f"\n   📝 Suggestion {i+1}:")
            print(f"      Original: '{suggestion.original_text}'")
            print(f"      Suggested: '{suggestion.suggested_text}'")
            print(f"      Type: {suggestion.correction_type}")
            print(f"      Confidence: {suggestion.confidence * 100:.1f}%")
            if suggestion.explanation:
                print(f"      Explanation: {suggestion.explanation}")
        
        if len(suggestions) > 5:
            print(f"\n   ... and {len(suggestions) - 5} more suggestions")
        
        # Test applying corrections
        print("\n4. Testing apply corrections...")
        if suggestions:
            corrected_text = engine.apply_corrections(sample_transcript, suggestions[:3])  # Apply first 3
            print(f"   ✅ Applied first 3 corrections!")
            print(f"   📝 Corrected excerpt: {corrected_text[:100]}...")
        
        # Test session management
        print("\n5. Testing session management...")
        session_id = engine.create_session(
            transcript=sample_transcript,
            user_id="test_user"
        )
        print(f"   ✅ Created session: {session_id}")
        
        session_data = engine.get_session(session_id)
        if session_data:
            print(f"   📊 Session data retrieved successfully!")
            print(f"   📝 Transcript length: {len(session_data['original_transcript'])} chars")
            print(f"   🔧 Suggestions count: {len(session_data['suggestions'])}")
        
        print("\n" + "=" * 50)
        print("🎉 TranscriptCorrectionEngine Test Completed Successfully!")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import Error: {e}")
        print("   💡 Make sure the correction dependencies are installed:")
        print("      pip install -r requirements-correction.txt")
        return False
    except Exception as e:
        print(f"   ❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test if all required dependencies are available."""
    print("🔍 Testing Dependencies")
    print("=" * 30)
    
    dependencies = [
        ('textblob', 'TextBlob natural language processing'),
        ('spacy', 'spaCy NLP library'),
        ('language_tool_python', 'LanguageTool grammar checker')
    ]
    
    all_available = True
    
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"   ✅ {module}: {description}")
        except ImportError:
            print(f"   ❌ {module}: Not available - {description}")
            all_available = False
    
    # Test spaCy model
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print(f"   ✅ spaCy model 'en_core_web_sm': Available")
    except OSError:
        print(f"   ❌ spaCy model 'en_core_web_sm': Not available")
        print(f"      Run: python -m spacy download en_core_web_sm")
        all_available = False
    except Exception as e:
        print(f"   ❌ spaCy model error: {e}")
        all_available = False
    
    print(f"\n   {'✅ All dependencies available!' if all_available else '❌ Some dependencies missing'}")
    return all_available

if __name__ == "__main__":
    print("🚀 Starting Transcript Correction Engine Tests")
    print("=" * 60)
    
    # Test dependencies first
    if test_dependencies():
        print("\n")
        test_correction_engine()
    else:
        print("\n❌ Cannot run engine tests - dependencies missing")
        print("\n💡 To install dependencies:")
        print("   pip install -r requirements-correction.txt")
        print("   python -m spacy download en_core_web_sm")
