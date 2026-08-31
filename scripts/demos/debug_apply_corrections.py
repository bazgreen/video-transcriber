#!/usr/bin/env python3
"""
Quick debug test for apply_corrections method.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_apply_corrections():
    """Debug the apply_corrections method."""
    from services.transcript_correction import TranscriptCorrectionEngine
    
    engine = TranscriptCorrectionEngine()
    
    sample_text = "This is a meating about artifical inteligence."
    print(f"Original: {sample_text}")
    
    suggestions = engine.generate_corrections(sample_text)
    print(f"\nFound {len(suggestions)} suggestions:")
    
    for i, suggestion in enumerate(suggestions):
        print(f"  {i+1}. '{suggestion.original_text}' -> '{suggestion.suggested_text}'")
        print(f"     Confidence: {suggestion.confidence}")
        print(f"     Auto-apply: {suggestion.auto_apply}")
        print(f"     Positions: {suggestion.start_position}-{suggestion.end_position}")
    
    # Apply corrections
    corrected = engine.apply_corrections(sample_text, suggestions)
    print(f"\nCorrected: {corrected}")
    print(f"Changed: {corrected != sample_text}")
    
    # Try forcing auto_apply
    for suggestion in suggestions:
        suggestion.auto_apply = True
    
    corrected_forced = engine.apply_corrections(sample_text, suggestions)
    print(f"Force corrected: {corrected_forced}")
    print(f"Force changed: {corrected_forced != sample_text}")

if __name__ == "__main__":
    test_apply_corrections()
