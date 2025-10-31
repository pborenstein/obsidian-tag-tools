# tagex Quick Reference Card

Single-page reference for all tagex commands. For detailed documentation, see [ANALYTICS.md](ANALYTICS.md).

## Installation

```bash
uv tool install --editable .
tagex --help
```

## Core Workflow

```bash
# 1. Initialize configuration (one-time setup)
tagex init

# 2. Get overview (defaults to current directory)
tagex stats

# 3. Export tags (defaults to current directory)
tagex tag export -o tags.json

# 4. Analyze (accepts vault path or JSON file)
tagex analyze [command] tags.json

# 5. Apply changes (safe by default - preview first)
tagex tag [operation]             # Preview changes (uses cwd)
tagex tag [operation] --execute   # Apply changes

# 6. Verify results
tagex stats
```

## Commands by Function

### Information Gathering

| Command | Purpose | Example |
|:--------|:--------|:--------|
| `stats` | Vault health metrics | `tagex stats --top 20` |
| `health` | Comprehensive health report | `tagex health` |
| `tag export` | Export tags to file | `tagex tag export -o tags.json` |

### Analysis Commands

| Command | Detects | When to Use |
|:--------|:--------|:------------|
| `analyze pairs` | Tags appearing together | Understand relationships |
| `analyze quality` | Overbroad/generic tags | Find tags that are too broad |
| `analyze plurals` | Singular/plural variants | book/books, child/children |
| `analyze synonyms` | Same meaning, different names | python/py, music/audio |
| `analyze merges` | Morphological/semantic variants | writing/writer/writers |
| `analyze suggest` | Content-based tag suggestions | Suggest tags for untagged notes |
| `analyze recommendations` | All-in-one analysis | Generate consolidated operations file |

### Tag Operations

| Command | Action | Example |
|:--------|:-------|:--------|
| `tag rename` | Change one tag | `tagex tag rename old new` (preview) |
| `tag merge` | Combine multiple tags | `tagex tag merge tag1 tag2 --into new` (preview) |
| `tag delete` | Remove tags | `tagex tag delete unwanted` (preview) |
| `tag add` | Add tags to files | `tagex tag add file.md python --execute` |
| `tag fix` | Fix duplicate 'tags:' fields | `tagex tag fix` (preview) |
| `tag apply` | Apply YAML operations file | `tagex tag apply ops.yaml` (preview) |

### Configuration Commands

| Command | Action | Example |
|:--------|:-------|:--------|
| `init` | Initialize .tagex/ config | `tagex init` (quick access) |
| `config validate` | Validate configuration | `tagex config validate` |
| `config show` | Display configuration | `tagex config show` |
| `config edit` | Edit config in $EDITOR | `tagex config edit synonyms` |

### Vault Maintenance

| Command | Action | Example |
|:--------|:-------|:--------|
| `vault cleanup` | Remove .bak files | `tagex vault cleanup --execute` |
| `vault backup` | Create vault backup | `tagex vault backup -o backup.tar.gz` |
| `vault verify` | Check vault integrity | `tagex vault verify` |

## Common Options

| Option | Available On | Effect | Default |
|:-------|:-------------|:-------|:--------|
| `[vault_path]` | All commands | Vault directory path | `.` (cwd) |
| `--tag-types` | All tag operations | frontmatter/inline/both | frontmatter |
| `--execute` | Tag operations (rename, merge, delete, add, fix, apply) | Apply changes (preview is default) | disabled |
| `--no-filter` | export, stats, analyze | Include technical noise | disabled |
| `-o, --output` | export, vault backup | Output file path | stdout / auto |
| `-f, --format` | export, stats | json/csv/txt or text/json | json, text |
| `--top N` | stats | Show top N tags | 20 |
| `--min-usage N` | analyze commands | Minimum tag uses | varies |
| `--force` | init | Overwrite existing config | disabled |
| `--strict` | config validate | Treat warnings as errors | disabled |
| `--export` | analyze commands | Export to YAML operations file | none |

## Quick Decision Tree

```
Need to... → Use this command
├─ Set up vault → tagex init
├─ Understand vault health → tagex stats (or tagex health)
├─ View configuration → tagex config show
├─ Fix frontmatter issues → tagex tag fix
├─ Find duplicates
│  ├─ Plural variants (book/books) → analyze plurals
│  ├─ Synonyms (python/py) → analyze synonyms
│  ├─ Typos/morphology (write/writing) → analyze merges
│  └─ Too generic (notes, misc) → analyze quality
├─ See relationships → analyze pairs
├─ Suggest tags for notes → analyze suggest
├─ Get all recommendations → analyze recommendations --export ops.yaml
├─ Make changes → tag rename/merge/delete/add (preview), then --execute
├─ Batch operations → tag apply ops.yaml (preview), then --execute
└─ Maintain vault → vault cleanup/backup/verify
```

