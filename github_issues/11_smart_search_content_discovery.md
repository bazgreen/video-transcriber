# Smart Search & Content Discovery

## 🎯 Issue Overview

**Priority**: ⭐⭐⭐ High Priority  
**Epic**: User Experience & Accessibility  
**Estimated Effort**: 6-8 weeks  
**Dependencies**: Database indexing system, AI/NLP libraries, search engine integration

### Problem Statement

Users struggle to find specific content across their growing transcript libraries, leading to:

- **Inefficient manual browsing** through large numbers of transcriptions
- **Limited search capabilities** that only work with exact text matches
- **No cross-session search** to find content across multiple transcripts
- **Missing context awareness** - searches don't understand meaning or intent
- **Poor content organization** making discovery difficult
- **No advanced filtering** by speakers, topics, dates, or content types
- **Lack of search analytics** to understand user behavior and improve results

### Solution Overview

Implement an intelligent search and discovery system that uses AI-powered semantic search, advanced filtering, cross-session capabilities, and smart content organization to help users quickly find exactly what they're looking for across their entire transcript library.

## ✨ Features & Capabilities

### 🔍 Core Search Features

#### Semantic Search Engine

- AI-powered understanding of search intent and context
- Natural language queries with intelligent interpretation
- Concept-based matching beyond exact keyword matches
- Synonym and related term recognition
- Multi-language search support with cross-language capabilities

#### Advanced Search Interface

- Real-time search suggestions and auto-complete
- Advanced filter panels with multiple criteria
- Search result previews with highlighted matches
- Saved searches and search history
- Boolean search operators and advanced syntax

#### Cross-Session Discovery

- Search across entire transcript library simultaneously
- Content similarity detection and clustering
- Related content recommendations
- Topic-based content grouping
- Timeline-based content exploration

#### Smart Filtering & Organization

- Filter by speakers, dates, duration, content type
- Topic-based filtering with AI-generated categories
- Sentiment-based content filtering
- Quality score and confidence level filtering
- Custom tag and metadata filtering

## 🏗️ Technical Implementation

### Phase 1: Search Infrastructure & Indexing (2-3 weeks)

#### Task 1.1: Search Engine & Indexing Service

**File**: `src/services/search_engine.py`

