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
tagex /path/to/vault extract [options]
tagex /path/to/vault rename old-tag new-tag [--dry-run]
tagex /path/to/vault merge tag1 tag2 --into target-tag [--dry-run]
tagex /path/to/vault delete unwanted-tag another-tag [--dry-run]
tagex /path/to/vault stats [--top N] [--format text|json] [--no-filter]

# Global --tag-types option (applies to all commands, default: frontmatter)
tagex --tag-types both|frontmatter|inline /path/to/vault COMMAND [options]

# Or using uv run during development
uv run main.py /path/to/vault extract [options]
uv run main.py /path/to/vault rename old-tag new-tag
uv run main.py /path/to/vault merge tag1 tag2 --into target-tag
uv run main.py /path/to/vault delete unwanted-tag --dry-run
uv run main.py /path/to/vault stats [--top 10] [--format json]

# Global --tag-types with uv run (default: frontmatter)
uv run main.py /path/to/vault extract  # frontmatter only (default)
uv run main.py --tag-types both /path/to/vault extract  # both types

# Run analysis scripts  
uv run tag-analysis/pair_analyzer.py tags.json [--no-filter]
uv run tag-analysis/merge_analyzer.py tags.json [--no-sklearn]

# Run tests
uv run pytest tests/
```

## Documentation

- [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) - System architecture and diagrams
- [doc/ANALYTICS.md](doc/ANALYTICS.md) - Tag analysis tools documentation
- [doc/TESTING_NARRATIVE.md](doc/TESTING_NARRATIVE.md) - Test development narrative
- [tag-analysis/SEMANTIC_ANALYSIS.md](tag-analysis/SEMANTIC_ANALYSIS.md) - Semantic similarity detection
- [tests/README.md](tests/README.md) - Test suite documentation

## Architecture Notes

### Core Modules

- **`extractor/`** - Tag extraction with filtering and validation
- **`parsers/`** - Frontmatter and inline tag parsing
- **`operations/`** - Tag modification (rename, merge, delete) with dry-run support
- **`tag-analysis/`** - Relationship analysis and semantic similarity detection
- **`utils/`** - File discovery, tag normalization, and validation

### Key Features

- **Vault-first CLI structure** - Vault path comes first, then command
- **Global tag type filtering** - --tag-types option applies to all operations
- **Multi-command operations** - Extract, rename, merge, delete, stats with consistent interface
- **Comprehensive statistics** - Tag distribution, vault health metrics, singleton analysis
- **Safe by default** - Dry-run mode and comprehensive logging
- **Tag validation** - Filters noise, preserves meaningful tags
- **Semantic analysis** - TF-IDF embedding-based similarity detection with morphological fallback
- **Smart processing** - Only modifies files containing target tags