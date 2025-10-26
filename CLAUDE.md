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

# Tag operations (console script)
tagex extract /path/to/vault [options]
tagex rename /path/to/vault old-tag new-tag [--dry-run]
tagex merge /path/to/vault tag1 tag2 --into target-tag [--dry-run]
tagex delete /path/to/vault unwanted-tag another-tag [--dry-run]
tagex stats /path/to/vault [--top N] [--format text|json] [--no-filter]
tagex health /path/to/vault

# Analysis commands (accept vault path or JSON file)
tagex analyze pairs /path/to/vault [--no-filter] [--min-pairs N]
tagex analyze merge /path/to/vault [--no-sklearn] [--min-usage N]
tagex analyze quality /path/to/vault [--format text|json]
tagex analyze synonyms /path/to/vault [--min-similarity 0.7] [--show-related] [--no-transformers]
tagex analyze plurals /path/to/vault [--prefer usage|plural|singular]

# Or using uv run during development
uv run python -m tagex.main init /path/to/vault
uv run python -m tagex.main validate /path/to/vault
uv run python -m tagex.main extract /path/to/vault [options]
uv run python -m tagex.main rename /path/to/vault old-tag new-tag
uv run python -m tagex.main merge /path/to/vault tag1 tag2 --into target-tag
uv run python -m tagex.main delete /path/to/vault unwanted-tag --dry-run
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
- **`tagex/core/operations/`** - Tag modification (rename, merge, delete) with dry-run support
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
- **Safe by default** - Dry-run mode and comprehensive logging
- **Tag validation** - Filters noise, preserves meaningful tags
- **Semantic synonym detection** - sentence-transformers for true synonym detection (not co-occurrence)
- **Configurable plural preferences** - usage-based (default), plural, or singular modes
- **TF-IDF merge suggestions** - Embedding-based similarity detection with morphological fallback
- **Smart processing** - Only modifies files containing target tags

### Configuration Structure

Configuration files are stored in `.tagex/` directory within each vault:

- **`.tagex/config.yaml`** - General settings (plural preferences, thresholds)
- **`.tagex/synonyms.yaml`** - User-defined synonym mappings
- **`.tagex/README.md`** - Documentation about configuration

Use `tagex init /vault` to create configuration directory with templates.
Use `tagex validate /vault` to check configuration validity.