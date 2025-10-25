"""
Frontmatter parser for extracting tags from YAML frontmatter in markdown files.
"""
import re
from typing import List, Optional, Union, Tuple, Dict, Any
import yaml


def extract_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Extract YAML frontmatter from markdown content.

    Args:
        content: Full markdown file content

    Returns:
        Tuple of (frontmatter_dict, remaining_content)
    """
    # Match frontmatter pattern: --- at start, content, --- delimiter
    # Allow optional trailing content after closing ---
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*(?:\n|$)'
    match = re.match(frontmatter_pattern, content, re.DOTALL)
    
    if not match:
        return None, content
    
    yaml_content = match.group(1)
    remaining_content = content[match.end():]
    
    try:
        frontmatter = yaml.safe_load(yaml_content)
        return frontmatter, remaining_content
    except yaml.YAMLError:
        # Return None if YAML is malformed
        return None, content


def extract_tags_from_frontmatter(frontmatter: Optional[Dict[str, Any]]) -> List[str]:
    """
    Extract tags from frontmatter dictionary.

    Args:
        frontmatter: Parsed YAML frontmatter as dictionary

    Returns:
        List of tag strings
    """
    if not frontmatter:
        return []
    
    tags = []
    
    # Check both 'tags' and 'tag' fields (some users use singular)
    for field in ['tags', 'tag']:
        if field in frontmatter:
            tag_value = frontmatter[field]
            tags.extend(_parse_tag_value(tag_value))
    
    return tags


def _parse_tag_value(tag_value: Union[str, List[str], None]) -> List[str]:
    """
    Parse tag value from frontmatter into list of strings.

    Args:
        tag_value: Value from frontmatter (can be string, list, or None)

    Returns:
        List of tag strings
    """
    if tag_value is None:
        return []
    
    if isinstance(tag_value, list):
        # Handle array format: tags: [tag1, tag2, tag3]
        return [str(tag).strip() for tag in tag_value if tag]
    
    if isinstance(tag_value, str):
        # Handle string format: tags: "tag1, tag2, tag3"
        if ',' in tag_value:
            return [tag.strip() for tag in tag_value.split(',') if tag.strip()]
        else:
            # Single tag: tags: single-tag
            return [tag_value.strip()] if tag_value.strip() else []
    
    # Handle other types by converting to string
    return [str(tag_value).strip()] if str(tag_value).strip() else []