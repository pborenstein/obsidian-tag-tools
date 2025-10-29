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
from .core.operations.add_tags import AddTagsOperation


@click.group()
@click.version_option()
def main():
    """Obsidian Tag Management Tool - Extract and modify tags in Obsidian vaults."""
    pass


@main.group()
def tags():
    """Tag operations - extract, rename, merge, delete, and apply tag modifications."""
    pass


@tags.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.', required=False)
@click.option('--output', '-o', type=click.Path(), help='Output file path (default: stdout)')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'txt']), default='json', help='Output format')
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--exclude', multiple=True, help='Patterns to exclude (can be used multiple times)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress summary output')
@click.option('--no-filter', is_flag=True, help='Disable tag filtering (include all raw tags)')
def extract(vault_path, output, format, tag_types, exclude, verbose, quiet, no_filter):
    """Extract tags from the vault.

    VAULT_PATH: Path to the Obsidian vault directory (defaults to current directory)
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


@tags.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('old_tag')
@click.argument('new_tag')
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--execute', is_flag=True, help='REQUIRED to actually apply changes. Without this flag, runs in preview mode')
def rename(vault_path, old_tag, new_tag, tag_types, execute):
    """Rename a tag across all files in the vault.

    VAULT_PATH: Path to the Obsidian vault directory

    OLD_TAG: Tag to rename

    NEW_TAG: New tag name

    By default, runs in preview mode (dry-run). Use --execute to apply changes.
    """
    operation = RenameOperation(vault_path, old_tag, new_tag, dry_run=not execute, tag_types=tag_types)
    operation.run_operation()


@tags.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('source_tags', nargs=-1, required=True)
@click.option('--into', 'target_tag', required=True, help='Target tag to merge into')
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--execute', is_flag=True, help='REQUIRED to actually apply changes. Without this flag, runs in preview mode')
def merge(vault_path, source_tags, target_tag, tag_types, execute):
    """Merge multiple tags into a single tag.

    VAULT_PATH: Path to the Obsidian vault directory

    SOURCE_TAGS: Tags to merge (space-separated)

    By default, runs in preview mode (dry-run). Use --execute to apply changes.
    """
    operation = MergeOperation(vault_path, list(source_tags), target_tag, dry_run=not execute, tag_types=tag_types)
    operation.run_operation()


@tags.command()
@click.argument('operations_file', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.option('--vault-path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.', help='Vault path (defaults to current directory)')
@click.option('--execute', is_flag=True, help='REQUIRED to actually apply changes. Without this flag, runs in preview mode (dry-run)')
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
def apply(operations_file, vault_path, execute, tag_types):
    """Apply tag operations from a YAML operations file.

    OPERATIONS_FILE: Path to YAML file containing operations (generated by 'tagex analyze recommendations')

    Reads the operations file and executes all enabled operations in order.
    Each operation type (merge, rename, delete) is applied to the vault.

    Operations are executed sequentially in the order they appear in the file.

    SAFETY: Runs in preview mode (dry-run) by default. Use --execute to actually modify files.
    """
    import yaml
    from pathlib import Path

    # Load operations file
    ops_file = Path(operations_file)
    if not ops_file.exists():
        print(f"Error: Operations file not found: {operations_file}")
        sys.exit(1)

    with open(ops_file, 'r', encoding='utf-8') as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error: Invalid YAML file: {e}")
            sys.exit(1)

    operations = data.get('operations', [])
    if not operations:
        print("No operations found in file.")
        return

    # Determine vault path
    if not vault_path:
        vault_path = str(Path.cwd())
        print(f"Using current directory as vault: {vault_path}")

    # Filter to enabled operations only
    enabled_ops = [op for op in operations if op.get('enabled', True)]

    print(f"\nLoaded {len(operations)} operations from: {operations_file}")
    print(f"Enabled operations: {len(enabled_ops)}")
    print(f"Disabled operations: {len(operations) - len(enabled_ops)}")

    # Dry-run is the default - execute flag turns it off
    dry_run = not execute

    # Big obvious header
    print("\n" + "="*70)
    if dry_run:
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║                    PREVIEW MODE (DRY-RUN)                            ║")
        print("║                  No files will be modified                           ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
    else:
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║                      EXECUTION MODE                                  ║")
        print("║                  Files WILL be modified                              ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
    print("="*70)

    print(f"Vault: {vault_path}")
    print(f"Tag types: {tag_types}")
    print(f"Operations: {len(enabled_ops)}")
    print("="*70 + "\n")

    # Track results for summary
    total_files_modified = 0
    total_tags_modified = 0
    errors = []

    # Execute each enabled operation
    for i, op in enumerate(enabled_ops, 1):
        op_type = op.get('type')
        source_tags = op.get('source', [])
        target_tag = op.get('target')
        reason = op.get('reason', '')

        # Compact single-line progress indicator
        sources_str = ', '.join(source_tags) if len(source_tags) <= 2 else f"{source_tags[0]}, ... ({len(source_tags)} tags)"
        print(f"[{i:3}/{len(enabled_ops)}] {op_type.upper():6} {sources_str:30} → {target_tag:20}", end=' ', flush=True)

        try:
            if op_type == 'merge':
                operation = MergeOperation(
                    vault_path=vault_path,
                    source_tags=source_tags,
                    target_tag=target_tag,
                    dry_run=dry_run,
                    tag_types=tag_types,
                    quiet=True
                )
                result = operation.run_operation()

            elif op_type == 'rename':
                if len(source_tags) != 1:
                    print(f"✗ Error: Rename requires exactly 1 source tag")
                    errors.append(f"Operation {i}: Rename requires exactly 1 source tag")
                    continue

                operation = RenameOperation(
                    vault_path=vault_path,
                    old_tag=source_tags[0],
                    new_tag=target_tag,
                    dry_run=dry_run,
                    tag_types=tag_types,
                    quiet=True
                )
                result = operation.run_operation()

            elif op_type == 'delete':
                operation = DeleteOperation(
                    vault_path=vault_path,
                    tags_to_delete=source_tags,
                    dry_run=dry_run,
                    tag_types=tag_types,
                    quiet=True
                )
                result = operation.run_operation()

            elif op_type == 'add_tags':
                # For add_tags, target_tag contains the file path
                # and source_tags contains the tags to add
                file_path = target_tag
                tags_to_add = source_tags

                # Create file_tag_map for AddTagsOperation
                file_tag_map = {file_path: tags_to_add}

                operation = AddTagsOperation(
                    vault_path=vault_path,
                    file_tag_map=file_tag_map,
                    dry_run=dry_run,
                    tag_types='frontmatter',  # add_tags only supports frontmatter
                    quiet=True
                )
                result = operation.run_operation()

            else:
                print(f"✗ Unknown operation type")
                errors.append(f"Operation {i}: Unknown operation type: {op_type}")
                continue

            # Show brief results on same line
            stats = result['stats']
            total_files_modified += stats['files_modified']
            total_tags_modified += stats['tags_modified']

            if stats['errors'] > 0:
                print(f"⚠ {stats['files_modified']}f {stats['tags_modified']}t {stats['errors']}err")
                errors.append(f"Operation {i}: {stats['errors']} errors occurred")
            else:
                print(f"✓ {stats['files_modified']}f {stats['tags_modified']}t")

        except Exception as e:
            print(f"✗ Error: {e}")
            errors.append(f"Operation {i}: {e}")

    print("\n" + "="*70)
    print(f"SUMMARY: {len(enabled_ops)} operations processed")
    print(f"  Files modified: {total_files_modified}")
    print(f"  Tags modified:  {total_tags_modified}")
    if errors:
        print(f"  Errors:         {len(errors)}")
        print("\nErrors encountered:")
        for err in errors:
            print(f"  - {err}")
    print("="*70)

    if dry_run:
        print("\n" + "="*70)
        print("PREVIEW COMPLETE - No files were modified")
        print("="*70)
        print(f"\nTo apply these changes, run:")
        vault_arg = f" --vault-path {vault_path}" if vault_path != str(Path.cwd()) else ""
        print(f"  tagex apply {operations_file}{vault_arg} --execute")
    else:
        print("\n" + "="*70)
        print("EXECUTION COMPLETE - Files have been modified")
        print("="*70)


@tags.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument('tags_to_delete', nargs=-1, required=True)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--execute', is_flag=True, help='REQUIRED to actually apply changes. Without this flag, runs in preview mode')
def delete(vault_path, tags_to_delete, tag_types, execute):
    """Delete tags entirely from all files in the vault.

    VAULT_PATH: Path to the Obsidian vault directory

    TAGS_TO_DELETE: Tags to delete (space-separated)

    WARNING: This operation removes tags from both frontmatter and inline content.
    By default, runs in preview mode (dry-run). Use --execute to apply changes.
    Inline tag deletion may affect readability.
    """
    operation = DeleteOperation(vault_path, list(tags_to_delete), dry_run=not execute, tag_types=tag_types)
    operation.run_operation()


@tags.command('fix-duplicates')
@click.argument('vault_path', type=click.Path(exists=True), default='.', required=False)
@click.option('--filelist', type=click.Path(), help='Text file containing list of files to process')
@click.option('--execute', is_flag=True, help='REQUIRED to actually apply changes. Without this flag, runs in preview mode')
@click.option('--recursive/--no-recursive', default=True, help='Search subdirectories (default: recursive)')
@click.option('--quiet', is_flag=True, help='Reduce output verbosity')
@click.option('--log', type=click.Path(), help='Save log to file')
def fix_duplicates(vault_path, filelist, execute, recursive, quiet, log):
    """Fix duplicate 'tags:' fields in frontmatter.

    VAULT_PATH: Path to Obsidian vault directory (defaults to current directory)

    Consolidates multiple 'tags:' fields into a single field in YAML frontmatter.
    Creates .bak backups before modification.

    By default, runs in preview mode (dry-run). Use --execute to apply changes.
    """
    from .core.operations.fix_duplicates import run_operation

    try:
        stats = run_operation(
            vault_path=vault_path,
            filelist=filelist,
            execute=execute,
            recursive=recursive,
            quiet=quiet,
            log_file=log
        )

        # Exit with error code if there were errors
        if stats['errors'] > 0:
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@main.group()
def vault():
    """Vault maintenance operations - cleanup, repair, and validation."""
    pass


@vault.command('cleanup-backups')
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--execute', is_flag=True, help='REQUIRED to actually delete files. Without this flag, runs in preview mode')
@click.option('--recursive/--no-recursive', default=True, help='Search subdirectories (default: recursive)')
@click.option('--quiet', is_flag=True, help='Reduce output verbosity')
def cleanup_backups(vault_path, execute, recursive, quiet):
    """Remove .bak backup files from vault.

    VAULT_PATH: Path to Obsidian vault directory

    Finds and removes all .bak files created by fix operations.

    By default, runs in preview mode (dry-run). Use --execute to actually delete files.
    """
    from .utils.vault_maintenance import run_cleanup

    try:
        stats = run_cleanup(
            vault_path=vault_path,
            execute=execute,
            recursive=recursive,
            quiet=quiet
        )

        # Exit with error code if there were errors
        if stats['errors'] > 0:
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


@main.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.', required=False)
@click.option('--force', '-f', is_flag=True, help='Overwrite existing configuration directory')
def init(vault_path, force):
    """Initialize tagex configuration in a vault.

    VAULT_PATH: Path to the Obsidian vault directory (defaults to current directory)

    Creates .tagex/ directory with:
    - config.yaml: General configuration (plural preference, etc.)
    - synonyms.yaml: Tag synonym definitions
    - README.md: Documentation for the configuration files
    """
    from pathlib import Path
    import shutil

    vault = Path(vault_path)
    tagex_dir = vault / '.tagex'

    # Check for existing directory
    if tagex_dir.exists() and not force:
        print(f"Configuration directory already exists: {tagex_dir}")
        print("\nUse --force to overwrite existing configuration")
        sys.exit(1)

    # Get the template files from the package
    package_dir = Path(__file__).parent
    template_dir = package_dir / 'templates' / '.tagex'

    if not template_dir.exists():
        print(f"Error: Template directory not found: {template_dir}")
        sys.exit(1)

    # Create .tagex directory
    tagex_dir.mkdir(exist_ok=True)

    # Copy template files
    files_created = []

    config_template = template_dir / 'config.yaml'
    if config_template.exists():
        shutil.copy(config_template, tagex_dir / 'config.yaml')
        files_created.append('config.yaml')

    synonyms_template = template_dir / 'synonyms.yaml'
    if synonyms_template.exists():
        shutil.copy(synonyms_template, tagex_dir / 'synonyms.yaml')
        files_created.append('synonyms.yaml')

    # Create exclusions.yaml using template
    from tagex.config.exclusions_config import ExclusionsConfig
    ExclusionsConfig.create_template(vault)
    files_created.append('exclusions.yaml')

    # Create README
    readme_content = """# Tagex Configuration

