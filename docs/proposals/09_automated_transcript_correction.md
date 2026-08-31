# Automated Transcript Correction & Quality Assurance

## 🎯 Issue Overview

**Priority**: ⭐⭐⭐ High Priority  
**Epic**: User Experience & Accessibility  
**Estimated Effort**: 6-8 weeks  
**Dependencies**: Core transcription service, AI insights integration

### Problem Statement

Manual transcript editing is time-consuming and error-prone. Users spend significant time correcting transcription mistakes, especially for:
- Technical terms and industry jargon
- Proper nouns (names, places, companies)  
- Punctuation and formatting inconsistencies
- Low-confidence segments that need human review
- Repetitive corrections across multiple sessions

### Solution Overview

Implement an intelligent transcript correction and quality assurance system that automatically identifies and fixes common transcription errors, provides confidence-based recommendations, and learns from user corrections to improve future accuracy.

## ✨ Features & Capabilities

### 🔧 Core Features

#### AI-Powered Auto-Correction Engine
- Grammar, punctuation, and spelling correction
- Context-aware sentence structure improvements
- Industry-specific terminology detection and correction
- Proper noun identification and standardization

#### Confidence-Based Quality Assessment
- Visual indicators for low-confidence segments
- Quality scoring with actionable recommendations  
- Segment-level accuracy prediction
- User feedback integration for continuous improvement

#### Custom Dictionary & Learning System
- User-defined terminology and jargon database
- Organization-wide shared dictionaries
- Machine learning from user corrections
- Industry template libraries (medical, legal, technical, etc.)

#### Advanced Correction Tools
- Bulk find & replace with regex support
- Suggested corrections with confidence scores
- Batch operations across multiple sessions
- Correction history and rollback functionality

## 🏗️ Technical Implementation

### Phase 1: Core Auto-Correction Engine (2 weeks)

#### Task 1.1: Grammar & Spelling Correction Service
**File**: `src/services/transcript_correction.py`

