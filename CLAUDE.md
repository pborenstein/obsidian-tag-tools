# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This tool extracts, analyzes, and modifies tags in Obsidian markdown files. It processes both frontmatter YAML tags and inline hashtags, provides relationship analysis, and enables safe tag operations across entire vaults.

## Development Commands

```bash
# Install dependencies
uv sync

# Install as system-wide tool (creates 'tagex' command)
uv tool install --editable .

# Quick start (most common commands)
tagex init                          # Initialize vault configuration (defaults to cwd)
tagex stats                         # View tag statistics
tagex health                        # Check vault health
tagex analyze recommendations --export ops.yaml
tagex tag apply ops.yaml --execute

# Configuration management
tagex init [vault_path] [--force]           # Initialize .tagex/ configuration
tagex config validate [vault_path] [--strict]
tagex config show [vault_path]               # Display current configuration
tagex config edit [vault_path] [config]     # Edit config in $EDITOR

# Tag operations (safe by default, require --execute to apply changes)
tagex tag export [vault_path] [options]                  # Export tags (formerly extract)
tagex tag rename [vault_path] old-tag new-tag [--execute]
tagex tag merge [vault_path] tag1 tag2 --into target [--execute]
tagex tag delete [vault_path] unwanted-tag another-tag [--execute]
tagex tag add [vault_path] file.md python programming [--execute]  # NEW
tagex tag fix [vault_path] [--execute]                   # Fix duplicate 'tags:' fields
tagex tag apply [vault_path] operations.yaml [--execute]

# Quick info commands (top level for convenience, default to cwd)
tagex stats [vault_path] [--top N] [--format text|json]
tagex health [vault_path]

# Analysis commands (accept vault path or JSON file, default to cwd)
tagex analyze pairs [vault_path] [--no-filter] [--min-pairs N]
tagex analyze quality [vault_path] [--format text|json]
tagex analyze synonyms [vault_path] [--min-similarity 0.7] [--show-related] [--no-transformers] [--export ops.yaml]
tagex analyze plurals [vault_path] [--prefer usage|plural|singular] [--export ops.yaml]
tagex analyze merges [vault_path] [--min-usage 3] [--no-sklearn] [--export ops.yaml]
tagex analyze suggest [vault_path] [paths...] [--min-tags 2] [--export suggestions.yaml]
tagex analyze recommendations [vault_path] [--export operations.yaml] [--analyzers synonyms,plurals,singletons]

# Unified recommendations and apply workflow
tagex analyze recommendations --export ops.yaml    # Generate recommendations
tagex tag apply ops.yaml                           # Preview changes
tagex tag apply ops.yaml --execute                 # Apply changes

# Vault maintenance operations
tagex vault cleanup [vault_path] [--execute]       # Remove .bak backup files
tagex vault backup [vault_path] [-o output.tar.gz] # Create vault backup
tagex vault verify [vault_path]                    # Verify vault integrity

# Or using uv run during development (preview mode by default, commands default to cwd)
uv run python -m tagex.main init
uv run python -m tagex.main config validate
uv run python -m tagex.main tag export
uv run python -m tagex.main tag rename old-tag new-tag                # Preview only
uv run python -m tagex.main tag rename old-tag new-tag --execute      # Actually rename
uv run python -m tagex.main tag merge tag1 tag2 --into target         # Preview only
uv run python -m tagex.main tag merge tag1 tag2 --into target --execute
uv run python -m tagex.main tag delete unwanted-tag                   # Preview only
uv run python -m tagex.main tag delete unwanted-tag --execute
uv run python -m tagex.main tag add file.md python --execute          # Add tags to file
uv run python -m tagex.main stats [--top 10] [--format json]
uv run python -m tagex.main health

# Global --tag-types option (applies to all commands, default: frontmatter)
uv run python -m tagex.main tag export              # frontmatter only (default), uses cwd
uv run python -m tagex.main tag export --tag-types both  # both types, uses cwd

# Run tests
uv run pytest tests/
```

## Documentation

- [docs/README.md](docs/README.md) - Documentation index with reading flows
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture and diagrams
- [docs/ANALYTICS.md](docs/ANALYTICS.md) - Tag analysis tools documentation
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md) - Vault setup and best practices
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [docs/TESTING_NARRATIVE.md](docs/TESTING_NARRATIVE.md) - Test development narrative
- [docs/SEMANTIC_ANALYSIS.md](docs/SEMANTIC_ANALYSIS.md) - Semantic similarity detection
- [tests/README.md](tests/README.md) - Test suite documentation

## Architecture Notes

### Core Modules

- **`tagex/core/extractor/`** - Tag extraction with filtering and validation
- **`tagex/core/parsers/`** - Frontmatter and inline tag parsing
- **`tagex/core/operations/`** - Tag modification (rename, merge, delete, fix_duplicates, add_tags) with dry-run support
- **`tagex/utils/`** - File discovery, tag normalization, and validation
- **`tagex/analysis/`** - Relationship analysis and semantic similarity detection
- **`tagex/config/`** - Configuration management (plural preferences, synonyms)

### Key Features

- **Hybrid CLI structure** - Quick-access commands (init, stats, health) at top level, organized groups for advanced operations
- **Command groups** - `config/`, `tag/`, `analyze/`, `vault/` for logical organization
- **Configuration system** - .tagex/ directory for vault-specific settings
- **Global tag type filtering** - --tag-types option applies to all operations
- **Multi-command operations** - Export, rename, merge, delete, add, fix, stats, analyze with consistent interface
- **Dual input modes** - All analyze commands accept vault path (auto-extract) or JSON file
- **Configuration commands** - init, config validate, config show, config edit for managing .tagex/ configuration
- **Health reporting** - Unified health command with comprehensive analysis
- **Comprehensive statistics** - Tag distribution, vault health metrics, singleton analysis
- **Safe by default** - All write operations require --execute flag; preview mode is default
- **Tag validation** - Filters noise, preserves meaningful tags
- **Semantic synonym detection** - sentence-transformers for true synonym detection (not co-occurrence)
- **Configurable plural preferences** - usage-based (default), plural, or singular modes
- **TF-IDF merge suggestions** - Embedding-based similarity detection with morphological fallback
- **Singleton tag reduction** - Intelligent merging of single-use tags into established frequent tags
- **Smart processing** - Only modifies files containing target tags
- **Content-based tag suggestions** - Analyzes note content to suggest relevant existing tags for untagged/lightly-tagged notes
- **Unified recommendations system** - Consolidates all analyzer suggestions into editable YAML operations file
- **Apply workflow** - Execute operations from YAML file with enable/disable flags for selective application
- **Frontmatter repair** - Fix duplicate 'tags:' fields automatically
- **Vault maintenance** - Cleanup, backup, and verify tools for vault organization
- **Current directory defaults** - All commands default to cwd when no path specified

### Configuration Structure

Configuration files are stored in `.tagex/` directory within each vault:

- **`.tagex/config.yaml`** - General settings (plural preferences, thresholds)
- **`.tagex/synonyms.yaml`** - User-defined synonym mappings
- **`.tagex/exclusions.yaml`** - Tags to exclude from merge suggestions
- **`.tagex/README.md`** - Documentation about configuration

Use `tagex init` to create configuration directory with templates.
Use `tagex config validate` to check configuration validity.
Use `tagex config show` to view current configuration.
Use `tagex config edit` to modify configuration in your $EDITOR.