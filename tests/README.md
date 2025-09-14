# Test Suite Documentation

This directory contains the comprehensive test suite for the tagex Obsidian tag management tool.

## Test Structure

```
tests/
├── conftest.py          ← Test fixtures and mock data
├── test_cli.py          ← CLI interface tests
├── test_extractor.py    ← Core tag extraction engine tests
├── test_operations.py   ← Tag rename/merge operation tests
├── test_parsers.py      ← Frontmatter and inline parser tests
├── test_utils.py        ← Utility function tests
├── test_workflows.py    ← End-to-end workflow tests
└── test_analysis.py     ← Tag analysis and pair analysis tests
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test module
pytest tests/test_cli.py

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run with verbose output
pytest tests/ -v

# Run specific test function
pytest tests/test_extractor.py::TestTagExtractor::test_extract_basic_tags
```

## Test Fixtures (conftest.py)

The test suite includes comprehensive fixtures for testing:

### Mock Vaults
- **`simple_vault`** - Basic Obsidian vault with standard markdown files
- **`complex_vault`** - Advanced vault with edge cases, malformed YAML, subdirectories

### Test Data
- **`expected_simple_tags`** - Expected extraction results for validation
- **`test_output_formats`** - Sample data in JSON/CSV/txt formats
- **`sample_pair_data`** - Mock data for analysis testing
- **`valid_tags_list`** / **`invalid_tags_list`** - Tag validation test cases

### Mock Operations
- **`mock_operation_log`** - Sample operation logging data
- **`temp_dir`** - Temporary directory management

## Test Categories

### 1. Core Extraction Tests (`test_extractor.py`)
Tests the main TagExtractor engine:
- Frontmatter YAML tag extraction
- Inline hashtag extraction
- **Tag type filtering** - selective extraction of frontmatter, inline, or both
- Tag filtering and validation
- File processing statistics
- Error handling for malformed files

### 2. Parser Tests (`test_parsers.py`)
Tests individual parsing modules:
- **Frontmatter parser**: YAML header processing, array/string formats
- **Inline parser**: Hashtag detection, URL fragment exclusion
- Edge cases: Malformed YAML, special characters

### 3. Operations Tests (`test_operations.py`)
Tests tag modification operations:
- **Rename operations**: Single tag renaming across vault
- **Merge operations**: Multi-tag consolidation
- **Delete operations**: Tag removal from frontmatter and inline content
- **Tag type filtering**: Selective processing of frontmatter, inline, or both tag types
- Dry-run functionality and logging
- File integrity and hash validation

### 4. CLI Tests (`test_cli.py`)
Tests command-line interface:
- Multi-command structure (extract/rename/merge/delete)
- **Tag types option** - `--tag-types` parameter validation and functionality
- Argument parsing and validation
- Output format options
- Error handling and exit codes

### 5. Utility Tests (`test_utils.py`)
Tests support functions:
- **File discovery**: Markdown file enumeration, pattern exclusion
- **Tag normalization**: Case handling, whitespace cleanup
- **Tag validation**: Noise filtering, character set validation

### 6. Analysis Tests (`test_analysis.py`)
Tests tag relationship analysis:
- Co-occurrence calculation
- Tag clustering detection
- Hub tag identification
- Filtering integration

### 7. Workflow Tests (`test_workflows.py`)
Tests complete end-to-end scenarios:
- Full extraction → analysis pipeline
- Operation → verification workflows
- Multi-format output generation

## Test Environment

**Dependencies:**
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting  
- `pytest-mock` - Mocking utilities
- `click.testing` - CLI testing utilities

**Fixtures create:**
- Temporary directories with mock Obsidian vaults
- Files with various tag formats and edge cases
- Expected results for validation
- Mock operation logs and statistics

## Key Testing Principles

1. **Isolation**: Each test uses temporary directories and fixtures
2. **Coverage**: Tests cover normal cases, edge cases, and error conditions
3. **Validation**: Tests verify both functionality and data integrity
4. **Realistic data**: Mock vaults mirror real Obsidian structure and content
5. **Operations safety**: Tag operations tested with dry-run and integrity checks

## Mock Vault Structure

The test fixtures create realistic Obsidian vaults:

**Simple Vault:**
- Files with frontmatter arrays: `tags: [work, notes, ideas]`
- Files with single tags: `tag: work`
- Files with only inline tags: `#articles #research`
- Files with no tags

**Complex Vault:**
- Nested directories and subdirectories
- Malformed YAML edge cases
- International characters in tags
- Template files (excluded by patterns)
- Binary files (ignored)
- Empty files

## Running Specific Test Categories

```bash
# Test core extraction only
pytest tests/test_extractor.py

# Test tag operations only  
pytest tests/test_operations.py

# Test CLI interface
pytest tests/test_cli.py

# Test with specific patterns
pytest tests/ -k "test_rename"
pytest tests/ -k "frontmatter"
```

The test suite ensures reliable tag extraction, safe operations, and accurate analysis across diverse Obsidian vault structures.