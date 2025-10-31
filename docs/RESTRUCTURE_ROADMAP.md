# Tagex Command Restructure: Implementation Roadmap

## Executive Summary

**Current Problem**: Inconsistent command grouping, unclear boundaries between read/write operations, confusing argument patterns.

**Recommended Solution**: Hybrid approach that keeps frequently-used commands short while grouping advanced operations logically.

**Migration Strategy**: Phased implementation with backwards compatibility.

---

## Recommended Structure (Quick Reference)

```
tagex
├── init, stats, health           ← Porcelain (quick access)
├── config/  (validate, show, edit)
├── analyze/ (pairs, quality, synonyms, plurals, merges, suggest, recommendations)
├── tag/     (export, rename, merge, delete, add, fix, apply)
└── vault/   (cleanup, backup, verify)
```

---

## Implementation Phases

### Phase 0: Documentation & Planning (Week 1)
**Status**: Ready to start

- [x] Document current structure
- [x] Analyze problems
- [x] Design new structure
- [ ] Create migration guide for users
- [ ] Update CHANGELOG with deprecation notices
- [ ] Create GitHub issue for tracking

**Deliverables**:
- Migration guide (docs/MIGRATION.md)
- Updated architecture docs
- User announcement draft

---

### Phase 1: Add Aliases (Week 2-3)
**Status**: Non-breaking, backwards compatible

**Changes**:
```python
# 1. Rename group: tags → tag
@main.group()
def tag():  # NEW
    """Tag operations (renamed from 'tags')"""
    pass

# Keep old name with deprecation warning
@main.group()
def tags():  # DEPRECATED
    click.echo("Warning: 'tags' is deprecated, use 'tag' instead", err=True)
    pass

# 2. Add command aliases
@tag.command('export')
@tag.command('extract')  # OLD NAME (alias)
def export_tags(...):
    """Export tags from vault (formerly 'extract')"""
    pass

@tag.command('fix')
@tag.command('fix-duplicates')  # OLD NAME (alias)
def fix_duplicates(...):
    """Fix duplicate tags fields"""
    pass

# 3. Add new commands
@tag.command('add')
def add_tags(...):
    """Add tags to a file"""
    pass

@config.group()
def config():
    """Configuration management"""
    pass

@config.command('show')
def show_config(...):
    """Display current configuration"""
    pass

@config.command('edit')
def edit_config(...):
    """Edit configuration in $EDITOR"""
    pass

@vault.command('backup')
def backup_vault(...):
    """Create backup of vault"""
    pass

@vault.command('verify')
def verify_vault(...):
    """Verify vault integrity"""
    pass
```

**Testing**:
```bash
# Old commands still work
tagex tags extract
tagex tags fix-duplicates

# New commands also work
tagex tag export
tagex tag fix

# Both produce same result
diff <(tagex tags extract) <(tagex tag export)
```

**Deliverables**:
- Working aliases
- Deprecation warnings in stderr
- Updated tests for both old and new names

---

### Phase 2: Update Arguments (Week 4)
**Status**: Potentially breaking, needs careful migration

**Changes**:

1. **Consistent vault_path handling**
```python
# BEFORE: Inconsistent
tagex tags rename <vault> <old> <new>
tagex tags apply <ops.yaml> --vault-path <vault>
tagex analyze suggest <paths...> --vault-path <vault>

# AFTER: Consistent
tagex tag rename [vault] <old> <new>        # vault defaults to cwd
tagex tag apply [vault] <ops.yaml>          # vault defaults to cwd
tagex analyze suggest [vault] [paths...]    # vault first, then paths
```

2. **Implementation strategy**:
```python
@tag.command('apply')
@click.argument('operations_file', type=click.Path(exists=True))
@click.argument('vault_path', type=click.Path(exists=True),
                default='.', required=False)
# DEPRECATED: keep for backwards compat
@click.option('--vault-path', type=click.Path(exists=True),
              help='DEPRECATED: Use positional argument instead')
def apply(operations_file, vault_path, **kwargs):
    # Handle both old and new style
    if kwargs.get('vault_path'):
        click.echo("Warning: --vault-path is deprecated, use positional argument", err=True)
        vault_path = kwargs['vault_path']

    # ... rest of implementation
```

**Migration Guide**:
```markdown
# Before (v0.x)
tagex tags apply operations.yaml --vault-path /vault

# After (v1.0)
tagex tag apply /vault operations.yaml
# OR (if in vault directory)
tagex tag apply operations.yaml

# Transition: Both work with deprecation warning
```

**Testing**:
```bash
# Test backward compatibility
tagex tag apply ops.yaml --vault-path /vault  # warns but works
tagex tag apply /vault ops.yaml               # new way, no warning
tagex tag apply ops.yaml                      # defaults to cwd
```

**Deliverables**:
- Backwards-compatible argument parsing
- Clear deprecation warnings
- Updated documentation

---

### Phase 3: Standardize Output (Week 5)
**Status**: Non-breaking, enhances consistency

**Changes**:

