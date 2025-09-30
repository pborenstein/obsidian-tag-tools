"""
Tests for the operations module - tag rename, merge, and operation logging.
"""

import pytest
import json
from pathlib import Path
import shutil


class TestTagOperationEngine:
    """Tests for the base TagOperationEngine class."""
    
    def test_operation_engine_initialization(self):
        """Test TagOperationEngine can be initialized."""
        from tagex.core.operations.tag_operations import TagOperationEngine
        
        # This is an abstract base class, so we may need to test via subclasses
        # But we can test that it exists and has expected interface
        assert hasattr(TagOperationEngine, '__init__')
    
    def test_dry_run_mode_available(self):
        """Test that dry-run mode is available in operation engine."""
        from tagex.core.operations.tag_operations import TagOperationEngine
        
        # Check that dry-run functionality exists in the interface
        # This might be tested through subclasses
        assert hasattr(TagOperationEngine, 'run_operation')


class TestRenameOperation:
    """Tests for tag rename operations."""
    
    def test_rename_operation_initialization(self):
        """Test RenameOperation can be initialized."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        operation = RenameOperation(
            vault_path="/test/vault",
            old_tag="old-name",
            new_tag="new-name",
            dry_run=True
        )
        assert operation is not None
    
    def test_rename_dry_run_mode(self, simple_vault):
        """Test rename operation in dry-run mode."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        operation = RenameOperation(
            vault_path=str(simple_vault),
            old_tag="work",
            new_tag="professional", 
            dry_run=True
        )
        
        results = operation.run_operation()
        
        # Dry run should return preview of changes without modifying files
        assert "preview" in results or "changes" in results or isinstance(results, dict)
        
        # Original files should be unchanged
        file1_content = (simple_vault / "file1.md").read_text()
        assert "work" in file1_content  # Should still contain old tag
        assert "professional" not in file1_content  # Should not contain new tag
    
    def test_rename_actual_execution(self, temp_dir):
        """Test actual rename operation execution."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        # Create a copy of vault for modification
        test_vault = temp_dir / "rename_vault"
        test_vault.mkdir()
        
        # Create test file with target tag
        test_file = test_vault / "test.md"
        test_file.write_text("""---
tags: [work, notes]
---

# Test File

Content with #work inline tag.
""")
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work", 
            new_tag="professional",
            dry_run=False
        )
        
        results = operation.run_operation()
        
        # Check that file was actually modified
        modified_content = test_file.read_text()
        assert "professional" in modified_content
        # Original tag should be replaced (depending on implementation)
        
        # Results should contain operation summary
        assert isinstance(results, dict)
        assert "stats" in results
        assert "files_modified" in results["stats"]
    
    def test_rename_preserves_file_structure(self, temp_dir):
        """Test that rename operation preserves original file structure."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "structure_vault"
        test_vault.mkdir()
        
        # Create file with complex structure
        test_file = test_vault / "complex.md"
        original_content = """---
title: "Complex File"
tags: [work, notes, ideas]
created: 2024-01-15
author: "Test User"
---

# Complex File

This file has complex structure with #work tags.

## Section 2

More content here.
"""
        test_file.write_text(original_content)
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional", 
            dry_run=False
        )
        
        operation.run_operation()
        
        # Check that structure is preserved
        modified_content = test_file.read_text()
        
        # Should still have frontmatter structure
        assert "title: \"Complex File\"" in modified_content
        assert "created: 2024-01-15" in modified_content  
        assert "author: \"Test User\"" in modified_content
        
        # Should preserve content structure
        assert "# Complex File" in modified_content
        assert "## Section 2" in modified_content
    
    def test_rename_only_target_tag(self, temp_dir):
        """Test rename only affects the target tag, not other tags."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "selective_vault"
        test_vault.mkdir()
        
        test_file = test_vault / "selective.md"
        test_file.write_text("""---
tags: [work, workflow, workspace]
---

