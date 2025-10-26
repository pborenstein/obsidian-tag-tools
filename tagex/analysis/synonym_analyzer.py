"""
Synonym detection for tag quality improvements.

This module provides co-occurrence based synonym detection to identify tags that
appear in similar contexts and are likely conceptual equivalents.
"""

from typing import Dict, List, Set, Any


def detect_synonyms_by_context(
    tag_stats: Dict[str, Dict[str, Any]],
    min_shared_files: int = 3,
    similarity_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Detect potential synonyms based on shared context.

    Tags that appear with similar sets of other tags are likely synonyms.
    Uses Jaccard similarity on co-occurring tags.

    Args:
        tag_stats: Dictionary mapping tag names to their statistics
                  Expected format: {'tag': {'count': int, 'files': set}}
        min_shared_files: Minimum number of shared files to consider co-occurrence
        similarity_threshold: Minimum Jaccard similarity to suggest synonymy

    Returns:
        List of synonym candidates with similarity scores and suggestions
    """
    synonym_candidates = []
    tags = list(tag_stats.keys())

    # Build co-occurrence sets for each tag
    cooccurrence: Dict[str, Set[str]] = {}
    for tag in tags:
        # Find all other tags that appear in same files
        cooccurrence[tag] = set()
        for other_tag, stats in tag_stats.items():
            if other_tag != tag:
                shared_files = tag_stats[tag]['files'] & stats['files']
                if len(shared_files) >= min_shared_files:
                    cooccurrence[tag].add(other_tag)

    # Compare co-occurrence sets
    for i, tag1 in enumerate(tags):
        for tag2 in tags[i+1:]:
            if not cooccurrence[tag1] or not cooccurrence[tag2]:
                continue

            # Jaccard similarity
            intersection = len(cooccurrence[tag1] & cooccurrence[tag2])
            union = len(cooccurrence[tag1] | cooccurrence[tag2])
            similarity = intersection / union if union > 0 else 0

            # High context similarity suggests synonymy
            if similarity >= similarity_threshold:
                # Suggest merging into the more commonly used tag
                if tag_stats[tag1]['count'] > tag_stats[tag2]['count']:
                    suggestion = f"merge {tag2} → {tag1}"
                    target = tag1
                    source = tag2
                else:
                    suggestion = f"merge {tag1} → {tag2}"
                    target = tag2
                    source = tag1

                synonym_candidates.append({
                    'tag1': tag1,
                    'tag2': tag2,
                    'target': target,
                    'source': source,
                    'context_similarity': similarity,
                    'shared_context': intersection,
                    'suggestion': suggestion,
                    'tag1_count': tag_stats[tag1]['count'],
                    'tag2_count': tag_stats[tag2]['count']
                })

    return sorted(synonym_candidates, key=lambda x: x['context_similarity'], reverse=True)


def suggest_synonym_groups(
    tag_stats: Dict[str, Dict[str, Any]],
    min_shared_files: int = 3,
    similarity_threshold: float = 0.7
) -> List[List[str]]:
    """Suggest groups of tags that are likely synonyms.

    Uses transitive closure to group tags that share high context similarity.

    Args:
        tag_stats: Dictionary mapping tag names to their statistics
        min_shared_files: Minimum number of shared files to consider co-occurrence
        similarity_threshold: Minimum Jaccard similarity to suggest synonymy

    Returns:
        List of synonym groups (each group is a list of tags)
    """
    # Get all pairwise candidates
    candidates = detect_synonyms_by_context(
        tag_stats,
        min_shared_files=min_shared_files,
        similarity_threshold=similarity_threshold
    )

    # Build adjacency graph
    graph: Dict[str, Set[str]] = {}
    for candidate in candidates:
        tag1 = candidate['tag1']
        tag2 = candidate['tag2']

        if tag1 not in graph:
            graph[tag1] = set()
        if tag2 not in graph:
            graph[tag2] = set()

        graph[tag1].add(tag2)
        graph[tag2].add(tag1)

    # Find connected components (synonym groups)
    visited: Set[str] = set()
    synonym_groups: List[List[str]] = []

    def dfs(tag: str, group: List[str]) -> None:
        """Depth-first search to find connected components."""
        visited.add(tag)
        group.append(tag)
        if tag in graph:
            for neighbor in graph[tag]:
                if neighbor not in visited:
                    dfs(neighbor, group)

    for tag in graph:
        if tag not in visited:
            group: List[str] = []
            dfs(tag, group)
            if len(group) > 1:
                # Sort by usage count (most used first)
                group.sort(key=lambda t: tag_stats[t]['count'], reverse=True)
                synonym_groups.append(group)

    return synonym_groups


def find_acronym_expansions(
    tag_stats: Dict[str, Dict[str, Any]],
    min_overlap_ratio: float = 0.5
) -> List[Dict[str, Any]]:
    """Find potential acronym/expansion pairs.

    Examples: ai/artificial-intelligence, ml/machine-learning, js/javascript

    Args:
        tag_stats: Dictionary mapping tag names to their statistics
        min_overlap_ratio: Minimum file overlap ratio to consider relationship

    Returns:
        List of potential acronym pairs
    """
    acronym_candidates = []
    tags = list(tag_stats.keys())

    for tag in tags:
        tag_lower = tag.lower()

        # Skip if not a short potential acronym (2-4 chars, no special chars)
        if len(tag_lower) < 2 or len(tag_lower) > 4 or '-' in tag_lower or '/' in tag_lower:
            continue

        # Look for potential expansions
        for other_tag in tags:
            if tag == other_tag:
                continue

            other_lower = other_tag.lower()

            # Check if other tag could be an expansion
            # Simple heuristic: check if acronym letters match first letters of words
            words = other_lower.replace('-', ' ').replace('/', ' ').split()
            if len(words) >= 2:
                # Build acronym from first letters
                potential_acronym = ''.join(w[0] for w in words if w)

                if potential_acronym == tag_lower:
                    # Calculate file overlap
                    shared = len(tag_stats[tag]['files'] & tag_stats[other_tag]['files'])
                    tag_files = len(tag_stats[tag]['files'])
                    other_files = len(tag_stats[other_tag]['files'])
                    min_files = min(tag_files, other_files)

                    overlap_ratio = shared / min_files if min_files > 0 else 0

                    if overlap_ratio >= min_overlap_ratio:
                        acronym_candidates.append({
                            'acronym': tag,
                            'expansion': other_tag,
                            'overlap_ratio': overlap_ratio,
                            'shared_files': shared,
                            'acronym_count': tag_stats[tag]['count'],
                            'expansion_count': tag_stats[other_tag]['count'],
                            'suggestion': f"merge {tag} → {other_tag} (acronym expansion)"
                        })

    return sorted(acronym_candidates, key=lambda x: x['overlap_ratio'], reverse=True)
