# Obsidian Tag Management Tool

Extract, analyze, and modify tags in Obsidian vault markdown files using the `tagex` command-line tool.

## Project Overview

tagex is a command-line tool for managing tags across entire Obsidian vaults. It provides comprehensive tag extraction, analysis, and modification operations with safety features like preview-by-default mode (requires --execute flag) and operation logging.

**Key capabilities:**

- Extract tags from frontmatter YAML and inline hashtags
- Analyze tag relationships and co-occurrence patterns
- Suggest tags for untagged/lightly-tagged notes based on content analysis
- Rename, merge, and delete tags across entire vaults
- Fix duplicate frontmatter 'tags:' fields automatically
- Generate vault health metrics and statistics
- Detect semantic similarities for tag consolidation
- Unified recommendations system for streamlined tag cleanup
- Vault maintenance tools (backup cleanup, repair operations)
- Safe operations with preview mode by default and comprehensive logging
- Commands default to current working directory for convenience

## Quick Start

```bash
# Install (editably) with uv
uv tool install --editable .

# Sanity check CLI
tagex --help

# Initialize configuration
cd "$HOME/Obsidian/MyVault"
tagex init

# View vault statistics and health metrics
tagex stats

# Export all tags to JSON
tagex tag export -f json -o tags.json

# Top 20 tags (requires jq (https://jqlang.org/))
jq -r '.[0:20] | .[] | "\(.tag)\t\(.tagCount)"' tags.json

# Preview a rename, then apply (safe by default)
tagex tag rename "work" "project"              # Preview only
tagex tag rename "work" "project" --execute    # Actually apply
```

## Commands

The tool provides comprehensive tag management through multiple commands. All commands default to the current working directory when no vault path is specified.

```bash
# Configuration management (defaults to cwd)
tagex init [vault_path]                      # Initialize .tagex/ configuration
tagex config validate [vault_path]           # Validate configuration files
tagex config show [vault_path]               # Display current configuration
tagex config edit [config|synonyms|exclusions]  # Edit configuration in $EDITOR

# Export tags from vault (defaults to cwd)
tagex tag export [vault_path] [options]

# Rename a tag across all files (safe by default - preview mode)
tagex tag rename old-tag new-tag             # Preview only (uses cwd)
tagex tag rename old-tag new-tag --execute   # Actually rename

# Merge multiple tags into one (safe by default - preview mode)
tagex tag merge tag1 tag2 tag3 --into target-tag             # Preview only (uses cwd)
tagex tag merge tag1 tag2 tag3 --into target-tag --execute   # Actually merge

# Delete tags from all files (safe by default - preview mode)
tagex tag delete tag-to-remove another-tag             # Preview only (uses cwd)
tagex tag delete tag-to-remove another-tag --execute   # Actually delete

# Add tags to specific files (safe by default - preview mode)
tagex tag add file.md python programming               # Preview only
tagex tag add file.md python programming --execute     # Actually add

# Fix duplicate 'tags:' fields in frontmatter (safe by default)
tagex tag fix                # Preview duplicates (uses cwd)
tagex tag fix --execute      # Fix duplicates

# Get comprehensive vault statistics (defaults to cwd)
tagex stats [vault_path] --top 15

# Get comprehensive health report (defaults to cwd)
tagex health [vault_path]

# Analyze tag relationships and quality (accept vault or JSON input, defaults to cwd)
tagex analyze pairs [vault_path]                                      # Auto-extract and analyze
tagex analyze merges [vault_path] --min-usage 5 --export ops.yaml    # Export operations to YAML
tagex analyze quality [vault_path]
tagex analyze synonyms [vault_path] --min-similarity 0.7 --export ops.yaml
tagex analyze plurals [vault_path] --prefer usage --export ops.yaml
tagex analyze suggest [vault_path] [paths...] --min-tags 2 --export suggestions.yaml

# Unified recommendations workflow (consolidates all analyzers, defaults to cwd)
tagex analyze recommendations [vault_path] --export operations.yaml
tagex tag apply operations.yaml                  # Preview changes (safe default)
tagex tag apply operations.yaml --execute        # Apply changes (requires explicit flag)

# Vault maintenance operations
tagex vault cleanup [vault_path]                 # Remove .bak backup files (preview)
tagex vault cleanup --execute                    # Actually remove backups
tagex vault backup [vault_path]                  # Create vault backup
tagex vault verify [vault_path]                  # Verify vault integrity

# Global --tag-types option examples (frontmatter is default)
tagex tag export [vault_path]  # frontmatter only (default)
tagex tag rename --tag-types inline old-tag new-tag             # Preview only
tagex tag rename --tag-types inline old-tag new-tag --execute   # Execute
tagex tag merge --tag-types both tag1 tag2 --into new-tag       # Preview only
tagex stats [vault_path] --tag-types both --format json
```