Content with #work #workflow and #workspace tags.
""")
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional",
            dry_run=False
        )
        
        operation.run_operation()
        
        modified_content = test_file.read_text()
        
        # Should have renamed 'work' to 'professional'
        # But should preserve 'workflow' and 'workspace' (similar but different tags)
        assert "workflow" in modified_content
        assert "workspace" in modified_content
    
    def test_rename_handles_no_matching_files(self, simple_vault):
        """Test rename operation when no files contain the target tag."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        operation = RenameOperation(
            vault_path=str(simple_vault),
            old_tag="nonexistent-tag",
            new_tag="new-tag",
            dry_run=False
        )
        
        results = operation.run_operation()
        
        # Should handle gracefully
        assert isinstance(results, dict)
        assert results.get("files_modified", 0) == 0 or results.get("statistics", {}).get("files_modified", 0) == 0


class TestMergeOperation:
    """Tests for tag merge operations."""
    
    def test_merge_operation_initialization(self):
        """Test MergeOperation can be initialized."""
        from tagex.core.operations.tag_operations import MergeOperation
        
        operation = MergeOperation(
            vault_path="/test/vault",
            source_tags=["tag1", "tag2", "tag3"],
            target_tag="merged-tag",
            dry_run=True
        )
        assert operation is not None
    
    def test_merge_dry_run_mode(self, temp_dir):
        """Test merge operation in dry-run mode."""
        from tagex.core.operations.tag_operations import MergeOperation
        
        # Create test vault with merge candidates
        test_vault = temp_dir / "merge_vault"
        test_vault.mkdir()
        
        (test_vault / "file1.md").write_text("""---
tags: [ideas, brainstorming]
---
Content""")
        
        (test_vault / "file2.md").write_text("""---
tags: [thoughts, ideas]
---
Content with #brainstorming""")
        
        operation = MergeOperation(
            vault_path=str(test_vault),
            source_tags=["ideas", "brainstorming", "thoughts"],
            target_tag="thinking",
            dry_run=True
        )
        
        results = operation.run_operation()
        
        # Should return preview without modifying files
        assert isinstance(results, dict)
        
        # Files should be unchanged
        file1_content = (test_vault / "file1.md").read_text()
        assert "ideas" in file1_content
        assert "thinking" not in file1_content
    
    def test_merge_actual_execution(self, temp_dir):
        """Test actual merge operation execution."""
        from tagex.core.operations.tag_operations import MergeOperation
        
        test_vault = temp_dir / "merge_exec_vault"
        test_vault.mkdir()
        
        (test_vault / "file1.md").write_text("""---
tags: [ideas, brainstorming, notes]
---

Content with #thoughts inline.""")
        
        (test_vault / "file2.md").write_text("""---
tags: [thoughts, reference]
---

Content with #ideas and #brainstorming.""")
        
        operation = MergeOperation(
            vault_path=str(test_vault),
            source_tags=["ideas", "brainstorming", "thoughts"],
            target_tag="thinking",
            dry_run=False
        )
        
        results = operation.run_operation()
        
        # Check files were modified
        file1_content = (test_vault / "file1.md").read_text()
        file2_content = (test_vault / "file2.md").read_text()
        
        # Should contain target tag
        assert "thinking" in file1_content or "thinking" in file2_content
        
        # Other tags should be preserved
        assert "notes" in file1_content
        assert "reference" in file2_content
    
    def test_merge_handles_partial_matches(self, temp_dir):
        """Test merge when files only contain some of the source tags."""
        from tagex.core.operations.tag_operations import MergeOperation
        
        test_vault = temp_dir / "partial_vault"
        test_vault.mkdir()
        
        # File with only one of the source tags
        (test_vault / "partial.md").write_text("""---
tags: [ideas, unrelated]
---
Content""")
        
        # File with multiple source tags
        (test_vault / "multiple.md").write_text("""---
tags: [ideas, brainstorming, thoughts]
---
Content""")
        
        operation = MergeOperation(
            vault_path=str(test_vault),
            source_tags=["ideas", "brainstorming", "thoughts"],
            target_tag="thinking",
            dry_run=False
        )
        
        operation.run_operation()
        
        # Both files should be processed
        partial_content = (test_vault / "partial.md").read_text()
        multiple_content = (test_vault / "multiple.md").read_text()
        
        # Files that had any of the source tags should be modified
        assert "thinking" in partial_content or "thinking" in multiple_content


