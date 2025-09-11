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
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from abc import ABC, abstractmethod


class TagOperationEngine(ABC):
    """Base class for all tag operations with backup, logging, and reversibility."""
    
    def __init__(self, vault_path: str, dry_run: bool = True):
        self.vault_path = Path(vault_path)
        self.dry_run = dry_run
        self.backup_dir = self.vault_path / "tagex_backups"
        self.operation_log = {
            "operation": self.__class__.__name__.lower(),
            "timestamp": datetime.now().isoformat(),
            "vault_path": str(self.vault_path),
            "dry_run": self.dry_run,
            "backup_path": None,
            "changes": [],
            "stats": {
                "files_processed": 0,
                "files_modified": 0,
                "tags_modified": 0,
                "errors": 0
            }
        }
    
    def create_backup(self) -> Optional[Path]:
        """Create timestamped backup of vault before operation."""
        if self.dry_run:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        if self.backup_dir.exists():
            # Keep only last 5 backups
            backups = sorted([d for d in self.backup_dir.iterdir() if d.is_dir()])
            if len(backups) >= 5:
                for old_backup in backups[:-4]:
                    shutil.rmtree(old_backup)
        
        print(f"Creating backup at: {backup_path}")
        shutil.copytree(self.vault_path, backup_path, 
                       ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'tagex_backups'))
        
        self.operation_log["backup_path"] = str(backup_path)
        return backup_path
    
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
    
    def transform_frontmatter_tags(self, content: str, tag_transform_func) -> str:
        """Transform tags in YAML frontmatter using provided function."""
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if not match:
            return content
        
        yaml_content = match.group(1)
        remaining_content = content[match.end():]
        
        # Process tag lines
        lines = yaml_content.split('\n')
        modified_lines = []
        
        for i, line in enumerate(lines):
            if line.strip().startswith('tags:') or line.strip().startswith('tag:'):
                # Handle different YAML tag formats
                if ':' in line:
                    key, value = line.split(':', 1)
                    transformed_value = self._transform_tag_value(value.strip(), tag_transform_func)
                    modified_lines.append(f"{key}: {transformed_value}")
                else:
                    modified_lines.append(line)
            elif line.strip().startswith('- ') and self._is_tag_array_item(lines, i):
                # Handle YAML array items
                tag_value = line.strip()[2:].strip()
                if tag_value:
                    transformed_tag = tag_transform_func(tag_value.strip('"\''))
                    if transformed_tag:
                        modified_lines.append(f"  - {transformed_tag}")
                    # Skip deleted tags
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        new_yaml = '\n'.join(modified_lines)
        return f"---\n{new_yaml}\n---\n{remaining_content}"
    
    def transform_inline_tags(self, content: str, tag_transform_func) -> str:
        """Transform inline #tags in content using provided function."""
        def replace_tag(match):
            tag = match.group(1)
            transformed_tag = tag_transform_func(tag)
            if transformed_tag:
                return f"#{transformed_tag}"
            else:
                return ""  # Delete tag
        
        # Avoid processing tags in code blocks
        def preserve_code_blocks(text):
            # This is a simplified approach - we could make it more robust
            return re.sub(r'#([a-zA-Z0-9][a-zA-Z0-9_\-\/]*)', replace_tag, text)
        
        return preserve_code_blocks(content)
    
    def _transform_tag_value(self, value: str, tag_transform_func) -> str:
        """Transform a tag value (single tag, array, or comma-separated)."""
        if value.startswith('[') and value.endswith(']'):
            # Array format: [tag1, tag2, tag3]
            tag_list = value[1:-1].split(',')
            transformed_tags = []
            for tag in tag_list:
                tag = tag.strip().strip('"\'')
                transformed_tag = tag_transform_func(tag)
                if transformed_tag:
                    transformed_tags.append(f'"{transformed_tag}"')
            return f"[{', '.join(transformed_tags)}]"
        else:
            # Single tag or comma-separated string
            if ',' in value:
                tags = [tag.strip().strip('"\'') for tag in value.split(',')]
                transformed_tags = []
                for tag in tags:
                    transformed_tag = tag_transform_func(tag)
                    if transformed_tag:
                        transformed_tags.append(transformed_tag)
                return ', '.join(transformed_tags)
            else:
                # Single tag
                tag = value.strip().strip('"\'')
                transformed_tag = tag_transform_func(tag)
                return f'"{transformed_tag}"' if transformed_tag else '""'
    
    def _is_tag_array_item(self, lines: List[str], line_index: int) -> bool:
        """Check if a line is part of a tags array in YAML."""
        # Look back for tags: declaration
        for i in range(line_index - 1, max(0, line_index - 5), -1):
            if lines[i].strip().startswith(('tags:', 'tag:')):
                return True
        return False
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in vault."""
        markdown_files = []
        for file_path in self.vault_path.rglob("*.md"):
            if ".obsidian" not in str(file_path) and "tagex_backups" not in str(file_path):
                markdown_files.append(file_path)
        return markdown_files
    
    def run_operation(self):
        """Execute the complete operation."""
        print(f"Starting {self.operation_log['operation']} operation on vault: {self.vault_path}")
        print(f"Dry run: {self.dry_run}")
        
        # Create backup if not dry run
        if not self.dry_run:
            self.create_backup()
        
        # Find and process files
        markdown_files = self.find_markdown_files()
        print(f"Found {len(markdown_files)} markdown files")
        
        for file_path in markdown_files:
            self.process_file_tags(file_path)
        
        # Save operation log
        self.save_operation_log()
        
        # Generate report
        self.generate_report()
    
    def save_operation_log(self):
        """Save detailed operation log for undo capability."""
        log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{self.operation_log['operation']}_{log_timestamp}.json"
        log_path = self.vault_path / log_filename
        
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
    
    def __init__(self, vault_path: str, old_tag: str, new_tag: str, dry_run: bool = True):
        super().__init__(vault_path, dry_run)
        self.old_tag = old_tag.lower().strip()
        self.new_tag = new_tag.strip()
        self.operation_log.update({
            "operation_type": "rename",
            "old_tag": self.old_tag,
            "new_tag": self.new_tag
        })
    
    def transform_tags(self, content: str, file_path: str) -> str:
        """Rename old_tag to new_tag in content."""
        def tag_transform(tag: str) -> str:
            if tag.lower().strip() == self.old_tag:
                self.operation_log["stats"]["tags_modified"] += 1
                return self.new_tag
            return tag
        
        # Transform both frontmatter and inline tags
        content = self.transform_frontmatter_tags(content, tag_transform)
        content = self.transform_inline_tags(content, tag_transform)
        
        return content
    
    def get_file_modifications(self, original: str, modified: str) -> List[Dict]:
        """Get specific tag rename modifications."""
        return [{
            "type": "tag_rename",
            "from": self.old_tag,
            "to": self.new_tag
        }]


class MergeOperation(TagOperationEngine):
    """Operation to merge multiple tags into a single tag."""
    
    def __init__(self, vault_path: str, source_tags: List[str], target_tag: str, dry_run: bool = True):
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
        
        # Transform both frontmatter and inline tags
        content = self.transform_frontmatter_tags(content, tag_transform)
        content = self.transform_inline_tags(content, tag_transform)
        
        return content
    
    def get_file_modifications(self, original: str, modified: str) -> List[Dict]:
        """Get specific tag merge modifications."""
        return [{
            "type": "tag_merge",
            "sources": self.source_tags,
            "target": self.target_tag
        }]


class ApplyOperation(TagOperationEngine):
    """Operation to apply migration mappings from JSON file."""
    
    def __init__(self, vault_path: str, migration_file: str, dry_run: bool = True):
        super().__init__(vault_path, dry_run)
        self.migration_file = Path(migration_file)
        
        # Load migration mappings
        with open(self.migration_file, 'r') as f:
            migration_data = json.load(f)
        
        # Support both direct mappings and TagMigrator format
        if isinstance(migration_data, dict) and "TAG_MAPPINGS" in migration_data:
            self.mappings = migration_data["TAG_MAPPINGS"]
            self.delete_tags = set(migration_data.get("DELETE_TAGS", []))
        else:
            # Assume direct mapping format
            self.mappings = migration_data
            self.delete_tags = set()
        
        self.operation_log.update({
            "operation_type": "apply",
            "migration_file": str(self.migration_file),
            "mappings_count": len(self.mappings),
            "delete_count": len(self.delete_tags)
        })
    
    def transform_tags(self, content: str, file_path: str) -> str:
        """Apply migration mappings to tags."""
        def tag_transform(tag: str) -> str:
            tag_normalized = tag.lower().strip()
            
            # Check if tag should be deleted
            if tag_normalized in self.delete_tags:
                self.operation_log["stats"]["tags_modified"] += 1
                return None
            
            # Check for direct mapping
            if tag_normalized in self.mappings:
                self.operation_log["stats"]["tags_modified"] += 1
                return self.mappings[tag_normalized]
            
            # Check for partial matches
            for old_tag, new_tag in self.mappings.items():
                if old_tag in tag_normalized:
                    self.operation_log["stats"]["tags_modified"] += 1
                    return new_tag
            
            return tag
        
        # Transform both frontmatter and inline tags
        content = self.transform_frontmatter_tags(content, tag_transform)
        content = self.transform_inline_tags(content, tag_transform)
        
        return content
    
    def get_file_modifications(self, original: str, modified: str) -> List[Dict]:
        """Get migration application modifications."""
        return [{
            "type": "migration_apply",
            "migration_file": str(self.migration_file)
        }]


class UndoOperation:
    """Operation to undo a previous tag operation using its log file."""
    
    def __init__(self, vault_path: str, operation_log_file: str):
        self.vault_path = Path(vault_path)
        self.log_file = Path(operation_log_file)
        
        # Load operation log
        with open(self.log_file, 'r') as f:
            self.operation_log = json.load(f)
    
    def run_undo(self):
        """Restore vault from backup specified in operation log."""
        backup_path = self.operation_log.get("backup_path")
        
        if not backup_path:
            print("No backup path found in operation log - cannot undo")
            return False
        
        backup_path = Path(backup_path)
        if not backup_path.exists():
            print(f"Backup not found at: {backup_path}")
            return False
        
        print(f"Restoring vault from backup: {backup_path}")
        
        # Remove current vault contents (except backups)
        for item in self.vault_path.iterdir():
            if item.name == "tagex_backups":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        
        # Restore from backup
        for item in backup_path.iterdir():
            if item.is_dir():
                shutil.copytree(item, self.vault_path / item.name)
            else:
                shutil.copy2(item, self.vault_path / item.name)
        
        print("Vault restored successfully")
        print(f"Undid operation: {self.operation_log['operation']} from {self.operation_log['timestamp']}")
        
        return True