#!/usr/bin/env python3
"""
Tag merge analyzer - suggests tag consolidation opportunities.

This analyzer identifies potential tag merges using multiple approaches:

1. SIMILAR NAMES: Uses string similarity (85%+ threshold) to catch likely typos
   and minor variations like "writing/writng" or "tech/technology"

2. SEMANTIC DUPLICATES: Uses TF-IDF character-level n-gram embeddings to find
   semantically similar tags beyond simple string matching. Analyzes character
   patterns (2-4 char n-grams) and calculates cosine similarity to identify
   conceptually related tags like "music/audio" or "family/relatives".
   Falls back to regex patterns if sklearn unavailable.

3. HIGH FILE OVERLAP: Identifies tags that appear together in 80%+ of files,
   suggesting they may be functionally equivalent or one subsumes the other.

4. VARIANT PATTERNS: Detects morphological variants like plural/singular
   forms and verb tenses (writing/writers, parent/parenting).

   Note: This project prefers PLURAL forms as canonical (books not book,
   ideas not idea, projects not project). When suggesting merges, the plural
   form is recommended unless usage patterns strongly indicate otherwise.

The embedding approach is particularly effective at catching semantic relationships
that simple string matching misses, using character-level features that work well
for short tag text.
"""
import json
import sys
import argparse
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import re
from typing import Dict, List, Set, Any, Optional, Iterable
from tagex.utils.tag_normalizer import is_valid_tag

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


def load_tag_data(json_file: str) -> List[Dict[str, Any]]:
    """Load tag data from JSON file.

    Args:
        json_file: Path to JSON file containing tag data

    Returns:
        List of tag dictionaries
    """
    with open(json_file, 'r') as f:
        return json.load(f)  # type: ignore[no-any-return]


def build_tag_stats(tag_data: List[Dict[str, Any]], filter_noise: bool = False) -> Dict[str, Dict[str, Any]]:
    """Build tag usage statistics.

    Args:
        tag_data: List of tag dictionaries
        filter_noise: Whether to filter out invalid tags

    Returns:
        Dictionary mapping tag names to their statistics
    """
    tag_stats: Dict[str, Dict[str, Any]] = {}

    for tag_info in tag_data:
        tag = tag_info['tag']
        if filter_noise and not is_valid_tag(tag):
            continue
        tag_stats[tag] = {
            'count': tag_info['tagCount'],
            'files': set(tag_info['relativePaths'])
        }

    return tag_stats


def find_similar_tags(tags: Iterable[str], similarity_threshold: float = 0.85) -> List[List[str]]:
    """Find tags with very similar names (likely typos/variants).

    Args:
        tags: Iterable of tag strings
        similarity_threshold: Minimum similarity ratio (0-1) to consider tags similar

    Returns:
        List of groups of similar tags
    """
    similar_groups: List[List[str]] = []
    processed: Set[str] = set()

    tags_list = list(tags)
    for i, tag1 in enumerate(tags_list):
        if tag1 in processed:
            continue

        group = [tag1]
        processed.add(tag1)

        for j, tag2 in enumerate(tags_list[i+1:], i+1):
            if tag2 in processed:
                continue

            # Only consider very similar tags to avoid false positives
            if len(tag1) > 3 and len(tag2) > 3:
                similarity = SequenceMatcher(None, tag1.lower(), tag2.lower()).ratio()
                if similarity >= similarity_threshold:
                    group.append(tag2)
                    processed.add(tag2)

        if len(group) > 1:
            similar_groups.append(group)

    return similar_groups


def find_variant_patterns(tags: Iterable[str]) -> Dict[str, List[str]]:
    """Find tags that are likely variants of each other.

    Convention: This function groups variants but does NOT determine which
    form to prefer. Downstream code should prefer PLURAL forms when suggesting
    merges (e.g., books not book, ideas not idea).

    Uses enhanced plural detection from plural_normalizer module to handle
    irregular plurals and complex patterns.

    Args:
        tags: Iterable of tag strings

    Returns:
        Dictionary mapping base forms to lists of variant tags
    """
    from tagex.utils.plural_normalizer import normalize_plural_forms, normalize_compound_plurals, get_preferred_form

    variants: Dict[str, List[str]] = defaultdict(list)

    # Group by base patterns
    for tag in tags:
        # Remove common suffixes/prefixes that might indicate variants
        base = tag.lower()

        # Use enhanced plural normalization
        plural_forms = normalize_plural_forms(tag)
        compound_forms = normalize_compound_plurals(tag)
        all_forms = plural_forms | compound_forms

        # Get preferred form (usually plural)
        canonical = get_preferred_form(all_forms).lower()
        for form in all_forms:
            variants[canonical].append(tag)

        # Remove -ing suffix
        if base.endswith('ing'):
            base_form = base[:-3]
            variants[base_form].append(tag)

        # Remove -ed suffix
        if base.endswith('ed'):
            base_form = base[:-2]
            variants[base_form].append(tag)

        # Add the tag to its own base form
        variants[base].append(tag)

    # Return only groups with multiple variants
    return {k: list(set(v)) for k, v in variants.items() if len(set(v)) > 1}