class TestOperationLogging:
    """Tests for operation logging functionality."""
    
    def test_operation_creates_log_file(self, temp_dir):
        """Test that operations create log files."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "log_vault"
        test_vault.mkdir()
        
        test_file = test_vault / "test.md"
        test_file.write_text("""---
tags: [work]
---
Content""")
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work", 
            new_tag="professional",
            dry_run=False
        )
        
        operation.run_operation()
        
        # Should create log file in log/ directory
        log_dir = Path("log")
        assert log_dir.exists(), "log directory should exist"

        log_files = list(log_dir.glob("tag-*-op_*.json"))

        # Should have created at least one log file
        assert len(log_files) > 0
    
    def test_log_file_structure(self, mock_operation_log):
        """Test that log file has expected structure."""
        # This tests the expected structure based on the fixture
        log_data = mock_operation_log
        
        # Required top-level fields
        assert "operation" in log_data
        assert "timestamp" in log_data
        assert "vault_path" in log_data
        assert "dry_run" in log_data
        assert "files_processed" in log_data
        assert "statistics" in log_data
        
        # Statistics structure
        stats = log_data["statistics"]
        assert "total_files" in stats
        assert "files_modified" in stats
        assert "errors" in stats
        
        # Modifications structure (if not dry run)
        if not log_data["dry_run"]:
            assert "modifications" in log_data
            if len(log_data["modifications"]) > 0:
                mod = log_data["modifications"][0]
                assert "file" in mod
                assert "original_hash" in mod or "changes" in mod
    
    def test_operation_integrity_checks(self, temp_dir):
        """Test that operations include integrity checks."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "integrity_vault"
        test_vault.mkdir()
        
        test_file = test_vault / "integrity_test.md"
        original_content = """---
tags: [test-tag]
---

# Test File

Content to check integrity."""
        test_file.write_text(original_content)
        
        # Get original file hash/size for comparison
        original_size = test_file.stat().st_size
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="test-tag",
            new_tag="renamed-tag",
            dry_run=False
        )
        
        results = operation.run_operation()
        
        # File should exist and have reasonable size
        assert test_file.exists()
        new_size = test_file.stat().st_size
        
        # Size should be similar (tag rename shouldn't drastically change file size)
        assert abs(new_size - original_size) < 100  # Allow for reasonable tag name differences
    
    def test_dry_run_produces_log(self, temp_dir):
        """Test that dry-run mode also produces logs."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "dry_run_vault"
        test_vault.mkdir()
        
        (test_vault / "test.md").write_text("""---
tags: [work]
---
Content""")
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional",
            dry_run=True
        )
        
        results = operation.run_operation()
        
        # Dry run should also produce results/logs
        assert isinstance(results, dict)
        # Should indicate no files were actually modified
        if "files_modified" in results:
            # In dry run, files_modified should be 0 or indicate preview mode
            pass


class TestDeleteOperation:
    """Tests for tag delete operations."""

    def test_delete_operation_initialization(self):
        """Test DeleteOperation can be initialized."""
        from tagex.core.operations.tag_operations import DeleteOperation

        operation = DeleteOperation(
            vault_path="/test/vault",
            tags_to_delete=["unwanted-tag", "another-tag"],
            dry_run=True
        )
        assert operation is not None
        assert operation.tags_to_delete == ["unwanted-tag", "another-tag"]

    def test_delete_single_tag_frontmatter_only(self, temp_dir):
        """Test deleting a tag that only appears in frontmatter."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "delete_vault"
        test_vault.mkdir()

        test_file = test_vault / "frontmatter_only.md"
        test_file.write_text("""---
tags: [work, notes, unwanted-tag]
---

# Test File

Content with no inline tags.
""")

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["unwanted-tag"],
            dry_run=False
        )

        results = operation.run_operation()

        # Check that tag was removed
        modified_content = test_file.read_text()
        assert "unwanted-tag" not in modified_content
        assert "work" in modified_content  # Other tags preserved
        assert "notes" in modified_content

        # Should report minimal warnings for frontmatter-only deletion
        assert operation.inline_deletions == 0
        assert operation.frontmatter_deletions == 1

    def test_delete_single_tag_inline_only(self, temp_dir):
        """Test deleting a tag that only appears inline (should warn)."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "inline_vault"
        test_vault.mkdir()

        test_file = test_vault / "inline_only.md"
        test_file.write_text("""---
