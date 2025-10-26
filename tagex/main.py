#!/usr/bin/env python3
"""
Obsidian Tag Extractor - Extract tags from Obsidian vault markdown files
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict
import click
from collections import Counter, defaultdict
import math

from .core.extractor.core import TagExtractor
from .core.extractor.output_formatter import (
    format_as_plugin_json,
    format_as_csv,
    format_as_text,
    save_output,
    print_summary
)
from .core.operations.tag_operations import RenameOperation, MergeOperation, DeleteOperation


@click.group()
@click.version_option()
def main():
    """Obsidian Tag Management Tool - Extract and modify tags in Obsidian vaults."""
    pass


@main.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path (default: stdout)')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'txt']), default='json', help='Output format')
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--exclude', multiple=True, help='Patterns to exclude (can be used multiple times)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress summary output')
@click.option('--no-filter', is_flag=True, help='Disable tag filtering (include all raw tags)')
def extract(vault_path, output, format, tag_types, exclude, verbose, quiet, no_filter):
    """Extract tags from the vault.

    VAULT_PATH: Path to the Obsidian vault directory
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Convert exclude patterns to set
    exclude_patterns = set(exclude) if exclude else None

    try:
        # Initialize extractor
        extractor = TagExtractor(vault_path, exclude_patterns, filter_tags=not no_filter, tag_types=tag_types)

        # Extract tags
        tag_data = extractor.extract_tags()

        # Get statistics
        stats = extractor.get_statistics()

        # Format output
        formatted_data: Any
        if format == 'json':
            formatted_data = format_as_plugin_json(tag_data)
        elif format == 'csv':
            formatted_data = format_as_csv(tag_data)
        elif format == 'txt':
            formatted_data = format_as_text(tag_data)

        # Save or print output
        if output:
            save_output(formatted_data, Path(output), format)
            if not quiet:
                print(f"Output saved to: {output}")
        else:
            if format == 'json':
                import json
                print(json.dumps(formatted_data, indent=2, ensure_ascii=False))
            elif format == 'csv':
                import csv
                import io
                output_buffer = io.StringIO()
                writer = csv.writer(output_buffer)
                writer.writerows(formatted_data)
                print(output_buffer.getvalue().strip())
            elif format == 'txt':
                print(formatted_data)

        # Print summary if not quiet
        if not quiet and output:
            print_summary(tag_data, stats)

    except Exception as e:
        logging.error(f"Error during extraction: {e}")
        sys.exit(1)


@main.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('old_tag')
@click.argument('new_tag')
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
def rename(vault_path, old_tag, new_tag, tag_types, dry_run):
    """Rename a tag across all files in the vault.

    VAULT_PATH: Path to the Obsidian vault directory

    OLD_TAG: Tag to rename

    NEW_TAG: New tag name
    """
    operation = RenameOperation(vault_path, old_tag, new_tag, dry_run=dry_run, tag_types=tag_types)
    operation.run_operation()


@main.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('source_tags', nargs=-1, required=True)
@click.option('--into', 'target_tag', required=True, help='Target tag to merge into')
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
def merge(vault_path, source_tags, target_tag, tag_types, dry_run):
    """Merge multiple tags into a single tag.

    VAULT_PATH: Path to the Obsidian vault directory

    SOURCE_TAGS: Tags to merge (space-separated)
    """
    operation = MergeOperation(vault_path, list(source_tags), target_tag, dry_run=dry_run, tag_types=tag_types)
    operation.run_operation()


@main.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('tags_to_delete', nargs=-1, required=True)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
def delete(vault_path, tags_to_delete, tag_types, dry_run):
    """Delete tags entirely from all files in the vault.

    VAULT_PATH: Path to the Obsidian vault directory

    TAGS_TO_DELETE: Tags to delete (space-separated)

    WARNING: This operation removes tags from both frontmatter and inline content.
    Use --dry-run first to preview changes. Inline tag deletion may affect readability.
    """
    operation = DeleteOperation(vault_path, list(tags_to_delete), dry_run=dry_run, tag_types=tag_types)
    operation.run_operation()