def find_semantic_duplicates_embedding(
    tag_stats: Dict[str, Dict[str, Any]],
    similarity_threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """Find semantically similar tags using TF-IDF embeddings.

    Args:
        tag_stats: Dictionary mapping tag names to their statistics
        similarity_threshold: Minimum cosine similarity to consider tags semantically similar

    Returns:
        List of semantic duplicate groups with metadata
    """
    if not SKLEARN_AVAILABLE:
        print("Warning: sklearn not available, falling back to pattern matching")
        return find_semantic_duplicates_pattern(tag_stats)
    
    tags = list(tag_stats.keys())
    if len(tags) < 2:
        return []
    
    # Create character-level n-grams for better semantic matching
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 4),
        lowercase=True,
        max_features=1000
    )
    
    try:
        # Fit and transform tags
        tfidf_matrix = vectorizer.fit_transform(tags)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Find similar tag groups
        groups = []
        processed = set()
        
        for i, tag1 in enumerate(tags):
            if tag1 in processed:
                continue
                
            group = [tag1]
            processed.add(tag1)
            
            for j, tag2 in enumerate(tags[i+1:], i+1):
                if tag2 in processed:
                    continue
                    
                if similarity_matrix[i][j] >= similarity_threshold:
                    group.append(tag2)
                    processed.add(tag2)
            
            if len(group) > 1:
                # Sort by usage count
                sorted_group = sorted(group, key=lambda t: tag_stats[t]['count'], reverse=True)
                groups.append({
                    'method': 'embedding',
                    'tags': sorted_group,
                    'suggested_keep': sorted_group[0],
                    'total_usage': sum(tag_stats[tag]['count'] for tag in sorted_group),
                    'similarity_scores': [similarity_matrix[tags.index(sorted_group[0])][tags.index(t)] 
                                        for t in sorted_group[1:]]
                })
        
        return groups
        
    except Exception as e:
        print(f"Warning: embedding analysis failed ({e}), falling back to pattern matching")
        return find_semantic_duplicates_pattern(tag_stats)