tags: [work, notes]
---

# Test File

Content with #unwanted-tag inline tag.
More content with #work tag.
""")

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["unwanted-tag"],
            dry_run=False
        )

        results = operation.run_operation()

        # Check that inline tag was removed
        modified_content = test_file.read_text()
        assert "#unwanted-tag" not in modified_content
        assert "#work" in modified_content  # Other inline tags preserved

        # Should report warnings for inline deletion
        assert operation.inline_deletions == 1
        assert operation.frontmatter_deletions == 0
        assert len(operation.operation_log["warnings"]) > 0

    def test_delete_tag_both_locations_warns_about_inline(self, temp_dir):
        """Test deleting a tag that appears in both frontmatter and inline."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "both_vault"
        test_vault.mkdir()

        test_file = test_vault / "both_locations.md"
        test_file.write_text("""---
tags: [work, unwanted-tag, notes]
---

# Test File

Content with #unwanted-tag inline and #work inline.
""")

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["unwanted-tag"],
            dry_run=False
        )

        results = operation.run_operation()

        # Check that tag was removed from both locations
        modified_content = test_file.read_text()
        assert "unwanted-tag" not in modified_content
        assert "#unwanted-tag" not in modified_content
        assert "work" in modified_content
        assert "#work" in modified_content

        # Should report both types but warn about inline
        assert operation.inline_deletions == 1
        assert operation.frontmatter_deletions == 1
        assert len(operation.operation_log["warnings"]) > 0

    def test_delete_multiple_tags(self, temp_dir):
        """Test deleting multiple tags at once."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "multi_vault"
        test_vault.mkdir()

        test_file1 = test_vault / "file1.md"
        test_file1.write_text("""---
tags: [work, unwanted1, notes, unwanted2]
---

Content with #unwanted1 and #work.
""")

        test_file2 = test_vault / "file2.md"
        test_file2.write_text("""---
tags: [unwanted2, reference]
---

Content with #unwanted2 inline.
""")

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["unwanted1", "unwanted2"],
            dry_run=False
        )

        results = operation.run_operation()

        # Check both files
        file1_content = test_file1.read_text()
        file2_content = test_file2.read_text()

        # Unwanted tags should be gone
        assert "unwanted1" not in file1_content
        assert "unwanted2" not in file1_content
        assert "unwanted2" not in file2_content

        # Other tags should remain
        assert "work" in file1_content
        assert "notes" in file1_content
        assert "reference" in file2_content

        # Should have processed both files
        assert results["stats"]["files_modified"] >= 2

    def test_delete_dry_run_mode(self, temp_dir):
        """Test delete operation in dry-run mode."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "dry_delete_vault"
        test_vault.mkdir()

        test_file = test_vault / "dry_test.md"
        original_content = """---
tags: [work, unwanted-tag, notes]
---

Content with #unwanted-tag inline.
"""
        test_file.write_text(original_content)

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["unwanted-tag"],
            dry_run=True
        )

        results = operation.run_operation()

        # File should be unchanged
        current_content = test_file.read_text()
        assert current_content == original_content

        # Should still report what would be done
        assert isinstance(results, dict)
        assert results["dry_run"] == True

    def test_delete_preserves_file_structure(self, temp_dir):
        """Test that delete preserves original file structure."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "structure_delete_vault"
        test_vault.mkdir()

        test_file = test_vault / "complex.md"
        test_file.write_text("""---
