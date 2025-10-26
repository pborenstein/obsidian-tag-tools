# tagex Quick Reference Card

Single-page reference for all tagex commands. For detailed documentation, see [ANALYTICS.md](ANALYTICS.md).

## Installation

```bash
uv tool install --editable .
tagex --help
```

## Core Workflow

```bash
# 1. Get overview
tagex stats /vault

# 2. Extract tags
tagex extract /vault -o tags.json

# 3. Analyze
tagex analyze [command] tags.json

# 4. Apply changes
tagex [operation] /vault --dry-run
tagex [operation] /vault

# 5. Verify
tagex stats /vault
```

## Commands by Function

### Information Gathering

| Command | Purpose | Example |
|:--------|:--------|:--------|
| `stats` | Vault health metrics | `tagex stats /vault --top 20` |
| `extract` | Export tags to file | `tagex extract /vault -o tags.json` |

### Analysis Commands

| Command | Detects | When to Use |
|:--------|:--------|:------------|
| `analyze pairs` | Tags appearing together | Understand relationships |
| `analyze quality` | Overbroad/generic tags | Find tags that are too broad |
| `analyze plurals` | Singular/plural variants | book/books, child/children |
| `analyze synonyms` | Same meaning, different names | python/py, music/audio |
| `analyze merge` | Morphological/semantic variants | writing/writer/writers |

### Tag Operations

| Command | Action | Example |
|:--------|:-------|:--------|
| `rename` | Change one tag | `tagex rename /vault old new --dry-run` |
| `merge` | Combine multiple tags | `tagex merge /vault tag1 tag2 --into new --dry-run` |
| `delete` | Remove tags | `tagex delete /vault unwanted --dry-run` |

## Common Options

| Option | Available On | Effect | Default |
|:-------|:-------------|:-------|:--------|
| `--tag-types` | All commands | frontmatter/inline/both | frontmatter |
| `--dry-run` | Operations | Preview only | disabled |
| `--no-filter` | Extract, analysis | Include technical noise | disabled |
| `-o, --output` | extract | Output file path | stdout |
| `-f, --format` | extract, stats | json/csv/txt or text/json | json, text |
| `--top N` | stats | Show top N tags | 20 |
| `--min-usage N` | Analysis | Minimum tag uses | varies |

## Quick Decision Tree

```
Need to... → Use this command
├─ Understand vault health → tagex stats /vault
├─ Find duplicates
│  ├─ Plural variants (book/books) → analyze plurals
│  ├─ Synonyms (python/py) → analyze synonyms
│  ├─ Typos/morphology (write/writing) → analyze merge
│  └─ Too generic (notes, misc) → analyze quality
├─ See relationships → analyze pairs
└─ Make changes → rename/merge/delete --dry-run
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
```

**Detects:** Abbreviations, acronyms, conceptual equivalents

### analyze merge

**What:** Semantic & morphological duplicates
**Use when:** Typos, morphology, character similarity
**Output:** Merge suggestions from 4 detection methods

```bash
tagex analyze merge tags.json
tagex analyze merge tags.json --min-usage 10
tagex analyze merge tags.json --no-sklearn  # Pattern-based fallback
```

**Methods:** String similarity (85%+), TF-IDF embeddings (0.6+), file overlap (80%+), morphological patterns

## Tag Operations Details

### rename

**What:** Change one tag across vault
**Safety:** Dry-run by default

```bash
tagex rename /vault old-name new-name --dry-run
tagex rename /vault old-name new-name
tagex rename /vault --tag-types inline old new --dry-run
```

### merge

**What:** Consolidate multiple tags into one
**Safety:** Dry-run by default

```bash
tagex merge /vault tag1 tag2 tag3 --into target --dry-run
tagex merge /vault tag1 tag2 --into target
tagex merge /vault --tag-types both tag1 tag2 --into new
```

### delete

**What:** Remove tags from all files
**Safety:** Dry-run by default
**Warning:** Permanently removes tags

```bash
tagex delete /vault unwanted-tag --dry-run
tagex delete /vault tag1 tag2 tag3 --dry-run
tagex delete /vault --tag-types inline temp-tag
```

## Extract Command Details

### Basic extraction

```bash
# JSON to stdout (default)
tagex extract /vault

# JSON to file
tagex extract /vault -o tags.json

# CSV format
tagex extract /vault -f csv -o tags.csv

# Text format
tagex extract /vault -f txt -o tags.txt
```

### Filtering

```bash
# Frontmatter only (default)
tagex extract /vault -o fm_tags.json

# Inline only
tagex extract /vault --tag-types inline -o inline_tags.json

# Both types
tagex extract /vault --tag-types both -o all_tags.json

# Include technical noise
tagex extract /vault --no-filter -o raw_tags.json
```

### Exclusions

```bash
# Exclude patterns (repeatable)
tagex extract /vault --exclude "*.excalidraw.md" --exclude "templates/*"
```

## Stats Command Details

```bash
# Basic stats
tagex stats /vault

# Top 50 tags
tagex stats /vault --top 50

# JSON output
tagex stats /vault --format json

# Include noise
tagex stats /vault --no-filter

# Both tag types
tagex stats /vault --tag-types both
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
# Baseline
tagex stats /vault --top 20 > before.txt

# Extract
tagex extract /vault -o tags.json

# Run all analyses
tagex analyze quality tags.json > quality.txt
tagex analyze plurals tags.json > plurals.txt
tagex analyze synonyms tags.json > synonyms.txt
tagex analyze merge tags.json > merge.txt

# Apply recommended merges (from reports)
tagex merge /vault family families --into families --dry-run
tagex merge /vault family families --into families

# Verify
tagex stats /vault --top 20 > after.txt
diff before.txt after.txt
```

### Find and fix specific issues

```bash
# Find overbroad tags
tagex analyze quality tags.json | grep "extreme"

# Find all plural variants
tagex analyze plurals tags.json

# Find synonyms for python-related tags
tagex extract /vault -o tags.json
grep -i python tags.json
tagex analyze synonyms tags.json | grep -i python
```

### Batch operations

```bash
# Rename multiple tags
tagex rename /vault old1 new1 --dry-run && \
tagex rename /vault old2 new2 --dry-run && \
tagex rename /vault old3 new3 --dry-run

# After dry-run verification, remove --dry-run flags
```

## Configuration Files

### .tagex-synonyms.yaml

Place in vault root to define synonym relationships:

```yaml
synonyms:
  - [python, py, python3]
  - [javascript, js, ecmascript]

prefer:
  technology: [tech, technical]
  documentation: [docs, doc]
```

See [SYNONYM_CONFIGURATION.md](SYNONYM_CONFIGURATION.md) for complete guide.

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
tagex analyze pairs tags.json | grep "Most Connected"
```

### Find underused tags

```bash
tagex stats /vault | grep "Singletons"
tagex extract /vault -o tags.json
jq '.[] | select(.tagCount == 1) | .tag' tags.json
```

### Compare tag types

```bash
tagex extract /vault -o fm.json
tagex extract /vault --tag-types inline -o inline.json
wc -l fm.json inline.json  # Compare counts
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

- Always use `--dry-run` first
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

**Quick Reference Version:** 1.0
**Last Updated:** 2025-10-25
**Project:** tagex - Obsidian Tag Management Tool