@main.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--top', '-t', type=int, default=20, help='Number of top tags to show (default: 20)')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--no-filter', is_flag=True, help='Disable tag filtering (include all raw tags)')
def stats(vault_path, tag_types, top, format, no_filter):
    """Display comprehensive tag statistics for the vault.

    VAULT_PATH: Path to the Obsidian vault directory

    Shows tag counts, distribution patterns, and vault health metrics.
    """
    # Set up logging
    logging.basicConfig(level=logging.WARNING)  # Suppress info logs for cleaner output

    try:
        # Initialize extractor
        extractor = TagExtractor(vault_path, filter_tags=not no_filter, tag_types=tag_types)

        # Extract tags
        tag_data = extractor.extract_tags()

        # Get basic statistics
        basic_stats = extractor.get_statistics()

        # Calculate comprehensive statistics
        stats_result = calculate_tag_statistics(tag_data, basic_stats, top)

        if format == 'json':
            import json
            print(json.dumps(stats_result, indent=2, ensure_ascii=False))
        else:
            print_tag_statistics(stats_result, tag_types)

    except Exception as e:
        logging.error(f"Error during stats generation: {e}")
        sys.exit(1)


@main.group()
def analyze():
    """Analyze tag relationships and suggest improvements.

    Provides insights into tag usage patterns, co-occurrence, and merge opportunities.
    """
    pass


@analyze.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--min-pairs', type=int, default=2, help='Minimum pair threshold')
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
def pairs(input_file, min_pairs, no_filter):
    """Analyze tag pair patterns and co-occurrence.

    INPUT_FILE: JSON file containing tag data (from extract command)
    """
    from .analysis.pair_analyzer import load_tag_data, analyze_tag_relationships, find_tag_clusters
    from collections import defaultdict

    filter_noise = not no_filter

    tag_data = load_tag_data(input_file)
    pairs_result, file_to_tags = analyze_tag_relationships(tag_data, min_pairs, filter_noise)

    # Top tag pairs
    print("\nTop 20 Tag Pairs:")
    for (tag1, tag2), count in sorted(pairs_result.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"{count:3d}  {tag1} + {tag2}")

    # Find clusters
    clusters = find_tag_clusters(pairs_result)
    print(f"\nFound {len(clusters)} natural tag clusters:")
    for i, cluster in enumerate(clusters, 1):
        print(f"\nCluster {i} ({len(cluster)} tags):")
        for tag in sorted(cluster):
            print(f"  - {tag}")

    # Most connected tags
    tag_connections: Dict[str, int] = defaultdict(int)
    for (tag1, tag2), count in pairs_result.items():
        tag_connections[tag1] += count
        tag_connections[tag2] += count

    print(f"\nMost Connected Tags (hub tags):")
    for tag, total_connections in sorted(tag_connections.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"{total_connections:3d}  {tag}")


@analyze.command('merge')
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--min-usage', type=int, default=3, help='Minimum tag usage to consider')
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
@click.option('--no-sklearn', is_flag=True, help='Force use of pattern-based fallback instead of embeddings')
def analyze_merge(input_file, min_usage, no_filter, no_sklearn):
    """Suggest tag merge opportunities.

    INPUT_FILE: JSON file containing tag data (from extract command)

    Identifies potential tag merges using multiple approaches:
    - Similar names (string similarity)
    - Semantic duplicates (TF-IDF embeddings)
    - High file overlap
    - Variant patterns (plural/singular, tenses)
    """
    from .analysis.merge_analyzer import load_tag_data, build_tag_stats, suggest_merges, print_merge_suggestions
    import argparse

    filter_noise = not no_filter

    tag_data = load_tag_data(input_file)
    tag_stats = build_tag_stats(tag_data, filter_noise)

    print(f"Analyzing {len(tag_stats)} tags for merge opportunities...")
    print(f"Minimum usage threshold: {min_usage}")

    # Create a minimal args object for the suggest_merges function
    args = argparse.Namespace(no_sklearn=no_sklearn)

    suggestions = suggest_merges(tag_stats, min_usage, args)
    print_merge_suggestions(suggestions)


