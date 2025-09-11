"""
File discovery utilities for finding markdown files in an Obsidian vault.
"""
from pathlib import Path
from typing import List, Set


def find_markdown_files(vault_path: str, exclude_patterns: Set[str] = None) -> List[Path]:
    """
    Recursively find all markdown files in a vault directory.
    
    Args:
        vault_path: Path to the Obsidian vault root
        exclude_patterns: Set of directory patterns to exclude
        
    Returns:
        List of Path objects for markdown files
    """
    if exclude_patterns is None:
        exclude_patterns = {'.obsidian', '.git', '.DS_Store', '__pycache__', 'node_modules'}
    
    vault_root = Path(vault_path)
    if not vault_root.exists():
        raise FileNotFoundError(f"Vault path does not exist: {vault_path}")
    
    if not vault_root.is_dir():
        raise NotADirectoryError(f"Vault path is not a directory: {vault_path}")
    
    markdown_files = []
    
    def should_exclude_dir(dir_path: Path) -> bool:
        """Check if directory should be excluded based on patterns."""
        return any(pattern in dir_path.name for pattern in exclude_patterns)
    
    def scan_directory(directory: Path) -> None:
        """Recursively scan directory for markdown files."""
        try:
            for item in directory.iterdir():
                if item.is_file():
                    if item.suffix.lower() == '.md':
                        markdown_files.append(item)
                elif item.is_dir():
                    if not should_exclude_dir(item):
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