```python
"""
Smart search engine service with semantic search, indexing, and content discovery.
Provides intelligent search capabilities across transcript libraries.
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
import math

try:
    import whoosh
    from whoosh.index import create_index, open_dir
    from whoosh.fields import Schema, TEXT, ID, DATETIME, NUMERIC, KEYWORD
    from whoosh.qparser import QueryParser, MultifieldParser
    from whoosh.query import And, Or, Term, Phrase
    from whoosh.analysis import StemmingAnalyzer
    WHOOSH_AVAILABLE = True
except ImportError:
    WHOOSH_AVAILABLE = False

try:
    import spacy
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Represents a single search result."""
    session_id: str
    title: str
    content: str
    highlighted_content: str
    relevance_score: float
    timestamp: str
    duration: int
    speakers: List[str]
    topics: List[str]
    segment_matches: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class SearchSuggestion:
    """Represents a search suggestion."""
    text: str
    type: str  # 'query', 'topic', 'speaker', 'filter'
    confidence: float
    result_count: int

@dataclass
class SearchFilters:
    """Represents search filtering criteria."""
    date_range: Optional[Tuple[str, str]] = None
    speakers: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    duration_range: Optional[Tuple[int, int]] = None
    content_types: Optional[List[str]] = None
    quality_threshold: Optional[float] = None
    tags: Optional[List[str]] = None

class ContentIndexer:
    """Handles indexing of transcript content for search."""
    
    def __init__(self, index_dir: str):
        """Initialize content indexer with index directory."""
        self.index_dir = index_dir
        self.schema = self._create_schema()
        self.index = None
        self._initialize_index()
        
    def _create_schema(self) -> 'Schema':
        """Create Whoosh schema for transcript indexing."""
        if not WHOOSH_AVAILABLE:
            return None
            
        return Schema(
            session_id=ID(stored=True, unique=True),
            title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            content=TEXT(stored=True, analyzer=StemmingAnalyzer()),
            speakers=KEYWORD(stored=True, commas=True),
            topics=KEYWORD(stored=True, commas=True),
            tags=KEYWORD(stored=True, commas=True),
            timestamp=DATETIME(stored=True),
            duration=NUMERIC(stored=True),
            quality_score=NUMERIC(stored=True),
            metadata=TEXT(stored=True)
        )
    
    def _initialize_index(self):
        """Initialize or open existing search index."""
        if not WHOOSH_AVAILABLE:
            logger.warning("Whoosh not available, search indexing disabled")
            return
            
        try:
            import os
            if not os.path.exists(self.index_dir):
                os.makedirs(self.index_dir)
                self.index = create_index(self.schema, self.index_dir)
            else:
                self.index = open_dir(self.index_dir)
                
            logger.info(f"Search index initialized at {self.index_dir}")
            
        except Exception as e:
            logger.error(f"Error initializing search index: {e}")
            self.index = None
    
    def index_session(self, session_data: Dict[str, Any]) -> bool:
        """
        Index a transcription session for search.
        
        Args:
            session_data: Session data with transcript and metadata
            
        Returns:
            Success boolean
        """
        if not self.index:
            return False
            
        try:
            writer = self.index.writer()
            
            # Extract searchable content
            content = session_data.get('transcript', '')
            segments = session_data.get('segments', [])
            
            # Process segments for better indexing
            segment_texts = []
            speakers = set()
            
            for segment in segments:
                segment_text = segment.get('text', '')
                segment_texts.append(segment_text)
                
                if 'speaker' in segment:
                    speakers.add(segment['speaker'])
            
            # Extract topics and metadata
            analysis = session_data.get('analysis', {})
            topics = analysis.get('topics', [])
            if isinstance(topics, list) and topics:
                topic_names = [topic.get('name', '') for topic in topics if isinstance(topic, dict)]
            else:
                topic_names = []
            
            # Create document
            writer.add_document(
                session_id=session_data['id'],
                title=session_data.get('title', f"Session {session_data['id']}"),
                content=content,
                speakers=','.join(speakers),
                topics=','.join(topic_names),
                tags=','.join(session_data.get('tags', [])),
                timestamp=datetime.fromisoformat(session_data.get('created_at', datetime.now().isoformat())),
                duration=session_data.get('duration', 0),
                quality_score=session_data.get('quality_score', 0.8),
                metadata=json.dumps(session_data.get('metadata', {}))
            )
            
            writer.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error indexing session {session_data.get('id', 'unknown')}: {e}")
            return False
    
    def remove_session(self, session_id: str) -> bool:
        """Remove session from search index."""
        if not self.index:
            return False
            
        try:
            writer = self.index.writer()
            writer.delete_by_term('session_id', session_id)
            writer.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error removing session {session_id} from index: {e}")
            return False
    
    def rebuild_index(self, sessions_data: List[Dict[str, Any]]) -> bool:
        """Rebuild entire search index from session data."""
        if not self.index:
            return False
            
        try:
            writer = self.index.writer()
            writer.clear()
            
            for session_data in sessions_data:
                self.index_session(session_data)
                
            logger.info(f"Rebuilt search index with {len(sessions_data)} sessions")
            return True
            
        except Exception as e:
            logger.error(f"Error rebuilding search index: {e}")
            return False

class SemanticSearchEngine:
    """Handles AI-powered semantic search capabilities."""
    
    def __init__(self):
        """Initialize semantic search engine."""
        self.sentence_transformer = None
        self.nlp_model = None
        self.session_embeddings = {}
        self.tfidf_vectorizer = None
        
        if SEMANTIC_SEARCH_AVAILABLE:
            try:
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                self.nlp_model = spacy.load('en_core_web_sm')
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
                logger.info("Semantic search engine initialized")
            except Exception as e:
                logger.warning(f"Could not initialize semantic search: {e}")
                SEMANTIC_SEARCH_AVAILABLE = False
    
    def generate_embeddings(self, sessions_data: List[Dict[str, Any]]):
        """Generate embeddings for all sessions."""
        if not SEMANTIC_SEARCH_AVAILABLE or not self.sentence_transformer:
            return
            
        try:
            texts = []
            session_ids = []
            
            for session in sessions_data:
                content = session.get('transcript', '')
                if content:
                    texts.append(content)
                    session_ids.append(session['id'])
            
            if texts:
                embeddings = self.sentence_transformer.encode(texts)
                self.session_embeddings = dict(zip(session_ids, embeddings))
                
                # Train TF-IDF vectorizer
                self.tfidf_vectorizer.fit(texts)
                
                logger.info(f"Generated embeddings for {len(session_ids)} sessions")
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
    
    def semantic_search(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Perform semantic search using sentence embeddings.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of (session_id, similarity_score) tuples
        """
        if not SEMANTIC_SEARCH_AVAILABLE or not self.sentence_transformer or not self.session_embeddings:
            return []
            
        try:
            # Generate query embedding
            query_embedding = self.sentence_transformer.encode([query])
            
            # Calculate similarities
            similarities = []
            for session_id, session_embedding in self.session_embeddings.items():
                similarity = cosine_similarity(query_embedding, [session_embedding])[0][0]
                similarities.append((session_id, float(similarity)))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def extract_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Extract intent and entities from search query.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary with intent and extracted entities
        """
        if not SEMANTIC_SEARCH_AVAILABLE or not self.nlp_model:
            return {'intent': 'general_search', 'entities': {}}
            
        try:
            doc = self.nlp_model(query)
            
            entities = {
                'persons': [ent.text for ent in doc.ents if ent.label_ == 'PERSON'],
                'organizations': [ent.text for ent in doc.ents if ent.label_ == 'ORG'],
                'dates': [ent.text for ent in doc.ents if ent.label_ == 'DATE'],
                'topics': [ent.text for ent in doc.ents if ent.label_ in ['PRODUCT', 'EVENT', 'WORK_OF_ART']]
            }
            
            # Determine intent based on query patterns
            intent = 'general_search'
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['who said', 'who mentioned', 'speaker']):
                intent = 'speaker_search'
            elif any(word in query_lower for word in ['when', 'date', 'time']):
                intent = 'temporal_search'
            elif any(word in query_lower for word in ['topic', 'about', 'discuss']):
                intent = 'topic_search'
            elif any(word in query_lower for word in ['similar', 'like', 'related']):
                intent = 'similarity_search'
            
            return {
                'intent': intent,
                'entities': entities,
                'keywords': [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
            }
            
        except Exception as e:
            logger.error(f"Error extracting query intent: {e}")
            return {'intent': 'general_search', 'entities': {}}

class SmartSearchService:
    """Main service for intelligent search and content discovery."""
    
    def __init__(self, index_dir: str):
        """Initialize smart search service."""
        self.indexer = ContentIndexer(index_dir)
        self.semantic_engine = SemanticSearchEngine()
        self.search_analytics = defaultdict(int)
        self.popular_queries = defaultdict(int)
        
    def search(self, query: str, filters: SearchFilters = None, 
              user_id: str = None, limit: int = 50) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """
        Perform comprehensive search across transcript library.
        
        Args:
            query: Search query
            filters: Optional search filters
            user_id: User performing search (for analytics)
            limit: Maximum results to return
            
        Returns:
            Tuple of (search results, metadata)
        """
        try:
            # Track search analytics
            if user_id:
                self.search_analytics[f"user_{user_id}"] += 1
                self.popular_queries[query.lower()] += 1
            
            # Extract query intent and entities
            query_intent = self.semantic_engine.extract_query_intent(query)
            
            # Perform multiple search strategies
            keyword_results = self._keyword_search(query, filters, limit)
            semantic_results = self._semantic_search(query, filters, limit)
            
            # Combine and rank results
            combined_results = self._combine_search_results(
                keyword_results, semantic_results, query_intent
            )
            
            # Generate search metadata
            metadata = {
                'query_intent': query_intent,
                'total_results': len(combined_results),
                'search_time': datetime.now().isoformat(),
                'filters_applied': filters.__dict__ if filters else {},
                'suggestions': self._generate_suggestions(query, query_intent)
            }
            
            return combined_results[:limit], metadata
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return [], {'error': str(e)}
    
    def _keyword_search(self, query: str, filters: SearchFilters, 
                       limit: int) -> List[SearchResult]:
        """Perform keyword-based search using Whoosh."""
        if not self.indexer.index:
            return []
            
        try:
            searcher = self.indexer.index.searcher()
            
            # Create query parser for multiple fields
            parser = MultifieldParser(
                ['title', 'content', 'speakers', 'topics'],
                self.indexer.schema
            )
            
            parsed_query = parser.parse(query)
            
            # Apply filters
            if filters:
                filter_query = self._build_filter_query(filters)
                if filter_query:
                    parsed_query = And([parsed_query, filter_query])
            
            # Execute search
            results = searcher.search(parsed_query, limit=limit)
            
            search_results = []
            for result in results:
                # Get highlighted content
                highlighted = result.highlights('content', top=3)
                
                search_results.append(SearchResult(
                    session_id=result['session_id'],
                    title=result['title'],
                    content=result['content'][:500] + '...' if len(result['content']) > 500 else result['content'],
                    highlighted_content=highlighted,
                    relevance_score=result.score,
                    timestamp=result['timestamp'].isoformat(),
                    duration=result['duration'],
                    speakers=result['speakers'].split(',') if result['speakers'] else [],
                    topics=result['topics'].split(',') if result['topics'] else [],
                    segment_matches=[],  # Would be populated with detailed segment matches
                    metadata=json.loads(result['metadata']) if result['metadata'] else {}
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []
    
    def _semantic_search(self, query: str, filters: SearchFilters, 
                        limit: int) -> List[SearchResult]:
        """Perform semantic search using embeddings."""
        if not SEMANTIC_SEARCH_AVAILABLE:
            return []
            
        try:
            # Get semantic similarities
            similarities = self.semantic_engine.semantic_search(query, limit * 2)
            
            search_results = []
            for session_id, similarity_score in similarities:
                # Load session data (would be from database/cache)
                session_data = self._load_session_data(session_id)
                if session_data:
                    search_results.append(SearchResult(
                        session_id=session_id,
                        title=session_data.get('title', f"Session {session_id}"),
                        content=session_data.get('transcript', '')[:500] + '...',
                        highlighted_content='',  # Would implement semantic highlighting
                        relevance_score=similarity_score,
                        timestamp=session_data.get('created_at', ''),
                        duration=session_data.get('duration', 0),
                        speakers=session_data.get('speakers', []),
                        topics=session_data.get('topics', []),
                        segment_matches=[],
                        metadata=session_data.get('metadata', {})
                    ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _combine_search_results(self, keyword_results: List[SearchResult], 
                               semantic_results: List[SearchResult],
                               query_intent: Dict[str, Any]) -> List[SearchResult]:
        """Combine and rank results from different search strategies."""
        try:
            # Create result map to avoid duplicates
            results_map = {}
            
            # Add keyword results with weight
            for result in keyword_results:
                if result.session_id not in results_map:
                    result.relevance_score *= 0.7  # Weight keyword results
                    results_map[result.session_id] = result
                else:
                    # Boost score if found in both
                    results_map[result.session_id].relevance_score += result.relevance_score * 0.3
            
            # Add semantic results with weight
            for result in semantic_results:
                if result.session_id not in results_map:
                    result.relevance_score *= 0.6  # Weight semantic results
                    results_map[result.session_id] = result
                else:
                    # Boost score if found in both
                    results_map[result.session_id].relevance_score += result.relevance_score * 0.4
            
            # Sort by final relevance score
            combined_results = list(results_map.values())
            combined_results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error combining search results: {e}")
            return keyword_results + semantic_results
    
    def _generate_suggestions(self, query: str, query_intent: Dict[str, Any]) -> List[SearchSuggestion]:
        """Generate search suggestions based on query and intent."""
        suggestions = []
        
        try:
            # Popular query suggestions
            similar_queries = [q for q in self.popular_queries.keys() 
                             if q != query.lower() and query.lower() in q]
            
            for similar_query in similar_queries[:3]:
                suggestions.append(SearchSuggestion(
                    text=similar_query.title(),
                    type='query',
                    confidence=0.8,
                    result_count=self.popular_queries[similar_query]
                ))
            
            # Entity-based suggestions
            entities = query_intent.get('entities', {})
            for entity_type, entity_list in entities.items():
                for entity in entity_list[:2]:
                    suggestions.append(SearchSuggestion(
                        text=f"More about {entity}",
                        type=entity_type,
                        confidence=0.7,
                        result_count=0
                    ))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    def get_search_analytics(self, user_id: str = None) -> Dict[str, Any]:
        """Get search analytics and insights."""
        try:
            analytics = {
                'total_searches': sum(self.search_analytics.values()),
                'popular_queries': dict(sorted(
                    self.popular_queries.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:10]),
                'search_trends': {},  # Would implement trend analysis
                'user_search_count': self.search_analytics.get(f"user_{user_id}", 0) if user_id else 0
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            return {}
    
    # Helper methods
    def _build_filter_query(self, filters: SearchFilters):
        """Build Whoosh query from filters."""
        # Implementation would build complex filter queries
        return None
    
    def _load_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from storage."""
        # Implementation would load from database/cache
        return {}

# Factory function
def create_search_service(index_dir: str = 'data/search_index') -> SmartSearchService:
    """Create smart search service with specified index directory."""
    return SmartSearchService(index_dir)
```

