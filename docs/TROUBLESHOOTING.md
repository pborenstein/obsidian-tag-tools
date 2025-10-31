# Troubleshooting

Solutions to common issues when using tagex.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Extraction Issues](#extraction-issues)
- [Tag Operation Issues](#tag-operation-issues)
- [Analysis Issues](#analysis-issues)
- [Performance Issues](#performance-issues)

## Installation Issues

### "uv: command not found"

**Symptoms:**

- Running `uv sync` or `uv tool install` returns "command not found"
- Cannot install tagex

**Solutions:**

1. Install uv package manager:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Or install with pip:

   ```bash
   pip install --upgrade uv
   ```

3. Verify installation:

   ```bash
   uv --version
   ```

**Related Issues:**

- [Python version mismatch](#python-version-mismatch)

### Python Version Mismatch

**Symptoms:**

- `requires-python = ">=3.10"` error
- Package installation failures
- Import errors

**Solutions:**

1. Check your Python version:

   ```bash
   python3 --version
   ```

2. Install Python 3.10 or higher:

   ```bash
   # macOS with Homebrew
   brew install python@3.11

   # Or download from python.org
   ```

3. Update with pyenv if using:

   ```bash
   pyenv install 3.11.0
   pyenv local 3.11.0
   ```

**Related Issues:**

- [Virtual environment issues](#virtual-environment-issues)

### Virtual Environment Issues

**Symptoms:**

- Import errors despite installation
- `ModuleNotFoundError` for tagex modules
- Wrong Python version in environment

**Solutions:**

1. Ensure virtual environment is activated:

   ```bash
   # Check if activated (prompt should show (.venv))
   which python
   ```

2. If using uv (recommended):

   ```bash
   uv sync
   ```

3. Or create and activate manually:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # bash/zsh
   # or
   source .venv/bin/activate.fish  # fish
   pip install -e .
   ```

**Related Issues:**

- [Missing dependencies](#missing-dependencies)

### Missing Dependencies

**Symptoms:**

- `ModuleNotFoundError: No module named 'click'`
- `ModuleNotFoundError: No module named 'yaml'`
- Import errors for scikit-learn

**Solutions:**

1. Install all dependencies:

   ```bash
   uv sync
   # Or
   pip install -e .
   ```

2. For analysis features, ensure scikit-learn is installed:

   ```bash
   pip install scikit-learn
   ```

3. Verify installation:

   ```bash
   python3 -c "import tagex; print('OK')"
   tagex --help
   ```

**Related Issues:**

- [Virtual environment not activated](#virtual-environment-issues)

### "tagex: command not found"

**Symptoms:**

- Running `tagex` returns "command not found"
- Installation succeeded but command unavailable

**Solutions:**

1. If using `uv tool install`:

   ```bash
   uv tool install --editable .
   ```

2. Check if uv tools are in PATH:

   ```bash
   echo $PATH | grep -i uv
   ```

3. Add uv bin directory to PATH if needed:

   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"
   ```

4. Alternative: use via Python module:

   ```bash
   uv run python -m tagex.main --help
   ```

## Extraction Issues

### No Tags Found in Vault

**Symptoms:**

- `tagex tag export /vault` returns empty results
- Total tags: 0 despite vault having tags
- "No tags found" message

**Solutions:**

1. Check tag type filtering (default is frontmatter only):

   ```bash
   # Extract both frontmatter and inline tags
   tagex tag export /vault --tag-types both

   # Extract only inline tags
   tagex tag export /vault --tag-types inline
   ```

2. Verify vault path is correct:

   ```bash
   ls /path/to/vault/*.md
   ```

3. Check if files have frontmatter:

   ```bash
   head -n 10 /path/to/vault/some-file.md
   ```

4. Use `--verbose` to see what's being processed:

   ```bash
   tagex tag export /vault --verbose
   ```

**Related Issues:**

- [Tags filtered out as noise](#tags-filtered-out-as-noise)
- [File exclusion patterns](#files-being-excluded)

### Tags Filtered Out as Noise

**Symptoms:**

- Expected tags missing from output
- Pure numbers or dates not appearing
- Technical strings being filtered

**Solutions:**

1. Disable filtering to see raw tags:

   ```bash
   tagex tag export /vault --no-filter
   ```

2. Review tag validation rules in output:

   - Numbers like `2024` are filtered by default
   - HTML entities like `&nbsp;` are filtered
   - Single-character tags may be filtered
   - Technical patterns are excluded

3. If legitimate tags are being filtered, report as issue

**Related Issues:**

- [No tags found](#no-tags-found-in-vault)

### Files Being Excluded

**Symptoms:**

- Some markdown files not processed
- Subdirectory files missing
- Template files being processed when they shouldn't

**Solutions:**

1. Check exclusion patterns:

   ```bash
   # Exclude templates directory
   tagex tag export /vault --exclude "templates/*"

   # Multiple exclusions
   tagex tag export /vault --exclude "templates/*" --exclude "archive/*"
   ```

2. Verify file discovery with verbose mode:

   ```bash
   tagex tag export /vault --verbose
   ```

3. Check for permission issues:

   ```bash
   ls -la /vault/subdirectory
   ```

### Malformed YAML Errors

**Symptoms:**

- `YAML parsing error in file: example.md`
- Files being skipped during extraction
- Frontmatter validation errors

**Solutions:**

1. Check the file's frontmatter syntax:

   ```yaml
   ---
   tags: [work, notes]  # Array format
   # OR
   tags:
     - work
     - notes
   # OR
   tag: work  # Single tag
   ---
   ```

2. Common YAML errors:

   - Missing closing `---`
   - Incorrect indentation
   - Special characters without quotes
   - Tabs instead of spaces

3. Fix the problematic file or exclude it:

   ```bash
   tagex tag export /vault --exclude "broken-file.md"
   ```

**Related Issues:**

- [Files being excluded](#files-being-excluded)

## Tag Operation Issues

### Preview Shows Changes But Operation Fails

**Symptoms:**

- Preview mode shows expected changes
- Running with --execute fails or makes no changes
- "No files modified" despite preview showing changes

**Solutions:**

1. Check file permissions:

   ```bash
   ls -la /vault/*.md
   chmod 644 /vault/*.md  # If needed
   ```

2. Ensure files haven't changed since preview:

   ```bash
   # Run preview and actual operation immediately after
   tagex tag rename /vault old-tag new-tag
   tagex tag rename /vault old-tag new-tag --execute
   ```

3. Check for file locks (Obsidian open):

   - Close Obsidian before running operations
   - Or sync after operation completes

**Related Issues:**

- [Files not being modified](#files-not-being-modified)

### Files Not Being Modified

**Symptoms:**

- Operation completes but files unchanged
- Stats show "0 files modified"
- Tags still present after delete operation

**Solutions:**

1. Verify tag type matches operation:

   ```bash
   # If tags are inline but operation targets frontmatter (default)
   tagex tag delete /vault old-tag --tag-types inline

   # Process both types
   tagex tag rename /vault old-tag new-tag --tag-types both
   ```

2. Check exact tag name (case-sensitive):

   ```bash
   # Extract tags first to verify names
   tagex tag export /vault -o tags.json
   cat tags.json | grep -i "partial-name"
   ```

3. Verify tag exists in vault:

   ```bash
   # Search for tag in files
   grep -r "old-tag" /vault/
   ```

**Related Issues:**

- [Tag type mismatch](#no-tags-found-in-vault)

### Inline Tag Deletion Warnings

**Symptoms:**

- Warning about inline tag deletion
- Operation requires confirmation
- Concerned about content modification

**Solutions:**

1. This is expected behavior - inline tags are part of content:

   ```bash
   # Preview changes carefully first
   tagex tag delete /vault inline-tag --tag-types inline
   ```

2. Consider renaming instead of deleting:

   ```bash
   # Safer - preserves tag structure
   tagex tag rename /vault old-tag new-tag --tag-types inline
   ```

3. Check log files after operation:

   ```bash
   # Review what was modified
   cat logs/tag-delete-op_*.json
   ```

**Related Issues:**

- [Operation verification](#verifying-operation-results)

### Verifying Operation Results

**Symptoms:**

- Want to confirm operation worked correctly
- Need to audit changes
- Checking for unintended modifications

**Solutions:**

1. Check operation logs:

   ```bash
   # View most recent operation
   ls -lt logs/*.json | head -1
   cat logs/tag-rename-op_TIMESTAMP.json
   ```

2. Re-extract tags and compare:

   ```bash
   tagex tag export /vault -o after.json
   # Compare with before.json
   ```

3. Use git to review changes:

   ```bash
   git diff
   git status
   ```

4. Verify specific files:

   ```bash
   grep -l "new-tag" /vault/*.md
   ```

## Analysis Issues

### "No module named 'sklearn'"

**Symptoms:**

- `tagex analyze merges` fails
- ImportError for scikit-learn
- Analysis command crashes

**Solutions:**

1. Install scikit-learn:

   ```bash
   pip install scikit-learn
   ```

2. Or use pattern-based fallback:

   ```bash
   tagex analyze merges tags.json --no-sklearn
   ```

3. Verify installation:

   ```bash
   python3 -c "import sklearn; print(sklearn.__version__)"
   ```

**Related Issues:**

- [Missing dependencies](#missing-dependencies)

### No Merge Suggestions Found

**Symptoms:**

- `tagex analyze merges` returns empty results
- "No similar tags found"
- Expected related tags not suggested

**Solutions:**

1. Lower minimum usage threshold:

   ```bash
   # Default is 3, try lower
   tagex analyze merges tags.json --min-usage 2
   ```

2. Check if vault has enough tags:

   ```bash
   # Need multiple tags for similarity detection
   tagex stats /vault
   ```

3. Verify tag data file has tags:

   ```bash
   jq 'length' tags.json
   jq '.[0:5]' tags.json  # Show first 5 tags
   ```

**Related Issues:**

- [No tags found](#no-tags-found-in-vault)

### Pair Analysis Shows No Relationships

**Symptoms:**

- `tagex analyze pairs` returns empty
- No tag co-occurrences detected
- "No pairs found" message

**Solutions:**

1. Lower minimum pair threshold:

   ```bash
   tagex analyze pairs tags.json --min-pairs 2
   ```

2. Check if using filtered tags:

   ```bash
   # Include all tags for analysis
   tagex tag export /vault --no-filter -o raw_tags.json
   tagex analyze pairs raw_tags.json
   ```

3. Verify files have multiple tags:

   ```bash
   # Files need multiple tags to create pairs
   grep -A5 "^tags:" /vault/*.md | head -20
   ```

## Performance Issues

### Slow Extraction on Large Vaults

**Symptoms:**

- Extract command takes minutes
- Processing thousands of files
- High CPU usage

**Solutions:**

1. Use exclusion patterns for unnecessary directories:

   ```bash
   tagex tag export /vault --exclude "archive/*" --exclude ".obsidian/*"
   ```

2. Process specific subdirectory:

   ```bash
   tagex tag export /vault/active-notes
   ```

3. Expected performance:

   - ~1000 files/second for tag extraction
   - Slower for complex YAML or many inline tags
   - First run slower than subsequent runs (OS caching)

### High Memory Usage During Analysis

**Symptoms:**

- Memory usage spikes during `analyze merge`
- System becomes unresponsive
- Out of memory errors

**Solutions:**

1. Use pattern-based fallback (lower memory):

   ```bash
   tagex analyze merges tags.json --no-sklearn
   ```

2. Filter tags before analysis:

   ```bash
   # Reduce tag set size
   tagex tag export /vault --min-usage 3 -o filtered.json
   tagex analyze merges filtered.json
   ```

3. Process on machine with more RAM

## Getting Help

If you encounter issues not covered here:

1. Check [docs/README.md](README.md) for documentation index
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. Check operation logs in `logs/` directory
4. Run with `--verbose` flag for detailed output
5. Report issues at project repository

## Common Workflows

### Verifying Installation

```bash
# Complete installation check
git clone https://github.com/pborenstein/obsidian-tag-tools.git
cd obsidian-tag-tools
uv tool install --editable .
tagex --help
tagex stats /path/to/test/vault
```

### Safe Tag Renaming

```bash
# Always preview first (default behavior)
tagex tag rename /vault old-tag new-tag
# Review output, then execute
tagex tag rename /vault old-tag new-tag --execute
# Verify changes
cat logs/tag-rename-op_*.json | tail -1
```

### Comprehensive Tag Analysis

```bash
# Extract all tags
tagex tag export /vault --tag-types both -o all_tags.json

# Get statistics
tagex stats /vault --tag-types both

# Analyze relationships
tagex analyze pairs all_tags.json
tagex analyze merges all_tags.json
```