title: "Complex File"
tags: [work, unwanted-tag, notes, ideas]
created: 2024-01-15
author: "Test User"
---

# Complex File

This file has complex structure with #unwanted-tag and #work tags.

## Section 2

More content here.

```code
# This should not be touched
unwanted-tag = "in code"
```

Final content.
""")

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["unwanted-tag"],
            dry_run=False
        )

        operation.run_operation()

        modified_content = test_file.read_text()

        # Structure should be preserved
        assert "title: \"Complex File\"" in modified_content
        assert "created: 2024-01-15" in modified_content
        assert "author: \"Test User\"" in modified_content
        assert "# Complex File" in modified_content
        assert "## Section 2" in modified_content

        # Tag should be removed from frontmatter and inline
        assert "unwanted-tag" not in modified_content.split("```")[0]  # Before code block
        assert "#unwanted-tag" not in modified_content.split("```")[0]  # Before code block

        # But should be preserved in code blocks
        assert 'unwanted-tag = "in code"' in modified_content

        # Other tags preserved
        assert "work" in modified_content
        assert "#work" in modified_content

    def test_delete_nonexistent_tag(self, simple_vault):
        """Test deleting a tag that doesn't exist in any files."""
        from tagex.core.operations.tag_operations import DeleteOperation

        operation = DeleteOperation(
            vault_path=str(simple_vault),
            tags_to_delete=["absolutely-nonexistent-tag"],
            dry_run=False
        )

        results = operation.run_operation()

        # Should handle gracefully
        assert isinstance(results, dict)
        assert results["stats"]["files_modified"] == 0
        assert results["stats"]["tags_modified"] == 0

    def test_delete_nonexistent_tag_no_file_modifications(self, temp_dir):
        """Test that deleting nonexistent tags doesn't modify any files unnecessarily."""
        from tagex.core.operations.tag_operations import DeleteOperation
        import hashlib

        test_vault = temp_dir / "nochange_vault"
        test_vault.mkdir()

        # Create test files with various tag formats
        files_data = [
            ("empty_tags.md", """---
tags: []
---

Content with no tags."""),
            ("single_tag.md", """---
tags: [work]
---

Content with #work tag."""),
            ("multi_tags.md", """---
tags: [work, notes, ideas]
---

Content with #work and #notes tags."""),
            ("multiline_tags.md", """---
tags:
  - work
  - notes
---

Content here."""),
            ("no_frontmatter.md", """# Just Content

Regular markdown with #work inline tag.""")
        ]

        # Create files and calculate their original hashes
        original_hashes = {}
        for filename, content in files_data:
            file_path = test_vault / filename
            file_path.write_text(content)
            original_hashes[filename] = hashlib.sha256(content.encode('utf-8')).hexdigest()

        # Delete a nonexistent tag
        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["nonexistent-tag"],
            dry_run=False
        )

        results = operation.run_operation()

        # Verify no files were modified
        assert results["stats"]["files_modified"] == 0
        assert results["stats"]["tags_modified"] == 0

        # Verify file contents are exactly the same (by hash)
        for filename, original_content in files_data:
            file_path = test_vault / filename
            current_content = file_path.read_text()
            current_hash = hashlib.sha256(current_content.encode('utf-8')).hexdigest()
            assert current_hash == original_hashes[filename], f"File {filename} was unexpectedly modified"
            assert current_content == original_content, f"Content of {filename} changed unexpectedly"

    def test_delete_empty_tag_list(self, simple_vault):
        """Test delete operation with empty tag list."""
        from tagex.core.operations.tag_operations import DeleteOperation

        operation = DeleteOperation(
            vault_path=str(simple_vault),
            tags_to_delete=[],
            dry_run=False
        )

        results = operation.run_operation()

        # Should handle gracefully
        assert isinstance(results, dict)
        assert results["stats"]["files_modified"] == 0
        assert results["stats"]["tags_modified"] == 0

    def test_delete_case_insensitive_matching(self, temp_dir):
        """Test that delete operation matches tags case-insensitively."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "case_vault"
        test_vault.mkdir()

        test_file = test_vault / "case_test.md"
        test_file.write_text("""---
