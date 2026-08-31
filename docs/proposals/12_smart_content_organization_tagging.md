# Smart Content Organization & Tagging

## 🎯 Issue Overview

**Priority**: ⭐⭐⭐ High Priority  
**Epic**: User Experience & Content Management  
**Estimated Effort**: 5-7 weeks  
**Dependencies**: AI/ML libraries, content analysis system, database schema updates

### Problem Statement

Users accumulate large amounts of transcribed content but struggle with organization and retrieval, leading to:

- **Manual tagging burden** - Users must manually categorize every session
- **Inconsistent organization** - Different users tag similar content differently
- **Poor content discoverability** - Related content scattered without clear relationships
- **No automatic categorization** - System doesn't learn from content patterns
- **Limited metadata extraction** - Missing key information like topics, speakers, sentiment
- **Difficult content curation** - No smart collections or automated groupings
- **Scalability issues** - Organization becomes harder as content volume grows

### Solution Overview

Implement an AI-powered content organization system that automatically tags, categorizes, and organizes transcriptions using machine learning, natural language processing, and intelligent clustering algorithms to create smart collections and improve content discoverability.

## ✨ Features & Capabilities

### 🏷️ Intelligent Auto-Tagging

#### AI-Powered Tag Generation

- Automatic topic extraction using NLP and topic modeling
- Speaker identification and consistent naming
- Sentiment analysis and emotional tone detection
- Intent recognition (meeting, interview, presentation, etc.)
- Domain-specific tag recognition (technical, business, personal)

#### Smart Tag Suggestions

- Real-time tag recommendations during upload
- Learning from user tagging patterns
- Contextual tag suggestions based on content similarity
- Bulk tagging operations for efficiency
- Tag confidence scoring and validation

#### Tag Management System

- Hierarchical tag structures with parent-child relationships
- Tag merging and aliasing for consistency
- Popular tag discovery and trending topics
- Custom tag templates for different content types
- Tag analytics and usage insights

### 📁 Automated Content Organization

#### Smart Collections

- Automatic grouping of related content
- Project-based organization with smart detection
- Speaker-based collections with identity management
- Topic-based clustering using machine learning
- Time-based organization with intelligent chronology

#### Content Classification

- Meeting vs. interview vs. presentation detection
- Formal vs. informal content classification
- Quality-based categorization (audio quality, transcript accuracy)
- Length-based organization (short clips, full sessions, multi-part series)
- Language and accent detection for international content

## 🏗️ Technical Implementation

### Phase 1: AI Content Analysis Engine (2-3 weeks)

#### Task 1.1: Content Analysis Service
**File**: `src/services/content_analysis.py`

