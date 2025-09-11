#!/usr/bin/env python3
"""
Tag migration script based on co-occurrence analysis.
Creates hierarchical tag structure and consolidates similar tags.
"""
import json
import os
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
import argparse


# Tag migration mappings based on co-occurrence analysis
TAG_MAPPINGS = {
    # Personal content hierarchy
    "notebook": "personal/notebook",
    "fragments": "personal/fragments", 
    "daily": "personal/daily",
    "dictated": "personal/dictated",
    "poem": "personal/poetry",
    "sharesheet": "personal/tools",
    
    # Reference content hierarchy  
    "clippings": "reference/clippings",
    "info": "reference/info",
    
    # Judaism/Religion hierarchy
    "judaism": "topics/judaism",
    "jewish": "topics/judaism",
    "religion": "topics/religion",
    "christianity": "topics/religion/christianity",
    "akedah": "topics/judaism/stories",
    "torah": "topics/judaism/torah",
    "weddings": "topics/judaism/lifecycle",
    
    # Family/Relationships hierarchy
    "fathers": "topics/family/fathers",
    "parenting": "topics/family/parenting",
    "family": "topics/family",
    "marriage": "topics/family/marriage",
    "relationships": "topics/family/relationships",
    
    # Technology hierarchy
    "llms": "tech/ai/llms",
    "ai": "tech/ai",
    "ai-generated": "tech/ai/generated",
    "claude": "tech/ai/claude",
    "claude-code": "tech/ai/claude",
    "gpt2": "tech/ai/gpt",
    "tech": "tech/general",
    "technology": "tech/general",
    "software": "tech/software",
    "software-development": "tech/software/development",
    "programming": "tech/software/programming",
    "development": "tech/software/development",
    "api": "tech/software/api",
    
    # Media hierarchy
    "culture": "media/culture",
    "film": "media/film",
    "films": "media/film",
    "movie": "media/film",
    "movies": "media/film",
    "tv": "media/tv",
    "television": "media/tv",
    "series": "media/tv/series",
    "book": "media/books",
    "books": "media/books",
    "novel": "media/books/fiction",
    "novels": "media/books/fiction",
    "fiction": "media/books/fiction",
    "reading": "media/books",
    "authors": "media/books/authors",
    
    # Writing hierarchy
    "writing": "creative/writing",
    "blogging": "creative/writing/blogging",
    "publish": "creative/writing/publishing",
    
    # Work/Professional hierarchy
    "workplace": "professional/workplace",
    "work": "professional/work",
    
    # Tools/Utilities hierarchy
    "tools": "tools/general",
    "obsidian": "tools/obsidian",
    "utilities": "tools/utilities",
}

# Tags to delete (overly specific or low-value)
DELETE_TAGS = {
    # Overly specific AI tags
    "gpt-4o-audio-via-the-new-websocket-realtime-api",
    "llm-prices-crashed-thanks-to-competition-and-increased-efficiency",
    "llms-need-better-criticism",
    "llms-somehow-got-even-harder-to-use",
    
    # Very specific technical tags
    "write-vs-insert",
    "writefloatbe", 
    "readfloatbe",
    "readuint32le",
    "readxx",
    
    # Overly specific descriptive tags
    "writing-about-things-i-ve-found",
    "knowledge-is-incredibly-unevenly-distributed",
    "this-is-truly-the-darkest-dumbest-timeline",
    
    # Technical noise tags
    "3/4_bit",
    "yaml-header-front-matter",
    "xml-mime-type",
}

# Context-aware mappings (apply different mappings based on file location)
CONTEXT_MAPPINGS = {
    "Daily/": {
        "notebook": "personal/daily-notes",
        "fragments": "personal/daily-fragments",
    },
    "Reference/": {
        "judaism": "reference/judaism",
        "culture": "reference/culture",
        "history": "reference/history",
    },
    "L/": {  # Personal notes directory
        "notebook": "personal/thoughts",
        "fragments": "personal/fragments",
    }
}


