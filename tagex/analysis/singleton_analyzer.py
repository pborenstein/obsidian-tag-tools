#!/usr/bin/env python3
"""
Singleton tag analyzer - suggests merging singleton tags into frequent tags.

This analyzer specifically targets tags that appear only once (singletons) and
suggests merging them into existing frequent tags based on multiple similarity metrics:

1. STRING SIMILARITY: Catches typos and minor variations (e.g., "machne-learning" → "machine-learning")
2. SEMANTIC SIMILARITY: Uses sentence embeddings to find true synonyms (e.g., "ai" → "artificial-intelligence")
3. CHARACTER N-GRAM SIMILARITY: TF-IDF based matching for morphological relationships
4. CO-OCCURRENCE: Suggests merges when singleton appears in files that predominantly use a frequent tag

The analyzer only suggests one-directional merges: singleton → frequent tag (count >= threshold).
This ensures we're consolidating rare tags into established taxonomy, not the reverse.
"""

from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher
from collections import defaultdict

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SingletonAnalyzer:
    """Analyzes singleton tags and suggests merges into frequent tags."""

    def __init__(
        self,
        tag_stats: Dict[str, Dict[str, Any]],
        frequent_threshold: int = 5,
        string_similarity_threshold: float = 0.85,
        semantic_similarity_threshold: float = 0.70,
        tfidf_similarity_threshold: float = 0.60,
        co_occurrence_threshold: float = 0.70
    ):
        """
        Initialize singleton analyzer.

        Args:
            tag_stats: Dictionary mapping tag names to their statistics (count, files)
            frequent_threshold: Minimum usage count to consider a tag "frequent"
            string_similarity_threshold: Minimum string similarity ratio (0-1)
            semantic_similarity_threshold: Minimum semantic similarity for embeddings (0-1)
            tfidf_similarity_threshold: Minimum TF-IDF similarity (0-1)
            co_occurrence_threshold: Minimum co-occurrence ratio (0-1)
        """
        self.tag_stats = tag_stats
        self.frequent_threshold = frequent_threshold
        self.string_similarity_threshold = string_similarity_threshold
        self.semantic_similarity_threshold = semantic_similarity_threshold
        self.tfidf_similarity_threshold = tfidf_similarity_threshold
        self.co_occurrence_threshold = co_occurrence_threshold

        # Separate singletons from frequent tags
        self.singletons = {tag: stats for tag, stats in tag_stats.items() if stats['count'] == 1}
        self.frequent_tags = {tag: stats for tag, stats in tag_stats.items() if stats['count'] >= frequent_threshold}

        self.semantic_model = None

    def analyze(self, use_semantic: bool = True) -> List[Dict[str, Any]]:
        """
        Analyze singletons and generate merge suggestions.

        Args:
            use_semantic: Whether to use semantic similarity (requires sentence-transformers)

        Returns:
            List of merge suggestions with metadata
        """
        if not self.singletons:
            print("  No singleton tags found")
            return []

        if not self.frequent_tags:
            print("  No frequent tags found (threshold >= {self.frequent_threshold})")
            return []

        print(f"  Found {len(self.singletons)} singleton tags")
        print(f"  Found {len(self.frequent_tags)} frequent tags (>= {self.frequent_threshold} uses)")

        suggestions = []

        # Load semantic model if needed
        if use_semantic and TRANSFORMERS_AVAILABLE:
            try:
                print("  Loading semantic model...")
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                print(f"  Warning: Could not load semantic model: {e}")
                self.semantic_model = None

        # Process each singleton
        for singleton_tag, singleton_stats in self.singletons.items():
            # Find all potential matches
            matches = self._find_matches(singleton_tag, singleton_stats)

            # Keep only the best match
            if matches:
                best_match = max(matches, key=lambda x: x['confidence'])
                suggestions.append(best_match)

        # Sort by confidence descending
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)

        return suggestions

    def _find_matches(self, singleton_tag: str, singleton_stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find potential merge targets for a singleton tag.

        Args:
            singleton_tag: The singleton tag name
            singleton_stats: Statistics for the singleton tag

        Returns:
            List of potential matches with confidence scores
        """
        matches = []

        for frequent_tag, frequent_stats in self.frequent_tags.items():
            # Skip if same tag
            if singleton_tag == frequent_tag:
                continue

            # Calculate various similarity metrics
            string_sim = self._string_similarity(singleton_tag, frequent_tag)
            co_occurrence = self._co_occurrence_ratio(singleton_stats, frequent_stats)

            # String similarity (typos, abbreviations)
            if string_sim >= self.string_similarity_threshold:
                matches.append({
                    'singleton': singleton_tag,
                    'target': frequent_tag,
                    'method': 'string_similarity',
                    'confidence': string_sim,
                    'reason': f"String similarity: {string_sim:.3f}",
                    'target_usage': frequent_stats['count'],
                    'metadata': {
                        'string_similarity': round(string_sim, 3)
                    }
                })

            # Co-occurrence (appears in same file with target tag)
            elif co_occurrence >= self.co_occurrence_threshold:
                matches.append({
                    'singleton': singleton_tag,
                    'target': frequent_tag,
                    'method': 'co_occurrence',
                    'confidence': co_occurrence,
                    'reason': f"Co-occurrence: {co_occurrence:.3f}",
                    'target_usage': frequent_stats['count'],
                    'metadata': {
                        'co_occurrence_ratio': round(co_occurrence, 3)
                    }
                })

        # TF-IDF similarity (morphological relationships)
        if SKLEARN_AVAILABLE:
            tfidf_matches = self._tfidf_similarity(singleton_tag)
            matches.extend(tfidf_matches)

        # Semantic similarity (true synonyms)
        if self.semantic_model is not None:
            semantic_matches = self._semantic_similarity(singleton_tag)
            matches.extend(semantic_matches)

        return matches

    def _string_similarity(self, tag1: str, tag2: str) -> float:
        """Calculate string similarity using SequenceMatcher."""
        return SequenceMatcher(None, tag1.lower(), tag2.lower()).ratio()

    def _co_occurrence_ratio(
        self,
        singleton_stats: Dict[str, Any],
        frequent_stats: Dict[str, Any]
    ) -> float:
        """
        Calculate how often singleton appears with the frequent tag.

        Since singleton appears in only 1 file, we check if that file
        also contains the frequent tag.
        """
        singleton_files = singleton_stats.get('files', set())
        frequent_files = frequent_stats.get('files', set())

        if not singleton_files or not frequent_files:
            return 0.0

        # Check if the singleton's file contains the frequent tag
        intersection = singleton_files.intersection(frequent_files)

        # Return 1.0 if they co-occur, 0.0 otherwise
        return 1.0 if intersection else 0.0

    def _tfidf_similarity(self, singleton_tag: str) -> List[Dict[str, Any]]:
        """Find similar tags using TF-IDF character n-grams."""
        if not SKLEARN_AVAILABLE:
            return []

        try:
            # Create corpus with singleton and all frequent tags
            tags = [singleton_tag] + list(self.frequent_tags.keys())

            # Vectorize using character n-grams
            vectorizer = TfidfVectorizer(
                analyzer='char_wb',
                ngram_range=(2, 4),
                lowercase=True,
                max_features=1000
            )

            tfidf_matrix = vectorizer.fit_transform(tags)

            # Calculate similarity between singleton (index 0) and all frequent tags
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

            # Find matches above threshold
            matches = []
            for i, sim_score in enumerate(similarities):
                if sim_score >= self.tfidf_similarity_threshold:
                    frequent_tag = list(self.frequent_tags.keys())[i]
                    matches.append({
                        'singleton': singleton_tag,
                        'target': frequent_tag,
                        'method': 'tfidf',
                        'confidence': sim_score,
                        'reason': f"Character similarity: {sim_score:.3f}",
                        'target_usage': self.frequent_tags[frequent_tag]['count'],
                        'metadata': {
                            'tfidf_similarity': round(sim_score, 3)
                        }
                    })

            return matches

        except Exception as e:
            # Silently fail - this is an optional enhancement
            return []

    def _semantic_similarity(self, singleton_tag: str) -> List[Dict[str, Any]]:
        """Find semantically similar tags using sentence embeddings."""
        if self.semantic_model is None:
            return []

        try:
            # Encode singleton and all frequent tags
            singleton_embedding = self.semantic_model.encode([singleton_tag])
            frequent_tag_list = list(self.frequent_tags.keys())
            frequent_embeddings = self.semantic_model.encode(frequent_tag_list)

            # Calculate cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            similarities = cosine_similarity(singleton_embedding, frequent_embeddings).flatten()

            # Find matches above threshold
            matches = []
            for i, sim_score in enumerate(similarities):
                if sim_score >= self.semantic_similarity_threshold:
                    frequent_tag = frequent_tag_list[i]
                    matches.append({
                        'singleton': singleton_tag,
                        'target': frequent_tag,
                        'method': 'semantic',
                        'confidence': sim_score,
                        'reason': f"Semantic similarity: {sim_score:.3f}",
                        'target_usage': self.frequent_tags[frequent_tag]['count'],
                        'metadata': {
                            'semantic_similarity': round(sim_score, 3)
                        }
                    })

            return matches

        except Exception as e:
            # Silently fail - this is an optional enhancement
            return []


def analyze_singletons(
    tag_stats: Dict[str, Dict[str, Any]],
    frequent_threshold: int = 5,
    use_semantic: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function to analyze singleton tags.

    Args:
        tag_stats: Dictionary mapping tag names to their statistics
        frequent_threshold: Minimum usage count to consider a tag "frequent"
        use_semantic: Whether to use semantic similarity (requires sentence-transformers)

    Returns:
        List of merge suggestions
    """
    analyzer = SingletonAnalyzer(tag_stats, frequent_threshold=frequent_threshold)
    return analyzer.analyze(use_semantic=use_semantic)