```python
"""
AI-powered content analysis service for automatic tagging and organization.
Provides intelligent content categorization, topic extraction, and metadata enrichment.
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict
import hashlib

try:
    import spacy
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.chunk import ne_chunk
    from nltk.tag import pos_tag
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans, DBSCAN
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

try:
    from textblob import TextBlob
    import langdetect
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ContentTag:
    """Represents an automatically generated or suggested tag."""
    text: str
    category: str  # 'topic', 'speaker', 'sentiment', 'intent', 'domain'
    confidence: float
    source: str  # 'ai_generated', 'user_confirmed', 'pattern_detected'
    metadata: Dict[str, Any] = None

@dataclass
class ContentAnalysis:
    """Comprehensive analysis results for a piece of content."""
    session_id: str
    content_type: str  # 'meeting', 'interview', 'presentation', 'conversation'
    topics: List[ContentTag]
    speakers: List[ContentTag]
    sentiment: Dict[str, float]  # positive, negative, neutral scores
    intent: ContentTag
    language: str
    quality_metrics: Dict[str, float]
    suggested_tags: List[ContentTag]
    smart_collections: List[str]
    metadata: Dict[str, Any]

@dataclass
class SmartCollection:
    """Represents an automatically created content collection."""
    id: str
    name: str
    description: str
    criteria: Dict[str, Any]
    content_ids: List[str]
    auto_update: bool
    confidence: float
    created_at: str

class TopicExtractor:
    """Extracts topics and themes from transcript content."""
    
    def __init__(self):
        """Initialize topic extraction with ML models."""
        self.vectorizer = None
        self.lda_model = None
        self.nlp_model = None
        self.stop_words = set()
        
        if ML_AVAILABLE and NLP_AVAILABLE:
            try:
                self.vectorizer = TfidfVectorizer(
                    max_features=1000,
                    stop_words='english',
                    ngram_range=(1, 3),
                    min_df=2,
                    max_df=0.8
                )
                
                self.lda_model = LatentDirichletAllocation(
                    n_components=10,
                    random_state=42,
                    max_iter=10
                )
                
                # Download required NLTK data
                try:
                    nltk.download('stopwords', quiet=True)
                    nltk.download('punkt', quiet=True)
                    nltk.download('averaged_perceptron_tagger', quiet=True)
                    nltk.download('maxent_ne_chunker', quiet=True)
                    nltk.download('words', quiet=True)
                    self.stop_words = set(stopwords.words('english'))
                except:
                    logger.warning("Could not download NLTK data")
                
                # Load spaCy model
                try:
                    self.nlp_model = spacy.load('en_core_web_sm')
                except OSError:
                    logger.warning("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
                    
                logger.info("Topic extractor initialized with ML models")
                
            except Exception as e:
                logger.error(f"Error initializing topic extractor: {e}")
    
    def extract_topics(self, content: str, max_topics: int = 5) -> List[ContentTag]:
        """
        Extract main topics from transcript content.
        
        Args:
            content: Transcript text
            max_topics: Maximum number of topics to extract
            
        Returns:
            List of topic tags with confidence scores
        """
        if not content or not content.strip():
            return []
        
        topics = []
        
        try:
            # Method 1: Named Entity Recognition with spaCy
            if self.nlp_model:
                topics.extend(self._extract_named_entities(content))
            
            # Method 2: Keyword extraction with TF-IDF
            topics.extend(self._extract_tfidf_keywords(content, max_topics))
            
            # Method 3: Topic modeling with LDA
            if len(content.split()) > 50:  # Only for longer content
                topics.extend(self._extract_lda_topics(content))
            
            # Method 4: Pattern-based topic detection
            topics.extend(self._extract_pattern_topics(content))
            
            # Deduplicate and rank topics
            topics = self._deduplicate_and_rank_topics(topics, max_topics)
            
            return topics
            
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
            return []
    
    def _extract_named_entities(self, content: str) -> List[ContentTag]:
        """Extract named entities as topics using spaCy."""
        topics = []
        
        try:
            doc = self.nlp_model(content[:10000])  # Limit length for performance
            
            # Extract entities by type
            entity_counts = defaultdict(int)
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE']:
                    entity_counts[ent.text.lower()] += 1
            
            # Convert to ContentTag objects
            for entity, count in entity_counts.items():
                confidence = min(0.9, count / 10)  # Scale confidence
                topics.append(ContentTag(
                    text=entity.title(),
                    category='topic',
                    confidence=confidence,
                    source='ai_generated',
                    metadata={'extraction_method': 'named_entity', 'count': count}
                ))
            
        except Exception as e:
            logger.error(f"Error in named entity extraction: {e}")
        
        return topics
    
    def _extract_tfidf_keywords(self, content: str, max_keywords: int = 10) -> List[ContentTag]:
        """Extract keywords using TF-IDF vectorization."""
        topics = []
        
        try:
            if not self.vectorizer:
                return topics
            
            # Prepare text
            sentences = sent_tokenize(content)
            if len(sentences) < 3:
                return topics
            
            # Fit TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform(sentences)
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get top keywords
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            top_indices = mean_scores.argsort()[-max_keywords:][::-1]
            
            for idx in top_indices:
                if mean_scores[idx] > 0.1:  # Minimum relevance threshold
                    keyword = feature_names[idx]
                    # Filter out stop words and short words
                    if len(keyword) > 2 and keyword.lower() not in self.stop_words:
                        topics.append(ContentTag(
                            text=keyword.title(),
                            category='topic',
                            confidence=float(mean_scores[idx]),
                            source='ai_generated',
                            metadata={'extraction_method': 'tfidf', 'score': float(mean_scores[idx])}
                        ))
            
        except Exception as e:
            logger.error(f"Error in TF-IDF keyword extraction: {e}")
        
        return topics
    
    def _extract_lda_topics(self, content: str) -> List[ContentTag]:
        """Extract topics using Latent Dirichlet Allocation."""
        topics = []
        
        try:
            if not self.lda_model or not self.vectorizer:
                return topics
            
            # Prepare text for LDA
            sentences = sent_tokenize(content)
            if len(sentences) < 10:
                return topics
            
            # Vectorize and run LDA
            tfidf_matrix = self.vectorizer.fit_transform(sentences)
            lda_output = self.lda_model.fit_transform(tfidf_matrix)
            
            # Get feature names
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Extract top words from dominant topics
            dominant_topic_idx = np.argmax(np.mean(lda_output, axis=0))
            topic_words = self.lda_model.components_[dominant_topic_idx]
            top_word_indices = topic_words.argsort()[-5:][::-1]
            
            for idx in top_word_indices:
                word = feature_names[idx]
                confidence = float(topic_words[idx] / np.sum(topic_words))
                
                if len(word) > 2 and confidence > 0.01:
                    topics.append(ContentTag(
                        text=word.title(),
                        category='topic',
                        confidence=confidence,
                        source='ai_generated',
                        metadata={'extraction_method': 'lda', 'topic_id': dominant_topic_idx}
                    ))
            
        except Exception as e:
            logger.error(f"Error in LDA topic extraction: {e}")
        
        return topics
    
    def _extract_pattern_topics(self, content: str) -> List[ContentTag]:
        """Extract topics using pattern matching for common business/technical terms."""
        topics = []
        
        # Define topic patterns
        topic_patterns = {
            'Technology': [
                r'\b(?:AI|artificial intelligence|machine learning|ML|deep learning)\b',
                r'\b(?:API|database|software|application|system|platform)\b',
                r'\b(?:cloud|AWS|Azure|Google Cloud|infrastructure)\b',
                r'\b(?:security|encryption|authentication|privacy)\b'
            ],
            'Business': [
                r'\b(?:revenue|profit|budget|cost|ROI|investment)\b',
                r'\b(?:strategy|planning|goal|objective|target)\b',
                r'\b(?:customer|client|user|stakeholder)\b',
                r'\b(?:marketing|sales|growth|acquisition)\b'
            ],
            'Project Management': [
                r'\b(?:deadline|milestone|timeline|schedule)\b',
                r'\b(?:task|deliverable|requirement|specification)\b',
                r'\b(?:team|collaboration|meeting|standup)\b',
                r'\b(?:agile|scrum|kanban|waterfall)\b'
            ],
            'Meeting Types': [
                r'\b(?:presentation|demo|review|retrospective)\b',
                r'\b(?:interview|onboarding|training|workshop)\b',
                r'\b(?:planning|brainstorm|discussion|decision)\b'
            ]
        }
        
        try:
            content_lower = content.lower()
            
            for category, patterns in topic_patterns.items():
                matches = 0
                for pattern in patterns:
                    matches += len(re.findall(pattern, content_lower, re.IGNORECASE))
                
                if matches > 0:
                    confidence = min(0.8, matches / 20)  # Scale confidence
                    topics.append(ContentTag(
                        text=category,
                        category='topic',
                        confidence=confidence,
                        source='pattern_detected',
                        metadata={'extraction_method': 'pattern', 'match_count': matches}
                    ))
            
        except Exception as e:
            logger.error(f"Error in pattern topic extraction: {e}")
        
        return topics
    
    def _deduplicate_and_rank_topics(self, topics: List[ContentTag], 
                                    max_topics: int) -> List[ContentTag]:
        """Remove duplicates and rank topics by confidence."""
        try:
            # Group similar topics
            topic_groups = defaultdict(list)
            
            for topic in topics:
                # Simple similarity grouping by first word
                key = topic.text.lower().split()[0] if topic.text else 'unknown'
                topic_groups[key].append(topic)
            
            # Select best topic from each group
            final_topics = []
            for group_topics in topic_groups.values():
                # Sort by confidence and take the best
                group_topics.sort(key=lambda t: t.confidence, reverse=True)
                final_topics.append(group_topics[0])
            
            # Sort all topics by confidence and limit
            final_topics.sort(key=lambda t: t.confidence, reverse=True)
            return final_topics[:max_topics]
            
        except Exception as e:
            logger.error(f"Error deduplicating topics: {e}")
            return topics[:max_topics]

class SentimentAnalyzer:
    """Analyzes sentiment and emotional tone of content."""
    
    def __init__(self):
        """Initialize sentiment analyzer."""
        self.available = SENTIMENT_AVAILABLE
        
    def analyze_sentiment(self, content: str) -> Dict[str, float]:
        """
        Analyze sentiment of transcript content.
        
        Args:
            content: Transcript text
            
        Returns:
            Dictionary with sentiment scores
        """
        if not self.available or not content:
            return {'positive': 0.5, 'negative': 0.5, 'neutral': 0.5, 'compound': 0.0}
        
        try:
            blob = TextBlob(content)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Convert to positive/negative/neutral scores
            if polarity > 0.1:
                positive = (polarity + 1) / 2
                negative = 0.1
                neutral = 1 - positive - negative
            elif polarity < -0.1:
                negative = abs(polarity)
                positive = 0.1
                neutral = 1 - positive - negative
            else:
                neutral = 0.8
                positive = 0.1
                negative = 0.1
            
            return {
                'positive': positive,
                'negative': negative,
                'neutral': neutral,
                'compound': polarity,
                'subjectivity': subjectivity
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {'positive': 0.5, 'negative': 0.5, 'neutral': 0.5, 'compound': 0.0}

class ContentClassifier:
    """Classifies content type and intent."""
    
    def __init__(self):
        """Initialize content classifier."""
        self.meeting_patterns = [
            r'\b(?:meeting|agenda|action item|follow up)\b',
            r'\b(?:discuss|decision|vote|approve)\b',
            r'\b(?:team|group|committee|board)\b'
        ]
        
        self.interview_patterns = [
            r'\b(?:interview|candidate|position|role)\b',
            r'\b(?:experience|background|skills|qualification)\b',
            r'\b(?:question|answer|tell me about|describe)\b'
        ]
        
        self.presentation_patterns = [
            r'\b(?:presentation|slide|demo|show)\b',
            r'\b(?:introduce|overview|summary|conclusion)\b',
            r'\b(?:next slide|moving on|in summary)\b'
        ]
        
        self.training_patterns = [
            r'\b(?:training|tutorial|lesson|learn)\b',
            r'\b(?:instruction|guide|step|process)\b',
            r'\b(?:example|practice|exercise)\b'
        ]
    
    def classify_content(self, content: str, metadata: Dict[str, Any] = None) -> ContentTag:
        """
        Classify content type and intent.
        
        Args:
            content: Transcript text
            metadata: Additional metadata
            
        Returns:
            ContentTag with classification result
        """
        try:
            content_lower = content.lower()
            
            # Score each content type
            scores = {
                'meeting': self._score_patterns(content_lower, self.meeting_patterns),
                'interview': self._score_patterns(content_lower, self.interview_patterns),
                'presentation': self._score_patterns(content_lower, self.presentation_patterns),
                'training': self._score_patterns(content_lower, self.training_patterns),
                'conversation': 0.3  # Default baseline
            }
            
            # Additional scoring based on metadata
            if metadata:
                duration = metadata.get('duration', 0)
                speaker_count = len(metadata.get('speakers', []))
                
                # Long sessions with multiple speakers likely meetings
                if duration > 1800 and speaker_count > 2:  # 30+ minutes, 3+ speakers
                    scores['meeting'] += 0.2
                
                # Short sessions with 2 speakers likely interviews
                elif 600 < duration < 2400 and speaker_count == 2:  # 10-40 minutes, 2 speakers
                    scores['interview'] += 0.2
                
                # Single speaker likely presentation
                elif speaker_count == 1:
                    scores['presentation'] += 0.2
            
            # Find best classification
            best_type = max(scores.keys(), key=lambda k: scores[k])
            confidence = min(0.9, scores[best_type])
            
            return ContentTag(
                text=best_type,
                category='intent',
                confidence=confidence,
                source='ai_generated',
                metadata={'scores': scores, 'classification_method': 'pattern_based'}
            )
            
        except Exception as e:
            logger.error(f"Error classifying content: {e}")
            return ContentTag(
                text='conversation',
                category='intent',
                confidence=0.5,
                source='ai_generated',
                metadata={'error': str(e)}
            )
    
    def _score_patterns(self, content: str, patterns: List[str]) -> float:
        """Score content against pattern list."""
        total_matches = 0
        for pattern in patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            total_matches += matches
        
        # Normalize score (rough heuristic)
        return min(0.8, total_matches / 10)

class SmartContentAnalyzer:
    """Main service for AI-powered content analysis and tagging."""
    
    def __init__(self):
        """Initialize content analyzer with all sub-components."""
        self.topic_extractor = TopicExtractor()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.content_classifier = ContentClassifier()
        
        logger.info("Smart content analyzer initialized")
    
    def analyze_content(self, session_data: Dict[str, Any]) -> ContentAnalysis:
        """
        Perform comprehensive content analysis.
        
        Args:
            session_data: Complete session data with transcript and metadata
            
        Returns:
            ContentAnalysis with all extracted information
        """
        try:
            session_id = session_data.get('id', 'unknown')
            content = session_data.get('transcript', '')
            
            if not content or not content.strip():
                return self._create_empty_analysis(session_id)
            
            # Extract topics
            topics = self.topic_extractor.extract_topics(content)
            
            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze_sentiment(content)
            
            # Classify content type
            intent = self.content_classifier.classify_content(content, session_data)
            
            # Extract speaker information
            speakers = self._extract_speaker_tags(session_data)
            
            # Detect language
            language = self._detect_language(content)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(session_data)
            
            # Generate suggested tags
            suggested_tags = self._generate_suggested_tags(topics, speakers, intent, sentiment)
            
            # Determine smart collections
            smart_collections = self._determine_smart_collections(
                topics, speakers, intent, session_data
            )
            
            return ContentAnalysis(
                session_id=session_id,
                content_type=intent.text,
                topics=topics,
                speakers=speakers,
                sentiment=sentiment,
                intent=intent,
                language=language,
                quality_metrics=quality_metrics,
                suggested_tags=suggested_tags,
                smart_collections=smart_collections,
                metadata={
                    'analysis_timestamp': datetime.now().isoformat(),
                    'content_length': len(content),
                    'word_count': len(content.split())
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing content for session {session_data.get('id', 'unknown')}: {e}")
            return self._create_empty_analysis(session_data.get('id', 'unknown'))
    
    def _extract_speaker_tags(self, session_data: Dict[str, Any]) -> List[ContentTag]:
        """Extract speaker information as tags."""
        speakers = []
        
        try:
            # From segments
            segments = session_data.get('segments', [])
            speaker_counts = defaultdict(int)
            
            for segment in segments:
                speaker = segment.get('speaker')
                if speaker:
                    speaker_counts[speaker] += 1
            
            # Create speaker tags
            total_segments = len(segments)
            for speaker, count in speaker_counts.items():
                confidence = min(0.9, count / max(1, total_segments))
                speakers.append(ContentTag(
                    text=speaker,
                    category='speaker',
                    confidence=confidence,
                    source='ai_generated',
                    metadata={'segment_count': count, 'total_segments': total_segments}
                ))
            
            # Sort by participation
            speakers.sort(key=lambda s: s.confidence, reverse=True)
            
        except Exception as e:
            logger.error(f"Error extracting speaker tags: {e}")
        
        return speakers
    
    def _detect_language(self, content: str) -> str:
        """Detect content language."""
        try:
            if SENTIMENT_AVAILABLE:
                import langdetect
                return langdetect.detect(content[:1000])  # Sample first 1000 chars
            else:
                return 'en'  # Default to English
        except:
            return 'en'
    
    def _calculate_quality_metrics(self, session_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate content quality metrics."""
        try:
            content = session_data.get('transcript', '')
            
            # Basic quality metrics
            word_count = len(content.split())
            char_count = len(content)
            
            # Estimate accuracy based on content characteristics
            accuracy_score = 0.8  # Default
            
            # Check for common transcription errors
            error_patterns = [
                r'\[inaudible\]', r'\[unclear\]', r'\?\?\?', r'\.\.\.',
                r'\b[a-z]{1,2}\b(?:\s+\b[a-z]{1,2}\b){3,}'  # Many short words (OCR errors)
            ]
            
            error_count = 0
            for pattern in error_patterns:
                error_count += len(re.findall(pattern, content, re.IGNORECASE))
            
            if word_count > 0:
                error_ratio = error_count / word_count
                accuracy_score = max(0.3, 0.9 - error_ratio * 2)
            
            return {
                'accuracy_score': accuracy_score,
                'completeness_score': min(1.0, word_count / 100),  # Based on length
                'clarity_score': accuracy_score,  # Simplified
                'word_count': word_count,
                'character_count': char_count
            }
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            return {'accuracy_score': 0.8, 'completeness_score': 0.8, 'clarity_score': 0.8}
    
    def _generate_suggested_tags(self, topics: List[ContentTag], speakers: List[ContentTag],
                                intent: ContentTag, sentiment: Dict[str, float]) -> List[ContentTag]:
        """Generate suggested tags from analysis results."""
        suggested = []
        
        try:
            # Add top topics as suggestions
            for topic in topics[:5]:
                suggested.append(ContentTag(
                    text=f"#{topic.text.lower().replace(' ', '_')}",
                    category='topic_tag',
                    confidence=topic.confidence * 0.9,
                    source='ai_generated',
                    metadata={'original_topic': topic.text}
                ))
            
            # Add intent-based tag
            suggested.append(ContentTag(
                text=f"#{intent.text}",
                category='intent_tag',
                confidence=intent.confidence,
                source='ai_generated',
                metadata={'classification': intent.text}
            ))
            
            # Add sentiment-based tag if strong
            if sentiment.get('compound', 0) > 0.3:
                suggested.append(ContentTag(
                    text="#positive_tone",
                    category='sentiment_tag',
                    confidence=sentiment['positive'],
                    source='ai_generated',
                    metadata={'sentiment_analysis': sentiment}
                ))
            elif sentiment.get('compound', 0) < -0.3:
                suggested.append(ContentTag(
                    text="#negative_tone",
                    category='sentiment_tag',
                    confidence=sentiment['negative'],
                    source='ai_generated',
                    metadata={'sentiment_analysis': sentiment}
                ))
            
            # Add speaker count tag
            if len(speakers) > 1:
                suggested.append(ContentTag(
                    text=f"#{len(speakers)}_speakers",
                    category='metadata_tag',
                    confidence=0.8,
                    source='ai_generated',
                    metadata={'speaker_count': len(speakers)}
                ))
            
        except Exception as e:
            logger.error(f"Error generating suggested tags: {e}")
        
        return suggested
    
    def _determine_smart_collections(self, topics: List[ContentTag], speakers: List[ContentTag],
                                   intent: ContentTag, session_data: Dict[str, Any]) -> List[str]:
        """Determine which smart collections this content belongs to."""
        collections = []
        
        try:
            # Content type collection
            collections.append(f"{intent.text.title()} Sessions")
            
            # Speaker-based collections
            for speaker in speakers[:2]:  # Top 2 speakers
                collections.append(f"Sessions with {speaker.text}")
            
            # Topic-based collections
            for topic in topics[:3]:  # Top 3 topics
                if topic.confidence > 0.6:
                    collections.append(f"{topic.text} Discussions")
            
            # Time-based collections
            timestamp = session_data.get('created_at', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    collections.append(f"{dt.strftime('%B %Y')} Sessions")
                    collections.append(f"Q{((dt.month-1)//3)+1} {dt.year} Sessions")
                except:
                    pass
            
            # Duration-based collections
            duration = session_data.get('duration', 0)
            if duration < 900:  # 15 minutes
                collections.append("Quick Sessions")
            elif duration > 3600:  # 1 hour
                collections.append("Extended Sessions")
            
        except Exception as e:
            logger.error(f"Error determining smart collections: {e}")
        
        return collections
    
    def _create_empty_analysis(self, session_id: str) -> ContentAnalysis:
        """Create empty analysis for sessions with no content."""
        return ContentAnalysis(
            session_id=session_id,
            content_type='unknown',
            topics=[],
            speakers=[],
            sentiment={'positive': 0.5, 'negative': 0.5, 'neutral': 0.5, 'compound': 0.0},
            intent=ContentTag('unknown', 'intent', 0.0, 'ai_generated'),
            language='en',
            quality_metrics={'accuracy_score': 0.0, 'completeness_score': 0.0, 'clarity_score': 0.0},
            suggested_tags=[],
            smart_collections=[],
            metadata={'analysis_timestamp': datetime.now().isoformat(), 'error': 'no_content'}
        )

# Factory function
def create_content_analyzer() -> SmartContentAnalyzer:
    """Create smart content analyzer instance."""
    return SmartContentAnalyzer()
```