class TagMigrator:
    def __init__(self, vault_path: str, dry_run: bool = True):
        self.vault_path = Path(vault_path)
        self.dry_run = dry_run
        self.backup_dir = self.vault_path / "tag_migration_backup"
        self.migration_log = []
        self.stats = {
            "files_processed": 0,
            "tags_migrated": 0,
            "tags_deleted": 0,
            "errors": 0
        }
    
    def create_backup(self):
        """Create backup of vault before migration."""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"vault_backup_{timestamp}"
        
        print(f"Creating backup at: {backup_path}")
        shutil.copytree(self.vault_path, backup_path, 
                       ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
        
        return backup_path
    
    def get_context_mapping(self, file_path: str) -> Dict[str, str]:
        """Get context-specific tag mappings based on file location."""
        for context_dir, mappings in CONTEXT_MAPPINGS.items():
            if file_path.startswith(context_dir):
                return {**TAG_MAPPINGS, **mappings}
        return TAG_MAPPINGS
    
    def migrate_file_tags(self, file_path: Path) -> bool:
        """Migrate tags in a single file."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            relative_path = str(file_path.relative_to(self.vault_path))
            mappings = self.get_context_mapping(relative_path)
            
            # Extract and process frontmatter
            content = self._migrate_frontmatter_tags(content, mappings)
            
            # Extract and process inline tags
            content = self._migrate_inline_tags(content, mappings)
            
            # Write back if changed
            if content != original_content:
                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                self.migration_log.append({
                    "file": str(file_path),
                    "action": "migrated",
                    "changes": "tag migration applied"
                })
                self.stats["files_processed"] += 1
                return True
            
            return False
            
        except Exception as e:
            self.stats["errors"] += 1
            self.migration_log.append({
                "file": str(file_path),
                "action": "error",
                "error": str(e)
            })
            return False
    
    def _migrate_frontmatter_tags(self, content: str, mappings: Dict[str, str]) -> str:
        """Migrate tags in YAML frontmatter."""
        frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
        match = re.match(frontmatter_pattern, content, re.DOTALL)
        
        if not match:
            return content
        
        yaml_content = match.group(1)
        remaining_content = content[match.end():]
        
        # Process tag lines
        lines = yaml_content.split('\n')
        modified_lines = []
        
        for line in lines:
            if line.strip().startswith('tags:') or line.strip().startswith('tag:'):
                # Handle different YAML tag formats
                if ':' in line:
                    key, value = line.split(':', 1)
                    migrated_value = self._migrate_tag_value(value.strip(), mappings)
                    modified_lines.append(f"{key}: {migrated_value}")
                else:
                    modified_lines.append(line)
            elif line.strip().startswith('- ') and any(prev_line.strip().startswith(('tags:', 'tag:')) for prev_line in lines[max(0, len(modified_lines)-3):len(modified_lines)]):
                # Handle YAML array items
                tag_value = line.strip()[2:].strip()
                if tag_value:
                    migrated_tag = self._migrate_single_tag(tag_value, mappings)
                    if migrated_tag:
                        modified_lines.append(f"  - {migrated_tag}")
                    # Skip deleted tags
                else:
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        
        new_yaml = '\n'.join(modified_lines)
        return f"---\n{new_yaml}\n---\n{remaining_content}"
    
    def _migrate_inline_tags(self, content: str, mappings: Dict[str, str]) -> str:
        """Migrate inline #tags in content."""
        def replace_tag(match):
            tag = match.group(1)
            migrated_tag = self._migrate_single_tag(tag, mappings)
            if migrated_tag:
                return f"#{migrated_tag}"
            else:
                return ""  # Delete tag
        
        # Remove code blocks first to avoid processing tags in code
        content_without_code = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        content_without_code = re.sub(r'`[^`]*`', '', content_without_code)
        
        # Find and replace inline tags
        tag_pattern = r'#([a-zA-Z0-9][a-zA-Z0-9_\-\/]*)'
        migrated_content = re.sub(tag_pattern, replace_tag, content)
        
        return migrated_content
    
    def _migrate_tag_value(self, value: str, mappings: Dict[str, str]) -> str:
        """Migrate a tag value (could be single tag or array)."""
        if value.startswith('[') and value.endswith(']'):
            # Array format: [tag1, tag2, tag3]
            tag_list = value[1:-1].split(',')
            migrated_tags = []
            for tag in tag_list:
                tag = tag.strip().strip('"\'')
                migrated_tag = self._migrate_single_tag(tag, mappings)
                if migrated_tag:
                    migrated_tags.append(f'"{migrated_tag}"')
            return f"[{', '.join(migrated_tags)}]"
        else:
            # Single tag or comma-separated string
            if ',' in value:
                tags = [tag.strip().strip('"\'') for tag in value.split(',')]
                migrated_tags = []
                for tag in tags:
                    migrated_tag = self._migrate_single_tag(tag, mappings)
                    if migrated_tag:
                        migrated_tags.append(migrated_tag)
                return ', '.join(migrated_tags)
            else:
                # Single tag
                tag = value.strip().strip('"\'')
                migrated_tag = self._migrate_single_tag(tag, mappings)
                return f'"{migrated_tag}"' if migrated_tag else '""'
    
    def _migrate_single_tag(self, tag: str, mappings: Dict[str, str]) -> str:
        """Migrate a single tag."""
        # Normalize tag
        tag = tag.lower().strip()
        
        # Check if tag should be deleted
        if tag in DELETE_TAGS:
            self.stats["tags_deleted"] += 1
            return None
        
        # Check for direct mapping
        if tag in mappings:
            self.stats["tags_migrated"] += 1
            return mappings[tag]
        
        # Check for partial matches (for compound tags)
        for old_tag, new_tag in mappings.items():
            if old_tag in tag:
                self.stats["tags_migrated"] += 1
                return new_tag
        
        # Return original tag if no mapping found
        return tag
    
    def run_migration(self):
        """Run the complete migration process."""
        print(f"Starting tag migration for vault: {self.vault_path}")
        print(f"Dry run: {self.dry_run}")
        
        if not self.dry_run:
            self.create_backup()
        
        # Find all markdown files
        markdown_files = list(self.vault_path.rglob("*.md"))
        print(f"Found {len(markdown_files)} markdown files")
        
        # Process each file
        for file_path in markdown_files:
            if ".obsidian" in str(file_path):
                continue
            self.migrate_file_tags(file_path)
        
        # Generate report
        self._generate_report()
    
    def _generate_report(self):
        """Generate migration report."""
        print("\n" + "="*50)
        print("MIGRATION REPORT")
        print("="*50)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Tags migrated: {self.stats['tags_migrated']}")
        print(f"Tags deleted: {self.stats['tags_deleted']}")
        print(f"Errors: {self.stats['errors']}")
        
        if self.migration_log:
            print(f"\nDetailed log written to: tag_migration_log.json")
            with open("tag_migration_log.json", 'w') as f:
                json.dump(self.migration_log, f, indent=2)
        
        # Show sample mappings applied
        print(f"\nSample mappings that will be applied:")
        for old_tag, new_tag in list(TAG_MAPPINGS.items())[:10]:
            print(f"  {old_tag} → {new_tag}")
        print(f"  ... and {len(TAG_MAPPINGS) - 10} more mappings")
        
        print(f"\nTags to be deleted:")
        for tag in list(DELETE_TAGS)[:10]:
            print(f"  - {tag}")
        if len(DELETE_TAGS) > 10:
            print(f"  ... and {len(DELETE_TAGS) - 10} more")


def main():
    parser = argparse.ArgumentParser(description="Migrate tags based on co-occurrence analysis")
    parser.add_argument("vault_path", help="Path to Obsidian vault")
    parser.add_argument("--dry-run", action="store_true", default=True, 
                       help="Show what would be changed without making changes")
    parser.add_argument("--execute", action="store_true", 
                       help="Actually perform the migration (overrides dry-run)")
    
    args = parser.parse_args()
    
    # Default to dry run unless explicitly told to execute
    dry_run = not args.execute
    
    migrator = TagMigrator(args.vault_path, dry_run=dry_run)
    migrator.run_migration()


if __name__ == "__main__":
    main()