```python
"""
Automated transcript correction service using NLP and machine learning.
Provides intelligent correction suggestions and quality assessment.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

try:
    import spacy
    from textblob import TextBlob
    import language_tool_python
    CORRECTION_AVAILABLE = True
except ImportError:
    CORRECTION_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class CorrectionSuggestion:
    """Represents a single correction suggestion."""
    original_text: str
    suggested_text: str
    confidence: float
    correction_type: str  # 'grammar', 'spelling', 'punctuation', 'terminology'
    start_position: int
    end_position: int
    explanation: str
    auto_apply: bool = False

@dataclass
class QualityMetrics:
    """Quality assessment metrics for a transcript segment."""
    overall_score: float  # 0-100
    confidence_score: float
    grammar_score: float
    spelling_score: float
    readability_score: float
    issues_count: int
    suggestions_count: int

class TranscriptCorrectionEngine:
    """Main engine for automated transcript correction and quality assessment."""
    
    def __init__(self, custom_dictionary: Optional[Dict[str, str]] = None):
        """Initialize the correction engine with optional custom dictionary."""
        self.custom_dictionary = custom_dictionary or {}
        self.user_corrections = {}  # Learn from user corrections
        self.grammar_tool = None
        self.nlp_model = None
        
        if CORRECTION_AVAILABLE:
            try:
                self.grammar_tool = language_tool_python.LanguageTool('en-US')
                self.nlp_model = spacy.load('en_core_web_sm')
                logger.info("Correction engine initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize correction tools: {e}")
                
    def analyze_transcript_quality(self, transcript_text: str, 
                                 segments: List[Dict] = None) -> QualityMetrics:
        """
        Analyze overall transcript quality and return metrics.
        
        Args:
            transcript_text: Full transcript text
            segments: Optional list of transcript segments with timing
            
        Returns:
            QualityMetrics object with quality assessment
        """
        if not CORRECTION_AVAILABLE:
            return QualityMetrics(
                overall_score=75.0,  # Default score
                confidence_score=80.0,
                grammar_score=70.0,
                spelling_score=80.0,
                readability_score=75.0,
                issues_count=0,
                suggestions_count=0
            )
            
        try:
            # Grammar analysis
            grammar_issues = self.grammar_tool.check(transcript_text)
            grammar_score = max(0, 100 - len(grammar_issues) * 2)
            
            # Spelling analysis using TextBlob
            blob = TextBlob(transcript_text)
            corrected_text = str(blob.correct())
            spelling_score = 100 if corrected_text == transcript_text else 85
            
            # Readability analysis
            readability_score = self._calculate_readability(transcript_text)
            
            # Confidence analysis from segments
            confidence_score = self._analyze_segment_confidence(segments or [])
            
            # Overall score calculation
            overall_score = (grammar_score * 0.3 + spelling_score * 0.25 + 
                           readability_score * 0.25 + confidence_score * 0.2)
            
            return QualityMetrics(
                overall_score=round(overall_score, 1),
                confidence_score=round(confidence_score, 1),
                grammar_score=round(grammar_score, 1),
                spelling_score=round(spelling_score, 1),
                readability_score=round(readability_score, 1),
                issues_count=len(grammar_issues),
                suggestions_count=len(grammar_issues) + (0 if corrected_text == transcript_text else 1)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing transcript quality: {e}")
            return QualityMetrics(
                overall_score=50.0,
                confidence_score=50.0,
                grammar_score=50.0,
                spelling_score=50.0,
                readability_score=50.0,
                issues_count=0,
                suggestions_count=0
            )
    
    def generate_corrections(self, text: str, segment_confidence: float = 1.0) -> List[CorrectionSuggestion]:
        """
        Generate correction suggestions for a text segment.
        
        Args:
            text: Text to analyze and correct
            segment_confidence: Confidence score from transcription (0-1)
            
        Returns:
            List of CorrectionSuggestion objects
        """
        suggestions = []
        
        if not CORRECTION_AVAILABLE:
            return suggestions
            
        try:
            # Grammar corrections
            grammar_issues = self.grammar_tool.check(text)
            for issue in grammar_issues:
                if issue.replacements:
                    suggestions.append(CorrectionSuggestion(
                        original_text=text[issue.offset:issue.offset + issue.errorLength],
                        suggested_text=issue.replacements[0],
                        confidence=0.9 if segment_confidence > 0.8 else 0.7,
                        correction_type='grammar',
                        start_position=issue.offset,
                        end_position=issue.offset + issue.errorLength,
                        explanation=issue.message,
                        auto_apply=segment_confidence < 0.6  # Auto-apply for low confidence
                    ))
            
            # Spelling corrections
            blob = TextBlob(text)
            corrected_text = str(blob.correct())
            if corrected_text != text:
                suggestions.append(CorrectionSuggestion(
                    original_text=text,
                    suggested_text=corrected_text,
                    confidence=0.8,
                    correction_type='spelling',
                    start_position=0,
                    end_position=len(text),
                    explanation="Spelling corrections applied",
                    auto_apply=False
                ))
            
            # Custom dictionary corrections
            for term, replacement in self.custom_dictionary.items():
                if term.lower() in text.lower():
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    if pattern.search(text):
                        suggestions.append(CorrectionSuggestion(
                            original_text=term,
                            suggested_text=replacement,
                            confidence=0.95,
                            correction_type='terminology',
                            start_position=text.lower().find(term.lower()),
                            end_position=text.lower().find(term.lower()) + len(term),
                            explanation=f"Custom dictionary term: {term} → {replacement}",
                            auto_apply=True
                        ))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating corrections: {e}")
            return suggestions
    
    def apply_corrections(self, text: str, corrections: List[CorrectionSuggestion]) -> str:
        """
        Apply a list of corrections to text.
        
        Args:
            text: Original text
            corrections: List of corrections to apply
            
        Returns:
            Corrected text
        """
        corrected_text = text
        
        # Sort corrections by position (reverse order to maintain positions)
        corrections.sort(key=lambda x: x.start_position, reverse=True)
        
        for correction in corrections:
            if correction.auto_apply or correction.confidence > 0.9:
                corrected_text = (
                    corrected_text[:correction.start_position] +
                    correction.suggested_text +
                    corrected_text[correction.end_position:]
                )
        
        return corrected_text
    
    def learn_from_correction(self, original: str, corrected: str, correction_type: str):
        """
        Learn from user corrections to improve future suggestions.
        
        Args:
            original: Original text
            corrected: User-corrected text
            correction_type: Type of correction made
        """
        key = f"{correction_type}:{original.lower()}"
        self.user_corrections[key] = corrected
        
        # Add to custom dictionary if it's a terminology correction
        if correction_type == 'terminology':
            self.custom_dictionary[original] = corrected
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score using various metrics."""
        try:
            blob = TextBlob(text)
            sentences = len(blob.sentences)
            words = len(blob.words)
            
            if sentences == 0:
                return 50.0
                
            avg_sentence_length = words / sentences
            
            # Simple readability score (inverted - shorter sentences = better)
            readability = max(0, 100 - (avg_sentence_length - 15) * 2)
            return min(100, readability)
            
        except Exception:
            return 75.0
    
    def _analyze_segment_confidence(self, segments: List[Dict]) -> float:
        """Analyze confidence scores from transcript segments."""
        if not segments:
            return 80.0
            
        confidences = [seg.get('confidence', 0.8) for seg in segments]
        avg_confidence = sum(confidences) / len(confidences)
        return avg_confidence * 100

# Factory function for creating correction engine
def create_correction_engine(custom_dictionary: Dict[str, str] = None) -> TranscriptCorrectionEngine:
    """Create and return a transcript correction engine."""
    return TranscriptCorrectionEngine(custom_dictionary)
```

**Acceptance Criteria**:
- ✅ Grammar correction using LanguageTool integration
- ✅ Spelling correction using TextBlob
- ✅ Quality metrics calculation (grammar, spelling, readability, confidence)
- ✅ Custom dictionary support for terminology
- ✅ Learning system for user corrections
- ✅ Confidence-based auto-correction
- ✅ Graceful degradation when NLP libraries unavailable

#### Task 1.2: Correction API Endpoints
**File**: `src/routes/correction_routes.py`

