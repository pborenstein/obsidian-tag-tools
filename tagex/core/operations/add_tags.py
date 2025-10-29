#!/usr/bin/env python3
"""
Add tags operation - adds tags to notes' frontmatter.

This operation adds specified tags to notes, handling:
- Notes with no frontmatter (creates YAML block)
- Notes with frontmatter but no tags field (adds tags field)
- Notes with existing tags (appends without duplicates)
"""

from pathlib import Path
from typing import List, Dict, Any
import re
import yaml

from .tag_operations import TagOperationEngine
from ..parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter


class AddTagsOperation(TagOperationEngine):
    """Operation to add tags to specific notes."""

    def __init__(
        self,
        vault_path: str,
        file_tag_map: Dict[str, List[str]],
        dry_run: bool = False,
        tag_types: str = 'frontmatter',
        quiet: bool = False
    ):
        """
        Initialize add tags operation.

        Args:
            vault_path: Path to the Obsidian vault
            file_tag_map: Dictionary mapping file paths to lists of tags to add
            dry_run: If True, preview changes without modifying files
            tag_types: Tag types to process (only 'frontmatter' supported for adding)
            quiet: If True, suppress progress output
        """
        super().__init__(vault_path, dry_run, tag_types, quiet)
        self.file_tag_map = file_tag_map
        self.operation_log.update({
            "operation_type": "add_tags",
            "file_count": len(file_tag_map)
        })

        # Validate that tag_types is frontmatter (can't add inline tags)
        if tag_types != 'frontmatter':
            raise ValueError("AddTagsOperation only supports tag_types='frontmatter'")

    def transform_tags(self, content: str, file_path: str) -> str:
        """
        Add tags to the note's frontmatter.

        Args:
            content: Original file content
            file_path: Relative path to file (from vault)

        Returns:
            Modified content with added tags
        """
        # Get tags to add for this file
        tags_to_add = self.file_tag_map.get(file_path)
        if not tags_to_add:
            return content  # No tags to add for this file

        # Parse current frontmatter
        frontmatter, body = extract_frontmatter(content)
        current_tags = extract_tags_from_frontmatter(frontmatter) if frontmatter else []
        current_tags_lower = {tag.lower() for tag in current_tags}

        # Filter out tags that already exist (case-insensitive)
        new_tags = [tag for tag in tags_to_add if tag.lower() not in current_tags_lower]

        if not new_tags:
            # All tags already exist
            return content

        # Update tag count
        self.operation_log["stats"]["tags_modified"] += len(new_tags)

        # Handle different frontmatter scenarios
        if frontmatter is None:
            # No frontmatter - create new one
            return self._create_frontmatter(content, new_tags)
        else:
            # Frontmatter exists - update it
            return self._update_frontmatter(content, frontmatter, current_tags, new_tags)

    def _create_frontmatter(self, content: str, tags: List[str]) -> str:
        """
        Create new frontmatter with tags at the start of the file.

        Args:
            content: Original file content
            tags: Tags to add

        Returns:
            Content with new frontmatter prepended
        """
        # Create frontmatter YAML
        frontmatter_content = "tags: [" + ", ".join(tags) + "]"
        new_frontmatter = f"---\n{frontmatter_content}\n---\n"

        # Prepend to content
        return new_frontmatter + content

    def _update_frontmatter(
        self,
        content: str,
        frontmatter: Dict[str, Any],
        current_tags: List[str],
        new_tags: List[str]
    ) -> str:
        """
        Update existing frontmatter to add new tags.

        Args:
            content: Original file content
            frontmatter: Parsed frontmatter dictionary
            current_tags: Current tags in frontmatter
            new_tags: New tags to add

        Returns:
            Content with updated frontmatter
        """
        # Extract frontmatter section
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---(\s*\n)', content, re.DOTALL)
        if not frontmatter_match:
            # Shouldn't happen since we already parsed frontmatter
            return self._create_frontmatter(content, new_tags)

        yaml_content = frontmatter_match.group(1)
        original_ending = frontmatter_match.group(2)
        body = content[frontmatter_match.end():]

        if current_tags:
            # Tags field exists - append new tags
            updated_yaml = self._append_to_tags_field(yaml_content, new_tags)
        else:
            # No tags field - add it
            updated_yaml = self._add_tags_field(yaml_content, new_tags)

        # Reconstruct file
        return f"---\n{updated_yaml}\n---{original_ending}{body}"

    def _append_to_tags_field(self, yaml_content: str, new_tags: List[str]) -> str:
        """
        Append tags to existing tags field in YAML.

        Args:
            yaml_content: Current YAML content
            new_tags: Tags to append

        Returns:
            Updated YAML content
        """
        lines = yaml_content.split('\n')
        updated_lines = []
        i = 0
        tags_field_found = False

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check if this is the tags field
            if stripped.startswith('tags:') or stripped.startswith('tag:'):
                # Detect duplicate tags: fields (invalid YAML)
                if tags_field_found:
                    # Skip duplicate tags: field - don't copy it
                    # If it has values, we need to skip those too
                    value_part = line.split(':', 1)[1].strip() if len(line.split(':', 1)) > 1 else ''
                    if not value_part:
                        # Multi-line format - skip array items
                        i += 1
                        while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip() == ''):
                            i += 1
                        i -= 1  # Back up since we'll increment at end of loop
                    # If inline format, just skip the line (which happens by not adding to updated_lines)
                else:
                    # First tags: field - update it
                    tags_field_found = True
                    key_part = line.split(':', 1)[0] + ':'
                    value_part = line.split(':', 1)[1].strip() if len(line.split(':', 1)) > 1 else ''
                    indent = line[:len(line) - len(line.lstrip())]

                    if value_part:
                        # Inline format: tags: [tag1, tag2] or tags: tag1
                        if value_part.startswith('[') and value_part.endswith(']'):
                            # Array format - append to array
                            inner = value_part[1:-1]
                            existing_tags = [t.strip().strip('"\'') for t in inner.split(',') if t.strip()]
                            all_tags = existing_tags + new_tags
                            updated_lines.append(f"{indent}{key_part} [{', '.join(all_tags)}]")
                        else:
                            # Convert single tag to array with new tags
                            existing_tag = value_part.strip().strip('"\'')
                            all_tags = [existing_tag] + new_tags
                            updated_lines.append(f"{indent}{key_part} [{', '.join(all_tags)}]")
                    else:
                        # Multi-line array format
                        updated_lines.append(line)  # Keep the "tags:" line

                        # Copy existing array items
                        i += 1
                        while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip() == ''):
                            updated_lines.append(lines[i])
                            i += 1

                        # Add new tags as array items
                        array_indent = indent + "  "
                        for tag in new_tags:
                            updated_lines.append(f"{array_indent}- {tag}")

                        i -= 1  # Back up since we'll increment at end of loop
            else:
                updated_lines.append(line)

            i += 1

        return '\n'.join(updated_lines)

    def _add_tags_field(self, yaml_content: str, tags: List[str]) -> str:
        """
        Add tags field to YAML that doesn't have one.

        Also handles removing duplicate tags: fields if they exist.

        Args:
            yaml_content: Current YAML content
            tags: Tags to add

        Returns:
            Updated YAML content with tags field
        """
        # Check for and remove any existing duplicate tags: fields
        # (This shouldn't normally happen, but handles edge cases)
        lines = yaml_content.split('\n')
        filtered_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip any existing tags: or tag: fields (duplicates)
            if stripped.startswith('tags:') or stripped.startswith('tag:'):
                value_part = line.split(':', 1)[1].strip() if len(line.split(':', 1)) > 1 else ''
                if not value_part:
                    # Multi-line format - skip array items
                    i += 1
                    while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip() == ''):
                        i += 1
                    i -= 1  # Back up since we'll increment at end of loop
                # If inline format, just skip the line
            else:
                filtered_lines.append(line)

            i += 1

        # Add tags field at the end of YAML
        tags_line = f"tags: [{', '.join(tags)}]"

        cleaned_yaml = '\n'.join(filtered_lines)
        if cleaned_yaml.strip():
            # Existing YAML - append tags field
            return f"{cleaned_yaml}\n{tags_line}"
        else:
            # Empty YAML - just add tags
            return tags_line

    def get_file_modifications(self, original: str, modified: str) -> List[Dict]:
        """Get specific tag addition modifications."""
        # Extract the file path from current context
        # (This is called from process_file_tags which has the relative path)
        return [{
            "type": "tags_added",
            "added_count": self.operation_log["stats"]["tags_modified"]
        }]

    def get_operation_log_name(self) -> str:
        """Get standardized operation name for log files."""
        return "tag-add-op"

    def run_operation(self):
        """Execute the add tags operation on specific files only."""
        if not self.quiet:
            print(f"Starting {self.operation_log['operation']} operation on vault: {self.vault_path}")
            print(f"Dry run: {self.dry_run}")
            print(f"Files to process: {len(self.file_tag_map)}")

        # Process only the files in file_tag_map
        for relative_path in self.file_tag_map.keys():
            file_path = self.vault_path / relative_path
            if file_path.exists():
                self.process_file_tags(file_path)
            else:
                if not self.quiet:
                    print(f"Warning: File not found: {relative_path}")
                self.operation_log["stats"]["errors"] += 1

        # Save operation log (only if not quiet)
        if not self.quiet:
            self.save_operation_log()

        # Generate report
        if not self.quiet:
            self.generate_report()

        # Return operation results
        return self.operation_log
