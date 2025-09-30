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

# Tag operations (console script)
tagex extract /path/to/vault [options]
tagex rename /path/to/vault old-tag new-tag [--dry-run]
tagex merge /path/to/vault tag1 tag2 --into target-tag [--dry-run]
tagex delete /path/to/vault unwanted-tag another-tag [--dry-run]
tagex stats /path/to/vault [--top N] [--format text|json] [--no-filter]

# Global --tag-types option (applies to all commands, default: frontmatter)
# Per-command --tag-types option (applies per command, default: frontmatter)
# Or using uv run during development
uv run python -m tagex.main extract /path/to/vault [options]
uv run python -m tagex.main rename /path/to/vault old-tag new-tag
uv run python -m tagex.main merge /path/to/vault tag1 tag2 --into target-tag
uv run python -m tagex.main delete /path/to/vault unwanted-tag --dry-run
uv run python -m tagex.main stats /path/to/vault [--top 10] [--format json]

# Global --tag-types with uv run (default: frontmatter)
uv run python -m tagex.main extract /path/to/vault  # frontmatter only (default)
uv run python -m tagex.main extract /path/to/vault --tag-types both  # both types

# Run analysis commands
tagex analyze pairs tags.json [--no-filter] [--min-pairs N]
tagex analyze merge tags.json [--no-sklearn] [--min-usage N]

# Run tests
uv run pytest tests/
```

## Documentation

- [docs/README.md](docs/README.md) - Documentation index with reading flows
- [docs/architecture.md](docs/architecture.md) - System architecture and diagrams
- [docs/analytics.md](docs/analytics.md) - Tag analysis tools documentation
- [docs/testing-narrative.md](docs/testing-narrative.md) - Test development narrative
- [docs/semantic-analysis.md](docs/semantic-analysis.md) - Semantic similarity detection
- [tests/README.md](tests/README.md) - Test suite documentation

## Architecture Notes

### Core Modules

- **`tagex/core/extractor/`** - Tag extraction with filtering and validation
- **`tagex/core/parsers/`** - Frontmatter and inline tag parsing
- **`tagex/core/operations/`** - Tag modification (rename, merge, delete) with dry-run support
- **`tagex/utils/`** - File discovery, tag normalization, and validation
- **`tagex/analysis/`** - Relationship analysis and semantic similarity detection

### Key Features

- **Vault-first CLI structure** - Vault path comes first, then command
- **Global tag type filtering** - --tag-types option applies to all operations
- **Multi-command operations** - Extract, rename, merge, delete, stats, analyze with consistent interface
- **Comprehensive statistics** - Tag distribution, vault health metrics, singleton analysis
- **Safe by default** - Dry-run mode and comprehensive logging
- **Tag validation** - Filters noise, preserves meaningful tags
- **Semantic analysis** - TF-IDF embedding-based similarity detection with morphological fallback
- **Smart processing** - Only modifies files containing target tags