**Acceptance Criteria**:

- ✅ Full-text search with Whoosh integration
- ✅ Semantic search using sentence transformers
- ✅ Advanced filtering and query processing
- ✅ Search result ranking and combination
- ✅ Query intent recognition and entity extraction
- ✅ Search analytics and popular query tracking
- ✅ Graceful degradation when AI libraries unavailable

#### Task 1.2: Search API Endpoints
**File**: `src/routes/search_routes.py`

```python
"""
API routes for smart search and content discovery functionality.
Provides endpoints for searching, filtering, suggestions, and analytics.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

from src.services.search_engine import create_search_service, SearchFilters

logger = logging.getLogger(__name__)

# Create blueprint for search routes
search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('/query', methods=['POST'])
@login_required
def perform_search() -> Tuple[Dict[str, Any], int]:
    """
    Perform comprehensive search across transcript library.
    
    Body Parameters:
    - query: Search query string
    - filters: Optional search filters
    - limit: Maximum results (default 50)
    - search_type: 'all', 'keyword', 'semantic'
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Search query required'}), 400
        
        query = data['query'].strip()
        if not query:
            return jsonify({'error': 'Empty search query'}), 400
        
        # Parse search filters
        filters = None
        if 'filters' in data:
            filter_data = data['filters']
            filters = SearchFilters(
                date_range=tuple(filter_data['date_range']) if filter_data.get('date_range') else None,
                speakers=filter_data.get('speakers'),
                topics=filter_data.get('topics'),
                duration_range=tuple(filter_data['duration_range']) if filter_data.get('duration_range') else None,
                content_types=filter_data.get('content_types'),
                quality_threshold=filter_data.get('quality_threshold'),
                tags=filter_data.get('tags')
            )
        
        # Create search service
        search_service = create_search_service()
        
        # Perform search
        results, metadata = search_service.search(
            query=query,
            filters=filters,
            user_id=current_user.id,
            limit=data.get('limit', 50)
        )
        
        # Convert results to JSON-serializable format
        result_data = []
        for result in results:
            result_data.append({
                'session_id': result.session_id,
                'title': result.title,
                'content': result.content,
                'highlighted_content': result.highlighted_content,
                'relevance_score': result.relevance_score,
                'timestamp': result.timestamp,
                'duration': result.duration,
                'speakers': result.speakers,
                'topics': result.topics,
                'segment_matches': result.segment_matches,
                'metadata': result.metadata
            })
        
        return jsonify({
            'query': query,
            'results': result_data,
            'metadata': metadata,
            'total_results': len(result_data),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        return jsonify({'error': 'Search failed', 'details': str(e)}), 500

@search_bp.route('/suggestions', methods=['GET'])
@login_required
def get_search_suggestions() -> Tuple[Dict[str, Any], int]:
    """
    Get search suggestions based on partial query.
    
    Query Parameters:
    - q: Partial search query
    - limit: Maximum suggestions (default 10)
    """
    try:
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if not query:
            return jsonify({'suggestions': []}), 200
        
        search_service = create_search_service()
        
        # Get query intent for better suggestions
        query_intent = search_service.semantic_engine.extract_query_intent(query)
        suggestions = search_service._generate_suggestions(query, query_intent)
        
        # Add autocomplete suggestions
        autocomplete_suggestions = []
        
        # Popular queries that start with the input
        for popular_query, count in search_service.popular_queries.items():
            if popular_query.startswith(query.lower()) and popular_query != query.lower():
                autocomplete_suggestions.append({
                    'text': popular_query.title(),
                    'type': 'autocomplete',
                    'confidence': min(0.9, count / 100),
                    'result_count': count
                })
        
        # Combine suggestions
        all_suggestions = [s.__dict__ for s in suggestions] + autocomplete_suggestions
        all_suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return jsonify({
            'query': query,
            'suggestions': all_suggestions[:limit],
            'total_count': len(all_suggestions),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting search suggestions: {e}")
        return jsonify({'error': 'Failed to get suggestions', 'details': str(e)}), 500

@search_bp.route('/filters/options', methods=['GET'])
@login_required
def get_filter_options() -> Tuple[Dict[str, Any], int]:
    """
    Get available filter options for search interface.
    
    Returns available speakers, topics, content types, etc.
    """
    try:
        # This would query the database for available filter options
        # For now, return mock data structure
        
        filter_options = {
            'speakers': [],  # Would populate from database
            'topics': [],   # Would populate from AI analysis
            'content_types': [
                'meeting', 'interview', 'lecture', 'presentation', 
                'conversation', 'phone_call', 'other'
            ],
            'date_ranges': [
                {'label': 'Last 7 days', 'value': 7},
                {'label': 'Last 30 days', 'value': 30},
                {'label': 'Last 90 days', 'value': 90},
                {'label': 'Last year', 'value': 365},
                {'label': 'Custom range', 'value': 'custom'}
            ],
            'duration_ranges': [
                {'label': 'Short (< 15 min)', 'min': 0, 'max': 900},
                {'label': 'Medium (15-60 min)', 'min': 900, 'max': 3600},
                {'label': 'Long (> 1 hour)', 'min': 3600, 'max': 999999}
            ],
            'quality_thresholds': [
                {'label': 'High quality (90%+)', 'value': 0.9},
                {'label': 'Good quality (80%+)', 'value': 0.8},
                {'label': 'Fair quality (70%+)', 'value': 0.7},
                {'label': 'Any quality', 'value': 0.0}
            ]
        }
        
        return jsonify({
            'filter_options': filter_options,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting filter options: {e}")
        return jsonify({'error': 'Failed to get filter options', 'details': str(e)}), 500

@search_bp.route('/similar/<session_id>', methods=['GET'])
@login_required
def find_similar_content(session_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Find content similar to a specific session.
    
    Query Parameters:
    - limit: Maximum results (default 10)
    """
    try:
        limit = int(request.args.get('limit', 10))
        
        search_service = create_search_service()
        
        # Load session data
        session_data = load_session_data(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        # Use transcript content for similarity search
        content = session_data.get('transcript', '')
        if not content:
            return jsonify({'error': 'No content to compare'}), 400
        
        # Perform semantic similarity search
        similar_sessions = search_service.semantic_engine.semantic_search(
            content[:1000],  # Use first 1000 chars for similarity
            top_k=limit + 1  # +1 to exclude the original session
        )
        
        # Filter out the original session and format results
        similar_results = []
        for sim_session_id, similarity_score in similar_sessions:
            if sim_session_id != session_id:
                sim_data = load_session_data(sim_session_id)
                if sim_data:
                    similar_results.append({
                        'session_id': sim_session_id,
                        'title': sim_data.get('title', f"Session {sim_session_id}"),
                        'similarity_score': similarity_score,
                        'content_preview': sim_data.get('transcript', '')[:200] + '...',
                        'timestamp': sim_data.get('created_at', ''),
                        'duration': sim_data.get('duration', 0),
                        'speakers': sim_data.get('speakers', []),
                        'topics': sim_data.get('topics', [])
                    })
        
        return jsonify({
            'session_id': session_id,
            'similar_content': similar_results[:limit],
            'total_found': len(similar_results),
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error finding similar content: {e}")
        return jsonify({'error': 'Similar content search failed', 'details': str(e)}), 500

@search_bp.route('/analytics', methods=['GET'])
@login_required
def get_search_analytics() -> Tuple[Dict[str, Any], int]:
    """
    Get search analytics and insights.
    
    Query Parameters:
    - timeframe: 'day', 'week', 'month' (default 'week')
    """
    try:
        timeframe = request.args.get('timeframe', 'week')
        
        search_service = create_search_service()
        analytics = search_service.get_search_analytics(current_user.id)
        
        # Add user-specific analytics
        user_analytics = {
            'user_search_count': analytics.get('user_search_count', 0),
            'total_searches': analytics.get('total_searches', 0),
            'popular_queries': analytics.get('popular_queries', {}),
            'search_trends': analytics.get('search_trends', {}),
            'timeframe': timeframe
        }
        
        return jsonify({
            'analytics': user_analytics,
            'success': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting search analytics: {e}")
        return jsonify({'error': 'Analytics retrieval failed', 'details': str(e)}), 500

@search_bp.route('/saved-searches', methods=['GET', 'POST', 'DELETE'])
@login_required
def handle_saved_searches() -> Tuple[Dict[str, Any], int]:
    """Handle saved search management."""
    try:
        if request.method == 'GET':
            # Get user's saved searches
            saved_searches = get_user_saved_searches(current_user.id)
            
            return jsonify({
                'saved_searches': saved_searches,
                'total_count': len(saved_searches),
                'success': True
            }), 200
            
        elif request.method == 'POST':
            # Save a search
            data = request.get_json()
            if not data or 'query' not in data or 'name' not in data:
                return jsonify({'error': 'Query and name required'}), 400
            
            saved_search = save_user_search(
                user_id=current_user.id,
                name=data['name'],
                query=data['query'],
                filters=data.get('filters'),
                metadata=data.get('metadata', {})
            )
            
            return jsonify({
                'saved_search': saved_search,
                'success': True
            }), 201
            
        elif request.method == 'DELETE':
            # Delete saved search
            data = request.get_json()
            if not data or 'search_id' not in data:
                return jsonify({'error': 'Search ID required'}), 400
            
            success = delete_user_saved_search(current_user.id, data['search_id'])
            
            return jsonify({'success': success}), 200 if success else 404
            
    except Exception as e:
        logger.error(f"Error handling saved searches: {e}")
        return jsonify({'error': 'Saved search operation failed', 'details': str(e)}), 500

# Helper functions (would be implemented with database integration)
def load_session_data(session_id: str) -> Dict[str, Any]:
    """Load session data from database."""
    # Implementation would load from database
    return {}

def get_user_saved_searches(user_id: str) -> List[Dict[str, Any]]:
    """Get user's saved searches."""
    # Implementation would load from database
    return []

def save_user_search(user_id: str, name: str, query: str, 
                    filters: Dict = None, metadata: Dict = None) -> Dict[str, Any]:
    """Save a search for a user."""
    # Implementation would save to database
    return {}

def delete_user_saved_search(user_id: str, search_id: str) -> bool:
    """Delete a user's saved search."""
    # Implementation would delete from database
    return True
```

