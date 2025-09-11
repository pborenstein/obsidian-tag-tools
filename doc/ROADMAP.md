# TagEx Roadmap

This roadmap outlines planned features and improvements based on real-world Obsidian power user needs.

## Missing Core Features

### Tag Operations
- [ ] **Tag rename/merge operations** - Actually modify tags across files after analysis
- [ ] **Bulk tag operations** - Add/remove tags from multiple files at once
- [ ] **Tag hierarchy management** - Convert flat tags to nested structures
- [ ] **Duplicate/similar tag detection** - Find and cleanup redundant tags

### Integration & Workflow
- [ ] **Obsidian plugin integration** - Work directly with Obsidian's tag system
- [ ] **Watch mode** - Real-time tag monitoring for active vaults
- [ ] **Graph view integration** - Export data compatible with Obsidian's graph
- [ ] **Extended export formats** - OPML, mind maps, other tool integrations

### Advanced Analysis
- [ ] **Tag usage trends** - Track tag usage patterns over time
- [ ] **Unused/orphaned tag detection** - Find tags that should be cleaned up
- [ ] **Tag dependency analysis** - Identify tags that always appear together
- [ ] **Smart consolidation recommendations** - Beyond current migration analysis

### Practical Usage
- [ ] **Configuration file support** - Save common settings and exclusions
- [ ] **Tag naming conventions** - Define and validate tag naming rules
- [ ] **Tag aliases/synonyms** - Support for equivalent tag mappings
- [ ] **Backup/restore functionality** - Safe tag operations with rollback

### User Experience
- [ ] **Interactive mode** - Review changes before applying
- [ ] **Dry-run mode** - Preview tag operations without modification
- [ ] **Undo functionality** - Reverse tag operations
- [ ] **Progress indicators** - Show progress for large vault operations

## Immediate Priorities

### 1. Tag Operations (`tagex fix` command)
Implement actual tag modification capabilities:
- `tagex fix rename old-tag new-tag` - Rename tags across all files
- `tagex fix merge tag1,tag2,tag3 into new-tag` - Consolidate multiple tags
- `tagex fix apply migration.json` - Apply migration analysis results

### 2. Interactive Mode (`tagex interactive`)
Step-by-step tag cleanup workflow:
- Present analysis results
- Allow user to select actions
- Preview changes before applying
- Confirm each operation

### 3. Configuration System
- `.tagexrc` or `tagex.config.json` for persistent settings
- Vault-specific configuration
- Default exclusion patterns
- Tag naming rules and validation

## Future Enhancements

### Advanced Features
- Time-series analysis of tag evolution
- Machine learning for tag suggestions
- Integration with external knowledge management tools
- Multi-vault tag synchronization

### Performance & Scale
- [ ] Incremental processing for large vaults
- [ ] Background processing capabilities
- [ ] Memory optimization for massive tag sets
- [ ] Parallel processing for analysis operations
- [ ] Caching of validation results
- [ ] Batch processing of tag operations

## Implementation Notes

The current analysis tools provide excellent research capabilities but need actionable operations. Most Obsidian users want to go from "here are your tag problems" to "fix these tag problems" without manually editing hundreds of files.

Focus should be on practical tag management workflows that integrate naturally with existing Obsidian usage patterns.