This directory contains configuration files for tagex, a tag management tool for Obsidian vaults.

## Configuration Files

### config.yaml
General configuration for tag processing behavior.

Key settings:
- **plural.preference**: How to choose between singular/plural variants
  - `usage`: Prefer most-used form (default)
  - `plural`: Always prefer plural forms
  - `singular`: Always prefer singular forms
- **plural.usage_ratio_threshold**: Minimum usage ratio for preference (default: 2.0)

### synonyms.yaml
Defines synonym relationships between tags.

Format:
```yaml
canonical-tag:
  - synonym1
  - synonym2
```

When tagex analyzes your vault, it will recognize these relationships and suggest merges.

### exclusions.yaml
Lists tags that should be excluded from merge/synonym suggestions.

Format:
```yaml
exclude_tags:
  - spain
  - france
  - proper-noun-tag
```

Tags in this list will never be suggested for merging, even if they have high semantic similarity.
Useful for proper nouns, country names, author names, etc.

## Using the Configuration

Configuration is automatically loaded when you run tagex commands on this vault:

```bash
# Uses vault's configuration
tagex analyze plurals /path/to/vault

# Override configuration with command-line option
tagex analyze plurals /path/to/vault --prefer plural
```

## Validation

To check if your configuration files are valid:

```bash
tagex validate /path/to/vault
```

