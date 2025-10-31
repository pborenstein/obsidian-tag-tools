# Tagex Command Structure Analysis

## Current State Diagram

```
tagex
├── init [vault_path]                          # TOP LEVEL - Configuration
├── validate [vault_path]                      # TOP LEVEL - Configuration
├── stats [vault_path]                         # TOP LEVEL - Information
├── health [vault_path]                        # TOP LEVEL - Information
│
├── tags/                                      # GROUPED - Operations
│   ├── extract [vault_path]
│   ├── rename <vault> <old> <new>
│   ├── merge <vault> <tags...> --into <target>
│   ├── delete <vault> <tags...>
│   ├── fix-duplicates [vault_path]
│   └── apply <operations.yaml>
│
├── analyze/                                   # GROUPED - Analysis
│   ├── pairs [input_path]
│   ├── quality [input_path]
│   ├── synonyms [input_path]
│   ├── plurals [input_path]
│   ├── merge [input_path]
│   ├── suggest [paths...] --vault-path <vault>
│   └── recommendations [input_path]
│
└── vault/                                     # GROUPED - Maintenance
    └── cleanup-backups <vault_path>
```

## Current Problems

### 1. **Inconsistent Grouping**
- `init` and `validate` are top-level but should be grouped (configuration commands)
- `stats` and `health` are top-level but should be grouped (information/reporting commands)
- Only 3 command groups exist, but 2 logical groups are missing

### 2. **Argument Inconsistencies**
- Some commands use `[vault_path]` (optional, defaults to cwd)
- Others require `<vault_path>` (mandatory)
- `analyze suggest` has weird structure: `paths` are positional but `--vault-path` is required option
- `tags apply` has `operations_file` as positional but `--vault-path` as option

### 3. **Unclear Boundaries**
- `tags extract` extracts data but doesn't modify anything
- `analyze recommendations` generates operations file (isn't this "generating" not "analyzing"?)
- `tags apply` applies operations from file (more like "ops apply" or "execute")

### 4. **Command Discovery Issues**
- Users won't find `stats` or `health` easily (they're hidden at top level)
- No clear workflow guidance from command structure itself
- Hard to remember which commands are grouped and which aren't

### 5. **Workflow Confusion**
```
Current workflow (unclear):
tagex init /vault                              # Setup
tagex analyze recommendations /vault           # Generate ops
tagex tags apply ops.yaml --vault-path /vault  # Apply ops

Why does "analyze" create an actionable file?
Why is vault_path positional in one but option in the other?
```

---

## Proposed Restructure: Option A (Semantic Grouping)

```
tagex
├── config/                                    # Configuration & Setup
│   ├── init [vault_path]
│   ├── validate [vault_path]
│   └── show [vault_path]                      # NEW: show current config
│
├── info/                                      # Information & Reporting
│   ├── stats [vault_path]
│   ├── health [vault_path]
│   ├── tags [vault_path]                      # NEW: alias for stats
│   └── extract [vault_path]                   # MOVED: from tags.extract
│
├── analyze/                                   # Analysis Only (no writes)
│   ├── pairs [vault_path]
│   ├── quality [vault_path]
│   ├── synonyms [vault_path]
│   ├── plurals [vault_path]
│   ├── merges [vault_path]                    # RENAMED: from merge
│   ├── suggest [vault_path] [paths...]        # FIXED: vault first
│   └── all [vault_path]                       # RENAMED: from recommendations
│
├── ops/                                       # Operations (writes files)
│   ├── rename <vault> <old> <new>
│   ├── merge <vault> <tags...> --into <target>
│   ├── delete <vault> <tags...>
│   ├── add <vault> <file> <tags...>           # NEW: explicit add operation
│   ├── fix-duplicates [vault_path]
│   └── apply [vault_path] <operations.yaml>   # FIXED: vault can be in file
│
└── vault/                                     # Vault Maintenance
    ├── cleanup-backups <vault_path>
    ├── backup <vault_path>                    # NEW: create backup
    └── verify <vault_path>                    # NEW: verify integrity
```

### Benefits of Option A
1. **Clear Semantic Boundaries**
   - `config` = configure the tool
   - `info` = read-only information
   - `analyze` = read-only analysis
   - `ops` = write operations on tags
   - `vault` = file system operations