**Acceptance Criteria**:

- ✅ AI-powered topic extraction using multiple NLP techniques
- ✅ Automatic content classification (meeting, interview, presentation, etc.)
- ✅ Sentiment analysis and emotional tone detection
- ✅ Speaker identification and participation analysis
- ✅ Quality metrics calculation for transcript assessment
- ✅ Smart tag generation with confidence scoring
- ✅ Automatic smart collection assignment
- ✅ Graceful degradation when AI libraries unavailable

#### Task 1.2: Smart Collections Management
**File**: `src/services/smart_collections.py`

```python
"""
Smart collections management service for automatic content organization.
Creates and manages intelligent groupings of related transcription content.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import uuid

from src.services.content_analysis import ContentAnalysis, SmartCollection

logger = logging.getLogger(__name__)

@dataclass
class CollectionRule:
    """Defines rules for automatic collection creation and maintenance."""
    name: str
    criteria_type: str  # 'topic', 'speaker', 'content_type', 'date_range', 'quality', 'custom'
    criteria_value: Any
    auto_update: bool
    min_items: int
    max_items: Optional[int]
    confidence_threshold: float

class SmartCollectionsManager:
    """Manages automatic creation and maintenance of smart content collections."""
    
    def __init__(self):
        """Initialize smart collections manager."""
        self.collections = {}  # collection_id -> SmartCollection
        self.collection_rules = []  # List of CollectionRule objects
        self.content_index = defaultdict(set)  # content_id -> set of collection_ids
        
        # Initialize default collection rules
        self._initialize_default_rules()
        
        logger.info("Smart collections manager initialized")
    
    def _initialize_default_rules(self):
        """Initialize default collection rules."""
        default_rules = [
            # Content type collections
            CollectionRule(
                name="Meeting Sessions",
                criteria_type="content_type",
                criteria_value="meeting",
                auto_update=True,
                min_items=1,
                max_items=None,
                confidence_threshold=0.6
            ),
            CollectionRule(
                name="Interview Sessions",
                criteria_type="content_type", 
                criteria_value="interview",
                auto_update=True,
                min_items=1,
                max_items=None,
                confidence_threshold=0.6
            ),
            CollectionRule(
                name="Presentation Sessions",
                criteria_type="content_type",
                criteria_value="presentation", 
                auto_update=True,
                min_items=1,
                max_items=None,
                confidence_threshold=0.6
            ),
            
            # Quality-based collections
            CollectionRule(
                name="High Quality Transcripts",
                criteria_type="quality",
                criteria_value={"accuracy_score": 0.9},
                auto_update=True,
                min_items=3,
                max_items=None,
                confidence_threshold=0.8
            ),
            
            # Recent content collections
            CollectionRule(
                name="Recent Sessions",
                criteria_type="date_range",
                criteria_value={"days": 7},
                auto_update=True,
                min_items=1,
                max_items=50,
                confidence_threshold=0.9
            ),
            CollectionRule(
                name="This Month",
                criteria_type="date_range", 
                criteria_value={"days": 30},
                auto_update=True,
                min_items=1,
                max_items=None,
                confidence_threshold=0.9
            )
        ]
        
        self.collection_rules.extend(default_rules)
    
    def process_content_analysis(self, analysis: ContentAnalysis, 
                               session_data: Dict[str, Any]) -> List[str]:
        """
        Process content analysis and assign to appropriate smart collections.
        
        Args:
            analysis: ContentAnalysis result
            session_data: Original session data
            
        Returns:
            List of collection IDs that content was added to
        """
        try:
            assigned_collections = []
            
            # Process each collection rule
            for rule in self.collection_rules:
                if self._content_matches_rule(analysis, session_data, rule):
                    collection_id = self._get_or_create_collection(rule, analysis)
                    if collection_id:
                        if self._add_content_to_collection(collection_id, analysis.session_id):
                            assigned_collections.append(collection_id)
            
            # Process dynamic collections from analysis
            for collection_name in analysis.smart_collections:
                collection_id = self._get_or_create_dynamic_collection(
                    collection_name, analysis, session_data
                )
                if collection_id:
                    if self._add_content_to_collection(collection_id, analysis.session_id):
                        assigned_collections.append(collection_id)
            
            # Update content index
            self.content_index[analysis.session_id].update(assigned_collections)
            
            return assigned_collections
            
        except Exception as e:
            logger.error(f"Error processing content analysis for collections: {e}")
            return []
    
    def _content_matches_rule(self, analysis: ContentAnalysis, 
                            session_data: Dict[str, Any], rule: CollectionRule) -> bool:
        """Check if content matches collection rule criteria."""
        try:
            if rule.criteria_type == "content_type":
                return (analysis.intent.text == rule.criteria_value and 
                       analysis.intent.confidence >= rule.confidence_threshold)
            
            elif rule.criteria_type == "topic":
                for topic in analysis.topics:
                    if (topic.text.lower() == rule.criteria_value.lower() and
                        topic.confidence >= rule.confidence_threshold):
                        return True
                return False
            
            elif rule.criteria_type == "speaker":
                for speaker in analysis.speakers:
                    if (speaker.text.lower() == rule.criteria_value.lower() and
                        speaker.confidence >= rule.confidence_threshold):
                        return True
                return False
            
            elif rule.criteria_type == "quality":
                quality_metrics = analysis.quality_metrics
                for metric, threshold in rule.criteria_value.items():
                    if quality_metrics.get(metric, 0) >= threshold:
                        return True
                return False
            
            elif rule.criteria_type == "date_range":
                try:
                    timestamp = session_data.get('created_at', '')
                    if timestamp:
                        content_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        days_ago = rule.criteria_value.get('days', 7)
                        cutoff_date = datetime.now() - timedelta(days=days_ago)
                        return content_date >= cutoff_date
                except:
                    return False
            
            elif rule.criteria_type == "custom":
                # Custom rule evaluation would go here
                return self._evaluate_custom_rule(rule.criteria_value, analysis, session_data)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rule match: {e}")
            return False
    
    def _get_or_create_collection(self, rule: CollectionRule, 
                                analysis: ContentAnalysis) -> Optional[str]:
        """Get existing collection or create new one based on rule."""
        try:
            # Check for existing collection with this rule
            for collection_id, collection in self.collections.items():
                if (collection.name == rule.name and 
                    collection.criteria.get('rule_type') == rule.criteria_type):
                    return collection_id
            
            # Create new collection
            collection_id = str(uuid.uuid4())
            
            collection = SmartCollection(
                id=collection_id,
                name=rule.name,
                description=f"Automatically created collection for {rule.criteria_type}: {rule.criteria_value}",
                criteria={
                    'rule_type': rule.criteria_type,
                    'rule_value': rule.criteria_value,
                    'confidence_threshold': rule.confidence_threshold
                },
                content_ids=[],
                auto_update=rule.auto_update,
                confidence=0.8,
                created_at=datetime.now().isoformat()
            )
            
            self.collections[collection_id] = collection
            logger.info(f"Created new smart collection: {rule.name}")
            
            return collection_id
            
        except Exception as e:
            logger.error(f"Error creating collection for rule {rule.name}: {e}")
            return None
    
    def _get_or_create_dynamic_collection(self, collection_name: str,
                                        analysis: ContentAnalysis,
                                        session_data: Dict[str, Any]) -> Optional[str]:
        """Get or create dynamic collection based on analysis results."""
        try:
            # Check for existing collection
            for collection_id, collection in self.collections.items():
                if collection.name == collection_name:
                    return collection_id
            
            # Create new dynamic collection
            collection_id = str(uuid.uuid4())
            
            # Determine collection type and criteria
            criteria = {'dynamic': True}
            confidence = 0.7
            
            if "Sessions with" in collection_name:
                criteria['type'] = 'speaker_based'
                criteria['speaker'] = collection_name.replace("Sessions with ", "")
                confidence = 0.8
            elif "Discussions" in collection_name:
                criteria['type'] = 'topic_based'
                criteria['topic'] = collection_name.replace(" Discussions", "")
                confidence = 0.7
            elif "Sessions" in collection_name and any(month in collection_name for month in 
                ['January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']):
                criteria['type'] = 'time_based'
                criteria['time_period'] = collection_name
                confidence = 0.9
            
            collection = SmartCollection(
                id=collection_id,
                name=collection_name,
                description=f"Dynamically created collection based on content analysis",
                criteria=criteria,
                content_ids=[],
                auto_update=True,
                confidence=confidence,
                created_at=datetime.now().isoformat()
            )
            
            self.collections[collection_id] = collection
            logger.info(f"Created new dynamic collection: {collection_name}")
            
            return collection_id
            
        except Exception as e:
            logger.error(f"Error creating dynamic collection {collection_name}: {e}")
            return None
    
    def _add_content_to_collection(self, collection_id: str, session_id: str) -> bool:
        """Add content to collection if not already present."""
        try:
            if collection_id in self.collections:
                collection = self.collections[collection_id]
                if session_id not in collection.content_ids:
                    collection.content_ids.append(session_id)
                    logger.debug(f"Added session {session_id} to collection {collection.name}")
                    return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding content to collection: {e}")
            return False
    
    def get_collections_for_content(self, session_id: str) -> List[SmartCollection]:
        """Get all collections containing specific content."""
        try:
            content_collections = []
            
            for collection_id in self.content_index.get(session_id, set()):
                if collection_id in self.collections:
                    content_collections.append(self.collections[collection_id])
            
            return content_collections
            
        except Exception as e:
            logger.error(f"Error getting collections for content {session_id}: {e}")
            return []
    
    def get_all_collections(self) -> List[SmartCollection]:
        """Get all smart collections."""
        return list(self.collections.values())
    
    def get_collection_contents(self, collection_id: str) -> List[str]:
        """Get all content IDs in a collection."""
        if collection_id in self.collections:
            return self.collections[collection_id].content_ids.copy()
        return []
    
    def update_collections(self, force_update: bool = False):
        """Update all auto-updating collections."""
        try:
            updated_count = 0
            
            for collection in self.collections.values():
                if collection.auto_update or force_update:
                    # Re-evaluate collection membership for all content
                    # This would typically query the database for all sessions
                    # and re-run the collection assignment logic
                    updated_count += 1
            
            logger.info(f"Updated {updated_count} smart collections")
            
        except Exception as e:
            logger.error(f"Error updating collections: {e}")
    
    def _evaluate_custom_rule(self, criteria: Dict[str, Any], 
                            analysis: ContentAnalysis, 
                            session_data: Dict[str, Any]) -> bool:
        """Evaluate custom collection rules."""
        # Placeholder for custom rule evaluation
        # Could include complex logic combining multiple criteria
        return False
    
    def remove_content_from_collections(self, session_id: str):
        """Remove content from all collections (e.g., when session deleted)."""
        try:
            for collection in self.collections.values():
                if session_id in collection.content_ids:
                    collection.content_ids.remove(session_id)
            
            # Remove from content index
            if session_id in self.content_index:
                del self.content_index[session_id]
                
            logger.info(f"Removed session {session_id} from all collections")
            
        except Exception as e:
            logger.error(f"Error removing content from collections: {e}")
    
    def get_collection_statistics(self) -> Dict[str, Any]:
        """Get statistics about smart collections."""
        try:
            stats = {
                'total_collections': len(self.collections),
                'auto_updating_collections': sum(1 for c in self.collections.values() if c.auto_update),
                'total_content_items': len(self.content_index),
                'average_items_per_collection': 0,
                'most_popular_collections': [],
                'collection_types': defaultdict(int)
            }
            
            # Calculate average items per collection
            if self.collections:
                total_items = sum(len(c.content_ids) for c in self.collections.values())
                stats['average_items_per_collection'] = total_items / len(self.collections)
            
            # Find most popular collections
            collection_sizes = [(c.name, len(c.content_ids)) for c in self.collections.values()]
            collection_sizes.sort(key=lambda x: x[1], reverse=True)
            stats['most_popular_collections'] = collection_sizes[:5]
            
            # Count collection types
            for collection in self.collections.values():
                criteria_type = collection.criteria.get('rule_type', 
                                                      collection.criteria.get('type', 'unknown'))
                stats['collection_types'][criteria_type] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection statistics: {e}")
            return {}

# Factory function
def create_smart_collections_manager() -> SmartCollectionsManager:
    """Create smart collections manager instance."""
    return SmartCollectionsManager()
```