def calculate_tag_statistics(tag_data, basic_stats, top_count):
    """Calculate comprehensive tag statistics."""
    if not tag_data:
        return {
            "basic": basic_stats,
            "total_tags": 0,
            "tag_distribution": {},
            "vault_health": {}
        }

    # Basic counts
    total_tags = len(tag_data)
    # tag_data is a dict where keys are tag names and values are tag info
    tag_counts = [(tag_name, tag_info['count']) for tag_name, tag_info in tag_data.items()]
    tag_counts.sort(key=lambda x: x[1], reverse=True)

    # Usage distribution analysis
    usage_counts = [count for _, count in tag_counts]
    usage_counter = Counter(usage_counts)

    # Singletons, doubletons, tripletons
    singletons = usage_counter[1] if 1 in usage_counter else 0
    doubletons = usage_counter[2] if 2 in usage_counter else 0
    tripletons = usage_counter[3] if 3 in usage_counter else 0

    # Calculate tag health metrics
    total_tag_uses = sum(usage_counts)
    files_processed = basic_stats.get('files_processed', 0)

    # Diversity metrics
    shannon_entropy = calculate_shannon_entropy(usage_counts) if usage_counts else 0
    tag_density = total_tag_uses / files_processed if files_processed > 0 else 0

    # Coverage analysis - how many files have tags
    tagged_files = set()
    for tag_info in tag_data.values():
        tagged_files.update(tag_info.get('files', []))

    tag_coverage = len(tagged_files) / files_processed if files_processed > 0 else 0

    # Concentration analysis (Gini-like metric)
    concentration_score = calculate_concentration_score(usage_counts)

    return {
        "basic": basic_stats,
        "total_tags": total_tags,
        "total_tag_uses": total_tag_uses,
        "tag_distribution": {
            "singletons": {"count": singletons, "percentage": singletons/total_tags*100 if total_tags > 0 else 0},
            "doubletons": {"count": doubletons, "percentage": doubletons/total_tags*100 if total_tags > 0 else 0},
            "tripletons": {"count": tripletons, "percentage": tripletons/total_tags*100 if total_tags > 0 else 0},
            "frequent_tags": {"count": total_tags - singletons - doubletons - tripletons,
                            "percentage": (total_tags - singletons - doubletons - tripletons)/total_tags*100 if total_tags > 0 else 0}
        },
        "vault_health": {
            "tag_density": round(tag_density, 2),
            "tag_coverage": round(tag_coverage * 100, 1),
            "diversity_score": round(shannon_entropy, 2),
            "concentration_score": round(concentration_score, 2),
            "tagged_files": len(tagged_files),
            "untagged_files": files_processed - len(tagged_files)
        },
        "top_tags": tag_counts[:top_count],
        "usage_distribution": dict(sorted(usage_counter.items())[:20])  # Top 20 usage patterns
    }


def calculate_shannon_entropy(usage_counts):
    """Calculate Shannon entropy for tag diversity."""
    if not usage_counts:
        return 0

    total = sum(usage_counts)
    entropy = 0
    for count in usage_counts:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def calculate_concentration_score(usage_counts):
    """Calculate how concentrated tag usage is (0-1, where 1 is maximum concentration)."""
    if len(usage_counts) <= 1:
        return 1.0

    sorted_counts = sorted(usage_counts, reverse=True)
    total = sum(sorted_counts)

    # Calculate cumulative distribution
    cumulative = 0
    gini_sum = 0
    for i, count in enumerate(sorted_counts):
        cumulative += count
        gini_sum += (2 * (i + 1) - len(sorted_counts) - 1) * count

    if total == 0:
        return 0

    gini = gini_sum / (total * len(sorted_counts))
    return abs(gini)