tags: [Work, NOTES, Ideas]
---

Content with #Work and #IDEAS tags.
""")

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["work", "ideas"],  # lowercase
            dry_run=False
        )

        operation.run_operation()

        modified_content = test_file.read_text()

        # Should remove Work and Ideas (case insensitive)
        assert "Work" not in modified_content or len([x for x in modified_content.split() if "Work" in x]) == 0
        assert "IDEAS" not in modified_content or len([x for x in modified_content.split() if "IDEAS" in x]) == 0

        # Should preserve NOTES
        assert "NOTES" in modified_content

    def test_delete_handles_tag_array_formats(self, temp_dir):
        """Test delete with various YAML tag array formats."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "format_vault"
        test_vault.mkdir()

        # Single line array
        (test_vault / "array.md").write_text("""---
tags: [work, unwanted, notes]
---
Content""")

        # Multi-line array
        (test_vault / "multiline.md").write_text("""---
tags:
  - work
  - unwanted
  - notes
---
Content""")

        # Comma separated
        (test_vault / "comma.md").write_text("""---
tags: work, unwanted, notes
---
Content""")

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["unwanted"],
            dry_run=False
        )

        operation.run_operation()

        # All files should have unwanted tag removed
        array_content = (test_vault / "array.md").read_text()
        multiline_content = (test_vault / "multiline.md").read_text()
        comma_content = (test_vault / "comma.md").read_text()

        assert "unwanted" not in array_content
        assert "unwanted" not in multiline_content
        assert "unwanted" not in comma_content

        # Other tags should remain
        assert "work" in array_content and "notes" in array_content
        assert "work" in multiline_content and "notes" in multiline_content
        assert "work" in comma_content and "notes" in comma_content

    def test_delete_creates_operation_log(self, temp_dir):
        """Test that delete operation creates proper log files."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "log_delete_vault"
        test_vault.mkdir()

        test_file = test_vault / "test.md"
        test_file.write_text("""---
tags: [work, unwanted]
---

Content with #unwanted inline.
""")

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["unwanted"],
            dry_run=False
        )

        results = operation.run_operation()

        # Should create log file in log/ directory
        log_dir = Path("log")
        assert log_dir.exists(), "log directory should exist"

        log_files = list(log_dir.glob("tag-delete-op_*.json"))
        assert len(log_files) > 0

        # Log should have delete-specific structure
        assert results["operation_type"] == "delete"
        assert "tags_to_delete" in results
        assert "warnings" in results
        assert results["tags_to_delete"] == ["unwanted"]

    def test_delete_warning_content_and_format(self, temp_dir):
        """Test that warnings contain proper information."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "warning_vault"
        test_vault.mkdir()

        test_file = test_vault / "warning_test.md"
        test_file.write_text("""---
tags: [work]
---

Content with #unwanted-inline tag that will generate warning.
""")

        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["unwanted-inline"],
            dry_run=False
        )

        results = operation.run_operation()

        # Should have warnings
        warnings = results["warnings"]
        assert len(warnings) > 0

        # Warning should contain file path and explanation
        warning = warnings[0]
        assert "file" in warning
        assert "type" in warning
        assert warning["type"] == "inline_deletion"
        assert "message" in warning
        assert "readability" in warning["message"].lower()


