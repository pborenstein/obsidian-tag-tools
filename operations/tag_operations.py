#!/usr/bin/env python3
"""
Tag operation engine for modifying tags across Obsidian vaults.
Provides base functionality for rename, merge, apply, and undo operations.
"""
import json
import os
import re
import shutil
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional, Any
from abc import ABC, abstractmethod

from parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
from parsers.inline_parser import extract_inline_tags


class TagOperationEngine(ABC):
    """Base class for all tag operations with backup, logging, and reversibility."""
    
    def __init__(self, vault_path: str, dry_run: bool = False):
        self.vault_path = Path(vault_path)
        self.dry_run = dry_run
        self.operation_log = {
            "operation": self.__class__.__name__.lower(),
            "timestamp": datetime.now().isoformat(),
            "vault_path": str(self.vault_path),
            "dry_run": self.dry_run,
            "changes": [],
            "stats": {
                "files_processed": 0,
                "files_modified": 0,
                "tags_modified": 0,
                "errors": 0
            }
        }
    
    
    def calculate_file_hash(self, content: str) -> str:
        """Calculate hash of file content for integrity checking."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def process_file_tags(self, file_path: Path) -> bool:
        """Process tags in a single file. Returns True if file was modified."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            before_hash = self.calculate_file_hash(original_content)
            relative_path = str(file_path.relative_to(self.vault_path))
            
            # Apply tag transformations
            modified_content = self.transform_tags(original_content, relative_path)
            
            # Check if content changed
            if modified_content != original_content:
                after_hash = self.calculate_file_hash(modified_content)
                
                # Write back if not dry run
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)
                
                # Log the change
                self.operation_log["changes"].append({
                    "file": relative_path,
                    "before_hash": before_hash,
                    "after_hash": after_hash,
                    "modifications": self.get_file_modifications(original_content, modified_content)
                })
                
                self.operation_log["stats"]["files_modified"] += 1
                return True
            
            return False
            
        except Exception as e:
            self.operation_log["stats"]["errors"] += 1
            self.operation_log["changes"].append({
                "file": relative_path,
                "error": str(e)
            })
            print(f"Error processing {file_path}: {e}")
            return False
        finally:
            self.operation_log["stats"]["files_processed"] += 1
    
    @abstractmethod
    def transform_tags(self, content: str, file_path: str) -> str:
        """Transform tags in file content. Implemented by subclasses."""
        pass
    
    @abstractmethod
    def get_file_modifications(self, original: str, modified: str) -> List[Dict]:
        """Get list of specific modifications made to file."""
        pass
    
    @abstractmethod
    def get_operation_log_name(self) -> str:
        """Get standardized operation name for log files."""
        pass
    
    def file_contains_tag(self, content: str, target_tag: str) -> bool:
        """Check if file contains the target tag using proven parsers."""
        target_tag_lower = target_tag.lower().strip()
        
        # Use proven frontmatter parser
        frontmatter, remaining_content = extract_frontmatter(content)
        if frontmatter:
            frontmatter_tags = extract_tags_from_frontmatter(frontmatter)
            for tag in frontmatter_tags:
                if tag.lower().strip() == target_tag_lower:
                    return True
        
        # Use proven inline parser
        inline_tags = extract_inline_tags(remaining_content)
        for tag in inline_tags:
            if tag.lower().strip() == target_tag_lower:
                return True
        
        return False
    
    def transform_file_tags(self, content: str, tag_transform_func) -> str:
        """Transform tags in file content using proven parsers."""
        # Parse frontmatter and content
        frontmatter, remaining_content = extract_frontmatter(content)
        
        # Transform frontmatter tags if present, preserving original YAML structure
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---(\s*\n)', content, re.DOTALL)
        if frontmatter and frontmatter_match:
            original_yaml = frontmatter_match.group(1)
            original_ending = frontmatter_match.group(2)  # Preserve original spacing after ---
            transformed_yaml = self._transform_yaml_text(original_yaml, tag_transform_func)
            frontmatter_section = f"---\n{transformed_yaml}\n---{original_ending}"
        elif frontmatter_match:
            # Frontmatter exists but couldn't parse - preserve original
            frontmatter_section = frontmatter_match.group(0)
        else:
            frontmatter_section = ""
        
        # Transform inline tags in remaining content
        transformed_content = self._transform_inline_tags(remaining_content, tag_transform_func)
        
        return frontmatter_section + transformed_content
    
    def _transform_yaml_text(self, yaml_text: str, tag_transform_func) -> str:
        """Transform only tag lines in YAML text, preserving all other formatting."""
        lines = yaml_text.split('\n')
        transformed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check if this is a tag field line
            if stripped.startswith('tags:') or stripped.startswith('tag:'):
                # Extract the key and value parts
                if ':' in line:
                    key_part = line.split(':', 1)[0] + ':'
                    value_part = line.split(':', 1)[1].strip() if len(line.split(':', 1)) > 1 else ''
                    
                    if value_part:
                        # Single line tag format: "tags: [tag1, tag2]" or "tags: single-tag"
                        transformed_value = self._transform_yaml_tag_value(value_part, tag_transform_func)
                        if transformed_value:
                            indent = line[:len(line) - len(line.lstrip())]
                            transformed_lines.append(f"{indent}{key_part} {transformed_value}")
                        else:
                            # Skip empty tag field
                            pass
                    else:
                        # Multi-line array format starts here
                        indent = line[:len(line) - len(line.lstrip())]
                        transformed_lines.append(line)  # Keep the "tags:" line
                        
                        # Process following array items
                        i += 1
                        while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip() == ''):
                            item_line = lines[i]
                            if item_line.strip().startswith('- '):
                                tag_value = item_line.strip()[2:].strip()
                                if tag_value:
                                    transformed_tag = tag_transform_func(tag_value.strip('"\''))
                                    if transformed_tag:
                                        item_indent = item_line[:len(item_line) - len(item_line.lstrip())]
                                        transformed_lines.append(f"{item_indent}- {transformed_tag}")
                            else:
                                # Empty line in array, preserve it
                                transformed_lines.append(item_line)
                            i += 1
                        i -= 1  # Back up one since we'll increment at end of loop
                else:
                    # Malformed tag line, preserve as-is
                    transformed_lines.append(line)
            else:
                # Not a tag line, preserve as-is
                transformed_lines.append(line)
            
            i += 1
        
        return '\n'.join(transformed_lines)
    
    def _transform_yaml_tag_value(self, value: str, tag_transform_func) -> str:
        """Transform a YAML tag value while preserving format."""
        value = value.strip()
        
        if value.startswith('[') and value.endswith(']'):
            # Array format: [tag1, tag2, tag3]
            inner = value[1:-1]
            if not inner.strip():
                return None  # Empty array
            
            tags = []
            for tag in inner.split(','):
                tag = tag.strip().strip('"\'')
                if tag:
                    transformed = tag_transform_func(tag)
                    if transformed:
                        # Preserve original quoting style if possible
                        if '"' in inner:
                            tags.append(f'"{transformed}"')
                        else:
                            tags.append(transformed)
            
            return f"[{', '.join(tags)}]" if tags else None
            
        elif ',' in value:
            # Comma-separated format: tag1, tag2, tag3
            tags = []
            for tag in value.split(','):
                tag = tag.strip().strip('"\'')
                if tag:
                    transformed = tag_transform_func(tag)
                    if transformed:
                        tags.append(transformed)
            return ', '.join(tags) if tags else None
            
        else:
            # Single tag
            tag = value.strip().strip('"\'')
            return tag_transform_func(tag) if tag else None
    
    def _transform_inline_tags(self, content: str, tag_transform_func) -> str:
        """Transform inline tags in content while preserving code blocks."""
        # We need to preserve code blocks, so we'll use a placeholder approach
        code_blocks = []
        
        # Store fenced code blocks
        def store_fenced_block(match):
            code_blocks.append(match.group(0))
            return f"__FENCED_BLOCK_{len(code_blocks)-1}__"
        
        content = re.sub(r'```.*?```', store_fenced_block, content, flags=re.DOTALL)
        
        # Store inline code
        def store_inline_code(match):
            code_blocks.append(match.group(0))
            return f"__INLINE_CODE_{len(code_blocks)-1}__"
        
        content = re.sub(r'`[^`]*`', store_inline_code, content)
        
        # Transform tags in the content with placeholders
        def replace_tag(match):
            tag = match.group(1)
            transformed_tag = tag_transform_func(tag)
            if transformed_tag is None:
                return ""  # Delete tag
            elif transformed_tag != tag:
                return f"#{transformed_tag}"
            else:
                return match.group(0)  # No change
        
        # Use the same pattern as the proven inline parser
        tag_pattern = r'(?:^|(?<=\s))#([a-zA-Z0-9][a-zA-Z0-9_\-\/]*)'
        content = re.sub(tag_pattern, replace_tag, content)
        
        # Restore code blocks
        def restore_fenced_block(match):
            index = int(match.group(1))
            return code_blocks[index] if index < len(code_blocks) else match.group(0)
        
        def restore_inline_code(match):
            index = int(match.group(1))
            return code_blocks[index] if index < len(code_blocks) else match.group(0)
        
        content = re.sub(r'__FENCED_BLOCK_(\d+)__', restore_fenced_block, content)
        content = re.sub(r'__INLINE_CODE_(\d+)__', restore_inline_code, content)
        
        return content
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in vault."""
        markdown_files = []
        for file_path in self.vault_path.rglob("*.md"):
            if ".obsidian" not in str(file_path):
                markdown_files.append(file_path)
        return markdown_files
    
    def run_operation(self):
        """Execute the complete operation."""
        print(f"Starting {self.operation_log['operation']} operation on vault: {self.vault_path}")
        print(f"Dry run: {self.dry_run}")
        
        
        # Find and process files
        markdown_files = self.find_markdown_files()
        print(f"Found {len(markdown_files)} markdown files")
        
        for file_path in markdown_files:
            self.process_file_tags(file_path)
        
        # Save operation log
        self.save_operation_log()
        
        # Generate report
        self.generate_report()
        
        # Return operation results for testing/inspection
        return self.operation_log
    
    def save_operation_log(self):
        """Save detailed operation log outside vault."""
        log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Use standardized operation name format
        operation_name = self.get_operation_log_name()
        log_filename = f"{operation_name}_{log_timestamp}.json"
        
        # Save in current working directory, not in vault
        log_path = Path.cwd() / log_filename
        
        with open(log_path, 'w') as f:
            json.dump(self.operation_log, f, indent=2, ensure_ascii=False)
        
        print(f"Operation log saved: {log_filename}")
        return log_path
    
    def generate_report(self):
        """Generate operation summary report."""
        stats = self.operation_log["stats"]
        print("\n" + "="*50)
        print(f"{self.operation_log['operation'].upper()} OPERATION REPORT")
        print("="*50)
        print(f"Files processed: {stats['files_processed']}")
        print(f"Files modified: {stats['files_modified']}")
        print(f"Tags modified: {stats['tags_modified']}")
        print(f"Errors: {stats['errors']}")
        
        if self.dry_run:
            print("\nThis was a dry run - no files were actually modified")
            print("Run without --dry-run to apply changes")


class RenameOperation(TagOperationEngine):
    """Operation to rename a single tag across all files."""
    
    def __init__(self, vault_path: str, old_tag: str, new_tag: str, dry_run: bool = False):
        super().__init__(vault_path, dry_run)
        self.old_tag = old_tag.lower().strip()
        self.new_tag = new_tag.strip()
        self.operation_log.update({
            "operation_type": "rename",
            "old_tag": self.old_tag,
            "new_tag": self.new_tag
        })
    
    def transform_tags(self, content: str, file_path: str) -> str:
        """Rename old_tag to new_tag in content, but only if file contains the tag."""
        # First check if this file actually contains the target tag
        if not self.file_contains_tag(content, self.old_tag):
            return content  # No changes needed
        
        def tag_transform(tag: str) -> str:
            if tag.lower().strip() == self.old_tag:
                self.operation_log["stats"]["tags_modified"] += 1
                return self.new_tag
            return tag
        
        # Use the proven parser-based transformation
        return self.transform_file_tags(content, tag_transform)
    
    def get_file_modifications(self, original: str, modified: str) -> List[Dict]:
        """Get specific tag rename modifications."""
        return [{
            "type": "tag_rename",
            "from": self.old_tag,
            "to": self.new_tag
        }]
    
    def get_operation_log_name(self) -> str:
        """Get standardized operation name for log files."""
        return "tag-rename-op"


class MergeOperation(TagOperationEngine):
    """Operation to merge multiple tags into a single tag."""
    
    def __init__(self, vault_path: str, source_tags: List[str], target_tag: str, dry_run: bool = False):
        super().__init__(vault_path, dry_run)
        self.source_tags = [tag.lower().strip() for tag in source_tags]
        self.target_tag = target_tag.strip()
        self.operation_log.update({
            "operation_type": "merge",
            "source_tags": self.source_tags,
            "target_tag": self.target_tag
        })
    
    def transform_tags(self, content: str, file_path: str) -> str:
        """Merge source tags into target tag."""
        def tag_transform(tag: str) -> str:
            if tag.lower().strip() in self.source_tags:
                self.operation_log["stats"]["tags_modified"] += 1
                return self.target_tag
            return tag
        
        # Use the proven parser-based transformation
        return self.transform_file_tags(content, tag_transform)
    
    def get_file_modifications(self, original: str, modified: str) -> List[Dict]:
        """Get specific tag merge modifications."""
        return [{
            "type": "tag_merge",
            "sources": self.source_tags,
            "target": self.target_tag
        }]
    
    def get_operation_log_name(self) -> str:
        """Get standardized operation name for log files."""
        return "tag-merge-op"


class DeleteOperation(TagOperationEngine):
    """Operation to delete tags entirely from all files."""

    def __init__(self, vault_path: str, tags_to_delete: List[str], dry_run: bool = False):
        super().__init__(vault_path, dry_run)
        self.tags_to_delete = [tag.lower().strip() for tag in tags_to_delete]
        self.inline_deletions = 0
        self.frontmatter_deletions = 0
        self.operation_log.update({
            "operation_type": "delete",
            "tags_to_delete": self.tags_to_delete,
            "warnings": []
        })

    def transform_tags(self, content: str, file_path: str) -> str:
        """Delete specified tags from content."""
        # Track what types of tags we're deleting for warnings
        frontmatter, remaining_content = extract_frontmatter(content)
        has_frontmatter_tags = False
        has_inline_tags = False

        # Check if file contains target tags in different locations
        if frontmatter:
            frontmatter_tags = extract_tags_from_frontmatter(frontmatter)
            for tag in frontmatter_tags:
                if tag.lower().strip() in self.tags_to_delete:
                    has_frontmatter_tags = True
                    break

        inline_tags = extract_inline_tags(remaining_content)
        for tag in inline_tags:
            if tag.lower().strip() in self.tags_to_delete:
                has_inline_tags = True
                break

        # Issue warnings for inline tag deletions
        if has_inline_tags:
            self.inline_deletions += 1
            warning_msg = (
                f"WARNING: Deleting inline tags from '{file_path}'. "
                f"This removes tags from content text, which may affect readability."
            )
            print(f"WARNING: {warning_msg}")
            self.operation_log["warnings"].append({
                "file": file_path,
                "type": "inline_deletion",
                "message": warning_msg
            })

        if has_frontmatter_tags:
            self.frontmatter_deletions += 1

        # Perform the deletion using tag transform function
        def tag_transform(tag: str) -> Optional[str]:
            if tag.lower().strip() in self.tags_to_delete:
                self.operation_log["stats"]["tags_modified"] += 1
                return None  # Return None to delete the tag
            return tag

        # Use the proven parser-based transformation
        return self.transform_file_tags(content, tag_transform)

    def get_file_modifications(self, original: str, modified: str) -> List[Dict]:
        """Get specific tag deletion modifications."""
        return [{
            "type": "tag_deletion",
            "deleted_tags": self.tags_to_delete
        }]

    def get_operation_log_name(self) -> str:
        """Get standardized operation name for log files."""
        return "tag-delete-op"

    def generate_report(self):
        """Generate operation summary report with deletion-specific warnings."""
        # Call parent report first
        super().generate_report()

        # Add deletion-specific information
        print(f"\nDELETION DETAILS:")
        print(f"Files with frontmatter tag deletions: {self.frontmatter_deletions}")
        print(f"Files with inline tag deletions: {self.inline_deletions}")

        if self.inline_deletions > 0:
            print(f"\nWARNING: {self.inline_deletions} files had inline tags deleted.")
            print("   Inline tag deletion removes tags from content text, which may affect")
            print("   readability and context. Consider reviewing these files manually.")

        if len(self.operation_log["warnings"]) > 0:
            print(f"\n{len(self.operation_log['warnings'])} warnings logged. Check operation log for details.")

    def _transform_yaml_tag_value(self, value: str, tag_transform_func) -> Optional[str]:
        """Transform a YAML tag value, handling None returns for deletion."""
        value = value.strip()

        if value.startswith('[') and value.endswith(']'):
            # Array format: [tag1, tag2, tag3]
            inner = value[1:-1]
            if not inner.strip():
                return None  # Empty array

            tags = []
            for tag in inner.split(','):
                tag = tag.strip().strip('"\'')
                if tag:
                    transformed = tag_transform_func(tag)
                    if transformed is not None:  # Keep tags that aren't deleted
                        # Preserve original quoting style if possible
                        if '"' in inner:
                            tags.append(f'"{transformed}"')
                        else:
                            tags.append(transformed)

            return f"[{', '.join(tags)}]" if tags else None

        elif ',' in value:
            # Comma-separated format: tag1, tag2, tag3
            tags = []
            for tag in value.split(','):
                tag = tag.strip().strip('"\'')
                if tag:
                    transformed = tag_transform_func(tag)
                    if transformed is not None:  # Keep tags that aren't deleted
                        tags.append(transformed)
            return ', '.join(tags) if tags else None

        else:
            # Single tag
            tag = value.strip().strip('"\'')
            return tag_transform_func(tag) if tag else None



