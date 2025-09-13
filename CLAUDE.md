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

# Tag extraction (console script)
tagex extract /path/to/vault [options]

# Tag operations (console script)
tagex rename /path/to/vault old-tag new-tag [--dry-run]
tagex merge /path/to/vault tag1 tag2 --into target-tag [--dry-run]

# Or using uv run during development
uv run main.py extract /path/to/vault [options]
uv run main.py rename /path/to/vault old-tag new-tag
uv run main.py merge /path/to/vault tag1 tag2 --into target-tag

# Run analysis scripts  
uv run tag-analysis/pair_analyzer.py tags.json [--no-filter]
uv run tag-analysis/merge_analyzer.py tags.json [--no-sklearn]

# Run tests
pytest tests/
```

## Documentation

- [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) - System architecture and diagrams
- [doc/ANALYTICS.md](doc/ANALYTICS.md) - Tag analysis tools documentation
- [tag-analysis/SEMANTIC_ANALYSIS.md](tag-analysis/SEMANTIC_ANALYSIS.md) - Semantic similarity detection
- [tests/README.md](tests/README.md) - Test suite documentation

## Architecture Notes

### Core Modules

- **`extractor/`** - Tag extraction with filtering and validation
- **`parsers/`** - Frontmatter and inline tag parsing
- **`operations/`** - Tag modification (rename, merge) with dry-run support
- **`tag-analysis/`** - Relationship analysis and semantic similarity detection
- **`utils/`** - File discovery, tag normalization, and validation

### Key Features

- **Multi-command CLI** - Extract, rename, merge operations
- **Safe by default** - Dry-run mode and comprehensive logging
- **Tag validation** - Filters noise, preserves meaningful tags
- **Semantic analysis** - TF-IDF embedding-based similarity detection with morphological fallback
- **Smart processing** - Only modifies files containing target tags