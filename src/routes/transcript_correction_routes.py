"""
API routes for automated transcript correction and quality assurance.
Provides endpoints for correction analysis, suggestions, and session management.
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Any, Tuple
from flask import Blueprint, request, jsonify, current_app, render_template

from src.services.transcript_correction import (
    create_transcript_correction_engine, 
    get_industry_dictionary,
    CorrectionSuggestion,
    QualityMetrics,
    INDUSTRY_DICTIONARIES
)

logger = logging.getLogger(__name__)

# Create blueprint for correction routes
correction_bp = Blueprint('correction', __name__)

@correction_bp.route('/transcript-correction')
def transcript_correction_page():
    """Serve the transcript correction interface."""
    return render_template('transcript-correction.html')

# API routes with prefix
api_bp = Blueprint('correction_api', __name__, url_prefix='/api/correction')

# Global correction engine instance
correction_engine = None

def get_correction_engine():
    """Get or create correction engine instance."""
    global correction_engine
    if correction_engine is None:
        correction_engine = create_transcript_correction_engine()
    return correction_engine

@api_bp.route('/quality-analysis', methods=['POST'])

def analyze_transcript_quality() -> Tuple[Dict[str, Any], int]:
    """
    Analyze transcript quality and return metrics.
    
    Body Parameters:
    - transcript: Full transcript text
    - segments: Optional list of transcript segments with timing/confidence
    """
    try:
        data = request.get_json()
        if not data or 'transcript' not in data:
            return jsonify({'error': 'Transcript text required'}), 400
        
        transcript_text = data['transcript']
        segments = data.get('segments', [])
        
        engine = get_correction_engine()
        quality_metrics = engine.analyze_transcript_quality(transcript_text, segments)
        
        return jsonify({
            'quality_metrics': {
                'overall_score': quality_metrics.overall_score,
                'confidence_score': quality_metrics.confidence_score,
                'grammar_score': quality_metrics.grammar_score,
                'spelling_score': quality_metrics.spelling_score,
                'readability_score': quality_metrics.readability_score,
                'issues_count': quality_metrics.issues_count,
                'suggestions_count': quality_metrics.suggestions_count
            },
            'recommendations': _generate_quality_recommendations(quality_metrics),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing transcript quality: {e}")
        return jsonify({'error': 'Quality analysis failed', 'details': str(e)}), 500

@api_bp.route('/suggestions', methods=['POST'])

def generate_correction_suggestions() -> Tuple[Dict[str, Any], int]:
    """
    Generate correction suggestions for text.
    
    Body Parameters:
    - text: Text to analyze and correct
    - confidence: Optional confidence score from transcription (0-1)
    - auto_apply: Whether to auto-apply high-confidence corrections
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text required'}), 400
        
        text = data['text']
        confidence = data.get('confidence', 1.0)
        auto_apply = data.get('auto_apply', False)
        
        engine = get_correction_engine()
        suggestions = engine.generate_corrections(text, confidence)
        
        # Convert suggestions to JSON-serializable format
        suggestions_data = []
        for suggestion in suggestions:
            suggestions_data.append({
                'original_text': suggestion.original_text,
                'suggested_text': suggestion.suggested_text,
                'confidence': suggestion.confidence,
                'correction_type': suggestion.correction_type,
                'start_position': suggestion.start_position,
                'end_position': suggestion.end_position,
                'explanation': suggestion.explanation,
                'auto_apply': suggestion.auto_apply
            })
        
        # Apply corrections if requested
        corrected_text = text
        if auto_apply:
            corrected_text = engine.apply_corrections(text, suggestions)
        
        return jsonify({
            'original_text': text,
            'corrected_text': corrected_text,
            'suggestions': suggestions_data,
            'total_suggestions': len(suggestions),
            'auto_applied': auto_apply,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating correction suggestions: {e}")
        return jsonify({'error': 'Suggestion generation failed', 'details': str(e)}), 500

@api_bp.route('/sessions', methods=['POST'])

def start_correction_session() -> Tuple[Dict[str, Any], int]:
    """
    Start a new correction session for a transcript.
    
    Body Parameters:
    - session_id: Unique session identifier
    - transcript: Original transcript text
    - segments: Optional transcript segments
    """
    try:
        data = request.get_json()
        if not data or 'session_id' not in data or 'transcript' not in data:
            return jsonify({'error': 'Session ID and transcript required'}), 400
        
        session_id = data['session_id']
        transcript_text = data['transcript']
        segments = data.get('segments', [])
        
        engine = get_correction_engine()
        correction_session = engine.start_correction_session(session_id, transcript_text, segments)
        
        return jsonify({
            'session': {
                'session_id': correction_session.session_id,
                'original_transcript': correction_session.original_transcript,
                'quality_before': {
                    'overall_score': correction_session.quality_before.overall_score,
                    'confidence_score': correction_session.quality_before.confidence_score,
                    'grammar_score': correction_session.quality_before.grammar_score,
                    'spelling_score': correction_session.quality_before.spelling_score,
                    'readability_score': correction_session.quality_before.readability_score,
                    'issues_count': correction_session.quality_before.issues_count,
                    'suggestions_count': correction_session.quality_before.suggestions_count
                },
                'created_at': correction_session.created_at
            },
            'success': True
        }), 201
        
    except Exception as e:
        logger.error(f"Error starting correction session: {e}")
        return jsonify({'error': 'Session creation failed', 'details': str(e)}), 500

@api_bp.route('/sessions/<session_id>/apply', methods=['POST'])

def apply_correction_to_session(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Apply a correction to an active session.
    
    Body Parameters:
    - correction: Correction object to apply
    - user_approved: Whether user approved the correction
    """
    try:
        data = request.get_json()
        if not data or 'correction' not in data:
            return jsonify({'error': 'Correction data required'}), 400
        
        correction_data = data['correction']
        user_approved = data.get('user_approved', True)
        
        # Create CorrectionSuggestion object
        correction = CorrectionSuggestion(
            original_text=correction_data['original_text'],
            suggested_text=correction_data['suggested_text'],
            confidence=correction_data['confidence'],
            correction_type=correction_data['correction_type'],
            start_position=correction_data['start_position'],
            end_position=correction_data['end_position'],
            explanation=correction_data['explanation'],
            auto_apply=correction_data.get('auto_apply', False)
        )
        
        engine = get_correction_engine()
        success = engine.apply_correction_to_session(session_id, correction, user_approved)
        
        if not success:
            return jsonify({'error': 'Session not found or correction failed'}), 404
        
        # Get updated session
        session = engine.correction_sessions.get(session_id)
        if session:
            return jsonify({
                'corrected_text': session.corrected_transcript,
                'quality_after': {
                    'overall_score': session.quality_after.overall_score,
                    'confidence_score': session.quality_after.confidence_score,
                    'grammar_score': session.quality_after.grammar_score,
                    'spelling_score': session.quality_after.spelling_score,
                    'readability_score': session.quality_after.readability_score,
                    'issues_count': session.quality_after.issues_count,
                    'suggestions_count': session.quality_after.suggestions_count
                },
                'corrections_applied_count': len(session.corrections_applied),
                'success': True
            }), 200
        else:
            return jsonify({'error': 'Session state error'}), 500
        
    except Exception as e:
        logger.error(f"Error applying correction to session {session_id}: {e}")
        return jsonify({'error': 'Correction application failed', 'details': str(e)}), 500

@api_bp.route('/sessions/<session_id>/complete', methods=['POST'])

def complete_correction_session(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Complete a correction session and return final results.
    
    Body Parameters:
    - user_feedback: Optional user feedback
    """
    try:
        data = request.get_json() or {}
        user_feedback = data.get('user_feedback', {})
        
        engine = get_correction_engine()
        completed_session = engine.complete_correction_session(session_id, user_feedback)
        
        if not completed_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Calculate improvement metrics
        quality_improvement = (
            completed_session.quality_after.overall_score - 
            completed_session.quality_before.overall_score
        )
        
        return jsonify({
            'session_summary': {
                'session_id': completed_session.session_id,
                'original_transcript': completed_session.original_transcript,
                'corrected_transcript': completed_session.corrected_transcript,
                'quality_improvement': round(quality_improvement, 2),
                'corrections_applied': len(completed_session.corrections_applied),
                'quality_before': {
                    'overall_score': completed_session.quality_before.overall_score,
                    'issues_count': completed_session.quality_before.issues_count
                },
                'quality_after': {
                    'overall_score': completed_session.quality_after.overall_score,
                    'issues_count': completed_session.quality_after.issues_count
                },
                'created_at': completed_session.created_at,
                'completed_at': completed_session.completed_at
            },
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error completing correction session {session_id}: {e}")
        return jsonify({'error': 'Session completion failed', 'details': str(e)}), 500

@api_bp.route('/sessions/<session_id>', methods=['GET'])

def get_correction_session(session_id: str) -> Tuple[Dict[str, Any], int]:
    """Get details of a correction session."""
    try:
        engine = get_correction_engine()
        session = engine.correction_sessions.get(session_id)
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session': {
                'session_id': session.session_id,
                'original_transcript': session.original_transcript,
                'corrected_transcript': session.corrected_transcript,
                'corrections_applied_count': len(session.corrections_applied),
                'quality_before': {
                    'overall_score': session.quality_before.overall_score,
                    'issues_count': session.quality_before.issues_count
                },
                'quality_after': {
                    'overall_score': session.quality_after.overall_score,
                    'issues_count': session.quality_after.issues_count
                },
                'created_at': session.created_at,
                'completed_at': session.completed_at
            },
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting correction session {session_id}: {e}")
        return jsonify({'error': 'Session retrieval failed', 'details': str(e)}), 500

@api_bp.route('/dictionaries', methods=['GET'])

def get_available_dictionaries() -> Tuple[Dict[str, Any], int]:
    """Get list of available industry dictionaries."""
    try:
        return jsonify({
            'dictionaries': {
                industry: {
                    'name': industry.title(),
                    'term_count': len(terms),
                    'sample_terms': list(terms.keys())[:5]
                }
                for industry, terms in INDUSTRY_DICTIONARIES.items()
            },
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dictionaries: {e}")
        return jsonify({'error': 'Dictionary retrieval failed', 'details': str(e)}), 500

@api_bp.route('/dictionaries/<industry>', methods=['GET'])

def get_industry_dictionary_endpoint(industry: str) -> Tuple[Dict[str, Any], int]:
    """Get specific industry dictionary."""
    try:
        dictionary = get_industry_dictionary(industry)
        
        if not dictionary:
            return jsonify({'error': 'Industry dictionary not found'}), 404
        
        return jsonify({
            'industry': industry,
            'dictionary': dictionary,
            'term_count': len(dictionary),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting industry dictionary {industry}: {e}")
        return jsonify({'error': 'Dictionary retrieval failed', 'details': str(e)}), 500

@api_bp.route('/dictionaries/custom', methods=['POST', 'PUT'])

def update_custom_dictionary() -> Tuple[Dict[str, Any], int]:
    """
    Update custom dictionary with new terms.
    
    Body Parameters:
    - terms: Dictionary of term -> replacement mappings
    """
    try:
        data = request.get_json()
        if not data or 'terms' not in data:
            return jsonify({'error': 'Terms dictionary required'}), 400
        
        new_terms = data['terms']
        if not isinstance(new_terms, dict):
            return jsonify({'error': 'Terms must be a dictionary'}), 400
        
        engine = get_correction_engine()
        engine.update_custom_dictionary(new_terms)
        
        return jsonify({
            'updated_terms': new_terms,
            'total_custom_terms': len(engine.custom_dictionary),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating custom dictionary: {e}")
        return jsonify({'error': 'Dictionary update failed', 'details': str(e)}), 500

@api_bp.route('/statistics', methods=['GET'])

def get_correction_statistics() -> Tuple[Dict[str, Any], int]:
    """Get correction performance statistics."""
    try:
        engine = get_correction_engine()
        statistics = engine.get_correction_statistics()
        
        return jsonify({
            'statistics': statistics,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting correction statistics: {e}")
        return jsonify({'error': 'Statistics retrieval failed', 'details': str(e)}), 500

@api_bp.route('/batch-correct', methods=['POST'])

def batch_correct_transcripts() -> Tuple[Dict[str, Any], int]:
    """
    Apply batch corrections to multiple transcripts.
    
    Body Parameters:
    - transcripts: List of transcript objects with id and text
    - auto_apply: Whether to auto-apply high-confidence corrections
    - industry: Optional industry dictionary to use
    """
    try:
        data = request.get_json()
        if not data or 'transcripts' not in data:
            return jsonify({'error': 'Transcripts list required'}), 400
        
        transcripts = data['transcripts']
        auto_apply = data.get('auto_apply', False)
        industry = data.get('industry')
        
        # Update dictionary if industry specified
        engine = get_correction_engine()
        if industry:
            industry_dict = get_industry_dictionary(industry)
            engine.update_custom_dictionary(industry_dict)
        
        results = []
        for transcript in transcripts:
            if not isinstance(transcript, dict) or 'id' not in transcript or 'text' not in transcript:
                continue
            
            try:
                # Generate corrections
                suggestions = engine.generate_corrections(transcript['text'])
                
                # Apply corrections if requested
                corrected_text = transcript['text']
                if auto_apply:
                    corrected_text = engine.apply_corrections(transcript['text'], suggestions)
                
                # Analyze quality
                quality_before = engine.analyze_transcript_quality(transcript['text'])
                quality_after = engine.analyze_transcript_quality(corrected_text)
                
                results.append({
                    'id': transcript['id'],
                    'original_text': transcript['text'],
                    'corrected_text': corrected_text,
                    'suggestions_count': len(suggestions),
                    'quality_improvement': quality_after.overall_score - quality_before.overall_score,
                    'quality_before': quality_before.overall_score,
                    'quality_after': quality_after.overall_score
                })
                
            except Exception as e:
                logger.error(f"Error processing transcript {transcript.get('id', 'unknown')}: {e}")
                results.append({
                    'id': transcript.get('id', 'unknown'),
                    'error': str(e)
                })
        
        return jsonify({
            'results': results,
            'total_processed': len(results),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch correction: {e}")
        return jsonify({'error': 'Batch correction failed', 'details': str(e)}), 500

def _generate_quality_recommendations(quality_metrics: QualityMetrics) -> List[str]:
    """Generate quality improvement recommendations based on metrics."""
    recommendations = []
    
    if quality_metrics.grammar_score < 70:
        recommendations.append("Consider reviewing grammar issues - multiple grammatical errors detected")
    
    if quality_metrics.spelling_score < 80:
        recommendations.append("Spelling corrections recommended - several misspelled words found")
    
    if quality_metrics.readability_score < 60:
        recommendations.append("Text readability could be improved - consider shorter sentences")
    
    if quality_metrics.confidence_score < 70:
        recommendations.append("Low transcription confidence detected - manual review recommended")
    
    if quality_metrics.overall_score > 90:
        recommendations.append("Excellent transcript quality - minimal corrections needed")
    elif quality_metrics.overall_score > 75:
        recommendations.append("Good transcript quality - minor improvements possible")
    else:
        recommendations.append("Transcript quality needs improvement - consider automated corrections")
    
    return recommendations


@api_bp.route('/learn', methods=['POST'])

def learn_from_correction():
    """Learn from a user correction to improve future suggestions."""
    try:
        data = request.get_json()
        original_text = data.get('original_text', '').strip()
        corrected_text = data.get('corrected_text', '').strip()
        correction_type = data.get('correction_type', 'manual')
        confidence = data.get('confidence', 1.0)
        session_id = data.get('session_id')
        
        if not original_text or not corrected_text:
            return jsonify({
                'success': False,
                'error': 'Both original and corrected text are required'
            }), 400
        
        engine = get_correction_engine()
        if not engine:
            return jsonify({
                'success': False,
                'error': 'Correction engine not available'
            }), 503
        
        # Learn from the correction
        learning_data = {
            'original': original_text,
            'corrected': corrected_text,
            'type': correction_type,
            'confidence': confidence,
            'user_id': 'anonymous',
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        engine.learn_from_correction(learning_data)
        
        return jsonify({
            'success': True,
            'message': 'Learning data recorded successfully'
        })
        
    except Exception as e:
        logger.error(f"Learning error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to record learning data'
        }), 500


@api_bp.route('/export', methods=['POST'])

def export_corrected_transcript():
    """Export a corrected transcript in various formats."""
    try:
        data = request.get_json()
        transcript = data.get('transcript', '').strip()
        session_id = data.get('session_id')
        format_type = data.get('format', 'txt').lower()
        
        if not transcript:
            return jsonify({
                'success': False,
                'error': 'Transcript content is required'
            }), 400
        
        # Supported export formats
        supported_formats = ['txt', 'srt', 'vtt', 'json']
        if format_type not in supported_formats:
            return jsonify({
                'success': False,
                'error': f'Unsupported format. Supported: {", ".join(supported_formats)}'
            }), 400
        
        # Generate export content
        if format_type == 'txt':
            content = transcript
            mimetype = 'text/plain'
            filename = f'corrected_transcript_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        elif format_type == 'json':
            export_data = {
                'transcript': transcript,
                'session_id': session_id,
                'exported_at': datetime.utcnow().isoformat(),
                'exported_by': 'anonymous',
                'format': 'corrected_transcript'
            }
            content = json.dumps(export_data, indent=2)
            mimetype = 'application/json'
            filename = f'corrected_transcript_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        else:
            # For SRT and VTT, we need to format with timestamps
            # This is a simplified version - in practice, you'd need actual timestamps
            lines = transcript.split('\n')
            if format_type == 'srt':
                content = ""
                for i, line in enumerate(lines, 1):
                    if line.strip():
                        start_time = f"00:00:{i*5:02d},000"
                        end_time = f"00:00:{(i+1)*5:02d},000"
                        content += f"{i}\n{start_time} --> {end_time}\n{line}\n\n"
                mimetype = 'text/plain'
                filename = f'corrected_transcript_{datetime.now().strftime("%Y%m%d_%H%M%S")}.srt'
            
            else:  # VTT
                content = "WEBVTT\n\n"
                for i, line in enumerate(lines, 1):
                    if line.strip():
                        start_time = f"00:00:{i*5:02d}.000"
                        end_time = f"00:00:{(i+1)*5:02d}.000"
                        content += f"{start_time} --> {end_time}\n{line}\n\n"
                mimetype = 'text/plain'
                filename = f'corrected_transcript_{datetime.now().strftime("%Y%m%d_%H%M%S")}.vtt'
        
        from flask import Response
        return Response(
            content,
            mimetype=mimetype,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': mimetype
            }
        )
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to export transcript'
        }), 500


# Register both blueprints - the main correction blueprint and the API blueprint
def register_correction_blueprints(app):
    """Register both correction blueprints with the Flask app."""
    app.register_blueprint(correction_bp)
    app.register_blueprint(api_bp)
