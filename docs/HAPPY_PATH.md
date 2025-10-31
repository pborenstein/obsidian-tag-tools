# tagex Happy Path Cheat Sheet

**The fastest way to clean up your Obsidian vault's tags (15 minutes)**

## The Commands

```bash
# 1. Install (one-time)
uv tool install --editable .

# 2. Navigate to your vault
cd "$HOME/Obsidian/MyVault"

# 3. Initialize (one-time)
tagex init

# 4. See what you have
tagex stats
tagex health

# 5. Fix any duplicates (if health reported them)
tagex tag fix                    # Preview
tagex tag fix --execute          # Apply

# 6. Generate recommendations
tagex analyze recommendations --export operations.yaml

# 7. Review and edit operations.yaml
#    - Set enabled: true for operations you want
#    - Set enabled: false for operations you don't want
#    - Delete entire operations you disagree with

# 8. Preview changes
tagex tag apply operations.yaml

# 9. Apply changes (when ready)
tagex tag apply operations.yaml --execute

# 10. Verify improvements
tagex stats
tagex health

# 11. Clean up backups (optional - after verifying everything)
tagex vault cleanup --execute
```

## Safety Rules

- **Preview by default** - Commands show what will happen without modifying files
- **--execute to apply** - Add `--execute` flag only when ready to modify
- **Backups created** - `.bak` files are your safety net
- **Logs maintained** - All changes logged to `.tagex/logs/`

## Quick Fixes (Individual Tags)

```bash
tagex tag rename old-tag new-tag --execute
tagex tag merge tag1 tag2 tag3 --into target --execute
tagex tag delete unwanted-tag --execute
tagex tag add file.md python programming --execute
```

## When Things Go Wrong

```bash
# Restore from backup
mv "My Note.md.bak" "My Note.md"

# Check what changed
ls -la .tagex/logs/
cat .tagex/logs/operations-*.log
```

---

**Need more details?** See [GETTING_STARTED.md](GETTING_STARTED.md) for the complete guide with explanations.
