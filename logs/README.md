# Operation Log Directory

This directory contains detailed operation logs for tag modification operations performed by tagex.

## Log Files

Log files are automatically created when you run tag operations (rename, merge, delete) and follow this naming pattern:

```
<operation-type>_<timestamp>.json
```

**Examples:**
- `tag-rename-op_20241216_143022.json` - Tag rename operation
- `tag-merge-op_20241216_143157.json` - Tag merge operation
- `tag-delete-op_20241216_143245.json` - Tag delete operation

## Log File Structure

Each log file contains comprehensive operation details in JSON format:

```json
{
  "operation": "renameOperation",
  "operation_type": "rename",
  "timestamp": "2024-12-16T14:30:22.123456",
  "vault_path": "/path/to/vault",
  "dry_run": false,
  "tag_types": "frontmatter",
  "old_tag": "old-tag-name",
  "new_tag": "new-tag-name",
  "changes": [
    {
      "file": "notes/example.md",
      "before_hash": "a1b2c3d4e5f6g7h8",
      "after_hash": "h8g7f6e5d4c3b2a1",
      "modifications": [
        {
          "type": "tag_rename",
          "from": "old-tag-name",
          "to": "new-tag-name"
        }
      ]
    }
  ],
  "stats": {
    "files_processed": 45,
    "files_modified": 3,
    "tags_modified": 7,
    "errors": 0
  }
}
```

## Key Fields

- **operation**: Internal operation class name
- **operation_type**: Human-readable operation type (rename, merge, delete)
- **timestamp**: ISO 8601 timestamp when operation started
- **vault_path**: Absolute path to the Obsidian vault
- **dry_run**: Whether this was a preview-only operation
- **tag_types**: Which tag types were processed (frontmatter, inline, both)
- **changes**: Array of all file modifications with integrity hashes
- **stats**: Summary statistics of the operation

## Operation-Specific Fields

### Rename Operations
- `old_tag`: The tag that was renamed
- `new_tag`: The new tag name

### Merge Operations
- `source_tags`: Array of tags that were merged
- `target_tag`: The tag they were merged into

### Delete Operations
- `deleted_tags`: Array of tags that were deleted

## File Integrity

Each file change includes before/after SHA-256 hashes (truncated to 16 characters) for integrity verification. This allows you to:

1. Verify that files were actually modified
2. Detect if files have been changed since the operation
3. Implement rollback functionality if needed

## Usage

Log files are created automatically - you don't need to do anything to generate them. They provide:

- **Audit trail** for all tag operations
- **Debugging information** when operations don't work as expected
- **Rollback data** for implementing undo functionality
- **Statistics** for understanding the scope of changes

## Cleanup

Log files accumulate over time. You can safely delete old log files you no longer need, but keep recent ones for reference and debugging.