Or during development:
```bash
# Extract tags
uv run python -m tagex.main extract /path/to/vault [options]

# Tag operations
uv run python -m tagex.main rename /path/to/vault old-tag new-tag
uv run python -m tagex.main /path/to/vault merge tag1 tag2 --into new-tag
uv run python -m tagex.main /path/to/vault delete old-tag
uv run python -m tagex.main stats /path/to/vault --top 20
```

### Options Reference

| Option | Commands | Description | Default |
|:-------|:---------|:------------|:---------|
| `--tag-types` | All tag operations | Tag types to process (`both`, `frontmatter`, `inline`) | `frontmatter` |
| `--output`, `-o` | extract | Output file path | stdout |
| `--format`, `-f` | extract, stats | Output format (`json`, `csv`, `txt` for extract; `text`, `json` for stats) | `json`, `text` |
| `--exclude` | extract | File patterns to exclude (repeatable) | none |
| `--verbose`, `-v` | extract | Enable verbose logging | disabled |
| `--quiet`, `-q` | extract | Suppress summary output | disabled |
| `--no-filter` | extract, stats, analyze | Include all raw tags without filtering | disabled |
| `--execute` | rename, merge, delete, apply, fix-duplicates | Actually apply changes (default is preview mode) | disabled |
| `--top`, `-t` | stats | Number of top tags to display | 20 |
| `--force` | init | Overwrite existing configuration files | disabled |
| `--strict` | validate | Treat warnings as errors | disabled |

### Examples

```bash
# Extract tags (JSON output, frontmatter only by default)
tagex tags extract /path/to/vault
tagex tags extract /path/to/vault -f csv -o tags.csv
tagex tags extract /path/to/vault --tag-types both --no-filter

# Tag operations (preview by default, --execute to apply)
tagex tags rename /path/to/vault work project                            # Preview only
tagex tags rename /path/to/vault work project --execute                  # Actually rename
tagex tags merge /path/to/vault personal diary journal --into writing    # Preview only
tagex tags delete /path/to/vault --tag-types inline obsolete-tag         # Preview only

# Vault statistics
tagex stats /path/to/vault --top 10 --format json
```

**Workflow:**
```bash
# Initialize configuration (first time, defaults to cwd)
tagex init

# Get vault health overview (defaults to cwd)
tagex health

# Fix any duplicate tags: fields (safe by default)
tagex tags fix-duplicates                    # Preview duplicates
tagex tags fix-duplicates --execute          # Fix them

# Generate unified recommendations (recommended workflow, defaults to cwd)
tagex analyze recommendations --export operations.yaml

# Review and edit operations.yaml, then preview
tagex tags apply operations.yaml

# Apply changes (requires explicit --execute flag)
tagex tags apply operations.yaml --execute

# Verify improvements
tagex health

# Clean up backup files if needed
tagex vault cleanup-backups

# Alternative: Run individual analyzers (all default to cwd)
tagex analyze pairs
tagex analyze synonyms
tagex analyze plurals

# Traditional workflow: extract once and analyze multiple times
tagex tags extract -o tags.json
tagex analyze pairs tags.json
tagex analyze merge tags.json
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
| Rename | Single tag renaming across vault | Preview by default, requires --execute |
| Merge | Consolidate multiple tags | Preview by default, requires --execute |
| Delete | Remove tags from all files | Preview by default, requires --execute, inline tag warnings |
| Fix duplicates | Repair duplicate 'tags:' fields in frontmatter | Preview by default, requires --execute |
| Selective processing | Target frontmatter, inline, or both | Type-specific operations |
| Logging | Track all modifications | Integrity checks |
| Structure preservation | Maintain file formatting | No YAML corruption |

### Vault Maintenance

| Operation | Description | Safety Features |
|:----------|:------------|:---------------|
| Cleanup backups | Remove .bak backup files from vault | Safe deletion of backup files |

### Advanced Analysis

The `analyze` command provides comprehensive insights into tag usage patterns, relationships, and quality issues. All analyze commands now support **dual input modes** (vault path or JSON file):

```bash
# Unified recommendations (recommended - consolidates all analyzers)
tagex analyze recommendations /path/to/vault --export operations.yaml
tagex analyze recommendations /path/to/vault --analyzers plurals,synonyms