```python
"""
API routes for transcript correction and quality assurance functionality.
Provides endpoints for analyzing quality, generating corrections, and managing dictionaries.
"""

import json
import logging
from typing import Dict, List, Any, Tuple
from flask import Blueprint, request, jsonify, current_app

from src.services.transcript_correction import create_correction_engine, CORRECTION_AVAILABLE

logger = logging.getLogger(__name__)

# Create blueprint for correction routes
correction_bp = Blueprint('correction', __name__, url_prefix='/api/correction')

@correction_bp.route('/status', methods=['GET'])
def get_correction_status() -> Tuple[Dict[str, Any], int]:
    """Get transcript correction service status and capabilities."""
    try:
        return jsonify({
            'available': CORRECTION_AVAILABLE,
            'features': {
                'grammar_correction': CORRECTION_AVAILABLE,
                'spelling_correction': CORRECTION_AVAILABLE,
                'quality_assessment': True,
                'custom_dictionary': True,
                'batch_processing': True,
                'learning_system': True
            },
            'version': '1.0.0',
            'supported_languages': ['en-US', 'en-GB'] if CORRECTION_AVAILABLE else []
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting correction status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500

@correction_bp.route('/analyze/<session_id>', methods=['POST'])
def analyze_transcript_quality(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Analyze transcript quality for a session.
    
    Body Parameters:
    - custom_dictionary (optional): Dict of custom terms
    - include_suggestions (optional): Whether to include correction suggestions
    """
    try:
        data = request.get_json() or {}
        
        # Load session data
        results_folder = current_app.config.get('RESULTS_FOLDER', 'results')
        session_data = load_session_data(session_id, results_folder)
        
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
            
        # Get transcript and segments
        transcript_text = session_data.get('transcript', '')
        segments = session_data.get('segments', [])
        
        # Create correction engine with custom dictionary
        custom_dict = data.get('custom_dictionary', {})
        engine = create_correction_engine(custom_dict)
        
        # Analyze quality
        quality_metrics = engine.analyze_transcript_quality(transcript_text, segments)
        
        response = {
            'session_id': session_id,
            'quality_metrics': {
                'overall_score': quality_metrics.overall_score,
                'confidence_score': quality_metrics.confidence_score,
                'grammar_score': quality_metrics.grammar_score,
                'spelling_score': quality_metrics.spelling_score,
                'readability_score': quality_metrics.readability_score,
                'issues_count': quality_metrics.issues_count,
                'suggestions_count': quality_metrics.suggestions_count
            },
            'assessment': _get_quality_assessment(quality_metrics.overall_score),
            'recommendations': _get_quality_recommendations(quality_metrics)
        }
        
        # Include suggestions if requested
        if data.get('include_suggestions', False):
            suggestions = []
            for segment in segments[:10]:  # Limit to first 10 segments
                segment_suggestions = engine.generate_corrections(
                    segment.get('text', ''),
                    segment.get('confidence', 1.0)
                )
                suggestions.extend([{
                    'segment_index': segments.index(segment),
                    'original_text': s.original_text,
                    'suggested_text': s.suggested_text,
                    'confidence': s.confidence,
                    'correction_type': s.correction_type,
                    'explanation': s.explanation,
                    'auto_apply': s.auto_apply
                } for s in segment_suggestions])
            
            response['suggestions'] = suggestions[:50]  # Limit total suggestions
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error analyzing transcript quality: {e}")
        return jsonify({'error': 'Failed to analyze quality', 'details': str(e)}), 500

@correction_bp.route('/correct/<session_id>', methods=['POST'])
def apply_corrections(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Apply corrections to a transcript session.
    
    Body Parameters:
    - corrections: List of corrections to apply
    - auto_apply_high_confidence: Whether to auto-apply high-confidence corrections
    - custom_dictionary: Custom dictionary for terminology
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
            
        # Load session data
        results_folder = current_app.config.get('RESULTS_FOLDER', 'results')
        session_data = load_session_data(session_id, results_folder)
        
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
            
        # Create correction engine
        custom_dict = data.get('custom_dictionary', {})
        engine = create_correction_engine(custom_dict)
        
        # Get corrections to apply
        requested_corrections = data.get('corrections', [])
        auto_apply_high_confidence = data.get('auto_apply_high_confidence', True)
        
        # Apply corrections to segments
        corrected_segments = []
        total_corrections = 0
        
        for segment in session_data.get('segments', []):
            original_text = segment.get('text', '')
            
            # Generate suggestions for this segment
            suggestions = engine.generate_corrections(
                original_text,
                segment.get('confidence', 1.0)
            )
            
            # Filter corrections to apply
            corrections_to_apply = []
            
            if auto_apply_high_confidence:
                corrections_to_apply.extend([s for s in suggestions if s.auto_apply or s.confidence > 0.9])
            
            # Add user-requested corrections
            for req_correction in requested_corrections:
                if req_correction.get('segment_index') == session_data['segments'].index(segment):
                    corrections_to_apply.append(req_correction)
            
            # Apply corrections
            corrected_text = engine.apply_corrections(original_text, suggestions)
            
            corrected_segment = segment.copy()
            corrected_segment['text'] = corrected_text
            corrected_segment['corrections_applied'] = len(corrections_to_apply)
            corrected_segments.append(corrected_segment)
            
            total_corrections += len(corrections_to_apply)
        
        # Update session data
        session_data['segments'] = corrected_segments
        session_data['transcript'] = ' '.join([seg['text'] for seg in corrected_segments])
        session_data['correction_history'] = session_data.get('correction_history', []) + [{
            'timestamp': datetime.now().isoformat(),
            'corrections_applied': total_corrections,
            'auto_applied': auto_apply_high_confidence
        }]
        
        # Save updated session
        save_session_data(session_id, session_data, results_folder)
        
        return jsonify({
            'session_id': session_id,
            'corrections_applied': total_corrections,
            'segments_updated': len(corrected_segments),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error applying corrections: {e}")
        return jsonify({'error': 'Failed to apply corrections', 'details': str(e)}), 500

@correction_bp.route('/dictionary', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_custom_dictionary() -> Tuple[Dict[str, Any], int]:
    """Manage custom dictionary for terminology corrections."""
    try:
        if request.method == 'GET':
            # Get current dictionary
            dictionary_file = current_app.config.get('CUSTOM_DICTIONARY_FILE', 'data/config/custom_dictionary.json')
            dictionary = load_custom_dictionary(dictionary_file)
            
            return jsonify({
                'dictionary': dictionary,
                'entry_count': len(dictionary),
                'last_updated': get_dictionary_last_updated(dictionary_file)
            }), 200
            
        elif request.method == 'POST':
            # Add new entries
            data = request.get_json()
            if not data or 'entries' not in data:
                return jsonify({'error': 'Entries required'}), 400
                
            dictionary_file = current_app.config.get('CUSTOM_DICTIONARY_FILE', 'data/config/custom_dictionary.json')
            dictionary = load_custom_dictionary(dictionary_file)
            
            entries_added = 0
            for entry in data['entries']:
                if 'term' in entry and 'replacement' in entry:
                    dictionary[entry['term']] = entry['replacement']
                    entries_added += 1
            
            save_custom_dictionary(dictionary, dictionary_file)
            
            return jsonify({
                'entries_added': entries_added,
                'total_entries': len(dictionary),
                'success': True
            }), 200
            
        elif request.method == 'DELETE':
            # Remove entries
            data = request.get_json()
            if not data or 'terms' not in data:
                return jsonify({'error': 'Terms to delete required'}), 400
                
            dictionary_file = current_app.config.get('CUSTOM_DICTIONARY_FILE', 'data/config/custom_dictionary.json')
            dictionary = load_custom_dictionary(dictionary_file)
            
            entries_removed = 0
            for term in data['terms']:
                if term in dictionary:
                    del dictionary[term]
                    entries_removed += 1
            
            save_custom_dictionary(dictionary, dictionary_file)
            
            return jsonify({
                'entries_removed': entries_removed,
                'total_entries': len(dictionary),
                'success': True
            }), 200
            
    except Exception as e:
        logger.error(f"Error managing dictionary: {e}")
        return jsonify({'error': 'Dictionary operation failed', 'details': str(e)}), 500

# Helper functions
def load_session_data(session_id: str, results_folder: str) -> Dict[str, Any]:
    """Load session data from file."""
    try:
        session_file = f"{results_folder}/{session_id}/session_data.json"
        with open(session_file, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_session_data(session_id: str, data: Dict[str, Any], results_folder: str):
    """Save session data to file."""
    import os
    session_dir = f"{results_folder}/{session_id}"
    os.makedirs(session_dir, exist_ok=True)
    
    session_file = f"{session_dir}/session_data.json"
    with open(session_file, 'w') as f:
        json.dump(data, f, indent=2)

def load_custom_dictionary(file_path: str) -> Dict[str, str]:
    """Load custom dictionary from file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_custom_dictionary(dictionary: Dict[str, str], file_path: str):
    """Save custom dictionary to file."""
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(dictionary, f, indent=2)

def get_dictionary_last_updated(file_path: str) -> str:
    """Get last updated timestamp for dictionary file."""
    try:
        import os
        timestamp = os.path.getmtime(file_path)
        return datetime.fromtimestamp(timestamp).isoformat()
    except Exception:
        return "Unknown"

def _get_quality_assessment(score: float) -> str:
    """Get quality assessment based on score."""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 70:
        return "Fair"
    elif score >= 60:
        return "Poor"
    else:
        return "Needs Major Improvement"

def _get_quality_recommendations(metrics) -> List[str]:
    """Get quality improvement recommendations."""
    recommendations = []
    
    if metrics.grammar_score < 80:
        recommendations.append("Consider reviewing grammar and sentence structure")
    
    if metrics.spelling_score < 85:
        recommendations.append("Run spelling correction on the transcript")
    
    if metrics.confidence_score < 70:
        recommendations.append("Review low-confidence segments for accuracy")
    
    if metrics.readability_score < 75:
        recommendations.append("Consider breaking up long sentences for better readability")
    
    if metrics.issues_count > 10:
        recommendations.append("Apply auto-corrections to fix common issues")
    
    return recommendations
```

