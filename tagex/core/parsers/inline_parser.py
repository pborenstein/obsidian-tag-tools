"""
Inline tag parser for extracting #tags from markdown content.
"""
import re
from typing import List, Set


def extract_inline_tags(content: str) -> List[str]:
    """
    Extract inline tags from markdown content.
    
    Args:
        content: Markdown content (without frontmatter)
        
    Returns:
        List of inline tag strings (without # prefix)
    """
    # Remove code blocks before processing
    content_without_code = _remove_code_blocks(content)
    
    # Regex pattern for inline tags
    # Matches #tag, #nested/tag, #tag-with-dashes, including international characters
    # Pattern: word boundary, # followed by word char, then word chars, underscore, dash, or slash, ending with word char
    tag_pattern = r'(?:^|(?<=\s))#([\w](?:[\w_\-/]*[\w]|[\w]*))(?=\s|$|[^a-zA-Z0-9_\-/])'
    
    tags = []
    for match in re.finditer(tag_pattern, content_without_code):
        tag = match.group(1)
        tags.append(tag)
    
    return tags


def _remove_code_blocks(content: str) -> str:
    """
    Remove code blocks from content to avoid extracting tags from code.
    
    Args:
        content: Markdown content
        
    Returns:
        Content with code blocks removed
    """
    # Remove fenced code blocks (``` ... ```)
    fenced_code_pattern = r'```.*?```'
    content = re.sub(fenced_code_pattern, '', content, flags=re.DOTALL)
    
    # Remove inline code (` ... `)
    inline_code_pattern = r'`[^`]*`'
    content = re.sub(inline_code_pattern, '', content)
    
    # Remove HTML comments (<!-- ... -->)
    html_comment_pattern = r'<!--.*?-->'
    content = re.sub(html_comment_pattern, '', content, flags=re.DOTALL)
    
    return content


def is_valid_tag(tag: str) -> bool:
    """
    Validate if a tag string is valid according to Obsidian rules.
    
    Args:
        tag: Tag string to validate
        
    Returns:
        True if tag is valid, False otherwise
    """
    if not tag:
        return False
    
    # Must start with alphanumeric character
    if not tag[0].isalnum():
        return False
    
    # Can only contain alphanumeric, underscore, dash, and slash
    valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/')
    if not all(c in valid_chars for c in tag):
        return False
    
    # Cannot start or end with slash
    if tag.startswith('/') or tag.endswith('/'):
        return False
    
    # Cannot have consecutive slashes
    if '//' in tag:
        return False
    
    return True