1. **Consistent vault path display**
```python
# All commands show vault path clearly
print(f"Vault: {vault_path}")
print(f"Tag types: {tag_types}")
print(f"Command: {command_name}")
print("=" * 70)
```

2. **Consistent progress indicators**
```python
# Use same format across all commands
print(f"[1/10] Analyzing synonyms...")
print(f"[2/10] Detecting plurals...")
```

3. **Consistent error messages**
```python
# Standardize error format
def print_error(msg: str, details: Optional[str] = None):
    click.echo(f"Error: {msg}", err=True)
    if details:
        click.echo(f"  {details}", err=True)
    click.echo("\nFor help, run: tagex --help", err=True)
```

**Deliverables**:
- Consistent output formatter
- Updated all commands to use it
- Better error messages

---

### Phase 4: Documentation Update (Week 6)
**Status**: Critical for user adoption

**Updates needed**:

1. **README.md**
```markdown
# Quick Start
tagex init              # Setup
tagex health            # Check vault
tagex analyze recommendations --export ops.yaml
tagex tag apply ops.yaml --execute

# Common Commands
tagex stats             # Tag statistics
tagex health            # Vault health report
tagex config validate   # Check configuration
tagex tag export        # Export tags to JSON

# Analysis
tagex analyze synonyms  # Find semantic duplicates
tagex analyze plurals   # Find singular/plural variants
tagex analyze recommendations  # All-in-one analysis
```

2. **CLAUDE.md**
- Update all command examples
- Add migration notes
- Update workflow examples

3. **docs/COMMANDS.md** (NEW)
```markdown
# Command Reference

## Quick Access Commands
These commands are available at the top level for convenience.

### tagex init [vault_path]
Initialize tagex configuration...

### tagex stats [vault_path]
Display tag statistics...

### tagex health [vault_path]
Generate health report...

## Configuration Commands (tagex config)
Manage vault configuration.

### tagex config validate [vault_path]
...

## Tag Operations (tagex tag)
...
```

4. **docs/MIGRATION.md** (NEW)
```markdown
# Migration Guide: v0.x → v1.0

## Breaking Changes
None! All v0.x commands still work with deprecation warnings.

## Deprecated Commands
- `tagex tags` → `tagex tag`
- `tagex tags extract` → `tagex tag export`
- `tagex tags fix-duplicates` → `tagex tag fix`

## New Commands
- `tagex tag add` - Add tags to files
- `tagex config show` - Display configuration
...
```

**Deliverables**:
- Updated README
- Migration guide
- Command reference
- Updated CLAUDE.md

---

### Phase 5: Remove Deprecations (v2.0 - Future)
**Status**: Breaking changes, major version bump

**Changes**:
- Remove `tags` group entirely
- Remove old argument format support
- Remove deprecated command names
- Clean up codebase

**Timeline**: 6-12 months after Phase 4

---

## Quick Wins (Can Implement Now)

These improvements require minimal code changes and provide immediate value:

### 1. Add Missing Commands (2 hours)
```python
@tag.command('add')
@click.argument('vault_path', type=click.Path(exists=True))
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('tags', nargs=-1, required=True)
@click.option('--execute', is_flag=True)
def add(vault_path, file_path, tags, execute):
    """Add tags to a specific file."""
    # Implementation similar to AddTagsOperation
    pass

@config.command('show')
@click.argument('vault_path', default='.', required=False)
def show(vault_path):
    """Display current configuration."""
    from pathlib import Path
    import yaml

    config_file = Path(vault_path) / '.tagex' / 'config.yaml'
    if config_file.exists():
        with open(config_file) as f:
            config = yaml.safe_load(f)
        print(yaml.dump(config, default_flow_style=False))
    else:
        print("No configuration found. Run: tagex init")

@vault.command('backup')
@click.argument('vault_path', type=click.Path(exists=True))
@click.option('--output', type=click.Path())
def backup(vault_path, output):
    """Create backup of vault."""
    # Create timestamped backup
    pass
```

### 2. Improve Help Text (1 hour)
```python
@main.group()
def analyze():
    """Analyze tag relationships and suggest improvements.

    All analyze commands are READ-ONLY and safe to run anytime.
    They help you understand your tag structure before making changes.

    Common workflow:
      1. tagex analyze recommendations --export ops.yaml
      2. edit ops.yaml (review and adjust)
      3. tagex tag apply ops.yaml (preview)
      4. tagex tag apply ops.yaml --execute (apply changes)

    Examples:
      tagex analyze synonyms          # Find semantic duplicates
      tagex analyze plurals           # Find singular/plural variants
      tagex analyze recommendations   # Run all analyzers
    """
    pass
```