**Acceptance Criteria**:

- ✅ Automatic collection creation based on configurable rules
- ✅ Dynamic collection generation from content analysis
- ✅ Content assignment to multiple relevant collections
- ✅ Auto-updating collections with new content
- ✅ Collection statistics and management
- ✅ Content removal and cleanup handling
- ✅ Flexible rule system for custom collection criteria

## 📋 Complete Task Breakdown

### Week 1-2: AI Content Analysis
- [ ] Task 1.1: Content Analysis Service (topic extraction, sentiment analysis, classification)
- [ ] Task 1.2: Smart Collections Management (automatic grouping, rule-based organization)
- [ ] Task 1.3: Database schema for tags, collections, and content metadata
- [ ] Task 1.4: Content indexing and search integration

### Week 3-4: Tagging System
- [ ] Task 2.1: Tag Management API (CRUD operations, hierarchy, suggestions)
- [ ] Task 2.2: Auto-tagging Engine (ML-based tag generation)
- [ ] Task 2.3: Tag Analytics and Insights (usage patterns, trending topics)
- [ ] Task 2.4: Bulk Operations (batch tagging, content organization)

### Week 5-6: User Interface
- [ ] Task 3.1: Tag Management Interface (tag editor, hierarchy browser)
- [ ] Task 3.2: Smart Collections Dashboard (collection browser, content organization)
- [ ] Task 3.3: Auto-tagging Controls (approval workflows, confidence settings)
- [ ] Task 3.4: Content Organization Tools (drag-and-drop, bulk operations)