**Acceptance Criteria**:
- ✅ Comprehensive search API with multiple search types
- ✅ Real-time search suggestions and autocomplete
- ✅ Advanced filtering with dynamic filter options
- ✅ Content similarity detection and recommendations
- ✅ Search analytics and user behavior tracking
- ✅ Saved searches management
- ✅ Proper error handling and user authentication

## 📋 Complete Task Breakdown

### Week 1-2: Search Infrastructure

- [ ] Task 1.1: Search Engine & Indexing Service (Whoosh integration, semantic search)
- [ ] Task 1.2: Search API Endpoints (comprehensive search API)
- [ ] Task 1.3: Database schema for search analytics and saved searches
- [ ] Task 1.4: Search index initialization and management

### Week 3-4: Advanced Search Features
- [ ] Task 2.1: Semantic Search Implementation (sentence transformers, embeddings)
- [ ] Task 2.2: Query Intent Recognition (NLP for understanding search intent)
- [ ] Task 2.3: Advanced Filtering System (multi-criteria filtering)
- [ ] Task 2.4: Content Similarity Engine (find related content)

### Week 5-6: User Interface & Experience
- [ ] Task 3.1: Search Interface Component (React/Vue search UI)
- [ ] Task 3.2: Filter Panel Implementation (advanced filtering UI)
- [ ] Task 3.3: Search Results Display (rich result presentation)
- [ ] Task 3.4: Search Analytics Dashboard (usage insights)

