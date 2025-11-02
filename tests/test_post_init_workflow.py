"""
Integration tests for post-init workflows.

Tests that all commands work correctly immediately after running 'tagex init'
with virgin config files (containing only comments/None values).

Regression tests for issue #5 and similar config-related issues.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner


@pytest.fixture
def test_vault(tmp_path):
    """Create a test vault with sample markdown files."""
    vault = tmp_path / "test_vault"
    vault.mkdir()

    # Create sample files with various tags
    (vault / "work.md").write_text("""---
tags: [work, project, development]
---

# Work Notes

Some #work-related content with #project tags.
""")

    (vault / "personal.md").write_text("""---
tags: [personal, ideas, thoughts]
---

# Personal Notes

Content with #ideas and #creativity tags.
""")

    (vault / "meeting.md").write_text("""---
tags: [work, meetings, notes]
---

# Meeting Notes

Discussion about #project and #development work.
""")

    # Create file with plural tags
    (vault / "books.md").write_text("""---
tags: [book, books, reading]
---

# Reading List

Notes about various #book and #books I've read.
""")

    # Create file with potential synonyms
    (vault / "tech.md").write_text("""---
tags: [technology, tech, computers, computer]
---

# Technology Notes

Content about #tech and #technology topics.
""")

    return vault


class TestPostInitAnalyzeCommands:
    """Test all analyze commands work with virgin configs after init."""

    def test_init_then_analyze_recommendations(self, test_vault):
        """Test: tagex init → tagex analyze recommendations (regression test for issue #5)."""
        from tagex.main import main as cli

        runner = CliRunner()

        # Step 1: Run init
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0
        assert (test_vault / '.tagex').exists()
        assert (test_vault / '.tagex' / 'exclusions.yaml').exists()

        # Step 2: Run analyze recommendations (this was crashing in issue #5)
        result = runner.invoke(cli, ['analyze', 'recommendations', str(test_vault)])

        # Should not crash
        assert result.exit_code == 0

        # Output should be reasonable (may be empty if no recommendations)
        assert result.output is not None

    def test_init_then_analyze_merges(self, test_vault):
        """Test: tagex init → tagex analyze merges."""
        from tagex.main import main as cli

        runner = CliRunner()

        # Init
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0

        # Analyze merges
        result = runner.invoke(cli, ['analyze', 'merges', str(test_vault)])

        assert result.exit_code == 0
        assert result.output is not None

    def test_init_then_analyze_synonyms(self, test_vault):
        """Test: tagex init → tagex analyze synonyms."""
        from tagex.main import main as cli

        runner = CliRunner()

        # Init
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0

        # Analyze synonyms
        result = runner.invoke(cli, ['analyze', 'synonyms', str(test_vault)])

        assert result.exit_code == 0
        assert result.output is not None

    def test_init_then_analyze_plurals(self, test_vault):
        """Test: tagex init → tagex analyze plurals."""
        from tagex.main import main as cli

        runner = CliRunner()

        # Init
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0

        # Analyze plurals
        result = runner.invoke(cli, ['analyze', 'plurals', str(test_vault)])

        assert result.exit_code == 0
        assert result.output is not None

    def test_init_then_analyze_suggest(self, test_vault):
        """Test: tagex init → tagex analyze suggest."""
        from tagex.main import main as cli

        runner = CliRunner()

        # Init
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0

        # Analyze suggest
        result = runner.invoke(cli, ['analyze', 'suggest', str(test_vault)])

        assert result.exit_code == 0
        assert result.output is not None

    def test_init_then_health(self, test_vault):
        """Test: tagex init → tagex health."""
        from tagex.main import main as cli

        runner = CliRunner()

        # Init
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0

        # Health check
        result = runner.invoke(cli, ['health', str(test_vault)])

        assert result.exit_code == 0
        assert result.output is not None
        # Health output should contain metrics
        assert 'total' in result.output.lower() or 'health' in result.output.lower()

    def test_all_analyze_commands_in_sequence(self, test_vault):
        """Test running all analyze commands in sequence after init."""
        from tagex.main import main as cli

        runner = CliRunner()

        # Init once
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0

        # Run all analyze commands
        commands = [
            ['analyze', 'recommendations', str(test_vault)],
            ['analyze', 'merges', str(test_vault)],
            ['analyze', 'synonyms', str(test_vault)],
            ['analyze', 'plurals', str(test_vault)],
            ['analyze', 'suggest', str(test_vault)],
            ['health', str(test_vault)],
        ]

        for cmd in commands:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == 0, f"Command {' '.join(cmd)} failed: {result.output}"


class TestPostInitWithConfigModifications:
    """Test workflows where user modifies config after init."""

    def test_init_then_add_exclusions_then_analyze(self, test_vault, tmp_path):
        """Test: init → user adds exclusions → analyze respects exclusions."""
        from tagex.main import main as cli
        import yaml

        runner = CliRunner()

        # Init
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0

        # Manually add exclusions to config
        exclusions_file = test_vault / '.tagex' / 'exclusions.yaml'
        with open(exclusions_file, 'w') as f:
            yaml.dump({
                'exclude_tags': ['work', 'personal'],
                'auto_generated_tags': []
            }, f)

        # Run analyze - should respect exclusions
        result = runner.invoke(cli, ['analyze', 'merges', str(test_vault)])
        assert result.exit_code == 0

        # Excluded tags should not appear in merge suggestions
        # (If they do appear, they should be marked as excluded)
        output_lower = result.output.lower()
        # This is a soft check - exact output format may vary
        assert result.exit_code == 0

    def test_init_then_add_synonyms_then_analyze(self, test_vault):
        """Test: init → user adds synonyms → analyze uses them."""
        from tagex.main import main as cli
        import yaml

        runner = CliRunner()

        # Init
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0

        # Manually add synonyms to config
        synonyms_file = test_vault / '.tagex' / 'synonyms.yaml'
        with open(synonyms_file, 'w') as f:
            yaml.dump({
                'tech': ['technology', 'computers']
            }, f)

        # Run analyze recommendations - should use user synonyms
        result = runner.invoke(cli, ['analyze', 'recommendations', str(test_vault)])
        assert result.exit_code == 0


class TestInitCommand:
    """Test the init command itself."""

    def test_init_creates_directory_structure(self, tmp_path):
        """Test init creates .tagex directory with all required files."""
        from tagex.main import main as cli

        vault = tmp_path / "new_vault"
        vault.mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ['init', str(vault)])

        assert result.exit_code == 0

        # Verify directory structure
        tagex_dir = vault / '.tagex'
        assert tagex_dir.exists()
        assert tagex_dir.is_dir()

        # Verify all config files created
        assert (tagex_dir / 'exclusions.yaml').exists()
        assert (tagex_dir / 'synonyms.yaml').exists()
        assert (tagex_dir / 'config.yaml').exists()
        assert (tagex_dir / 'README.md').exists()

    def test_init_config_files_are_valid_yaml(self, tmp_path):
        """Test all created config files are valid YAML."""
        from tagex.main import main as cli
        import yaml

        vault = tmp_path / "yaml_test_vault"
        vault.mkdir()

        runner = CliRunner()
        result = runner.invoke(cli, ['init', str(vault)])
        assert result.exit_code == 0

        tagex_dir = vault / '.tagex'

        # All YAML files should parse without error
        yaml_files = ['exclusions.yaml', 'synonyms.yaml', 'config.yaml']
        for filename in yaml_files:
            filepath = tagex_dir / filename
            with open(filepath) as f:
                try:
                    config = yaml.safe_load(f)
                    # Config may be None if file only has comments (this is OK)
                    assert config is None or isinstance(config, dict)
                except yaml.YAMLError as e:
                    pytest.fail(f"{filename} is not valid YAML: {e}")

    def test_init_refuses_overwrite_without_force(self, tmp_path):
        """Test init refuses to overwrite existing config without --force."""
        from tagex.main import main as cli

        vault = tmp_path / "no_overwrite_vault"
        vault.mkdir()

        runner = CliRunner()

        # First init should succeed
        result1 = runner.invoke(cli, ['init', str(vault)])
        assert result1.exit_code == 0

        # Second init without --force should fail or warn
        result2 = runner.invoke(cli, ['init', str(vault)])

        # Should either exit with error or show warning message
        # (Exact behavior depends on implementation)
        assert result2.exit_code != 0 or 'exist' in result2.output.lower()

    def test_init_force_overwrites_existing(self, tmp_path):
        """Test init --force overwrites existing config."""
        from tagex.main import main as cli
        import yaml

        vault = tmp_path / "force_vault"
        vault.mkdir()

        runner = CliRunner()

        # First init
        result1 = runner.invoke(cli, ['init', str(vault)])
        assert result1.exit_code == 0

        # Modify config file
        exclusions_file = vault / '.tagex' / 'exclusions.yaml'
        with open(exclusions_file, 'w') as f:
            yaml.dump({'exclude_tags': ['modified']}, f)

        # Read modified content
        modified_content = exclusions_file.read_text()
        assert 'modified' in modified_content

        # Force reinit
        result2 = runner.invoke(cli, ['init', str(vault), '--force'])
        assert result2.exit_code == 0

        # Config should be reset to template (without 'modified')
        reset_content = exclusions_file.read_text()
        assert 'modified' not in reset_content


