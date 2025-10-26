"""
Tests for overbroad tag detection and tag quality analysis.
"""

import pytest
from tagex.analysis.breadth_analyzer import (
    detect_overbroad_tags,
    calculate_tag_specificity,
    suggest_tag_refinements,
    analyze_tag_quality,
    format_quality_report,
    GENERIC_WORDS
)


@pytest.fixture
def sample_tag_stats():
    """Create sample tag statistics for testing."""
    return {
        'notes': {
            'count': 700,
            'files': set(range(700))  # 70% of 1000 files
        },
        'ideas': {
            'count': 500,
            'files': set(range(500))  # 50% of files
        },
        'project': {
            'count': 300,
            'files': set(range(300))  # 30% of files
        },
        'python': {
            'count': 50,
            'files': set(range(100, 150))  # 5% of files
        },
        'python/data-analysis': {
            'count': 20,
            'files': set(range(100, 120))  # 2% of files
        },
        'misc': {
            'count': 100,
            'files': set(range(900, 1000))  # 10% of files
        }
    }


class TestDetectOverbroadTags:
    """Test overbroad tag detection."""

    def test_detect_extreme_coverage(self, sample_tag_stats):
        total_files = 1000
        overbroad = detect_overbroad_tags(sample_tag_stats, total_files)

        # 'notes' at 70% should be extreme
        notes_entry = next(t for t in overbroad if t['tag'] == 'notes')
        assert notes_entry['severity'] == 'extreme'
        assert notes_entry['file_ratio'] == 0.7

    def test_detect_very_high_coverage(self, sample_tag_stats):
        total_files = 1000
        overbroad = detect_overbroad_tags(sample_tag_stats, total_files)

        # 'ideas' at 50% should be very_high
        ideas_entry = next(t for t in overbroad if t['tag'] == 'ideas')
        assert ideas_entry['severity'] == 'very_high'
        assert ideas_entry['file_ratio'] == 0.5

    def test_detect_high_coverage(self, sample_tag_stats):
        total_files = 1000
        overbroad = detect_overbroad_tags(sample_tag_stats, total_files)

        # 'project' at 30% should be high
        project_entry = next(t for t in overbroad if t['tag'] == 'project')
        assert project_entry['severity'] == 'high'
        assert project_entry['file_ratio'] == 0.3

    def test_specific_tags_not_detected(self, sample_tag_stats):
        total_files = 1000
        overbroad = detect_overbroad_tags(sample_tag_stats, total_files)

        # 'python' at 5% should not be detected
        python_tags = [t for t in overbroad if t['tag'] == 'python']
        assert len(python_tags) == 0

    def test_sorted_by_ratio(self, sample_tag_stats):
        total_files = 1000
        overbroad = detect_overbroad_tags(sample_tag_stats, total_files)

        # Should be sorted by file_ratio descending
        ratios = [t['file_ratio'] for t in overbroad]
        assert ratios == sorted(ratios, reverse=True)

    def test_custom_thresholds(self, sample_tag_stats):
        total_files = 1000
        thresholds = {
            'high_coverage': 0.10,
            'very_high_coverage': 0.20,
            'extreme_coverage': 0.40
        }
        overbroad = detect_overbroad_tags(sample_tag_stats, total_files, thresholds)

        # With lower thresholds, more tags should be detected
        assert len(overbroad) > 0
        # 'misc' at 10% should now be detected as high
        misc_tags = [t for t in overbroad if t['tag'] == 'misc']
        assert len(misc_tags) == 1


class TestCalculateTagSpecificity:
    """Test tag specificity scoring."""

    def test_generic_word_penalty(self, sample_tag_stats):
        total_files = 1000

        specificity = calculate_tag_specificity('notes', sample_tag_stats, total_files)

        assert specificity['is_generic'] is True
        # Generic words get -5 penalty
        assert specificity['specificity_score'] < 0

    def test_nested_tag_bonus(self, sample_tag_stats):
        total_files = 1000

        nested = calculate_tag_specificity('python/data-analysis', sample_tag_stats, total_files)
        flat = calculate_tag_specificity('python', sample_tag_stats, total_files)

        # Nested tag should have higher structure score
        assert nested['structure_score'] > flat['structure_score']
        # Depth of 2 for nested + 1 for compound (data-analysis has hyphen) = 3
        assert nested['structure_score'] == 3
        assert flat['structure_score'] == 1

    def test_compound_tag_bonus(self):
        tag_stats = {
            'data-science': {
                'count': 20,
                'files': set(range(20))
            }
        }
        total_files = 100

        specificity = calculate_tag_specificity('data-science', tag_stats, total_files)

        # Should get bonus for compound (hyphen)
        assert specificity['structure_score'] == 2  # depth 1 + compound

    def test_information_content(self, sample_tag_stats):
        total_files = 1000

        rare = calculate_tag_specificity('python/data-analysis', sample_tag_stats, total_files)
        common = calculate_tag_specificity('notes', sample_tag_stats, total_files)

        # Rare tags should have higher IC score
        assert rare['ic_score'] > common['ic_score']

    def test_assessment_categories(self, sample_tag_stats):
        total_files = 1000

        # Generic tag should be too_broad
        notes = calculate_tag_specificity('notes', sample_tag_stats, total_files)
        assert notes['assessment'] == 'too_broad'

        # Nested specific tag should be highly_specific
        nested = calculate_tag_specificity('python/data-analysis', sample_tag_stats, total_files)
        # Might be appropriately_specific or highly_specific depending on exact score
        assert nested['assessment'] in ['appropriately_specific', 'highly_specific']


