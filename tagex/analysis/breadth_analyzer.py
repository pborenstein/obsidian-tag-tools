"""
Overbroad tag detection for tag quality improvements.

This module identifies tags that are used too broadly to be meaningful,
provides specificity scoring, and suggests refinements.
"""

import math
from collections import Counter, defaultdict
from typing import Dict, List, Set, Any, Optional


# Common generic words that indicate low specificity
GENERIC_WORDS = {
    'notes', 'ideas', 'misc', 'general', 'stuff', 'things',
    'temp', 'draft', 'random', 'other', 'various', 'todo',
    'pending', 'review', 'inbox', 'archive'
}


def detect_overbroad_tags(
    tag_stats: Dict[str, Dict[str, Any]],
    total_files: int,
    thresholds: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """Detect tags that appear in too many files to be meaningful.

    Args:
        tag_stats: Tag usage statistics
        total_files: Total number of files in vault
        thresholds: Configuration for detection thresholds

    Returns:
        List of overbroad tags with analysis
    """
    if thresholds is None:
        thresholds = {
            'high_coverage': 0.30,      # Appears in >30% of files
            'very_high_coverage': 0.50, # Appears in >50% of files
            'extreme_coverage': 0.70    # Appears in >70% of files
        }

    overbroad = []

    for tag, stats in tag_stats.items():
        usage_ratio = len(stats['files']) / total_files

        severity = None
        if usage_ratio >= thresholds['extreme_coverage']:
            severity = 'extreme'
        elif usage_ratio >= thresholds['very_high_coverage']:
            severity = 'very_high'
        elif usage_ratio >= thresholds['high_coverage']:
            severity = 'high'

        if severity:
            overbroad.append({
                'tag': tag,
                'severity': severity,
                'file_count': len(stats['files']),
                'file_ratio': usage_ratio,
                'total_files': total_files,
            })

    return sorted(overbroad, key=lambda x: x['file_ratio'], reverse=True)


def calculate_tag_specificity(
    tag: str,
    tag_stats: Dict[str, Dict[str, Any]],
    total_files: int
) -> Dict[str, Any]:
    """Calculate specificity score for a tag.

    Uses multiple metrics:
    - Information content (inverse probability)
    - Structural depth (nested tags are more specific)
    - Generic word detection
    - Co-occurrence diversity

    Args:
        tag: The tag to analyze
        tag_stats: Tag usage statistics
        total_files: Total number of files in vault

    Returns:
        Dictionary with specificity analysis
    """
    # 1. Information Content
    p_tag = len(tag_stats[tag]['files']) / total_files
    ic_score = -math.log2(p_tag) if p_tag > 0 else 0

    # 2. Structural depth
    depth = len(tag.split('/'))
    has_compound = '-' in tag or '_' in tag
    structure_score = depth + (1 if has_compound else 0)

    # 3. Generic word penalty
    is_generic = tag.lower() in GENERIC_WORDS
    generic_penalty = -5 if is_generic else 0

    # 4. Co-occurrence diversity (how many different tags does it appear with?)
    cooccurring_tags = set()
    for other_tag, stats in tag_stats.items():
        if other_tag != tag:
            if len(tag_stats[tag]['files'] & stats['files']) > 0:
                cooccurring_tags.add(other_tag)

    # High diversity might indicate overuse
    diversity_ratio = len(cooccurring_tags) / max(len(tag_stats) - 1, 1)
    diversity_penalty = -2 if diversity_ratio > 0.5 else 0

    # Combined specificity score
    total_score = ic_score + structure_score + generic_penalty + diversity_penalty

    return {
        'tag': tag,
        'specificity_score': total_score,
        'ic_score': ic_score,
        'structure_score': structure_score,
        'is_generic': is_generic,
        'cooccurrence_diversity': diversity_ratio,
        'assessment': _assess_specificity(total_score)
    }


def _assess_specificity(score: float) -> str:
    """Assess specificity level based on score.

    Args:
        score: The specificity score

    Returns:
        Assessment category
    """
    if score >= 5.0:
        return 'highly_specific'
    elif score >= 3.0:
        return 'appropriately_specific'
    elif score >= 1.0:
        return 'moderately_specific'
    else:
        return 'too_broad'


def suggest_tag_refinements(
    tag: str,
    tag_stats: Dict[str, Dict[str, Any]],
    all_tags: Set[str],
    max_suggestions: int = 5
) -> List[str]:
    """Suggest more specific alternatives to an overbroad tag.

    Analyzes what other tags commonly appear with this tag to suggest
    natural breakdowns.

    Args:
        tag: The tag to suggest refinements for
        tag_stats: Tag usage statistics
        all_tags: Set of all tags in the vault
        max_suggestions: Maximum number of suggestions to return

    Returns:
        List of suggestion strings
    """
    suggestions = []

    # Find frequently co-occurring tags
    cooccurrence = Counter()
    for other_tag in all_tags:
        if other_tag != tag and not other_tag.startswith(tag + '/'):
            shared = len(tag_stats[tag]['files'] & tag_stats[other_tag]['files'])
            if shared >= 5:
                cooccurrence[other_tag] = shared

    # Suggest hierarchical breakdowns
    top_cooccurring = [t for t, _ in cooccurrence.most_common(10)]

    if top_cooccurring:
        suggestions.append(f"Consider breaking down '{tag}' into:")
        for related_tag in top_cooccurring[:max_suggestions]:
            suggestions.append(f"  - {tag}/{related_tag}")

    # Check if nested versions already exist
    existing_nested = sorted([t for t in all_tags if t.startswith(tag + '/')])
    if existing_nested:
        suggestions.append(f"\nExisting specific tags (consider using these instead):")
        for nested in existing_nested[:max_suggestions]:
            uses = tag_stats[nested]['count']
            suggestions.append(f"  - {nested} ({uses} uses)")

    return suggestions


def analyze_tag_quality(
    tag_stats: Dict[str, Dict[str, Any]],
    total_files: int
) -> Dict[str, Any]:
    """Perform comprehensive tag quality analysis.

    Args:
        tag_stats: Tag usage statistics
        total_files: Total number of files in vault

    Returns:
        Dictionary with complete quality analysis
    """
    # Detect overbroad tags
    overbroad = detect_overbroad_tags(tag_stats, total_files)

    # Calculate specificity for all tags
    specificity_scores = {
        tag: calculate_tag_specificity(tag, tag_stats, total_files)
        for tag in tag_stats.keys()
    }

    # Group by assessment
    by_assessment: Dict[str, List[tuple[str, Dict[str, Any]]]] = defaultdict(list)
    for tag, score_data in specificity_scores.items():
        by_assessment[score_data['assessment']].append((tag, score_data))

    # Sort each assessment group by score
    for assessment in by_assessment:
        by_assessment[assessment].sort(key=lambda x: x[1]['specificity_score'])

    return {
        'overbroad_tags': overbroad,
        'specificity_scores': specificity_scores,
        'by_assessment': dict(by_assessment),
        'summary': {
            'total_tags': len(tag_stats),
            'overbroad_count': len(overbroad),
            'too_broad_count': len(by_assessment.get('too_broad', [])),
            'moderately_specific_count': len(by_assessment.get('moderately_specific', [])),
            'appropriately_specific_count': len(by_assessment.get('appropriately_specific', [])),
            'highly_specific_count': len(by_assessment.get('highly_specific', []))
        }
    }


def format_quality_report(
    analysis: Dict[str, Any],
    tag_stats: Dict[str, Dict[str, Any]],
    max_items: int = 10
) -> str:
    """Format quality analysis as a readable text report.

    Args:
        analysis: Quality analysis dictionary from analyze_tag_quality()
        tag_stats: Tag usage statistics
        max_items: Maximum items to show in each section

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=== TAG QUALITY REPORT ===\n")

    # Summary
    summary = analysis['summary']
    lines.append("SUMMARY:")
    lines.append(f"  Total tags: {summary['total_tags']}")
    lines.append(f"  Overbroad tags: {summary['overbroad_count']}")
    lines.append(f"  Too broad: {summary['too_broad_count']}")
    lines.append(f"  Moderately specific: {summary['moderately_specific_count']}")
    lines.append(f"  Appropriately specific: {summary['appropriately_specific_count']}")
    lines.append(f"  Highly specific: {summary['highly_specific_count']}\n")

    # Overbroad tags
    overbroad = analysis['overbroad_tags']
    if overbroad:
        lines.append("OVERBROAD TAGS (used too generally):\n")
        for item in overbroad[:max_items]:
            lines.append(f"  {item['tag']}")
            lines.append(f"    Coverage: {item['file_ratio']:.1%} ({item['file_count']}/{item['total_files']} files)")
            lines.append(f"    Severity: {item['severity']}")

            # Get refinement suggestions
            suggestions = suggest_tag_refinements(
                item['tag'],
                tag_stats,
                set(tag_stats.keys()),
                max_suggestions=3
            )
            if suggestions:
                for suggestion in suggestions[:5]:
                    lines.append(f"    {suggestion}")
            lines.append("")

    # Specificity analysis
    lines.append("\nSPECIFICITY ANALYSIS:\n")

    by_assessment = analysis['by_assessment']
    for assessment in ['too_broad', 'moderately_specific', 'appropriately_specific', 'highly_specific']:
        if assessment in by_assessment and by_assessment[assessment]:
            lines.append(f"\n{assessment.replace('_', ' ').title()}:")
            for tag, data in by_assessment[assessment][:max_items]:
                lines.append(f"  {tag} [score: {data['specificity_score']:.2f}]")

    return '\n'.join(lines)
