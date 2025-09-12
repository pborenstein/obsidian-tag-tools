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
from operations.tag_operations import RenameOperation, MergeOperation, ApplyOperation


@click.group()
@click.version_option()
def cli():
    """TagEx - Extract and modify tags in Obsidian vaults."""
    pass


@cli.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path (default: stdout)')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'txt']), default='json', help='Output format')
@click.option('--exclude', multiple=True, help='Patterns to exclude (can be used multiple times)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress summary output')
@click.option('--no-filter', is_flag=True, help='Disable tag filtering (include all raw tags)')
def extract(vault_path, output, format, exclude, verbose, quiet, no_filter):
    """
    Extract tags from an Obsidian vault.
    
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
        extractor = TagExtractor(vault_path, exclude_patterns, filter_tags=not no_filter)
        
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
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('old_tag')
@click.argument('new_tag')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
def rename(vault_path, old_tag, new_tag, dry_run):
    """
    Rename a tag across all files in the vault.
    
    VAULT_PATH: Path to the Obsidian vault directory
    OLD_TAG: Tag to rename
    NEW_TAG: New tag name
    """
    operation = RenameOperation(vault_path, old_tag, new_tag, dry_run=dry_run)
    operation.run_operation()


@cli.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('source_tags', nargs=-1, required=True)
@click.option('--into', 'target_tag', required=True, help='Target tag to merge into')
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
def merge(vault_path, source_tags, target_tag, dry_run):
    """
    Merge multiple tags into a single tag.
    
    VAULT_PATH: Path to the Obsidian vault directory
    SOURCE_TAGS: Tags to merge (space-separated)
    """
    operation = MergeOperation(vault_path, list(source_tags), target_tag, dry_run=dry_run)
    operation.run_operation()


@cli.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('migration_file', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Preview changes without modifying files')
def apply(vault_path, migration_file, dry_run):
    """
    Apply tag migration mappings from a JSON file.
    
    VAULT_PATH: Path to the Obsidian vault directory
    MIGRATION_FILE: JSON file containing tag mappings
    """
    operation = ApplyOperation(vault_path, migration_file, dry_run=dry_run)
    operation.run_operation()




if __name__ == "__main__":
    cli()
