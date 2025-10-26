#!/usr/bin/env python3
"""
Input handler for analyze commands - supports both vault and JSON inputs.

This module provides unified input handling for analyze commands, allowing them
to accept either:
- Vault paths (extract tags on-the-fly)
- JSON files (load pre-extracted tag data)
"""
import json
from pathlib import Path
from typing import List, Dict, Any


def load_or_extract_tags(input_path: str, tag_types: str = 'frontmatter',
                         filter_tags: bool = True) -> List[Dict[str, Any]]:
    """Load tag data from JSON file or extract from vault.

    Args:
        input_path: Path to either a JSON file or vault directory
        tag_types: Tag types to extract if vault ('frontmatter', 'inline', 'both')
        filter_tags: Whether to filter tags when extracting from vault

    Returns:
        List of tag dictionaries in standard format

    Raises:
        ValueError: If input path doesn't exist or is invalid
    """
    path = Path(input_path)

    if not path.exists():
        raise ValueError(f"Input path does not exist: {input_path}")

    # Check if it's a JSON file
    if path.is_file() and path.suffix == '.json':
        return _load_json_file(str(path))

    # Check if it's a directory (vault)
    if path.is_dir():
        return _extract_from_vault(str(path), tag_types, filter_tags)

    # If it's a file but not JSON, treat as error
    if path.is_file():
        raise ValueError(f"File must be .json format: {input_path}")

    raise ValueError(f"Invalid input path: {input_path}")


def _load_json_file(json_file: str) -> List[Dict[str, Any]]:
    """Load tag data from JSON file.

    Args:
        json_file: Path to JSON file containing tag data

    Returns:
        List of tag dictionaries
    """
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Handle both old and new formats
    # Old format: direct list
    # New format: dict with 'tags' key
    if isinstance(data, list):
        return data  # type: ignore[return-value]
    elif isinstance(data, dict) and 'tags' in data:
        return data['tags']  # type: ignore[return-value]
    else:
        raise ValueError(f"Invalid JSON format in {json_file}")


def _extract_from_vault(vault_path: str, tag_types: str,
                       filter_tags: bool) -> List[Dict[str, Any]]:
    """Extract tags from vault on-the-fly.

    Args:
        vault_path: Path to vault directory
        tag_types: Tag types to extract ('frontmatter', 'inline', 'both')
        filter_tags: Whether to filter tags

    Returns:
        List of tag dictionaries in plugin JSON format
    """
    from tagex.core.extractor.core import TagExtractor
    from tagex.core.extractor.output_formatter import format_as_plugin_json

    # Initialize extractor
    extractor = TagExtractor(vault_path, filter_tags=filter_tags, tag_types=tag_types)

    # Extract tags
    tag_data = extractor.extract_tags()

    # Convert to plugin JSON format (same format as extract command output)
    # This ensures compatibility with all analyze commands
    return format_as_plugin_json(tag_data)


def get_input_type(input_path: str) -> str:
    """Determine if input is a vault or JSON file.

    Args:
        input_path: Path to check

    Returns:
        'vault' or 'json'

    Raises:
        ValueError: If path is invalid
    """
    path = Path(input_path)

    if not path.exists():
        raise ValueError(f"Path does not exist: {input_path}")

    if path.is_file() and path.suffix == '.json':
        return 'json'
    elif path.is_dir():
        return 'vault'
    else:
        raise ValueError(f"Invalid input: must be .json file or directory")
