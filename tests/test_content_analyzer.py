"""
Tests for content-based tag suggestion analyzer.
"""

import pytest
from pathlib import Path
from tagex.analysis.content_analyzer import ContentAnalyzer, analyze_content


class TestContentAnalyzer:
    """Tests for the content analyzer module."""

    def test_content_analyzer_exists(self):
        """Test that content analyzer module exists."""
        from tagex.analysis import content_analyzer
        assert content_analyzer is not None

    def test_content_analyzer_initialization(self):
        """Test ContentAnalyzer initialization."""
        tag_stats = {
            'python': {'count': 10, 'files': {'file1.md', 'file2.md'}},
            'programming': {'count': 8, 'files': {'file1.md', 'file3.md'}},
            'rare-tag': {'count': 1, 'files': {'file4.md'}}
        }

        analyzer = ContentAnalyzer(
            tag_stats=tag_stats,
            vault_path='/tmp/test-vault',
            min_tag_count=2,
            min_tag_frequency=2
        )

        assert analyzer is not None
        assert len(analyzer.candidate_tags) == 2  # Only tags with count >= 2
        assert 'rare-tag' not in analyzer.candidate_tags
        assert 'python' in analyzer.candidate_tags
        assert 'programming' in analyzer.candidate_tags

    def test_content_extraction(self, tmp_path):
        """Test note content extraction."""
        # Create a test vault
        vault = tmp_path / "vault"
        vault.mkdir()

        # Create a test note
        note_path = vault / "test.md"
        note_content = """---
tags: [existing-tag]
---

# Test Note

This is a test note about Python programming.
We're testing the content extraction functionality.

## Section 2

More content here.
"""
        note_path.write_text(note_content)

        tag_stats = {'python': {'count': 5, 'files': set()}}
        analyzer = ContentAnalyzer(tag_stats, str(vault))

        content = analyzer._extract_note_content(note_path)

        assert content is not None
        assert 'test' in content.lower()
        assert 'python' in content.lower()
        assert 'programming' in content.lower()
        # Should not include frontmatter
        assert 'existing-tag' not in content.lower()

    def test_keyword_matching_fallback(self, tmp_path):
        """Test keyword matching when transformers not available."""
        vault = tmp_path / "vault"
        vault.mkdir()

        tag_stats = {
            'python': {'count': 10, 'files': set()},
            'javascript': {'count': 8, 'files': set()},
            'database': {'count': 5, 'files': set()}
        }

        analyzer = ContentAnalyzer(tag_stats, str(vault))

        # Test keyword matching
        content = "This is a note about Python programming and databases."
        current_tags = set()

        suggestions = analyzer._keyword_matching(
            content,
            current_tags,
            top_n=3,
            min_confidence=0.3
        )

        assert len(suggestions) > 0
        # Should suggest python since it's in the content
        tag_names = [s['tag'] for s in suggestions]
        assert 'python' in tag_names

    def test_exclude_existing_tags(self, tmp_path):
        """Test that existing tags are excluded from suggestions."""
        vault = tmp_path / "vault"
        vault.mkdir()

        tag_stats = {
            'python': {'count': 10, 'files': set()},
            'programming': {'count': 8, 'files': set()}
        }

        analyzer = ContentAnalyzer(tag_stats, str(vault))

        content = "This is a note about Python programming."
        current_tags = {'python'}  # Already has python tag

        suggestions = analyzer._keyword_matching(
            content,
            current_tags,
            top_n=3,
            min_confidence=0.3
        )

        # Should not suggest python since it's already tagged
        tag_names = [s['tag'] for s in suggestions]
        assert 'python' not in tag_names

    def test_convenience_function(self, tmp_path):
        """Test the analyze_content convenience function."""
        vault = tmp_path / "vault"
        vault.mkdir()

        # Create a test note with no tags
        note_path = vault / "test.md"
        note_content = "# Test\n\nA simple note."
        note_path.write_text(note_content)

        tag_stats = {
            'test': {'count': 5, 'files': set()},
            'notes': {'count': 3, 'files': set()}
        }

        # Should not crash when called
        result = analyze_content(
            tag_stats=tag_stats,
            vault_path=str(vault),
            min_tag_count=1,
            top_n=2,
            use_semantic=False  # Use keyword matching only
        )

        # Result should be a list (may be empty if no matches found)
        assert isinstance(result, list)


class TestContentAnalyzerCLI:
    """Tests for the suggest CLI command."""

    def test_suggest_command_help(self):
        """Test suggest command help."""
        from tagex.main import main as cli
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', 'suggest', '--help'])

        # Should show help without errors
        assert result.exit_code == 0
        help_text = result.output.lower()
        assert 'suggest' in help_text or 'content' in help_text

    def test_suggest_command_defaults_to_cwd(self):
        """Test that suggest command defaults to current working directory."""
        from tagex.main import main as cli
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(cli, ['analyze', 'suggest'])

        # Should succeed with default vault path (cwd)
        # May succeed or fail based on whether cwd is a valid vault,
        # but should not crash from missing argument
        assert result.exit_code in [0, 1]  # Either success or validation error, not crash
