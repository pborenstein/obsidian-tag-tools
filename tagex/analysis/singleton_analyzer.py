#!/usr/bin/env python3
"""
Singleton tag analyzer - suggests merging singleton tags into frequent tags.

This analyzer specifically targets tags that appear only once (singletons) and
suggests merging them into existing frequent tags based on similarity metrics:

1. STRING SIMILARITY: Catches typos and minor variations (e.g., "machne-learning" → "machine-learning")
2. SEMANTIC SIMILARITY: Uses sentence embeddings to find true synonyms (e.g., "ai" → "artificial-intelligence")

The analyzer only suggests one-directional merges: singleton → frequent tag (count >= threshold).
This ensures we're consolidating rare tags into established taxonomy, not the reverse.

Note: TF-IDF and co-occurrence methods were removed as they produced too many false positives.
"""

from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class SingletonAnalyzer:
    """Analyzes singleton tags and suggests merges into frequent tags."""

    def __init__(
        self,
        tag_stats: Dict[str, Dict[str, Any]],
        frequent_threshold: int = 2,
        string_similarity_threshold: float = 0.90,
        semantic_similarity_threshold: float = 0.70
    ):
        """
        Initialize singleton analyzer.

        Args:
            tag_stats: Dictionary mapping tag names to their statistics (count, files)
            frequent_threshold: Minimum usage count to consider a tag "frequent" (default: 2)
            string_similarity_threshold: Minimum string similarity ratio (0-1, default: 0.90)
            semantic_similarity_threshold: Minimum semantic similarity for embeddings (0-1, default: 0.70)
        """
        self.tag_stats = tag_stats
        self.frequent_threshold = frequent_threshold
        self.string_similarity_threshold = string_similarity_threshold
        self.semantic_similarity_threshold = semantic_similarity_threshold

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

        # Check string similarity against all frequent tags
        for frequent_tag, frequent_stats in self.frequent_tags.items():
            # Skip if same tag
            if singleton_tag == frequent_tag:
                continue

            # String similarity (catches typos, abbreviations)
            string_sim = self._string_similarity(singleton_tag, frequent_tag)
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

        # Semantic similarity (true synonyms)
        if self.semantic_model is not None:
            semantic_matches = self._semantic_similarity(singleton_tag)
            matches.extend(semantic_matches)

        return matches

    def _string_similarity(self, tag1: str, tag2: str) -> float:
        """Calculate string similarity using SequenceMatcher."""
        return SequenceMatcher(None, tag1.lower(), tag2.lower()).ratio()

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
                    # Convert numpy scalar to Python float for YAML serialization
                    confidence = float(sim_score)
                    matches.append({
                        'singleton': singleton_tag,
                        'target': frequent_tag,
                        'method': 'semantic',
                        'confidence': confidence,
                        'reason': f"Semantic similarity: {confidence:.3f}",
                        'target_usage': self.frequent_tags[frequent_tag]['count'],
                        'metadata': {
                            'semantic_similarity': round(confidence, 3)
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