## Documentation

For more information, see:
- [Main Documentation](https://github.com/yourusername/tagex/docs)
- [Configuration Guide](https://github.com/yourusername/tagex/docs/CONFIGURATION.md)
"""

    readme_file = tagex_dir / 'README.md'
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    files_created.append('README.md')

    # Print success message
    print(f"\nInitialized tagex configuration in: {vault_path}")
    print(f"\nCreated directory: .tagex/")
    print("\nCreated files:")
    for f in files_created:
        print(f"  ✓ .tagex/{f}")

    print("\nNext steps:")
    print(f"  1. Edit .tagex/config.yaml to set your preferences")
    print(f"  2. Edit .tagex/synonyms.yaml to define tag synonyms")
    print(f"  3. Edit .tagex/exclusions.yaml to exclude tags (optional)")
    print("  4. Run: tagex validate " + str(vault_path))
    print("  5. Run: tagex analyze recommendations " + str(vault_path))


@main.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.', required=False)
@click.option('--strict', is_flag=True, help='Treat warnings as errors')
def validate(vault_path, strict):
    """Validate tagex configuration in a vault.

    VAULT_PATH: Path to the Obsidian vault directory (defaults to current directory)

    Checks:
    - Configuration file syntax (YAML validity)
    - Synonym file syntax and structure
    - Configuration value ranges and types
    - Tag references (warnings for undefined tags)
    """
    from pathlib import Path
    import yaml

    vault = Path(vault_path)
    tagex_dir = vault / '.tagex'

    errors = []
    warnings = []

    print(f"Validating tagex configuration in: {vault_path}\n")

    # Check if .tagex directory exists
    if not tagex_dir.exists():
        warnings.append(".tagex/ directory not found")
        print("⚠ No configuration found")
        print(f"\nRun: tagex init {vault_path}")
        if strict:
            sys.exit(1)
        return

    # Define file paths
    config_file = tagex_dir / 'config.yaml'
    synonyms_file = tagex_dir / 'synonyms.yaml'

    # Validate config file
    if config_file.exists():
        print("Checking .tagex/config.yaml...")
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)

            if config_data is None:
                warnings.append("config.yaml is empty")
            else:
                # Validate plural configuration
                if 'plural' in config_data:
                    plural_config = config_data['plural']

                    # Check preference value
                    if 'preference' in plural_config:
                        pref = plural_config['preference']
                        if pref not in ['usage', 'plural', 'singular']:
                            errors.append(f"Invalid plural.preference: '{pref}' (must be 'usage', 'plural', or 'singular')")

                    # Check usage_ratio_threshold
                    if 'usage_ratio_threshold' in plural_config:
                        ratio = plural_config['usage_ratio_threshold']
                        if not isinstance(ratio, (int, float)):
                            errors.append(f"Invalid plural.usage_ratio_threshold: must be a number")
                        elif ratio <= 0:
                            errors.append(f"Invalid plural.usage_ratio_threshold: must be > 0")

            print("  ✓ YAML syntax valid")

        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error in config.yaml: {e}")
        except Exception as e:
            errors.append(f"Error reading config.yaml: {e}")
    else:
        warnings.append("config.yaml not found (using defaults)")

    # Validate synonyms file
    if synonyms_file.exists():
        print("Checking .tagex/synonyms.yaml...")
        try:
            with open(synonyms_file, 'r') as f:
                synonyms_data = yaml.safe_load(f)

            if synonyms_data is None:
                warnings.append("synonyms.yaml is empty")
            elif not isinstance(synonyms_data, dict):
                errors.append("synonyms.yaml must contain a dictionary")
            else:
                # Validate structure
                canonical_tags = set()
                synonym_tags = set()

                for canonical, synonyms in synonyms_data.items():
                    if not isinstance(canonical, str):
                        errors.append(f"Invalid canonical tag (must be string): {canonical}")
                        continue

                    canonical_tags.add(canonical)

                    if not isinstance(synonyms, list):
                        errors.append(f"Synonyms for '{canonical}' must be a list")
                        continue

                    for syn in synonyms:
                        if not isinstance(syn, str):
                            errors.append(f"Invalid synonym for '{canonical}' (must be string): {syn}")
                        elif syn in synonym_tags:
                            errors.append(f"Duplicate synonym definition: '{syn}' appears multiple times")
                        else:
                            synonym_tags.add(syn)

                # Check for conflicts (canonical tag also listed as synonym)
                conflicts = canonical_tags & synonym_tags
                if conflicts:
                    for tag in conflicts:
                        errors.append(f"Conflict: '{tag}' is both canonical and synonym")

                print(f"  ✓ YAML syntax valid")
                print(f"  ✓ Found {len(canonical_tags)} canonical tags")
                print(f"  ✓ Found {len(synonym_tags)} synonym mappings")

        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error in synonyms.yaml: {e}")
        except Exception as e:
            errors.append(f"Error reading synonyms.yaml: {e}")
    else:
        warnings.append("synonyms.yaml not found")

    # Print results
    print()
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  ⚠ {w}")
        print()

    if errors:
        print("Errors:")
        for e in errors:
            print(f"  ✗ {e}")
        print("\nValidation FAILED")
        sys.exit(1)
    elif warnings and strict:
        print("Validation FAILED (strict mode)")
        sys.exit(1)
    else:
        print("✓ Validation PASSED")
        print("\nConfiguration is valid and ready to use.")


@main.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.', required=False)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--top', '-t', type=int, default=20, help='Number of top tags to show (default: 20)')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--no-filter', is_flag=True, help='Disable tag filtering (include all raw tags)')
def stats(vault_path, tag_types, top, format, no_filter):
    """Display comprehensive tag statistics for the vault.

    VAULT_PATH: Path to the Obsidian vault directory (defaults to current directory)

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


@main.command()
@click.argument('vault_path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.', required=False)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to process (default: frontmatter)')
@click.option('--no-filter', is_flag=True, help='Disable tag filtering (include all raw tags)')
def health(vault_path, tag_types, no_filter):
    """Generate comprehensive vault health report.

    VAULT_PATH: Path to the Obsidian vault directory (defaults to current directory)

    Runs all analyses and generates a unified report with:
    - Critical issues requiring immediate attention
    - Moderate issues for cleanup
    - Recommended actions prioritized by impact
    - Overall vault health score
    """
    from .core.extractor.core import TagExtractor
    from .analysis.merge_analyzer import build_tag_stats, suggest_merges
    from .analysis.plural_normalizer import normalize_plural_forms, normalize_compound_plurals, get_preferred_form
    from .config.plural_config import PluralConfig
    from .core.extractor.output_formatter import format_as_plugin_json
    from collections import defaultdict
    import argparse

    print(f"Analyzing vault health: {vault_path}\n")
    print("=" * 70)

    filter_tags = not no_filter

    # Extract tags
    print("\n1. Extracting tags...")
    extractor = TagExtractor(vault_path, filter_tags=filter_tags, tag_types=tag_types)
    tag_data_dict = extractor.extract_tags()
    tag_data = format_as_plugin_json(tag_data_dict)
    tag_stats = build_tag_stats(tag_data, filter_tags)
    basic_stats = extractor.get_statistics()

    total_tags = len(tag_stats)
    total_files = basic_stats['files_processed']

    print(f"   Found {total_tags} unique tags across {total_files} files")

    # Analyze plural variants
    print("\n2. Analyzing plural/singular variants...")
    config = PluralConfig.from_vault(vault_path)
    variant_groups = defaultdict(set)

    for tag in tag_stats.keys():
        forms = normalize_plural_forms(tag)
        forms.update(normalize_compound_plurals(tag))
        usage_counts = {t: tag_stats.get(t, {}).get('count', 0) for t in forms}
        canonical = get_preferred_form(forms, usage_counts, config.preference.value, config.usage_ratio_threshold)
        variant_groups[canonical].add(tag)

    plural_groups = {k: v for k, v in variant_groups.items() if len(v) > 1}
    plural_merges = sum(len(variants) - 1 for variants in plural_groups.values())

    print(f"   Found {len(plural_groups)} plural variant groups")
    print(f"   Potential merges: {plural_merges}")

    # Analyze merge opportunities
    print("\n3. Analyzing merge opportunities...")
    args = argparse.Namespace(no_sklearn=False)
    merge_suggestions = suggest_merges(tag_stats, min_usage=2, args=args)

    # Count suggestions by type
    similar_count = len(merge_suggestions.get('similar_names', []))
    semantic_count = len(merge_suggestions.get('semantic_duplicates', []))
    overlap_count = len(merge_suggestions.get('high_file_overlap', []))
    variant_count = len(merge_suggestions.get('variant_patterns', []))

    total_merge_suggestions = similar_count + semantic_count + overlap_count + variant_count

    print(f"   Similar names: {similar_count}")
    print(f"   Semantic duplicates: {semantic_count}")
    print(f"   High file overlap: {overlap_count}")
    print(f"   Variant patterns: {variant_count}")

    # Calculate health metrics
    print("\n4. Calculating vault health metrics...")

    # Singleton ratio (tags used only once)
    singletons = sum(1 for stats in tag_stats.values() if stats['count'] == 1)
    singleton_ratio = singletons / total_tags if total_tags > 0 else 0

    # Tag coverage (files with tags)
    tagged_files = set()
    for stats in tag_stats.values():
        tagged_files.update(stats['files'])
    tag_coverage = len(tagged_files) / total_files if total_files > 0 else 0

    # Generate health score (0-100)
    health_score = 100
    # Deduct for high singleton ratio
    if singleton_ratio > 0.5:
        health_score -= 20
    elif singleton_ratio > 0.3:
        health_score -= 10

    # Deduct for low tag coverage
    if tag_coverage < 0.4:
        health_score -= 20
    elif tag_coverage < 0.6:
        health_score -= 10

    # Deduct for cleanup opportunities
    cleanup_potential = plural_merges + total_merge_suggestions
    if cleanup_potential > total_tags * 0.3:
        health_score -= 20
    elif cleanup_potential > total_tags * 0.15:
        health_score -= 10

    # Print report
    print("\n" + "=" * 70)
    print("VAULT HEALTH REPORT")
    print("=" * 70)

    # Overall score
    print(f"\nOVERALL HEALTH SCORE: {health_score}/100")
    if health_score >= 80:
        print("Status: Excellent - Well-maintained tag structure")
    elif health_score >= 60:
        print("Status: Good - Some cleanup opportunities")
    elif health_score >= 40:
        print("Status: Fair - Moderate cleanup needed")
    else:
        print("Status: Needs Attention - Significant cleanup recommended")

    # Critical Issues
    critical_issues = []
    if singleton_ratio > 0.5:
        critical_issues.append(f"High singleton ratio ({singleton_ratio:.1%}) - many tags used only once")
    if tag_coverage < 0.4:
        critical_issues.append(f"Low tag coverage ({tag_coverage:.1%}) - many files lack tags")

    if critical_issues:
        print("\nCRITICAL ISSUES (fix first):")
        for i, issue in enumerate(critical_issues, 1):
            print(f"  {i}. {issue}")

    # Moderate Issues
    moderate_issues = []
    if 0.3 <= singleton_ratio <= 0.5:
        moderate_issues.append(f"Moderate singleton ratio ({singleton_ratio:.1%})")
    if plural_merges > 0:
        moderate_issues.append(f"{plural_merges} plural/singular variants to consolidate")
    if total_merge_suggestions > 0:
        moderate_issues.append(f"{total_merge_suggestions} potential tag merges")

    if moderate_issues:
        print("\nMODERATE ISSUES:")
        for i, issue in enumerate(moderate_issues, 1):
            print(f"  {i}. {issue}")

    # Recommended Actions
    print("\nRECOMMENDED ACTIONS (prioritized by impact):")
    action_num = 1

    if plural_merges > 5:
        print(f"  {action_num}. Consolidate plural/singular variants")
        print(f"     Run: tagex analyze plurals {vault_path}")
        action_num += 1

    if total_merge_suggestions > 5:
        print(f"  {action_num}. Review merge suggestions")
        print(f"     Run: tagex analyze merge {vault_path}")
        action_num += 1

    if singleton_ratio > 0.3:
        print(f"  {action_num}. Review singleton tags (used only once)")
        print(f"     Run: tagex stats {vault_path}")
        action_num += 1

    if tag_coverage < 0.6:
        print(f"  {action_num}. Increase tag coverage by tagging more files")
        print(f"     Currently: {tag_coverage:.1%} of files have tags")
        action_num += 1

    print("\n" + "=" * 70)
    print("\nFor detailed analysis, run individual analyze commands:")
    print(f"  tagex analyze plurals {vault_path}")
    print(f"  tagex analyze merge {vault_path}")
    print(f"  tagex analyze quality {vault_path}")
    print(f"  tagex analyze synonyms {vault_path}")


@main.group()
def analyze():
    """Analyze tag relationships and suggest improvements.

    Provides insights into tag usage patterns, co-occurrence, and merge opportunities.
    """
    pass


@analyze.command()
@click.argument('input_path', type=click.Path(exists=True), default='.', required=False)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to extract (when input is vault)')
@click.option('--min-pairs', type=int, default=2, help='Minimum pair threshold')
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
def pairs(input_path, tag_types, min_pairs, no_filter):
    """Analyze tag pair patterns and co-occurrence.

    INPUT_PATH: Vault directory or JSON file containing tag data (defaults to current directory)
    """
    from .analysis.pair_analyzer import analyze_tag_relationships, find_tag_clusters
    from .utils.input_handler import load_or_extract_tags, get_input_type
    from collections import defaultdict

    filter_noise = not no_filter

    # Show which mode we're using
    input_type = get_input_type(input_path)
    if input_type == 'vault':
        print(f"Extracting tags from vault: {input_path}")
        print(f"Tag types: {tag_types}\n")
    else:
        print(f"Loading tags from JSON: {input_path}\n")

    tag_data = load_or_extract_tags(input_path, tag_types, filter_noise)
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
@click.argument('input_path', type=click.Path(exists=True), default='.' ,required=False)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to extract (when input is vault)')
@click.option('--min-usage', type=int, default=3, help='Minimum tag usage to consider')
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
@click.option('--no-sklearn', is_flag=True, help='Force use of pattern-based fallback instead of embeddings')
def analyze_merge(input_path, tag_types, min_usage, no_filter, no_sklearn):
    """Suggest tag merge opportunities.

    INPUT_PATH: Vault directory or JSON file containing tag data (defaults to current directory)

    Identifies potential tag merges using multiple approaches:
    - Similar names (string similarity)
    - Semantic duplicates (TF-IDF embeddings)
    - High file overlap
    - Variant patterns (plural/singular, tenses)
    """
    from .analysis.merge_analyzer import build_tag_stats, suggest_merges, print_merge_suggestions
    from .utils.input_handler import load_or_extract_tags, get_input_type
    from .config.exclusions_config import ExclusionsConfig
    from pathlib import Path
    import argparse

    filter_noise = not no_filter

    # Show which mode we're using
    input_type = get_input_type(input_path)
    if input_type == 'vault':
        print(f"Extracting tags from vault: {input_path}")
        print(f"Tag types: {tag_types}\n")
        vault_path = Path(input_path)
    else:
        print(f"Loading tags from JSON: {input_path}\n")
        vault_path = None

    tag_data = load_or_extract_tags(input_path, tag_types, filter_noise)
    tag_stats = build_tag_stats(tag_data, filter_noise)

    # Load exclusions configuration
    exclusions = ExclusionsConfig(vault_path)
    excluded_tags = exclusions.get_all_exclusions()
    if excluded_tags:
        print(f"Loaded {len(excluded_tags)} excluded tags from .tagex/exclusions.yaml")

    print(f"Analyzing {len(tag_stats)} tags for merge opportunities...")
    print(f"Minimum usage threshold: {min_usage}")

    # Create a minimal args object for the suggest_merges function
    args = argparse.Namespace(no_sklearn=no_sklearn)

    suggestions = suggest_merges(tag_stats, min_usage, args)

    # Filter excluded tags from suggestions
    if excluded_tags:
        filtered_suggestions = []
        excluded_count = 0
        for group in suggestions:
            # Check if any tag in the group is excluded
            all_tags = group['similar_tags'] + [group['representative']]
            if any(exclusions.is_excluded(tag) for tag in all_tags):
                excluded_count += 1
                continue
            filtered_suggestions.append(group)

        suggestions = filtered_suggestions
        if excluded_count > 0:
            print(f"\nFiltered out {excluded_count} suggestion groups involving excluded tags\n")

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
@click.argument('input_path', type=click.Path(exists=True), default='.' ,required=False)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to extract (when input is vault)')
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--max-items', type=int, default=10, help='Maximum items to show per section')
def quality(input_path, tag_types, no_filter, format, max_items):
    """Analyze tag quality (overbroad tags, specificity).

    INPUT_PATH: Vault directory or JSON file containing tag data (defaults to current directory)

    Identifies:
    - Overbroad tags (used too generally)
    - Tag specificity scores
    - Refinement suggestions
    """
    from .analysis.merge_analyzer import build_tag_stats
    from .analysis.breadth_analyzer import analyze_tag_quality, format_quality_report
    from .utils.input_handler import load_or_extract_tags, get_input_type
    import json

    filter_noise = not no_filter

    # Show which mode we're using
    input_type = get_input_type(input_path)
    if input_type == 'vault':
        print(f"Extracting tags from vault: {input_path}")
        print(f"Tag types: {tag_types}\n")
    else:
        print(f"Loading tags from JSON: {input_path}\n")

    tag_data = load_or_extract_tags(input_path, tag_types, filter_noise)
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
@click.argument('input_path', type=click.Path(exists=True), default='.' ,required=False)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to extract (when input is vault)')
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
@click.option('--min-similarity', type=float, default=0.7, help='Minimum semantic similarity threshold (0.0-1.0)')
@click.option('--show-related', is_flag=True, help='Also show related tags (co-occurrence based)')
@click.option('--no-transformers', is_flag=True, help='Skip semantic analysis (faster, co-occurrence only)')
def synonyms(input_path, tag_types, no_filter, min_similarity, show_related, no_transformers):
    """Detect synonym tags using semantic similarity.

    INPUT_PATH: Vault directory or JSON file containing tag data (defaults to current directory)

    Uses sentence-transformers to find tags with similar MEANINGS:
    - "tech" vs "technology"
    - "ml" vs "machine-learning"
    - "python" vs "py"

    True synonyms are ALTERNATIVES (not used together), unlike related tags
    which co-occur frequently.

    Use --show-related to also see related tags based on co-occurrence patterns.
    """
    from .analysis.merge_analyzer import build_tag_stats
    from .analysis.synonym_analyzer import (
        detect_synonyms_by_semantics,
        detect_related_tags,
        find_acronym_expansions
    )
    from .utils.input_handler import load_or_extract_tags, get_input_type
    from .config.exclusions_config import ExclusionsConfig
    from pathlib import Path

    filter_noise = not no_filter

    # Show which mode we're using
    input_type = get_input_type(input_path)
    if input_type == 'vault':
        print(f"Extracting tags from vault: {input_path}")
        print(f"Tag types: {tag_types}\n")
        vault_path = Path(input_path)
    else:
        print(f"Loading tags from JSON: {input_path}\n")
        vault_path = None

    tag_data = load_or_extract_tags(input_path, tag_types, filter_noise)
    tag_stats = build_tag_stats(tag_data, filter_noise)

    # Load exclusions configuration
    exclusions = ExclusionsConfig(vault_path)
    excluded_tags = exclusions.get_all_exclusions()
    if excluded_tags:
        print(f"Loaded {len(excluded_tags)} excluded tags from .tagex/exclusions.yaml\n")

    print(f"Analyzing {len(tag_stats)} tags for synonyms...\n")

    # Semantic synonym detection (the real thing)
    if not no_transformers:
        try:
            print("=" * 70)
            print("SEMANTIC SYNONYMS (tags with similar meanings)")
            print("=" * 70)
            print(f"Minimum similarity: {min_similarity}\n")

            synonym_candidates = detect_synonyms_by_semantics(
                tag_stats,
                similarity_threshold=min_similarity
            )

            # Filter excluded tags
            if excluded_tags:
                filtered_candidates = []
                excluded_count = 0
                for candidate in synonym_candidates:
                    # Check if any tag in the pair is excluded
                    if (exclusions.is_excluded(candidate['tag1']) or
                        exclusions.is_excluded(candidate['tag2'])):
                        excluded_count += 1
                        continue
                    filtered_candidates.append(candidate)

                synonym_candidates = filtered_candidates
                if excluded_count > 0:
                    print(f"  Filtered out {excluded_count} suggestions involving excluded tags\n")

            if synonym_candidates:
                for candidate in synonym_candidates[:20]:
                    print(f"  {candidate['tag1']} ({candidate['tag1_count']} uses) ≈ "
                          f"{candidate['tag2']} ({candidate['tag2_count']} uses)")
                    print(f"    Semantic similarity: {candidate['semantic_similarity']:.3f}")
                    print(f"    Co-occurrence ratio: {candidate['co_occurrence_ratio']:.1%}")
                    print(f"    Suggestion: {candidate['suggestion']}")
                    print()
            else:
                print("No semantic synonyms found with current threshold.\n")

        except ImportError as e:
            print(f"⚠ {e}")
            print("\nFalling back to co-occurrence analysis...\n")
            no_transformers = True

    # Related tags (co-occurrence based) - optional
    if show_related or no_transformers:
        print("\n" + "=" * 70)
        print("RELATED TAGS (co-occurrence patterns)")
        print("=" * 70)
        print("Note: These tags appear TOGETHER (related topics), not synonyms\n")

        related_candidates = detect_related_tags(
            tag_stats,
            min_shared_files=3,
            similarity_threshold=0.7,
            min_context_tags=5
        )

        # Filter excluded tags
        if excluded_tags and related_candidates:
            filtered_related = []
            for candidate in related_candidates:
                # Check if any tag in the pair is excluded
                if (exclusions.is_excluded(candidate['tag1']) or
                    exclusions.is_excluded(candidate['tag2'])):
                    continue
                filtered_related.append(candidate)
            related_candidates = filtered_related

        if related_candidates:
            for candidate in related_candidates[:20]:
                print(f"  {candidate['tag1']} ({candidate['tag1_count']} uses) + "
                      f"{candidate['tag2']} ({candidate['tag2_count']} uses)")
                print(f"    Context similarity: {candidate['context_similarity']:.2f}")
                print(f"    Shared context tags: {candidate['shared_context']}")
                print()
        else:
            print("No related tag patterns found.\n")

    # Acronym expansions
    acronym_candidates = find_acronym_expansions(tag_stats)

    if acronym_candidates:
        print("\n" + "=" * 70)
        print("ACRONYM/EXPANSION CANDIDATES")
        print("=" * 70)
        print()
        for candidate in acronym_candidates[:10]:
            print(f"  {candidate['acronym']} ({candidate['acronym_count']} uses) → "
                  f"{candidate['expansion']} ({candidate['expansion_count']} uses)")
            print(f"    File overlap: {candidate['overlap_ratio']:.1%}")
            print(f"    Suggestion: {candidate['suggestion']}")
            print()


@analyze.command()
@click.argument('input_path', type=click.Path(exists=True), default='.' ,required=False)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to extract (when input is vault)')
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
@click.option('--export', type=click.Path(), help='Export operations to YAML file')
@click.option('--analyzers', type=str, default='synonyms,plurals', help='Comma-separated list of analyzers to run (available: synonyms,plurals,singletons)')
@click.option('--min-similarity', type=float, default=0.7, help='Minimum semantic similarity threshold (0.0-1.0)')
@click.option('--no-transformers', is_flag=True, help='Skip semantic analysis (faster, no synonym detection)')
def recommendations(input_path, tag_types, no_filter, export, analyzers, min_similarity, no_transformers):
    """Generate consolidated tag operation recommendations.

    INPUT_PATH: Vault directory or JSON file containing tag data (defaults to current directory)

    Runs multiple analyzers and consolidates their recommendations into
    a single actionable operations file. Recommendations can be exported
    to YAML format for review and execution.

    Analyzers:
    - synonyms: Semantic similarity detection (requires sentence-transformers)
    - plurals: Singular/plural variant detection
    - singletons: Merge singleton tags into frequent tags

    The exported YAML file can be edited to enable/disable specific operations,
    then applied using: tagex apply <file.yaml>
    """
    from .analysis.merge_analyzer import build_tag_stats
    from .analysis.recommendations import RecommendationsEngine
    from .utils.input_handler import load_or_extract_tags, get_input_type
    from pathlib import Path

    filter_noise = not no_filter

    # Show which mode we're using
    input_type = get_input_type(input_path)
    vault_path = input_path if input_type == 'vault' else None

    if input_type == 'vault':
        print(f"Extracting tags from vault: {input_path}")
        print(f"Tag types: {tag_types}\n")
    else:
        print(f"Loading tags from JSON: {input_path}\n")

    tag_data = load_or_extract_tags(input_path, tag_types, filter_noise)
    tag_stats = build_tag_stats(tag_data, filter_noise)

    print(f"Analyzing {len(tag_stats)} tags for improvement opportunities...")

    # Parse analyzer list
    analyzer_list = [a.strip() for a in analyzers.split(',')]
    print(f"Enabled analyzers: {', '.join(analyzer_list)}\n")

    # Run recommendations engine
    engine = RecommendationsEngine(
        tag_stats=tag_stats,
        vault_path=vault_path,
        analyzers=analyzer_list
    )

    operations = engine.run_all_analyzers(
        min_similarity=min_similarity,
        no_transformers=no_transformers
    )

    # Print summary
    engine.print_summary()

    # Export if requested
    if export:
        engine.export_to_yaml(export)
        print(f"\nNext steps:")
        print(f"  1. Review and edit: {export}")
        print(f"  2. Preview changes: tagex apply {export}")
        print(f"  3. Apply changes:  tagex apply {export} --execute")
    else:
        print("\nTo export recommendations to a file:")
        print(f"  tagex analyze recommendations {input_path} --export operations.yaml")


@analyze.command()
@click.argument('input_path', type=click.Path(exists=True), default='.' ,required=False)
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to extract (when input is vault)')
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
@click.option('--prefer', type=click.Choice(['usage', 'plural', 'singular']), help='Override preference mode (default: usage-based or from config)')
def plurals(input_path, tag_types, no_filter, prefer):
    """Detect singular/plural variants.

    INPUT_PATH: Vault directory or JSON file containing tag data (defaults to current directory)

    Uses enhanced plural detection including irregular plurals
    (child/children) and complex patterns (-ies/-y, -ves/-f).

    Preference modes:
    - usage: Prefer most-used form (default)
    - plural: Always prefer plural forms
    - singular: Always prefer singular forms
    """
    from .analysis.merge_analyzer import build_tag_stats
    from .utils.input_handler import load_or_extract_tags, get_input_type
    from .config.plural_config import PluralConfig
    from .config.exclusions_config import ExclusionsConfig
    from .analysis.plural_normalizer import (
        normalize_plural_forms,
        normalize_compound_plurals,
        get_preferred_form
    )
    from collections import defaultdict
    from pathlib import Path

    filter_noise = not no_filter

    # Show which mode we're using
    input_type = get_input_type(input_path)
    if input_type == 'vault':
        print(f"Extracting tags from vault: {input_path}")
        print(f"Tag types: {tag_types}\n")
        vault_path = Path(input_path)
    else:
        print(f"Loading tags from JSON: {input_path}\n")
        # For JSON input, try to find vault path from config or use current dir
        vault_path = Path.cwd()

    # Load configuration
    config = PluralConfig.from_vault(str(vault_path))
    exclusions = ExclusionsConfig(vault_path)
    excluded_tags = exclusions.get_all_exclusions()
    if excluded_tags:
        print(f"Loaded {len(excluded_tags)} excluded tags from .tagex/exclusions.yaml\n")

    # Override with command-line option if provided
    preference = prefer if prefer else config.preference.value
    usage_ratio = config.usage_ratio_threshold

    tag_data = load_or_extract_tags(input_path, tag_types, filter_noise)
    tag_stats = build_tag_stats(tag_data, filter_noise)

    print(f"Analyzing {len(tag_stats)} tags for plural variants...")
    print(f"Preference mode: {preference}")
    if preference == 'usage':
        print(f"Usage ratio threshold: {usage_ratio}x\n")
    else:
        print()

    # Group tags by their plural forms
    variant_groups = defaultdict(set)

    for tag in tag_stats.keys():
        # Get all normalized forms
        forms = normalize_plural_forms(tag)
        forms.update(normalize_compound_plurals(tag))

        # Get preferred form based on configuration
        usage_counts = {t: tag_stats.get(t, {}).get('count', 0) for t in forms}
        canonical = get_preferred_form(forms, usage_counts, preference, usage_ratio)

        variant_groups[canonical].add(tag)

    # Filter to only groups with multiple variants
    variant_groups = {k: v for k, v in variant_groups.items() if len(v) > 1}

    # Filter excluded tags
    if excluded_tags:
        filtered_groups = {}
        excluded_count = 0
        for canonical, variants in variant_groups.items():
            # Check if canonical or any variant is excluded
            if exclusions.is_excluded(canonical) or any(exclusions.is_excluded(v) for v in variants):
                excluded_count += 1
                continue
            filtered_groups[canonical] = variants
        variant_groups = filtered_groups
        if excluded_count > 0:
            print(f"Filtered out {excluded_count} variant groups involving excluded tags\n")

    if variant_groups:
        print(f"Found {len(variant_groups)} plural variant groups:\n")

        # Sort by total usage
        sorted_groups = sorted(
            variant_groups.items(),
            key=lambda x: sum(tag_stats[t]['count'] for t in x[1]),
            reverse=True
        )

        # Generate suggestion text based on preference mode
        if preference == 'usage':
            suggestion_reason = "most-used form"
        elif preference == 'plural':
            suggestion_reason = "plural preferred"
        else:  # singular
            suggestion_reason = "singular preferred"

        for canonical, variants in sorted_groups[:20]:
            print(f"  Group (canonical: {canonical}):")
            for tag in sorted(variants, key=lambda t: tag_stats[t]['count'], reverse=True):
                count = tag_stats[tag]['count']
                is_canonical = ' [preferred]' if tag == canonical else ''
                print(f"    - {tag} ({count} uses){is_canonical}")
            print(f"    → Suggestion: merge all into '{canonical}' ({suggestion_reason})")
            print()
    else:
        print("No plural variant groups found.\n")


@analyze.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('--vault-path', type=click.Path(exists=True, file_okay=False, dir_okay=True), required=True, help='Vault directory path')
@click.option('--tag-types', type=click.Choice(['both', 'frontmatter', 'inline']), default='frontmatter', help='Tag types to extract')
@click.option('--min-tags', type=int, default=2, help='Only suggest for notes with fewer than this many tags')
@click.option('--max-tags', type=int, help='Only suggest for notes with at most this many tags')
@click.option('--top-n', type=int, default=3, help='Number of tags to suggest per note')
@click.option('--min-confidence', type=float, default=0.3, help='Minimum confidence threshold (0.0-1.0)')
@click.option('--no-transformers', is_flag=True, help='Skip semantic analysis, use keyword matching')
@click.option('--export', type=click.Path(), help='Export operations to YAML file')
@click.option('--no-filter', is_flag=True, help='Disable noise filtering')
def suggest(paths, vault_path, tag_types, min_tags, max_tags, top_n, min_confidence, no_transformers, export, no_filter):
    """Suggest tags for notes based on content analysis.

    PATHS: Optional file paths or glob patterns to analyze (if not specified, analyzes entire vault)

    Analyzes note content and suggests relevant tags from existing tags in the vault.
    By default, only processes notes with fewer than --min-tags tags.

    Examples:
      # Suggest tags for all notes with < 2 tags
      tagex analyze suggest --vault-path /vault --min-tags 2

      # Suggest tags for specific directory
      tagex analyze suggest /vault/projects/ --vault-path /vault --min-tags 1

      # Export suggestions to YAML for review
      tagex analyze suggest --vault-path /vault --min-tags 2 --export suggestions.yaml
    """
    from .analysis.content_analyzer import ContentAnalyzer
    from .analysis.merge_analyzer import build_tag_stats
    from .analysis.recommendations import Operation
    from .utils.input_handler import load_or_extract_tags
    from datetime import datetime
    import yaml
    from pathlib import Path

    filter_noise = not no_filter

    print(f"Extracting tags from vault: {vault_path}")
    print(f"Tag types: {tag_types}\n")

    # Extract all tags from vault using the standard loader
    tag_data = load_or_extract_tags(vault_path, tag_types, filter_noise)
    tag_stats = build_tag_stats(tag_data, filter_noise)

    print(f"Found {len(tag_stats)} existing tags in vault")

    # Build target criteria description
    if max_tags is not None:
        criteria = f"notes with < {min_tags} and <= {max_tags} tags"
    else:
        criteria = f"notes with < {min_tags} tags"
    print(f"Target criteria: {criteria}\n")

    # Run content analyzer
    analyzer = ContentAnalyzer(
        tag_stats=tag_stats,
        vault_path=vault_path,
        min_tag_count=min_tags,
        max_tag_count=max_tags
    )

    # Convert paths to list or None
    path_list = list(paths) if paths else None

    suggestions = analyzer.analyze(
        paths=path_list,
        use_semantic=not no_transformers,
        top_n=top_n,
        min_confidence=min_confidence
    )

    if not suggestions:
        print("\nNo tag suggestions generated.")
        return

    # Print suggestions
    print(f"\n{'='*70}")
    print(f"TAG SUGGESTIONS ({len(suggestions)} notes)")
    print('='*70)

    for i, sugg in enumerate(suggestions[:20], 1):
        file_path = sugg['file']
        current = sugg['current_tags']
        suggested = sugg['suggested_tags']
        confidences = sugg['confidences']

        print(f"\n{i}. {file_path}")
        print(f"   Current tags: {', '.join(current) if current else '(none)'}")
        print(f"   Suggested tags:")
        for tag, conf in zip(suggested, confidences):
            print(f"     - {tag} (confidence: {conf:.2f})")

    if len(suggestions) > 20:
        print(f"\n... and {len(suggestions) - 20} more notes")

    # Export if requested
    if export:
        print(f"\n{'='*70}")
        print("Exporting to YAML...")

        # Convert suggestions to operations
        operations = []
        for sugg in suggestions:
            # Create an "add_tags" operation
            op = Operation(
                operation_type='add_tags',
                source_tags=sugg['suggested_tags'],
                target_tag=sugg['file'],  # Use target to store the file path
                reason=f"Content-based suggestion (avg confidence: {sum(sugg['confidences'])/len(sugg['confidences']):.2f})",
                enabled=True,
                confidence=sum(sugg['confidences'])/len(sugg['confidences']),
                source_analyzer='content',
                metadata={
                    'file': sugg['file'],
                    'current_tags': sugg['current_tags'],
                    'confidences': sugg['confidences'],
                    'methods': sugg['methods']
                }
            )
            operations.append(op)

        # Export to YAML
        yaml_data = {
            'metadata': {
                'generated_by': 'tagex analyze suggest',
                'timestamp': datetime.now().isoformat(),
                'vault_path': str(vault_path),
                'total_suggestions': len(operations)
            },
            'operations': [op.to_dict() for op in operations]
        }

        with open(export, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        print(f"Exported {len(operations)} operations to: {export}")
        print(f"\nNext steps:")
        print(f"  1. Review and edit: {export}")
        print(f"  2. Preview changes: tagex apply {export} --vault-path {vault_path}")
        print(f"  3. Apply changes:  tagex apply {export} --vault-path {vault_path} --execute")
    else:
        print(f"\nTo export suggestions to a file:")
        print(f"  tagex analyze suggest --vault-path {vault_path} --min-tags {min_tags} --export suggestions.yaml")


if __name__ == "__main__":
    main()