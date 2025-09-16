# Obsidian Tag Management Tool

Extract, analyze, and modify tags in Obsidian vault markdown files using the `tagex` command-line tool.


## Quick start

```bash
# Install (editably) with uv
uv tool install --editable .

# Sanity check CLI
tagex --help

# Extract all tags to JSON from your vault
tagex "$HOME/Obsidian/MyVault" extract -f json -o tags.json

# Top 20 tags (requires jq)
jq -r '.[0:20] | .[] | "\(.tag)\t\(.tagCount)"' tags.json

# Dry-run a rename, then apply
tagex "$HOME/Obsidian/MyVault" rename "work" "project" --dry-run
tagex "$HOME/Obsidian/MyVault" rename "work" "project"

# View vault statistics and health metrics
tagex "$HOME/Obsidian/MyVault" stats
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
uv run main.py /path/to/vault extract [options]

# Tag operations
uv run main.py /path/to/vault rename old-tag new-tag
uv run main.py /path/to/vault merge tag1 tag2 --into new-tag
uv run main.py /path/to/vault delete old-tag
uv run main.py /path/to/vault stats --top 20
```

### Global Options

- `--tag-types`: Tag types to process (`both`, `frontmatter`, `inline`) (default: frontmatter)
- `--version`: Show version information
- `--help`: Show help information

### Extract Command Options

- `--output`, `-o`: Output file path (default: stdout)
- `--format`, `-f`: Output format (`json`, `csv`, `txt`) (default: json)
- `--exclude`: Patterns to exclude (can be used multiple times)
- `--verbose`, `-v`: Enable verbose logging
- `--quiet`, `-q`: Suppress summary output
- `--no-filter`: Disable tag filtering (include all raw tags)

### Operation Command Options

- `--dry-run`: Preview changes without modifying files (recommended for testing)
- All tag operations include logging and can be previewed safely

### Stats Command Options

- `--top`, `-t`: Number of top tags to display (default: 20)
- `--format`, `-f`: Output format (`text`, `json`) (default: text)
- `--no-filter`: Include all raw tags without filtering

### Examples

**Tag Extraction:**
```bash
# Extract tags from vault and output as JSON
tagex /path/to/vault extract

# Save tags to CSV file
tagex /path/to/vault extract -f csv -o tags.csv

# Extract with exclusions
tagex /path/to/vault extract --exclude "*.template.md" --exclude "drafts/*"

# Extract all raw tags without filtering
tagex /path/to/vault extract --no-filter

# Extract frontmatter tags (default behavior)
tagex /path/to/vault extract

# Extract only inline hashtags
tagex --tag-types inline /path/to/vault extract

# Extract both frontmatter and inline tags
tagex --tag-types both /path/to/vault extract

# Get a list of tags sorted by frequency
tagex /path/to/vault extract -f json | jq -r '.[] | "\(.tag) \(.tagCount)"'
```

**Tag Operations:**
```bash
# Preview tag rename (safe)
tagex /path/to/vault rename work project --dry-run

# Actually rename tag after reviewing preview
tagex /path/to/vault rename work project

# Merge multiple related tags
tagex /path/to/vault merge personal-note diary-entry journal --into writing

# Rename frontmatter tags (default behavior)
tagex /path/to/vault rename work project --dry-run

# Delete only inline tags (preserve frontmatter tags)
tagex --tag-types inline /path/to/vault delete obsolete-tag --dry-run

# Preview deleting tags (safe)
tagex /path/to/vault delete obsolete-tag temp-tag --dry-run
```

**Vault Statistics:**

```bash
# Display comprehensive tag statistics
tagex /path/to/vault stats

# Show top 10 tags with JSON output
tagex /path/to/vault stats --top 10 --format json

# Stats for frontmatter tags (default behavior)
tagex /path/to/vault stats

# Include all tags (no filtering)
tagex /path/to/vault stats --no-filter
```

**Complete Workflow:**
```bash
# 1. Extract and analyze tags
tagex /vault extract -o tags.json
# By default, analysis scripts filter noise. Use --no-filter to disable.
uv run tag-analysis/pair_analyzer.py tags.json

# 2. Preview and apply changes
tagex /vault rename old-name new-name --dry-run
tagex /vault rename old-name new-name

# 3. Verify changes
tagex /vault extract -o updated_tags.json
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