class TestSuggestTagRefinements:
    """Test tag refinement suggestions."""

    def test_suggests_hierarchical_breakdowns(self):
        tag_stats = {
            'notes': {
                'count': 100,
                'files': set(range(100))
            },
            'meeting': {
                'count': 30,
                'files': set(range(30))  # High overlap with notes
            },
            'research': {
                'count': 25,
                'files': set(range(50, 75))
            }
        }
        all_tags = set(tag_stats.keys())

        suggestions = suggest_tag_refinements('notes', tag_stats, all_tags)

        # Should suggest breaking down into notes/meeting, notes/research
        suggestion_text = '\n'.join(suggestions)
        assert 'notes/meeting' in suggestion_text
        assert 'notes/research' in suggestion_text

    def test_shows_existing_nested_tags(self):
        tag_stats = {
            'work': {
                'count': 100,
                'files': set(range(100))
            },
            'work/meetings': {
                'count': 20,
                'files': set(range(20))
            },
            'work/projects': {
                'count': 30,
                'files': set(range(30, 60))
            }
        }
        all_tags = set(tag_stats.keys())

        suggestions = suggest_tag_refinements('work', tag_stats, all_tags)

        suggestion_text = '\n'.join(suggestions)
        assert 'work/meetings' in suggestion_text
        assert 'work/projects' in suggestion_text
        assert 'Existing specific tags' in suggestion_text

    def test_no_suggestions_for_specific_tag(self):
        tag_stats = {
            'python/data-analysis/pandas': {
                'count': 5,
                'files': set(range(5))
            },
            'other': {
                'count': 2,
                'files': set(range(10, 12))
            }
        }
        all_tags = set(tag_stats.keys())

        suggestions = suggest_tag_refinements(
            'python/data-analysis/pandas',
            tag_stats,
            all_tags
        )

        # Should have few or no suggestions for already specific tag
        assert len(suggestions) <= 2  # Maybe just the header


class TestAnalyzeTagQuality:
    """Test comprehensive tag quality analysis."""

    def test_complete_analysis(self, sample_tag_stats):
        total_files = 1000

        analysis = analyze_tag_quality(sample_tag_stats, total_files)

        # Should have all required keys
        assert 'overbroad_tags' in analysis
        assert 'specificity_scores' in analysis
        assert 'by_assessment' in analysis
        assert 'summary' in analysis

    def test_summary_counts(self, sample_tag_stats):
        total_files = 1000

        analysis = analyze_tag_quality(sample_tag_stats, total_files)
        summary = analysis['summary']

        assert summary['total_tags'] == len(sample_tag_stats)
        assert summary['overbroad_count'] >= 0
        assert summary['too_broad_count'] >= 0

    def test_assessment_grouping(self, sample_tag_stats):
        total_files = 1000

        analysis = analyze_tag_quality(sample_tag_stats, total_files)
        by_assessment = analysis['by_assessment']

        # Should have assessment categories
        possible_assessments = [
            'too_broad',
            'moderately_specific',
            'appropriately_specific',
            'highly_specific'
        ]

        for assessment in by_assessment.keys():
            assert assessment in possible_assessments

        # Each group should be sorted by score
        for assessment, tags in by_assessment.items():
            scores = [score_data['specificity_score'] for _, score_data in tags]
            assert scores == sorted(scores)


class TestFormatQualityReport:
    """Test quality report formatting."""

    def test_report_structure(self, sample_tag_stats):
        total_files = 1000

        analysis = analyze_tag_quality(sample_tag_stats, total_files)
        report = format_quality_report(analysis, sample_tag_stats, max_items=5)

        # Should contain key sections
        assert 'TAG QUALITY REPORT' in report
        assert 'SUMMARY:' in report
        assert 'SPECIFICITY ANALYSIS:' in report

    def test_report_includes_overbroad(self, sample_tag_stats):
        total_files = 1000

        analysis = analyze_tag_quality(sample_tag_stats, total_files)
        report = format_quality_report(analysis, sample_tag_stats, max_items=10)

        # Should include overbroad tags
        if analysis['overbroad_tags']:
            assert 'OVERBROAD TAGS' in report

    def test_max_items_limit(self, sample_tag_stats):
        total_files = 1000

        analysis = analyze_tag_quality(sample_tag_stats, total_files)
        report = format_quality_report(analysis, sample_tag_stats, max_items=2)

        # Report should be generated successfully with limit
        assert 'TAG QUALITY REPORT' in report


class TestGenericWords:
    """Test generic word detection."""

    def test_generic_words_set_exists(self):
        assert len(GENERIC_WORDS) > 0
        assert 'notes' in GENERIC_WORDS
        assert 'ideas' in GENERIC_WORDS
        assert 'misc' in GENERIC_WORDS

    def test_generic_word_detection_in_specificity(self):
        tag_stats = {
            'misc': {
                'count': 10,
                'files': set(range(10))
            }
        }
        total_files = 100

        specificity = calculate_tag_specificity('misc', tag_stats, total_files)

        assert specificity['is_generic'] is True
        assert specificity['assessment'] == 'too_broad'
