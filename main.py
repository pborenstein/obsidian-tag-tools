#!/usr/bin/env python3
"""
Obsidian Tag Extractor - Extract tags from Obsidian vault markdown files
"""
import logging
import sys
from pathlib import Path
import click

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
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='both', help='Tag types to process (default: both)')
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


if __name__ == "__main__":
    cli()
