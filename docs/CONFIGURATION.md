# Configuration Guide

Best practices and recommendations for configuring tagex with your Obsidian vault.

## Table of Contents

- [Vault Setup](#vault-setup)
- [Git Integration](#git-integration)
- [Tag Naming Conventions](#tag-naming-conventions)
- [Frontmatter vs Inline Tags](#frontmatter-vs-inline-tags)
- [Exclusion Patterns](#exclusion-patterns)
- [Workflow Configuration](#workflow-configuration)

## Vault Setup

### Prerequisites

Before using tagex, ensure you have:

1. **Python 3.10 or higher**

   ```bash
   python3 --version
   ```

2. **UV package manager** (recommended)

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **An Obsidian vault** with markdown files

### Installation

Install tagex as a command-line tool:

```bash
# Clone or navigate to tagex directory
cd /path/to/tagex

# Install with uv (recommended)
uv tool install --editable .

# Verify installation
tagex --help
```

### First-Time Setup

1. **Test with stats command** (read-only):

   ```bash
   tagex stats /path/to/vault
   ```

2. **Extract tags to verify setup**:

   ```bash
   tagex extract /path/to/vault -o tags.json
   ```

3. **Review extraction results**:

   ```bash
   # View top 20 tags
   jq -r '.[0:20] | .[] | "\(.tag)\t\(.tagCount)"' tags.json
   ```

## Git Integration

### Recommended .gitignore

Add these patterns to your vault's `.gitignore`:

```gitignore
# tagex outputs (optional - decide based on workflow)
tags.json
tags.csv
*_tags.json

# tagex logs (usually want to ignore)
logs/*.json
!logs/README.md

# Python artifacts
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.pytest_cache/

# Virtual environments
.venv/
venv/
env/

# OS files
.DS_Store
```

### Using Git with Tag Operations

**Recommended workflow** for safe tag operations:

```bash
# 1. Ensure clean working directory
cd /path/to/vault
git status

# 2. Create branch for tag changes
git checkout -b tag-cleanup

# 3. Preview changes with dry-run
tagex rename /vault old-tag new-tag --dry-run

# 4. Execute operation
tagex rename /vault old-tag new-tag

# 5. Review changes
git diff
git status

# 6. Commit if satisfied
git add .
git commit -m "Rename tag: old-tag → new-tag"

# 7. Merge to main
git checkout main
git merge tag-cleanup
```

### What to Track in Git

**Do track:**

- Operation logs (for audit trail)
- Tag extraction results (for analysis history)
- Documentation of tag conventions

**Don't track:**

- Temporary extraction files
- Python cache files
- Virtual environment

## Tag Naming Conventions

### Best Practices

1. **Use lowercase** for consistency:

   ```yaml
   tags: [project, work, notes]  # Good
   tags: [Project, WORK, Notes]  # Inconsistent
   ```

2. **Use hyphens** for multi-word tags:

   ```yaml
   tags: [machine-learning, data-science]  # Good
   tags: [machine_learning, datascience]   # Less standard
   ```

3. **Avoid special characters**:

   ```yaml
   tags: [books, reading]           # Good
   tags: [books!, reading?, test&]  # Problematic
   ```

4. **Keep tags concise**:

   ```yaml
   tags: [python, ml, web]                        # Good
   tags: [python-programming-language, machine-learning-algorithms]  # Too verbose
   ```

### Tag Hierarchies

Obsidian supports nested tags with forward slashes:

```yaml
tags:
  - projects/work
  - projects/personal
  - areas/health
  - areas/finance
```

**Benefits:**

- Logical organization
- Easy filtering by prefix
- Clear relationships

**tagex handling:**

- Extracts full hierarchical tags
- Preserves slashes in operations
- Can rename entire hierarchies

### Tag vs Tags Field

Both are valid in frontmatter:

```yaml
---
# Single tag
tag: work
---

---
# Multiple tags (array)
tags: [work, notes, ideas]
---

---
# Multiple tags (YAML list)
tags:
  - work
  - notes
  - ideas
---
```

**Recommendation:** Use `tags` (plural) consistently, even for single tag:

```yaml
tags: [work]  # Preferred - consistent structure
```

## Frontmatter vs Inline Tags

### Frontmatter Tags

Located in YAML header at top of file:

```markdown
---
tags: [work, notes, ideas]
title: My Note
date: 2024-01-15
---

Note content here...
```

**Characteristics:**

- Structured metadata
- Easy to bulk-edit
- Not visible in reading view
- Standard location for tags

**Best for:**

- Primary categorization
- Systematic organization
- Automation and scripting
- Cross-vault consistency

### Inline Tags

Hashtags within note content:

```markdown
---
tags: [work]
---

Meeting notes about #project-alpha and #team-sync.

We discussed #quarterly-goals and #budget-planning.
```

**Characteristics:**

- Contextual placement
- Visible in reading view
- Part of note content
- Flexible positioning

**Best for:**

- Topic mentions
- Contextual references
- Quick tagging while writing
- Subject emphasis

### Recommended Usage Pattern

**Hybrid approach** (use both strategically):

```markdown
---
tags: [work, meetings, 2024-q1]  # High-level categories
---

# Weekly Team Meeting

Discussed #project-alpha timeline and #budget-planning.

Action items:
- Follow up on #quarterly-goals
- Review #team-sync process
```

**Frontmatter:** Primary categories and metadata
**Inline:** Specific topics and contextual references

### Tag Type Filtering in tagex

Control which tag types to process:

```bash
# Frontmatter only (default)
tagex extract /vault

# Inline only
tagex extract /vault --tag-types inline

# Both types
tagex extract /vault --tag-types both

# Operations support same filtering
tagex rename /vault old-tag new-tag --tag-types both
```

## Exclusion Patterns

### Common Exclusion Patterns

Exclude files/directories you don't want processed:

```bash
# Exclude templates directory
tagex extract /vault --exclude "templates/*"

# Exclude multiple patterns
tagex extract /vault \
  --exclude "templates/*" \
  --exclude "archive/*" \
  --exclude ".obsidian/*"

# Exclude daily notes
tagex extract /vault --exclude "daily/*"
```

### Pattern Syntax

Uses glob-style patterns:

| Pattern | Matches | Example |
|:--------|:--------|:--------|
| `*.md` | All markdown files | `note.md`, `file.md` |
| `dir/*` | All files in directory | `templates/template.md` |
| `**/archive/*` | Archive in any subdirectory | `notes/archive/old.md` |
| `daily-*.md` | Files with prefix | `daily-2024-01-15.md` |

### Recommended Exclusions

Common directories to exclude:

```bash
tagex extract /vault \
  --exclude ".obsidian/*" \      # Obsidian config
  --exclude "templates/*" \       # Template files
  --exclude "archive/*" \         # Archived notes
  --exclude ".trash/*" \          # Deleted files
  --exclude "drafts/*"            # Work in progress
```

## Workflow Configuration

### Daily Workflow

**Quick tag health check:**

```bash
# Morning routine - check vault health
tagex stats /vault --top 10
```

**Weekly cleanup:**

```bash
# Extract and analyze
tagex extract /vault -o weekly-tags.json
tagex analyze pairs weekly-tags.json

# Review merge suggestions
tagex analyze merge weekly-tags.json --min-usage 5
```

### Project-Based Workflow

**Starting new project:**

```bash
# 1. Extract current state
tagex extract /vault -o before-cleanup.json

# 2. Review and plan tag consolidation
tagex analyze merge before-cleanup.json

# 3. Execute planned changes
tagex rename /vault old-tag new-tag --dry-run
tagex rename /vault old-tag new-tag

# 4. Verify results
tagex extract /vault -o after-cleanup.json
```

### Backup Workflow

**Before major tag operations:**

```bash
# 1. Git commit current state
cd /vault
git add .
git commit -m "Pre-tag-operation backup"

# 2. Extract complete tag inventory
tagex extract /vault --tag-types both -o backup-tags.json

# 3. Run operation with dry-run first
tagex merge /vault tag1 tag2 --into new-tag --dry-run

# 4. Execute operation
tagex merge /vault tag1 tag2 --into new-tag

# 5. Verify and commit
git diff
git commit -am "Merge tags: tag1, tag2 → new-tag"
```

### Automated Analysis

**Cron job for weekly reports:**

```bash
#!/bin/bash
# save as: ~/scripts/tagex-weekly.sh

VAULT="$HOME/Obsidian/MyVault"
OUTPUT_DIR="$HOME/tagex-reports"
DATE=$(date +%Y-%m-%d)

# Extract tags
tagex extract "$VAULT" -o "$OUTPUT_DIR/tags-$DATE.json"

# Generate statistics
tagex stats "$VAULT" --format json > "$OUTPUT_DIR/stats-$DATE.json"

# Analyze relationships
tagex analyze pairs "$OUTPUT_DIR/tags-$DATE.json" > "$OUTPUT_DIR/pairs-$DATE.txt"
```

**Add to crontab:**

```bash
# Run every Sunday at 9 AM
0 9 * * 0 ~/scripts/tagex-weekly.sh
```

## Environment Variables

### Python Path Configuration

If using development installation:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PYTHONPATH="/path/to/tagex:$PYTHONPATH"
```

### UV Configuration

Configure uv tool directory:

```bash
# Add uv bin to PATH
export PATH="$HOME/.local/bin:$PATH"
```

## Performance Tuning

### Large Vaults (>10,000 files)

**Use exclusion patterns** to reduce scope:

```bash
tagex extract /vault \
  --exclude "archive/*" \
  --exclude ".obsidian/*" \
  --exclude "daily/*"
```

**Process in sections:**

```bash
# Process active notes only
tagex extract /vault/active

# Process projects separately
tagex extract /vault/projects
```

### Memory Constraints

**For analysis on large tag sets:**

```bash
# Use pattern-based fallback (lower memory)
tagex analyze merge tags.json --no-sklearn

# Filter before analysis
tagex extract /vault --min-usage 3 -o filtered.json
tagex analyze merge filtered.json
```

## Integration with Obsidian

### Obsidian Settings

**Recommended settings** for tag compatibility:

1. **Files & Links**:
   - Automatically update internal links: Yes

2. **Editor**:
   - Strict line breaks: Yes (preserves formatting)

3. **Files & Links**:
   - Detect all file extensions: Yes

### Sync Considerations

**If using Obsidian Sync:**

- Close Obsidian before tag operations
- Let sync complete before reopening
- Check for conflicts after sync

**If using Git sync:**

- Commit before tag operations
- Pull latest changes first
- Push after operations complete

## Best Practices Summary

1. **Always use `--dry-run`** before operations
2. **Keep git history** of tag changes
3. **Use consistent naming** (lowercase, hyphens)
4. **Separate frontmatter and inline** tag purposes
5. **Exclude irrelevant directories** for performance
6. **Review logs** after operations
7. **Extract regularly** to track tag evolution
8. **Analyze before cleanup** to inform decisions

## Getting Started Checklist

- [ ] Install Python 3.10+ and uv
- [ ] Install tagex with `uv tool install --editable .`
- [ ] Run `tagex stats /vault` to verify setup
- [ ] Create vault `.gitignore` for tagex outputs
- [ ] Establish tag naming conventions
- [ ] Document exclusion patterns
- [ ] Test with `--dry-run` first
- [ ] Set up backup workflow

## Next Steps

- Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [ANALYTICS.md](ANALYTICS.md) for analysis features
- Check [README.md](../README.md) for command reference
