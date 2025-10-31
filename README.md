# Obsidian Tag Management Tool

Extract, analyze, and modify tags in Obsidian vault markdown files.

Safe by default (preview mode requires --execute flag to apply changes).

## Quick Start

Most common workflow:

```bash
# Install
uv tool install --editable .

# Initialize vault
cd "$HOME/Obsidian/MyVault"
tagex init

# View current state
tagex stats
tagex health

# Generate recommendations
tagex analyze recommendations --export operations.yaml

# Review operations.yaml, then preview
tagex tag apply operations.yaml

# Apply changes
tagex tag apply operations.yaml --execute
```

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for detailed walkthrough or [docs/HAPPY_PATH.md](docs/HAPPY_PATH.md) for command reference.

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
| `--execute` | rename, merge, delete, apply, fix | Actually apply changes (default is preview mode) | disabled |
| `--top`, `-t` | stats | Number of top tags to display | 20 |
| `--force` | init | Overwrite existing configuration files | disabled |
| `--strict` | validate | Treat warnings as errors | disabled |

### Examples

```bash
# Export tags (JSON output, frontmatter only by default)
tagex tag export /path/to/vault
tagex tag export /path/to/vault -f csv -o tags.csv
tagex tag export /path/to/vault --tag-types both --no-filter

# Tag operations (preview by default, --execute to apply)
tagex tag rename /path/to/vault work project                            # Preview only
tagex tag rename /path/to/vault work project --execute                  # Actually rename
tagex tag merge /path/to/vault personal diary journal --into writing    # Preview only
tagex tag delete /path/to/vault --tag-types inline obsolete-tag         # Preview only

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
tagex tag fix                    # Preview duplicates
tagex tag fix --execute          # Fix them

# Generate unified recommendations (recommended workflow, defaults to cwd)
tagex analyze recommendations --export operations.yaml

# Review and edit operations.yaml, then preview
tagex tag apply operations.yaml

# Apply changes (requires explicit --execute flag)
tagex tag apply operations.yaml --execute

# Verify improvements
tagex health

# Clean up backup files if needed
tagex vault cleanup

# Alternative: Run individual analyzers (all default to cwd)
tagex analyze pairs
tagex analyze synonyms
tagex analyze plurals

# Traditional workflow: export once and analyze multiple times
tagex tag export -o tags.json
tagex analyze pairs tags.json
tagex analyze merges tags.json
```

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

See [docs/README.md](docs/README.md) for complete documentation index and reading flows.

### Quick Links

| Document | Description | Audience |
|:---------|:------------|:---------|
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | Step-by-step workflow walkthrough | New users |
| [docs/HAPPY_PATH.md](docs/HAPPY_PATH.md) | Minimal command reference | All users |
| [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) | Complete command cheat sheet | All users |
| [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) | Installation, vault setup, git integration | Users & Developers |
| [docs/CONFIGURATION_REFERENCE.md](docs/CONFIGURATION_REFERENCE.md) | `.tagex/` configuration files reference | Users & Developers |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues and solutions | Users & Developers |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture and component design | Developers |
| [docs/ANALYTICS.md](docs/ANALYTICS.md) | Tag analysis tools and usage guide | Users & Developers |
| [docs/ALGORITHMS.md](docs/ALGORITHMS.md) | Algorithm implementations and complexity | Developers |
| [tests/README.md](tests/README.md) | Test suite organization and usage | Developers |

