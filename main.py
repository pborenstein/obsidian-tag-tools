#!/usr/bin/env python3
"""
Obsidian Tag Extractor - Extract tags from Obsidian vault markdown files
"""
import logging
import sys
from pathlib import Path
import click
from collections import Counter
import math

from extractor.core import TagExtractor
from extractor.output_formatter import (
    format_as_plugin_json,
    format_as_csv,
    format_as_text,
    save_output,
    print_summary
)
from operations.tag_operations import RenameOperation, MergeOperation, DeleteOperation


@click.group()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.version_option()
@click.pass_context
def cli(ctx, vault_path, tag_types):
    """Obsidian Tag Management Tool - Extract and modify tags in Obsidian vaults.

    VAULT_PATH: Path to the Obsidian vault directory
    """
    # Store vault_path and tag_types in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj['vault_path'] = vault_path
    ctx.obj['tag_types'] = tag_types


@cli.command()
@click.option('--output', '-o', type=click.Path(), help='Output file path (default: stdout)')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'txt']), default='json', help='Output format')
@click.option('--exclude', multiple=True, help='Patterns to exclude (can be used multiple times)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress summary output')
@click.option('--no-filter', is_flag=True, help='Disable tag filtering (include all raw tags)')
@click.pass_context
def extract(ctx, output, format, exclude, verbose, quiet, no_filter):
    """Extract tags from the vault."""
    vault_path = ctx.obj['vault_path']
    tag_types = ctx.obj['tag_types']
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


@cli.command()
@click.argument('old_tag')
@click.argument('new_tag')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
@click.pass_context
def rename(ctx, old_tag, new_tag, dry_run):
    """Rename a tag across all files in the vault.

    OLD_TAG: Tag to rename
    NEW_TAG: New tag name
    """
    vault_path = ctx.obj['vault_path']
    tag_types = ctx.obj['tag_types']
    operation = RenameOperation(vault_path, old_tag, new_tag, dry_run=dry_run, tag_types=tag_types)
    operation.run_operation()


@cli.command()
@click.argument('source_tags', nargs=-1, required=True)
@click.option('--into', 'target_tag', required=True, help='Target tag to merge into')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
@click.pass_context
def merge(ctx, source_tags, target_tag, dry_run):
    """Merge multiple tags into a single tag.

    SOURCE_TAGS: Tags to merge (space-separated)
    """
    vault_path = ctx.obj['vault_path']
    tag_types = ctx.obj['tag_types']
    operation = MergeOperation(vault_path, list(source_tags), target_tag, dry_run=dry_run, tag_types=tag_types)
    operation.run_operation()


@cli.command()
@click.argument('tags_to_delete', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
@click.pass_context
def delete(ctx, tags_to_delete, dry_run):
    """Delete tags entirely from all files in the vault.

    TAGS_TO_DELETE: Tags to delete (space-separated)

    WARNING: This operation removes tags from both frontmatter and inline content.
    Use --dry-run first to preview changes. Inline tag deletion may affect readability.
    """
    vault_path = ctx.obj['vault_path']
    tag_types = ctx.obj['tag_types']
    operation = DeleteOperation(vault_path, list(tags_to_delete), dry_run=dry_run, tag_types=tag_types)
    operation.run_operation()


@cli.command()
@click.option('--top', '-t', type=int, default=20, help='Number of top tags to show (default: 20)')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--no-filter', is_flag=True, help='Disable tag filtering (include all raw tags)')
@click.pass_context
def stats(ctx, top, format, no_filter):
    """Display comprehensive tag statistics for the vault.

    Shows tag counts, distribution patterns, and vault health metrics.
    """
    vault_path = ctx.obj['vault_path']
    tag_types = ctx.obj['tag_types']

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


if __name__ == "__main__":
    cli()