def print_tag_statistics(stats, tag_types):
    """Print formatted tag statistics."""
    basic = stats["basic"]
    vault_health = stats["vault_health"]
    distribution = stats["tag_distribution"]

    print("Vault Tag Statistics")
    print("=" * 50)

    # Basic information
    print(f"\nVault Overview:")
    print(f"   Path: {basic['vault_path']}")
    print(f"   Tag types: {tag_types}")
    print(f"   Files processed: {basic['files_processed']:,}")
    print(f"   Processing errors: {basic['errors']}")

    # Core metrics
    print(f"\nTag Metrics:")
    print(f"   Total unique tags: {stats['total_tags']:,}")
    print(f"   Total tag uses: {stats['total_tag_uses']:,}")
    print(f"   Average tags per file: {vault_health['tag_density']}")

    # Coverage
    print(f"\nTag Coverage:")
    print(f"   Files with tags: {vault_health['tagged_files']:,} ({vault_health['tag_coverage']}%)")
    print(f"   Files without tags: {vault_health['untagged_files']:,}")

    # Distribution analysis
    print(f"\nTag Distribution:")
    print(f"   Singletons (used once): {distribution['singletons']['count']:,} ({distribution['singletons']['percentage']:.1f}%)")
    print(f"   Doubletons (used twice): {distribution['doubletons']['count']:,} ({distribution['doubletons']['percentage']:.1f}%)")
    print(f"   Tripletons (used 3x): {distribution['tripletons']['count']:,} ({distribution['tripletons']['percentage']:.1f}%)")
    print(f"   Frequent tags (4+ uses): {distribution['frequent_tags']['count']:,} ({distribution['frequent_tags']['percentage']:.1f}%)")

    # Health metrics
    print(f"\nVault Health:")
    print(f"   Diversity score: {vault_health['diversity_score']:.2f} (higher = more diverse)")
    print(f"   Concentration score: {vault_health['concentration_score']:.2f} (lower = more balanced)")

    # Health interpretation
    interpret_vault_health(vault_health, distribution, stats['total_tags'])

    # Top tags
    print(f"\nTop {len(stats['top_tags'])} Most Used Tags:")
    for i, (tag, count) in enumerate(stats['top_tags'], 1):
        percentage = count / stats['total_tag_uses'] * 100
        print(f"   {i:2d}. {tag:<20} {count:4d} uses ({percentage:4.1f}%)")

    # Usage patterns
    print(f"\nUsage Patterns:")
    usage_dist = stats['usage_distribution']
    for usage_count in sorted(usage_dist.keys())[:10]:  # Show first 10 patterns
        tag_count = usage_dist[usage_count]
        print(f"   {tag_count:3d} tags used {usage_count:2d}x each")


def interpret_vault_health(health, distribution, total_tags):
    """Provide health interpretation and recommendations."""
    print(f"\nHealth Assessment:")

    # Tag coverage assessment
    coverage = health['tag_coverage']
    if coverage >= 80:
        print("   + Excellent tag coverage - most files are tagged")
    elif coverage >= 60:
        print("   + Good tag coverage - majority of files tagged")
    elif coverage >= 40:
        print("   * Moderate tag coverage - consider tagging more files")
    else:
        print("   - Low tag coverage - many files lack tags")

    # Singleton analysis
    singleton_pct = distribution['singletons']['percentage']
    if singleton_pct >= 50:
        print("   - High singleton ratio - many tags used only once (consider consolidation)")
    elif singleton_pct >= 30:
        print("   * Moderate singleton ratio - some cleanup opportunities")
    else:
        print("   + Good tag reuse - low singleton ratio")

    # Diversity assessment
    diversity = health['diversity_score']
    if total_tags > 0:
        max_diversity = math.log2(total_tags)
        diversity_ratio = diversity / max_diversity if max_diversity > 0 else 0

        if diversity_ratio >= 0.8:
            print("   + High tag diversity - well-distributed usage")
        elif diversity_ratio >= 0.6:
            print("   + Good tag diversity - reasonably balanced")
        elif diversity_ratio >= 0.4:
            print("   * Moderate diversity - some tags dominate")
        else:
            print("   - Low diversity - heavily concentrated on few tags")


@analyze.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--max-items', type=int, default=10, help='Maximum items to show per section')
def quality(input_file, no_filter, format, max_items):
    """Analyze tag quality (overbroad tags, specificity).

    INPUT_FILE: JSON file containing tag data (from extract command)

    Identifies:
    - Overbroad tags (used too generally)
    - Tag specificity scores
    - Refinement suggestions
    """
    from .analysis.merge_analyzer import load_tag_data, build_tag_stats
    from .analysis.breadth_analyzer import analyze_tag_quality, format_quality_report
    import json

    filter_noise = not no_filter

    tag_data = load_tag_data(input_file)
    tag_stats = build_tag_stats(tag_data, filter_noise)

    # Get total files
    total_files = len(set(f for stats in tag_stats.values() for f in stats['files']))

    print(f"Analyzing tag quality for {len(tag_stats)} tags across {total_files} files...")

    analysis = analyze_tag_quality(tag_stats, total_files)

    if format == 'text':
        report = format_quality_report(analysis, tag_stats, max_items=max_items)
        print(report)
    elif format == 'json':
        # Convert sets to lists for JSON serialization
        json_analysis = {
            'overbroad_tags': analysis['overbroad_tags'],
            'summary': analysis['summary']
        }
        print(json.dumps(json_analysis, indent=2))


