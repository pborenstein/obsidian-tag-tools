"""
Tag normalization utilities for consistent tag processing.
"""
from typing import List, Set
import re


def normalize_tag(tag: str) -> str:
    """
    Normalize a single tag to consistent format.
    
    Args:
        tag: Raw tag string
        
    Returns:
        Normalized tag string
    """
    if not tag:
        return ""
    
    # Convert to lowercase
    normalized = tag.lower()
    
    # Remove leading # if present
    if normalized.startswith('#'):
        normalized = normalized[1:]
    
    # Strip whitespace
    normalized = normalized.strip()
    
    # Remove empty parts separated by slashes
    if '/' in normalized:
        parts = [part.strip() for part in normalized.split('/') if part.strip()]
        normalized = '/'.join(parts)
    
    return normalized


def normalize_tags(tags: List[str]) -> List[str]:
    """
    Normalize a list of tags and remove duplicates.
    
    Args:
        tags: List of raw tag strings
        
    Returns:
        List of normalized, deduplicated tag strings
    """
    if not tags:
        return []
    
    # Normalize each tag
    normalized_tags = []
    for tag in tags:
        normalized = normalize_tag(tag)
        if normalized and normalized not in normalized_tags:
            normalized_tags.append(normalized)
    
    return normalized_tags


def deduplicate_tags(tags: List[str]) -> List[str]:
    """
    Remove duplicate tags while preserving order.
    
    Args:
        tags: List of tag strings
        
    Returns:
        List with duplicates removed
    """
    seen = set()
    result = []
    
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    
    return result


def is_nested_tag(tag: str) -> bool:
    """
    Check if a tag is nested (contains forward slash).
    
    Args:
        tag: Tag string to check
        
    Returns:
        True if tag is nested, False otherwise
    """
    return '/' in tag


def get_tag_hierarchy(tag: str) -> List[str]:
    """
    Get the tag hierarchy for a nested tag.
    
    Args:
        tag: Nested tag string (e.g., "parent/child/grandchild")
        
    Returns:
        List of tag hierarchy levels (e.g., ["parent", "parent/child", "parent/child/grandchild"])
    """
    if not is_nested_tag(tag):
        return [tag]
    
    parts = tag.split('/')
    hierarchy = []
    
    for i in range(len(parts)):
        level = '/'.join(parts[:i+1])
        hierarchy.append(level)
    
    return hierarchy


def flatten_nested_tags(tags: List[str]) -> List[str]:
    """
    Flatten nested tags to include all hierarchy levels.
    
    Args:
        tags: List of tag strings (may include nested tags)
        
    Returns:
        List of tags with all hierarchy levels included
    """
    flattened = []
    
    for tag in tags:
        hierarchy = get_tag_hierarchy(tag)
        flattened.extend(hierarchy)
    
    return deduplicate_tags(flattened)


def is_valid_tag(tag: str) -> bool:
    """
    Comprehensive tag validation to filter out noise.
    
    Args:
        tag: Tag string to validate
        
    Returns:
        True if tag is valid, False otherwise
    """
    if not tag or not isinstance(tag, str):
        return False
    
    # Remove leading # if present for validation
    clean_tag = tag.lstrip('#').strip()
    if not clean_tag:
        return False
    
    # Rule 1: No pure numbers (tags are never only numbers)
    if clean_tag.isdigit():
        return False
    
    # Rule 2: Must start with alphanumeric character
    if not clean_tag[0].isalnum():
        return False
    
    # Rule 3: Filter HTML entities and unicode noise
    if any(pattern in clean_tag for pattern in ['&#x', '\u200b', '\ufeff', '&nbsp;']):
        return False
    
    # Rule 4: Filter technical noise patterns
    noise_patterns = [
        r'^[a-f0-9]{8,}$',  # Long hex strings
        r'^[0-9a-f]{2,}-[0-9a-f]{2,}',  # UUID-like patterns
        r'dispatcher',  # Technical dispatcher tags
        r'^(dom|util|fs|stream|event|parameter)-',  # Technical prefixes
        r'^l[0-9]+$',  # Line number patterns like l123
        r'^[0-9]+px$',  # CSS pixel values
        r'^v[0-9]+\.[0-9]+\.[0-9]+',  # Full semantic versions only (keep shorter versions like v1.2)
        r'^[a-zA-Z]{1,2}$',  # Very short 1-2 letter-only tags (allows v1, but not tags with digits)
    ]
    
    for pattern in noise_patterns:
        if re.search(pattern, clean_tag, re.IGNORECASE):
            return False
    
    # Rule 5: Must contain at least one letter (including international letters)
    if not re.search(r'[^\d_\-/.]+', clean_tag):
        return False
    
    # Rule 6: Valid character set (letters, digits, underscore, dash, slash, dot)
    # Allow international characters by using \w+ but filtering out purely numeric/symbol tags
    if not re.match(r'^[\w\-/.]+$', clean_tag):
        return False
    
    # Rule 7: Slash validation for nested tags
    if '/' in clean_tag:
        parts = clean_tag.split('/')
        # No empty parts
        if any(not part.strip() for part in parts):
            return False
        # Each part must be valid
        for part in parts:
            if not re.match(r'^[a-zA-Z0-9_\-]+$', part):
                return False
    
    return True


def filter_valid_tags(tags: List[str]) -> List[str]:
    """
    Filter a list of tags to only include valid ones.
    
    Args:
        tags: List of tag strings
        
    Returns:
        List of valid tags only
    """
    return [tag for tag in tags if is_valid_tag(tag)]