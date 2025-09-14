"""
File discovery utilities for finding markdown files in an Obsidian vault.
"""
from pathlib import Path
from typing import List, Set, Union
import fnmatch


def find_markdown_files(vault_path: str, exclude_patterns: Union[Set[str], List[str], None] = None) -> List[Path]:
    """
    Recursively find all markdown files in a vault directory.

    Args:
        vault_path: Path to the Obsidian vault root
        exclude_patterns: List/Set of glob patterns to exclude (files and directories)

    Returns:
        List of Path objects for markdown files
    """
    if exclude_patterns is None:
        exclude_patterns = {'.obsidian', '.git', '.DS_Store', '__pycache__', 'node_modules'}

    # Convert to set for faster lookup
    if isinstance(exclude_patterns, list):
        exclude_patterns = set(exclude_patterns)

    vault_root = Path(vault_path)
    if not vault_root.exists():
        raise FileNotFoundError(f"Vault path does not exist: {vault_path}")

    if not vault_root.is_dir():
        raise NotADirectoryError(f"Vault path is not a directory: {vault_path}")

    markdown_files = []

    def should_exclude_path(path: Path, vault_root: Path) -> bool:
        """Check if path should be excluded based on glob patterns."""
        # Get relative path for pattern matching
        try:
            relative_path = path.relative_to(vault_root)
            relative_str = str(relative_path)

            # Check against all exclusion patterns
            for pattern in exclude_patterns:
                # Handle directory patterns like "templates/*"
                if pattern.endswith('/*'):
                    dir_pattern = pattern[:-2]  # Remove "/*"
                    if relative_str.startswith(dir_pattern + '/') or relative_str == dir_pattern:
                        return True
                # Handle file patterns like "*.template.md"
                elif fnmatch.fnmatch(relative_str, pattern):
                    return True
                # Handle exact matches like ".obsidian"
                elif pattern in relative_str:
                    return True

            return False
        except ValueError:
            # Path is not within vault root
            return False

    def scan_directory(directory: Path) -> None:
        """Recursively scan directory for markdown files."""
        try:
            for item in directory.iterdir():
                # Skip excluded paths
                if should_exclude_path(item, vault_root):
                    continue

                if item.is_file():
                    if item.suffix.lower() == '.md':
                        markdown_files.append(item)
                elif item.is_dir():
                    scan_directory(item)
        except PermissionError:
            # Skip directories we can't read
            pass

    scan_directory(vault_root)

    # Sort by path for consistent output
    return sorted(markdown_files)


def get_relative_path(file_path: Path, vault_root: Path) -> str:
    """
    Get relative path from vault root for a file.
    
    Args:
        file_path: Full path to the file
        vault_root: Path to vault root directory
        
    Returns:
        Relative path as string
    """
    try:
        return str(file_path.relative_to(vault_root))
    except ValueError:
        # File is not within vault root
        return str(file_path)