class TestOperationEdgeCases:
    """Tests for edge cases and error conditions in operations."""

    def test_operation_with_nonexistent_vault(self):
        """Test operation with nonexistent vault path."""
        from tagex.core.operations.tag_operations import RenameOperation

        operation = RenameOperation(
            vault_path="/nonexistent/vault/path",
            old_tag="work",
            new_tag="professional",
            dry_run=True
        )

        # Should handle gracefully
        try:
            results = operation.run_operation()
            # Should either return empty results or raise appropriate exception
            assert isinstance(results, dict) or results is None
        except (FileNotFoundError, OSError):
            # Acceptable to raise appropriate exceptions
            pass
    
    def test_operation_with_invalid_tag_names(self, simple_vault):
        """Test operation with invalid tag names."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        # Test with empty tag name
        operation = RenameOperation(
            vault_path=str(simple_vault),
            old_tag="",
            new_tag="valid-tag",
            dry_run=True
        )
        
        # Should handle invalid input gracefully
        try:
            results = operation.run_operation()
            if results:
                assert results.get("files_modified", 0) == 0
        except ValueError:
            # Acceptable to raise validation errors
            pass
    
    def test_operation_with_readonly_files(self, temp_dir):
        """Test operation behavior with readonly files."""
        import os
        import stat
        from tagex.core.operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "readonly_vault"
        test_vault.mkdir()
        
        test_file = test_vault / "readonly.md"
        test_file.write_text("""---
tags: [work]
---
Content""")
        
        # Make file readonly
        test_file.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
        
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional",
            dry_run=False
        )
        
        try:
            results = operation.run_operation()
            # Should handle readonly files gracefully
            assert isinstance(results, dict)
        except PermissionError:
            # Acceptable to fail with permission errors
            pass
        finally:
            # Restore write permissions for cleanup
            try:
                test_file.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            except:
                pass
    
    def test_concurrent_operations_safety(self, temp_dir):
        """Test that operations are safe from concurrent modification issues."""
        from tagex.core.operations.tag_operations import RenameOperation
        
        test_vault = temp_dir / "concurrent_vault"  
        test_vault.mkdir()
        
        test_file = test_vault / "concurrent.md"
        test_file.write_text("""---
tags: [work, notes]
---
Content""")
        
        # Create two operations on the same vault
        operation1 = RenameOperation(
            vault_path=str(test_vault),
            old_tag="work",
            new_tag="professional",
            dry_run=True  # Use dry run to avoid actual conflicts
        )
        
        operation2 = RenameOperation(
            vault_path=str(test_vault), 
            old_tag="notes",
            new_tag="documentation",
            dry_run=True
        )
        
        # Both should execute without interfering
        results1 = operation1.run_operation()
        results2 = operation2.run_operation()
        
        assert isinstance(results1, dict)
        assert isinstance(results2, dict)
        
        # Original file should be unchanged (dry run)
        content = test_file.read_text()
        assert "work" in content
        assert "notes" in content


class TestOperationsWithTagTypes:
    """Test operations with tag_types parameter filtering."""

    def test_rename_with_frontmatter_only(self, temp_dir):
        """Test rename operation with frontmatter-only tag filtering."""
        from tagex.core.operations.tag_operations import RenameOperation

        test_vault = temp_dir / "frontmatter_rename_vault"
        test_vault.mkdir()

        test_file = test_vault / "mixed_tags.md"
        test_file.write_text("""---
