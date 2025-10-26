# Obsidian Tag Management Tool

Extract, analyze, and modify tags in Obsidian vault markdown files using the `tagex` command-line tool.

## Project Overview

tagex is a command-line tool for managing tags across entire Obsidian vaults. It provides comprehensive tag extraction, analysis, and modification operations with safety features like dry-run mode and operation logging.

**Key capabilities:**

- Extract tags from frontmatter YAML and inline hashtags
- Analyze tag relationships and co-occurrence patterns
- Rename, merge, and delete tags across entire vaults
- Generate vault health metrics and statistics
- Detect semantic similarities for tag consolidation
- Unified recommendations system for streamlined tag cleanup
- Safe operations with preview mode by default and comprehensive logging

## Quick Start

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
# Configuration management
tagex init /path/to/vault                    # Initialize .tagex/ configuration
tagex validate /path/to/vault                # Validate configuration files

# Extract tags from vault
tagex extract /path/to/vault [options]

# Rename a tag across all files
tagex rename /path/to/vault old-tag new-tag [--dry-run]

# Merge multiple tags into one
tagex merge /path/to/vault tag1 tag2 tag3 --into target-tag [--dry-run]

# Delete tags from all files
tagex delete /path/to/vault tag-to-remove another-tag --dry-run

# Get comprehensive vault statistics
tagex stats /path/to/vault --top 15

# Get comprehensive health report (unified analysis)
tagex health /path/to/vault

# Analyze tag relationships and quality (accept vault or JSON input)
tagex analyze pairs /path/to/vault           # Auto-extract and analyze
tagex analyze merge tags.json --min-usage 5  # Or use pre-extracted JSON
tagex analyze quality /path/to/vault
tagex analyze synonyms /path/to/vault --min-similarity 0.7
tagex analyze plurals /path/to/vault --prefer usage

# Unified recommendations workflow (consolidates all analyzers)
tagex analyze recommendations /path/to/vault --export operations.yaml
tagex apply operations.yaml                  # Preview changes (safe default)
tagex apply operations.yaml --execute        # Apply changes (requires explicit flag)

# Global --tag-types option examples (frontmatter is default)
tagex extract /path/to/vault  # frontmatter only (default)
tagex rename /path/to/vault --tag-types inline old-tag new-tag --dry-run
tagex merge /path/to/vault --tag-types both tag1 tag2 --into new-tag
tagex stats /path/to/vault --tag-types both --format json
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
tagex extract /path/to/vault
tagex extract /path/to/vault -f csv -o tags.csv
tagex extract /path/to/vault --tag-types both --no-filter

# Tag operations with dry-run preview
tagex rename /path/to/vault work project --dry-run
tagex merge /path/to/vault personal diary journal --into writing --dry-run
tagex delete /path/to/vault --tag-types inline obsolete-tag --dry-run

# Vault statistics
tagex stats /path/to/vault --top 10 --format json
```

**Workflow:**
```bash
# Initialize configuration (first time)
tagex init /vault

# Get vault health overview
tagex health /vault

# Generate unified recommendations (recommended workflow)
tagex analyze recommendations /vault --export operations.yaml

# Review and edit operations.yaml, then preview
tagex apply operations.yaml

# Apply changes (requires explicit --execute flag)
tagex apply operations.yaml --execute

# Verify improvements
tagex health /vault

# Alternative: Run individual analyzers
tagex analyze pairs /vault
tagex analyze synonyms /vault
tagex analyze plurals /vault

# Traditional workflow: extract once and analyze multiple times
tagex extract /vault -o tags.json
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
| Rename | Single tag renaming across vault | Preview mode, dry-run |
| Merge | Consolidate multiple tags | Multi-tag input validation |
| Delete | Remove tags from all files | Inline tag warnings |
| Selective processing | Target frontmatter, inline, or both | Type-specific operations |
| Logging | Track all modifications | Integrity checks |
| Structure preservation | Maintain file formatting | No YAML corruption |

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
```

| Analysis Type | Description |
|:--------------|:------------|
| **Recommendations** | **Unified analysis consolidating all analyzers into editable YAML operations file** |
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
tagex apply ops.yaml

# Apply changes (requires explicit --execute flag)
tagex apply ops.yaml --execute
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
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Vault setup, git integration, and best practices | Users & Developers |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues and solutions | Users & Developers |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and component design | Developers |
| [docs/ANALYTICS.md](docs/ANALYTICS.md) | Tag analysis tools and usage guide | Users & Developers |
| [docs/SEMANTIC_ANALYSIS.md](docs/SEMANTIC_ANALYSIS.md) | Semantic similarity detection algorithms | Developers |
| [tests/README.md](tests/README.md) | Test suite organization and usage | Developers |