**Acceptance Criteria**:
- ✅ Quality analysis endpoint with detailed metrics
- ✅ Correction application with user preferences
- ✅ Custom dictionary management (CRUD operations)
- ✅ Session data integration and persistence
- ✅ Comprehensive error handling and logging
- ✅ Support for batch corrections and auto-apply

### Phase 2: Quality Assessment UI (2 weeks)

#### Task 2.1: Quality Dashboard Component
**File**: `data/static/js/transcript-quality.js`

```javascript
/**
 * Transcript Quality Assessment Dashboard
 * Provides real-time quality analysis and correction suggestions
 */

class TranscriptQualityManager {
    constructor() {
        this.sessionId = null;
        this.qualityData = null;
        this.corrections = [];
        this.customDictionary = {};
        this.isAnalyzing = false;
        
        this.initializeEventListeners();
    }
    
    /**
     * Initialize the quality dashboard for a session
     */
    async initializeQualityDashboard(sessionId) {
        this.sessionId = sessionId;
        
        try {
            // Show quality dashboard
            this.showQualityDashboard();
            
            // Check correction service status
            const status = await this.checkCorrectionStatus();
            if (!status.available) {
                this.showUnavailableMessage();
                return;
            }
            
            // Analyze transcript quality
            await this.analyzeQuality();
            
        } catch (error) {
            console.error('Error initializing quality dashboard:', error);
            this.showErrorMessage('Failed to initialize quality dashboard');
        }
    }
    
    /**
     * Analyze transcript quality
     */
    async analyzeQuality(includeSuggestions = true) {
        if (this.isAnalyzing) return;
        
        this.isAnalyzing = true;
        this.showAnalyzingIndicator();
        
        try {
            const response = await fetch(`/api/correction/analyze/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    custom_dictionary: this.customDictionary,
                    include_suggestions: includeSuggestions
                })
            });
            
            if (!response.ok) {
                throw new Error(`Analysis failed: ${response.statusText}`);
            }
            
            this.qualityData = await response.json();
            this.corrections = this.qualityData.suggestions || [];
            
            // Update UI with quality results
            this.displayQualityMetrics();
            this.displayCorrections();
            
        } catch (error) {
            console.error('Error analyzing quality:', error);
            this.showErrorMessage('Failed to analyze transcript quality');
        } finally {
            this.isAnalyzing = false;
            this.hideAnalyzingIndicator();
        }
    }
    
    /**
     * Display quality metrics with visual indicators
     */
    displayQualityMetrics() {
        const metrics = this.qualityData.quality_metrics;
        
        const qualityHtml = `
            <div class="quality-metrics-container">
                <div class="quality-header">
                    <h3>📊 Transcript Quality Assessment</h3>
                    <span class="quality-badge ${this.getQualityBadgeClass(metrics.overall_score)}">
                        ${this.qualityData.assessment}
                    </span>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Overall Score</div>
                        <div class="metric-value">
                            <span class="score">${metrics.overall_score}%</span>
                            <div class="score-bar">
                                <div class="score-fill" style="width: ${metrics.overall_score}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Grammar</div>
                        <div class="metric-value">
                            <span class="score">${metrics.grammar_score}%</span>
                            <div class="score-bar">
                                <div class="score-fill grammar" style="width: ${metrics.grammar_score}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Spelling</div>
                        <div class="metric-value">
                            <span class="score">${metrics.spelling_score}%</span>
                            <div class="score-bar">
                                <div class="score-fill spelling" style="width: ${metrics.spelling_score}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-label">Confidence</div>
                        <div class="metric-value">
                            <span class="score">${metrics.confidence_score}%</span>
                            <div class="score-bar">
                                <div class="score-fill confidence" style="width: ${metrics.confidence_score}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="quality-summary">
                    <div class="issues-count">
                        <span class="count">${metrics.issues_count}</span> issues found
                    </div>
                    <div class="suggestions-count">
                        <span class="count">${metrics.suggestions_count}</span> corrections available
                    </div>
                </div>
                
                <div class="recommendations">
                    <h4>💡 Recommendations</h4>
                    <ul>
                        ${this.qualityData.recommendations.map(rec => 
                            `<li>${rec}</li>`
                        ).join('')}
                    </ul>
                </div>
            </div>
        `;
        
        document.getElementById('qualityMetrics').innerHTML = qualityHtml;
    }
    
    /**
     * Display correction suggestions with interactive controls
     */
    displayCorrections() {
        if (!this.corrections.length) {
            document.getElementById('correctionsList').innerHTML = 
                '<div class="no-corrections">✅ No corrections needed</div>';
            return;
        }
        
        const correctionsHtml = `
            <div class="corrections-container">
                <div class="corrections-header">
                    <h3>🔧 Suggested Corrections</h3>
                    <div class="corrections-controls">
                        <button class="btn btn-primary" onclick="qualityManager.applyAllHighConfidence()">
                            Apply High Confidence (${this.getHighConfidenceCount()})
                        </button>
                        <button class="btn btn-outline-secondary" onclick="qualityManager.toggleCorrectionTypes()">
                            Filter Types
                        </button>
                    </div>
                </div>
                
                <div class="corrections-list">
                    ${this.corrections.map((correction, index) => 
                        this.renderCorrectionItem(correction, index)
                    ).join('')}
                </div>
            </div>
        `;
        
        document.getElementById('correctionsList').innerHTML = correctionsHtml;
    }
    
    /**
     * Render individual correction item
     */
    renderCorrectionItem(correction, index) {
        const confidenceClass = correction.confidence > 0.9 ? 'high' : 
                               correction.confidence > 0.7 ? 'medium' : 'low';
        
        return `
            <div class="correction-item ${confidenceClass}" data-index="${index}">
                <div class="correction-header">
                    <span class="correction-type ${correction.correction_type}">
                        ${this.getCorrectionTypeIcon(correction.correction_type)}
                        ${correction.correction_type}
                    </span>
                    <span class="confidence-badge ${confidenceClass}">
                        ${Math.round(correction.confidence * 100)}%
                    </span>
                </div>
                
                <div class="correction-content">
                    <div class="text-comparison">
                        <div class="original-text">
                            <label>Original:</label>
                            <span class="text-content">"${correction.original_text}"</span>
                        </div>
                        <div class="suggested-text">
                            <label>Suggested:</label>
                            <span class="text-content">"${correction.suggested_text}"</span>
                        </div>
                    </div>
                    
                    <div class="correction-explanation">
                        <small>${correction.explanation}</small>
                    </div>
                </div>
                
                <div class="correction-actions">
                    <button class="btn btn-success btn-sm" 
                            onclick="qualityManager.applyCorrection(${index})">
                        ✓ Apply
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" 
                            onclick="qualityManager.ignoreCorrection(${index})">
                        ✗ Ignore
                    </button>
                    <button class="btn btn-outline-info btn-sm" 
                            onclick="qualityManager.editCorrection(${index})">
                        ✏️ Edit
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Apply selected corrections to the transcript
     */
    async applyCorrections(correctionIndices = []) {
        try {
            const correctionsToApply = correctionIndices.length ? 
                correctionIndices.map(i => this.corrections[i]) : 
                this.corrections.filter(c => c.auto_apply);
            
            const response = await fetch(`/api/correction/correct/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    corrections: correctionsToApply,
                    auto_apply_high_confidence: true,
                    custom_dictionary: this.customDictionary
                })
            });
            
            if (!response.ok) {
                throw new Error(`Correction failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Show success message
            this.showSuccessMessage(
                `Applied ${result.corrections_applied} corrections to ${result.segments_updated} segments`
            );
            
            // Refresh the transcript view
            if (window.transcriptViewer) {
                window.transcriptViewer.refreshTranscript();
            }
            
            // Re-analyze quality
            await this.analyzeQuality(false);
            
        } catch (error) {
            console.error('Error applying corrections:', error);
            this.showErrorMessage('Failed to apply corrections');
        }
    }
    
    /**
     * Custom dictionary management
     */
    async manageCustomDictionary() {
        const modalHtml = `
            <div class="dictionary-modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>📖 Custom Dictionary</h3>
                        <button class="close-btn" onclick="qualityManager.closeDictionaryModal()">×</button>
                    </div>
                    
                    <div class="modal-body">
                        <div class="dictionary-tabs">
                            <button class="tab-btn active" data-tab="existing">Current Terms</button>
                            <button class="tab-btn" data-tab="add">Add Terms</button>
                            <button class="tab-btn" data-tab="import">Import/Export</button>
                        </div>
                        
                        <div class="tab-content" id="existing">
                            <div id="dictionaryList">Loading...</div>
                        </div>
                        
                        <div class="tab-content" id="add" style="display: none;">
                            <div class="add-terms-form">
                                <textarea id="newTerms" placeholder="Enter terms in format: original_term -> replacement_term (one per line)"></textarea>
                                <button class="btn btn-primary" onclick="qualityManager.addCustomTerms()">Add Terms</button>
                            </div>
                        </div>
                        
                        <div class="tab-content" id="import" style="display: none;">
                            <div class="import-export-controls">
                                <input type="file" id="dictionaryFile" accept=".json" />
                                <button class="btn btn-outline-primary" onclick="qualityManager.importDictionary()">Import</button>
                                <button class="btn btn-outline-secondary" onclick="qualityManager.exportDictionary()">Export</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        await this.loadDictionaryTerms();
    }
    
    // Utility methods
    getQualityBadgeClass(score) {
        if (score >= 90) return 'excellent';
        if (score >= 80) return 'good';
        if (score >= 70) return 'fair';
        if (score >= 60) return 'poor';
        return 'very-poor';
    }
    
    getCorrectionTypeIcon(type) {
        const icons = {
            'grammar': '📝',
            'spelling': '🔤',
            'punctuation': '⏺️',
            'terminology': '📖'
        };
        return icons[type] || '🔧';
    }
    
    getHighConfidenceCount() {
        return this.corrections.filter(c => c.confidence > 0.9).length;
    }
    
    // Event handlers
    initializeEventListeners() {
        // Add keyboard shortcuts for common actions
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'q':
                        e.preventDefault();
                        this.analyzeQuality();
                        break;
                    case 'a':
                        e.preventDefault();
                        this.applyAllHighConfidence();
                        break;
                }
            }
        });
    }
    
    showAnalyzingIndicator() {
        // Implementation for loading indicator
    }
    
    hideAnalyzingIndicator() {
        // Implementation for hiding loading indicator
    }
    
    showSuccessMessage(message) {
        // Implementation for success notification
    }
    
    showErrorMessage(message) {
        // Implementation for error notification
    }
}

