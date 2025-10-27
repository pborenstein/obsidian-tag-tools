"""
Exclusions configuration for preventing tags from being merged.

This module manages tag exclusions stored in .tagex/exclusions.yaml
in the vault directory.
"""

import yaml
from pathlib import Path
from typing import Set


class ExclusionsConfig:
    """Manage tags that should be excluded from merge/synonym suggestions.

    Exclusions are stored in .tagex/exclusions.yaml in the vault with format:

    exclude_tags:
      - spain
      - france
      - china
      - india
      # Country names
      - usa
      - britain
      # Proper nouns
      - shakespeare
      - orwell

    Tags in this list will never be suggested for merging, even if they
    have high semantic similarity.
    """

    def __init__(self, vault_path: Path = None):
        """Initialize exclusions configuration.

        Args:
            vault_path: Path to the vault root directory (optional)
        """
        self.vault_path = vault_path
        self.excluded_tags: Set[str] = set()

        if vault_path:
            self.config_file = Path(vault_path) / '.tagex' / 'exclusions.yaml'
            if self.config_file.exists():
                self.load()

    def load(self) -> None:
        """Load exclusions from YAML file.

        Raises:
            yaml.YAMLError: If the YAML file is malformed
        """
        with open(self.config_file) as f:
            config = yaml.safe_load(f)

        if not config:
            return

        # Process excluded tags (normalize to lowercase)
        if 'exclude_tags' in config:
            self.excluded_tags = {tag.lower().strip() for tag in config['exclude_tags'] if tag}

    def is_excluded(self, tag: str) -> bool:
        """Check if a tag is excluded.

        Args:
            tag: The tag to check

        Returns:
            True if the tag is excluded
        """
        return tag.lower().strip() in self.excluded_tags

    def is_operation_excluded(self, source_tags: list, target_tag: str) -> bool:
        """Check if an operation involves any excluded tags.

        Args:
            source_tags: List of source tags being merged
            target_tag: Target tag for the merge

        Returns:
            True if any tag in the operation is excluded
        """
        # Check target
        if self.is_excluded(target_tag):
            return True

        # Check sources
        for tag in source_tags:
            if self.is_excluded(tag):
                return True

        return False

    def add_exclusion(self, tag: str) -> None:
        """Add a tag to the exclusion list and save.

        Args:
            tag: Tag to exclude
        """
        self.excluded_tags.add(tag.lower().strip())
        self.save()

    def remove_exclusion(self, tag: str) -> bool:
        """Remove a tag from the exclusion list and save.

        Args:
            tag: Tag to remove from exclusions

        Returns:
            True if the tag was removed, False if it wasn't in the list
        """
        tag_lower = tag.lower().strip()
        if tag_lower in self.excluded_tags:
            self.excluded_tags.remove(tag_lower)
            self.save()
            return True
        return False

    def save(self) -> None:
        """Save exclusions to YAML file."""
        if not self.vault_path:
            return

        config = {
            'exclude_tags': sorted(list(self.excluded_tags))
        }

        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, 'w') as f:
            f.write("# Tags to exclude from merge/synonym suggestions\n")
            f.write("# These tags will never be suggested for merging\n")
            f.write("# Useful for proper nouns, country names, etc.\n\n")
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def get_all_exclusions(self) -> Set[str]:
        """Get all excluded tags.

        Returns:
            Set of excluded tag names
        """
        return self.excluded_tags.copy()

    @staticmethod
    def create_template(vault_path: Path) -> Path:
        """Create a template exclusions file.

        Args:
            vault_path: Path to the vault root directory

        Returns:
            Path to the created template file
        """
        config_file = vault_path / '.tagex' / 'exclusions.yaml'
        config_file.parent.mkdir(parents=True, exist_ok=True)

        template = """# Tags to exclude from merge/synonym suggestions
# These tags will never be suggested for merging
# Useful for proper nouns, country names, etc.

exclude_tags:
  # Add tags to exclude below (one per line)
  # Example:
  # - spain
  # - france
  # - shakespeare
"""

        with open(config_file, 'w') as f:
            f.write(template)

        return config_file
