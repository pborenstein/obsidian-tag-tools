#!/usr/bin/env python3
"""
Content-based tag suggestion analyzer.

This analyzer examines notes with few or no tags and suggests relevant tags
based on content similarity to existing tags. Uses semantic embeddings to
match note content against tag names and their typical usage contexts.
"""

from typing import Dict, List, Any, Set, Optional
from pathlib import Path
import re

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from ..utils.file_discovery import find_markdown_files
from ..core.parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
from ..config.exclusions_config import ExclusionsConfig


class ContentAnalyzer:
    """Suggests tags for notes based on content analysis."""

    def __init__(
        self,
        tag_stats: Dict[str, Dict[str, Any]],
        vault_path: str,
        min_tag_count: int = 0,
        max_tag_count: Optional[int] = None,
        min_tag_frequency: int = 2
    ):
        """
        Initialize content analyzer.

        Args:
            tag_stats: Dictionary mapping tag names to their statistics (count, files)
            vault_path: Path to the Obsidian vault
            min_tag_count: Only process notes with < this many tags (default: 0)
            max_tag_count: Only process notes with <= this many tags (default: None)
            min_tag_frequency: Only suggest tags used >= this many times (default: 2)
        """
        self.tag_stats = tag_stats
        self.vault_path = Path(vault_path)
        self.min_tag_count = min_tag_count
        self.max_tag_count = max_tag_count
        self.min_tag_frequency = min_tag_frequency

        # Load exclusions config
        self.exclusions = ExclusionsConfig(vault_path)

        # Filter to frequent tags only, excluding auto-generated tags
        self.candidate_tags = {
            tag: stats for tag, stats in tag_stats.items()
            if stats['count'] >= min_tag_frequency
            and not self.exclusions.is_suggestion_excluded(tag)
        }

        self.semantic_model = None

    def analyze(
        self,
        paths: Optional[List[str]] = None,
        use_semantic: bool = True,
        top_n: int = 3,
        min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Analyze notes and generate tag suggestions.

        Args:
            paths: Optional list of file paths or glob patterns to analyze
            use_semantic: Whether to use semantic similarity (requires sentence-transformers)
            top_n: Number of tags to suggest per note
            min_confidence: Minimum confidence threshold for suggestions

        Returns:
            List of tag suggestions (one per note)
        """
        if not self.candidate_tags:
            print(f"  No candidate tags found (min frequency: {self.min_tag_frequency})")
            return []

        # Find notes matching criteria
        target_notes = self._find_target_notes(paths)

        if not target_notes:
            if self.max_tag_count is not None:
                criteria = f"< {self.min_tag_count} and <= {self.max_tag_count} tags"
            else:
                criteria = f"< {self.min_tag_count} tags"
            print(f"  No notes found matching criteria ({criteria})")
            return []

        print(f"  Found {len(target_notes)} notes to analyze")
        print(f"  Candidate tags: {len(self.candidate_tags)} (>= {self.min_tag_frequency} uses)")

        # Load semantic model if needed
        if use_semantic and TRANSFORMERS_AVAILABLE:
            try:
                print("  Loading semantic model...")
                self.semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
                # Pre-embed all candidate tags
                self.tag_embeddings = self._embed_tags()
            except Exception as e:
                print(f"  Warning: Could not load semantic model: {e}")
                self.semantic_model = None
        elif use_semantic and not TRANSFORMERS_AVAILABLE:
            print("  Warning: sentence-transformers not available, skipping semantic analysis")

        # Analyze each note
        suggestions = []
        for note_path, current_tags in target_notes:
            note_suggestions = self._suggest_tags_for_note(
                note_path,
                current_tags,
                top_n,
                min_confidence
            )
            if note_suggestions:
                suggestions.append(note_suggestions)

        print(f"  Generated suggestions for {len(suggestions)} notes")
        return suggestions

    def _find_target_notes(self, paths: Optional[List[str]] = None) -> List[tuple]:
        """
        Find notes matching the criteria (tag count threshold + optional paths).

        Args:
            paths: Optional list of file paths or glob patterns

        Returns:
            List of (note_path, current_tags) tuples
        """
        target_notes = []

        # Get all markdown files
        if paths:
            # Handle paths/globs
            all_files = set()
            for path_pattern in paths:
                path = Path(path_pattern)
                if path.is_file() and path.suffix == '.md':
                    all_files.add(path)
                elif path.is_dir():
                    # Find all .md files in directory
                    all_files.update(path.rglob('*.md'))
                elif '*' in str(path_pattern):
                    # Glob pattern
                    all_files.update(self.vault_path.glob(path_pattern))
        else:
            # Use all files in vault
            all_files = set(find_markdown_files(self.vault_path, exclude_patterns={'.obsidian'}))

        # Filter by tag count
        for file_path in all_files:
            if not file_path.exists():
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract current tags
                frontmatter, _ = extract_frontmatter(content)
                current_tags = extract_tags_from_frontmatter(frontmatter) if frontmatter else []
                tag_count = len(current_tags)

                # Check if note matches criteria
                # We want to suggest for notes with >= min_tag_count tags
                if tag_count >= self.min_tag_count:
                    # Has too many tags - skip
                    continue

                if self.max_tag_count is not None and tag_count > self.max_tag_count:
                    # Has more tags than maximum - skip
                    continue

                target_notes.append((file_path, set(t.lower() for t in current_tags)))

            except Exception as e:
                print(f"  Warning: Could not read {file_path}: {e}")
                continue

        return target_notes

    def _suggest_tags_for_note(
        self,
        note_path: Path,
        current_tags: Set[str],
        top_n: int,
        min_confidence: float
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest tags for a single note.

        Args:
            note_path: Path to the note
            current_tags: Set of tags already on the note (lowercase)
            top_n: Number of tags to suggest
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary with suggestion details or None if no good suggestions
        """
        # Extract note content
        content = self._extract_note_content(note_path)
        if not content:
            return None

        # Get tag suggestions
        if self.semantic_model is not None:
            suggestions = self._semantic_similarity(content, current_tags, top_n, min_confidence)
        else:
            # Fallback to basic keyword matching
            suggestions = self._keyword_matching(content, current_tags, top_n, min_confidence)

        if not suggestions:
            return None

        return {
            'file': str(note_path.relative_to(self.vault_path)),
            'current_tags': list(current_tags),
            'suggested_tags': [s['tag'] for s in suggestions],
            'confidences': [round(s['confidence'], 3) for s in suggestions],
            'methods': [s['method'] for s in suggestions]
        }

    def _extract_note_content(self, note_path: Path) -> Optional[str]:
        """
        Extract meaningful content from a note for analysis.

        Args:
            note_path: Path to the note

        Returns:
            Extracted content string or None if error
        """
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove frontmatter
            _, body = extract_frontmatter(content)

            # Extract title (filename without extension)
            title = note_path.stem

            # Remove code blocks (both inline and fenced)
            body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
            body = re.sub(r'`[^`]*`', '', body)

            # Extract headers (give them more weight)
            headers = re.findall(r'^#+\s+(.+)$', body, re.MULTILINE)
            header_text = ' '.join(headers)

            # Get first few paragraphs (up to ~500 chars)
            paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
            intro_text = ' '.join(paragraphs[:3])[:500]

            # Combine: title gets repeated for emphasis, then headers, then intro
            combined = f"{title} {title} {header_text} {intro_text}"

            return combined.strip()

        except Exception as e:
            return None

    def _embed_tags(self) -> Dict[str, Any]:
        """Pre-embed all candidate tags for efficient similarity calculation."""
        if self.semantic_model is None:
            return {}

        tag_list = list(self.candidate_tags.keys())
        embeddings = self.semantic_model.encode(tag_list, show_progress_bar=False)

        return {
            tag: embeddings[i]
            for i, tag in enumerate(tag_list)
        }

    def _semantic_similarity(
        self,
        content: str,
        current_tags: Set[str],
        top_n: int,
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """
        Find semantically similar tags using embeddings.

        Args:
            content: Note content
            current_tags: Current tags (to exclude from suggestions)
            top_n: Number of suggestions to return
            min_confidence: Minimum similarity threshold

        Returns:
            List of tag suggestions with confidence scores
        """
        if self.semantic_model is None or not self.tag_embeddings:
            return []

        try:
            # Embed the content
            content_embedding = self.semantic_model.encode([content])[0]

            # Calculate similarity to all candidate tags
            similarities = []
            for tag, tag_embedding in self.tag_embeddings.items():
                # Skip tags already on the note
                if tag.lower() in current_tags:
                    continue

                # Calculate cosine similarity
                sim = cosine_similarity(
                    content_embedding.reshape(1, -1),
                    tag_embedding.reshape(1, -1)
                )[0][0]

                # Convert numpy scalar to Python float
                sim = float(sim)

                if sim >= min_confidence:
                    similarities.append({
                        'tag': tag,
                        'confidence': sim,
                        'method': 'semantic'
                    })

            # Sort by confidence and return top N
            similarities.sort(key=lambda x: x['confidence'], reverse=True)
            return similarities[:top_n]

        except Exception as e:
            print(f"  Warning: Semantic similarity failed: {e}")
            return []

    def _keyword_matching(
        self,
        content: str,
        current_tags: Set[str],
        top_n: int,
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """
        Simple keyword-based tag matching (fallback when embeddings not available).

        Args:
            content: Note content
            current_tags: Current tags (to exclude from suggestions)
            top_n: Number of suggestions to return
            min_confidence: Minimum similarity threshold

        Returns:
            List of tag suggestions with confidence scores
        """
        content_lower = content.lower()
        suggestions = []

        for tag, stats in self.candidate_tags.items():
            # Skip tags already on the note
            if tag.lower() in current_tags:
                continue

            # Simple substring matching
            tag_parts = tag.lower().replace('-', ' ').replace('/', ' ').split()

            # Count how many tag parts appear in content
            matches = sum(1 for part in tag_parts if part in content_lower)

            if matches > 0:
                # Confidence based on: matches / total parts, weighted by tag frequency
                confidence = (matches / len(tag_parts)) * 0.5

                # Boost by tag frequency (more common tags are safer suggestions)
                frequency_boost = min(stats['count'] / 10, 0.5)
                confidence += frequency_boost

                if confidence >= min_confidence:
                    suggestions.append({
                        'tag': tag,
                        'confidence': min(confidence, 1.0),
                        'method': 'keyword'
                    })

        # Sort by confidence and return top N
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions[:top_n]


def analyze_content(
    tag_stats: Dict[str, Dict[str, Any]],
    vault_path: str,
    paths: Optional[List[str]] = None,
    min_tag_count: int = 0,
    max_tag_count: Optional[int] = None,
    top_n: int = 3,
    use_semantic: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function to analyze note content and suggest tags.

    Args:
        tag_stats: Dictionary mapping tag names to their statistics
        vault_path: Path to the Obsidian vault
        paths: Optional list of file paths or glob patterns
        min_tag_count: Only process notes with < this many tags
        max_tag_count: Only process notes with <= this many tags
        top_n: Number of tags to suggest per note
        use_semantic: Whether to use semantic similarity

    Returns:
        List of tag suggestions
    """
    analyzer = ContentAnalyzer(
        tag_stats,
        vault_path,
        min_tag_count=min_tag_count,
        max_tag_count=max_tag_count
    )
    return analyzer.analyze(
        paths=paths,
        use_semantic=use_semantic,
        top_n=top_n
    )
