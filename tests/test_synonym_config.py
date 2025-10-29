"""
Tests for synonym configuration management.
"""

import pytest
import yaml
from pathlib import Path
from tagex.config.synonym_config import SynonymConfig


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary vault directory."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    return vault


@pytest.fixture
def config_file(temp_vault):
    """Create a test synonym configuration file."""
    tagex_dir = temp_vault / '.tagex'
    tagex_dir.mkdir(exist_ok=True)
    config_path = temp_vault / '.tagex/synonyms.yaml'
    config = {
        'synonyms': [
            ['neuro', 'neurodivergent', 'neurodivergence'],
            ['adhd', 'add', 'attention-deficit'],
            ['tech', 'technology', 'technical']
        ],
        'prefer': {
            'python': ['py', 'python3'],
            'javascript': ['js', 'ecmascript']
        }
    }
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return config_path


class TestSynonymConfigLoading:
    """Test loading synonym configurations."""

    def test_load_empty_vault(self, temp_vault):
        config = SynonymConfig(temp_vault)
        assert len(config.synonym_groups) == 0
        assert len(config.canonical_map) == 0

    def test_load_existing_config(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        # Should have 5 groups (3 from synonyms, 2 from prefer)
        assert len(config.synonym_groups) == 5

        # Check synonym groups loaded correctly
        assert ['neuro', 'neurodivergent', 'neurodivergence'] in config.synonym_groups
        assert ['adhd', 'add', 'attention-deficit'] in config.synonym_groups
        assert ['tech', 'technology', 'technical'] in config.synonym_groups

        # Check prefer mappings loaded correctly
        assert ['python', 'py', 'python3'] in config.synonym_groups
        assert ['javascript', 'js', 'ecmascript'] in config.synonym_groups

    def test_canonical_map(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        # Test synonym group canonical
        assert config.canonical_map['neuro'] == 'neuro'
        assert config.canonical_map['neurodivergent'] == 'neuro'
        assert config.canonical_map['neurodivergence'] == 'neuro'

        # Test prefer canonical
        assert config.canonical_map['python'] == 'python'
        assert config.canonical_map['py'] == 'python'
        assert config.canonical_map['python3'] == 'python'


class TestGetCanonical:
    """Test getting canonical forms."""

    def test_get_canonical_for_synonym(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        assert config.get_canonical('neurodivergent') == 'neuro'
        assert config.get_canonical('add') == 'adhd'
        assert config.get_canonical('py') == 'python'

    def test_get_canonical_for_non_synonym(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        # Should return the tag itself
        assert config.get_canonical('unknown-tag') == 'unknown-tag'

    def test_get_canonical_for_canonical_tag(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        # Should return itself
        assert config.get_canonical('neuro') == 'neuro'
        assert config.get_canonical('python') == 'python'


class TestGetSynonyms:
    """Test getting synonym sets."""

    def test_get_synonyms_excludes_self(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        synonyms = config.get_synonyms('neuro')
        assert 'neuro' not in synonyms
        assert 'neurodivergent' in synonyms
        assert 'neurodivergence' in synonyms

    def test_get_synonyms_for_non_canonical(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        synonyms = config.get_synonyms('neurodivergent')
        assert 'neurodivergent' not in synonyms
        assert 'neuro' in synonyms
        assert 'neurodivergence' in synonyms

    def test_get_synonyms_for_unknown_tag(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        synonyms = config.get_synonyms('unknown-tag')
        assert len(synonyms) == 0


class TestGetAllInGroup:
    """Test getting all tags in a synonym group."""

    def test_get_all_in_group_includes_self(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        group = config.get_all_in_group('neuro')
        assert 'neuro' in group
        assert 'neurodivergent' in group
        assert 'neurodivergence' in group
        assert len(group) == 3

    def test_get_all_in_group_for_non_canonical(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        group = config.get_all_in_group('py')
        assert 'python' in group
        assert 'py' in group
        assert 'python3' in group
        assert len(group) == 3

    def test_get_all_in_group_for_unknown_tag(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        group = config.get_all_in_group('unknown-tag')
        assert group == {'unknown-tag'}


class TestAddSynonymGroup:
    """Test adding new synonym groups."""

    def test_add_synonym_group(self, temp_vault):
        config = SynonymConfig(temp_vault)

        # Add a new group
        config.add_synonym_group(['music', 'audio', 'sound'])

        # Verify it was added
        assert ['music', 'audio', 'sound'] in config.synonym_groups
        assert config.canonical_map['music'] == 'music'
        assert config.canonical_map['audio'] == 'music'
        assert config.canonical_map['sound'] == 'music'

    def test_add_synonym_group_saves_to_file(self, temp_vault):
        config = SynonymConfig(temp_vault)

        # Add a new group
        config.add_synonym_group(['music', 'audio', 'sound'])

        # Reload from file
        config2 = SynonymConfig(temp_vault)
        assert ['music', 'audio', 'sound'] in config2.synonym_groups

    def test_add_synonym_group_ignores_single_tag(self, temp_vault):
        config = SynonymConfig(temp_vault)

        # Try to add a single-tag group
        config.add_synonym_group(['music'])

        # Should not be added
        assert len(config.synonym_groups) == 0


class TestRemoveGroup:
    """Test removing synonym groups."""

    def test_remove_group_by_canonical(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        # Remove a group
        result = config.remove_group('neuro')

        assert result is True
        assert ['neuro', 'neurodivergent', 'neurodivergence'] not in config.synonym_groups
        assert 'neuro' not in config.canonical_map
        assert 'neurodivergent' not in config.canonical_map

    def test_remove_non_existent_group(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        result = config.remove_group('non-existent')
        assert result is False

    def test_remove_group_saves_to_file(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        config.remove_group('neuro')

        # Reload and verify
        config2 = SynonymConfig(temp_vault)
        assert ['neuro', 'neurodivergent', 'neurodivergence'] not in config2.synonym_groups


class TestHasSynonyms:
    """Test checking if synonyms are configured."""

    def test_has_synonyms_when_configured(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)
        assert config.has_synonyms() is True

    def test_has_synonyms_when_empty(self, temp_vault):
        config = SynonymConfig(temp_vault)
        assert config.has_synonyms() is False


class TestGetAllGroups:
    """Test getting all synonym groups."""

    def test_get_all_groups(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        groups = config.get_all_groups()
        assert len(groups) == 5
        assert ['neuro', 'neurodivergent', 'neurodivergence'] in groups
        assert ['python', 'py', 'python3'] in groups

    def test_get_all_groups_returns_copy(self, temp_vault, config_file):
        config = SynonymConfig(temp_vault)

        groups1 = config.get_all_groups()
        groups2 = config.get_all_groups()

        # Should be different objects
        assert groups1 is not groups2
        # But same content
        assert groups1 == groups2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_config_file(self, temp_vault):
        # Create empty config file
        tagex_dir = temp_vault / '.tagex'
        tagex_dir.mkdir(exist_ok=True)
        config_path = temp_vault / '.tagex/synonyms.yaml'
        config_path.write_text('')

        config = SynonymConfig(temp_vault)
        assert len(config.synonym_groups) == 0

    def test_config_with_empty_groups(self, temp_vault):
        tagex_dir = temp_vault / '.tagex'
        tagex_dir.mkdir(exist_ok=True)
        config_path = temp_vault / '.tagex/synonyms.yaml'
        config_data = {
            'synonyms': [
                ['valid', 'group'],
                [],  # Empty group
                ['single'],  # Single-element group
            ]
        }
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)

        config = SynonymConfig(temp_vault)
        # Should only load the valid group
        assert len(config.synonym_groups) == 1
        assert ['valid', 'group'] in config.synonym_groups
