# Obsidian Tag Management Tool

Extract, analyze, and modify tags in Obsidian vault markdown files using the `tagex` command-line tool.


## Quick start

```bash
# Install (editably) with uv
uv tool install --editable .

# Sanity check CLI
tagex --help

# Extract all tags to JSON from your vault
tagex extract "$HOME/Obsidian/MyVault" -f json -o tags.json

# Top 20 tags (requires jq)
jq -r '.[0:20] | .[] | "\(.tag)\t\(.tagCount)"' tags.json

# Dry-run a rename, then apply
tagex rename "$HOME/Obsidian/MyVault" "work" "project" --dry-run
tagex rename "$HOME/Obsidian/MyVault" "work" "project"

# Explore co-occurrence
uv run tag-analysis/pair_analyzer.py tags.json
```

## Commands

The tool provides comprehensive tag management through multiple commands:

```bash
# Extract tags from vault
tagex extract /path/to/vault [options]

# Rename a tag across all files
tagex rename /path/to/vault old-tag new-tag [--dry-run]

# Merge multiple tags into one
tagex merge /path/to/vault tag1 tag2 tag3 --into target-tag [--dry-run]

# Delete tags from all files
tagex delete /path/to/vault tag-to-remove another-tag --dry-run
```

Or during development:
```bash
# Extract tags
uv run main.py extract /path/to/vault [options]

# Tag operations
uv run main.py rename /path/to/vault old-tag new-tag
uv run main.py merge /path/to/vault tag1 tag2 --into new-tag
uv run main.py delete /path/to/vault old-tag
```

### Extract Command Options

- `--output`, `-o`: Output file path (default: stdout)
- `--format`, `-f`: Output format (`json`, `csv`, `txt`) (default: json)
- `--exclude`: Patterns to exclude (can be used multiple times)
- `--verbose`, `-v`: Enable verbose logging
- `--quiet`, `-q`: Suppress summary output
- `--no-filter`: Disable tag filtering (include all raw tags)
- `--tag-types`: Tag types to extract (`both`, `frontmatter`, `inline`) (default: both)

### Operation Command Options

- `--dry-run`: Preview changes without modifying files (recommended for testing)
- `--tag-types`: Tag types to process (`both`, `frontmatter`, `inline`) (default: both)
- All tag operations include logging and can be previewed safely

### Examples

**Tag Extraction:**
```bash
# Extract tags from vault and output as JSON
tagex extract /path/to/vault

# Save tags to CSV file
tagex extract /path/to/vault -f csv -o tags.csv

# Extract with exclusions
tagex extract /path/to/vault --exclude "*.template.md" --exclude "drafts/*"

# Extract all raw tags without filtering
tagex extract /path/to/vault --no-filter

# Extract only frontmatter tags
tagex extract /path/to/vault --tag-types frontmatter

# Extract only inline hashtags
tagex extract /path/to/vault --tag-types inline

# Get a list of tags sorted by frequency
tagex extract /path/to/vault -f json | jq -r '.[] | "\(.tag) \(.tagCount)"'
```

**Tag Operations:**
```bash
# Preview tag rename (safe)
tagex rename /path/to/vault work project --dry-run

# Actually rename tag after reviewing preview
tagex rename /path/to/vault work project

# Merge multiple related tags
tagex merge /path/to/vault personal-note diary-entry journal --into writing

# Rename only frontmatter tags (leave inline tags unchanged)
tagex rename /path/to/vault work project --tag-types frontmatter --dry-run

# Delete only inline tags (preserve frontmatter tags)
tagex delete /path/to/vault obsolete-tag --tag-types inline --dry-run

# Preview deleting tags (safe)
tagex delete /path/to/vault obsolete-tag temp-tag --dry-run
```

**Complete Workflow:**
```bash
# 1. Extract and analyze tags
tagex extract /vault -o tags.json
# By default, analysis scripts filter noise. Use --no-filter to disable.
uv run tag-analysis/pair_analyzer.py tags.json

# 2. Preview and apply changes
tagex rename /vault old-name new-name --dry-run
tagex rename /vault old-name new-name

# 3. Verify changes
tagex extract /vault -o updated_tags.json
```

## Features

**Tag Extraction:**

- Extracts tags from frontmatter YAML
- Extracts inline hashtags from content
- **Selective tag type filtering** - choose frontmatter, inline, or both
- Automatic tag validation - filters out noise (numbers, HTML entities, technical patterns) by default
- Multiple output formats (JSON, CSV, txt)
- File pattern exclusions
- Statistics and summaries

**Tag Operations:**

- **Rename tags** across entire vault with preview mode
- **Merge multiple tags** into consolidated tags
- **Delete tags** from all files, with warnings for inline tag removal
- **Selective processing** - operate on frontmatter, inline, or both tag types
- **Safe by default** - dry-run mode prevents accidental changes
- **Operation logging** tracks all modifications with integrity checks
- **Preserves file structure** - no YAML corruption or formatting changes

**Advanced Analysis:**

- Tag relationship analysis (pair analysis, clustering)
- Hub tag identification and cluster detection
- Comprehensive tag validation and noise filtering

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

