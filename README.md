# Obsidian Tag Management Tool

Extract, analyze, and modify tags in Obsidian vault markdown files using the `tagex` command-line tool.


## Quick start

```bash
# Install (editably) with uv
uv tool install --editable .

# Sanity check CLI
tagex --help

# View vault statistics and health metrics
tagex "$HOME/Obsidian/MyVault" stats

# Extract all tags to JSON from your vault
tagex "$HOME/Obsidian/MyVault" extract -f json -o tags.json

# Top 20 tags (requires jq (https://jqlang.org/))
jq -r '.[0:20] | .[] | "\(.tag)\t\(.tagCount)"' tags.json

# Dry-run a rename, then apply
tagex "$HOME/Obsidian/MyVault" rename "work" "project" --dry-run
tagex "$HOME/Obsidian/MyVault" rename "work" "project"
```

## Commands

The tool provides comprehensive tag management through multiple commands:

```bash
# Extract tags from vault
tagex /path/to/vault extract [options]

# Rename a tag across all files
tagex /path/to/vault rename old-tag new-tag [--dry-run]

# Merge multiple tags into one
tagex /path/to/vault merge tag1 tag2 tag3 --into target-tag [--dry-run]

# Delete tags from all files
tagex /path/to/vault delete tag-to-remove another-tag --dry-run

# Get comprehensive vault statistics
tagex /path/to/vault stats --top 15

# Global --tag-types option examples (frontmatter is default)
tagex /path/to/vault extract  # frontmatter only (default)
tagex --tag-types inline /path/to/vault rename old-tag new-tag --dry-run
tagex --tag-types both /path/to/vault merge tag1 tag2 --into new-tag
tagex --tag-types both /path/to/vault stats --format json
```

Or during development:
```bash
# Extract tags
uv run python -m tagex.main /path/to/vault extract [options]

# Tag operations
uv run python -m tagex.main /path/to/vault rename old-tag new-tag
uv run python -m tagex.main /path/to/vault merge tag1 tag2 --into new-tag
uv run python -m tagex.main /path/to/vault delete old-tag
uv run python -m tagex.main /path/to/vault stats --top 20
```

### Options Reference

| Option | Commands | Description | Default |
|:-------|:---------|:------------|:---------|
| `--tag-types` | All | Tag types to process (`both`, `frontmatter`, `inline`) | `frontmatter` |
| `--output`, `-o` | extract | Output file path | stdout |
| `--format`, `-f` | extract, stats | Output format (`json`, `csv`, `txt` for extract; `text`, `json` for stats) | `json`, `text` |
| `--exclude` | extract | File patterns to exclude (repeatable) | none |
| `--verbose`, `-v` | extract | Enable verbose logging | disabled |
| `--quiet`, `-q` | extract | Suppress summary output | disabled |
| `--no-filter` | extract, stats | Include all raw tags without filtering | disabled |
| `--dry-run` | rename, merge, delete | Preview changes without modifying files | disabled |
| `--top`, `-t` | stats | Number of top tags to display | 20 |

### Examples

```bash
# Extract tags (JSON output, frontmatter only by default)
tagex /path/to/vault extract
tagex /path/to/vault extract -f csv -o tags.csv
tagex --tag-types both /path/to/vault extract --no-filter

# Tag operations with dry-run preview
tagex /path/to/vault rename work project --dry-run
tagex /path/to/vault merge personal diary journal --into writing --dry-run
tagex --tag-types inline /path/to/vault delete obsolete-tag --dry-run

# Vault statistics
tagex /path/to/vault stats --top 10 --format json
```

**Workflow:**
```bash
# Extract, analyze, modify, verify
tagex /vault extract -o tags.json
uv run tag-analysis/pair_analyzer.py tags.json
tagex /vault rename old-name new-name --dry-run && tagex /vault rename old-name new-name
tagex /vault extract -o updated_tags.json
```

## Features

### Tag Extraction

| Feature | Description |
|:--------|:------------|
| Frontmatter YAML | Extracts tags from document metadata |
| Inline hashtags | Extracts hashtags from content |
| Tag type filtering | Process frontmatter, inline, or both |
| Tag validation | Filters noise (numbers, HTML entities, technical patterns) |
| Output formats | JSON, CSV, txt |
| File exclusions | Pattern-based file filtering |
| Statistics | Tag counts and vault summaries |

### Tag Operations

| Operation | Description | Safety Features |
|:----------|:------------|:---------------|
| Rename | Single tag renaming across vault | Preview mode, dry-run |
| Merge | Consolidate multiple tags | Multi-tag input validation |
| Delete | Remove tags from all files | Inline tag warnings |
| Selective processing | Target frontmatter, inline, or both | Type-specific operations |
| Logging | Track all modifications | Integrity checks |
| Structure preservation | Maintain file formatting | No YAML corruption |

### Advanced Analysis

| Analysis Type | Description |
|:--------------|:------------|
| Relationship analysis | Tag pair analysis and clustering |
| Hub identification | Detect central tags and clusters |
| Validation | Filter noise and validate tags |

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

Install as a global command:
```bash
uv tool install --editable .
```

Or install dependencies for development:
```bash
uv sync
```


## Documentation

| Document | Description |
| :----------|:-------------|
| [ARCHITECTURE.md](doc/ARCHITECTURE.md) | System architecture and component design |
| [ANALYTICS.md](doc/ANALYTICS.md) | Tag analysis tools and usage guide |