## Analysis Command Details

### analyze pairs

**What:** Tag co-occurrence patterns
**Use when:** Understanding which tags appear together
**Output:** Pair counts, hub tags, clusters

```bash
tagex analyze pairs tags.json
tagex analyze pairs tags.json --min-pairs 5
tagex analyze pairs tags.json --no-filter
```

### analyze quality

**What:** Overbroad tag detection
**Use when:** Tags appear in too many files (>30%)
**Output:** Coverage ratios, specificity scores, refinement suggestions

```bash
tagex analyze quality tags.json
tagex analyze quality tags.json --min-usage 10
```

### analyze plurals

**What:** Singular/plural variants
**Use when:** book/books, child/children splits
**Output:** Variant groups with merge recommendations

```bash
tagex analyze plurals tags.json
tagex analyze plurals tags.json --min-usage 5
tagex analyze plurals /vault --export ops.yaml     # Export to YAML
```

**Handles:** 34 irregular plurals + 5 pattern rules + compounds

### analyze synonyms

**What:** Context-based synonym detection
**Use when:** Different names, same meaning
**Output:** Synonym groups via Jaccard similarity (≥0.70)

```bash
tagex analyze synonyms tags.json
tagex analyze synonyms tags.json --min-shared 5
tagex analyze synonyms tags.json --min-similarity 0.8
tagex analyze synonyms /vault --export ops.yaml     # Export to YAML
```

**Detects:** Abbreviations, acronyms, conceptual equivalents

### analyze merges

**What:** Semantic & morphological duplicates
**Use when:** Typos, morphology, character similarity
**Output:** Merge suggestions from 4 detection methods

```bash
tagex analyze merges tags.json
tagex analyze merges tags.json --min-usage 10
tagex analyze merges tags.json --no-sklearn  # Pattern-based fallback
tagex analyze merges --export ops.yaml       # Export to YAML (uses cwd)
```

**Methods:** String similarity (85%+), TF-IDF embeddings (0.6+), file overlap (80%+), morphological patterns

### analyze suggest

**What:** Content-based tag suggestions for untagged/lightly-tagged notes
**Use when:** Notes have few or no tags
**Output:** Tag suggestions based on content analysis

```bash
tagex analyze suggest                        # Analyze all notes in cwd
tagex analyze suggest --min-tags 2           # Only notes with < 2 tags
tagex analyze suggest projects/              # Specific directory
tagex analyze suggest --export suggestions.yaml
```

**Uses:** TF-IDF and semantic similarity to match note content with existing tags

### analyze recommendations

**What:** Consolidated analysis from all analyzers
**Use when:** You want a comprehensive cleanup plan
**Output:** Single YAML operations file with all suggestions

```bash
tagex analyze recommendations --export ops.yaml
tagex analyze recommendations --analyzers synonyms,plurals
tagex analyze recommendations --export ops.yaml --analyzers synonyms,plurals,singletons
```

**Combines:** Synonym detection, plural normalization, singleton merging

## Tag Operations Details

### tag rename

**What:** Change one tag across vault
**Safety:** Dry-run by default

```bash
tagex tag rename old-name new-name              # Preview changes (uses cwd)
tagex tag rename old-name new-name --execute    # Apply changes
tagex tag rename --tag-types inline old new     # Preview inline only
tagex tag rename /vault old new                 # Preview with explicit vault path
```

### tag merge

**What:** Consolidate multiple tags into one
**Safety:** Dry-run by default

```bash
tagex tag merge tag1 tag2 tag3 --into target              # Preview (uses cwd)
tagex tag merge tag1 tag2 --into target --execute         # Apply
tagex tag merge --tag-types both tag1 tag2 --into new     # Both tag types
tagex tag merge /vault tag1 tag2 --into new               # Explicit vault path
```

### tag delete

**What:** Remove tags from all files
**Safety:** Dry-run by default
**Warning:** Permanently removes tags

```bash
tagex tag delete unwanted-tag                  # Preview (uses cwd)
tagex tag delete tag1 tag2 tag3                # Preview multiple
tagex tag delete --tag-types inline temp-tag   # Preview inline only
tagex tag delete unwanted --execute            # Apply deletion
```