2. **Consistent Argument Pattern**
   - All commands: `[vault_path]` defaults to cwd
   - Special data comes after vault
   - Options are truly optional

3. **Better Discovery**
   - `tagex info` shows all read-only commands
   - `tagex ops` shows all write commands
   - `tagex analyze` is purely analytical

4. **Clear Workflow**
```bash
tagex config init            # 1. Setup
tagex info stats             # 2. Understand current state
tagex analyze all --export   # 3. Generate recommendations
tagex ops apply ops.yaml     # 4. Execute changes
```

---

## Proposed Restructure: Option B (Workflow-Oriented)

```
tagex
├── setup/                                     # Initial setup
│   ├── init [vault_path]
│   ├── validate [vault_path]
│   └── config [vault_path]
│
├── inspect/                                   # Read & understand
│   ├── stats [vault_path]
│   ├── health [vault_path]
│   ├── export [vault_path]                    # RENAMED: from tags.extract
│   ├── pairs [vault_path]
│   ├── quality [vault_path]
│   └── coverage [vault_path]                  # NEW: tag coverage analysis
│
├── recommend/                                 # Generate suggestions
│   ├── synonyms [vault_path]
│   ├── plurals [vault_path]
│   ├── merges [vault_path]
│   ├── content [vault_path] [paths...]        # RENAMED: from suggest
│   └── all [vault_path]                       # Full recommendations
│
├── modify/                                    # Execute changes
│   ├── rename <vault> <old> <new>
│   ├── merge <vault> <sources...> --into <target>
│   ├── delete <vault> <tags...>
│   ├── add <vault> <file> <tags...>
│   ├── fix [vault_path]                       # RENAMED: fix-duplicates
│   └── execute [vault_path] <ops.yaml>        # RENAMED: from apply
│
└── maintain/                                  # Vault maintenance
    ├── cleanup [vault_path]
    ├── backup [vault_path]
    └── verify [vault_path]
```

### Benefits of Option B
1. **Workflow-Driven Names**
   - setup → inspect → recommend → modify → maintain
   - Natural progression through tool usage
   - Command names match user mental model

2. **Verb-Based Groups**
   - Each group answers "what am I doing?"
   - More intuitive for new users

3. **Better Help Text**
```bash
$ tagex --help
Commands:
  setup      Initialize and configure tagex for your vault
  inspect    View information about your tags (read-only)
  recommend  Analyze and suggest improvements
  modify     Apply tag operations (writes files)
  maintain   Vault maintenance and cleanup
```

---

## Proposed Restructure: Option C (Flat with Prefixes)

```
tagex
├── config-init [vault_path]
├── config-validate [vault_path]
├── config-show [vault_path]
│
├── info-stats [vault_path]
├── info-health [vault_path]
├── info-export [vault_path]
│
├── analyze-pairs [vault_path]
├── analyze-quality [vault_path]
├── analyze-synonyms [vault_path]
├── analyze-plurals [vault_path]
├── analyze-merges [vault_path]
├── analyze-suggest [vault_path] [paths...]
├── analyze-all [vault_path]
│
├── tag-rename <vault> <old> <new>
├── tag-merge <vault> <sources...> --into <target>
├── tag-delete <vault> <tags...>
├── tag-add <vault> <file> <tags...>
├── tag-fix-duplicates [vault_path]
├── tag-apply [vault_path] <ops.yaml>
│
└── vault-cleanup [vault_path]
└── vault-backup [vault_path]
└── vault-verify [vault_path]
```

### Benefits of Option C
1. **Flat = Discoverable**
   - `tagex <tab>` shows all commands
   - No need to know grouping structure
   - Better for CLI autocomplete

2. **Prefix = Organized**
   - Prefixes provide logical grouping
   - Easy to filter: `tagex analyze-<tab>`

3. **No Argument Position Confusion**
   - Everything starts the same way
   - Consistent with git style: `git commit`, `git add`

---

## Recommendation: Hybrid Approach (Option D) ⭐

Best of all worlds:

