"""
Tests for plural normalization utilities.
"""

import pytest
from tagex.analysis.plural_normalizer import (
    normalize_plural_forms,
    normalize_compound_plurals,
    get_preferred_form,
    IRREGULAR_PLURALS,
    IRREGULAR_SINGULARS
)


class TestIrregularPlurals:
    """Test irregular plural detection."""

    def test_child_children(self):
        forms = normalize_plural_forms('child')
        assert 'child' in forms
        assert 'children' in forms

    def test_children_child(self):
        forms = normalize_plural_forms('children')
        assert 'child' in forms
        assert 'children' in forms

    def test_person_people(self):
        forms = normalize_plural_forms('person')
        assert 'person' in forms
        assert 'people' in forms

    def test_life_lives(self):
        forms = normalize_plural_forms('life')
        assert 'life' in forms
        assert 'lives' in forms

    def test_analysis_analyses(self):
        forms = normalize_plural_forms('analysis')
        assert 'analysis' in forms
        assert 'analyses' in forms


class TestPatternPlurals:
    """Test pattern-based plural detection."""

    def test_families_family(self):
        forms = normalize_plural_forms('families')
        assert 'families' in forms
        assert 'family' in forms

    def test_family_families(self):
        forms = normalize_plural_forms('family')
        assert 'family' in forms
        assert 'families' in forms

    def test_knives_knife(self):
        forms = normalize_plural_forms('knives')
        assert 'knives' in forms
        assert 'knife' in forms
        assert 'knif' in forms  # Also generates base form

    def test_watches_watch(self):
        forms = normalize_plural_forms('watches')
        assert 'watches' in forms
        assert 'watch' in forms

    def test_simple_plural(self):
        forms = normalize_plural_forms('books')
        assert 'books' in forms
        assert 'book' in forms

    def test_simple_singular(self):
        forms = normalize_plural_forms('book')
        assert 'book' in forms
        assert 'books' in forms

    def test_does_not_remove_double_s(self):
        # Words ending in -ss should not have it removed
        forms = normalize_plural_forms('class')
        assert 'class' in forms
        # Words ending in -ss should NOT have the -ss removed
        # They're too short for the -es pattern anyway (len <= 4)
        assert 'clas' not in forms


class TestCompoundPlurals:
    """Test compound tag plural detection."""

    def test_hyphenated_compound(self):
        forms = normalize_compound_plurals('tax-break')
        assert 'tax-break' in forms
        assert 'tax-breaks' in forms

    def test_nested_tag_last_component(self):
        forms = normalize_compound_plurals('child/development')
        assert 'child/development' in forms
        assert 'children/development' in forms

    def test_nested_tag_multiple_components(self):
        forms = normalize_compound_plurals('family/relationship')
        assert 'family/relationship' in forms
        # Should try pluralizing each component
        assert 'families/relationship' in forms
        assert 'family/relationships' in forms


class TestPreferredForm:
    """Test preferred form selection."""

    def test_prefers_plural_by_default(self):
        forms = {'book', 'books'}
        preferred = get_preferred_form(forms)
        assert preferred == 'books'

    def test_prefers_irregular_plural(self):
        forms = {'child', 'children'}
        preferred = get_preferred_form(forms)
        assert preferred == 'children'

    def test_prefers_longer_form(self):
        # When both end in 's', prefer longer (usually plural)
        forms = {'ideas', 'idea'}
        preferred = get_preferred_form(forms)
        assert preferred == 'ideas'

    def test_respects_usage_counts_when_significant(self):
        forms = {'book', 'books'}
        usage_counts = {'book': 50, 'books': 5}  # 10x difference
        preferred = get_preferred_form(forms, usage_counts)
        # Should prefer 'book' since it's 10x more common
        assert preferred == 'book'

    def test_prefers_most_used_with_default_usage_mode(self):
        forms = {'book', 'books'}
        usage_counts = {'book': 10, 'books': 8}  # Similar usage
        # Default mode is 'usage', so it prefers most-used (book)
        preferred = get_preferred_form(forms, usage_counts)
        assert preferred == 'book'

    def test_prefers_plural_with_plural_mode(self):
        forms = {'book', 'books'}
        usage_counts = {'book': 10, 'books': 8}
        # With preference='plural', always prefer plural form
        preferred = get_preferred_form(forms, usage_counts, preference='plural')
        assert preferred == 'books'

    def test_prefers_singular_with_singular_mode(self):
        forms = {'book', 'books'}
        usage_counts = {'book': 8, 'books': 10}
        # With preference='singular', always prefer singular form
        preferred = get_preferred_form(forms, usage_counts, preference='singular')
        assert preferred == 'book'

    def test_empty_forms(self):
        preferred = get_preferred_form(set())
        assert preferred == ''

    def test_single_form(self):
        forms = {'book'}
        preferred = get_preferred_form(forms)
        assert preferred == 'book'


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_short_tags(self):
        # Tags <= 4 chars should not apply pattern rules
        forms = normalize_plural_forms('cat')
        assert 'cat' in forms

    def test_tag_ending_in_ay(self):
        # -ay words should not apply -y/-ies pattern
        forms = normalize_plural_forms('day')
        assert 'day' in forms
        assert 'days' in forms
        # Should NOT have 'daies'
        assert 'daies' not in forms

    def test_preserves_case(self):
        # Should preserve original case
        forms = normalize_plural_forms('Family')
        assert 'Family' in forms
        # Generated forms should maintain case from original
        assert any('amilies' in f for f in forms)  # Contains the pattern

    def test_nested_tag_with_hyphen(self):
        forms = normalize_compound_plurals('project/sub-task')
        assert 'project/sub-task' in forms
        assert 'projects/sub-task' in forms  # Nested component
        assert 'project/sub-tasks' in forms  # Hyphenated component


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_irregular_in_compound(self):
        # Test irregular plural in hyphenated compound
        forms = normalize_compound_plurals('child-development')
        assert 'child-development' in forms
        assert 'children-development' in forms

    def test_complex_nested_irregular(self):
        # Test irregular plural in nested tag
        forms = normalize_compound_plurals('person/information')
        assert 'person/information' in forms
        assert 'people/information' in forms

    def test_pattern_ies_in_compound(self):
        # Test -ies pattern in compound
        forms = normalize_compound_plurals('family-history')
        assert 'family-history' in forms
        assert 'families-history' in forms