@analyze.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
@click.option('--min-similarity', type=float, default=0.7, help='Minimum context similarity threshold')
@click.option('--min-shared', type=int, default=3, help='Minimum shared files for co-occurrence')
def synonyms(input_file, no_filter, min_similarity, min_shared):
    """Detect potential synonym tags.

    INPUT_FILE: JSON file containing tag data (from extract command)

    Uses co-occurrence analysis to find tags that appear in similar contexts
    and are likely conceptual equivalents.
    """
    from .analysis.merge_analyzer import load_tag_data, build_tag_stats
    from .analysis.synonym_analyzer import detect_synonyms_by_context, find_acronym_expansions

    filter_noise = not no_filter

    tag_data = load_tag_data(input_file)
    tag_stats = build_tag_stats(tag_data, filter_noise)

    print(f"Analyzing {len(tag_stats)} tags for synonym relationships...")
    print(f"Minimum context similarity: {min_similarity}")
    print(f"Minimum shared files: {min_shared}\n")

    # Context-based synonyms
    synonym_candidates = detect_synonyms_by_context(
        tag_stats,
        min_shared_files=min_shared,
        similarity_threshold=min_similarity
    )

    if synonym_candidates:
        print("SYNONYM CANDIDATES (by context similarity):\n")
        for candidate in synonym_candidates[:20]:
            print(f"  {candidate['tag1']} ({candidate['tag1_count']} uses) ~ "
                  f"{candidate['tag2']} ({candidate['tag2_count']} uses)")
            print(f"    Context similarity: {candidate['context_similarity']:.2f}")
            print(f"    Shared context tags: {candidate['shared_context']}")
            print(f"    Suggestion: {candidate['suggestion']}")
            print()
    else:
        print("No synonym candidates found with current thresholds.\n")

    # Acronym expansions
    acronym_candidates = find_acronym_expansions(tag_stats)

    if acronym_candidates:
        print("\nACRONYM/EXPANSION CANDIDATES:\n")
        for candidate in acronym_candidates[:10]:
            print(f"  {candidate['acronym']} ({candidate['acronym_count']} uses) → "
                  f"{candidate['expansion']} ({candidate['expansion_count']} uses)")
            print(f"    File overlap: {candidate['overlap_ratio']:.1%}")
            print(f"    Suggestion: {candidate['suggestion']}")
            print()


@analyze.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
def plurals(input_file, no_filter):
    """Detect singular/plural variants.

    INPUT_FILE: JSON file containing tag data (from extract command)

    Uses enhanced plural detection including irregular plurals
    (child/children) and complex patterns (-ies/-y, -ves/-f).
    Convention: Prefers plural forms as canonical.
    """
    from .analysis.merge_analyzer import load_tag_data, build_tag_stats
    from tagex.utils.plural_normalizer import (
        normalize_plural_forms,
        normalize_compound_plurals,
        get_preferred_form
    )
    from collections import defaultdict

    filter_noise = not no_filter

    tag_data = load_tag_data(input_file)
    tag_stats = build_tag_stats(tag_data, filter_noise)

    print(f"Analyzing {len(tag_stats)} tags for plural variants...")
    print("Convention: Prefers plural forms as canonical\n")

    # Group tags by their plural forms
    variant_groups = defaultdict(set)

    for tag in tag_stats.keys():
        # Get all normalized forms
        forms = normalize_plural_forms(tag)
        forms.update(normalize_compound_plurals(tag))

        # Get preferred form (usually plural)
        # Pass usage counts to help with decision
        usage_counts = {t: tag_stats.get(t, {}).get('count', 0) for t in forms}
        canonical = get_preferred_form(forms, usage_counts)

        variant_groups[canonical].add(tag)

    # Filter to only groups with multiple variants
    variant_groups = {k: v for k, v in variant_groups.items() if len(v) > 1}

    if variant_groups:
        print(f"Found {len(variant_groups)} plural variant groups:\n")

        # Sort by total usage
        sorted_groups = sorted(
            variant_groups.items(),
            key=lambda x: sum(tag_stats[t]['count'] for t in x[1]),
            reverse=True
        )

        for canonical, variants in sorted_groups[:20]:
            print(f"  Group (canonical: {canonical}):")
            for tag in sorted(variants, key=lambda t: tag_stats[t]['count'], reverse=True):
                count = tag_stats[tag]['count']
                is_canonical = ' [preferred]' if tag == canonical else ''
                print(f"    - {tag} ({count} uses){is_canonical}")
            print(f"    → Suggestion: merge all into '{canonical}' (plural preferred)")
            print()
    else:
        print("No plural variant groups found.\n")


if __name__ == "__main__":
    main()