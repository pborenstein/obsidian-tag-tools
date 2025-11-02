"""
Tests for exclusions configuration management.
"""

import pytest
import yaml
from pathlib import Path
from tagex.config.exclusions_config import ExclusionsConfig


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    return vault


@pytest.fixture
def config_file_with_none_values(temp_vault):
    """Create a test exclusions config file with None values (like tagex init creates)."""
    tagex_dir = temp_vault / '.tagex'
    tagex_dir.mkdir(exist_ok=True)
    config_path = temp_vault / '.tagex/exclusions.yaml'

    # Write config with only comments (results in None values when loaded)
    with open(config_path, 'w') as f:
        f.write("""exclude_tags:
  # Tags to exclude from merge/synonym suggestions
  # Example:
  # - spain

auto_generated_tags:
  # Tags inserted automatically by other tools
  # Example:
  # - copilot-conversation
""")
    return config_path


@pytest.fixture
def config_file_with_values(temp_vault):
    """Create a test exclusions config file with actual values."""
    tagex_dir = temp_vault / '.tagex'
    tagex_dir.mkdir(exist_ok=True)
    config_path = temp_vault / '.tagex/exclusions.yaml'
    config = {
        'exclude_tags': ['test-tag', 'exclude-me'],
        'auto_generated_tags': ['auto-tag', 'generated']
    }
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return config_path


class TestExclusionsConfigLoading:
    """Test loading exclusions configurations."""

    def test_load_empty_vault(self, temp_vault):
        """Test loading config from vault with no config file."""
        config = ExclusionsConfig(temp_vault)
        assert len(config.excluded_tags) == 0
        assert len(config.auto_generated_tags) == 0

    def test_load_config_with_none_values(self, temp_vault, config_file_with_none_values):
        """Test loading config with None values (regression test for issue #5)."""
        config = ExclusionsConfig(temp_vault)
        # Should not crash and should initialize as empty sets
        assert len(config.excluded_tags) == 0
        assert len(config.auto_generated_tags) == 0

    def test_load_config_with_values(self, temp_vault, config_file_with_values):
        """Test loading config with actual tag values."""
        config = ExclusionsConfig(temp_vault)
        assert 'test-tag' in config.excluded_tags
        assert 'exclude-me' in config.excluded_tags
        assert 'auto-tag' in config.auto_generated_tags
        assert 'generated' in config.auto_generated_tags

    def test_is_excluded(self, temp_vault, config_file_with_values):
        """Test checking if a tag is excluded."""
        config = ExclusionsConfig(temp_vault)
        assert config.is_excluded('test-tag')
        assert config.is_excluded('exclude-me')
        assert not config.is_excluded('not-excluded')

    def test_is_auto_generated(self, temp_vault, config_file_with_values):
        """Test checking if a tag is auto-generated."""
        config = ExclusionsConfig(temp_vault)
        assert config.is_auto_generated('auto-tag')
        assert config.is_auto_generated('generated')
        assert not config.is_auto_generated('manual-tag')