### Week 7: Testing & Optimization
- [ ] Task 4.1: Performance optimization (tagging speed, collection updates)
- [ ] Task 4.2: Testing suite (unit tests, integration tests, performance tests)
- [ ] Task 4.3: Documentation and user guides
- [ ] Task 4.4: Mobile interface optimization

## ✅ Acceptance Criteria

### Functional Requirements
- [ ] ✅ **Automatic Topic Extraction**: AI identifies 5+ relevant topics per session
- [ ] ✅ **Smart Tag Suggestions**: 90%+ accuracy in suggested tags
- [ ] ✅ **Content Classification**: Automatic meeting/interview/presentation detection
- [ ] ✅ **Speaker Recognition**: Consistent speaker identification across sessions
- [ ] ✅ **Sentiment Analysis**: Emotional tone detection and classification
- [ ] ✅ **Smart Collections**: Automatic grouping of related content
- [ ] ✅ **Tag Hierarchy**: Organized tag structures with parent-child relationships
- [ ] ✅ **Bulk Operations**: Efficient batch tagging and organization

### Performance Requirements
- [ ] ✅ **Analysis Speed**: Content analysis completed within 30 seconds per session
- [ ] ✅ **Tag Generation**: Auto-tags generated within 10 seconds
- [ ] ✅ **Collection Updates**: Smart collections updated in real-time
- [ ] ✅ **Search Integration**: Tagged content findable within 1 second
- [ ] ✅ **Scalability**: Support 50,000+ tagged items with sub-second response

