"""
Plural normalization utilities for tag quality improvements.

This module provides enhanced singular/plural detection beyond simple -s suffix removal,
including irregular plurals and pattern-based normalization.

Convention: This project prefers plural tags over singular tags (e.g., 'books' not 'book').
"""

from typing import Set

# Dictionary of irregular English plurals
IRREGULAR_PLURALS = {
    'child': 'children',
    'person': 'people',
    'man': 'men',
    'woman': 'women',
    'tooth': 'teeth',
    'foot': 'feet',
    'mouse': 'mice',
    'goose': 'geese',
    'life': 'lives',
    'knife': 'knives',
    'leaf': 'leaves',
    'self': 'selves',
    'elf': 'elves',
    'half': 'halves',
    'ox': 'oxen',
    'crisis': 'crises',
    'analysis': 'analyses',
    'thesis': 'theses',
    'phenomenon': 'phenomena',
    'criterion': 'criteria',
}

# Build reverse mapping
IRREGULAR_SINGULARS = {v: k for k, v in IRREGULAR_PLURALS.items()}


def normalize_plural_forms(tag: str) -> Set[str]:
    """Generate all possible singular/plural forms of a tag.

    Note: This project prefers plural forms. When suggesting merges,
    the plural form should be recommended as the canonical form.

    Args:
        tag: The tag to normalize

    Returns:
        Set of normalized forms (both singular and plural)

    Examples:
        >>> normalize_plural_forms('child')
        {'child', 'children'}
        >>> normalize_plural_forms('family')
        {'family', 'families'}
        >>> normalize_plural_forms('life')
        {'life', 'lives'}
    """
    normalized = {tag}
    tag_lower = tag.lower()

    # Check irregular forms first
    if tag_lower in IRREGULAR_PLURALS:
        normalized.add(IRREGULAR_PLURALS[tag_lower])
    elif tag_lower in IRREGULAR_SINGULARS:
        normalized.add(IRREGULAR_SINGULARS[tag_lower])

    # Pattern-based detection (apply to longer tags)
    if len(tag_lower) > 4:
        # -ies/-y pattern (families → family)
        if tag_lower.endswith('ies'):
            normalized.add(tag[:-3] + 'y')
        elif tag_lower.endswith('y') and not tag_lower.endswith('ay') and not tag_lower.endswith('ey'):
            normalized.add(tag[:-1] + 'ies')

        # -ves/-f pattern (lives → life)
        if tag_lower.endswith('ves'):
            normalized.add(tag[:-3] + 'fe')
            normalized.add(tag[:-3] + 'f')
        elif tag_lower.endswith('f') or tag_lower.endswith('fe'):
            base = tag[:-2] if tag_lower.endswith('fe') else tag[:-1]
            normalized.add(base + 'ves')

        # -es pattern (watches → watch, but not -ss words)
        if tag_lower.endswith('es') and not tag_lower.endswith('ses'):
            normalized.add(tag[:-2])

    # Simple -s pattern (apply to all tags)
    if tag_lower.endswith('s') and not tag_lower.endswith('ss'):
        normalized.add(tag[:-1])
    elif not tag_lower.endswith('s'):
        normalized.add(tag + 's')

    return normalized


def normalize_compound_plurals(tag: str) -> Set[str]:
    """Handle plurals in compound/nested tags.

    Examples:
        >>> normalize_compound_plurals('tax-break')
        {'tax-break', 'tax-breaks'}
        >>> normalize_compound_plurals('child/development')
        {'child/development', 'children/development'}

    Args:
        tag: The compound tag to normalize

    Returns:
        Set of normalized forms including compound variations
    """
    normalized = {tag}

    # Handle hyphenated compounds - try pluralizing each part
    if '-' in tag:
        parts = tag.split('-')
        for i, part in enumerate(parts):
            part_forms = normalize_plural_forms(part)
            for form in part_forms:
                new_parts = parts[:i] + [form] + parts[i+1:]
                normalized.add('-'.join(new_parts))

    # Handle nested tags
    if '/' in tag:
        parts = tag.split('/')
        # Try pluralizing each component
        for i, part in enumerate(parts):
            part_forms = normalize_plural_forms(part)
            for form in part_forms:
                new_parts = parts[:i] + [form] + parts[i+1:]
                normalized.add('/'.join(new_parts))

    return normalized


def get_preferred_form(forms: Set[str], usage_counts: dict = None,
                      preference: str = 'usage', usage_ratio_threshold: float = 2.0) -> str:
    """Get the preferred canonical form from a set of variants.

    Args:
        forms: Set of tag variants
        usage_counts: Optional dict mapping tags to usage counts
        preference: Preference mode ('plural', 'singular', or 'usage')
        usage_ratio_threshold: Minimum ratio to prefer most-used form (default: 2.0)

    Returns:
        The preferred canonical form

    Examples:
        >>> get_preferred_form({'book', 'books'}, {'book': 10, 'books': 2}, 'usage')
        'book'  # Most used
        >>> get_preferred_form({'book', 'books'}, {'book': 5, 'books': 5}, 'plural')
        'books'  # Plural preferred
        >>> get_preferred_form({'book', 'books'}, {'book': 5, 'books': 5}, 'singular')
        'book'  # Singular preferred
    """
    if not forms:
        return ''

    forms_list = list(forms)

    # Usage-based preference
    if preference == 'usage' and usage_counts:
        counted_forms = [f for f in forms_list if f in usage_counts]
        if counted_forms:
            max_usage = max(usage_counts[f] for f in counted_forms)
            most_used = [f for f in counted_forms if usage_counts[f] == max_usage]

            # Check if one form is significantly more common
            other_forms = [f for f in counted_forms if usage_counts[f] != max_usage]
            if other_forms:
                max_other = max(usage_counts[f] for f in other_forms)
                if max_usage >= max_other * usage_ratio_threshold:
                    return most_used[0]

            # If tied or close, prefer the most-used form
            if len(most_used) == 1:
                return most_used[0]
            # If multiple forms have same max usage, fall through to plural/singular logic
            forms_list = most_used

    # Singular preference
    if preference == 'singular':
        return min(forms_list, key=lambda t: (
            t.lower().endswith('s') or t.lower() in IRREGULAR_PLURALS.values(),  # Prefer non-plurals
            -len(t),  # Shorter forms (usually singular)
            t.lower()  # Alphabetical for tiebreaker
        ))

    # Plural preference (default)
    return max(forms_list, key=lambda t: (
        t.lower().endswith('s') or t.lower() in IRREGULAR_PLURALS.values(),  # Prefer plurals
        len(t),  # Longer forms (often plurals)
        t.lower()  # Alphabetical for tiebreaker
    ))
