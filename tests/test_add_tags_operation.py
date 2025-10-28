"""
Tests for AddTagsOperation - adding tags to notes' frontmatter.
"""

import pytest
from pathlib import Path
from tagex.core.operations.add_tags import AddTagsOperation


class TestAddTagsOperation:
    """Tests for the AddTagsOperation class."""

    def test_add_tags_operation_exists(self):
        """Test that AddTagsOperation module exists."""
        from tagex.core.operations import add_tags
        assert add_tags is not None
        assert AddTagsOperation is not None

    def test_add_tags_to_note_without_frontmatter(self, tmp_path):
        """Test adding tags to a note that has no frontmatter."""
        vault = tmp_path / "vault"
        vault.mkdir()

        note = vault / "test.md"
        note.write_text("# Test Note\n\nThis is a test note.")

        file_tag_map = {
            "test.md": ["python", "programming"]
        }

        operation = AddTagsOperation(
            vault_path=str(vault),
            file_tag_map=file_tag_map,
            dry_run=False,
            tag_types='frontmatter'
        )

        result = operation.run_operation()

        # Check that tags were added
        assert result['stats']['files_modified'] == 1
        assert result['stats']['tags_modified'] == 2

        # Verify file content
        content = note.read_text()
        assert 'tags: [python, programming]' in content
        assert '# Test Note' in content

    def test_add_tags_to_note_with_existing_frontmatter_no_tags(self, tmp_path):
        """Test adding tags to a note with frontmatter but no tags field."""
        vault = tmp_path / "vault"
        vault.mkdir()

        note = vault / "test.md"
        note_content = """---
title: My Note
date: 2024-01-01
---

# Test Note

Content here.
"""
        note.write_text(note_content)

        file_tag_map = {
            "test.md": ["python"]
        }

        operation = AddTagsOperation(
            vault_path=str(vault),
            file_tag_map=file_tag_map,
            dry_run=False,
            tag_types='frontmatter'
        )

        result = operation.run_operation()

        # Check that tag was added
        assert result['stats']['files_modified'] == 1
        assert result['stats']['tags_modified'] == 1

        # Verify file content
        content = note.read_text()
        assert 'tags: [python]' in content
        assert 'title: My Note' in content

    def test_add_tags_to_note_with_existing_tags(self, tmp_path):
        """Test adding tags to a note that already has some tags."""
        vault = tmp_path / "vault"
        vault.mkdir()

        note = vault / "test.md"
        note_content = """---
tags: [existing-tag]
---

# Test Note
"""
        note.write_text(note_content)

        file_tag_map = {
            "test.md": ["python", "programming"]
        }

        operation = AddTagsOperation(
            vault_path=str(vault),
            file_tag_map=file_tag_map,
            dry_run=False,
            tag_types='frontmatter'
        )

        result = operation.run_operation()

        # Check that tags were added
        assert result['stats']['files_modified'] == 1
        assert result['stats']['tags_modified'] == 2

        # Verify file content
        content = note.read_text()
        assert 'existing-tag' in content
        assert 'python' in content
        assert 'programming' in content

    def test_skip_duplicate_tags(self, tmp_path):
        """Test that duplicate tags are not added."""
        vault = tmp_path / "vault"
        vault.mkdir()

        note = vault / "test.md"
        note_content = """---
tags: [python, existing]
---

# Test Note
"""
        note.write_text(note_content)

        file_tag_map = {
            "test.md": ["python", "programming"]  # python already exists
        }

        operation = AddTagsOperation(
            vault_path=str(vault),
            file_tag_map=file_tag_map,
            dry_run=False,
            tag_types='frontmatter'
        )

        result = operation.run_operation()

        # Should only add programming (python already exists)
        assert result['stats']['files_modified'] == 1
        assert result['stats']['tags_modified'] == 1

        # Verify file content
        content = note.read_text()
        # Should not have duplicate python
        assert content.count('python') == 1

    def test_dry_run_mode(self, tmp_path):
        """Test that dry-run mode doesn't modify files."""
        vault = tmp_path / "vault"
        vault.mkdir()

        note = vault / "test.md"
        original_content = "# Test Note\n\nContent."
        note.write_text(original_content)

        file_tag_map = {
            "test.md": ["python"]
        }

        operation = AddTagsOperation(
            vault_path=str(vault),
            file_tag_map=file_tag_map,
            dry_run=True,
            tag_types='frontmatter'
        )

        result = operation.run_operation()

        # Should report would-be modifications
        assert result['stats']['files_modified'] == 1

        # But file should not be modified
        content = note.read_text()
        assert content == original_content
        assert 'python' not in content

    def test_multiline_tag_format(self, tmp_path):
        """Test adding tags to note with multiline tag format."""
        vault = tmp_path / "vault"
        vault.mkdir()

        note = vault / "test.md"
        note_content = """---
tags:
  - existing-tag
  - another-tag
---

# Test Note
"""
        note.write_text(note_content)

        file_tag_map = {
            "test.md": ["python"]
        }

        operation = AddTagsOperation(
            vault_path=str(vault),
            file_tag_map=file_tag_map,
            dry_run=False,
            tag_types='frontmatter'
        )

        result = operation.run_operation()

        # Check that tag was added
        assert result['stats']['files_modified'] == 1
        assert result['stats']['tags_modified'] == 1

        # Verify file content
        content = note.read_text()
        assert 'existing-tag' in content
        assert 'python' in content

    def test_only_frontmatter_tag_types(self, tmp_path):
        """Test that add_tags only supports frontmatter tag types."""
        vault = tmp_path / "vault"
        vault.mkdir()

        file_tag_map = {"test.md": ["python"]}

        # Should raise error for non-frontmatter tag types
        with pytest.raises(ValueError, match="frontmatter"):
            AddTagsOperation(
                vault_path=str(vault),
                file_tag_map=file_tag_map,
                dry_run=False,
                tag_types='inline'
            )

        with pytest.raises(ValueError, match="frontmatter"):
            AddTagsOperation(
                vault_path=str(vault),
                file_tag_map=file_tag_map,
                dry_run=False,
                tag_types='both'
            )

    def test_case_insensitive_duplicate_detection(self, tmp_path):
        """Test that duplicate detection is case-insensitive."""
        vault = tmp_path / "vault"
        vault.mkdir()

        note = vault / "test.md"
        note_content = """---
tags: [Python]
---

# Test Note
"""
        note.write_text(note_content)

        file_tag_map = {
            "test.md": ["python", "PYTHON", "PyThOn"]
        }

        operation = AddTagsOperation(
            vault_path=str(vault),
            file_tag_map=file_tag_map,
            dry_run=False,
            tag_types='frontmatter'
        )

        result = operation.run_operation()

        # Should not add any tags (all are duplicates with different case)
        assert result['stats']['files_modified'] == 0
        assert result['stats']['tags_modified'] == 0
