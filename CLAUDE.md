# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TagEx extracts tags from Obsidian markdown files and analyzes tag usage patterns. It processes both frontmatter YAML tags and inline hashtags.

## Development Commands

```bash
# Install dependencies
uv sync

# Install as system-wide tool
uv tool install --editable .

# Run main extractor (console script)
tagex /path/to/vault [options]

# Or using uv run
uv run main.py /path/to/vault [options]

# Run analysis scripts
uv run tag-analysis/cooccurrence_analyzer.py tags.json [--no-filter]
uv run tag-analysis/migration_analysis.py tags.json
```

## Documentation

- [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) - System architecture and diagrams
- [doc/ANALYTICS.md](doc/ANALYTICS.md) - Tag analysis tools documentation
- [doc/ROADMAP.md](doc/ROADMAP.md) - Planned features and improvements

## Architecture Notes

TagEx features comprehensive tag validation that filters out noise by default. The main extractor includes tag filtering using `--no-filter` to get raw output when needed.

The `tag-analysis/` directory contains analysis scripts that process extracted tag data to find relationships, clusters, and migration opportunities. The `cooccurrence_analyzer.py` script includes integrated filtering with `--no-filter` option. All analysis scripts accept JSON input files as command line arguments.

### Recent Improvements
- **Tag validation system**: Filters pure numbers, HTML entities, technical patterns, and malformed tags
- **Console script**: Install with `uv tool install --editable .` for system-wide `tagex` command
- **Inline parser fix**: Updated regex to prevent URL fragments from being captured as tags
- **Consolidated analysis**: Removed `meaningful_cooccurrence.py`, functionality merged into `cooccurrence_analyzer.py`