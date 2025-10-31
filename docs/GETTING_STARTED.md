# Getting Started with tagex

This guide walks you through the most common workflow for cleaning up your Obsidian vault's tags. Follow these steps in order for the best results.

## The Happy Path

```
Installation → Initialize → Explore → Fix → Analyze → Review → Preview → Apply → Verify → Clean Up
     ↓             ↓          ↓         ↓        ↓         ↓         ↓        ↓        ↓        ↓
  uv tool      tagex init  tagex    tagex    tagex     edit     tagex    tagex    tagex    tagex
  install                  stats    tag fix  analyze   ops.     tag      tag      stats    vault
                          health            recommend  yaml     apply    apply            cleanup
                                                                         --execute
```

**Time required:** 15 minutes (most of it reviewing recommendations)

**Result:** A cleaner, more consistent tag system across your entire vault

### Step 1: Install tagex

```bash
# Clone the repository
git clone https://github.com/pborenstein/obsidian-tag-tools.git
cd obsidian-tag-tools

# Install as a system-wide command
uv tool install --editable .

# Verify it works
tagex --help
```

**What this does:** Makes the `tagex` command available everywhere on your system.

### Step 2: Initialize Your Vault

```bash
# Navigate to your vault
cd "$HOME/Obsidian/MyVault"

# Initialize tagex configuration
tagex init
```

**What this does:** Creates a `.tagex/` directory with configuration files:

- `config.yaml` - General settings (plural preferences, thresholds)
- `synonyms.yaml` - Custom tag synonyms
- `exclusions.yaml` - Tags to exclude from analysis

**Pro tip:** Add `.tagex/` to your `.gitignore` if you track your vault with git.

### Step 3: Understand Your Current State

```bash
# Get a quick overview
tagex stats

# See health metrics
tagex health
```

**What this does:** Shows you:

- Total tags and files
- Most common tags
- Singleton tags (used only once)
- Tag quality issues
- Duplicate frontmatter fields

**What to look for:**

- High percentage of singleton tags → opportunities for consolidation
- Duplicate 'tags:' fields → needs fixing
- Many similar tags (python/Python/PYTHON) → needs normalization

### Step 4: Fix Obvious Problems

If `health` showed duplicate 'tags:' fields, fix them first:

```bash
# Preview what will be fixed
tagex tag fix

# Apply the fixes
tagex tag fix --execute
```

**What this does:** Consolidates duplicate `tags:` fields in your frontmatter.

### Step 5: Generate Recommendations

This is where the magic happens:

```bash
# Generate a comprehensive list of suggested improvements
tagex analyze recommendations --export operations.yaml
```

**What this does:** Analyzes your tags and creates an editable file with suggestions for:

- **Plurals** - Merge "note/notes", "book/books", etc.
- **Synonyms** - Merge semantically similar tags using AI
- **Singletons** - Consolidate rarely-used tags into established ones

**Output:** Creates `operations.yaml` with all suggestions.

### Step 6: Review and Edit Recommendations

```bash
# Open the operations file in your editor
open operations.yaml
# or
vim operations.yaml
```

**What to do:**

1. Review each suggested operation
2. Enable operations you want: `enabled: true`
3. Disable operations you don't want: `enabled: false`
4. Delete entire operations you disagree with
5. Modify source/target tags if needed

**Example operation:**

```yaml
- operation: merge
  source_tags:
    - python
    - Python
    - py
  target_tag: python
  enabled: true  # ← Set to false to skip this operation
  reason: "Plural/case variants detected"
  confidence: 0.95
```

### Step 7: Preview Changes

```bash
# See what will happen (safe - no changes made)
tagex tag apply operations.yaml
```

**What this does:** Shows you exactly what files will be modified and how.

**Look for:**

- Number of files affected
- Which tags will change
- Preview of modifications

**Red flags:**

- Unexpected files being modified
- Too many changes at once
- Tags merging that shouldn't

If something looks wrong, go back to Step 6 and adjust.

### Step 8: Apply Changes

When you're confident everything looks good:

```bash
# Apply the changes (requires explicit --execute flag)
tagex tag apply operations.yaml --execute
```

