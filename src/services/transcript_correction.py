"""
Automated transcript correction service using NLP and machine learning.
Provides intelligent correction suggestions and quality assessment.
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import language_tool_python
    import spacy
    from textblob import TextBlob

    CORRECTION_AVAILABLE = True
except ImportError:
    spacy = None
    TextBlob = None
    language_tool_python = None
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


@dataclass
class CorrectionSession:
    """Represents a correction session for a transcript."""

    session_id: str
    original_transcript: str
    corrected_transcript: str
    corrections_applied: List[CorrectionSuggestion]
    quality_before: QualityMetrics
    quality_after: QualityMetrics
    user_feedback: Dict[str, Any]
    created_at: str
    completed_at: Optional[str] = None


class TranscriptCorrectionEngine:
    """Main engine for automated transcript correction and quality assessment."""

    def __init__(self, custom_dictionary: Optional[Dict[str, str]] = None):
        """Initialize the correction engine with optional custom dictionary."""
        self.custom_dictionary = custom_dictionary or {}
        self.user_corrections = {}  # Learn from user corrections
        self.grammar_tool = None
        self.nlp_model = None
        self.correction_sessions = {}  # Track correction sessions

        if CORRECTION_AVAILABLE:
            try:
                self.grammar_tool = language_tool_python.LanguageTool("en-US")
                self.nlp_model = spacy.load("en_core_web_sm")
                logger.info("Correction engine initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize correction tools: {e}")
                self.correction_available = False
        else:
            logger.warning(
                "Correction libraries not available. Install with: pip install spacy textblob language_tool_python"
            )

        # Set instance variable for availability
        self.correction_available = CORRECTION_AVAILABLE and (
            self.grammar_tool is not None
        )

    def analyze_transcript_quality(
        self, transcript_text: str, segments: List[Dict] = None
    ) -> QualityMetrics:
        """
        Analyze overall transcript quality and return metrics.

        Args:
            transcript_text: Full transcript text
            segments: Optional list of transcript segments with timing

        Returns:
            QualityMetrics object with quality assessment
        """
        if not self.correction_available or not transcript_text.strip():
            return QualityMetrics(
                overall_score=75.0,  # Default score
                confidence_score=80.0,
                grammar_score=70.0,
                spelling_score=80.0,
                readability_score=75.0,
                issues_count=0,
                suggestions_count=0,
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
            overall_score = (
                grammar_score * 0.3
                + spelling_score * 0.25
                + readability_score * 0.25
                + confidence_score * 0.2
            )

            return QualityMetrics(
                overall_score=round(overall_score, 1),
                confidence_score=round(confidence_score, 1),
                grammar_score=round(grammar_score, 1),
                spelling_score=round(spelling_score, 1),
                readability_score=round(readability_score, 1),
                issues_count=len(grammar_issues),
                suggestions_count=len(grammar_issues)
                + (0 if corrected_text == transcript_text else 1),
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
                suggestions_count=0,
            )

    def generate_corrections(
        self, text: str, segment_confidence: float = 1.0
    ) -> List[CorrectionSuggestion]:
        """
        Generate correction suggestions for a text segment.

        Args:
            text: Text to analyze and correct
            segment_confidence: Confidence score from transcription (0-1)

        Returns:
            List of CorrectionSuggestion objects
        """
        suggestions = []

        if not self.correction_available or not text.strip():
            return suggestions

        try:
            # Grammar corrections
            grammar_issues = self.grammar_tool.check(text)
            for issue in grammar_issues:
                if issue.replacements:
                    suggestions.append(
                        CorrectionSuggestion(
                            original_text=text[
                                issue.offset : issue.offset + issue.errorLength
                            ],
                            suggested_text=issue.replacements[0],
                            confidence=0.9 if segment_confidence > 0.8 else 0.7,
                            correction_type="grammar",
                            start_position=issue.offset,
                            end_position=issue.offset + issue.errorLength,
                            explanation=issue.message,
                            auto_apply=segment_confidence
                            < 0.6,  # Auto-apply for low confidence
                        )
                    )

            # Spelling corrections
            blob = TextBlob(text)
            corrected_text = str(blob.correct())
            if corrected_text != text:
                suggestions.append(
                    CorrectionSuggestion(
                        original_text=text,
                        suggested_text=corrected_text,
                        confidence=0.8,
                        correction_type="spelling",
                        start_position=0,
                        end_position=len(text),
                        explanation="Spelling corrections applied",
                        auto_apply=False,
                    )
                )

            # Custom dictionary corrections
            for term, replacement in self.custom_dictionary.items():
                if term.lower() in text.lower():
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    if pattern.search(text):
                        suggestions.append(
                            CorrectionSuggestion(
                                original_text=term,
                                suggested_text=replacement,
                                confidence=0.95,
                                correction_type="terminology",
                                start_position=text.lower().find(term.lower()),
                                end_position=text.lower().find(term.lower())
                                + len(term),
                                explanation=f"Custom dictionary term: {term} → {replacement}",
                                auto_apply=True,
                            )
                        )

            # Learn from user corrections
            suggestions.extend(self._apply_learned_corrections(text))

            return suggestions

        except Exception as e:
            logger.error(f"Error generating corrections: {e}")
            return []

    def apply_corrections(
        self, text: str, corrections: List[CorrectionSuggestion]
    ) -> str:
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
            if correction.auto_apply or correction.confidence >= 0.9:
                corrected_text = (
                    corrected_text[: correction.start_position]
                    + correction.suggested_text
                    + corrected_text[correction.end_position :]
                )

        return corrected_text

    def start_correction_session(
        self, session_id: str, transcript_text: str, segments: List[Dict] = None
    ) -> CorrectionSession:
        """
        Start a new correction session for a transcript.

        Args:
            session_id: Unique session identifier
            transcript_text: Original transcript text
            segments: Optional transcript segments

        Returns:
            CorrectionSession object
        """
        quality_before = self.analyze_transcript_quality(transcript_text, segments)

        correction_session = CorrectionSession(
            session_id=session_id,
            original_transcript=transcript_text,
            corrected_transcript=transcript_text,
            corrections_applied=[],
            quality_before=quality_before,
            quality_after=quality_before,
            user_feedback={},
            created_at=datetime.now().isoformat(),
        )

        self.correction_sessions[session_id] = correction_session
        return correction_session

    def apply_correction_to_session(
        self,
        session_id: str,
        correction: CorrectionSuggestion,
        user_approved: bool = True,
    ) -> bool:
        """
        Apply a correction to an active session.

        Args:
            session_id: Session identifier
            correction: Correction to apply
            user_approved: Whether user approved the correction

        Returns:
            Success boolean
        """
        if session_id not in self.correction_sessions:
            return False

        session = self.correction_sessions[session_id]

        try:
            # Apply correction
            corrected_text = self.apply_corrections(
                session.corrected_transcript, [correction]
            )

            session.corrected_transcript = corrected_text
            session.corrections_applied.append(correction)

            # Learn from user approval/rejection
            if user_approved:
                self._learn_from_correction(correction)

            # Update quality metrics
            session.quality_after = self.analyze_transcript_quality(corrected_text)

            return True

        except Exception as e:
            logger.error(f"Error applying correction to session {session_id}: {e}")
            return False

    def complete_correction_session(
        self, session_id: str, user_feedback: Dict[str, Any] = None
    ) -> Optional[CorrectionSession]:
        """
        Complete a correction session and return final results.

        Args:
            session_id: Session identifier
            user_feedback: Optional user feedback

        Returns:
            Completed CorrectionSession or None if not found
        """
        if session_id not in self.correction_sessions:
            return None

        session = self.correction_sessions[session_id]
        session.completed_at = datetime.now().isoformat()
        session.user_feedback = user_feedback or {}

        return session

    def get_correction_statistics(self) -> Dict[str, Any]:
        """Get statistics about correction performance."""
        completed_sessions = [
            s for s in self.correction_sessions.values() if s.completed_at
        ]

        if not completed_sessions:
            return {
                "total_sessions": 0,
                "average_quality_improvement": 0,
                "most_common_corrections": [],
                "user_satisfaction": 0,
            }

        # Calculate average quality improvement
        quality_improvements = [
            s.quality_after.overall_score - s.quality_before.overall_score
            for s in completed_sessions
        ]
        avg_improvement = sum(quality_improvements) / len(quality_improvements)

        # Count correction types
        correction_types = {}
        for session in completed_sessions:
            for correction in session.corrections_applied:
                correction_types[correction.correction_type] = (
                    correction_types.get(correction.correction_type, 0) + 1
                )

        # Calculate user satisfaction from feedback
        satisfaction_scores = []
        for session in completed_sessions:
            if "satisfaction" in session.user_feedback:
                satisfaction_scores.append(session.user_feedback["satisfaction"])

        avg_satisfaction = (
            sum(satisfaction_scores) / len(satisfaction_scores)
            if satisfaction_scores
            else 0
        )

        return {
            "total_sessions": len(completed_sessions),
            "average_quality_improvement": round(avg_improvement, 2),
            "most_common_corrections": sorted(
                correction_types.items(), key=lambda x: x[1], reverse=True
            )[:5],
            "user_satisfaction": round(avg_satisfaction, 2),
            "total_corrections_applied": sum(
                len(s.corrections_applied) for s in completed_sessions
            ),
        }

    def update_custom_dictionary(self, new_terms: Dict[str, str]):
        """Update the custom dictionary with new terms."""
        self.custom_dictionary.update(new_terms)
        logger.info(f"Updated custom dictionary with {len(new_terms)} new terms")

    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score for text."""
        try:
            # Simple readability calculation based on sentence and word length
            sentences = re.split(r"[.!?]+", text)
            words = text.split()

            if not sentences or not words:
                return 75.0

            avg_words_per_sentence = len(words) / len(sentences)
            avg_chars_per_word = sum(len(word) for word in words) / len(words)

            # Simple readability score (higher is better)
            # Optimal: 15-20 words per sentence, 4-6 chars per word
            sentence_score = max(0, 100 - abs(avg_words_per_sentence - 17.5) * 2)
            word_score = max(0, 100 - abs(avg_chars_per_word - 5) * 10)

            return (sentence_score + word_score) / 2

        except Exception:
            return 75.0

    def _analyze_segment_confidence(self, segments: List[Dict]) -> float:
        """Analyze confidence scores from transcript segments."""
        if not segments:
            return 80.0

        try:
            confidences = []
            for segment in segments:
                if "confidence" in segment:
                    confidences.append(segment["confidence"])
                elif "words" in segment:
                    # Extract word-level confidences
                    word_confidences = [
                        word.get("confidence", 0.8)
                        for word in segment["words"]
                        if isinstance(word, dict)
                    ]
                    if word_confidences:
                        confidences.append(
                            sum(word_confidences) / len(word_confidences)
                        )

            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                # Ensure confidence is in 0-1 range, convert to percentage
                if avg_confidence > 1.0:
                    return min(avg_confidence, 100.0)  # Already a percentage
                else:
                    return avg_confidence * 100  # Convert to percentage
            else:
                return 80.0

        except Exception:
            return 80.0

    def _apply_learned_corrections(self, text: str) -> List[CorrectionSuggestion]:
        """Apply corrections learned from user behavior."""
        suggestions = []

        for original, replacement in self.user_corrections.items():
            if original.lower() in text.lower():
                start_pos = text.lower().find(original.lower())
                suggestions.append(
                    CorrectionSuggestion(
                        original_text=original,
                        suggested_text=replacement,
                        confidence=0.85,
                        correction_type="learned",
                        start_position=start_pos,
                        end_position=start_pos + len(original),
                        explanation=f"Learned correction: {original} → {replacement}",
                        auto_apply=False,
                    )
                )

        return suggestions

    def _learn_from_correction(self, correction: CorrectionSuggestion):
        """Learn from user-approved corrections."""
        if correction.confidence > 0.8:
            self.user_corrections[correction.original_text] = correction.suggested_text
            logger.debug(
                f"Learned correction: {correction.original_text} → {correction.suggested_text}"
            )

    def create_session(self, transcript: str, user_id: str = None) -> str:
        """Create a new correction session."""
        import uuid

        session_id = str(uuid.uuid4())

        self.correction_sessions[session_id] = {
            "session_id": session_id,
            "original_transcript": transcript,
            "corrected_transcript": transcript,
            "corrections_applied": [],
            "suggestions": [],
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by ID."""
        return self.correction_sessions.get(session_id)

    def update_session(self, session_id: str, **updates) -> bool:
        """Update session data."""
        if session_id in self.correction_sessions:
            self.correction_sessions[session_id].update(updates)
            self.correction_sessions[session_id][
                "updated_at"
            ] = datetime.now().isoformat()
            return True
        return False


# Factory function
def create_transcript_correction_engine(
    custom_dictionary: Dict[str, str] = None
) -> TranscriptCorrectionEngine:
    """Create a transcript correction engine instance."""
    return TranscriptCorrectionEngine(custom_dictionary)


# Default industry dictionaries
INDUSTRY_DICTIONARIES = {
    "medical": {
        "echocardiogram": "echocardiogram",
        "myocardial infarction": "myocardial infarction",
        "hypertension": "hypertension",
        "diabetes mellitus": "diabetes mellitus",
        "stethoscope": "stethoscope",
        "cardiovascular": "cardiovascular",
        "pharmaceutical": "pharmaceutical",
        "anesthesia": "anesthesia",
        "diagnosis": "diagnosis",
        "prognosis": "prognosis",
    },
    "legal": {
        "plaintiff": "plaintiff",
        "defendant": "defendant",
        "subpoena": "subpoena",
        "deposition": "deposition",
        "litigation": "litigation",
        "jurisdiction": "jurisdiction",
        "precedent": "precedent",
        "affidavit": "affidavit",
        "testimony": "testimony",
        "appellate": "appellate",
    },
    "technical": {
        "API": "API",
        "database": "database",
        "authentication": "authentication",
        "deployment": "deployment",
        "algorithm": "algorithm",
        "infrastructure": "infrastructure",
        "cybersecurity": "cybersecurity",
        "blockchain": "blockchain",
        "machine learning": "machine learning",
        "artificial intelligence": "artificial intelligence",
    },
    "business": {
        "ROI": "ROI",
        "stakeholder": "stakeholder",
        "quarterly": "quarterly",
        "revenue": "revenue",
        "entrepreneurship": "entrepreneurship",
        "acquisition": "acquisition",
        "synergy": "synergy",
        "scalability": "scalability",
        "valuation": "valuation",
        "portfolio": "portfolio",
    },
    "education": {
        # Academic Levels & Degrees
        "undergraduate": "undergraduate",
        "graduate": "graduate",
        "postgraduate": "postgraduate",
        "doctorate": "doctorate",
        "PhD": "PhD",
        "Ph.D.": "Ph.D.",
        "Masters": "Masters",
        "Master's": "Master's",
        "Bachelors": "Bachelors",
        "Bachelor's": "Bachelor's",
        "Associate's": "Associate's",
        # Educational Roles
        "professor": "professor",
        "lecturer": "lecturer",
        "instructor": "instructor",
        "teaching assistant": "teaching assistant",
        "dean": "dean",
        "provost": "provost",
        "chancellor": "chancellor",
        "registrar": "registrar",
        "emeritus": "emeritus",
        # Academic Processes
        "dissertation": "dissertation",
        "thesis": "thesis",
        "curriculum": "curriculum",
        "syllabus": "syllabus",
        "pedagogy": "pedagogy",
        "assessment": "assessment",
        "evaluation": "evaluation",
        "accreditation": "accreditation",
        "matriculation": "matriculation",
        "graduation": "graduation",
        # Educational Institutions
        "university": "university",
        "college": "college",
        "academy": "academy",
        "institute": "institute",
        "seminary": "seminary",
        "campus": "campus",
        "dormitory": "dormitory",
        "library": "library",
        "laboratory": "laboratory",
        "auditorium": "auditorium",
        # Research Terms
        "methodology": "methodology",
        "hypothesis": "hypothesis",
        "literature review": "literature review",
        "peer review": "peer review",
        "empirical": "empirical",
        "qualitative": "qualitative",
        "quantitative": "quantitative",
        "ethnography": "ethnography",
        "longitudinal": "longitudinal",
        "cross-sectional": "cross-sectional",
        # Mathematics
        "algebra": "algebra",
        "calculus": "calculus",
        "geometry": "geometry",
        "trigonometry": "trigonometry",
        "statistics": "statistics",
        "probability": "probability",
        "theorem": "theorem",
        "equation": "equation",
        "polynomial": "polynomial",
        "derivative": "derivative",
        # Science
        "biology": "biology",
        "chemistry": "chemistry",
        "physics": "physics",
        "experiment": "experiment",
        "theory": "theory",
        "hypothesis": "hypothesis",
        "molecule": "molecule",
        "organism": "organism",
        "ecosystem": "ecosystem",
        "photosynthesis": "photosynthesis",
        # Liberal Arts
        "humanities": "humanities",
        "philosophy": "philosophy",
        "linguistics": "linguistics",
        "literature": "literature",
        "sociology": "sociology",
        "psychology": "psychology",
        "anthropology": "anthropology",
        "archaeology": "archaeology",
        "historiography": "historiography",
        "epistemology": "epistemology",
        # Academic Publications
        "journal": "journal",
        "publication": "publication",
        "citation": "citation",
        "bibliography": "bibliography",
        "reference": "reference",
        "abstract": "abstract",
        "manuscript": "manuscript",
        "monograph": "monograph",
        "anthology": "anthology",
        "periodical": "periodical",
        # Academic Events
        "symposium": "symposium",
        "conference": "conference",
        "seminar": "seminar",
        "workshop": "workshop",
        "colloquium": "colloquium",
        "lecture": "lecture",
        "presentation": "presentation",
        "keynote": "keynote",
        "panel": "panel",
        "webinar": "webinar",
        # Assessment & Evaluation
        "examination": "examination",
        "quiz": "quiz",
        "assignment": "assignment",
        "rubric": "rubric",
        "grading": "grading",
        "evaluation": "evaluation",
        "midterm": "midterm",
        "final": "final",
        "comprehensive": "comprehensive",
        "oral examination": "oral examination",
        # Educational Technology
        "e-learning": "e-learning",
        "online learning": "online learning",
        "distance education": "distance education",
        "blended learning": "blended learning",
        "MOOC": "MOOC",
        "learning management system": "learning management system",
        "LMS": "LMS",
        "educational technology": "educational technology",
        "virtual classroom": "virtual classroom",
        "digital literacy": "digital literacy",
        # Academic Administration
        "enrollment": "enrollment",
        "registration": "registration",
        "transcript": "transcript",
        "GPA": "GPA",
        "grade point average": "grade point average",
        "academic year": "academic year",
        "semester": "semester",
        "quarter": "quarter",
        "prerequisite": "prerequisite",
        "corequisite": "corequisite",
    },
}


def get_industry_dictionary(industry: str) -> Dict[str, str]:
    """Get predefined dictionary for specific industry."""
    return INDUSTRY_DICTIONARIES.get(industry, {})
