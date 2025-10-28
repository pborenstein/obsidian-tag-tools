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

# Configuration management
tagex init /path/to/vault [--force]
tagex validate /path/to/vault [--strict]

# Tag operations (console script - safe by default, require --execute to apply)
tagex extract /path/to/vault [options]
tagex rename /path/to/vault old-tag new-tag [--execute]
tagex merge /path/to/vault tag1 tag2 --into target-tag [--execute]
tagex delete /path/to/vault unwanted-tag another-tag [--execute]
tagex stats /path/to/vault [--top N] [--format text|json] [--no-filter]
tagex health /path/to/vault

# Analysis commands (accept vault path or JSON file)
tagex analyze pairs /path/to/vault [--no-filter] [--min-pairs N]
tagex analyze quality /path/to/vault [--format text|json]
tagex analyze synonyms /path/to/vault [--min-similarity 0.7] [--show-related] [--no-transformers]
tagex analyze plurals /path/to/vault [--prefer usage|plural|singular]
tagex analyze suggest --vault-path /vault [paths...] [--min-tags 2] [--export suggestions.yaml]

# Unified recommendations and apply workflow (safe by default)
tagex analyze recommendations /path/to/vault [--export operations.yaml] [--analyzers synonyms,plurals,singletons]
tagex apply operations.yaml [--vault-path /path/to/vault]  # Preview mode (default)
tagex apply operations.yaml [--vault-path /path/to/vault] --execute  # Actually apply changes

# Or using uv run during development (preview mode by default)
uv run python -m tagex.main init /path/to/vault
uv run python -m tagex.main validate /path/to/vault
uv run python -m tagex.main extract /path/to/vault [options]
uv run python -m tagex.main rename /path/to/vault old-tag new-tag  # Preview only
uv run python -m tagex.main rename /path/to/vault old-tag new-tag --execute  # Actually rename
uv run python -m tagex.main merge /path/to/vault tag1 tag2 --into target-tag  # Preview only
uv run python -m tagex.main merge /path/to/vault tag1 tag2 --into target-tag --execute  # Actually merge
uv run python -m tagex.main delete /path/to/vault unwanted-tag  # Preview only
uv run python -m tagex.main delete /path/to/vault unwanted-tag --execute  # Actually delete
uv run python -m tagex.main stats /path/to/vault [--top 10] [--format json]
uv run python -m tagex.main health /path/to/vault

# Global --tag-types option (applies to all commands, default: frontmatter)
uv run python -m tagex.main extract /path/to/vault  # frontmatter only (default)
uv run python -m tagex.main extract /path/to/vault --tag-types both  # both types

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
- **`tagex/core/operations/`** - Tag modification (rename, merge, delete, add_tags) with dry-run support
- **`tagex/utils/`** - File discovery, tag normalization, and validation
- **`tagex/analysis/`** - Relationship analysis and semantic similarity detection
- **`tagex/config/`** - Configuration management (plural preferences, synonyms)

### Key Features

- **Vault-first CLI structure** - Vault path comes first, then command
- **Configuration system** - .tagex/ directory for vault-specific settings
- **Global tag type filtering** - --tag-types option applies to all operations
- **Multi-command operations** - Extract, rename, merge, delete, stats, analyze with consistent interface
- **Dual input modes** - All analyze commands accept vault path (auto-extract) or JSON file
- **Configuration commands** - init, validate for managing .tagex/ configuration
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

### Configuration Structure

Configuration files are stored in `.tagex/` directory within each vault:

- **`.tagex/config.yaml`** - General settings (plural preferences, thresholds)
- **`.tagex/synonyms.yaml`** - User-defined synonym mappings
- **`.tagex/exclusions.yaml`** - Tags to exclude from merge suggestions
- **`.tagex/README.md`** - Documentation about configuration

Use `tagex init /vault` to create configuration directory with templates.
Use `tagex validate /vault` to check configuration validity.