**What this does:** Modifies your vault files according to the operations you enabled.

**Safety features:**

- Creates `.bak` backup files
- Logs all changes to `.tagex/logs/`
- Only processes enabled operations
- Preserves file formatting

### Step 9: Verify Improvements

```bash
# Check the results
tagex stats
tagex health
```

**What to look for:**

- Reduced number of singleton tags
- Lower total tag count (consolidation worked)
- Improved tag quality scores
- No new health issues

### Step 10: Clean Up (Optional)

```bash
# Remove backup files if everything looks good
tagex vault cleanup

# Actually remove them
tagex vault cleanup --execute
```

**What this does:** Removes the `.bak` backup files created during modifications.

**Warning:** Only do this after you've verified everything is correct!

## Common Workflows

### Quick Tag Fixes

If you just need to fix a specific tag:

```bash
# Rename a tag
tagex tag rename work project --execute

# Merge several tags into one
tagex tag merge personal diary journal --into writing --execute

# Delete unwanted tags
tagex tag delete obsolete-tag --execute
```

### Analyzing Without Changes

Explore your tag relationships without modifying anything:

```bash
# See which tags appear together
tagex analyze pairs

# Find semantic similarities
tagex analyze synonyms

# Check tag quality issues
tagex analyze quality
```

### Suggest Tags for Notes

Help tag your untagged or lightly-tagged notes:

```bash
# Suggest tags based on content
tagex analyze suggest --min-tags 2 --export suggestions.yaml

# Review suggestions
cat suggestions.yaml

# Apply selected suggestions
tagex tag apply suggestions.yaml --execute
```

## What to Do When Things Go Wrong

### "I applied changes and something broke"

Your backup files are in the same directory as your notes with a `.bak` extension:

```bash
# Find your backups
find . -name "*.bak"

# Restore a specific file
mv "My Note.md.bak" "My Note.md"
```

### "I want to undo all changes"

Check the operation logs:

```bash
ls -la .tagex/logs/
cat .tagex/logs/operations-YYYY-MM-DD-HHMMSS.log
```

The logs show exactly what was changed in each file.

### "The recommendations are wrong"

Edit your configuration:

```bash
# Edit main config
tagex config edit

# Add known synonyms
tagex config edit synonyms

# Exclude tags from analysis
tagex config edit exclusions
```

Then re-run `tagex analyze recommendations`.

## Next Steps

- Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for a complete command list
- Explore [ANALYTICS.md](ANALYTICS.md) for advanced analysis workflows
- Check [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) to customize behavior
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

## Tips for Success

**Start small:** Your first time, only enable a few operations in `operations.yaml` to build confidence.

**Review carefully:** Always preview with `tagex tag apply` before using `--execute`.

**Use version control:** If your vault is in git, commit before making bulk changes.

**Check your backups:** The `.bak` files are your safety net. Don't delete them until you're sure.

**Iterate:** Clean up your tags in multiple passes. It's easier to review 10 changes than 100.

**Trust the confidence scores:** High confidence (>0.9) operations are usually safe. Lower scores need more scrutiny.

---

## Quick Reference Card

Copy this to keep handy during your first run:

```bash
# The Happy Path - Complete Workflow
cd "$HOME/Obsidian/MyVault"              # Navigate to vault
tagex init                                # One-time setup
tagex stats                               # See what you have
tagex health                              # Check for issues
tagex tag fix --execute                   # Fix duplicates (if any)
tagex analyze recommendations --export operations.yaml
                                          # Generate recommendations
# Edit operations.yaml (enable/disable operations)
tagex tag apply operations.yaml           # Preview changes
tagex tag apply operations.yaml --execute # Apply changes
tagex stats                               # Verify improvements
tagex vault cleanup --execute             # Remove backups (optional)

# Quick Fixes
tagex tag rename old new --execute        # Rename a tag
tagex tag merge tag1 tag2 --into new --execute
                                          # Merge tags
tagex tag delete unwanted --execute       # Delete a tag

# Safety: ALL commands preview by default
# Add --execute only when ready to modify files
```
