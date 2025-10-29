"""
File discovery utilities for finding markdown files in an Obsidian vault.
"""
from pathlib import Path
from typing import List, Set, Union, Optional
import fnmatch


def find_markdown_files(vault_path: str, exclude_patterns: Union[Set[str], List[str], None] = None, use_config: bool = True) -> List[Path]:
    """
    Recursively find all markdown files in a vault directory.

    Args:
        vault_path: Path to the Obsidian vault root
        exclude_patterns: List/Set of additional glob patterns to exclude (merged with config)
        use_config: Whether to load exclusion config from .tagex/config.yaml (default: True)

    Returns:
        List of Path objects for markdown files
    """
    from ..config.file_exclusion_config import FileExclusionConfig

    vault_root = Path(vault_path)
    if not vault_root.exists():
        raise FileNotFoundError(f"Vault path does not exist: {vault_path}")

    if not vault_root.is_dir():
        raise NotADirectoryError(f"Vault path is not a directory: {vault_path}")

    # Load configuration
    config = FileExclusionConfig.from_vault(vault_path) if use_config else FileExclusionConfig()

    # Merge CLI-provided exclusion patterns with config
    if exclude_patterns:
        if isinstance(exclude_patterns, list):
            exclude_patterns = set(exclude_patterns)
        config.exclude_patterns.update(exclude_patterns)

    markdown_files = []

    def should_exclude_path(path: Path, vault_root: Path) -> bool:
        """Check if path should be excluded based on configuration."""
        return config.should_exclude(path, vault_root)

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