### tag add

**What:** Add tags to specific files
**Safety:** Dry-run by default

```bash
tagex tag add note.md python programming       # Preview adding tags
tagex tag add note.md python --execute         # Apply tag addition
tagex tag add /vault/note.md ml ai --execute   # Explicit vault and file path
```

**Use when:** You want to add tags to specific files programmatically.

### tag fix

**What:** Fix duplicate 'tags:' fields in frontmatter
**Safety:** Dry-run by default

```bash
tagex tag fix                # Preview duplicates (uses cwd)
tagex tag fix --execute      # Fix duplicates
tagex tag fix /vault         # Preview with explicit vault path
```

**Use when:** You have files with multiple 'tags:' keys in frontmatter, which can happen after manual edits or plugin conflicts.

### tag apply

**What:** Apply batch operations from YAML file
**Safety:** Dry-run by default

```bash
tagex tag apply operations.yaml              # Preview all operations
tagex tag apply operations.yaml --execute    # Apply all operations
tagex tag apply /vault ops.yaml              # Explicit vault path
```

**Use when:** Applying recommendations from `analyze recommendations` or custom YAML operations files.

## Tag Export Command Details

### Basic export

```bash
# JSON to stdout (default)
tagex tag export

# JSON to file
tagex tag export -o tags.json

# CSV format
tagex tag export -f csv -o tags.csv

# Text format
tagex tag export -f txt -o tags.txt

# Explicit vault path
tagex tag export /vault -o tags.json
```

### Filtering

```bash
# Frontmatter only (default)
tagex tag export -o fm_tags.json

# Inline only
tagex tag export --tag-types inline -o inline_tags.json

# Both types
tagex tag export --tag-types both -o all_tags.json

# Include technical noise
tagex tag export --no-filter -o raw_tags.json
```

### Exclusions

```bash
# Exclude patterns (repeatable)
tagex tag export --exclude "*.excalidraw.md" --exclude "templates/*"
```

## Stats Command Details

```bash
# Basic stats (uses cwd)
tagex stats

# Top 50 tags
tagex stats --top 50

# JSON output
tagex stats --format json

# Include noise
tagex stats --no-filter

# Both tag types
tagex stats --tag-types both

# Explicit vault path
tagex stats /vault --top 20
```

**Output includes:**
- Total tags and uses
- Tag distribution (singletons, doubletons, etc.)
- Coverage (% files with tags)
- Health metrics (diversity, concentration)
- Top N tags by usage

## Workflow Examples

### Complete tag cleanup

```bash
# Initialize configuration
tagex init

# Baseline
tagex stats --top 20 > before.txt

# Export tags
tagex tag export -o tags.json

# Run all analyses
tagex analyze quality tags.json > quality.txt
tagex analyze plurals tags.json > plurals.txt
tagex analyze synonyms tags.json > synonyms.txt
tagex analyze merges tags.json > merge.txt

# OR: Get consolidated recommendations
tagex analyze recommendations --export ops.yaml

# Apply recommended merges (from reports)
tagex tag merge family families --into families              # Preview
tagex tag merge family families --into families --execute    # Apply

# OR: Apply from operations file
tagex tag apply ops.yaml              # Preview
tagex tag apply ops.yaml --execute    # Apply

# Verify
tagex stats --top 20 > after.txt
diff before.txt after.txt
```

### Find and fix specific issues

```bash
# Find overbroad tags
tagex analyze quality tags.json | grep "extreme"

# Find all plural variants
tagex analyze plurals

# Find synonyms for python-related tags
tagex tag export -o tags.json
grep -i python tags.json
tagex analyze synonyms tags.json | grep -i python

# Fix frontmatter issues
tagex tag fix                # Preview
tagex tag fix --execute      # Apply
```

### Batch operations

```bash
# Preview multiple tag renames
tagex tag rename old1 new1
tagex tag rename old2 new2
tagex tag rename old3 new3

# After verification, add --execute to each command
tagex tag rename old1 new1 --execute
tagex tag rename old2 new2 --execute
tagex tag rename old3 new3 --execute

# OR: Use operations file for batch changes
tagex analyze recommendations --export ops.yaml
# Edit ops.yaml to enable/disable specific operations
tagex tag apply ops.yaml --execute
```

## Configuration Files

Configuration is stored in `.tagex/` directory within each vault. Initialize with `tagex init`.

### .tagex/config.yaml

