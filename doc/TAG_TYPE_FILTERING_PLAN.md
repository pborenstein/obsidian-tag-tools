# Implementation Plan: Tag Type Filtering Options

## Overview

Add `--frontmatter-only` and `--inline-only` options to all tagex commands to allow users to work exclusively with frontmatter tags or inline hashtags.

## Current Architecture Analysis

The system separates tag extraction into two parsers:

- `parsers/frontmatter_parser.py` - Handles YAML frontmatter tags
- `parsers/inline_parser.py` - Handles #hashtag inline tags
- `extractor/core.py` - Combines both parsers in `_process_file()` at line 94-98
- `operations/tag_operations.py` - Uses both parsers for all operations

## Implementation Plan

### 1. CLI Option Structure

Add mutually exclusive options to all commands (extract, rename, merge, delete):

```python
@click.option('--frontmatter-only', is_flag=True, help='Work with frontmatter tags only')
@click.option('--inline-only', is_flag=True, help='Work with inline hashtags only')
```

Validation: Ensure both flags cannot be used simultaneously.

### 2. Core Extractor Modifications

**File**: `extractor/core.py`

Add `tag_types` parameter to `TagExtractor.__init__()`:

```python
def __init__(self, vault_path: str, exclude_patterns: Set[str] = None,
             filter_tags: bool = True, tag_types: str = 'both'):
    # tag_types: 'both', 'frontmatter', 'inline'
```

Modify `_process_file()` method to conditionally call parsers based on `tag_types`.

### 3. Operations Module Updates

**File**: `operations/tag_operations.py`

Update base class `TagOperationEngine.__init__()` to accept `tag_types` parameter.

Modify these methods to respect tag type filtering:

- `file_contains_tag()` - Only check relevant tag sources
- `transform_file_tags()` - Only transform specified tag types
- `_transform_yaml_text()` - Skip if inline-only mode
- `_transform_inline_tags()` - Skip if frontmatter-only mode

### 4. Parser Integration

**Files**: `parsers/frontmatter_parser.py`, `parsers/inline_parser.py`

No changes needed - parsers remain focused on their specific formats.

### 5. CLI Command Updates

**File**: `main.py`

Add options to all four commands:

```python
@click.option('--frontmatter-only', is_flag=True, help='Work with frontmatter tags only')
@click.option('--inline-only', is_flag=True, help='Work with inline hashtags only')
```

Add validation function:

```python
def validate_tag_type_options(frontmatter_only, inline_only):
    if frontmatter_only and inline_only:
        raise click.BadParameter("Cannot use both --frontmatter-only and --inline-only")
    return 'frontmatter' if frontmatter_only else 'inline' if inline_only else 'both'
```

### 6. Test Updates

**Files**: `tests/test_*.py`

Add test cases for:

- CLI validation (mutually exclusive flags)
- Frontmatter-only extraction/operations
- Inline-only extraction/operations
- Edge cases (files with only one tag type)

### 7. Documentation Updates

**Files**: Update help text and examples

- Add examples in CLAUDE.md showing new options
- Update command help text to describe tag type filtering

## Implementation Order

1. **Core Extractor** - Add tag_types parameter and filtering logic
2. **Operations Base** - Update TagOperationEngine to support tag type filtering
3. **CLI Integration** - Add options and validation to all commands
4. **Operations Implementations** - Update rename/merge/delete operations
5. **Tests** - Add comprehensive test coverage
6. **Documentation** - Update help and examples

## Key Benefits

- **Precision**: Users can target specific tag types for operations
- **Safety**: Prevents accidental modification of tags in unwanted locations
- **Flexibility**: Supports different workflow preferences (frontmatter vs inline)
- **Backward Compatibility**: Default behavior unchanged (both tag types)

## Example Usage

```bash
# Extract only frontmatter tags
tagex extract /path/to/vault --frontmatter-only

# Rename only inline hashtags
tagex rename /path/to/vault old-tag new-tag --inline-only

# Merge frontmatter tags only
tagex merge /path/to/vault tag1 tag2 --into target --frontmatter-only --dry-run
```