### 3. Add Workflow Command (3 hours)
```python
@main.command('workflow')
@click.argument('vault_path', default='.', required=False)
def workflow(vault_path):
    """Interactive workflow wizard.

    Guides you through the tag cleanup process step by step.
    """
    import click

    click.echo("Tagex Interactive Workflow\n")
    click.echo("=" * 50)

    # Step 1: Check if initialized
    if not (Path(vault_path) / '.tagex').exists():
        if click.confirm('Vault not initialized. Initialize now?'):
            # Run init
            pass

    # Step 2: Show stats
    click.echo("\nStep 1: Analyzing vault...")
    # Run stats

    # Step 3: Ask what to analyze
    choice = click.prompt(
        'What would you like to analyze?',
        type=click.Choice(['synonyms', 'plurals', 'all']),
        default='all'
    )

    # Step 4: Generate operations
    # ...

    # Step 5: Review and apply
    # ...
```

### 4. Standardize Vault Path Default (30 minutes)
```python
# Create utility function
def get_vault_path(path_arg):
    """Standardize vault path handling across all commands."""
    if path_arg is None or path_arg == '.':
        return Path.cwd()
    return Path(path_arg).resolve()

# Use in all commands
@main.command()
@click.argument('vault_path', default='.', required=False)
def stats(vault_path):
    vault = get_vault_path(vault_path)
    print(f"Vault: {vault}")
    # ...
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_command_aliases.py
def test_tag_group_alias():
    """Test that 'tags' and 'tag' both work."""
    result1 = runner.invoke(cli, ['tags', 'export', test_vault])
    result2 = runner.invoke(cli, ['tag', 'export', test_vault])
    assert result1.output == result2.output

def test_extract_export_alias():
    """Test that 'extract' and 'export' both work."""
    result1 = runner.invoke(cli, ['tag', 'extract', test_vault])
    result2 = runner.invoke(cli, ['tag', 'export', test_vault])
    assert result1.output == result2.output

def test_deprecation_warnings():
    """Test that old commands show deprecation warnings."""
    result = runner.invoke(cli, ['tags', 'extract', test_vault])
    assert 'deprecated' in result.stderr.lower()
```

### Integration Tests
```bash
# tests/integration/test_workflow.sh
#!/bin/bash

# Test full workflow with both old and new commands
echo "Testing backward compatibility..."

# Old style
tagex tags extract > old.json
tagex tags rename test-vault old-tag new-tag

# New style
tagex tag export > new.json
tagex tag rename test-vault old-tag new-tag

# Compare outputs
diff old.json new.json
```

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking user scripts | HIGH | LOW | Keep aliases, phased deprecation |
| Confusion during transition | MEDIUM | MEDIUM | Clear docs, warnings |
| Incomplete migration | MEDIUM | LOW | Comprehensive test suite |
| Documentation drift | LOW | MEDIUM | Update docs with each phase |

---

## Success Metrics

### Phase 1-2 (Aliases & Compatibility)
- [ ] All old commands still work
- [ ] All new commands work identically
- [ ] Test suite passes 100%
- [ ] No user-reported breakage

### Phase 3-4 (Standardization & Docs)
- [ ] All commands use consistent output format
- [ ] Documentation updated
- [ ] Migration guide complete
- [ ] User feedback positive

### Long-term (v2.0)
- [ ] Clean codebase with no legacy aliases
- [ ] Intuitive command structure
- [ ] High user satisfaction
- [ ] Easy to extend with new commands

---

## Timeline Summary

| Phase | Duration | Status |
|-------|----------|--------|
| 0: Planning | 1 week | ✅ Complete |
| 1: Aliases | 2 weeks | 🔜 Ready to start |
| 2: Arguments | 1 week | ⏳ After Phase 1 |
| 3: Output | 1 week | ⏳ After Phase 2 |
| 4: Docs | 1 week | ⏳ After Phase 3 |
| 5: Cleanup | Future (v2.0) | ⏸️ 6-12 months out |

**Total time to v1.0**: ~6 weeks

---

## Next Steps

1. **Review this roadmap** with stakeholders
2. **Create GitHub issues** for each phase
3. **Start Phase 1** implementation
4. **Draft migration guide** for users
5. **Set up deprecation timeline**

---

## Questions to Answer

- [ ] What's the target release date for v1.0?
- [ ] How long should we maintain deprecated commands?
- [ ] Should we add more interactive features (wizard mode)?
- [ ] Do we need a configuration migration tool?
- [ ] Should we support both Python and binary distributions?

---

## Appendix: Command Mapping

### Old → New Command Mapping

```
OLD COMMAND                          NEW COMMAND
─────────────────────────────────────────────────────────────
tagex tags extract                   tagex tag export
tagex tags rename                    tagex tag rename
tagex tags merge                     tagex tag merge
tagex tags delete                    tagex tag delete
tagex tags fix-duplicates            tagex tag fix
tagex tags apply                     tagex tag apply
                                     tagex tag add (NEW)

tagex vault cleanup-backups          tagex vault cleanup
                                     tagex vault backup (NEW)
                                     tagex vault verify (NEW)

tagex analyze merge                  tagex analyze merges

                                     tagex config validate (MOVED from top)
                                     tagex config show (NEW)
                                     tagex config edit (NEW)

tagex init                           tagex init (UNCHANGED)
tagex validate                       tagex config validate (MOVED)
tagex stats                          tagex stats (UNCHANGED)
tagex health                         tagex health (UNCHANGED)
```
