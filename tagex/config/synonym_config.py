"""
Synonym configuration management for tag quality improvements.

This module manages user-defined synonym mappings stored in .tagex/synonyms.yaml
in the vault directory.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Set


class SynonymConfig:
    """Manage user-defined synonym mappings.

    Synonyms are stored in .tagex/synonyms.yaml in the vault with format:

    synonyms:
      - [neuro, neurodivergent, neurodivergence, neurotype]
      - [adhd, add, attention-deficit]
      - [tech, technology, technical]

    prefer:
      python: [py, python3]
      javascript: [js, ecmascript]

    The first tag in each group becomes the canonical form.
    """

    def __init__(self, vault_path: Path = None):
        """Initialize synonym configuration.

        Args:
            vault_path: Path to the vault root directory (optional)
        """
        self.vault_path = vault_path
        self.synonym_groups: List[List[str]] = []
        self.canonical_map: Dict[str, str] = {}  # tag → canonical form

        if vault_path:
            self.config_file = vault_path / '.tagex' / 'synonyms.yaml'
            if self.config_file.exists():
                self.load()

    def _add_synonym_group(self, group: List[str]) -> None:
        """Add a synonym group to internal structures.

        Args:
            group: List of tags where first is canonical

        Raises:
            ValueError: If a tag already exists in another group
        """
        if len(group) < 2:
            return

        canonical = group[0]

        # Validate: check for tags that already have a different canonical
        for tag in group:
            existing_canonical = self.canonical_map.get(tag)
            if existing_canonical and existing_canonical != canonical:
                raise ValueError(
                    f"Conflicting synonym definition: '{tag}' is already defined "
                    f"with canonical '{existing_canonical}', cannot also use '{canonical}'"
                )

        # Add the group
        self.synonym_groups.append(group)
        for tag in group:
            self.canonical_map[tag] = canonical

    def load(self) -> None:
        """Load synonym configuration from YAML file.

        Raises:
            yaml.YAMLError: If the YAML file is malformed
            ValueError: If conflicting synonym definitions are found
        """
        with open(self.config_file) as f:
            config = yaml.safe_load(f)

        if not config:
            return

        # Process synonym groups
        if 'synonyms' in config:
            for group in config['synonyms']:
                self._add_synonym_group(group)

        # Process prefer mappings
        if 'prefer' in config:
            for canonical, variants in config['prefer'].items():
                self._add_synonym_group([canonical] + variants)

        # Process top-level canonical: [variants] format
        # (for backward compatibility and simpler format)
        for key, value in config.items():
            if key not in ('synonyms', 'prefer') and isinstance(value, list):
                self._add_synonym_group([key] + value)

    def get_canonical(self, tag: str) -> str:
        """Get canonical form of a tag.

        Args:
            tag: The tag to look up

        Returns:
            The canonical form, or the tag itself if not in any synonym group
        """
        return self.canonical_map.get(tag, tag)

    def get_synonyms(self, tag: str) -> Set[str]:
        """Get all synonyms for a tag (excluding the tag itself).

        Args:
            tag: The tag to find synonyms for

        Returns:
            Set of synonym tags
        """
        canonical = self.get_canonical(tag)
        for group in self.synonym_groups:
            if canonical in group:
                return set(group) - {tag}
        return set()

    def get_all_in_group(self, tag: str) -> Set[str]:
        """Get all tags in the same synonym group (including the tag itself).

        Args:
            tag: The tag to find group members for

        Returns:
            Set of all tags in the group, or just the tag if not in any group
        """
        canonical = self.get_canonical(tag)
        for group in self.synonym_groups:
            if canonical in group:
                return set(group)
        return {tag}

    def add_synonym_group(self, tags: List[str]) -> None:
        """Add a new synonym group and save to file.

        Args:
            tags: List of synonym tags (first becomes canonical)
        """
        if len(tags) > 1:
            canonical = tags[0]
            self.synonym_groups.append(tags)
            for tag in tags:
                self.canonical_map[tag] = canonical
            self.save()

    def save(self) -> None:
        """Save synonym configuration to YAML file."""
        # Ensure .tagex directory exists
        self.config_file.parent.mkdir(exist_ok=True)

        config = {'synonyms': self.synonym_groups}
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def has_synonyms(self) -> bool:
        """Check if any synonym groups are configured.

        Returns:
            True if at least one synonym group exists
        """
        return len(self.synonym_groups) > 0

    def get_all_groups(self) -> List[List[str]]:
        """Get all synonym groups.

        Returns:
            List of synonym groups (each group is a list of tags)
        """
        return self.synonym_groups.copy()

    def remove_group(self, canonical: str) -> bool:
        """Remove a synonym group by its canonical tag.

        Args:
            canonical: The canonical tag of the group to remove

        Returns:
            True if a group was removed, False otherwise
        """
        for i, group in enumerate(self.synonym_groups):
            if group[0] == canonical:
                # Remove from groups
                removed_group = self.synonym_groups.pop(i)
                # Remove from canonical map
                for tag in removed_group:
                    self.canonical_map.pop(tag, None)
                self.save()
                return True
        return False
