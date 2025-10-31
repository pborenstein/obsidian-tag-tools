# Configuration Reference

Reference guide for `.tagex/` directory configuration files.

## Table of Contents

- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Initializing Configuration](#initializing-configuration)
- [Configuration Files](#configuration-files)
- [Validating Configuration](#validating-configuration)
- [Best Practices](#best-practices)

## Overview

Tagex stores vault-specific configuration in the `.tagex/` directory within your vault. This reference documents the structure and format of each configuration file.

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
# Navigate to your vault
cd /path/to/vault

# Initialize with default templates (defaults to cwd)
tagex init

# Or specify a path explicitly
tagex init /path/to/vault

# Reinitialize (overwrites existing files)
tagex init --force
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
# Basic validation (run from vault directory)
cd /path/to/vault
tagex config validate

# Or specify path explicitly
tagex config validate /path/to/vault

# Strict mode (treats warnings as errors)
tagex config validate --strict
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

   # Validate changes (from vault directory)
   tagex config validate
   ```

5. **Use init --force to reset:**
   ```bash
   # If configuration becomes corrupted (from vault directory)
   tagex init --force
   ```


## Related Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Installation and vault setup
- [ANALYTICS.md](ANALYTICS.md) - Analysis tools and workflows
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
