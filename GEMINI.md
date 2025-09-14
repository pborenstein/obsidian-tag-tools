# Gemini Context: Obsidian Tag Tools (`tagex`)

This document provides a comprehensive overview of the `tagex` project for the Gemini AI assistant. It covers the project's purpose, architecture, and key operational commands to facilitate effective collaboration.

## 1. Project Overview

`tagex` is a Python-based command-line interface (CLI) tool for managing tags within an [Obsidian](https://obsidian.md/) vault. It allows users to extract, analyze, and perform bulk operations like renaming, merging, and deleting tags across all markdown files in a vault.

### Core Features:
- **Tag Extraction**: Scans markdown files to find tags in both YAML frontmatter and inline content (e.g., `#tag`).
- **Tag Operations**: Provides `rename`, `merge`, and `delete` commands to modify tags safely across the entire vault.
- **Safe by Default**: All modification operations support a `--dry-run` mode to preview changes before they are applied.
- **Output Formatting**: Extracted tag data can be output in JSON, CSV, or a human-readable text format.
- **Advanced Filtering**: A sophisticated tag validation system is used by default to filter out noise (e.g., numbers, technical artifacts), which can be disabled with `--no-filter`.

### Technology Stack:
- **Language**: Python 3.13+
- **CLI Framework**: `click`
- **Dependency Management**: `uv`
- **Configuration**: `pyproject.toml`
- **Parsing**: `pyyaml` for frontmatter; custom regex for inline tags.
- **Testing**: `pytest`

### Architecture:
The project follows a modular architecture, ensuring a clear separation of concerns:
- **`main.py`**: The main entry point, defining the `click`-based CLI commands (`extract`, `rename`, `merge`, `delete`). It orchestrates the other components.
- **`extractor/`**: Contains the core logic for finding and extracting tags.
  - `core.py`: `TagExtractor` class manages the extraction pipeline.
  - `output_formatter.py`: Handles formatting the extracted data into different output types.
- **`parsers/`**: Responsible for parsing tags from file content.
  - `frontmatter_parser.py`: Extracts tags from the YAML frontmatter block.
  - `inline_parser.py`: Extracts inline `#tags` from the markdown body.
- **`operations/`**: Implements the logic for tag modification operations.
  - `tag_operations.py`: Contains the `TagOperationEngine` base class and concrete implementations like `RenameOperation`, `MergeOperation`, and `DeleteOperation`. These classes are designed for safety, preserving file formatting and creating detailed operation logs.
- **`utils/`**: Provides helper modules.
  - `file_discovery.py`: Efficiently finds markdown files while respecting exclusion patterns.
  - `tag_normalizer.py`: Handles tag validation, cleaning, and normalization.
- **`tests/`**: Contains a comprehensive test suite built with `pytest` to ensure correctness and stability.

## 2. Building and Running

The project uses `uv` for dependency management and running scripts.

### Installation
Install dependencies and make the `tagex` command available in the environment:
```bash
uv sync
uv tool install --editable .
```

### Running the Application
Once installed, the tool can be run directly using the `tagex` command.

**Extracting Tags:**
```bash
# Extract all tags to stdout as JSON
tagex extract /path/to/vault

# Extract and save to a CSV file
tagex extract /path/to/vault -f csv -o my_tags.csv

# Extract with verbose logging and no tag filtering
tagex extract /path/to/vault --verbose --no-filter
```

**Modifying Tags:**
All modification commands should be run with `--dry-run` first to preview changes.

```bash
# Preview renaming a tag
tagex rename /path/to/vault old-tag new-tag --dry-run

# Apply the rename
tagex rename /path/to/vault old-tag new-tag

# Preview merging several tags into one
tagex merge /path/to/vault tag1 tag2 --into consolidated-tag --dry-run

# Preview deleting tags
tagex delete /path/to/vault obsolete-tag --dry-run
```

### Running During Development
To run the tool without installing it globally, use `uv run`:
```bash
uv run main extract /path/to/vault
```

### Running Tests
The project has a comprehensive `pytest` suite.
```bash
# Run all tests
pytest
```

## 3. Development Conventions

- **Modularity**: Code is organized into distinct modules (`parsers`, `extractor`, `operations`, `utils`) with clear responsibilities. New functionality should follow this pattern.
- **Type Hinting**: The codebase uses Python's type hints extensively. All new code should be fully type-hinted.
- **Testing**: A comprehensive test suite exists in the `tests/` directory. New features or bug fixes must be accompanied by corresponding tests. The tests are structured to mirror the application's modules (e.g., `test_parsers.py`, `test_operations.py`).
- **Safety First**: Operations that modify files are built with safety as a primary concern. They are designed to be idempotent where possible, preserve file formatting, and always offer a `--dry-run` mode.
- **Logging**: The application uses the `logging` module. Verbose logging can be enabled with the `-v`/`--verbose` flag.
- **CLI Design**: The CLI is built with `click`. Commands and options should be well-documented with help text.
- **Error Handling**: The application aims to handle errors gracefully (e.g., file not found, permissions issues) and provide clear feedback to the user.
