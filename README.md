# Obsidian Tag Management Tool

Extract, analyze, and modify tags in Obsidian vault markdown files using the `tagex` command-line tool.

## Commands

The tool provides comprehensive tag management through multiple commands:

```bash
# Extract tags from vault
tagex extract /path/to/vault [options]

# Rename a tag across all files
tagex rename /path/to/vault old-tag new-tag [--dry-run]

# Merge multiple tags into one
tagex merge /path/to/vault tag1 tag2 tag3 --into target-tag [--dry-run]

```

Or during development:
```bash
# Extract tags
uv run main.py extract /path/to/vault [options]

# Tag operations
uv run main.py rename /path/to/vault old-tag new-tag
uv run main.py merge /path/to/vault tag1 tag2 --into new-tag
```

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

```

**Complete Workflow:**
```bash
# 1. Extract and analyze tags
tagex extract /vault -o tags.json
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
- Automatic tag validation - filters out noise (numbers, HTML entities, technical patterns) by default
- Multiple output formats (JSON, CSV, text)
- File pattern exclusions
- Statistics and summaries

**Tag Operations:**

- **Rename tags** across entire vault with preview mode
- **Merge multiple tags** into consolidated tags
- **Safe by default** - dry-run mode prevents accidental changes
- **Operation logging** tracks all modifications with integrity checks
- **Preserves file structure** - no YAML corruption or formatting changes

**Advanced Analysis:**

- Tag relationship analysis (co-occurrence, clustering)
- Migration impact assessment tools
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

