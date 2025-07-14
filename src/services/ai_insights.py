"""
Advanced AI-Powered Insights Service for Video Transcription Analysis.

This service provides comprehensive AI-driven analysis capabilities including:
- Sentiment analysis and emotional tone detection
- Topic modeling and automatic content summarization
- Speaker diarization and voice pattern analysis
- Content classification and domain detection
- Key insights extraction and action item identification
- Advanced analytics and visualization data generation
"""

import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

# Optional AI/ML dependencies with graceful fallbacks
try:
    from textblob import TextBlob

    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    TextBlob = None

try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import TfidfVectorizer

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    TfidfVectorizer = None
    KMeans = None
    LatentDirichletAllocation = None

try:
    import spacy

    # Try to load the English model
    try:
        _nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        SPACY_AVAILABLE = False
        _nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None
    _nlp = None

from src.config import AnalysisConfig

logger = logging.getLogger(__name__)
analysis_config = AnalysisConfig()


class AIInsightsEngine:
    """
    Advanced AI-powered insights engine for comprehensive content analysis.

    This engine provides sophisticated analysis capabilities that go beyond
    basic keyword matching to deliver meaningful insights about content,
    speakers, topics, sentiment, and actionable information.

    Features:
    - Multi-level sentiment analysis (document, segment, speaker)
    - Automatic topic modeling and theme extraction
    - Speaker diarization and voice pattern analysis
    - Content classification and domain detection
    - Key insights and action items extraction
    - Advanced statistical analysis and trends
    """

    def __init__(self):
        """Initialize the AI insights engine with available ML libraries."""
        self.sentiment_available = TEXTBLOB_AVAILABLE
        self.topic_modeling_available = SKLEARN_AVAILABLE
        self.nlp_available = SPACY_AVAILABLE

        # Log available capabilities
        capabilities = []
        if self.sentiment_available:
            capabilities.append("Sentiment Analysis")
        if self.topic_modeling_available:
            capabilities.append("Topic Modeling")
        if self.nlp_available:
            capabilities.append("Advanced NLP")

        if capabilities:
            logger.info(
                f"AI Insights Engine initialized with: {', '.join(capabilities)}"
            )
        else:
            logger.warning(
                "AI Insights Engine initialized with basic capabilities only. "
                "Install textblob, scikit-learn, and spacy for full functionality."
            )

    def analyze_comprehensive(
        self, text: str, segments: List[Dict[str, Any]], basic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive AI-powered analysis of transcribed content.

        Args:
            text: Full transcription text
            segments: List of timestamped segments
            basic_analysis: Basic analysis results from existing system

        Returns:
            Dictionary containing advanced AI insights
        """
        logger.info("Starting comprehensive AI insights analysis...")

        ai_insights = {
            "sentiment_analysis": {},
            "topic_modeling": {},
            "speaker_analysis": {},
            "content_classification": {},
            "key_insights": {},
            "advanced_analytics": {},
            "processing_info": {
                "timestamp": datetime.now().isoformat(),
                "capabilities_used": [],
                "total_segments": len(segments),
                "total_words": len(text.split()),
            },
        }

        # Sentiment Analysis
        if self.sentiment_available:
            ai_insights["sentiment_analysis"] = self._analyze_sentiment(text, segments)
            ai_insights["processing_info"]["capabilities_used"].append(
                "sentiment_analysis"
            )

        # Topic Modeling
        if self.topic_modeling_available and len(segments) > 5:
            ai_insights["topic_modeling"] = self._analyze_topics(text, segments)
            ai_insights["processing_info"]["capabilities_used"].append("topic_modeling")

        # Speaker Analysis (basic pattern recognition)
        ai_insights["speaker_analysis"] = self._analyze_speakers(segments)
        ai_insights["processing_info"]["capabilities_used"].append("speaker_analysis")

        # Content Classification
        ai_insights["content_classification"] = self._classify_content(
            text, basic_analysis
        )
        ai_insights["processing_info"]["capabilities_used"].append(
            "content_classification"
        )

        # Key Insights Extraction
        ai_insights["key_insights"] = self._extract_key_insights(
            text, segments, basic_analysis
        )
        ai_insights["processing_info"]["capabilities_used"].append("key_insights")

        # Advanced Analytics
        ai_insights["advanced_analytics"] = self._generate_advanced_analytics(
            text, segments, basic_analysis, ai_insights
        )
        ai_insights["processing_info"]["capabilities_used"].append("advanced_analytics")

        logger.info(
            f"AI insights analysis completed with {len(ai_insights['processing_info']['capabilities_used'])} modules"
        )
        return ai_insights

    def _analyze_sentiment(
        self, text: str, segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive sentiment analysis at multiple levels.

        Returns:
            Dictionary containing overall, segment-wise, and trend analysis
        """
        logger.info("Analyzing sentiment patterns...")

        sentiment_data = {
            "overall": {},
            "segments": [],
            "trends": {},
            "emotional_peaks": [],
        }

        try:
            # Overall document sentiment
            doc_blob = TextBlob(text)
            sentiment_data["overall"] = {
                "polarity": float(doc_blob.sentiment.polarity),  # -1 to 1
                "subjectivity": float(doc_blob.sentiment.subjectivity),  # 0 to 1
                "interpretation": self._interpret_sentiment(
                    doc_blob.sentiment.polarity, doc_blob.sentiment.subjectivity
                ),
            }

            # Segment-wise sentiment analysis
            segment_sentiments = []
            for i, segment in enumerate(segments):
                if (
                    len(segment["text"].strip()) > 10
                ):  # Only analyze substantial segments
                    seg_blob = TextBlob(segment["text"])
                    segment_sentiment = {
                        "timestamp": segment.get("timestamp_str", f"Segment {i}"),
                        "start": segment.get("start", 0),
                        "polarity": float(seg_blob.sentiment.polarity),
                        "subjectivity": float(seg_blob.sentiment.subjectivity),
                        "text_preview": (
                            segment["text"][:100] + "..."
                            if len(segment["text"]) > 100
                            else segment["text"]
                        ),
                    }
                    sentiment_data["segments"].append(segment_sentiment)
                    segment_sentiments.append(seg_blob.sentiment.polarity)

            # Sentiment trends analysis
            if segment_sentiments:
                sentiment_data["trends"] = {
                    "variance": (
                        float(np.var(segment_sentiments)) if segment_sentiments else 0.0
                    ),
                    "mean": (
                        float(np.mean(segment_sentiments))
                        if segment_sentiments
                        else 0.0
                    ),
                    "progression": self._analyze_sentiment_progression(
                        segment_sentiments
                    ),
                    "stability": (
                        "stable" if np.var(segment_sentiments) < 0.1 else "variable"
                    ),
                }

                # Identify emotional peaks (segments with extreme sentiment)
                if len(segment_sentiments) > 0:
                    threshold = np.std(segment_sentiments) * 1.5
                    mean_sentiment = np.mean(segment_sentiments)

                    for i, (sentiment, segment_data) in enumerate(
                        zip(segment_sentiments, sentiment_data["segments"])
                    ):
                        if abs(sentiment - mean_sentiment) > threshold:
                            peak_type = (
                                "positive" if sentiment > mean_sentiment else "negative"
                            )
                            sentiment_data["emotional_peaks"].append(
                                {
                                    "timestamp": segment_data["timestamp"],
                                    "start": segment_data["start"],
                                    "type": peak_type,
                                    "intensity": float(abs(sentiment - mean_sentiment)),
                                    "text_preview": segment_data["text_preview"],
                                }
                            )

        except Exception as e:
            logger.warning(f"Sentiment analysis error: {e}")
            sentiment_data["error"] = str(e)

        return sentiment_data

    def _analyze_topics(
        self,
        text: str,
        segments: List[Dict[str, Any]],  # pylint: disable=unused-argument
    ) -> Dict[str, Any]:
        """
        Perform topic modeling to identify main themes and subjects.

        Returns:
            Dictionary containing topic clusters and theme analysis
        """
        logger.info("Performing topic modeling analysis...")

        topic_data = {
            "main_topics": [],
            "topic_distribution": {},
            "segment_topics": [],
            "topic_transitions": [],
        }

        try:
            # Prepare text data - use segments for better granularity
            segment_texts = [
                seg["text"] for seg in segments if len(seg["text"].strip()) > 20
            ]

            if len(segment_texts) < 3:
                topic_data["error"] = "Insufficient text for topic modeling"
                return topic_data

            # TF-IDF Vectorization
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words="english",
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.8,
            )

            tfidf_matrix = vectorizer.fit_transform(segment_texts)
            feature_names = vectorizer.get_feature_names_out()

            # Determine optimal number of topics (between 2 and 8)
            n_topics = min(max(2, len(segment_texts) // 3), 8)

            # LDA Topic Modeling
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                random_state=42,
                max_iter=10,
                learning_method="batch",
            )

            lda_matrix = lda.fit_transform(tfidf_matrix)

            # Extract main topics
            for topic_idx, topic in enumerate(lda.components_):
                top_words_idx = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                topic_strength = float(np.mean(topic[top_words_idx]))

                topic_data["main_topics"].append(
                    {
                        "topic_id": topic_idx,
                        "keywords": top_words[:5],
                        "strength": topic_strength,
                        "description": self._generate_topic_description(top_words[:3]),
                    }
                )

            # Assign topics to segments
            for i, segment in enumerate(segments[: len(lda_matrix)]):
                dominant_topic = int(np.argmax(lda_matrix[i]))
                topic_confidence = float(np.max(lda_matrix[i]))

                topic_data["segment_topics"].append(
                    {
                        "timestamp": segment.get("timestamp_str", f"Segment {i}"),
                        "start": segment.get("start", 0),
                        "topic_id": dominant_topic,
                        "confidence": topic_confidence,
                        "text_preview": (
                            segment["text"][:80] + "..."
                            if len(segment["text"]) > 80
                            else segment["text"]
                        ),
                    }
                )

            # Topic distribution analysis
            topic_counts = Counter(
                [st["topic_id"] for st in topic_data["segment_topics"]]
            )
            total_segments = len(topic_data["segment_topics"])

            topic_data["topic_distribution"] = {
                f"topic_{topic_id}": {
                    "percentage": round((count / total_segments) * 100, 1),
                    "segment_count": count,
                    "description": next(
                        (
                            t["description"]
                            for t in topic_data["main_topics"]
                            if t["topic_id"] == topic_id
                        ),
                        f"Topic {topic_id}",
                    ),
                }
                for topic_id, count in topic_counts.items()
            }

            # Analyze topic transitions (how topics change over time)
            if len(topic_data["segment_topics"]) > 1:
                transitions = []
                for i in range(1, len(topic_data["segment_topics"])):
                    prev_topic = topic_data["segment_topics"][i - 1]["topic_id"]
                    curr_topic = topic_data["segment_topics"][i]["topic_id"]
                    if prev_topic != curr_topic:
                        transitions.append(
                            {
                                "from_topic": prev_topic,
                                "to_topic": curr_topic,
                                "timestamp": topic_data["segment_topics"][i][
                                    "timestamp"
                                ],
                                "start": topic_data["segment_topics"][i]["start"],
                            }
                        )

                topic_data["topic_transitions"] = transitions

        except Exception as e:
            logger.warning(f"Topic modeling error: {e}")
            topic_data["error"] = str(e)

        return topic_data

    def _analyze_speakers(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze speaker patterns and characteristics (basic heuristic approach).

        Note: This is a simplified approach. True speaker diarization would
        require audio analysis with specialized libraries like pyannote.audio
        """
        logger.info("Analyzing speaker patterns...")

        speaker_data = {
            "estimated_speakers": 1,
            "speaking_patterns": {},
            "dialogue_detection": {},
            "speaker_characteristics": [],
        }

        try:
            # Detect potential dialogue patterns
            dialogue_indicators = [
                r"\b(he said|she said|they said|I said)\b",
                r"\b(asked|replied|answered|responded)\b",
                r"\b(according to|as mentioned by)\b",
                r'"[^"]*"',  # Quoted speech
                r"'[^']*'",  # Single quoted speech
            ]

            dialogue_segments = []
            for segment in segments:
                text = segment["text"]
                dialogue_score = 0

                for pattern in dialogue_indicators:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    dialogue_score += len(matches)

                if dialogue_score > 0:
                    dialogue_segments.append(
                        {
                            "timestamp": segment.get("timestamp_str", "Unknown"),
                            "start": segment.get("start", 0),
                            "dialogue_score": dialogue_score,
                            "text_preview": (
                                text[:100] + "..." if len(text) > 100 else text
                            ),
                        }
                    )

            speaker_data["dialogue_detection"] = {
                "total_segments": len(segments),
                "dialogue_segments": len(dialogue_segments),
                "dialogue_percentage": (
                    round((len(dialogue_segments) / len(segments)) * 100, 1)
                    if segments
                    else 0
                ),
                "segments": dialogue_segments[:10],  # Limit to first 10 for display
            }

            # Estimate speaker count based on dialogue patterns
            if (
                len(dialogue_segments) > len(segments) * 0.3
            ):  # 30% dialogue suggests multiple speakers
                speaker_data["estimated_speakers"] = 2
            elif len(dialogue_segments) > len(segments) * 0.5:  # 50% suggests even more
                speaker_data["estimated_speakers"] = 3

            # Analyze speaking patterns (pace, complexity)
            if segments:
                segment_lengths = [len(seg["text"].split()) for seg in segments]
                segment_durations = []

                for segment in segments:
                    if "start" in segment and "end" in segment:
                        duration = segment["end"] - segment["start"]
                        segment_durations.append(duration)

                speaker_data["speaking_patterns"] = {
                    "average_words_per_segment": (
                        round(np.mean(segment_lengths), 1) if segment_lengths else 0
                    ),
                    "words_variance": (
                        round(np.var(segment_lengths), 1) if segment_lengths else 0
                    ),
                    "speech_consistency": (
                        "consistent" if np.var(segment_lengths) < 50 else "variable"
                    ),
                }

                if segment_durations:
                    words_per_minute = [
                        (length / (duration / 60))
                        for length, duration in zip(segment_lengths, segment_durations)
                        if duration > 0
                    ]
                    if words_per_minute:
                        speaker_data["speaking_patterns"]["estimated_wpm"] = round(
                            np.mean(words_per_minute), 1
                        )
                        speaker_data["speaking_patterns"]["pace"] = (
                            self._categorize_speaking_pace(np.mean(words_per_minute))
                        )

        except Exception as e:
            logger.warning(f"Speaker analysis error: {e}")
            speaker_data["error"] = str(e)

        return speaker_data

    def _classify_content(
        self, text: str, basic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classify content type and domain using heuristic analysis.
        """
        logger.info("Classifying content type and domain...")

        classification = {
            "primary_domain": "general",
            "content_type": "unknown",
            "confidence_scores": {},
            "domain_indicators": {},
            "characteristics": {},
        }

        try:
            # Domain classification based on keywords and patterns
            domain_keywords = {
                "education": [
                    "student",
                    "learn",
                    "teach",
                    "course",
                    "lesson",
                    "assignment",
                    "homework",
                    "exam",
                    "grade",
                    "university",
                    "school",
                ],
                "business": [
                    "meeting",
                    "project",
                    "deadline",
                    "budget",
                    "revenue",
                    "client",
                    "customer",
                    "sales",
                    "marketing",
                    "strategy",
                ],
                "technical": [
                    "code",
                    "software",
                    "development",
                    "bug",
                    "feature",
                    "deployment",
                    "testing",
                    "database",
                    "API",
                    "framework",
                ],
                "healthcare": [
                    "patient",
                    "doctor",
                    "treatment",
                    "diagnosis",
                    "medical",
                    "health",
                    "symptoms",
                    "medication",
                    "therapy",
                    "clinic",
                ],
                "interview": [
                    "experience",
                    "background",
                    "position",
                    "role",
                    "company",
                    "skills",
                    "qualifications",
                    "previous",
                    "why did you",
                ],
                "presentation": [
                    "slide",
                    "chart",
                    "graph",
                    "data",
                    "analysis",
                    "conclusion",
                    "recommendation",
                    "overview",
                    "summary",
                ],
            }

            # Count domain indicators
            text_lower = text.lower()
            domain_scores = {}

            for domain, keywords in domain_keywords.items():
                score = sum(text_lower.count(keyword) for keyword in keywords)
                domain_scores[domain] = score

                # Track which specific indicators were found
                found_indicators = [kw for kw in keywords if kw in text_lower]
                if found_indicators:
                    classification["domain_indicators"][domain] = found_indicators[
                        :5
                    ]  # Limit for display

            # Determine primary domain
            if domain_scores:
                primary_domain = max(domain_scores, key=domain_scores.get)
                max_score = domain_scores[primary_domain]

                if max_score > 0:
                    classification["primary_domain"] = primary_domain
                    total_indicators = sum(domain_scores.values())
                    classification["confidence_scores"] = {
                        domain: (
                            round((score / total_indicators) * 100, 1)
                            if total_indicators > 0
                            else 0
                        )
                        for domain, score in domain_scores.items()
                    }

            # Content type classification
            content_patterns = {
                "lecture": [
                    r"\btoday we.+discuss\b",
                    r"\bin this (lesson|class|lecture)\b",
                    r"\blet.s (start|begin)\b",
                ],
                "meeting": [
                    r"\b(agenda|minutes|action items)\b",
                    r"\bmeeting\b",
                    r"\bnext steps\b",
                ],
                "interview": [
                    r"\btell me about\b",
                    r"\bcan you describe\b",
                    r"\bwhat is your experience\b",
                ],
                "presentation": [
                    r"\bas you can see\b",
                    r"\bin this slide\b",
                    r"\bmove on to\b",
                    r"\bin conclusion\b",
                ],
                "conversation": [
                    r"\bI think\b",
                    r"\bwhat do you think\b",
                    r"\bby the way\b",
                ],
                "tutorial": [
                    r"\bstep by step\b",
                    r"\bfirst.+then\b",
                    r"\blet.s (create|build|make)\b",
                ],
            }

            content_scores = {}
            for content_type, patterns in content_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, text, re.IGNORECASE))
                    score += matches
                content_scores[content_type] = score

            if content_scores and max(content_scores.values()) > 0:
                classification["content_type"] = max(
                    content_scores, key=content_scores.get
                )

            # Content characteristics analysis
            total_words = len(text.split())
            question_count = len(basic_analysis.get("questions", []))

            classification["characteristics"] = {
                "formality_level": self._assess_formality(text),
                "interactivity": (
                    "high" if question_count > total_words * 0.01 else "low"
                ),  # 1% questions = high interactivity
                "complexity": self._assess_complexity(text),
                "structure": self._assess_structure(text),
            }

        except Exception as e:
            logger.warning(f"Content classification error: {e}")
            classification["error"] = str(e)

        return classification

    def _extract_key_insights(
        self,
        text: str,
        segments: List[Dict[str, Any]],
        basic_analysis: Dict[str, Any],  # pylint: disable=unused-argument
    ) -> Dict[str, Any]:
        """
        Extract key insights and actionable items from the content.
        """
        logger.info("Extracting key insights and actionable items...")

        insights = {
            "action_items": [],
            "key_takeaways": [],
            "important_mentions": [],
            "decision_points": [],
            "follow_ups": [],
        }

        try:
            # Action item patterns
            action_patterns = [
                r"\b(need to|should|must|have to|will)\s+([^.!?]+)",
                r"\b(action item|todo|task):\s*([^.!?]+)",
                r"\b(remember to|don.t forget to)\s+([^.!?]+)",
                r"\b(next step|follow up)\s*:?\s*([^.!?]+)",
            ]

            for segment in segments:
                text_segment = segment["text"]
                for pattern in action_patterns:
                    matches = re.finditer(pattern, text_segment, re.IGNORECASE)
                    for match in matches:
                        action_text = (
                            match.group(2)
                            if len(match.groups()) > 1
                            else match.group(1)
                        )
                        insights["action_items"].append(
                            {
                                "timestamp": segment.get("timestamp_str", "Unknown"),
                                "start": segment.get("start", 0),
                                "action": action_text.strip(),
                                "context": (
                                    text_segment[:100] + "..."
                                    if len(text_segment) > 100
                                    else text_segment
                                ),
                            }
                        )

            # Decision point patterns
            decision_patterns = [
                r"\b(decided|decision|choose|chose|select)\s+([^.!?]+)",
                r"\b(we (will|should|need to) decide)\s+([^.!?]+)",
                r"\b(final decision|conclusion)\s*:?\s*([^.!?]+)",
            ]

            for segment in segments:
                text_segment = segment["text"]
                for pattern in decision_patterns:
                    matches = re.finditer(pattern, text_segment, re.IGNORECASE)
                    for match in matches:
                        decision_text = (
                            match.group(2)
                            if len(match.groups()) > 1
                            else match.group(1)
                        )
                        insights["decision_points"].append(
                            {
                                "timestamp": segment.get("timestamp_str", "Unknown"),
                                "start": segment.get("start", 0),
                                "decision": decision_text.strip(),
                                "context": text_segment,
                            }
                        )

            # Extract key takeaways based on emphasis patterns and keyword frequency
            emphasis_cues = basic_analysis.get("emphasis_cues", [])
            keyword_matches = basic_analysis.get("keyword_matches", [])

            # Combine emphasis cues as takeaways
            for cue in emphasis_cues[:5]:  # Limit to top 5
                insights["key_takeaways"].append(
                    {
                        "timestamp": cue.get("timestamp", "Unknown"),
                        "start": cue.get("start", 0),
                        "takeaway": cue.get("text", "").strip(),
                        "type": "emphasis",
                    }
                )

            # Add high-frequency keywords as important mentions
            for keyword_match in keyword_matches[:10]:  # Top 10 keywords
                if (
                    keyword_match.get("count", 0) > 2
                ):  # Only if mentioned multiple times
                    insights["important_mentions"].append(
                        {
                            "term": keyword_match.get("keyword", ""),
                            "frequency": keyword_match.get("count", 0),
                            "contexts": keyword_match.get("matches", [])[
                                :3
                            ],  # First 3 contexts
                        }
                    )

            # Extract follow-up items
            followup_patterns = [
                r"\b(follow up|check back|revisit|review)\s+([^.!?]+)",
                r"\b(will get back|will update|will check)\s+([^.!?]+)",
                r"\b(pending|waiting for|need to hear back)\s+([^.!?]+)",
            ]

            for segment in segments:
                text_segment = segment["text"]
                for pattern in followup_patterns:
                    matches = re.finditer(pattern, text_segment, re.IGNORECASE)
                    for match in matches:
                        followup_text = (
                            match.group(2)
                            if len(match.groups()) > 1
                            else match.group(1)
                        )
                        insights["follow_ups"].append(
                            {
                                "timestamp": segment.get("timestamp_str", "Unknown"),
                                "start": segment.get("start", 0),
                                "item": followup_text.strip(),
                                "context": (
                                    text_segment[:100] + "..."
                                    if len(text_segment) > 100
                                    else text_segment
                                ),
                            }
                        )

            # Limit results for performance and display
            for key, value in insights.items():
                if isinstance(value, list):
                    insights[key] = value[:10]  # Limit to 10 items per category

        except Exception as e:
            logger.warning(f"Key insights extraction error: {e}")
            insights["error"] = str(e)

        return insights

    def _generate_advanced_analytics(
        self,
        text: str,
        segments: List[Dict[str, Any]],
        basic_analysis: Dict[str, Any],
        ai_insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate advanced analytics and visualization data.
        """
        logger.info("Generating advanced analytics...")

        analytics = {
            "content_metrics": {},
            "engagement_indicators": {},
            "complexity_analysis": {},
            "temporal_patterns": {},
            "summary_statistics": {},
        }

        try:
            # Content metrics
            words = text.split()
            sentences = re.split(r"[.!?]+", text)

            analytics["content_metrics"] = {
                "total_words": len(words),
                "unique_words": len(
                    set(word.lower() for word in words if word.isalpha())
                ),
                "vocabulary_richness": (
                    round(len(set(words)) / len(words) * 100, 2) if words else 0
                ),
                "average_sentence_length": (
                    round(len(words) / len([s for s in sentences if s.strip()]), 1)
                    if sentences
                    else 0
                ),
                "reading_level": self._estimate_reading_level(text),
                "word_frequency_distribution": dict(Counter(words).most_common(10)),
            }

            # Engagement indicators
            questions = basic_analysis.get("questions", [])
            emphasis_cues = basic_analysis.get("emphasis_cues", [])

            analytics["engagement_indicators"] = {
                "question_density": (
                    round(len(questions) / len(segments) * 100, 2) if segments else 0
                ),
                "emphasis_density": (
                    round(len(emphasis_cues) / len(segments) * 100, 2)
                    if segments
                    else 0
                ),
                "interactivity_score": self._calculate_interactivity_score(
                    questions, emphasis_cues, segments
                ),
                "engagement_level": self._categorize_engagement_level(
                    questions, emphasis_cues, segments
                ),
            }

            # Complexity analysis
            analytics["complexity_analysis"] = {
                "lexical_diversity": self._calculate_lexical_diversity(words),
                "syntactic_complexity": self._estimate_syntactic_complexity(text),
                "concept_density": self._estimate_concept_density(text, basic_analysis),
                "overall_complexity": "low",  # Will be calculated based on above metrics
            }

            # Set overall complexity based on metrics
            complexity_score = (
                analytics["complexity_analysis"]["lexical_diversity"] * 0.4
                + analytics["complexity_analysis"]["syntactic_complexity"] * 0.3
                + analytics["complexity_analysis"]["concept_density"] * 0.3
            )

            if complexity_score > 0.7:
                analytics["complexity_analysis"]["overall_complexity"] = "high"
            elif complexity_score > 0.4:
                analytics["complexity_analysis"]["overall_complexity"] = "medium"
            else:
                analytics["complexity_analysis"]["overall_complexity"] = "low"

            # Temporal patterns (if timing data is available)
            if segments and any("start" in seg for seg in segments):
                analytics["temporal_patterns"] = self._analyze_temporal_patterns(
                    segments
                )

            # Summary statistics
            analytics["summary_statistics"] = {
                "processing_timestamp": datetime.now().isoformat(),
                "total_segments_analyzed": len(segments),
                "ai_modules_used": len(
                    ai_insights.get("processing_info", {}).get("capabilities_used", [])
                ),
                "analysis_completeness": self._calculate_analysis_completeness(
                    ai_insights
                ),
                "content_highlights": {
                    "most_frequent_keyword": self._get_top_keyword(basic_analysis),
                    "peak_sentiment_moment": self._get_peak_sentiment(ai_insights),
                    "primary_topic": self._get_primary_topic(ai_insights),
                    "key_insight_count": len(
                        ai_insights.get("key_insights", {}).get("action_items", [])
                    ),
                },
            }

        except Exception as e:
            logger.warning(f"Advanced analytics generation error: {e}")
            analytics["error"] = str(e)

        return analytics

    # Helper methods for analysis

    def _interpret_sentiment(self, polarity: float, subjectivity: float) -> str:
        """Interpret sentiment polarity and subjectivity scores."""
        if polarity > 0.1:
            emotion = "positive"
        elif polarity < -0.1:
            emotion = "negative"
        else:
            emotion = "neutral"

        if subjectivity > 0.6:
            objectivity = "subjective"
        elif subjectivity < 0.3:
            objectivity = "objective"
        else:
            objectivity = "balanced"

        return f"{emotion} and {objectivity}"

    def _analyze_sentiment_progression(self, sentiments: List[float]) -> str:
        """Analyze how sentiment changes over time."""
        if len(sentiments) < 3:
            return "insufficient_data"

        start_avg = np.mean(sentiments[: len(sentiments) // 3])
        end_avg = np.mean(sentiments[-len(sentiments) // 3 :])

        difference = end_avg - start_avg

        if difference > 0.2:
            return "improving"
        elif difference < -0.2:
            return "declining"
        else:
            return "stable"

    def _generate_topic_description(self, top_words: List[str]) -> str:
        """Generate a human-readable description for a topic."""
        if not top_words:
            return "General discussion"

        # Simple heuristic to create topic descriptions
        primary_word = top_words[0].replace("_", " ")
        return f"Discussion about {primary_word}"

    def _categorize_speaking_pace(self, wpm: float) -> str:
        """Categorize speaking pace based on words per minute."""
        if wpm < 120:
            return "slow"
        elif wpm < 160:
            return "normal"
        elif wpm < 200:
            return "fast"
        else:
            return "very_fast"

    def _assess_formality(self, text: str) -> str:
        """Assess the formality level of the text."""
        formal_indicators = len(
            re.findall(
                r"\b(furthermore|however|therefore|moreover|nevertheless)\b",
                text,
                re.IGNORECASE,
            )
        )
        informal_indicators = len(
            re.findall(
                r"\b(yeah|okay|um|uh|like|you know|kind of)\b", text, re.IGNORECASE
            )
        )

        total_words = len(text.split())
        formal_ratio = formal_indicators / total_words * 100 if total_words > 0 else 0
        informal_ratio = (
            informal_indicators / total_words * 100 if total_words > 0 else 0
        )

        if formal_ratio > informal_ratio and formal_ratio > 0.5:
            return "formal"
        elif informal_ratio > formal_ratio and informal_ratio > 1:
            return "informal"
        else:
            return "neutral"

    def _assess_complexity(self, text: str) -> str:
        """Assess text complexity based on sentence length and vocabulary."""
        sentences = re.split(r"[.!?]+", text)
        words = text.split()

        avg_sentence_length = (
            len(words) / len([s for s in sentences if s.strip()]) if sentences else 0
        )
        unique_word_ratio = len(set(words)) / len(words) if words else 0

        if avg_sentence_length > 20 and unique_word_ratio > 0.6:
            return "high"
        elif avg_sentence_length > 15 or unique_word_ratio > 0.5:
            return "medium"
        else:
            return "low"

    def _assess_structure(self, text: str) -> str:
        """Assess the structural organization of the text."""
        structure_indicators = [
            r"\b(first|second|third|finally|in conclusion)\b",
            r"\b(next|then|after that|meanwhile)\b",
            r"\b(however|but|although|despite)\b",
        ]

        structure_score = 0
        for pattern in structure_indicators:
            structure_score += len(re.findall(pattern, text, re.IGNORECASE))

        total_sentences = len(re.split(r"[.!?]+", text))
        structure_ratio = (
            structure_score / total_sentences if total_sentences > 0 else 0
        )

        if structure_ratio > 0.1:
            return "well_structured"
        elif structure_ratio > 0.05:
            return "moderately_structured"
        else:
            return "unstructured"

    def _estimate_reading_level(self, text: str) -> str:
        """Estimate reading level using basic metrics."""
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        words = text.split()

        if not sentences or not words:
            return "unknown"

        avg_sentence_length = len(words) / len(sentences)

        # Simple heuristic based on sentence length
        if avg_sentence_length > 25:
            return "advanced"
        elif avg_sentence_length > 20:
            return "intermediate"
        elif avg_sentence_length > 15:
            return "basic"
        else:
            return "elementary"

    def _calculate_interactivity_score(
        self, questions: List[Dict], emphasis_cues: List[Dict], segments: List[Dict]
    ) -> float:
        """Calculate a score representing content interactivity."""
        if not segments:
            return 0.0

        question_score = len(questions) / len(segments) * 50
        emphasis_score = len(emphasis_cues) / len(segments) * 30

        return min(round(question_score + emphasis_score, 2), 100.0)

    def _categorize_engagement_level(
        self, questions: List[Dict], emphasis_cues: List[Dict], segments: List[Dict]
    ) -> str:
        """Categorize the engagement level of the content."""
        score = self._calculate_interactivity_score(questions, emphasis_cues, segments)

        if score > 15:
            return "high"
        elif score > 8:
            return "medium"
        else:
            return "low"

    def _calculate_lexical_diversity(self, words: List[str]) -> float:
        """Calculate lexical diversity (type-token ratio)."""
        if not words:
            return 0.0
        return len(set(word.lower() for word in words if word.isalpha())) / len(words)

    def _estimate_syntactic_complexity(self, text: str) -> float:
        """Estimate syntactic complexity based on sentence structure."""
        complex_patterns = [
            r"\b(although|because|since|while|whereas|if)\b",  # Subordinating conjunctions
            r"\b(however|therefore|furthermore|moreover)\b",  # Conjunctive adverbs
            r",\s*which\s+",  # Relative clauses
            r";\s*",  # Semicolons
        ]

        complexity_score = 0
        for pattern in complex_patterns:
            complexity_score += len(re.findall(pattern, text, re.IGNORECASE))

        sentences = len(re.split(r"[.!?]+", text))
        return min(complexity_score / sentences if sentences > 0 else 0, 1.0)

    def _estimate_concept_density(self, text: str, basic_analysis: Dict) -> float:
        """Estimate concept density based on keyword frequency."""
        keyword_matches = basic_analysis.get("keyword_matches", [])
        total_words = len(text.split())

        if not total_words:
            return 0.0

        total_keyword_instances = sum(
            match.get("count", 0) for match in keyword_matches
        )
        return min(total_keyword_instances / total_words, 1.0)

    def _analyze_temporal_patterns(self, segments: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal patterns in the content."""
        patterns = {"pacing": {}, "segment_distribution": {}, "activity_timeline": []}

        # Analyze segment durations if available
        durations = []
        for segment in segments:
            if "start" in segment and "end" in segment:
                duration = segment["end"] - segment["start"]
                durations.append(duration)

        if durations:
            patterns["pacing"] = {
                "average_segment_duration": round(np.mean(durations), 2),
                "duration_variance": round(np.var(durations), 2),
                "pacing_consistency": (
                    "consistent" if np.var(durations) < 2 else "variable"
                ),
            }

        # Create activity timeline (simplified)
        timeline_intervals = min(10, len(segments))
        interval_size = (
            len(segments) // timeline_intervals if timeline_intervals > 0 else 1
        )

        for i in range(0, len(segments), interval_size):
            interval_segments = segments[i : i + interval_size]
            total_words = sum(len(seg["text"].split()) for seg in interval_segments)

            patterns["activity_timeline"].append(
                {
                    "interval": i // interval_size + 1,
                    "word_count": total_words,
                    "segment_count": len(interval_segments),
                    "intensity": "high" if total_words > 50 else "low",
                }
            )

        return patterns

    def _calculate_analysis_completeness(self, ai_insights: Dict) -> float:
        """Calculate what percentage of analysis modules were successfully used."""
        total_modules = 6  # Total number of analysis modules
        successful_modules = len(
            ai_insights.get("processing_info", {}).get("capabilities_used", [])
        )
        return round((successful_modules / total_modules) * 100, 1)

    def _get_top_keyword(self, basic_analysis: Dict) -> Optional[str]:
        """Get the most frequent keyword from basic analysis."""
        keyword_matches = basic_analysis.get("keyword_matches", [])
        if keyword_matches:
            return max(keyword_matches, key=lambda x: x.get("count", 0)).get("keyword")
        return None

    def _get_peak_sentiment(self, ai_insights: Dict) -> Optional[Dict[str, Any]]:
        """Get the segment with peak sentiment (positive or negative)."""
        sentiment_data = ai_insights.get("sentiment_analysis", {})
        emotional_peaks = sentiment_data.get("emotional_peaks", [])

        if emotional_peaks:
            return max(emotional_peaks, key=lambda x: x.get("intensity", 0))
        return None

    def _get_primary_topic(self, ai_insights: Dict) -> Optional[str]:
        """Get the primary topic from topic modeling."""
        topic_data = ai_insights.get("topic_modeling", {})
        main_topics = topic_data.get("main_topics", [])

        if main_topics:
            return max(main_topics, key=lambda x: x.get("strength", 0)).get(
                "description"
            )
        return None


# Utility function for external integration
def create_ai_insights_engine() -> AIInsightsEngine:
    """Factory function to create an AI insights engine instance."""
    return AIInsightsEngine()