General configuration settings:

```yaml
plural:
  preference: usage  # usage, plural, or singular
  usage_ratio_threshold: 2.0
```

### .tagex/synonyms.yaml

Define synonym relationships:

```yaml
python:
  - py
  - python3
javascript:
  - js
  - ecmascript
```

### .tagex/exclusions.yaml

Tags to exclude from merge suggestions:

```yaml
exclude_tags:
  - spain
  - france
  - proper-noun-tag
```

**Commands:**
- `tagex init` - Create configuration directory
- `tagex config show` - Display current configuration
- `tagex config edit [config|synonyms|exclusions]` - Edit in $EDITOR
- `tagex config validate` - Check configuration validity

## Output Formats

### JSON (default)

```json
[
  {
    "tag": "python",
    "tagCount": 67,
    "files": ["note1.md", "note2.md", ...],
    "source": "frontmatter"
  }
]
```

### CSV

```csv
tag,tagCount,files,source
python,67,"note1.md,note2.md,...",frontmatter
```

### Text

```
python (67 uses)
  note1.md
  note2.md
  ...
```

## Exit Codes

| Code | Meaning |
|:-----|:--------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |

## Common Patterns

### Find hub tags

```bash
tagex analyze pairs | grep "Most Connected"
```

### Find underused tags

```bash
tagex stats | grep "Singletons"
tagex tag export -o tags.json
jq '.[] | select(.tagCount == 1) | .tag' tags.json
```

### Compare tag types

```bash
tagex tag export -o fm.json
tagex tag export --tag-types inline -o inline.json
wc -l fm.json inline.json  # Compare counts
```

### Add tags to multiple files

```bash
# Add tags to specific files
tagex tag add projects/ml-notes.md machine-learning python --execute
tagex tag add projects/ai-research.md artificial-intelligence research --execute
```

### Create and apply batch operations

```bash
# Generate recommendations
tagex analyze recommendations --export ops.yaml

# Review the file
cat ops.yaml

# Apply selectively (edit YAML to enable/disable operations)
tagex tag apply ops.yaml --execute
```

## Performance

| Vault Size | Extract | Stats | Analysis |
|:-----------|:--------|:------|:---------|
| ~300 files | <1s | <1s | 1-3s |
| ~1,000 files | 2-3s | 1s | 5-15s |
| ~10,000 files | 20-30s | 5s | 60-180s |

**Tip:** Use `--min-usage` to speed up analysis on large vaults.

## Troubleshooting

### No tags found

Check:
- `--tag-types` setting (default: frontmatter only)
- YAML syntax in frontmatter
- File exclusion patterns

### Analysis seems wrong

- Extract with `--no-filter` to see raw tags
- Check tag validation rules in `tagex/utils/tag_normalizer.py`
- Verify JSON file is recent (`tagex extract` again)

### Operation didn't work

- Preview mode is default (safe by default)
- Check operation logs in current directory
- Verify tag exists: `grep -r "tag-name" /vault`

## Related Documentation

- **[README.md](../README.md)** - Project overview and installation
- **[ANALYTICS.md](ANALYTICS.md)** - Complete analysis guide with algorithms
- **[ALGORITHMS.md](ALGORITHMS.md)** - Technical algorithm details
- **[SYNONYM_CONFIGURATION.md](SYNONYM_CONFIGURATION.md)** - Synonym config format
- **[CONFIGURATION.md](CONFIGURATION.md)** - Vault setup and best practices
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues

---

**Quick Reference Version:** 2.0 (CLI Restructure)
**Last Updated:** 2025-10-30
**Project:** tagex - Obsidian Tag Management Tool

## Command Structure Changes (v2.0)

This reference reflects the major CLI restructure in v2.0:

- **`tags` → `tag`** (singular group name)
- **`tags extract` → `tag export`** (renamed command)
- **`tags fix-duplicates` → `tag fix`** (shorter)
- **`validate` → `config validate`** (grouped)
- **`analyze merge` → `analyze merges`** (renamed)
- **`vault cleanup-backups` → `vault cleanup`** (shorter)

**New commands:**
- `tag add` - Add tags to specific files
- `config show` - Display configuration
- `config edit` - Edit configuration in $EDITOR
- `vault backup` - Create vault backups
- `vault verify` - Verify vault integrity

**All vault_path arguments now optional** (default to current directory)

See [RESTRUCTURE_COMPLETE.md](RESTRUCTURE_COMPLETE.md) for full migration guide.