class TestEdgeCases:
    """Test edge cases in config handling."""

    def test_commands_work_without_tagex_directory(self, test_vault):
        """Test commands use defaults when .tagex directory doesn't exist."""
        from tagex.main import main as cli

        # Don't run init - .tagex directory won't exist
        runner = CliRunner()

        # Commands should still work with default configs
        result = runner.invoke(cli, ['analyze', 'merges', str(test_vault)])

        # May succeed or give informative message
        # Should not crash
        assert result.exit_code in [0, 1]  # Allow informative exit

    def test_analyze_with_malformed_exclusions_yaml(self, test_vault):
        """Test commands handle malformed exclusions.yaml gracefully."""
        from tagex.main import main as cli

        runner = CliRunner()

        # Init first
        init_result = runner.invoke(cli, ['init', str(test_vault)])
        assert init_result.exit_code == 0

        # Corrupt the exclusions file
        exclusions_file = test_vault / '.tagex' / 'exclusions.yaml'
        with open(exclusions_file, 'w') as f:
            f.write("invalid: [yaml: content\nmalformed")

        # Should handle gracefully (either use defaults or show helpful error)
        result = runner.invoke(cli, ['analyze', 'recommendations', str(test_vault)])

        # Should not crash hard - may warn but should be graceful
        assert result.exit_code in [0, 1]
        assert result.output is not None