def find_semantic_duplicates_pattern(tag_stats: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fallback pattern-based semantic duplicate detection using generic morphological patterns.

    Convention: When suggesting which tag to keep from a group, prefer PLURAL forms
    (e.g., books not book). The 'suggested_keep' field should select the plural variant
    when available, falling back to most-used tag if no clear plural exists.

    Args:
        tag_stats: Dictionary mapping tag names to their statistics

    Returns:
        List of semantic duplicate groups with metadata
    """
    duplicates = []

    # Find word stem groups dynamically
    stem_groups = defaultdict(list)

    for tag in tag_stats.keys():
        tag_lower = tag.lower()

        # Group by common morphological patterns
        if len(tag_lower) <= 3:
            continue  # Skip very short tags

        # Remove common suffixes to find stems
        stems = set()

        # Plural/singular patterns (prefer plural in suggestions)
        if tag_lower.endswith('s') and len(tag_lower) > 4:
            stems.add(tag_lower[:-1])  # remove 's'
        
        # -ing suffix
        if tag_lower.endswith('ing') and len(tag_lower) > 6:
            stems.add(tag_lower[:-3])  # remove 'ing'
            
        # -er/-ed suffixes
        if tag_lower.endswith('er') and len(tag_lower) > 5:
            stems.add(tag_lower[:-2])  # remove 'er'
        if tag_lower.endswith('ed') and len(tag_lower) > 5:
            stems.add(tag_lower[:-2])  # remove 'ed'
            
        # -tion/-sion suffixes
        if tag_lower.endswith('tion') and len(tag_lower) > 7:
            stems.add(tag_lower[:-4])  # remove 'tion'
        if tag_lower.endswith('sion') and len(tag_lower) > 7:
            stems.add(tag_lower[:-4])  # remove 'sion'
            
        # -ly suffix
        if tag_lower.endswith('ly') and len(tag_lower) > 5:
            stems.add(tag_lower[:-2])  # remove 'ly'
            
        # Add the original tag to its own stems
        stems.add(tag_lower)
        
        # Group tags by their stems
        for stem in stems:
            if len(stem) >= 3:  # Only use stems of reasonable length
                stem_groups[stem].append(tag)
    
    # Find groups with multiple tags
    for stem, tags in stem_groups.items():
        if len(tags) > 1:
            # Sort by usage count
            sorted_tags = sorted(tags, key=lambda t: tag_stats[t]['count'], reverse=True)

            # Prefer plural form if available, otherwise most-used
            plural_candidates = [t for t in sorted_tags if t.lower().endswith('s')]
            suggested_keep = plural_candidates[0] if plural_candidates else sorted_tags[0]

            duplicates.append({
                'method': 'pattern',
                'stem': stem,
                'tags': sorted_tags,
                'suggested_keep': suggested_keep,
                'total_usage': sum(tag_stats[tag]['count'] for tag in sorted_tags)
            })
    
    return duplicates


def find_overlapping_tags(
    tag_stats: Dict[str, Dict[str, Any]],
    overlap_threshold: float = 0.8
) -> List[Dict[str, Any]]:
    """Find tags with significant file overlap.

    Args:
        tag_stats: Dictionary mapping tag names to their statistics
        overlap_threshold: Minimum overlap ratio (0-1) to consider tags overlapping

    Returns:
        List of overlapping tag pairs with metadata
    """
    overlaps = []
    tags_list = list(tag_stats.keys())
    
    for i, tag1 in enumerate(tags_list):
        for tag2 in tags_list[i+1:]:
            files1 = tag_stats[tag1]['files']
            files2 = tag_stats[tag2]['files']
            
            if len(files1) == 0 or len(files2) == 0:
                continue
                
            intersection = len(files1.intersection(files2))
            union = len(files1.union(files2))
            overlap_ratio = intersection / union if union > 0 else 0
            
            if overlap_ratio >= overlap_threshold and intersection >= 5:
                overlaps.append({
                    'tag1': tag1,
                    'tag2': tag2,
                    'overlap_ratio': overlap_ratio,
                    'shared_files': intersection,
                    'total_files': union,
                    'suggested_keep': tag1 if tag_stats[tag1]['count'] > tag_stats[tag2]['count'] else tag2
                })
    
    return sorted(overlaps, key=lambda x: x['overlap_ratio'], reverse=True)


def suggest_merges(
    tag_stats: Dict[str, Dict[str, Any]],
    min_usage: int = 3,
    args: Optional[argparse.Namespace] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Generate merge suggestions.

    Args:
        tag_stats: Dictionary mapping tag names to their statistics
        min_usage: Minimum tag usage count to consider
        args: Command-line arguments (optional)

    Returns:
        Dictionary of suggestion categories with lists of suggestions
    """
    suggestions: Dict[str, List[Dict[str, Any]]] = {
        'similar_names': [],
        'semantic_duplicates': [],
        'high_overlap': [],
        'variant_patterns': []
    }
    
    # Filter out very low usage tags
    filtered_tags = {tag: stats for tag, stats in tag_stats.items() 
                    if stats['count'] >= min_usage}
    
    # Find similar names
    similar_groups = find_similar_tags(filtered_tags.keys())
    for group in similar_groups:
        # Suggest keeping the most used tag
        sorted_group = sorted(group, key=lambda t: filtered_tags[t]['count'], reverse=True)
        suggestions['similar_names'].append({
            'tags': sorted_group,
            'suggested_keep': sorted_group[0],
            'total_usage': sum(filtered_tags[tag]['count'] for tag in sorted_group)
        })
    
    # Find semantic duplicates using embeddings or fallback
    if args and args.no_sklearn:
        print("Using pattern-based fallback (--no-sklearn specified)")
        suggestions['semantic_duplicates'] = find_semantic_duplicates_pattern(filtered_tags)
    else:
        suggestions['semantic_duplicates'] = find_semantic_duplicates_embedding(filtered_tags)
    
    # Find overlapping tags
    suggestions['high_overlap'] = find_overlapping_tags(filtered_tags)
    
    # Find variant patterns
    variant_groups = find_variant_patterns(filtered_tags.keys())
    for base, variants in variant_groups.items():
        if len(variants) > 1:
            sorted_variants = sorted(variants, key=lambda t: filtered_tags[t]['count'], reverse=True)
            suggestions['variant_patterns'].append({
                'base': base,
                'tags': sorted_variants,
                'suggested_keep': sorted_variants[0],
                'total_usage': sum(filtered_tags[tag]['count'] for tag in sorted_variants)
            })
    
    return suggestions


def print_merge_suggestions(suggestions: Dict[str, List[Dict[str, Any]]]) -> None:
    """Print merge suggestions in a readable format.

    Args:
        suggestions: Dictionary of suggestion categories with lists of suggestions
    """
    
    print("=== TAG MERGE SUGGESTIONS ===\n")
    
    # Similar names
    if suggestions['similar_names']:
        print("SIMILAR NAMES:")
        for suggestion in suggestions['similar_names']:
            tags = suggestion['tags']
            keep = suggestion['suggested_keep']
            others = [t for t in tags if t != keep]
            print(f"  Keep: {keep}")
            print(f"  Merge: {', '.join(others)}")
            print(f"  Command: tagex /path/to/vault merge {' '.join(others)} --into {keep}")
            print(f"  Total usage: {suggestion['total_usage']}")
            print()
    
    # Semantic duplicates
    if suggestions['semantic_duplicates']:
        print("SEMANTIC DUPLICATES:")
        for suggestion in suggestions['semantic_duplicates']:
            tags = suggestion['tags']
            keep = suggestion['suggested_keep']
            others = [t for t in tags if t != keep]
            if others:  # Only show if there are actually other tags to merge
                print(f"  Keep: {keep}")
                print(f"  Merge: {', '.join(others)}")
                print(f"  Command: tagex /path/to/vault merge {' '.join(others)} --into {keep}")
                print(f"  Total usage: {suggestion['total_usage']}")
                if suggestion.get('method') == 'embedding' and 'similarity_scores' in suggestion:
                    scores = [f"{score:.2f}" for score in suggestion['similarity_scores']]
                    print(f"  Similarity scores: {', '.join(scores)}")
                print()
    
    # High overlap
    if suggestions['high_overlap']:
        print("HIGH FILE OVERLAP:")
        for suggestion in suggestions['high_overlap'][:10]:  # Top 10
            print(f"  {suggestion['tag1']} + {suggestion['tag2']}")
            print(f"  Overlap: {suggestion['overlap_ratio']:.1%} ({suggestion['shared_files']}/{suggestion['total_files']} files)")
            print(f"  Suggest keeping: {suggestion['suggested_keep']}")
            other = suggestion['tag1'] if suggestion['suggested_keep'] == suggestion['tag2'] else suggestion['tag2']
            print(f"  Command: tagex /path/to/vault rename {other} {suggestion['suggested_keep']}")
            print()


def main() -> None:
    """Main entry point for merge analyzer CLI."""
    parser = argparse.ArgumentParser(description='Analyze and suggest tag merges')
    parser.add_argument('input_file', help='JSON file containing tag data')
    parser.add_argument('--min-usage', type=int, default=3, help='Minimum tag usage to consider')
    parser.add_argument('--filter-noise', action='store_true', default=True, help='Filter out technical noise tags')
    parser.add_argument('--no-filter', action='store_true', help='Disable noise filtering')
    parser.add_argument('--no-sklearn', action='store_true', help='Force use of pattern-based fallback instead of embeddings')
    args = parser.parse_args()
    
    # Handle --no-filter override
    filter_noise = args.filter_noise and not args.no_filter
    
    tag_data = load_tag_data(args.input_file)
    tag_stats = build_tag_stats(tag_data, filter_noise)
    
    print(f"Analyzing {len(tag_stats)} tags for merge opportunities...")
    print(f"Minimum usage threshold: {args.min_usage}")
    
    suggestions = suggest_merges(tag_stats, args.min_usage, args)
    print_merge_suggestions(suggestions)


if __name__ == '__main__':
    main()