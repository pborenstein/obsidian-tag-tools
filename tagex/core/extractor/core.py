"""
Core tag extraction pipeline.
"""
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict
import logging

from ...utils.file_discovery import find_markdown_files, get_relative_path
from ..parsers.frontmatter_parser import extract_frontmatter, extract_tags_from_frontmatter
from ..parsers.inline_parser import extract_inline_tags
from ...utils.tag_normalizer import normalize_tags, deduplicate_tags, filter_valid_tags


logger = logging.getLogger(__name__)


class TagExtractor:
    """Main tag extraction engine."""
    
    def __init__(self, vault_path: str, exclude_patterns: Optional[Set[str]] = None, filter_tags: bool = True, tag_types: str = 'both'):
        """
        Initialize the tag extractor.

        Args:
            vault_path: Path to the Obsidian vault
            exclude_patterns: Additional patterns to exclude from scanning (merged with config)
            filter_tags: Whether to filter out invalid tags (default: True)
            tag_types: Which tag types to extract ('both', 'frontmatter', 'inline')
        """
        self.vault_path = Path(vault_path)
        self.exclude_patterns = exclude_patterns  # Will be merged with config in find_markdown_files
        self.filter_tags = filter_tags
        self.tag_types = tag_types
        self.file_count = 0
        self.error_count = 0
        
    def extract_tags(self) -> Dict[str, Dict]:
        """
        Extract all tags from the vault.
        
        Returns:
            Dictionary mapping tag names to tag data
        """
        logger.info(f"Starting tag extraction from vault: {self.vault_path}")
        
        # Find all markdown files
        markdown_files = find_markdown_files(str(self.vault_path), self.exclude_patterns)
        logger.info(f"Found {len(markdown_files)} markdown files")
        
        # Process each file
        tag_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "files": set()})
        
        for file_path in markdown_files:
            try:
                file_tags = self._process_file(file_path)
                if file_tags:
                    relative_path = get_relative_path(file_path, self.vault_path)
                    for tag in file_tags:
                        tag_data[tag]["count"] += 1
                        tag_data[tag]["files"].add(relative_path)
                self.file_count += 1

            except (UnicodeDecodeError, IOError, OSError, ValueError) as e:
                logger.error(f"Error processing file {file_path}: {e}")
                self.error_count += 1
                continue
            except Exception as e:
                logger.exception(f"Unexpected error processing {file_path}")
                self.error_count += 1
                continue
        
        logger.info(f"Processed {self.file_count} files, {self.error_count} errors")
        logger.info(f"Found {len(tag_data)} unique tags")
        
        return dict(tag_data)
    
    def _process_file(self, file_path: Path) -> List[str]:
        """
        Process a single markdown file to extract tags.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            List of normalized tags from the file
        """
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Extract frontmatter and remaining content
        frontmatter, markdown_content = extract_frontmatter(content)

        # Extract tags based on tag_types setting
        all_tags = []

        if self.tag_types in ('both', 'frontmatter'):
            frontmatter_tags = extract_tags_from_frontmatter(frontmatter) if frontmatter else []
            all_tags.extend(frontmatter_tags)

        if self.tag_types in ('both', 'inline'):
            inline_tags = extract_inline_tags(markdown_content)
            all_tags.extend(inline_tags)
        
        # Filter valid tags and normalize (if filtering enabled)
        if self.filter_tags:
            valid_tags = filter_valid_tags(all_tags)
            normalized_tags = normalize_tags(valid_tags)
        else:
            # Just normalize without filtering
            normalized_tags = normalize_tags(all_tags)
        
        return normalized_tags
    
    def get_statistics(self) -> Dict:
        """
        Get extraction statistics.
        
        Returns:
            Dictionary with extraction statistics
        """
        return {
            "files_processed": self.file_count,
            "errors": self.error_count,
            "vault_path": str(self.vault_path)
        }