```
tagex
├── init [vault_path]                          # Keep simple common commands at top
├── stats [vault_path]                         # Most-used commands stay short
├── health [vault_path]
│
├── config/                                    # Advanced config
│   ├── validate [vault_path]
│   ├── show [vault_path]
│   └── edit [vault_path]                      # NEW: open in $EDITOR
│
├── analyze/                                   # All analysis together
│   ├── pairs [vault_path]
│   ├── quality [vault_path]
│   ├── synonyms [vault_path]
│   ├── plurals [vault_path]
│   ├── merges [vault_path]
│   ├── suggest [vault_path] [paths...]
│   └── recommendations [vault_path] --export  # Keep familiar name
│
├── tag/                                       # RENAMED: tags → tag (singular)
│   ├── export [vault_path]                    # RENAMED: extract → export
│   ├── rename <vault> <old> <new>
│   ├── merge <vault> <sources...> --into <target>
│   ├── delete <vault> <tags...>
│   ├── add <vault> <file> <tags...>           # NEW
│   ├── fix [vault_path]                       # RENAMED: fix-duplicates → fix
│   └── apply [vault_path] <ops.yaml>
│
└── vault/                                     # Vault operations
    ├── cleanup [vault_path]                   # RENAMED: cleanup-backups → cleanup
    ├── backup [vault_path]                    # NEW
    └── verify [vault_path]                    # NEW
```

### Why This Works

1. **Frequently-used commands stay short**
   - `tagex init`
   - `tagex stats`
   - `tagex health`
   - These are the "porcelain" commands users run daily

2. **Grouped commands are more specific**
   - `tagex analyze recommendations` for deep analysis
   - `tagex tag rename` for tag operations
   - `tagex config validate` for config management

3. **Consistent argument patterns**
   - All commands default vault to cwd
   - Data arguments come after vault
   - Options are truly optional

4. **Backwards compatible transition**
   - Create aliases: `tags` → `tag`
   - Keep old commands with deprecation warnings
   - Gradual migration path

5. **Better tab completion**
```bash
tagex <tab>         → shows: init, stats, health, config, analyze, tag, vault
tagex analyze <tab> → shows: pairs, quality, synonyms, plurals, ...
tagex tag <tab>     → shows: export, rename, merge, delete, add, fix, apply
```

---

## Implementation Plan

### Phase 1: Add Aliases (Non-Breaking)
```python
# Keep existing structure, add aliases
@main.command('stats')
@main.command('info-stats')  # Alias
def stats(...): pass

# Test with both:
tagex stats
tagex info-stats
```

### Phase 2: Deprecation Warnings
```python
# Warn users about upcoming changes
@tags.command()
def extract(...):
    click.echo("Warning: 'tagex tags extract' will be renamed to 'tagex tag export' in v1.0")
    # ... existing code
```

### Phase 3: New Structure (Breaking)
```python
# Implement new structure with migration guide
# Provide `tagex migrate-config` command to update shell aliases
```

### Phase 4: Remove Old Commands
```python
# Remove deprecated commands in v2.0
# Clean up codebase
```

---

## Quick Wins (Immediate Improvements)

Even without restructuring, these changes would help:

1. **Make vault_path consistent**
   - All commands default to cwd
   - Update docs to show this clearly

2. **Rename confusing commands**
   - `tags extract` → `tag export` (it exports, doesn't modify)
   - `analyze merge` → `analyze merges` (it finds merge opportunities)
   - `tags fix-duplicates` → `tag fix` (shorter, clearer)
   - `vault cleanup-backups` → `vault cleanup` (shorter)

3. **Add missing commands**
   - `tag add` - explicit tag addition
   - `config show` - show current config
   - `vault backup` - create backups before operations

4. **Improve help text**
```python
@main.group()
def analyze():
    """Analyze tag relationships and suggest improvements.

    All analyze commands are READ-ONLY and safe to run.
    They help you understand your tag structure before making changes.

    Common workflow:
      1. tagex analyze recommendations --export ops.yaml
      2. edit ops.yaml
      3. tagex tag apply ops.yaml
    """
    pass
```

5. **Add workflow command**
```bash
tagex workflow   # Interactive wizard that guides through the process
```

---

## Summary

**Current State**: Inconsistent grouping, unclear boundaries, confusing workflows

**Recommended**: Hybrid approach (Option D)
- Keep common commands short: `init`, `stats`, `health`
- Group specific operations: `config/`, `analyze/`, `tag/`, `vault/`
- Consistent argument patterns
- Clear separation of read vs. write operations

**Migration**: Phased approach with aliases and deprecation warnings

**Quick Wins**: Rename confusing commands, add missing ones, improve help text