# Analyze tag pairs and co-occurrence
tagex analyze pairs /path/to/vault           # Auto-extract mode
tagex analyze pairs tags.json                # Pre-extracted mode

# Detect overbroad and generic tags
tagex analyze quality /path/to/vault

# Find plural/singular variants (with configurable preferences)
tagex analyze plurals /path/to/vault --prefer usage

# Detect semantic synonyms (using sentence-transformers)
tagex analyze synonyms /path/to/vault --min-similarity 0.7

# Show related tags (co-occurrence patterns)
tagex analyze synonyms /path/to/vault --show-related

# Suggest tag merge opportunities
tagex analyze merge /path/to/vault --min-usage 3

# Suggest tags for untagged/lightly-tagged notes
tagex analyze suggest --vault-path /vault --min-tags 2
tagex analyze suggest --vault-path /vault --min-tags 1 --export suggestions.yaml
```

| Analysis Type | Description |
|:--------------|:------------|
| **Recommendations** | **Unified analysis consolidating all analyzers into editable YAML operations file** |
| **Content suggestions** | **Suggest tags for notes based on semantic content analysis** |
| Pairs analysis | Tag co-occurrence and clustering patterns |
| Quality analysis | Overbroad tag detection and specificity scoring |
| Plural analysis | Singular/plural variant detection with configurable preference modes |
| Synonym analysis | Semantic similarity detection using sentence-transformers (not co-occurrence) |
| Merge suggestions | Semantic similarity and duplicate detection via TF-IDF embeddings |
| Hub identification | Detect central tags and natural clusters |
| Validation | Filter noise and validate tags |

### Unified Recommendations System

The `recommendations` command consolidates all analyzer suggestions into a single editable YAML file:

```bash
# Generate recommendations from all analyzers
tagex analyze recommendations /vault --export ops.yaml

# Select specific analyzers
tagex analyze recommendations /vault --export ops.yaml --analyzers plurals,synonyms

# Review and edit ops.yaml to:
# - Enable/disable individual operations (enabled: true/false)
# - Modify source/target tags
# - Delete unwanted operations
# - Reorder operations

# Preview changes (default - safe, no modifications)
tagex tags apply ops.yaml

# Apply changes (requires explicit --execute flag)
tagex tags apply ops.yaml --execute
```

**Safety features:**
- Preview mode by default (no `--execute` = no modifications)
- Explicit `--execute` flag required to apply changes
- Deduplication of suggestions from multiple analyzers
- Confidence scores and metadata for informed decisions
- Operation logs for all modifications

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended)

### Install tagex

**As a command-line tool** (recommended):

```bash
uv tool install --editable .
```

**For development**:

```bash
# Clone repository
git clone <repository-url>
cd tagex

# Install dependencies
uv sync

# Run tests
uv run pytest tests/
```

**Verify installation**:

```bash
tagex --help
tagex --version
```

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) if you encounter issues.


## Documentation

See [docs/README.md](docs/README.md) for the complete documentation index with suggested reading flows.

### Quick Links

| Document | Description | Audience |
|:---------|:------------|:---------|
| [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) | Single-page command cheat sheet | Users |
| [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) | Installation, vault setup, git integration | Users & Developers |
| [docs/CONFIGURATION_REFERENCE.md](docs/CONFIGURATION_REFERENCE.md) | `.tagex/` configuration files reference | Users & Developers |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues and solutions | Users & Developers |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and component design | Developers |
| [docs/ANALYTICS.md](docs/ANALYTICS.md) | Tag analysis tools and usage guide | Users & Developers |
| [docs/ALGORITHMS.md](docs/ALGORITHMS.md) | Algorithm implementations and complexity | Developers |
| [tests/README.md](tests/README.md) | Test suite organization and usage | Developers |