### User Experience Requirements
- [ ] ✅ **Intuitive Tagging**: Clear tag suggestion and approval interface
- [ ] ✅ **Visual Organization**: Easy-to-navigate collection and tag browsers
- [ ] ✅ **Tag Discovery**: Users can easily find and apply existing tags
- [ ] ✅ **Bulk Management**: Efficient tools for managing large content libraries
- [ ] ✅ **Mobile Support**: Full tagging functionality on mobile devices

### Technical Requirements
- [ ] ✅ **AI Integration**: Seamless NLP and ML library integration
- [ ] ✅ **Data Consistency**: Reliable tag and collection data management
- [ ] ✅ **Privacy Protection**: Secure handling of content analysis data
- [ ] ✅ **API Integration**: RESTful APIs for all tagging operations
- [ ] ✅ **Monitoring**: Analytics on tagging accuracy and usage patterns

## 🎯 Success Metrics

- **Auto-tagging Adoption**: 80%+ of users rely on automatic tags
- **Tag Accuracy**: 90%+ user approval rate for suggested tags
- **Organization Efficiency**: 60% reduction in time spent organizing content
- **Content Discovery**: 40% increase in content re-use through better organization
- **Collection Usage**: 70%+ of content accessed through smart collections
- **User Satisfaction**: 90%+ satisfaction with content organization features

## 🔄 Future Enhancements

- **Cross-language Tagging**: Multi-language content analysis and tagging
- **Custom ML Models**: User-specific machine learning model training
- **Integration APIs**: External system integration for tag synchronization
- **Advanced Analytics**: Predictive tagging and content recommendations
- **Collaborative Tagging**: Team-based tagging workflows and approval processes

This intelligent content organization system transforms the user experience from manual, time-consuming categorization to an automated, AI-powered system that learns and improves over time.
