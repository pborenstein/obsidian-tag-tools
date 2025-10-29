#!/usr/bin/env python3
"""
Configuration for file and directory exclusions.

Allows users to configure which files and directories to exclude from processing.
"""
import yaml
from pathlib import Path
from typing import Set, List, Optional


# Default configuration
DEFAULT_EXCLUDE_DOTFILES = True
DEFAULT_INCLUDE_DOTFILES: Set[str] = set()  # Empty by default
DEFAULT_EXCLUDE_PATTERNS: Set[str] = {
    # Common non-dotfile directories to exclude
    '__pycache__',
    'node_modules',
}


class FileExclusionConfig:
    """Configuration for file and directory exclusion behavior."""

    def __init__(self,
                 exclude_dotfiles: bool = DEFAULT_EXCLUDE_DOTFILES,
                 include_dotfiles: Optional[Set[str]] = None,
                 exclude_patterns: Optional[Set[str]] = None):
        """Initialize file exclusion configuration.

        Args:
            exclude_dotfiles: Whether to exclude all dotfiles/directories
            include_dotfiles: Specific dotfiles to include (allowlist)
            exclude_patterns: Additional patterns to exclude
        """
        self.exclude_dotfiles = exclude_dotfiles
        self.include_dotfiles = include_dotfiles or DEFAULT_INCLUDE_DOTFILES.copy()
        self.exclude_patterns = exclude_patterns or DEFAULT_EXCLUDE_PATTERNS.copy()

    @classmethod
    def from_vault(cls, vault_path: str) -> 'FileExclusionConfig':
        """Load configuration from vault's .tagex/config.yaml file.

        Args:
            vault_path: Path to vault directory

        Returns:
            FileExclusionConfig instance with loaded or default settings
        """
        config_file = Path(vault_path) / '.tagex' / 'config.yaml'

        if not config_file.exists():
            return cls()  # Return defaults

        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}

            file_config = config_data.get('file_exclusions', {})

            exclude_dotfiles = file_config.get('exclude_dotfiles', DEFAULT_EXCLUDE_DOTFILES)

            include_dotfiles = set(file_config.get('include_dotfiles', []))

            exclude_patterns = set(file_config.get('exclude_patterns', []))
            # Merge with defaults
            exclude_patterns.update(DEFAULT_EXCLUDE_PATTERNS)

            return cls(
                exclude_dotfiles=exclude_dotfiles,
                include_dotfiles=include_dotfiles,
                exclude_patterns=exclude_patterns
            )

        except Exception:
            # If there's any error loading config, use defaults
            return cls()

    def should_exclude(self, path: Path, vault_root: Path) -> bool:
        """Check if a path should be excluded.

        Args:
            path: Path to check (absolute or relative)
            vault_root: Vault root directory

        Returns:
            True if the path should be excluded
        """
        try:
            relative_path = path.relative_to(vault_root)
        except ValueError:
            # Path is not within vault root
            return False

        relative_str = str(relative_path)
        path_name = path.name

        # Check if it's a dotfile/directory
        if path_name.startswith('.'):
            if self.exclude_dotfiles:
                # Check if it's in the allowlist
                if path_name in self.include_dotfiles or relative_str in self.include_dotfiles:
                    return False  # Don't exclude - it's allowed
                return True  # Exclude all other dotfiles
            # If not excluding dotfiles, fall through to pattern checks

        # Check against exclusion patterns
        import fnmatch
        for pattern in self.exclude_patterns:
            # Handle directory patterns like "templates/*"
            if pattern.endswith('/*'):
                dir_pattern = pattern[:-2]  # Remove "/*"
                if relative_str.startswith(dir_pattern + '/') or relative_str == dir_pattern:
                    return True
            # Handle file patterns like "*.excalidraw.md"
            elif fnmatch.fnmatch(relative_str, pattern):
                return True
            # Handle exact matches
            elif pattern in relative_str:
                return True

        return False

    def to_dict(self) -> dict:
        """Convert configuration to dictionary format.

        Returns:
            Dictionary representation of configuration
        """
        return {
            'exclude_dotfiles': self.exclude_dotfiles,
            'include_dotfiles': sorted(list(self.include_dotfiles)),
            'exclude_patterns': sorted(list(self.exclude_patterns))
        }