### Week 7-8: Performance & Polish
- [ ] Task 4.1: Search Performance Optimization (indexing, caching)
- [ ] Task 4.2: Real-time Search Suggestions (autocomplete, smart suggestions)
- [ ] Task 4.3: Mobile Search Experience (responsive search UI)
- [ ] Task 4.4: Testing and Documentation (comprehensive testing suite)

## ✅ Acceptance Criteria

### Functional Requirements
- [ ] ✅ **Semantic Search**: AI-powered understanding of search intent and context
- [ ] ✅ **Cross-Session Search**: Find content across entire transcript library
- [ ] ✅ **Advanced Filtering**: Multi-criteria filtering by speakers, topics, dates, quality
- [ ] ✅ **Real-time Suggestions**: Intelligent autocomplete and search suggestions
- [ ] ✅ **Content Discovery**: Similarity detection and related content recommendations
- [ ] ✅ **Saved Searches**: User ability to save and manage frequent searches
- [ ] ✅ **Search Analytics**: Usage tracking and search behavior insights
- [ ] ✅ **Fuzzy Matching**: Find content despite spelling errors or partial matches

### Performance Requirements
- [ ] ✅ **Search Speed**: Results returned within 500ms for keyword search
- [ ] ✅ **Semantic Search Speed**: Results within 2 seconds for AI-powered search
- [ ] ✅ **Index Size**: Efficient indexing supporting 100,000+ transcripts
- [ ] ✅ **Suggestion Speed**: Autocomplete suggestions within 100ms
- [ ] ✅ **Concurrent Searches**: Support 100+ simultaneous search requests

