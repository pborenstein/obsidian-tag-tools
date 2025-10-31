# Setup Guide

Complete guide to installing tagex and setting up your Obsidian vault for tag management.

## Table of Contents

- [Vault Setup](#vault-setup)
- [Git Integration](#git-integration)
- [Tag Naming Conventions](#tag-naming-conventions)
- [Frontmatter vs Inline Tags](#frontmatter-vs-inline-tags)
- [Workflow Configuration](#workflow-configuration)
- [Environment Variables](#environment-variables)
- [Performance Tuning](#performance-tuning)
- [Integration with Obsidian](#integration-with-obsidian)
- [Best Practices Summary](#best-practices-summary)
- [Getting Started Checklist](#getting-started-checklist)

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

All commands default to the current working directory, making it convenient to work with your vault by running commands from within it.

1. **Navigate to your vault**:

   ```bash
   cd /path/to/vault
   ```

2. **Test with stats command** (read-only):

   ```bash
   tagex stats
   ```

3. **Initialize tagex configuration**:

   ```bash
   tagex init
   ```

   This creates:
   - `.tagex/config.yaml` - Plural preferences, file exclusions, and other settings
   - `.tagex/synonyms.yaml` - User-defined synonym mappings
   - `.tagex/exclusions.yaml` - Tag exclusions (merge and auto-generated)
   - `.tagex/README.md` - Documentation about the configuration

4. **Check for and fix any frontmatter issues**:

   ```bash
   tagex tag fix              # Preview duplicate 'tags:' fields
   tagex tag fix --execute    # Fix them if needed
   ```

5. **Extract tags to verify setup**:

   ```bash
   tagex tag export -o tags.json
   ```

6. **Review extraction results**:

   ```bash
   # View top 20 tags
   jq -r '.[0:20] | .[] | "\(.tag)\t\(.tagCount)"' tags.json
   ```


## Git Integration

### Recommended .gitignore

Add these patterns to your vault's `.gitignore`:

```gitignore
# tagex configuration (TRACK THIS - it's vault-specific)
# .tagex/

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

**Recommendation:** Track `.tagex/` in git to preserve configuration decisions across machines and share with collaborators.

### Using Git with Tag Operations

**Recommended workflow** for safe tag operations:

```bash
# 1. Ensure clean working directory
cd /path/to/vault
git status

# 2. Create branch for tag changes
git checkout -b tag-cleanup

# 3. Fix any frontmatter issues first
tagex tag fix                   # Preview
tagex tag fix --execute         # Fix if needed

# 4. Preview changes (safe by default, commands default to cwd)
tagex tag rename old-tag new-tag

# 5. Execute operation
tagex tag rename old-tag new-tag --execute

# 6. Review changes
git diff
git status

# 7. Commit if satisfied
git add .
git commit -m "Rename tag: old-tag → new-tag"

# 8. Merge to main
git checkout main
git merge tag-cleanup
```

### What to Track in Git

**Do track:**

- `.tagex/` directory (configuration and synonym mappings)
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

2. **Prefer plural forms** over singular:

   ```yaml
   tags: [books, ideas, projects]     # Good - plural forms
   tags: [book, idea, project]        # Avoid - singular forms
   tags: [books, idea, projects]      # Inconsistent - mixed
   ```

   **Rationale:** Plural tags are more natural when categorizing collections of notes. They read better in queries and lists. Exception: Use singular for abstract concepts (e.g., `mindfulness`, `productivity`) or proper nouns.

3. **Use hyphens** for multi-word tags:

   ```yaml
   tags: [machine-learning, data-science]  # Good
   tags: [machine_learning, datascience]   # Less standard
   ```

4. **Avoid special characters**:

   ```yaml
   tags: [books, reading]           # Good
   tags: [books!, reading?, test&]  # Problematic
   ```

5. **Keep tags concise**:

   ```yaml
   tags: [python, ml, web]                        # Good
   tags: [python-programming-language, machine-learning-algorithms]  # Too verbose
   ```

### Tag Hierarchies

Obsidian supports nested tags with forward slashes. **Use plural forms consistently** throughout hierarchies:

```yaml
tags:
  - projects/work          # Good - plural category
  - projects/personal      # Good
  - areas/health          # Good
  - areas/finance         # Good

# Avoid mixing singular/plural
tags:
  - project/work          # Inconsistent - singular category
  - projects/idea         # Inconsistent - singular subcategory
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

**Hybrid approach** (use both strategically, prefer plurals):

```markdown
---
tags: [meetings, projects, goals]  # High-level categories (plural forms)
---

# Weekly Team Meeting

Discussed #project-alpha timeline and #budget-planning.

Action items:
- Follow up on #quarterly-goals
- Review #team-sync process
```

**Frontmatter:** Primary categories and metadata (use plurals: `books`, `ideas`, `projects`)
**Inline:** Specific topics and contextual references (can be singular for specific instances: `#project-alpha`)

### Tag Type Filtering in tagex

Control which tag types to process:

```bash
# Frontmatter only (default)
tagex tag export /vault

# Inline only
tagex tag export /vault --tag-types inline

# Both types
tagex tag export /vault --tag-types both

# Operations support same filtering
tagex tag rename /vault old-tag new-tag --tag-types both
```


## Workflow Configuration

### Daily Workflow

**Quick tag health check:**

```bash
# Morning routine - check vault health (from vault directory)
cd /path/to/vault
tagex stats --top 10
```

**Weekly cleanup:**

```bash
# Extract and analyze (from vault directory)
cd /path/to/vault
tagex tag export -o weekly-tags.json
tagex analyze pairs weekly-tags.json

# Review merge suggestions
tagex analyze merges weekly-tags.json --min-usage 5
```

### Project-Based Workflow

**Starting new project:**

```bash
# Navigate to vault
cd /path/to/vault

# 1. Extract current state
tagex tag export -o before-cleanup.json

# 2. Review and plan tag consolidation
tagex analyze merges before-cleanup.json

# 3. Execute planned changes (safe by default)
tagex tag rename old-tag new-tag                # Preview
tagex tag rename old-tag new-tag --execute      # Apply

# 4. Verify results
tagex tag export -o after-cleanup.json
```

### Backup Workflow

**Before major tag operations:**

```bash
# 1. Navigate to vault and commit current state
cd /path/to/vault
git add .
git commit -m "Pre-tag-operation backup"

# 2. Extract complete tag inventory
tagex tag export --tag-types both -o backup-tags.json

# 3. Fix any frontmatter issues first
tagex tag fix                        # Preview
tagex tag fix --execute              # Fix if needed

# 4. Preview operation (safe by default)
tagex tag merge tag1 tag2 --into new-tag

# 5. Execute operation
tagex tag merge tag1 tag2 --into new-tag --execute

# 6. Verify and commit
git diff
git commit -am "Merge tags: tag1, tag2 → new-tag"

# 7. Clean up backup files if desired
tagex vault cleanup .
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
tagex tag export "$VAULT" -o "$OUTPUT_DIR/tags-$DATE.json"

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
tagex tag export /vault \
  --exclude "archive/*" \
  --exclude ".obsidian/*" \
  --exclude "daily/*"
```

**Process in sections:**

```bash
# Process active notes only
tagex tag export /vault/active

# Process projects separately
tagex tag export /vault/projects
```

### Memory Constraints

**For analysis on large tag sets:**

```bash
# Use pattern-based fallback (lower memory)
tagex analyze merges tags.json --no-sklearn

# Filter before analysis
tagex tag export /vault --min-usage 3 -o filtered.json
tagex analyze merges filtered.json
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

1. **Preview before executing** (all operations preview by default, use --execute to apply)
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
- [ ] Preview operations (safe by default) before using --execute
- [ ] Set up backup workflow



## Next Steps

- Read [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) for `.tagex/` directory details
- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- See [ANALYTICS.md](ANALYTICS.md) for analysis features
- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for command syntax