// Initialize global quality manager
const qualityManager = new TranscriptQualityManager();

// Export for module use
if (typeof module !== 'undefined') {
    module.exports = TranscriptQualityManager;
}
```

**Acceptance Criteria**:
- ✅ Interactive quality metrics dashboard with visual indicators
- ✅ Correction suggestions with confidence-based filtering
- ✅ One-click correction application with preview
- ✅ Custom dictionary management interface
- ✅ Keyboard shortcuts for power users
- ✅ Real-time updates and progress indicators

### Phase 3: Advanced Correction Features (2 weeks)

#### Task 3.1: Batch Operations & Learning System
**Additional endpoints in** `src/routes/correction_routes.py`

```python
@correction_bp.route('/batch/analyze', methods=['POST'])
def batch_analyze_quality() -> Tuple[Dict[str, Any], int]:
    """
    Analyze quality for multiple sessions in batch.
    
    Body Parameters:
    - session_ids: List of session IDs to analyze
    - custom_dictionary: Shared custom dictionary
    - parallel_processing: Whether to process in parallel
    """
    try:
        data = request.get_json()
        if not data or 'session_ids' not in data:
            return jsonify({'error': 'Session IDs required'}), 400
            
        session_ids = data['session_ids']
        custom_dict = data.get('custom_dictionary', {})
        parallel = data.get('parallel_processing', True)
        
        results = {}
        
        if parallel and len(session_ids) > 1:
            # Parallel processing for multiple sessions
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def analyze_session(session_id):
                engine = create_correction_engine(custom_dict)
                session_data = load_session_data(session_id, current_app.config.get('RESULTS_FOLDER'))
                if session_data:
                    quality = engine.analyze_transcript_quality(
                        session_data.get('transcript', ''),
                        session_data.get('segments', [])
                    )
                    return session_id, quality
                return session_id, None
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_session = {
                    executor.submit(analyze_session, session_id): session_id 
                    for session_id in session_ids
                }
                
                for future in as_completed(future_to_session):
                    session_id, quality = future.result()
                    if quality:
                        results[session_id] = {
                            'quality_metrics': {
                                'overall_score': quality.overall_score,
                                'confidence_score': quality.confidence_score,
                                'grammar_score': quality.grammar_score,
                                'spelling_score': quality.spelling_score,
                                'readability_score': quality.readability_score,
                                'issues_count': quality.issues_count
                            },
                            'assessment': _get_quality_assessment(quality.overall_score)
                        }
        else:
            # Sequential processing
            engine = create_correction_engine(custom_dict)
            for session_id in session_ids:
                session_data = load_session_data(session_id, current_app.config.get('RESULTS_FOLDER'))
                if session_data:
                    quality = engine.analyze_transcript_quality(
                        session_data.get('transcript', ''),
                        session_data.get('segments', [])
                    )
                    results[session_id] = {
                        'quality_metrics': {
                            'overall_score': quality.overall_score,
                            'confidence_score': quality.confidence_score,
                            'grammar_score': quality.grammar_score,
                            'spelling_score': quality.spelling_score,
                            'readability_score': quality.readability_score,
                            'issues_count': quality.issues_count
                        },
                        'assessment': _get_quality_assessment(quality.overall_score)
                    }
        
        # Calculate aggregate metrics
        scores = [r['quality_metrics']['overall_score'] for r in results.values()]
        aggregate_metrics = {
            'total_sessions': len(session_ids),
            'analyzed_sessions': len(results),
            'average_score': sum(scores) / len(scores) if scores else 0,
            'highest_score': max(scores) if scores else 0,
            'lowest_score': min(scores) if scores else 0,
            'sessions_needing_attention': len([s for s in scores if s < 70])
        }
        
        return jsonify({
            'results': results,
            'aggregate_metrics': aggregate_metrics,
            'processing_time': f"{len(session_ids)} sessions analyzed",
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return jsonify({'error': 'Batch analysis failed', 'details': str(e)}), 500

@correction_bp.route('/learn', methods=['POST'])
def learn_from_corrections() -> Tuple[Dict[str, Any], int]:
    """
    Learn from user corrections to improve future suggestions.
    
    Body Parameters:
    - corrections: List of user corrections with original/corrected text
    - session_id: Optional session ID for context
    - correction_type: Type of corrections being learned
    """
    try:
        data = request.get_json()
        if not data or 'corrections' not in data:
            return jsonify({'error': 'Corrections required'}), 400
            
        corrections = data['corrections']
        session_id = data.get('session_id')
        correction_type = data.get('correction_type', 'general')
        
        # Load or create learning data
        learning_file = current_app.config.get('LEARNING_DATA_FILE', 'data/config/learning_data.json')
        learning_data = load_learning_data(learning_file)
        
        # Process each correction
        learned_count = 0
        for correction in corrections:
            if 'original' in correction and 'corrected' in correction:
                original = correction['original']
                corrected = correction['corrected']
                
                # Add to learning data
                key = f"{correction_type}:{original.lower()}"
                learning_data[key] = {
                    'corrected': corrected,
                    'frequency': learning_data.get(key, {}).get('frequency', 0) + 1,
                    'last_seen': datetime.now().isoformat(),
                    'session_id': session_id,
                    'confidence': correction.get('confidence', 0.8)
                }
                learned_count += 1
        
        # Save learning data
        save_learning_data(learning_data, learning_file)
        
        # Update global custom dictionary with high-frequency corrections
        dictionary_file = current_app.config.get('CUSTOM_DICTIONARY_FILE', 'data/config/custom_dictionary.json')
        dictionary = load_custom_dictionary(dictionary_file)
        
        updates_made = 0
        for key, data in learning_data.items():
            if data['frequency'] >= 3:  # Add to dictionary after 3 occurrences
                original = key.split(':', 1)[1]
                if original not in dictionary:
                    dictionary[original] = data['corrected']
                    updates_made += 1
        
        if updates_made > 0:
            save_custom_dictionary(dictionary, dictionary_file)
        
        return jsonify({
            'learned_corrections': learned_count,
            'dictionary_updates': updates_made,
            'total_learning_entries': len(learning_data),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error learning from corrections: {e}")
        return jsonify({'error': 'Learning failed', 'details': str(e)}), 500

# Additional helper functions
def load_learning_data(file_path: str) -> Dict[str, Any]:
    """Load learning data from file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_learning_data(data: Dict[str, Any], file_path: str):
    """Save learning data to file."""
    import os
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
```

**Acceptance Criteria**:
- ✅ Batch processing for multiple sessions
- ✅ Parallel processing for improved performance
- ✅ Learning system that improves over time
- ✅ Automatic dictionary updates from user corrections
- ✅ Aggregate metrics and reporting
- ✅ Performance optimization for large datasets

## 📋 Complete Task Breakdown

### Week 1-2: Core Foundation
- [ ] Task 1.1: Grammar & Spelling Correction Service
- [ ] Task 1.2: Correction API Endpoints  
- [ ] Task 1.3: Integration with existing transcription pipeline
- [ ] Task 1.4: Basic unit tests

### Week 3-4: Quality Assessment UI
- [ ] Task 2.1: Quality Dashboard Component
- [ ] Task 2.2: Correction Suggestions Interface
- [ ] Task 2.3: Custom Dictionary Management UI
- [ ] Task 2.4: Integration testing

### Week 5-6: Advanced Features
- [ ] Task 3.1: Batch Operations & Learning System
- [ ] Task 3.2: Advanced correction algorithms
- [ ] Task 3.3: Performance optimization
- [ ] Task 3.4: Comprehensive testing

### Week 7-8: Polish & Documentation
- [ ] Task 4.1: User experience refinements
- [ ] Task 4.2: Documentation and help system
- [ ] Task 4.3: Performance testing and optimization
- [ ] Task 4.4: Deployment and monitoring

## ✅ Acceptance Criteria

### Functional Requirements
- [ ] ✅ **Grammar Correction**: Automatically detect and fix grammar errors with 90%+ accuracy
- [ ] ✅ **Spelling Correction**: Identify and correct spelling mistakes with custom dictionary support
- [ ] ✅ **Quality Scoring**: Provide quantitative quality assessment (0-100 scale) with breakdown
- [ ] ✅ **Confidence Indicators**: Visual highlighting of low-confidence transcript segments
- [ ] ✅ **Custom Dictionary**: User-managed terminology database with CRUD operations
- [ ] ✅ **Batch Processing**: Handle multiple sessions simultaneously with progress tracking
- [ ] ✅ **Learning System**: Improve suggestions based on user corrections over time
- [ ] ✅ **Auto-Correction**: Intelligent auto-application of high-confidence corrections

### Performance Requirements
- [ ] ✅ **Response Time**: Quality analysis completed within 10 seconds for 1-hour transcript
- [ ] ✅ **Throughput**: Handle 10+ concurrent quality analyses
- [ ] ✅ **Memory Usage**: Efficient processing without memory leaks
- [ ] ✅ **Graceful Degradation**: Function with optional NLP libraries unavailable

### User Experience Requirements
- [ ] ✅ **Intuitive Interface**: Clear quality metrics with visual indicators
- [ ] ✅ **Interactive Corrections**: One-click application with preview capabilities
- [ ] ✅ **Progress Feedback**: Real-time progress indicators during analysis
- [ ] ✅ **Keyboard Shortcuts**: Power user shortcuts for common actions
- [ ] ✅ **Mobile Compatibility**: Responsive design for mobile devices

### Security & Reliability
- [ ] ✅ **Data Validation**: Comprehensive input validation and sanitization
- [ ] ✅ **Error Handling**: Graceful error handling with user-friendly messages
- [ ] ✅ **Audit Trail**: Track correction history for transparency
- [ ] ✅ **Data Backup**: Preserve original transcripts before corrections

## 🎯 Success Metrics

- **User Satisfaction**: 90%+ of users report improved transcript quality
- **Time Savings**: 50%+ reduction in manual editing time
- **Accuracy Improvement**: 25%+ improvement in transcript accuracy scores
- **Adoption Rate**: 80%+ of sessions use quality analysis features
- **Error Reduction**: 70%+ reduction in grammar and spelling errors

## 📚 Documentation Requirements

- [ ] API documentation with interactive examples
- [ ] User guide with screenshots and workflows
- [ ] Administrator guide for dictionary management
- [ ] Performance tuning guidelines
- [ ] Troubleshooting documentation

This comprehensive feature addresses one of the most significant user pain points - the time-consuming nature of manual transcript correction - while providing intelligent automation and continuous improvement through machine learning.
