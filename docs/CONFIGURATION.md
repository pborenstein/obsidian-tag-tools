# Configuration Guide

Best practices and recommendations for configuring tagex with your Obsidian vault.

## Table of Contents

- [Vault Setup](#vault-setup)
- [Tagex Configuration](#tagex-configuration)
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

2. **Initialize tagex configuration**:

   ```bash
   tagex init /path/to/vault
   ```

   This creates:
   - `.tagex/config.yaml` - Plural preferences, file exclusions, and other settings
   - `.tagex/synonyms.yaml` - User-defined synonym mappings
   - `.tagex/exclusions.yaml` - Tag exclusions (merge and auto-generated)
   - `.tagex/README.md` - Documentation about the configuration

3. **Extract tags to verify setup**:

   ```bash
   tagex extract /path/to/vault -o tags.json
   ```

4. **Review extraction results**:

   ```bash
   # View top 20 tags
   jq -r '.[0:20] | .[] | "\(.tag)\t\(.tagCount)"' tags.json
   ```

## Tagex Configuration

Tagex stores vault-specific configuration in the `.tagex/` directory within your vault.

### Directory Structure

```
your-vault/
├── .tagex/
│   ├── config.yaml      # General settings (plural preferences, file exclusions)
│   ├── synonyms.yaml    # User-defined synonym mappings
│   ├── exclusions.yaml  # Tag exclusions (merge and auto-generated)
│   └── README.md        # Configuration documentation
├── .obsidian/           # Obsidian's configuration
└── your-notes.md
```

### Initializing Configuration

Create the `.tagex/` directory with template files:

```bash
# Initialize with default templates
tagex init /path/to/vault

# Reinitialize (overwrites existing files)
tagex init /path/to/vault --force
```

### Configuration Files

#### config.yaml

Controls general tagex behavior:

```yaml
# .tagex/config.yaml

plural:
  # Preference mode: usage, plural, or singular
  preference: usage

  # Minimum usage ratio to prefer most-used form (usage mode only)
  # Example: If tag1 has 10 uses and tag2 has 3 uses, ratio is 3.33
  # With threshold 2.0, prefer tag1 (10 > 3 * 2.0)
  usage_ratio_threshold: 2.0
```

**Plural preference modes:**

| Mode | Behavior | Example |
|:-----|:---------|:--------|
| `usage` | Prefer most-used form | `book (67)` + `books (12)` → `book` |
| `plural` | Always prefer plurals | `book (67)` + `books (12)` → `books` |
| `singular` | Always prefer singulars | `books (67)` + `book (12)` → `book` |

#### synonyms.yaml

Define explicit synonym relationships:

```yaml
# .tagex/synonyms.yaml

# Canonical tag as key, synonyms as list values
python:
  - py
  - python3
  - python-lang

javascript:
  - js
  - ecmascript

neuro:
  - neurodivergent
  - neurodivergence
  - neurotype

tech:
  - technology
  - technical
```

**Usage:**
- Tags listed under a key will be suggested for merge into that key
- The `analyze synonyms` command respects these mappings
- Helps codify vault-specific terminology decisions

#### exclusions.yaml

Exclude specific tags from operations and suggestions:

```yaml
# .tagex/exclusions.yaml

exclude_tags:
  # Tags to exclude from merge/synonym suggestions
  # Useful for proper nouns, country names, etc.
  - spain
  - france
  - shakespeare
  - orwell

auto_generated_tags:
  # Tags inserted automatically by other tools
  # These will never be suggested when recommending tags for notes
  - copilot-conversation
  - daily-note
  - auto-generated
  - fragments
```

**Two types of exclusions:**

1. **exclude_tags** - Tags to exclude from merge operations
   - Never suggested for merging/consolidation
   - Useful for proper nouns, place names, historical events
   - Example: `spain`, `shakespeare`, `ww2`

2. **auto_generated_tags** - Tags inserted automatically by tools
   - Never suggested when recommending tags for content
   - Useful for tool-generated tags like `copilot-conversation`, `daily-note`
   - Prevents auto-tags from polluting manual tag suggestions

**Use cases:**

```yaml
# Proper nouns and places
exclude_tags:
  - boston
  - massachusetts
  - shakespeare
  - orwell

# Tool-generated tags
auto_generated_tags:
  - copilot-conversation  # GitHub Copilot
  - daily-note            # Templater/Daily Notes
  - auto-tag              # Obsidian plugins
  - fragments             # Custom automation
```

**Why this matters:**

- **Merge operations**: Prevents consolidating important proper nouns
- **Content suggestions**: Keeps auto-generated tags from being suggested for manual notes
- **Tag quality**: Maintains clean separation between manual and automated tagging

### Validating Configuration

Check configuration files for errors:

```bash
# Basic validation
tagex validate /path/to/vault

# Strict mode (treats warnings as errors)
tagex validate /path/to/vault --strict
```

**What gets validated:**
- YAML syntax correctness
- Valid preference modes
- Numeric values in acceptable ranges
- Synonym conflicts (e.g., canonical tag also listed as synonym)
- File existence and readability

### Configuration Best Practices

1. **Version control your configuration:**
   ```bash
   git add .tagex/
   git commit -m "Add tagex configuration"
   ```

2. **Document decisions in synonyms.yaml:**
   ```yaml
   # Use 'tech' over 'technology' for brevity
   tech:
     - technology
     - technical
   ```

3. **Start with usage mode:**
   - Least disruptive to existing vault
   - Respects established patterns
   - Can always switch later

4. **Validate after editing:**
   ```bash
   # Edit configuration
   vim .tagex/config.yaml

   # Validate changes
   tagex validate /path/to/vault
   ```

5. **Use init --force to reset:**
   ```bash
   # If configuration becomes corrupted
   tagex init /path/to/vault --force
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

# 3. Preview changes (safe by default)
tagex rename /vault old-tag new-tag

# 4. Execute operation
tagex rename /vault old-tag new-tag --execute

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
tagex extract /vault

# Inline only
tagex extract /vault --tag-types inline

# Both types
tagex extract /vault --tag-types both

# Operations support same filtering
tagex rename /vault old-tag new-tag --tag-types both
```

## Exclusion Patterns

Tagex provides two ways to exclude files and directories from processing:

1. **Configuration-based** (recommended): Define exclusions in `.tagex/config.yaml`
2. **CLI-based**: Override or supplement with `--exclude` flag

### Default Behavior

By default, tagex **excludes all dotfiles and dotdirectories**:

```
.obsidian/     ← Excluded by default
.git/          ← Excluded by default
.trash/        ← Excluded by default
.tools/        ← Excluded by default
.claude/       ← Excluded by default
note.md        ← Included (not a dotfile)
templates/     ← Included (not a dotfile)
```

This prevents processing tool-specific directories like `.obsidian`, `.git`, `.vscode`, `.trash`, etc.

### Configuration-Based Exclusions

Define persistent exclusion rules in `.tagex/config.yaml`:

```yaml
file_exclusions:
  # Exclude all dotfiles/directories (default: true)
  exclude_dotfiles: true

  # Allowlist: specific dotfiles to include
  include_dotfiles:
    - .gitignore    # Process .gitignore file

  # Additional patterns to exclude (beyond dotfiles)
  exclude_patterns:
    - "templates/*"           # Exclude templates directory
    - "*.excalidraw.md"       # Exclude Excalidraw files
    - "archive/*"             # Exclude archive directory
    - "_drafts/*"             # Exclude drafts directory
```

**Advantages:**
- Persistent across all commands
- Vault-specific configuration
- No need to repeat flags
- Version-controlled with your vault

### CLI-Based Exclusions

Override or supplement configuration with the `--exclude` flag:

```bash
# Exclude templates directory
tagex tags extract /vault --exclude "templates/*"

# Exclude multiple patterns
tagex tags extract /vault \
  --exclude "templates/*" \
  --exclude "archive/*" \
  --exclude "daily/*"

# Combine with configuration (patterns are merged)
tagex tags extract /vault --exclude "drafts/*"
```

**Use CLI exclusions when:**
- One-time exclusions needed
- Testing different exclusion patterns
- Scripting with dynamic patterns

### Dotfile Handling

#### Including Specific Dotfiles

To process specific dotfiles while excluding all others:

```yaml
# .tagex/config.yaml
file_exclusions:
  exclude_dotfiles: true
  include_dotfiles:
    - .gitignore
    - .project-notes.md
```

#### Disabling Dotfile Exclusion

To process all dotfiles (not recommended):

```yaml
# .tagex/config.yaml
file_exclusions:
  exclude_dotfiles: false
```

### Pattern Syntax

Exclusion patterns use glob-style matching:

| Pattern | Matches | Example |
|:--------|:--------|:--------|
| `*.md` | All markdown files | `note.md`, `file.md` |
| `dir/*` | All files in directory | `templates/template.md` |
| `**/archive/*` | Archive in any subdirectory | `notes/archive/old.md` |
| `daily-*.md` | Files with prefix | `daily-2024-01-15.md` |
| `.tools` | Exact dotfile/directory name | `.tools/` |

### Common Exclusion Scenarios

**Default setup** (already configured by default):

```yaml
# .tagex/config.yaml - Already defaults to this
file_exclusions:
  exclude_dotfiles: true  # Excludes .obsidian, .git, .trash, etc.
  include_dotfiles: []
  exclude_patterns: []
```

**With templates and archive**:

```yaml
file_exclusions:
  exclude_dotfiles: true
  include_dotfiles: []
  exclude_patterns:
    - "templates/*"
    - "archive/*"
    - "_drafts/*"
```

**Daily notes and attachments**:

```yaml
file_exclusions:
  exclude_dotfiles: true
  include_dotfiles: []
  exclude_patterns:
    - "daily/*"
    - "attachments/*"
    - "*.excalidraw.md"
```

### Verification

Check which files are being processed:

```bash
# Extract and see file count
tagex tags extract /vault -o tags.json

# Check specific file appears
grep "suspicious-file" tags.json

# View all processed files
jq -r '.[] | .relativePaths[]' tags.json | sort | uniq
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
