# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TagEx extracts, analyzes, and modifies tags in Obsidian markdown files. It processes both frontmatter YAML tags and inline hashtags, provides advanced relationship analysis, and enables safe tag operations across entire vaults.

## Development Commands

```bash
# Install dependencies
uv sync

# Install as system-wide tool
uv tool install --editable .

# Tag extraction (console script)
tagex extract /path/to/vault [options]

# Tag operations (console script)
tagex rename /path/to/vault old-tag new-tag [--dry-run]
tagex merge /path/to/vault tag1 tag2 --into target-tag [--dry-run]
tagex apply /path/to/vault migration.json [--dry-run]

# Or using uv run during development
uv run main.py extract /path/to/vault [options]
uv run main.py rename /path/to/vault old-tag new-tag
uv run main.py merge /path/to/vault tag1 tag2 --into target-tag
uv run main.py apply /path/to/vault migration.json

# Run analysis scripts
uv run tag-analysis/cooccurrence_analyzer.py tags.json [--no-filter]
uv run tag-analysis/migration_analysis.py tags.json
```

## Documentation

- [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) - System architecture and diagrams
- [doc/ANALYTICS.md](doc/ANALYTICS.md) - Tag analysis tools documentation

## Architecture Notes

TagEx includes tag validation that filters out noise by default. The main extractor includes tag filtering using `--no-filter` to get raw output when needed.

### Core Modules

- **`extractor/`** - Tag extraction engine with filtering and validation
- **`parsers/`** - Frontmatter and inline tag parsing (reused by operations)
- **`operations/`** - Tag modification engine with dry-run and logging
- **`tag-analysis/`** - Advanced relationship analysis and migration planning
- **`utils/`** - File discovery, tag normalization, and validation utilities

### Key Features

- **Multi-command CLI** - Extract, rename, merge, and apply operations
- **Safe by default** - Dry-run mode and comprehensive logging
- **No corruption** - Uses proven parsers, preserves file formatting
- **Smart filtering** - Only processes files containing target tags
- **Operation logging** - Detailed change tracking with integrity checks

### Recent Major Implementation: Tag Operations

**NEW COMMANDS:**
- `tagex rename <vault> old-tag new-tag` - Rename tags across vault
- `tagex merge <vault> tag1 tag2 tag3 --into target` - Merge multiple tags  
- `tagex apply <vault> migration.json` - Apply migration mappings
- `tagex extract <vault>` - Original extraction (now a subcommand)

**ARCHITECTURE CHANGES:**
- New `operations/` module with TagOperationEngine base class
- RenameOperation, MergeOperation, ApplyOperation classes
- Uses existing proven parsers from parsers/ instead of manual YAML
- CLI changed from single command to command group
- Removed dangerous backup system after it corrupted vaults

**KEY FEATURES:**
- Dry-run by default, `--dry-run` flag for preview mode
- Only processes files that actually contain target tags
- Preserves original YAML structure (no corruption)
- Uses existing frontmatter_parser.py and inline_parser.py
- Operation logging in current directory (not in vault)
- Safe tag transformations with code block preservation

**FIXES IMPLEMENTED:**
- Fixed critical YAML corruption bug (type: -> type: null)
- Fixed date format corruption
- Fixed processing files without target tags
- Removed dangerous backup system that deleted .git directories

**PREVIOUS IMPROVEMENTS:**
- **Tag validation system**: Filters pure numbers, HTML entities, technical patterns, and malformed tags
- **Console script**: Install with `uv tool install --editable .` for system-wide `tagex` command
- **Inline parser fix**: Updated regex to prevent URL fragments from being captured as tags
- **Consolidated analysis**: Removed `meaningful_cooccurrence.py`, functionality merged into `cooccurrence_analyzer.py`