### User Experience Requirements
- [ ] ✅ **Intuitive Interface**: Clear search interface with progressive disclosure
- [ ] ✅ **Result Relevance**: 90%+ user satisfaction with search result quality
- [ ] ✅ **Search Guidance**: Helpful suggestions and search tips
- [ ] ✅ **Mobile Optimization**: Full functionality on mobile devices
- [ ] ✅ **Accessibility**: WCAG 2.1 AA compliance for search interface

### Technical Requirements
- [ ] ✅ **Scalable Architecture**: Horizontally scalable search infrastructure
- [ ] ✅ **Index Management**: Automatic index updates and maintenance
- [ ] ✅ **Data Privacy**: Search queries and results properly secured
- [ ] ✅ **Integration**: Seamless integration with existing transcription workflow
- [ ] ✅ **Monitoring**: Search performance and usage monitoring

## 🎯 Success Metrics

- **Search Usage**: 80%+ of users perform searches within first week
- **Search Success Rate**: 85%+ of searches result in user action (click, save, share)
- **Discovery Rate**: 40%+ of content accessed through search vs. browsing
- **Time to Find**: 60% reduction in time to find specific content
- **User Satisfaction**: 90%+ satisfaction rating for search functionality
- **Search Abandonment**: <10% search abandonment rate

## 🔄 Future Enhancements

- **Voice Search**: Voice-to-text search input capability
- **Visual Search**: Search based on uploaded images or screenshots
- **AI Summary**: Auto-generated summaries of search results
- **Collaborative Search**: Team-based search with shared results
- **API Integration**: External system integration for search functionality

This comprehensive search system transforms content discovery from a manual browsing task into an intelligent, AI-powered experience that helps users find exactly what they need across their entire transcript library.