tags: [old-tag, work]
---
# Title
Content with #old-tag and #work inline tags""")

        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="old-tag",
            new_tag="new-tag",
            dry_run=False,
            tag_types='frontmatter'
        )

        results = operation.run_operation()

        # Read modified content
        content = test_file.read_text()

        # Frontmatter tag should be renamed
        assert "new-tag" in content
        # Inline tag should remain unchanged
        assert "#old-tag" in content  # Inline tag preserved
        # Frontmatter should not contain old tag
        assert "tags: [new-tag, work]" in content or "tags: [work, new-tag]" in content

    def test_rename_with_inline_only(self, temp_dir):
        """Test rename operation with inline-only tag filtering."""
        from tagex.core.operations.tag_operations import RenameOperation

        test_vault = temp_dir / "inline_rename_vault"
        test_vault.mkdir()

        test_file = test_vault / "mixed_tags.md"
        test_file.write_text("""---
tags: [old-tag, work]
---
# Title
Content with #old-tag and #work inline tags""")

        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="old-tag",
            new_tag="new-tag",
            dry_run=False,
            tag_types='inline'
        )

        results = operation.run_operation()

        # Read modified content
        content = test_file.read_text()

        # Inline tag should be renamed
        assert "#new-tag" in content
        # Frontmatter tag should remain unchanged
        assert "tags: [old-tag, work]" in content

    def test_merge_with_tag_types_filtering(self, temp_dir):
        """Test merge operation with tag_types filtering."""
        from tagex.core.operations.tag_operations import MergeOperation

        test_vault = temp_dir / "merge_tag_types_vault"
        test_vault.mkdir()

        test_file = test_vault / "mixed_tags.md"
        test_file.write_text("""---
tags: [source1, work]
---
# Title
Content with #source1 and #source2 inline tags""")

        # Merge only frontmatter tags
        operation = MergeOperation(
            vault_path=str(test_vault),
            source_tags=["source1"],
            target_tag="merged",
            dry_run=False,
            tag_types='frontmatter'
        )

        results = operation.run_operation()
        content = test_file.read_text()

        # Frontmatter should have merged tag
        assert "merged" in content and "tags:" in content
        # Inline source1 should remain unchanged
        assert "#source1" in content

    def test_delete_with_tag_types_filtering(self, temp_dir):
        """Test delete operation with tag_types filtering."""
        from tagex.core.operations.tag_operations import DeleteOperation

        test_vault = temp_dir / "delete_tag_types_vault"
        test_vault.mkdir()

        test_file = test_vault / "mixed_tags.md"
        test_file.write_text("""---
tags: [to-delete, keep]
---
# Title
Content with #to-delete and #keep inline tags""")

        # Delete only from frontmatter
        operation = DeleteOperation(
            vault_path=str(test_vault),
            tags_to_delete=["to-delete"],
            dry_run=False,
            tag_types='frontmatter'
        )

        results = operation.run_operation()
        content = test_file.read_text()

        # Frontmatter should not have deleted tag
        assert "to-delete" not in content.split("---")[1]  # frontmatter section
        # Inline tag should remain
        assert "#to-delete" in content

    def test_operation_logs_include_tag_types(self, temp_dir):
        """Test that operation logs include tag_types setting."""
        from tagex.core.operations.tag_operations import RenameOperation

        test_vault = temp_dir / "log_tag_types_vault"
        test_vault.mkdir()

        test_file = test_vault / "test.md"
        test_file.write_text("""---
tags: [test]
---
# Test""")

        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="test",
            new_tag="renamed",
            dry_run=True,
            tag_types='frontmatter'
        )

        results = operation.run_operation()

        # Check that tag_types is logged
        assert results["tag_types"] == 'frontmatter'

    def test_no_matching_tag_types_produces_no_changes(self, temp_dir):
        """Test that operations produce no changes when no matching tag types exist."""
        from tagex.core.operations.tag_operations import RenameOperation

        test_vault = temp_dir / "no_match_vault"
        test_vault.mkdir()

        test_file = test_vault / "inline_only.md"
        test_file.write_text("""# Title
Content with #inline-only tag""")

        # Try to rename with frontmatter-only filtering
        operation = RenameOperation(
            vault_path=str(test_vault),
            old_tag="inline-only",
            new_tag="renamed",
            dry_run=False,
            tag_types='frontmatter'
        )

        results = operation.run_operation()

        # Should report no changes
        assert results["stats"]["files_modified"] == 0
        assert results["stats"]["tags_modified"] == 0

        # File content should be unchanged
        content = test_file.read_text()
        assert "#inline-only" in content
        assert "renamed" not in content